# Better Authの初期設定

事前に作成されたユーザーのメール・パスワードによるログイン・ログアウトと、DBに保存するセッションを用意する。
テナントを持たない構成として、Organizationプラグインは使わない。メール確認・パスワード再設定は後から追加する。

## 依存と配置

[Prisma](prisma.md)・[Mantine](mantine.md)・[React Hook Form](react-hook-form.md)・[i18n](i18n.md)の設定を引き継ぐ。

```sh
pnpm add -E better-auth@1.7.6 @better-auth/prisma-adapter@1.7.6
pnpm add -D -E auth@1.7.6
```

`auth`はschema生成用の公式CLI。本体・Prisma adapter・CLIの版を揃える。
バージョンは[共通の依存管理方針](../base/pnpm-workspace.md)に従って選び、完全固定する。

`auth@1.7.6`の間接依存`semver@6.3.1`は、`trustPolicy: no-downgrade`で拒否されるため、上記CLIの導入には[依存単位の審査](../base/pnpm-workspace.md#例外の運用)が必要。信頼性チェックを一括で無効にしない。

```text
auth.config.ts
src/
  auth/
    options.ts
    server.ts
    client.ts
    session.ts
  app/
    api/auth/[...all]/route.ts
    sign-in/
      page.tsx
      _components/auth-form.tsx
      _helpers/form-schema.ts
```

アプリ固有の認証設定なので、汎用処理用の`lib`ではなく`src/auth`にまとめる。
usecasesには認証済みユーザーのIDなどを引数で渡し、Next.jsのheadersやCookieを持ち込まない。

## 設定と環境変数

`src/auth/options.ts`は、認証処理・schema生成・フォームで共有する設定。Next.jsのサーバー専用処理や環境変数へ依存させず、秘密情報は`server.ts`で追加する。パスワード長はここだけで定義し、フォームの検証とエラー文言も同じ値を参照する。

```ts
import type { BetterAuthOptions } from "better-auth/minimal";

export const authOptions = {
  emailAndPassword: {
    enabled: true,
    disableSignUp: true,
    minPasswordLength: 8,
    maxPasswordLength: 128,
  },
} satisfies BetterAuthOptions;
```
認証方式とパスワードの長さを明示し、`disableSignUp: true`でメール・パスワードの新規登録APIを無効にする。
ユーザーの作成は管理側の処理として別途用意する。

[サーバー用の環境変数](env.md)へ、次の項目と対応する`process.env`の明示的な読み取りを追加する。

```ts
BETTER_AUTH_URL: z.url(),
BETTER_AUTH_SECRET: z.string().min(32),
```

ローカルのURLは`http://localhost:3000`、本番は実際に公開するHTTPSのURLにする。
秘密鍵は`openssl rand -base64 32`などで生成し、実行環境から渡す。`NEXT_PUBLIC_*`にはしない。

`src/auth/server.ts`：

```ts
import "server-only";
import { prismaAdapter } from "@better-auth/prisma-adapter";
import { betterAuth } from "better-auth/minimal";
import { getServerEnv } from "@/env/server";
import { getPrisma } from "@/prisma/client";
import { authOptions } from "./options";

let auth: ReturnType<typeof createAuth> | undefined;

export function getAuth() {
  auth ??= createAuth();
  return auth;
}

function createAuth() {
  const env = getServerEnv();
  return betterAuth({
    ...authOptions,
    baseURL: env.BETTER_AUTH_URL,
    secret: env.BETTER_AUTH_SECRET,
    database: prismaAdapter(getPrisma(), { provider: "postgresql" }),
  });
}
```
Prisma接続を使うため、組み込みDB接続部分を含まない`better-auth/minimal`からimportする。
認証インスタンスは遅延初期化して再利用し、import時に本番の秘密情報を要求しない。

## schemaの生成と適用

ルートの`auth.config.ts`はCLI専用とし、共通設定だけを読み込む。

```ts
import { betterAuth } from "better-auth/minimal";
import { authOptions } from "./src/auth/options";
export const auth = betterAuth(authOptions);
```
```sh
pnpm exec auth generate --config ./auth.config.ts --adapter prisma --dialect postgresql
```

`--adapter prisma`を指定することで、DB接続や生成済みPrisma Clientなしでschemaを生成できる。
実行時の`server-only`モジュールはCLIから読み込まない。CLI用設定を認証APIの実行に使わない。

生成される基本モデルは`User`・`Session`・`Account`・`Verification`。
[Prismaの命名規則](prisma.md#schemaの命名)に合わせ、テーブル名を`users`・`sessions`・`accounts`・`verifications`へ`@@map`する。
カラムは`emailVerified @map("email_verified")`、`userId @map("user_id")`など、snake_caseへ対応させる。
Prisma側のモデル名・フィールド名は維持するため、Better Auth側の名前設定を変更する必要はない。

schema差分とマッピングを確認してから、SQLを生成する。

```sh
pnpm run db:migrate --name add-auth
```

`db:migrate`は`--create-only`付きの既存scriptを使う。SQLを確認してから適用する。

```sh
pnpm run db:deploy
pnpm run db:generate
```

生成されたschema・migrationsはGit管理する。認証設定の変更で再生成した場合も差分を確認する。
再生成時も、テーブル名・カラム名のマッピングを差分確認の対象に含める。

## APIとセッション

`src/app/api/auth/[...all]/route.ts`：

```ts
import { toNextJsHandler } from "better-auth/next-js";
import { getAuth } from "@/auth/server";
export async function GET(request: Request) {
  return toNextJsHandler(getAuth()).GET(request);
}
export async function POST(request: Request) {
  return toNextJsHandler(getAuth()).POST(request);
}
```
ハンドラーを呼ぶ時点で`getAuth()`を実行し、モジュール読込時には初期化しない。

`src/auth/client.ts`：

```ts
"use client";
import { createAuthClient } from "better-auth/react";
export const authClient = createAuthClient();
```
同一オリジンなのでクライアント側のURL指定は不要。
ログイン操作はこのクライアントから認証APIへ送る。Server ActionでCookieを書き込む構成へ変更する場合は、`nextCookies()`を追加する。

`src/auth/session.ts`：

```ts
import "server-only";
import { headers } from "next/headers";
import { getAuth } from "./server";
export async function getSession() {
  const requestHeaders = await headers();
  return getAuth().api.getSession({ headers: requestHeaders });
}
```
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
    "lengthRange": "{min}〜{max}文字で入力してください"
  }
}
```

初期構成では認証エラーを共通の日本語メッセージで表示する。
細分化する場合はBetter Authのエラーコードを翻訳キーへ対応させ、返された英語メッセージをそのまま画面へ出さない。

ログアウトは`authClient.signOut()`の成功後に`router.replace("/sign-in")`・`router.refresh()`を呼ぶ。
失敗時は画面へエラーを表示し、ログアウトできたことにしない。

## CIとDocker

[PrismaのDocker設定](prisma.md#ciとdocker)を引き継ぐ。
認証用schemaの生成は設定変更時に行い、CI・Dockerではコミット済みschemaからPrisma Clientを生成する。
DB接続情報・認証の秘密鍵は実行時だけ渡す。

## 参考

- [Better Auth：導入](https://better-auth.com/docs/installation)
- [Prisma adapter](https://better-auth.com/docs/adapters/prisma)
- [CLI](https://better-auth.com/docs/concepts/cli)
- [Next.js連携](https://better-auth.com/docs/integrations/next)
- [設定オプション：disableSignUp](https://better-auth.com/docs/reference/options)
- [メール・パスワード認証](https://better-auth.com/docs/authentication/email-password)
- [セッション管理](https://better-auth.com/docs/concepts/session-management)
- [レート制限](https://better-auth.com/docs/concepts/rate-limit)
