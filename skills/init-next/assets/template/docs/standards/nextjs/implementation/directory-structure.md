# Next.jsのディレクトリ設計

[Baseの責務と依存関係](../../base/directory-structure.md)を保ち、画面に固有の実装は使う場所の近くに置く。

```text
src/
  app/
    layout.tsx
    settings/
      page.tsx
      _components/
        settings-form.tsx
      _helpers/
        actions.ts
        form-schema.ts
        view-model.ts
  components/
  env/
    server.ts
    public.ts
  prisma/
    client.ts
    generated/
  queries/
  usecases/
  domain/
  ports/
  adapters/
  lib/
```

配置の例であり、必要になったファイル・ディレクトリを作る。

## 配置の基準

| 配置 | 役割 |
| --- | --- |
| `app` | ページ・レイアウト・Route Handlerなど、Next.jsの入口と画面構成 |
| `app`配下の`_components` | そのページ、または配下のページで使うReactコンポーネント |
| `app`配下の`_helpers` | 同じ範囲で使うServer Actions・入力検証・表示用変換など |
| `src/components` | アプリ全体で共有するReactコンポーネント |
| `src/env` | [環境変数の検証・変換](../setup/env.md)。サーバー用と、必要な場合だけ公開用を分ける |
| `src/queries` | [表示用のDB取得](queries.md)。find/list/searchでデータを返す |
| `usecases`・`domain`・`ports`・`adapters` | Baseと同じ責務・依存関係 |
| `src/prisma` | [Prismaのクライアントと生成コード](../setup/prisma.md)。adapters配置の例外 |
| `src/lib` | アプリ固有の意味を持たない汎用処理。Baseの方針に従い、必要になったものだけ切り出す |

`_helpers`は、その画面を実現するための処理をまとめる名前として使う。
アプリ固有でない汎用処理を置く`src/lib`とは役割を分ける。

## 使う場所の近くに置く

一つのページだけで使うものは、そのページに最も近い`_components`・`_helpers`へ置く。
配下の複数ページで共有するようになったら、共通の親へ引き上げる。

```text
app/settings/
  _components/        # settings配下で共有するUI
  _helpers/           # settings配下で共有する処理
  profile/
    page.tsx
    _components/      # profileだけで使うUI
    _helpers/         # profileだけで使う処理
```

特定の配下だけで使うものを、最初から`src/components`へ集めない。
別のページの内部実装を直接参照するより、共有範囲に合う親へ移す。
一つのコンポーネントや関数に閉じた型・補助関数は、[コーディング方針](../../base/coding-guidelines.md)に従い、まず同じファイルに置く。

[テーブル表示](table.md)の共通描画・URL状態のhookは`src/components/data-table`、IME対応の検索入力は`src/components/search-input.tsx`に置く。
ページ固有の列・フィルターUIは近くの`_components`、URLキーと検索条件の対応は`_helpers`に置く。
ページ計算・LIKEエスケープは`src/queries/helpers`、URLのparser生成・検索パラメーター変換は`src/app/_helpers`で共有する。
検索条件のスキーマはqueriesの入力契約として`src/queries`に置く。DB実行ファイルと分け、UIからも参照できるよう、DB接続・`server-only`・URLや表示用ライブラリには依存させない。

`_components`・`_helpers`はNext.jsのprivate folderとしてルーティング対象から外れる。
この指定はimportの可否やサーバー専用化を制御するものではない。

## Baseとの責務分担

ページ固有であることと、その処理の責務は別に判断する。

| 処理 | 配置 |
| --- | --- |
| フォーム入力の検証、検索パラメーターの解釈 | 近くの`_helpers` |
| 依存を組み立ててusecaseを呼ぶServer Action | 近くの`_helpers` |
| 処理結果を画面向けのデータへ変換する | 近くの`_helpers` |
| 画面などへ返すデータのDB取得 | `queries` |
| 業務の目的を達成する処理手順 | `usecases` |
| 業務上の概念・ルール | `domain` |
| 外部機能の契約と実装 | `ports`・`adapters` |

usecaseなどの下位層から`app`・`components`へ依存させない。
画面表示やNext.js固有の制御は入口側に置き、usecaseは依存と入力を受け取り、結果を返す。
共通コンポーネントから特定のページの`_helpers`を参照せず、必要な値や処理をpropsなどで受け取る。

queriesとusecasesは入口から使い分け、相互に依存させない。queriesはPrisma・domain・libを利用でき、app・componentsへは依存しない。

Prismaは外部機能の配置ルールの例外とし、queries・usecasesからAPI・生成型を使える。
取得・更新の使い分けは[Prismaの利用方針](prisma.md#usecasesでの利用)に従う。
domainも生成型へ依存できるが、DB接続・クエリ実行は持ち込まない。

## ServerとClientの境界

ページ・レイアウトはServer Componentを基本とし、状態・イベント・ブラウザーAPIが必要な部分をClient Componentへ分ける。
`_components`にあること自体は、Client Componentであることを意味しない。

`_helpers`にはサーバー側とクライアント側の処理が入り得るため、実行場所の異なる処理はファイルを分ける。
例えばServer Actionsと、フォームからも使う入力スキーマを同じファイルへ混ぜない。
サーバー専用の通常モジュールには`server-only`を使い、Client側への誤importを検出する。
`"use server"`はServer Functionsを定義する指定であり、サーバー専用の補助関数すべてに付けるものではない。

## 参考

- [Next.js：コロケーションとprivate folders](https://nextjs.org/docs/app/getting-started/project-structure)
- [Next.js：Server／Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [Next.js：use server](https://nextjs.org/docs/app/api-reference/directives/use-server)
