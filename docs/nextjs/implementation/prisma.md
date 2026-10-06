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

## 依存関係の例外

| 利用する側 | 許可するもの |
| --- | --- |
| 入口・queries・usecases | Prismaによるクエリ・トランザクションと生成型 |
| domain | Prismaが生成した型。DB接続・クエリ実行は持ち込まない |
| Client Components | 必要な生成型やbrowser-safeなenum。クライアント生成モジュールは参照しない |

PrismaのAPIを隠すだけのrepository・portは作らない。
Next.jsと[別プロセスのWorker](../../base/async-jobs.md#nextjsとの共有部分)で共有する場合は、クライアント生成部分を切り出し、Workerから`server-only`付きのモジュールをimportしない。
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
    if (!post || post.authorId !== input.authorId || post.published) {
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
