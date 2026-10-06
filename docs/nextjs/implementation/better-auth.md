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
import { authOptions } from "@/auth/options";

type FormMessages = {
  invalidEmail: string;
  lengthRange: string;
};

export function createFormSchema(messages: FormMessages) {
  return z.object({
    email: z.email(messages.invalidEmail),
    password: z.string()
      .min(authOptions.emailAndPassword.minPasswordLength, messages.lengthRange)
      .max(authOptions.emailAndPassword.maxPasswordLength, messages.lengthRange),
  });
}
```

パスワードをtrim・変換しない。クライアントの検証に加えて、認証APIでもBetter Authが受信値を検証する。

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
import { authOptions } from "@/auth/options";
import { createFormSchema } from "../_helpers/form-schema";
export function AuthForm() {
  const translate = useTranslations();
  const router = useRouter();
  const schema = createFormSchema({
    invalidEmail: translate("validation.invalidEmail"),
    lengthRange: translate("validation.lengthRange", {
      min: authOptions.emailAndPassword.minPasswordLength,
      max: authOptions.emailAndPassword.maxPasswordLength,
    }),
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
            if (result.error) {
              form.setError("root", { message: translate("pages.signIn.failed") });
              return;
            }
            router.replace("/");
            router.refresh();
          } catch {
            form.setError("root", { message: translate("pages.signIn.failed") });
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
`page.tsx`は`<AuthForm />`を返すだけにする。
`messages/ja.json`では、画面固有の文言を`pages.signIn`、ユーザーの項目名を`models.user`、共通の入力検証メッセージを`validation`に置く。翻訳関数は`translate`とし、名前空間を指定せず完全なキーで参照する。

```json
{
  "pages": {
    "signIn": {
      "title": "ログイン",
      "submit": "ログイン",
      "failed": "認証に失敗しました"
    }
  },
  "models": {
    "user": {
      "email": "メールアドレス",
      "password": "パスワード"
    }
  },
  "validation": {
    "invalidEmail": "有効なメールアドレスを入力してください",
    "lengthRange": "{min, number}〜{max, number}文字で入力してください"
  }
}
```

初期構成では認証エラーを共通の日本語メッセージで表示する。
細分化する場合はBetter Authのエラーコードを翻訳キーへ対応させ、返された英語メッセージをそのまま画面へ出さない。

ログアウトは`authClient.signOut()`の成功後に`router.replace("/sign-in")`・`router.refresh()`を呼ぶ。
失敗時は画面へエラーを表示し、ログアウトできたことにしない。

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
