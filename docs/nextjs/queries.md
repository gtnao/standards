# Queriesの方針

`src/queries`に、画面などへ返すデータをDBから取得する関数を置く。読み取り専用とし、主にServer Components・Route Handlerから呼び出す。

## 責務と依存関係

queriesはPrisma・domain・libを利用できる。app・components・usecasesには依存せず、usecasesからもqueriesを呼ばない。
入口から、表示用の取得はqueries、業務処理はusecasesへ振り分ける。
更新前の状態確認など、業務処理の一部として行う読み取りは[usecase内でPrismaを使う](prisma.md#usecasesでの利用)。

queriesはデータを返し、`notFound()`・redirect・表示文言は呼び出し元で扱う。
読み取り専用でもアクセス制御は必要。入口で認証・権限を確認し、所有者などの取得範囲は信頼できる情報から決めて条件に含める。

## 配置と命名

`src/queries/user.ts`のように、モデル名のkebab-caseでまとめる。大きくなったら処理のまとまりに合わせて分割する。
補助関数はまず同じファイルに置き、共有が必要になったものだけ切り出す。

| 命名 | 用途 | 戻り値 |
| --- | --- | --- |
| `findUser({ id })` | IDで1件取得 | `T \| null` |
| `findUserByEmail({ email })` | ID以外の条件で1件取得 | `T \| null` |
| `listUsers()` | 複数件取得 | `T[]` |
| `listPostsByAuthorId({ authorId })` | 条件に一致する複数件取得 | `T[]` |

条件は`input`オブジェクトで受け取り、条件がなければ引数なしにする。
`ById`・`All`は付けない。同じモデルで取得する関連データの異なる関数が複数できた場合は、`With{X}`で区別する。
該当なしは`null`・空配列で表し、DB接続エラーなどを該当なしとして扱わない。

## 取得内容と型

`select`・`include`は名前付き定数にし、Prismaの型に対する`satisfies`で検査する。
定数名は取得内容に合わせ、同じ形ならfind/listで共有する。必要なカラムだけを返す場合は`select`を使う。
戻り値の型は取得定義から導出し、フィールドを手書きで重複定義しない。外部から型名を参照する必要がある場合だけexportする。

`src/queries/user.ts`の例。`User`に`id`・`name`がある場合：

```ts
import "server-only";
import { getPrisma } from "@/prisma/client";
import type { Prisma } from "@/prisma/generated/client";

const userSummarySelect = {
  id: true,
  name: true,
} satisfies Prisma.UserSelect;

type UserSummary = Prisma.UserGetPayload<{
  select: typeof userSummarySelect;
}>;

export async function findUser(input: { id: string }): Promise<UserSummary | null> {
  return getPrisma().user.findUnique({
    where: { id: input.id },
    select: userSummarySelect,
  });
}

export async function listUsers(): Promise<UserSummary[]> {
  return getPrisma().user.findMany({
    select: userSummarySelect,
    orderBy: { id: "asc" },
  });
}
```

並び順に意味があるlistは`orderBy`を明示する。DBの返却順には依存しない。
全件取得は件数が十分小さい用途に使い、増え続けるデータを無条件で取得しない。
