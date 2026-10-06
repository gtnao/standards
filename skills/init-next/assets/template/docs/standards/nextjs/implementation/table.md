# テーブル表示と検索状態

Mantineで表示し、TanStack Tableで列・ソート・ページ操作、nuqsでURLとの同期を扱う。
検索・ソート・ページ分割は[queries](queries.md#search)でDB側に適用し、Server Componentから結果を渡す。

```text
画面操作 → nuqsでURL更新 → Server Component → queries → テーブルへ結果を渡す
```

[Providerと依存の導入](../setup/table.md)を済ませてから実装する。

## 配置

```text
src/
  components/
    data-table/
      data-table.tsx
      features.ts
      use-table-search.ts
    search-input.tsx
    empty-content.tsx
  queries/
    item-search.ts
    item.ts
    helpers/
      pagination.ts
      like-pattern.ts
  app/
    _helpers/
      search-params.ts
      to-search-params.ts
    items/
      page.tsx
      _helpers/search-params.ts
      _components/items-table.tsx
```

責務の持ち主で配置を決める。検索条件はqueriesの入力契約、URLへの変換は入口、入力・表示・操作はUIの責務とする。
共有すること自体を理由にdomainへ置かない。
同じ変更を各ページで繰り返す部分を共通化し、列・フィルターの意味・DBクエリは対象ごとに残す。

| 配置 | 責務・受け渡すもの |
| --- | --- |
| `components/data-table/data-table.tsx` | 行・列・総件数・制御されたソート／ページ状態・変更ハンドラー・更新待ち状態を受け取る。Tableの初期化、Mantineでの描画、ページ操作、空表示、アクセシビリティをまとめる |
| `components/data-table/features.ts` | 各画面の列定義と共通テーブルが使うTanStackのfeature構成を共有する |
| `components/data-table/use-table-search.ts` | ページのparserと取得済み結果の検索条件を受け取る。nuqs、履歴、ページリセット、Tableの変更ハンドラー、更新待ち判定をまとめる |
| `components/empty-content.tsx` | MantineのEmptyStateで空状態のアイコン・見出し・説明を統一する。翻訳済みの文言を受け取る |
| `components/search-input.tsx` | 入力中の値・検索ボタン・Enterを扱う。値・ラベル・文字数上限・検索コールバックを受け取り、URLや特定モデルへ依存しない |
| `app/_helpers/search-params.ts` | Zodからnuqs parserを作る処理と数値のデコード。特定の検索キーや既定値を持たない |
| `app/_helpers/to-search-params.ts` | Next.jsの検索パラメーターを`URLSearchParams`へ変換し、リダイレクト時に既存の値を保持する |
| `queries/helpers/pagination.ts` | [ページ計算](queries.md#ページ計算の共通化)と戻り値の型。React・nuqs・Prismaへ依存しない |
| `queries/item-search.ts` | その対象で許可する検索条件・ソートキー・上限・既定値 |
| `queries/item.ts` | select・where・orderByとDB検索。画面部品へ依存しない |
| ページの`_helpers/search-params.ts` | 検索条件とURLキーの対応、loader・serializerの定義 |
| ページの`_components/items-table.tsx` | 列・セル・固有のフィルターを定義し、共通hookと共通テーブルを接続する |

`DataTable`はnuqs・特定のqueries・モデル名を知らず、propsとコールバックで動く。
共通hookも`status`など固有条件の意味を持たず、渡されたparserで型と許可値を扱う。
フィルターUIはページ側で組み立てる。業務条件を設定オブジェクトへ詰め込んだ汎用フォーム生成器にはしない。

データ取得はServer Componentで行うため、この構成のためだけに取得用Route HandlerやTanStack Queryは追加しない。

## URLの解析と検証

```text
/items?q=sample&status=active&sort=name&direction=asc&page=2
```

URLは確定した検索状態の基準にする。ページは1始まりとし、TanStack Tableの`pageIndex`との境界でだけ変換する。
既定値はURLから省き、不正な値はその項目の既定値へ戻す。ソートキーは許可した値に限定する。1ページの件数はqueries側の固定値を使い、URLには含めない。

nuqsの解析だけでは値の範囲を保証しないため、[検索条件のZodスキーマ](queries.md#search)をparserにも使う。
変換処理は`src/app/_helpers/search-params.ts`に共通化する。

```ts
import { createParser } from "nuqs/server";
import { z } from "zod";

export function createSearchParser<T extends string | number>(
  schema: z.ZodType<T>,
  decode: (value: string) => unknown = (value) => value,
) {
  return createParser({
    parse: (value) => {
      const result = schema.safeParse(decode(value));
      return result.success ? result.data : null;
    },
    serialize: String,
  });
}

export function decodeInteger(value: string) {
  return /^[1-9]\d*$/.test(value) ? Number(value) : null;
}
```

ページの`src/app/items/_helpers/search-params.ts`には対応関係だけを置く。

```ts
import { createLoader, createSerializer } from "nuqs/server";
import { itemSearchSchema } from "@/queries/item-search";
import { createSearchParser, decodeInteger } from "@/app/_helpers/search-params";

const defaults = itemSearchSchema.parse({});
const shape = itemSearchSchema.shape;

export const searchParsers = {
  q: createSearchParser(shape.q).withDefault(defaults.q),
  status: createSearchParser(shape.status).withDefault(defaults.status),
  sort: createSearchParser(shape.sort).withDefault(defaults.sort),
  direction: createSearchParser(shape.direction).withDefault(defaults.direction),
  page: createSearchParser(shape.page, decodeInteger).withDefault(defaults.page),
};
export const loadSearch = createLoader(searchParsers);
export const serializeSearch = createSerializer(searchParsers);
```

数値は文字列全体を検査し、`2abc`や`1.5`を整数へ丸めて受け付けない。
`nuqs/server`からimportすると、同じ定義をServer・Client双方で使える。

pageでは`await loadSearch(searchParams)`を検索関数へ渡す。認証・権限確認もこの入口で行う。
結果と、その結果に対応する解析済み検索条件をClient Componentへ渡す。
最終ページ超過でqueriesがページを補正した場合は、`serializeSearch`で`page`だけを書き換えてredirectする。無関係なURLパラメーターは保持する。

## URL更新と検索の実行

`src/components/data-table/use-table-search.ts`に`useQueryStates`との接続をまとめる。
共通の検索キーは`q`・`sort`・`direction`・`page`とし、固有のフィルターはparserに追加する。
型は受け取ったparserから導出し、ソートキーや固有フィルターの型を`string`・`unknown`へ広げない。
共通hookの引数は`useTableSearch(searchParsers, appliedSearch, result.pagination.pageSize)`とする。
`appliedSearch`にも同じparserから得た型を使い、別画面の検索条件を受け付けない。
第3引数の件数はTanStackの`PaginationState.pageSize`へ渡す。ページ操作でURLへ反映するのは`page`だけとする。
初期構成のフィルター値は文字列・数値とし、すべてのparserに既定値を持たせる。

```tsx
const [pending, startTransition] = useTransition();
const [search, setSearch] = useQueryStates(searchParsers, {
  shallow: false,
  history: "push",
  startTransition,
});
```

`shallow: false`でServer Componentを再取得する。確定した検索条件を履歴へ追加し、「戻る・進む」で復元できるようにする。

| 操作 | 更新方針 |
| --- | --- |
| テキスト入力・削除・変換確定 | 入力欄だけ更新し、検索条件は変更しない |
| 検索ボタン・変換中でないEnter | 入力欄の値を`q`へ反映し、ページを1へ戻す |
| 空欄で検索 | 検索語を解除し、ページを1へ戻す |
| 選択式フィルター・ソート | 確定済みの検索語を維持し、ページを1へ戻す |
| ページ切り替え | 確定済みの検索条件で対象ページへ移動する |

```ts
function submitSearch(q: string) {
  const parsed = searchParsers.q.parse(q);
  if (parsed === null) return;
  void setSearch({ q: parsed, page: 1 });
}

function updateFilters(
  patch: Partial<Omit<typeof search, "q" | "sort" | "direction" | "page">>,
) {
  void setSearch({ ...patch, page: 1 });
}
```

共通hookは`search`・`submitSearch`・`updateFilters`と、Tableに渡す`pagination`・`sorting`・`onPaginationChange`・`onSortingChange`・`updating`を返す。
`updateFilters`の型から`q`・`sort`・`direction`・`page`を除き、固有フィルターだけを受け付ける。
nuqsの型は`Values<typeof searchParsers>`から導出し、例えば`status`の許可値や数値フィルターの型をそのまま維持する。
フィルター・ソートを更新するときは、変更するキーと`page: 1`だけを渡す。
nuqsは指定されたキーだけを更新するため、現在の検索条件を展開し直す必要はない。

### 入力欄と確定済みの検索語

入力途中の値はローカルstateに保持し、検索操作で確定する。
戻る／進むでURLの検索語が変わったら入力欄にも反映する。
`src/components/search-input.tsx`：

```tsx
"use client";

import { Button, Group, TextInput } from "@mantine/core";
import { useEffect, useState } from "react";

type Props = {
  value: string;
  label: string;
  submitLabel: string;
  maxLength: number;
  onSearch: (value: string) => void;
};

export function SearchInput({ value, label, submitLabel, maxLength, onSearch }: Props) {
  const [draft, setDraft] = useState(value);
  useEffect(() => { setDraft(value); }, [value]);

  return <Group align="end">
    <TextInput
      label={label}
      value={draft}
      maxLength={maxLength}
      onChange={event => setDraft(event.currentTarget.value)}
      onKeyDown={event => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        if (event.nativeEvent.isComposing || event.nativeEvent.keyCode === 229) return;
        onSearch(event.currentTarget.value);
      }}
    />
    <Button type="button" onClick={() => onSearch(draft)}>{submitLabel}</Button>
  </Group>;
}
```

IMEの変換確定に使うEnterでは検索しない。変換確定後も、検索ボタンまたはEnterで実行する。
ページ側から`value={search.q}`・`onSearch={submitSearch}`・検索条件で定義した`maxLength`を渡す。
入力欄とボタンのラベルは、[i18nの方針](../setup/i18n.md)に従って翻訳済みの文字列を渡す。

## 共通テーブルとページ側の接続

`src/components/data-table/features.ts`でfeature構成を定義し、共通テーブルと各ページの列定義から参照する。

```ts
import { rowPaginationFeature, rowSortingFeature, tableFeatures } from "@tanstack/react-table";

export const dataTableFeatures = tableFeatures({ rowPaginationFeature, rowSortingFeature });
```

ページの`items-table.tsx`は、取得結果に対応する列を定義する。

```ts
import { createColumnHelper } from "@tanstack/react-table";
import { dataTableFeatures } from "@/components/data-table/features";
import type { searchItems } from "@/queries/item";

type ItemSummary = Awaited<ReturnType<typeof searchItems>>["items"][number];
const columnHelper = createColumnHelper<typeof dataTableFeatures, ItemSummary>();
```

Client Component内で`columnHelper.columns([...])`に列を定義する。
例えば名前の列は`columnHelper.accessor("name", { header: translate("models.item.name") })`とする。
ソート対象の列IDは検索条件と揃え、対象外の列には`enableSorting: false`を指定する。
セルのリンク・バッジ・行操作も、このページの列定義に含める。

共通部品への受け渡しは次の形にする。

| 共通部品 | ページから渡すもの |
| --- | --- |
| `useTableSearch` | `searchParsers`、取得済み結果に対応する`appliedSearch`、取得結果の`pagination.pageSize` |
| `SearchInput` | 現在の検索語、入力欄とボタンの翻訳済みラベル、文字数上限、hookの`submitSearch` |
| 固有フィルター | hookの`search`から対象の値を読み、変更を`updateFilters`へ渡す |
| `DataTable` | 取得した行、列、行IDを得る関数、総件数、hookのページ／ソート状態と変更ハンドラー、`updating`、空状態の`emptyContent`、翻訳済みの`labels` |

`DataTable`のpropsは行の型をジェネリックで保持する。列を`any`へ変換せず、行の型とfeature構成を揃える。
各ページから完成済みのtableインスタンスを渡す方式にはせず、`useTable`の初期化は共通部品の中へ置く。
共通hookと`DataTable`の境界ではTanStackの`PaginationState`・`SortingState`・`OnChangeFn`を使えるが、queriesへは持ち込まない。

ページ側の組み立ては次の形になる。`columns`と固有フィルターだけが対象に応じて変わる。

```tsx
const { search, submitSearch, updateFilters, ...tableState } =
  useTableSearch(searchParsers, appliedSearch, result.pagination.pageSize);

<SearchInput
  value={search.q}
  label={translate("pages.items.search")}
  submitLabel={translate("pages.items.submitSearch")}
  maxLength={searchTextMaxLength}
  onSearch={submitSearch}
/>

<DataTable
  data={result.items}
  columns={columns}
  getRowId={(row) => String(row.id)}
  rowCount={result.pagination.totalItems}
  {...tableState}
  emptyContent={
    <EmptyContent
      title={translate("pages.items.empty")}
      description={translate("pages.items.emptyDescription")}
    />
  }
  labels={{
    pagination: translate("pages.items.pagination"),
    page: page => translate("pages.items.page", { page }),
    previous: translate("pages.items.previousPage"),
    next: translate("pages.items.nextPage"),
  }}
/>
```

`searchTextMaxLength`はqueriesの検索条件からimportする。
固有フィルターの変更は、例えば`updateFilters({ status: "active" })`と渡す。URL更新やページリセットは書かない。

`DataTable`のpropsは、描画に必要なものだけを受け取る。

```ts
type Props<TData extends RowData> = {
  data: TData[];
  columns: ColumnDef<typeof dataTableFeatures, TData>[];
  getRowId: (row: TData) => string;
  rowCount: number;
  pagination: PaginationState;
  sorting: SortingState;
  onPaginationChange: OnChangeFn<PaginationState>;
  onSortingChange: OnChangeFn<SortingState>;
  updating: boolean;
  emptyContent: ReactNode;
  labels: { pagination: string; previous: string; next: string; page: (page: number) => string };
};
```

Tableの型は`@tanstack/react-table`、`ReactNode`は`react`からimportする。
取得結果の`{ items, pagination }`全体や検索スキーマは渡さない。別の一覧で`users`・`orders`を返しても、共通テーブルの実装は変わらない。

### 共通部品に閉じ込める処理

| 処理 | 実装する場所 |
| --- | --- |
| 1始まりのpageと0始まりのpageIndexの変換 | `use-table-search.ts` |
| TanStackの値／関数形式のupdaterの解決 | `use-table-search.ts` |
| 列ID・ページ番号を受け取ったparserで検証 | `use-table-search.ts` |
| `manualPagination: true`・`manualSorting: true` | `data-table.tsx` |
| 単一列ソート・ソート解除なしの設定 | `data-table.tsx` |
| MantineのTable、ヘッダー、行、セルの描画 | `data-table.tsx` |
| ソート用ボタン・`aria-sort`、更新待ち・空表示 | `data-table.tsx` |
| MantineのPaginationとTableのページ状態の接続 | `data-table.tsx` |

検索・ソート・ページ分割済みの行を受け取るため、クライアント側のソート・ページ分割用row modelは追加しない。
ヘッダー・セルはv9の`<table.FlexRender header={header} />`・`<table.FlexRender cell={cell} />`で描画する。
`DataTable`は翻訳済みの`labels`も受け取り、特定ページの翻訳キーへ依存しない。
列名・検索ラベル・操作文言は呼び出し元で[i18nのキー分類](i18n.md#キーの分類と命名)に従って用意する。

### ページ操作と空状態

ページ操作にはMantineの`Pagination`を使う。TanStackの0始まりの`pageIndex`と、Mantineの1始まりの`value`を境界で変換する。

```tsx
<Pagination
  total={table.getPageCount()}
  value={pagination.pageIndex + 1}
  onChange={page => table.setPageIndex(page - 1)}
  disabled={updating}
  component="nav"
  aria-label={labels.pagination}
  getItemProps={page => ({ "aria-label": labels.page(page) })}
  getControlProps={control => control === "previous"
    ? { "aria-label": labels.previous }
    : control === "next" ? { "aria-label": labels.next } : {}}
/>
```

総ページ数が1以下ならページ操作を表示しない。再取得中は操作を無効化する。
`labels.page`は`translate("pages.items.page", { page })`を呼ぶ関数として渡し、メッセージは`{page, number}ページ目`のように定義する。

0件の場合は、表の代わりに`emptyContent`を表示する。呼び出し側で共通の`EmptyContent`を組み立て、画面に合った見出し・説明を渡す。
`src/components/empty-content.tsx`：

```tsx
import { EmptyState } from "@mantine/core";
import { IconInbox } from "@tabler/icons-react";

type Props = { title: string; description?: string };

export function EmptyContent({ title, description }: Props) {
  return <EmptyState role="status" py="xl" title={title} description={description}
    icon={<IconInbox size={32} aria-hidden="true" />} withIndicatorBackground />;
}
```

空状態は検索が成功して0件だった場合に使い、取得失敗の表示とは分ける。

## 再取得中の表示

nuqsのstateはURLや取得結果より先に更新されるため、遷移中かどうかと取得済みの検索条件を合わせて判定する。
確定済みの検索条件と、Server Componentから受け取った結果の検索条件も比較し、違っている間は更新待ちとして表示する。
比較は共通hookがparserのキーに沿って行い、固有フィルターを追加したときの比較漏れを防ぐ。

更新待ちでも検索欄は操作できるようにする。古い行を残す場合はローディング表示・`aria-busy`を付け、古い件数に基づくページ操作は無効化する。
検索失敗は空の結果に置き換えず、ページのエラー表示へつなぐ。

## 参考

- [TanStack Table：v9への移行](https://tanstack.com/table/latest/docs/framework/react/guide/migrating)
- [TanStack Table：サーバー側での検索・ページ分割](https://tanstack.com/table/latest/docs/framework/react/examples/with-tanstack-query)
- [TanStack Table：React Compiler](https://tanstack.com/table/latest/docs/framework/react/guide/react-compiler)
- [nuqs：Next.js用Adapter](https://nuqs.dev/docs/adapters)
- [nuqs：サーバー側の解析](https://nuqs.dev/docs/server-side)
- [nuqs：履歴・遷移](https://nuqs.dev/docs/options)
- [Mantine：Pagination](https://mantine.dev/core/pagination/)
- [Mantine：EmptyState](https://mantine.dev/core/empty-state/)
- [Mantine：Table](https://mantine.dev/core/table/)
- [MDN：IMEとkeydownの順序](https://developer.mozilla.org/en-US/docs/Web/API/Element/keydown_event#keydown_events_with_ime)
