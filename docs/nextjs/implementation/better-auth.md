# 認証を使う画面と処理

[導入と設定](../setup/better-auth.md)を前提とする。

## アプリからのユーザー作成

管理者用のServer Action・Route Handlerから作成する場合は、実際のリクエストのheadersを渡す。

```ts
const requestHeaders = await headers();
await getAuth().api.createUser({
  headers: requestHeaders,
  body: { name, email, password },
});
```

`headers`は`next/headers`、`getAuth`は`@/auth/server`からimportする。
管理者のセッションと`user:create`権限はAdminプラグインが確認する。
`role`は省略し、既定の一般ユーザーとして作成する。`role: "user"`でも明示するとロール設定権限が必要になる。

headersもrequestも渡さない直接呼び出しは、CLIと同じ特権操作になる。アプリの操作では必ずリクエストを引き継ぎ、呼び出し元の認証・権限チェックを有効にする。

## セッション

セッション取得と未認証時のリダイレクトも`src/auth/server.ts`の`getSession`・`requireSession`にまとめる。
ページでは`requireSession()`、未認証時の応答を個別に決めるServer Action・Route Handlerでは`getSession()`を使う。

**`await headers()`を先に実行してから、認証設定を初期化する。**
`getAuth().api.getSession({ headers: await headers() })`の順序では、Next.jsがリクエスト時の処理と判定する前に環境変数を読むため、秘密情報なしでビルドできなくなる。

保護するページではセッションがなければ`redirect("/sign-in")`する。
Server Action・Route Handlerでも処理前に確認し、APIなら未認証時に401を返す。
レイアウトやproxyだけにチェックを任せず、各処理に必要な権限・データの所有者も確認する。

セッションはDB保存で始め、Cookieキャッシュは有効にしない。
標準のレート制限は維持する。保存先はメモリなので、複数インスタンスで共有する場合はDBなどへ変更する。

## 最小のフォーム

[React Hook Formの共通方針](react-hook-form.md)に従い、`Controller`でMantineの入力へ接続する。
画面はログインのみ。ページ専用のフォームとスキーマは、`_components`・`_helpers`へ置く。

ログイン側の`_helpers/form-schema.ts`：

```ts
import { z } from "zod";

type FormMessages = {
  invalidEmail: string;
  required: string;
};

export function createFormSchema(messages: FormMessages) {
  return z.object({
    email: z.email(messages.invalidEmail),
    // Sign-in only checks presence: showing the password policy here would
    // disclose it, and the server decides whether the credentials are valid.
    password: z.string().min(1, messages.required),
  });
}
```

ログインでは、パスワードは未入力だけを検証する。長さなどの条件を表示すると、未ログインの相手へパスワードの条件を示すことになる。入力が正しいかはサーバーが判定する。
パスワードをtrim・変換しない。メールアドレスの形式は秘密ではなく、入力誤りに気づけるため検証する。

ログイン側の`_components/auth-form.tsx`：

```tsx
"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Alert,
  Button,
  Container,
  PasswordInput,
  Stack,
  TextInput,
  Title,
} from "@mantine/core";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Controller, useForm } from "react-hook-form";
import type { z } from "zod";
import { authClient } from "@/auth/client";
import { createFormSchema } from "../_helpers/form-schema";

export function AuthForm() {
  const translate = useTranslations();
  const router = useRouter();

  const schema = createFormSchema({
    invalidEmail: translate("validation.invalidEmail"),
    required: translate("validation.required"),
  });
  const form = useForm<
    z.input<typeof schema>,
    unknown,
    z.output<typeof schema>
  >({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  return (
    <Container size="xs" py="xl">
      <form
        noValidate
        onSubmit={form.handleSubmit(async (values) => {
          form.clearErrors("root");
          try {
            const result = await authClient.signIn.email(values);
            if (result.error != null) {
              form.setError("root", {
                message: translate("pages.signIn.failed"),
              });
              return;
            }
            router.replace("/");
            router.refresh();
          } catch {
            form.setError("root", {
              message: translate("pages.signIn.failed"),
            });
          }
        })}
      >
        <Stack>
          <Title order={1}>{translate("pages.signIn.title")}</Title>

          <Controller
            control={form.control}
            name="email"
            render={({ field, fieldState }) => (
              <TextInput
                {...field}
                type="email"
                label={translate("models.user.email")}
                autoComplete="email"
                error={fieldState.error?.message}
              />
            )}
          />
          <Controller
            control={form.control}
            name="password"
            render={({ field, fieldState }) => (
              <PasswordInput
                {...field}
                label={translate("models.user.password")}
                autoComplete="current-password"
                error={fieldState.error?.message}
              />
            )}
          />

          {form.formState.errors.root?.message && (
            <Alert role="alert" color="red">
              {form.formState.errors.root.message}
            </Alert>
          )}
          <Button type="submit" loading={form.formState.isSubmitting}>
            {translate("pages.signIn.submit")}
          </Button>
        </Stack>
      </form>
    </Container>
  );
}
```
`page.tsx`は、ログイン済みなら`/`へリダイレクトし、それ以外は`<AuthForm />`を返す。ログイン済みのままログイン画面を表示しない。

```tsx
import { redirect } from "next/navigation";
import { getSession } from "@/auth/server";
import { AuthForm } from "./_components/auth-form";

export default async function Page() {
  const session = await getSession();
  if (session != null) {
    redirect("/");
  }

  return <AuthForm />;
}
```

`messages/ja.json`では、画面固有の文言を`pages.signIn`、ユーザーの項目名を`models.user`、共通の入力検証メッセージを`validation`に置く。翻訳関数は`translate`とし、名前空間を指定せず完全なキーで参照する。

```json
{
  "pages": {
    "signIn": {
      "title": "ログイン",
      "submit": "ログイン",
      "failed": "メールアドレスまたはパスワードが正しくありません"
    }
  },
  "models": {
    "user": {
      "email": "メールアドレス",
      "password": "パスワード"
    }
  },
  "validation": {
    "required": "入力してください",
    "invalidEmail": "有効なメールアドレスを入力してください"
  }
}
```

ログインの失敗は、メールアドレスの有無とパスワードの誤りを区別しない1つの文言で表示する。初期構成では、通信エラーなども同じ文言にまとめる。
細分化する場合はBetter Authのエラーコードを翻訳キーへ対応させ、返された英語メッセージをそのまま画面へ出さない。

## ログアウト

[共通レイアウトのユーザーメニュー](layout.md#ユーザーメニューとログアウト)から行う。
`authClient.signOut()`の後に`router.replace("/sign-in")`・`router.refresh()`を呼ぶ。初期構成では、失敗時の表示や処理中の状態は設けない。

## 参考

- [Better Auth：導入](https://better-auth.com/docs/installation)
- [Prisma adapter](https://better-auth.com/docs/adapters/prisma)
- [CLI・初期管理者の作成](https://better-auth.com/docs/concepts/cli)
- [Adminプラグイン・アクセス制御](https://better-auth.com/docs/plugins/admin)
- [Hooks](https://better-auth.com/docs/concepts/hooks)
- [Adminのユーザー作成実装（1.7.6）](https://github.com/better-auth/better-auth/blob/v1.7.6/packages/better-auth/src/plugins/admin/routes.ts)
- [Next.js連携](https://better-auth.com/docs/integrations/next)
- [設定オプション：disableSignUp](https://better-auth.com/docs/reference/options)
- [メール・パスワード認証](https://better-auth.com/docs/authentication/email-password)
- [セッション管理](https://better-auth.com/docs/concepts/session-management)
- [レート制限](https://better-auth.com/docs/concepts/rate-limit)
