# tsconfig.jsonの初期設定

Node.js 24で実行するアプリの設定例。TypeScript 7系を使い、設定例は6系でも利用できる。
バンドラーは使わず、開発はtsx、型チェック・ビルドはtsc、本番実行はNode.jsとする。
`package.json`には`"type": "module"`を設定し、ソースを`src/`に置く。

```json
{
  "compilerOptions": {
    "module": "NodeNext",
    "target": "ES2024",
    "lib": ["ES2024"],
    "types": ["node"],

    "rootDir": "src",
    "outDir": "dist",

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,

    "verbatimModuleSyntax": true,
    "noEmitOnError": true,
    "skipLibCheck": true,
    "sourceMap": true
  },
  "include": ["src/**/*.ts"]
}
```

すべてがコンパイラーを動かすための必須項目というわけではない。
実行環境と出力構成を指定した上で、新規プロジェクトで採用したい型チェックと運用上の設定を加えている。

## 開発・型チェック・ビルドの使い分け

`typescript`・`tsx`・`@types/node`を開発依存に追加する。`@types/node`は実行環境に合わせて24系を使う。

`package.json`の`scripts`は次のようにする。

```json
{
  "scripts": {
    "dev": "tsx src/index.ts",
    "typecheck": "tsc --noEmit",
    "build": "tsc",
    "start": "node --enable-source-maps dist/index.js"
  }
}
```

| 用途 | 役割 |
| --- | --- |
| `dev` | TypeScriptを直接実行する |
| `typecheck` | ファイルを生成せず、型チェックする |
| `build` | 型チェックしてJavaScriptを生成する |
| `start` | 生成済みのJavaScriptをNode.jsで実行する |

watchは初期設定に含めない。サーバー開発など、変更時の自動再起動が必要な用途では`tsx watch src/index.ts`を使う。

tsx自体は型チェックしないため、開発中も`typecheck`を使う。
また、tsxは拡張子の省略などを許容するので、「tsxで動いた」と「生成したJavaScriptがNode.jsで動く」は同じではない。
tsconfigは本番のNode.jsに合わせ、CIなどでビルド後の実行も確認する。

## 設定を明示・省略する方針

**プロジェクトの品質・安全性に関する方針は明示し、他の設定から自動的に決まる付随設定や、常に有効な機能の指定は省略する。**

- `strict: true`：厳格な型チェックを採用する方針なので、既定値と同じでも明示する。
- `moduleResolution`：`module: "NodeNext"`から決まるため省略する。
- `esModuleInterop`：TypeScript 6以降では対応する相互運用の挙動が常に有効なので省略する。

環境・入出力・検証の省略など、プロジェクトとして判断した内容も明示する。

## 各項目の意味と採用理由

### module

`NodeNext`は、Node.jsのモジュール規則に合わせて、読み込み先の解決・検証・JavaScriptの出力を行う指定。
`package.json`の`"type": "module"`と組み合わせることで、通常の`.ts`をESMとして扱う。
`NodeNext`はTypeScriptの更新に伴って追従する規則も変わるため、Node.js 24専用の固定モードではない。コンパイラー更新時も本番のNode.jsで動作を確認する。

今回の相対importは、`.ts`内でも出力後の拡張子で書く。

```ts
// src/index.tsからsrc/foo.tsを読み込む
import { foo } from "./foo.js";
```

TypeScriptは対応する`foo.ts`を参照し、生成されたJavaScriptではNode.jsが`foo.js`を読み込む。tsxもこの書き方に対応する。

### target・lib

| 項目 | 意味 |
| --- | --- |
| `target: "ES2024"` | 出力するJavaScriptの構文の世代を指定する |
| `lib: ["ES2024"]` | 使用可能とみなすJavaScript標準APIの型を指定する |

Node.js 24向けの基準としてES2024を選ぶ。`@tsconfig/node24`もES2024を基準にしている。
`ESNext`はTypeScriptの更新に伴って意味が変わるため、世代を固定する。

`lib`を明示することで、ブラウザー専用のDOM型を含めない。
どちらも実行環境に不足するAPIを追加する設定ではない。新しいAPIを使う場合は、Node.js側の対応も確認する。

### types

`["node"]`で`@types/node`を読み込み、`process`やNode.js組み込みモジュールの型を使えるようにする。
この指定だけで型パッケージがインストールされるわけではないため、`@types/node`の導入も必要。

TypeScript 6以降では`types`の既定値が空配列になっている。古い設定例のように、インストールしただけで自動的に読み込まれるとは考えない。
通常のimport先の型をすべて列挙する項目ではない。

### rootDir・outDir・include

| 項目 | 意味 |
| --- | --- |
| `rootDir: "src"` | 出力時のディレクトリ構造の基準を`src`にする |
| `outDir: "dist"` | 生成物を`dist`に置く |
| `include: ["src/**/*.ts"]` | コンパイル対象の探索範囲を`src`内の`.ts`にする |

この組み合わせで、`src/index.ts`は`dist/index.js`になる。
TypeScript 6以降では`rootDir`の既定値がtsconfigのあるディレクトリなので、`src`を明示する。

`rootDir`は対象ファイルを選ぶ設定ではない。また、`include`の外でもimportされたファイルは対象になる。
テストや開発用スクリプトを追加する場合は、それらも型チェック対象に含め、ビルド対象と分ける。
具体例は[Vitestの初期設定](vitest.md)を参照。

