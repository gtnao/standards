# Prismaの初期設定

PostgreSQLへのアクセスと型生成にPrismaを使い、スキーマ変更はPrisma Migrateで管理する。
Prismaは`adapters`配置の例外とし、`src/prisma/`にまとめる。

## 導入と配置

```sh
pnpm add -D -E prisma@7.9.1
pnpm add -E @prisma/client@7.9.1 @prisma/adapter-pg@7.9.1 pg@8.23.0
```

CLI用の環境変数読み込みに`@next/env`も開発依存へ追加し、Next.jsと同じ版に揃える。Zodは[環境変数の共通設定](env.md)で導入したものを使う。

2026年10月3日の検証では、最新安定版の`prisma@7.10.0`は公開元の証明が以前の版より弱く、[共通の信頼性検証](../base/pnpm-workspace.md#trustpolicy)で拒否された。
そのため、例外を追加せず7.9.1へ揃える。導入時には、待機期間・信頼性検証・互換性を満たす版を改めて確認する。
`prisma@latest`は同日時点で8系のRC版を指すため、そのまま指定しない。

```text
prisma/
  schema.prisma
  migrations/
prisma.config.ts
src/
  prisma/
    client.ts
    generated/
```

`prisma/schema.prisma`の生成設定と接続先種別：

```prisma
generator client {
  provider     = "prisma-client"
  output       = "../src/prisma/generated"
  moduleFormat = "esm"
}

datasource db {
  provider = "postgresql"
}
```

実際に扱うモデルをこのschemaへ追加する。旧`prisma-client-js`ではなく、出力先を明示する`prisma-client`を使う。
生成コードは手編集せず、`.gitignore`に`/src/prisma/generated/`を追加する。schemaとmigrationsはGit管理する。

## schemaの命名

DBのテーブル名はsnake_case・複数形、カラム名はsnake_caseにする。
Prismaのモデル名は単数形のPascalCase、フィールド名はlowerCamelCaseを使い、DB上の名前と分ける。

```prisma
model UserProfile {
  id          String @id
  displayName String @map("display_name")

  @@map("user_profiles")
}
```

各モデルに`@@map`を明示し、DB上の名前が異なるフィールドには`@map`を付ける。`id`など同じ名前のフィールドへの`@map`は不要。
リレーションフィールド自体はカラムではないため、`@map`は付けない。外部キーのスカラーフィールドは同じ命名方針に従う。
外部ライブラリのCLIが生成したモデルも、マイグレーションSQLを作る前にこの規則へ揃える。

## CLIの設定と環境変数

`prisma.config.ts`：

```ts
import { loadEnvConfig } from "@next/env";
import { defineConfig } from "prisma/config";
import { z } from "zod";

loadEnvConfig(process.cwd());
const databaseUrl = z.string().min(1).optional().parse(process.env.DATABASE_URL);
export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: { path: "prisma/migrations" },
  ...(databaseUrl ? { datasource: { url: databaseUrl } } : {}),
});
```

Next.js外で動くCLIでも[同じ環境変数の読み込み規則](env.md)を使うため、`@next/env`で読み込む。
`server-only`付きの環境変数モジュールはCLIからimportしない。

`prisma generate`はDB接続を必要としないため、CLI設定ではURLの未指定を許す。接続が必要なマイグレーションではURLがなければエラーになる。
ダミーの本番URLや秘密情報を、型生成のためだけにCI・Dockerへ渡さない。

7.10以降のCLIは`prisma7.config.ts`を生成するが、今回検証する7.9.1では`prisma.config.ts`を使う。設定ファイル名も採用版に合わせる。

[ローカルのPostgreSQL](../base/docker-compose.md)には、ルートの`.env`から接続する。

```dotenv
DATABASE_URL=postgresql://app:local-password@127.0.0.1:5432/app
```

ポートを変更したらURLも合わせる。実際の接続先は`.env.example`にも説明し、本番の認証情報は実行環境から渡す。
アプリの`src/env/server.ts`では、`DATABASE_URL: z.string().min(1)`として必須検証し、`process.env.DATABASE_URL`を明示的に読み取る。

## クライアントの生成と再利用

`src/prisma/client.ts`：

```ts
import "server-only";
import { PrismaPg } from "@prisma/adapter-pg";
import { getServerEnv } from "@/env/server";
import { PrismaClient } from "./generated/client";

const globalForPrisma = globalThis as typeof globalThis & {
  prisma?: PrismaClient;
};
let client: PrismaClient | undefined;

export function getPrisma() {
  if (client) return client;
  if (globalForPrisma.prisma) {
    client = globalForPrisma.prisma;
    return client;
  }

  const { DATABASE_URL } = getServerEnv();
  client = new PrismaClient({
    adapter: new PrismaPg({
      connectionString: DATABASE_URL,
      connectionTimeoutMillis: 5_000,
    }),
  });
  if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = client;
  return client;
}
```

呼び出し時に環境変数を検証し、プロセス内では同じクライアントを再利用する。
開発時は`globalThis`にも保持し、ホットリロードで接続プールが増えることを防ぐ。リクエストごとに`$disconnect()`しない。

`connectionTimeoutMillis: 5_000`は、接続・プール取得を無期限に待たせないための初期値。サービスの応答時間に合わせて調整する。
接続数はドライバー側で管理される。インスタンス数が増えたら、プールの`max`とDB全体の接続上限を合わせて見直す。

遅延生成しても、静的ページの描画からクエリを実行すればビルド中にDBへ接続する。
リクエスト時に読むデータは、動的なページやRoute Handlerから呼ぶ。

## 依存関係の例外

| 利用する側 | 許可するもの |
| --- | --- |
| 入口・usecases | Prismaによるクエリ・トランザクションと生成型 |
| domain | Prismaが生成した型。DB接続・クエリ実行は持ち込まない |
| Client Components | 必要な生成型やbrowser-safeなenum。クライアント生成モジュールは参照しない |

PrismaのAPIを隠すだけのrepository・portは作らない。
生成型は`generated/models`、enumは`generated/enums`など責務に合う公開エントリーから参照し、`generated/internal`には依存しない。
`src/prisma`からusecases・domainへ逆向きに依存させない。

## 生成とマイグレーション

既存のscriptsへ次を反映する。

```json
{
  "scripts": {
    "db:generate": "prisma generate",
    "db:migrate": "prisma migrate dev --create-only",
    "db:deploy": "prisma migrate deploy",
    "dev": "pnpm run db:generate && next dev",
    "typecheck": "pnpm run db:generate && next typegen && tsc --noEmit",
    "build": "pnpm run db:generate && next build"
  }
}
```

インストール時の自動生成に依存せず、起動・型チェック・ビルドの前に生成する。
依存のinstall scriptは[共通方針](../base/pnpm-workspace.md#strictdepbuilds)に従い、実際の内容を確認して個別に許可する。
今回確認した版では、既存の`allowBuilds`へ次を追加する。

```yaml
allowBuilds:
  "prisma@7.9.1": true
  "@prisma/engines@7.9.1": true
```

前者はNode.jsの対応版チェック、後者はCLIが使うSchema Engineの取得を行う。更新時は対象版の内容を再確認する。

開発時はschemaを変更し、必ず`--create-only`でマイグレーションSQLを作成する。生成と適用を分け、人間がSQLを確認できる段階を設ける。

```sh
docker compose up -d --wait
pnpm run db:migrate --name init
```

生成された`migration.sql`を確認・必要に応じて修正してから、開発DBへ適用する。

```sh
pnpm run db:deploy
pnpm run db:generate
```

`db:deploy`は本番専用ではなく、作成済みのSQLを適用するコマンドとして開発でも使う。
`--create-only`でも既存の未適用マイグレーションは適用され得るため、未確認のSQLを残したまま次の`db:migrate`を実行しない。
共有済み・適用済みのマイグレーションは編集せず、次のマイグレーションを追加する。履歴を残す運用では`db push`を通常の変更手順にしない。

本番はデプロイ工程で、レビュー済みのマイグレーションだけを適用する。

```sh
pnpm run db:deploy
```

本番で`migrate dev`やresetを使わない。アプリの起動コマンドにはマイグレーションを混ぜず、デプロイ時の独立した処理にする。

## CIとDocker

既存CIの`typecheck`・`build`から生成が実行される。schemaからの型生成だけなら、DBや接続情報をCIに追加する必要はない。

[Dockerの許可リスト](docker.md#dockerignore)へ、他の許可項目と合わせて次を追加する。

```dockerignore
!prisma/
!prisma/**
!prisma.config.ts
```

末尾の除外項目には`src/prisma/generated/`を追加し、`.env`類の除外も維持する。
ローカルの生成物をコピーせず、イメージ内の`pnpm run build`で生成する。生成はソース・schema・CLI設定をコピーした後に行う。

アプリのstandaloneイメージとマイグレーションの実行環境は役割が異なる。
マイグレーションを実行するデプロイジョブには、Prisma CLIを含む依存・CLI設定・schema・migrationsを用意する。standaloneイメージにCLIまで含まれるとは扱わない。

## 検証範囲

2026年10月3日、Node.js 24.21.0・Next.js 16.3.6・Prisma 7.9.1・PostgreSQL 18.6のLinux arm64環境で確認した。
共通のpnpm設定を維持したインストール、クライアント生成、型チェック、`migrate dev`・`migrate deploy`が成功した。
DB接続情報なしでNext.js・Dockerをビルドし、standaloneイメージからPostgreSQLへの書き込み・読み取りも確認した。

## 参考

- [DBのテーブル名・カラム名とPrismaの名前の対応](https://www.prisma.io/docs/orm/v7/prisma-schema/data-model/database-mapping)

- [Prisma 7：migrate devとcreate-only](https://docs.prisma.io/docs/cli/v7/migrate/dev)
- [create-only実行時の既存マイグレーションの適用](https://github.com/prisma/prisma/issues/11184)

- [Prisma 7：PostgreSQLへの導入](https://www.prisma.io/docs/v7/prisma-orm/quickstart/postgresql)
- [Prisma Clientの生成設定と型](https://www.prisma.io/docs/orm/v7/prisma-schema/overview/generators)
- [CLI設定](https://www.prisma.io/docs/orm/v7/reference/prisma-config-reference)
- [接続の再利用](https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections)
- [接続プール](https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections/connection-pool)
- [開発と本番のマイグレーション](https://www.prisma.io/docs/orm/v7/prisma-migrate/workflows/development-and-production)
