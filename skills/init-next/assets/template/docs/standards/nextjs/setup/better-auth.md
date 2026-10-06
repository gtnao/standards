# Better Authの初期設定

Adminプラグインで管理者がユーザーを作成し、メール・パスワードによるログイン・ログアウトと、DBに保存するセッションを用意する。
テナントを持たない構成として、Organizationプラグインは使わない。メール確認・パスワード再設定は後から追加する。

[利用時の方針](../implementation/better-auth.md)も参照する。

## 依存と配置

[Prisma](prisma.md)・[Mantine](mantine.md)・[React Hook Form](../implementation/react-hook-form.md)・[i18n](i18n.md)の設定を引き継ぐ。

```sh
pnpm add -E better-auth@1.7.6 @better-auth/prisma-adapter@1.7.6
pnpm add -D -E auth@1.7.6
```

`auth`はschema生成・初期管理者作成に使う公式CLI。本体・Prisma adapter・CLIの版を揃える。
バージョンは[共通の依存管理方針](../../base/pnpm-workspace.md)に従って選び、完全固定する。

本体とPrisma adapterは例外なしで導入できる。CLIの`auth@1.7.6`だけは、間接依存の`semver@6.3.1`が[`trustPolicy: no-downgrade`](../../base/pnpm-workspace.md#trustpolicy)で拒否され、次のエラーで止まる。

```text
High-risk trust downgrade for "semver@6.3.1" (possible package takeover)
```

2026年10月6日にレジストリの情報を確認した結果は次のとおり。

| 確認項目 | 内容 |
| --- | --- |
| 経路 | CLIが使うBabel（`@babel/core`など）が`semver@^6.3.1`を要求する。アプリの実行時依存には入らない |
| 検出理由 | 公開元の証明が付いた7.5系より後の2023年7月10日に、6系の保守版として証明なしで公開された。[別メジャー間の公開方法の違い](../../base/pnpm-workspace.md#trustpolicy)に当たる |
| 公開元・内容 | `npm/node-semver`のリポジトリ、`latest-6`タグ。install scriptと依存はない |

この内容を導入時にも確認したうえで、[例外の運用](../../base/pnpm-workspace.md#例外の運用)に従い、この版だけを`pnpm-workspace.yaml`で除外する。

```yaml
trustPolicyExclude:
  # Better AuthのCLI（auth@1.7.6）が使うBabel経由で解決される。
  # 6系の保守版が、証明付きの7系より後に証明なしで公開されたための検出。
  # CLIがこの版を解決しなくなったら削除する。
  - "semver@6.3.1"
```

パッケージ名だけの除外や`trustPolicy`自体の無効化はしない。CLIやBabelを更新して解決される版が変わったら、例外を引き継がずに確認し直す。

```text
auth.schema.config.ts
auth.admin.config.ts
src/
  auth/
    options.ts
    admin.ts
    server.ts
    client.ts
  app/
    api/auth/[...all]/route.ts
    sign-in/
      page.tsx
      _components/auth-form.tsx
      _helpers/form-schema.ts
```

アプリ固有の認証設定なので、汎用処理用の`lib`ではなく`src/auth`にまとめる。
usecasesには認証済みユーザーのIDなどを引数で渡し、Next.jsのheadersやCookieを持ち込まない。

ファイルは実行環境・利用元の境界で分ける。短い補助関数ごとには分割しない。

| ファイル | 分ける理由 |
| --- | --- |
| `server.ts` | Next.jsのサーバー専用。認証インスタンス・セッション取得・未認証時のリダイレクトをまとめる |
| `client.ts` | ブラウザーから認証APIを呼ぶクライアント |
| `options.ts` | サーバー・CLIで共有し、ブラウザーから参照してもよい設定。秘密情報やサーバー実装を含めない |
| `admin.ts` | サーバーとCLIで共有するAdminプラグイン・権限・検証。ブラウザー用の設定から分離する |

ルートの2ファイルは、公式CLIへ`--config`で渡すための設定。アプリの認証インスタンスは`src/auth/server.ts`であり、これらをアプリからimportしない。
`src/`の外に置いてアプリのコード・Dockerのビルド対象と区別し、名前で用途を分ける。

| ファイル | 用途 |
| --- | --- |
| `auth.schema.config.ts` | schemaの生成。共通設定だけを読み込み、DB接続・秘密情報を要求しない |
| `auth.admin.config.ts` | 初期管理者の作成。DBへ接続し、リクエストの認証を経ずに管理APIを呼べる |

設定ファイルのパスと固定の引数は、`package.json`のscriptsにまとめる。実行時には、都度変わる引数だけを渡す。

```json
{
  "scripts": {
    "auth:generate": "auth generate --config ./auth.schema.config.ts --adapter prisma --dialect postgresql",
    "auth:create-admin": "auth create-admin --config ./auth.admin.config.ts"
  }
}
```

## 設定と環境変数

`src/auth/options.ts`は、認証処理・schema生成で共有する設定。Next.jsのサーバー専用処理や環境変数へ依存させず、秘密情報は`server.ts`で追加する。
パスワード長はここだけで定義し、ユーザー作成時の検証も同じ値を参照する。ユーザー作成・パスワード変更のフォームで条件を示す場合もここから読む。[ログインフォーム](../implementation/better-auth.md#最小のフォーム)では長さを検証しない。

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

`src/auth/admin.ts`にAdminプラグインと共通の検証をまとめる。ブラウザー側からも読み込める`options.ts`へ、サーバー側のプラグインを持ち込まない。

```ts
import { APIError, createAuthMiddleware } from "better-auth/api";
import type { BetterAuthOptions } from "better-auth/minimal";
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
    // Admin user creation accepts a missing or short password by default.
    before: createAuthMiddleware(async (ctx) => {
      if (ctx.path !== "/admin/create-user") {
        return;
      }
      if (!passwordSchema.safeParse(ctx.body?.password).success) {
        throw new APIError("BAD_REQUEST", {
          message: "Invalid password",
          code: "INVALID_PASSWORD",
        });
      }
    }),
  },
} satisfies BetterAuthOptions;
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
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { getServerEnv } from "@/env/server";
import { getPrisma } from "@/prisma/client";
import { adminOptions } from "./admin";
import { authOptions } from "./options";

let auth: ReturnType<typeof createAuth> | undefined;

export function getAuth() {
  auth ??= createAuth();
  return auth;
}

export async function getSession() {
  // Read the request first so that Next.js treats this as request-time work
  // before the auth settings read secrets from the environment.
  const requestHeaders = await headers();
  return getAuth().api.getSession({ headers: requestHeaders });
}

export async function requireSession() {
  const session = await getSession();
  if (session == null) {
    redirect("/sign-in");
  }
  return session;
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

## APIの接続

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

## schemaの生成と適用

ルートの`auth.schema.config.ts`はschema生成専用とし、共通設定だけを読み込む。

```ts
import { betterAuth } from "better-auth/minimal";
import { adminOptions } from "./src/auth/admin";
import { authOptions } from "./src/auth/options";

export const auth = betterAuth({ ...authOptions, ...adminOptions });
```
```sh
pnpm run auth:generate
```

scriptで`--adapter prisma`を指定しているため、DB接続や生成済みPrisma Clientなしでschemaを生成できる。
実行時の`server-only`モジュールはCLIから読み込まない。CLI用設定を認証APIの実行に使わない。

生成される基本モデルは`User`・`Session`・`Account`・`Verification`。
[Prismaの命名規則](../implementation/prisma.md#schemaの命名)に合わせ、テーブル名を`users`・`sessions`・`accounts`・`verifications`へ`@@map`する。
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

migration適用とPrisma Client生成を済ませてから、DBへ接続する`auth.admin.config.ts`をルートに置く。
`@next/env`は[環境変数の方針](env.md)に従って導入し、Next.jsと同じ規則で`.env*`を読む。
schema生成用の`auth.schema.config.ts`と分け、生成時にはDB接続や秘密情報を要求しない。

```ts
import { prismaAdapter } from "@better-auth/prisma-adapter";
import nextEnv from "@next/env";
import { PrismaPg } from "@prisma/adapter-pg";
import { betterAuth } from "better-auth/minimal";
import { z } from "zod";
import { adminOptions } from "./src/auth/admin";
import { authOptions } from "./src/auth/options";
import { PrismaClient } from "./src/prisma/generated/client";

nextEnv.loadEnvConfig(process.cwd(), process.env.NODE_ENV !== "production");

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
    connectionTimeoutMillis: 5_000,
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
pnpm run auth:create-admin \
  --email admin@example.com \
  --name "管理者" \
  --role admin \
  --no-email-verified
```

パスワードは対話入力する。引数に載せず、シェル履歴へ残さない。
メール確認はしていないため、`--no-email-verified`を指定する。既存ユーザーがいる場合の確認も省略しない。

公式CLIはDB接続を持つ信頼された処理として管理APIを直接呼ぶため、管理者がまだいなくても作成できる。公開の新規登録APIを一時的に有効にする必要はない。

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
