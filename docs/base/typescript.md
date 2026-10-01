# TypeScriptの共通方針

実行環境に合わせてモジュール解決・標準APIの型・出力を選び、型チェックの方針を共通にする。
完成した設定例は[CLI](../cli/tsconfig.md)・[Next.js](../nextjs/typescript.md)を参照。

## 設定を明示・省略する方針

既定値と同じかどうかだけで省略を決めず、採用する方針として明示する価値があるかで判断する。
品質・安全性や環境・入出力・検証の省略について判断した内容は明示する。
他の設定から自動的に決まる付随設定や、常に有効な機能の指定は省略できる。
フレームワークが要求・補正する設定は、その制約も踏まえる。

## 型チェックの対象

本番コード・テスト・設定ファイル・開発用スクリプトを対象にする。
型チェックの範囲と、本番向けに生成・配布する対象は分けて考える。
生成物の除外や必要な生成型の取り込みは、実行環境ごとの設定に従う。

## 型チェックの設定

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

型としてしか使わないかどうかを変換ツールに推測させず、型チェックと変換ツールの食い違いを減らすため採用する。
モジュール形式に合わないimport・exportを暗黙にCommonJSへ書き換えることも防ぐ。

### skipLibCheck

`.d.ts`内部の整合性検証を省略する。依存先だけでなく、自分で書いた`.d.ts`も対象になる。
アプリのコードや、アプリからのライブラリの使い方は引き続き型チェックされる。

**アプリは厳格にチェックし、型定義内部の検証は省略して、チェック時間と依存先の型定義によるビルド停止を抑える**方針で`true`を採用する。
型定義同士の不整合を見逃す可能性は受け入れる。問題のある型定義を修正する設定ではない。

これは問題発生時の回避策としてだけでなく、TypeScript 5.9の`tsc --init`生成例や、`@tsconfig/node24`・`@tsconfig/strictest`でも初期設定として採用されている。
コンパイラーの省略時の既定値が`false`であることと、初期設定として`true`を書くことは別。

## 参考

- [TypeScript：TSConfigリファレンス](https://www.typescriptlang.org/tsconfig/)
- [TypeScript：skipLibCheck](https://www.typescriptlang.org/tsconfig/skipLibCheck.html)
- [TypeScript 6.0：既定値の変更](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html)
