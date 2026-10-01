# Next.jsのTypeScript設定

[create-next-appで生成した設定](create-next-app.md)を土台に、型チェックの方針を加える。
JavaScriptへの変換・ビルドはNext.js、型チェックはTypeScriptが担当する。

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowArbitraryExtensions": true,
    "verbatimModuleSyntax": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["**/*", ".next/types/**/*.ts", ".next/dev/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## 生成設定からの変更

2026年9月23日に確認した`create-next-app@16.3.5`・`16.3.6`の生成設定との差分。

| 項目 | 生成時 | 変更後・理由 |
| --- | --- | --- |
| `allowJs` | `true` | `false`。新規コードはTypeScriptで統一する |
| `allowArbitraryExtensions` | なし | `true`。[next-intlの生成宣言](i18n.md#nextjs設定と型安全性)をJSON importに対応付ける |
| `noUncheckedIndexedAccess` | なし | `true`。配列・辞書の要素が存在しない可能性を型に反映する |
| `exactOptionalPropertyTypes` | なし | `true`。プロパティの省略と明示的な`undefined`を区別する |
| `verbatimModuleSyntax` | なし | `true`。型だけのimportを`import type`で明示する |
| `isolatedModules` | `true` | 削除。`verbatimModuleSyntax`により有効になるため |
| `include` | `next-env.d.ts`・`**/*.ts`・`**/*.tsx`・`**/*.mts`とNext.jsの生成型 | 通常の探索を`**/*`にまとめ、Next.jsの生成型は明示したまま残す |

その他は生成値を維持する。`target`・`lib`も現時点ではNext.jsの生成値を使い、[Node.js CLI向けの設定](../cli/tsconfig.md)をそのまま移さない。

## 各項目の意味と理由

### 実行環境とモジュール

| 項目 | 意味・理由 |
| --- | --- |
| `target: "ES2017"` | TypeScriptが想定するJavaScriptの構文世代。今回は`noEmit`なので、最終的なブラウザー向け出力がこの指定だけで決まるわけではない |
| `lib: ["dom", "dom.iterable", "esnext"]` | ブラウザーAPI、DOMコレクションの反復処理、そのTypeScriptが提供する最新のJavaScript標準APIの型を読み込む |
| `module: "esnext"` | import・exportをES Modulesとして扱う。JavaScriptの構文世代を指定する`target`とは役割が異なる |
| `moduleResolution: "bundler"` | import先をバンドラー向けの規則で解決する。拡張子を省略した相対importなどを扱える |
| `jsx: "react-jsx"` | JSXをReactの自動ランタイム方式として扱う。JSXを書くためだけの`import React`が不要になる |
| `resolveJsonModule: true` | JSONのimportを認め、内容から型を推論する |
| `esModuleInterop: true` | CommonJSをES Modules形式でimportする際の互換性を調整する。生成設定のTypeScript 5では、default importの型チェックにも影響する |

`lib`は型の指定であり、実行環境へAPIを追加する設定ではない。
`esnext`に型があることと、対象ブラウザーで使えることは別なので、新しいAPIの利用時には対応状況を確認する。

CLIで使う`NodeNext`は、出力をNode.jsで直接実行するための規則。
Next.jsのコードはバンドラーを通るため、同じ設定に揃える必要はない。

`esModuleInterop`などはTypeScriptの版によって省略可能でも、確認したNext.jsの設定補正では再追加される。
生成された`module: "esnext"`を使う構成では残す。

### 型チェック

| 項目 | 意味・理由 |
| --- | --- |
| `allowJs: false` | JavaScriptを通常のチェック対象として取り込まない。JavaScriptの設定ファイルが存在すること自体は禁止しない |
| `strict: true` | 暗黙の`any`や`null`などに関する基本的な厳格チェックを有効にする |
| `noUncheckedIndexedAccess: true` | 配列・辞書へのアクセスで、値が存在しない可能性を反映する |
| `exactOptionalPropertyTypes: true` | `value?: T`で、未指定と`value: undefined`を区別する |
| `skipLibCheck: true` | `.d.ts`内部の整合性検証を省略する。アプリからその型を使う部分は引き続き検証する |
| `verbatimModuleSyntax: true` | 型専用のimportを明示し、変換ツールによるimportの扱いの食い違いを減らす |

基本方針は[共通の型チェック方針](../base/typescript.md)に従う。
JavaScriptも対象にする場合、`allowJs: true`だけではその内部の本格的な型チェックは有効にならず、`checkJs`などが別途必要になる。

生成時の`isolatedModules: true`は、ファイル単位で変換するツールが正しく処理できない書き方を検出するもの。
型チェックをファイル内だけに限定する意味ではない。`verbatimModuleSyntax`で満たせるため重複指定せず、Next.jsの設定補正もこの組み合わせを認識している。

### 出力・キャッシュ・エディター

| 項目 | 意味・理由 |
| --- | --- |
| `noEmit: true` | tscからJavaScript・型定義・source mapを出力しない。変換はNext.jsに任せるため、今回はtsconfig側に置く |
| `incremental: true` | 前回の型チェック情報を`.tsbuildinfo`へ保存し、次回に再利用する。`noEmit`でもこの情報は保存され得る |
| `plugins: [{ "name": "next" }]` | エディターにNext.js固有の補完・診断を追加する。通常の`tsc`にその診断を追加する指定ではない |
| `paths` | `@/components/button`などを`src/components/button`として解決する。Next.js側もこの指定に対応する |

`paths`はTypeScript自身が出力先のimport文字列を書き換える設定ではない。
また、`noEmit`を使うため、CLI向けの`rootDir`・`outDir`・`noEmitOnError`・`sourceMap`は追加しない。
Next.jsが生成するコードの出力先やsource mapは、Next.js側の設定で扱う。

## 型チェックの対象

`**/*`で、本番コード・テスト・設定ファイル・開発用スクリプトを広く対象にする。
すべての種類のファイルをチェックするわけではなく、TypeScriptが扱う拡張子が対象になる。
`allowJs: false`なのでJavaScriptは含めない。

| 対象 | 扱い |
| --- | --- |
| `next-env.d.ts` | `**/*`に含まれる。Next.js固有の型や画像importなどの型を読み込む生成ファイル。手編集しない |
| `.next/types/**/*.ts` | Next.jsが生成するルートなどの型。明示的に含める |
| `.next/dev/types/**/*.ts` | 開発時に生成される型。こちらも明示的に含める |
| `node_modules` | 通常のファイル探索から除外する。import先の型定義を読み込まなくなるわけではない |

必要な生成型まで外してしまうため、`.next`全体を`exclude`には入れない。
別の生成先が増えたら、その用途に合わせて除外を追加する。

## 実行コマンド

生成時には`typecheck`がないため、追加する。`dev`・`build`・`start`は生成値を使う。

```json
{
  "scripts": {
    "dev": "next dev",
    "typecheck": "next typegen && tsc --noEmit",
    "build": "next build",
    "start": "next start"
  }
}
```

| コマンド | 役割 |
| --- | --- |
| `dev` | 変更を反映する開発サーバーを起動する |
| `typecheck` | Next.jsの型を生成してから、プロジェクトを型チェックする |
| `build` | 型チェックを含む本番向けビルドを行う |
| `start` | ビルド済みアプリを本番モードで起動する |

`next typegen`は`PageProps`・`LayoutProps`などの型を生成する。
開発サーバーを一度も起動していない環境でも検査できるよう、`typecheck`の先頭で実行する。
tsconfigにも`noEmit`はあるが、スクリプトでは型チェック専用であることを明示する。

`next build`でも型チェックするが、ビルドせず検査できる独立したコマンドは残す。
`typescript.ignoreBuildErrors`でビルド時の検査を無効化しない。

## TypeScriptと型パッケージの版

生成時は`typescript: "^5"`・`@types/node: "^20"`・React向けの型が`^19`だが、その版を維持するという意味ではない。
[生成後のバージョン調整方針](create-next-app.md#生成後インストール前に調整すること)に従い、使用するランタイム・React・Next.jsと対応を確認して固定する。

現行Next.jsにはTypeScript 7の利用手順もあり、ビルド時にはプロジェクトの`tsc`を呼び出す方式が既定になっている。
ただし、ビルドで使えることとエディターのプラグイン対応は別なので、それぞれ確認する。
TypeScriptのメジャー更新時には、`types`の既定値などの変更も確認し、必要なグローバル型を明示する。CLI用の`types: ["node"]`だけを機械的に移さない。

## 参考

- [create-next-app：生成されるtsconfig](https://github.com/vercel/next.js/blob/v16.3.6/packages/create-next-app/templates/app-empty/ts/tsconfig.json)
- [Next.js：TypeScript・型生成・プラグイン](https://nextjs.org/docs/app/api-reference/config/typescript)
- [Next.js：tsconfigを補正する実装](https://github.com/vercel/next.js/blob/v16.3.6/packages/next/src/lib/typescript/writeConfigurationDefaults.ts)
- [Next.js：TypeScript CLIによる型チェック](https://nextjs.org/docs/app/api-reference/config/next-config-js/useTypeScriptCli)
- [TypeScript：設定リファレンス](https://www.typescriptlang.org/tsconfig/)
- [TypeScript：verbatimModuleSyntax](https://www.typescriptlang.org/tsconfig/verbatimModuleSyntax.html)
