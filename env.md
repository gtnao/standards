# 環境変数の扱い

ローカルでは`.env`を使い、本番・CIでは実行環境から環境変数を渡す。
Node.js 24の標準機能で読み込み、Zodで値を検証・変換する。

`package.json`の実行コマンドは次のようにする。

```json
{
  "scripts": {
    "dev": "tsx --env-file-if-exists=.env src/index.ts",
    "start": "node --enable-source-maps dist/index.js"
  }
}
```

開発・ビルド・本番実行の構成は[tsconfigの初期設定](tsconfig.md#開発型チェックビルドの使い分け)を参照。

## ファイルと読み込みの方針

| 対象 | 方針 |
| --- | --- |
| `.env` | ローカルで使う実際の値。Git管理しない |
| `.env.example` | 必要な変数の説明と記入例。Git管理し、実際の秘密情報は入れない |
| 本番・CI | 実行環境から環境変数を渡す |

最初から環境別のファイルを揃えず、ローカルの`.env`で始める。
Gitへの除外設定は[.gitignoreの初期設定](gitignore.md)を参照。

通常のNode.jsは、`.env`を置いただけでは自動で読み込まない。
tsxもNode.jsのCLIオプションを受け付けるため、開発用コマンドで読み込みを指定する。dotenvなどの追加パッケージは不要。

`--env-file-if-exists`は、ファイルがない場合も実行を続ける。
必要なのは設定値であり、`.env`ファイル自体ではないため、この指定を選ぶ。環境変数を直接渡していれば、ファイルなしでも動かせる。
必須値の不足はアプリ側の検証で検出する。

既に実行環境にある値と`.env`の値が重複した場合は、実行環境側が優先される。
`--env-file=.env`を使うと、ファイルが存在しない時点でエラーになる。

## Zodによる検証・変換

環境変数は文字列なので、数値やbooleanへの変換も必要になる。
アプリ用の環境変数の読み取り・検証・変換をまとめ、利用側では検証済みの値を使う。
TypeScriptの型宣言や`!`だけで存在を保証したことにはしない。

Zodを実行時の依存として追加する。

```sh
pnpm add zod
```

以下はZod 4を使った、バッチ処理向けの例。変数は実際の用途に合わせて定義する。

`.env.example`：

```dotenv
# 必須：利用するAPIの認証キー
API_KEY=

# 任意：省略時は100
BATCH_SIZE=100

# 任意：省略時はfalse
DRY_RUN=false
```

読み取り・検証・変換：

```ts
import { z } from "zod";

const envSchema = z.object({
  API_KEY: z.string().trim().min(1),

  BATCH_SIZE: z
    .string()
    .regex(/^\d+$/)
    .pipe(z.coerce.number().int().min(1).max(1000))
    .default(100),

  DRY_RUN: z
    .stringbool({
      truthy: ["true"],
      falsy: ["false"],
      case: "sensitive",
    })
    .default(false),
});

export const env = envSchema.parse(process.env);
```

| 項目 | 挙動・理由 |
| --- | --- |
| `API_KEY` | 前後の空白を取り除き、未指定・空文字・空白だけならエラー。秘密情報に仮の既定値は設けない |
| `BATCH_SIZE` | 数字だけの文字列を受け付け、数値に変換して1〜1000の整数か検証する |
| `DRY_RUN` | `"true"`・`"false"`だけを受け付け、booleanに変換する |
| `.default(...)` | 未指定の場合だけ既定値を使う。空文字や不正な値はエラーにする |
| `.parse(process.env)` | 検証に失敗すると例外になる。処理開始時に実行する |

数値は先に文字列を検証して、`z.coerce.number()`だけだと空文字が`0`になる挙動を避ける。
booleanも、`z.coerce.boolean()`では文字列の`"false"`が`true`になるため、`z.stringbool()`を使う。

利用側では型が確定する。

```ts
env.API_KEY;    // string
env.BATCH_SIZE; // number
env.DRY_RUN;    // boolean
```

`.env`から環境変数への読み込みはNode.js、値の検証・変換はZodが担当する。

## 参考

- [Node.js：環境変数と.env](https://nodejs.org/docs/latest-v24.x/api/environment_variables.html)
- [Node.js：--env-file](https://nodejs.org/docs/latest-v24.x/api/cli.html#--env-filefile)
- [tsx：Node.jsのCLIオプション](https://tsx.is/node-enhancement)
- [Zod：スキーマ・型変換・既定値](https://zod.dev/api)
