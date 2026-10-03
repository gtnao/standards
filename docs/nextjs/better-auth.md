# Better Authの初期設定

Adminプラグインで管理者がユーザーを作成し、メール・パスワードによるログイン・ログアウトと、DBに保存するセッションを用意する。
テナントを持たない構成として、Organizationプラグインは使わない。メール確認・パスワード再設定は後から追加する。

## 依存と配置

[Prisma](prisma.md)・[Mantine](mantine.md)・[React Hook Form](react-hook-form.md)・[i18n](i18n.md)の設定を引き継ぐ。

```sh
pnpm add -E better-auth@1.7.6 @better-auth/prisma-adapter@1.7.6
pnpm add -D -E auth@1.7.6
```

`auth`はschema生成・初期管理者作成に使う公式CLI。本体・Prisma adapter・CLIの版を揃える。
バージョンは[共通の依存管理方針](../base/pnpm-workspace.md)に従って選び、完全固定する。

`auth@1.7.6`の間接依存`semver@6.3.1`は、`trustPolicy: no-downgrade`で拒否されるため、上記CLIの導入には[依存単位の審査](../base/pnpm-workspace.md#例外の運用)が必要。信頼性チェックを一括で無効にしない。

```text
auth.config.ts
auth.cli.config.ts
src/
  auth/
    options.ts
    admin.ts
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
ユーザーの作成にはAdminプラグインを使い、初期管理者だけ公式CLIから作成する。

## 管理者の権限とユーザー作成時の検証

`src/auth/admin.ts`にAdminプラグインと共通の検証をまとめる。フォームから読み込む`options.ts`へ、サーバー側のプラグインを持ち込まない。

```ts
import { APIError, createAuthMiddleware } from "better-auth/api";
import { admin } from "better-auth/plugins";
import { createAccessControl } from "better-auth/plugins/access";
import { defaultStatements } from "better-auth/plugins/admin/access";
import { z } from "zod";
import { authOptions } from "./options";

const ac = createAccessControl(defaultStatements);
const roles = {
  admin: ac.newRole({ user: ["create", "list", "get"] }),
  user: ac.newRole({}),
};
const passwordSchema = z
  .string()
  .min(authOptions.emailAndPassword.minPasswordLength)
  .max(authOptions.emailAndPassword.maxPasswordLength);

export const adminOptions = {
  plugins: [admin({ ac, roles })],
  hooks: {
    before: createAuthMiddleware(async (ctx) => {
      if (ctx.path !== "/admin/create-user") return;
      if (!passwordSchema.safeParse(ctx.body?.password).success) {
        throw new APIError("BAD_REQUEST", {
          message: "Invalid password",
          code: "INVALID_PASSWORD",
        });
      }
    }),
  },
};
```

管理者にはユーザーの作成・一覧・取得だけを許可する。標準の管理者権限は広いため、利用する操作を明示する。一般ユーザーには管理操作を許可しない。
削除・停止・代理ログイン・ロール変更・パスワード変更は、必要になった時点で権限と操作方法を追加する。
`adminUserIds`は権限チェックを迂回するため指定しない。

Better Auth 1.7.6のAdminによるユーザー作成は、パスワード省略を許し、指定時も上限だけを検証する。メール・パスワード認証用のユーザーを作るため、before hookで必須・下限・上限を検証する。制約は`authOptions`を参照し、HTTP APIと初期管理者作成の両方に適用する。

この設定はCLIからも読み込むため、`server-only`は実行時の`server.ts`に置く。

## サーバー設定

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
import { adminOptions } from "./admin";
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
    ...adminOptions,
    baseURL: env.BETTER_AUTH_URL,
    secret: env.BETTER_AUTH_SECRET,
    database: prismaAdapter(getPrisma(), { provider: "postgresql" }),
  });
}
```
Prisma接続を使うため、組み込みDB接続部分を含まない`better-auth/minimal`からimportする。
認証インスタンスは遅延初期化して再利用し、import時に本番の秘密情報を要求しない。

## schemaの生成と適用

ルートの`auth.config.ts`はschema生成専用とし、共通設定だけを読み込む。

```ts
import { betterAuth } from "better-auth/minimal";
import { adminOptions } from "./src/auth/admin";
import { authOptions } from "./src/auth/options";

export const auth = betterAuth({ ...authOptions, ...adminOptions });
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

Adminプラグインが追加するフィールドも保持する。停止や代理ログインを使わなくても、プラグインが参照する標準schemaの一部なので削らない。

| モデル | フィールド | DBカラム |
| --- | --- | --- |
| User | `role` | `role` |
| User | `banned` | `banned` |
| User | `banReason` | `ban_reason` |
| User | `banExpires` | `ban_expires` |
| Session | `impersonatedBy` | `impersonated_by` |

`banReason`・`banExpires`・`impersonatedBy`には対応する`@map`を付ける。

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

## 初期管理者の作成

migration適用とPrisma Client生成を済ませてから、DBへ接続する`auth.cli.config.ts`をルートに置く。
`@next/env`は[環境変数の方針](env.md)に従って導入し、Next.jsと同じ規則で`.env*`を読む。
schema生成用の`auth.config.ts`と分け、生成時にはDB接続や秘密情報を要求しない。

```ts
import { prismaAdapter } from "@better-auth/prisma-adapter";
import { loadEnvConfig } from "@next/env";
import { PrismaPg } from "@prisma/adapter-pg";
import { betterAuth } from "better-auth/minimal";
import { z } from "zod";
import { adminOptions } from "./src/auth/admin";
import { authOptions } from "./src/auth/options";
import { PrismaClient } from "./src/prisma/generated/client";

loadEnvConfig(process.cwd());
const env = z
  .object({
    DATABASE_URL: z.string().min(1),
    BETTER_AUTH_URL: z.url(),
    BETTER_AUTH_SECRET: z.string().min(32),
  })
  .parse({
    DATABASE_URL: process.env.DATABASE_URL,
    BETTER_AUTH_URL: process.env.BETTER_AUTH_URL,
    BETTER_AUTH_SECRET: process.env.BETTER_AUTH_SECRET,
  });
const prisma = new PrismaClient({
  adapter: new PrismaPg({
    connectionString: env.DATABASE_URL,
    connectionTimeoutMillis: 5000,
  }),
});
export const auth = betterAuth({
  ...authOptions,
  ...adminOptions,
  baseURL: env.BETTER_AUTH_URL,
  secret: env.BETTER_AUTH_SECRET,
  database: prismaAdapter(prisma, { provider: "postgresql" }),
});
```

作成先DBの環境変数を設定して実行する。

```sh
pnpm exec auth create-admin \
  --config ./auth.cli.config.ts \
  --email admin@example.com \
  --name "管理者" \
  --role admin \
  --no-email-verified
```

パスワードは対話入力する。引数に載せず、シェル履歴へ残さない。
メール確認はしていないため、`--no-email-verified`を指定する。既存ユーザーがいる場合の確認も省略しない。

公式CLIはDB接続を持つ信頼された処理として管理APIを直接呼ぶため、管理者がまだいなくても作成できる。公開の新規登録APIを一時的に有効にする必要はない。

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
    "lengthRange": "{min, number}〜{max, number}文字で入力してください"
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
- [CLI・初期管理者の作成](https://better-auth.com/docs/concepts/cli)
- [Adminプラグイン・アクセス制御](https://better-auth.com/docs/plugins/admin)
- [Hooks](https://better-auth.com/docs/concepts/hooks)
- [Adminのユーザー作成実装（1.7.6）](https://github.com/better-auth/better-auth/blob/v1.7.6/packages/better-auth/src/plugins/admin/routes.ts)
- [Next.js連携](https://better-auth.com/docs/integrations/next)
- [設定オプション：disableSignUp](https://better-auth.com/docs/reference/options)
- [メール・パスワード認証](https://better-auth.com/docs/authentication/email-password)
- [セッション管理](https://better-auth.com/docs/concepts/session-management)
- [レート制限](https://better-auth.com/docs/concepts/rate-limit)
