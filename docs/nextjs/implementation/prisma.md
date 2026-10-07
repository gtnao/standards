# Prismaの利用方針

[導入と設定](../setup/prisma.md)を前提とする。

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

### 種別と種別ごとのテーブル

種別を表すフィールドは`kind`と命名し、`type`は使わない。`type`はTypeScriptやライブラリの名前と重なりやすく、検索や補完で紛れる。

種別はDBのenumにせず、`String`で保存する。許可する値はdomainで定義し、入力の検証とTypeScriptの型に使う。

```ts
import { z } from "zod";

export const connectionKindSchema = z.enum(["trocco"]);

export type ConnectionKind = z.output<typeof connectionKindSchema>;
```

PostgreSQLのenumは値の追加は軽いが、値の削除は型を作り直してテーブル全体を書き換えるマイグレーションになる。Prismaもその形のSQLを生成する。
大きなテーブルでは長いロックになるため、種別の増減をDBの型変更にしない。DB側で値を制約しない代わりに、書き込みは必ずdomainの定義を通す。

種別によって項目が異なるレコードは、共通項目と`kind`を持つ親テーブルと、種別ごとの子テーブルに分ける。
子テーブル名は`<親の単数形>_<種別>_<内容>`の複数形にし、接頭辞で親との対応が分かるようにする。
子テーブルは親の`id`を主キー兼外部キーにし、親の削除で一緒に消す。

外部サービスへの接続情報の例：

```prisma
model Connection {
  id        String   @id @default(uuid(7))
  name      String
  // Allowed values are defined in the domain, not as a database enum.
  kind      String
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  troccoSetting ConnectionTroccoSetting?

  @@map("connections")
}

model ConnectionTroccoSetting {
  connectionId String     @id @map("connection_id")
  connection   Connection @relation(fields: [connectionId], references: [id], onDelete: Cascade)
  // Encrypted with SecretCipher; the JSON holds every parameter needed to decrypt.
  apiKeyEnc    Json       @map("api_key_enc")
  createdAt    DateTime   @default(now()) @map("created_at")
  updatedAt    DateTime   @updatedAt @map("updated_at")

  @@map("connection_trocco_settings")
}
```

秘匿情報を含むカラムは、[秘匿情報の保存](../../base/secret-storage.md)に従って暗号化したJSONを置き、`_enc`の接尾辞を付ける。

## 依存関係の例外

| 利用する側 | 許可するもの |
| --- | --- |
| 入口・queries・usecases | Prismaによるクエリ・トランザクションと生成型 |
| domain | Prismaが生成した型。DB接続・クエリ実行は持ち込まない |
| Client Components | 必要な生成型やbrowser-safeなenum。クライアント生成モジュールは参照しない |

PrismaのAPIを隠すだけのrepository・portは作らない。
Next.jsと[別プロセスのWorker](../setup/worker.md#nextjsとの共有部分)で共有する場合は、クライアント生成部分を切り出し、Workerから`server-only`付きのモジュールをimportしない。
生成型は`generated/models`、enumは`generated/enums`など責務に合う公開エントリーから参照し、`generated/internal`には依存しない。
`src/prisma`からqueries・usecases・domainへ逆向きに依存させない。

## usecasesでの利用

更新の可否判断や更新対象の確認もusecaseの責務として扱い、表示用の[queries](queries.md)を経由しない。
一体として成功・失敗させる処理はトランザクションにまとめ、その中では同じクライアントを使う。

`Post`に`id`・`authorId`・`published`がある場合の例：

```ts
import { getPrisma } from "@/prisma/client";

type Args = {
  input: { id: string; authorId: string };
};

export async function publishPost({ input }: Args) {
  return getPrisma().$transaction(async (tx) => {
    const post = await tx.post.findUnique({
      where: { id: input.id },
      select: { authorId: true, published: true },
    });
    if (post == null || post.authorId !== input.authorId || post.published) {
      return false;
    }

    const result = await tx.post.updateMany({
      where: { id: input.id, authorId: input.authorId, published: false },
      data: { published: true },
    });
    return result.count === 1;
  });
}
```

入口からは認証・入力検証を済ませた値を渡す。所有者のIDはフォームの自己申告値を使わず、認証済みユーザーから決める。

トランザクション内の処理を補助関数へ分ける場合は、`tx`を渡す。
補助関数から別の接続を取得したり、独立したトランザクションを開始したりしない。

読み取った時点の状態は同時更新で変わり得るため、更新時にも必要な条件を含め、DBの一意制約などと合わせて整合性を守る。
例では所有者・未公開の条件を更新時にも確認する。処理によって分離レベルや競合時の再試行も検討する。
トランザクションは短く保ち、外部APIへの通信などを中へ持ち込まない。

## 参考

- [Prisma 7：トランザクション](https://www.prisma.io/docs/orm/v7/prisma-client/queries/transactions)

- [DBのテーブル名・カラム名とPrismaの名前の対応](https://www.prisma.io/docs/orm/v7/prisma-schema/data-model/database-mapping)

- [Prisma 7：migrate devとcreate-only](https://docs.prisma.io/docs/cli/v7/migrate/dev)
- [create-only実行時の既存マイグレーションの適用](https://github.com/prisma/prisma/issues/11184)

- [Prisma 7：PostgreSQLへの導入](https://www.prisma.io/docs/v7/prisma-orm/quickstart/postgresql)
- [Prisma Clientの生成設定と型](https://www.prisma.io/docs/orm/v7/prisma-schema/overview/generators)
- [CLI設定](https://www.prisma.io/docs/orm/v7/reference/prisma-config-reference)
- [接続の再利用](https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections)
- [接続プール](https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections/connection-pool)
- [開発と本番のマイグレーション](https://www.prisma.io/docs/orm/v7/prisma-migrate/workflows/development-and-production)
