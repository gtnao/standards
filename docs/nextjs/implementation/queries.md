# Queriesの方針

`src/queries`に、画面などへ返すデータをDBから取得する関数を置く。読み取り専用とし、主にServer Components・Route Handlerから呼び出す。

## 責務と依存関係

queriesはPrisma・domain・libを利用できる。app・components・usecasesには依存せず、usecasesからもqueriesを呼ばない。
入口から、表示用の取得はqueries、業務処理はusecasesへ振り分ける。
更新前の状態確認など、業務処理の一部として行う読み取りは[usecase内でPrismaを使う](prisma.md#usecasesでの利用)。

queriesはデータを返し、`notFound()`・redirect・表示文言は呼び出し元で扱う。
URL由来のIDは入口でDBの型に合う範囲まで検証する。例えばPostgreSQLの`Int`なら、正の整数であることに加えて`z.int32().positive()`で上限も検査する。
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
| `searchItems(input)` | 条件・ソート・ページを指定して取得 | `{ items, pagination }` |

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

## search

ページネーションを伴う取得は`search{Models}`にする。`By{Field}`は付けず、フィルター・ソート・ページ指定を`input`にまとめる。
配列の戻り値キーは対象のモデル名の複数形にする。例えば`searchItems`は`items`を返す。

URLやTanStack Tableの状態をそのまま受け取らず、アプリの検索条件を定義する。
検索条件はqueriesの入力契約として、`src/queries/item-search.ts`に定義する。[テーブル側](table.md)もこの定義を参照する。
このファイルはスキーマ・型・検索条件の定数だけを持ち、DB接続・`server-only`・URLや表示用ライブラリへ依存させない。
DBを実行する`src/queries/item.ts`は`server-only`を付けて分離し、Client Componentから実行時にimportしない。

`Item`に`id`・`name`・`status`がある場合の例。`src/queries/item-search.ts`：

```ts
import { z } from "zod";

export const searchTextMaxLength = 100;

export const itemSearchSchema = z.object({
  q: z.string().max(searchTextMaxLength).default(""),
  status: z.enum(["all", "active", "inactive"]).default("all"),
  sort: z.enum(["id", "name"]).default("id"),
  direction: z.enum(["asc", "desc"]).default("asc"),
  page: z.number().int().min(1).default(1),
});

export type ItemSearchInput = z.infer<typeof itemSearchSchema>;
```

状態などの許可値がdomainに定義済みなら、そのスキーマから導出し、検索側で列挙し直さない。
検索文字数は初期値の例。用途に合わせて決め、許可するフィールドと上限をサーバーでも検証する。
1ページの件数はqueries側で固定し、検索入力・URL・選択UIには含めない。取得結果の`pagination.pageSize`をTable側でも使う。
入力中の空白を消さないよう、`q`は入力値を保持し、検索の直前に前後の空白を除く。

`src/queries/item.ts`：

```ts
import "server-only";
import { itemSearchSchema, type ItemSearchInput } from "@/queries/item-search";
import { getPagination } from "@/queries/helpers/pagination";
import { escapeLikePattern } from "@/queries/helpers/like-pattern";
import { getPrisma } from "@/prisma/client";
import type { Prisma } from "@/prisma/generated/client";

const itemPageSize = 20;

const itemSummarySelect = {
  id: true,
  name: true,
  status: true,
} satisfies Prisma.ItemSelect;

export async function searchItems(input: ItemSearchInput) {
  const value = itemSearchSchema.parse(input);
  const q = value.q.trim();
  const literalQuery = escapeLikePattern(q);
  const where: Prisma.ItemWhereInput = {
    ...(q ? { name: { contains: literalQuery, mode: "insensitive" } } : {}),
    ...(value.status !== "all" ? { status: value.status } : {}),
  };
  const orderBy: Prisma.ItemOrderByWithRelationInput[] =
    value.sort === "name"
      ? [{ name: value.direction }, { id: "asc" }]
      : [{ id: value.direction }];

  return getPrisma().$transaction(async (tx) => {
    const totalItems = await tx.item.count({ where });
    const pagination = getPagination({ page: value.page, pageSize: itemPageSize, totalItems });
    const items = await tx.item.findMany({
      where,
      select: itemSummarySelect,
      orderBy,
      skip: (pagination.page - 1) * pagination.pageSize,
      take: pagination.pageSize,
    });
    return {
      items,
      pagination,
    };
  });
}
```

`where`は件数・一覧で共有する。所有者などの取得範囲が必要な場合も、認証済み情報から決めた条件を両方へ適用する。
URL由来の値をPrismaのフィールド名や`where`へ自由に展開せず、許可した条件へ明示的に対応させる。

### ページ計算の共通化

`src/queries/helpers/pagination.ts`に件数・ページ補正と戻り値の型をまとめる。
モデル名・DBアクセス・URL操作は持ち込まず、検証済みの数値から計算する。

```ts
export type Pagination = {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
};

type Input = Pick<Pagination, "page" | "pageSize" | "totalItems">;

export function getPagination(input: Input): Pagination {
  const totalPages = Math.ceil(input.totalItems / input.pageSize);
  return {
    page: Math.min(input.page, Math.max(1, totalPages)),
    pageSize: input.pageSize,
    totalItems: input.totalItems,
    totalPages,
  };
}
```

各queriesは、この計算結果から`skip`・`take`を決める。
フィルター・取得カラム・並び順・トランザクションは対象ごとのqueriesに残す。PrismaのモデルAPIを引数に取る汎用検索関数にはまとめない。

### ソートと文字列検索

ソートは単一列を基本とし、同値の行を一意なIDで並べる。これにより、同じ値を持つ行の順序が不定になることを防ぐ。
任意のリクエスト間でデータを固定するものではなく、追加・削除・更新でページの構成は変わり得る。

文字列検索は大文字小文字を区別しない部分一致から始める。
PostgreSQLのLIKE系検索では`%`・`_`が特殊な意味を持つため、通常の文字として探す場合はバックスラッシュと合わせてエスケープする。
検索条件の組み立てを補助する処理として、`src/queries/helpers/like-pattern.ts`で共有する。

```ts
export function escapeLikePattern(value: string): string {
  return value.replace(/[\\%_]/g, "\\$&");
}
```

これは検索の意味を揃える処理であり、SQLを文字列連結で組み立てるものではない。

### ページと件数

ページ番号を指定する一覧には`skip`・`take`を使う。深いページや全件数の計算は負荷が増えるため、データ量に応じてインデックス・検索方法・カーソル方式を見直す。

| 状態 | 戻り値と扱い |
| --- | --- |
| 該当あり | 指定ページの配列と、フィルター適用後の総件数・総ページ数 |
| 該当なし | `items: []`・`page: 1`・`totalItems: 0`・`totalPages: 0` |
| 最終ページ超過 | 最終ページへ補正し、実際の`page`を返す。URLの補正は入口で行う |

トランザクションの分離レベルはDBの設定に従い、通常の一覧検索では上書きしない。
PostgreSQLの既定値は`Read Committed`で、同じトランザクション内でもSELECT間の追加・削除が結果に反映され得る。通常の一覧では、この変動を許容する。
この例は件数からページを補正してから一覧を取得するため、順番に実行する。

## 参考

- [Prisma 7：ページネーション](https://www.prisma.io/docs/orm/v7/prisma-client/queries/pagination)
- [Prisma 7：フィルターとソート](https://www.prisma.io/docs/orm/v7/prisma-client/queries/filtering-and-sorting)
- [Prisma 7：トランザクション](https://www.prisma.io/docs/orm/v7/prisma-client/queries/transactions)
- [PostgreSQL：トランザクション分離](https://www.postgresql.org/docs/current/transaction-iso.html)