### strict

暗黙の`any`や`null`・`undefined`の扱いなど、基本となる厳格な型チェックをまとめて有効にする。
TypeScript 6以降では既定値も`true`だが、プロジェクトの方針として明示する。

次の2項目は`strict`に含まれないため、追加で有効にする。

### noUncheckedIndexedAccess

配列や辞書を添字で参照したとき、要素が存在しない可能性を型に反映する。

```ts
const names: string[] = [];
const first = names[0]; // string | undefined
```

存在確認をせずに値を使うミスを検出するため採用する。

### exactOptionalPropertyTypes

プロパティが存在しないことと、値として`undefined`を持つことを区別する。

```ts
type Options = { label?: string };

const a: Options = {};                   // OK
const b: Options = { label: "example" }; // OK
const c: Options = { label: undefined }; // エラー
```

明示的な`undefined`も許容したい場合は、`label?: string | undefined`と書く。
省略と値の指定の違いを正確に表すため採用する。読み取り時に`undefined`の可能性がなくなるわけではない。

### verbatimModuleSyntax

型だけの読み込みは`import type`で明示し、それ以外のimport・exportは基本的にそのまま出力する。

```ts
import type { Options } from "./options.js";
```

型としてしか使わないかどうかを変換ツールに推測させず、tsxとtscの変換の食い違いを減らすため採用する。
モジュール形式に合わないimport・exportを暗黙にCommonJSへ書き換えることも防ぐ。

### noEmitOnError

型エラーなどがあるとき、JavaScriptやsource mapを生成しない。
既定値は`false`で、通常の`tsc`はエラー終了しても生成物を出力し得るため、ビルドの方針として`true`にする。

以前生成した`dist`のファイルを削除する機能ではない。ビルドが失敗したら、古い生成物をそのまま実行・配布しない。

### skipLibCheck

`.d.ts`内部の整合性検証を省略する。依存先だけでなく、自分で書いた`.d.ts`も対象になる。
アプリのコードや、アプリからのライブラリの使い方は引き続き型チェックされる。

**アプリは厳格にチェックし、型定義内部の検証は省略して、チェック時間と依存先の型定義によるビルド停止を抑える**方針で`true`を採用する。
型定義同士の不整合を見逃す可能性は受け入れる。問題のある型定義を修正する設定ではない。

これは問題発生時の回避策としてだけでなく、TypeScript 5.9の`tsc --init`生成例や、`@tsconfig/node24`・`@tsconfig/strictest`でも初期設定として採用されている。
コンパイラーの省略時の既定値が`false`であることと、初期設定として`true`を書くことは別。

### sourceMap

生成したJavaScriptと元のTypeScriptの対応情報を出力する。
デバッグやエラー調査で元のソースを追いやすくするため採用する。

Node.jsでは`--enable-source-maps`を付けると、スタックトレースを元のTypeScriptの位置に対応付けられる。
そのため、本番へ配布する場合も必要な`.js.map`を含める。

## 初期設定で入れない項目

| 項目 | 省略する理由 |
| --- | --- |
| `moduleResolution` | `module: "NodeNext"`から決まる |
| `esModuleInterop` | TypeScript 6以降では対応する挙動が常に有効 |
| `isolatedModules` | 採用した`verbatimModuleSyntax`により有効になるため、重複指定しない |
| `noEmit` | 同じ設定でビルドも行う。型チェックだけのときはscripts側で`tsc --noEmit`を使う |
| `declaration`・`declarationMap` | Node.jsで実行するアプリなので、他のコードから利用するための型定義を生成する必要がない |
| `allowImportingTsExtensions`・`rewriteRelativeImportExtensions` | 相対importを出力後の`.js`で書く方針なので不要 |
| `paths` | 今回はパスエイリアスを設けない。tscが出力先のimportを書き換えてくれる設定でもない |
| `resolveJsonModule`・`jsx`・デコレーター関連 | 実際にその機能を使う場合に追加する |
| `incremental` | 初期段階では追加せず、ビルド時間を短縮する必要が出てから検討する |

## 参考

- [TypeScript：現行版の導入](https://www.typescriptlang.org/download/)
- [TypeScript：TSConfigリファレンス](https://www.typescriptlang.org/tsconfig/)
- [TypeScript：Node.js・tsx向けのモジュール設定](https://www.typescriptlang.org/docs/handbook/modules/guides/choosing-compiler-options.html)
- [TypeScript 6.0：既定値の変更](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html)
- [TypeScript 5.9：tsc --initの生成例](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html#minimal-and-updated-tsc---init)
- [TypeScript：skipLibCheck](https://www.typescriptlang.org/tsconfig/skipLibCheck.html)
- [TypeScript：noEmitOnError](https://www.typescriptlang.org/tsconfig/noEmitOnError.html)
- [tsconfig/bases：Node.js 24向け設定](https://github.com/tsconfig/bases/blob/main/bases/node24.json)
- [tsconfig/bases：strictest設定](https://github.com/tsconfig/bases/blob/main/bases/strictest.json)
- [Node.js：source mapの有効化](https://nodejs.org/api/cli.html#--enable-source-maps)
