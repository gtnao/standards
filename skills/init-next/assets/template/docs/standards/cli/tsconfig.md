# tsconfig.jsonの初期設定

Node.js 24で実行するアプリの設定例。TypeScript 7系を使い、設定例は6系でも利用できる。
バンドラーは使わず、開発はtsx、型チェック・ビルドはtsc、本番実行はNode.jsとする。
[package.jsonの共通設定](../base/package-json.md)で`"type": "module"`を設定し、ソースを`src/`に置く。
テストを含む初期構成では、続けて[Vitestの設定](vitest.md#型チェックとビルドを分ける)を反映し、型チェック対象を広げてビルド設定を分離する。

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

[共通の判断基準](../base/typescript.md#設定を明示省略する方針)に従う。
この構成では`moduleResolution`は`NodeNext`から決まり、TypeScript 6以降の`esModuleInterop`も独立した指定が不要なので省略する。

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

### 共通の型チェック設定

[TypeScriptの共通方針](../base/typescript.md#型チェックの設定)に従い、次を`true`にする。

- `strict`
- `noUncheckedIndexedAccess`
- `exactOptionalPropertyTypes`
- `verbatimModuleSyntax`
- `skipLibCheck`

### noEmitOnError

型エラーなどがあるとき、JavaScriptやsource mapを生成しない。
既定値は`false`で、通常の`tsc`はエラー終了しても生成物を出力し得るため、ビルドの方針として`true`にする。

以前生成した`dist`のファイルを削除する機能ではない。ビルドが失敗したら、古い生成物をそのまま実行・配布しない。

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
