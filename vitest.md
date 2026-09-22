# Vitestの初期設定

Node.jsで動くTypeScriptのユニットテストを対象にする。
本番のビルドは引き続きtscを使う。Vitestは内部でViteを使うが、アプリのビルド方式を変更する必要はない。

ルートに`vitest.config.ts`を置く。

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    globals: false,
    include: ["src/**/*.test.ts"],
    passWithNoTests: true,
  },
});
```

## 導入・実行

```sh
pnpm add -D vitest
```

[pnpmの設定](pnpm-workspace.md)に従い、公開後の待機期間を満たすバージョンを使う。

`package.json`のscriptsに追加・反映する。ビルド用設定は後述。

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit",
    "build": "tsc -p tsconfig.build.json"
  }
}
```

`test`は一度実行して終了する。変更のたびに再実行したいときだけ`test:watch`を使う。
通常のテスト実行では型チェックをしないため、CIでは`typecheck`・`test`・`lint`・`build`をそれぞれ実行する。具体例は[GitHub ActionsのCI初期設定](github-actions.md)を参照。

生成物をGitに含めないよう、`.gitignore`に`.vitest/`を追加する。

## 設定の意味と採用理由

| 項目 | 意味・理由 |
| --- | --- |
| `environment: "node"` | Node.js向けのテストであることを明示する。既定値と同じ |
| `globals: false` | `test`・`expect`・`vi`などを必要なファイルでimportする方針。既定値と同じ |
| `include` | `src`内の`*.test.ts`に統一する。生成先の`dist`を探索対象にせず、テストの命名・配置も明確にする |
| `passWithNoTests: true` | テスト未作成の初期段階でもCIを通せるよう、テスト0件を成功扱いにする |

設定ファイルなしでもVitestは動くが、実行環境とテストの書き方・配置を明示しておく。
`passWithNoTests`は探索設定の誤りで0件になった場合も成功するため、テストの追加後は実行件数も確認する。

`globals: false`なら、テストAPIの出所がコードから分かり、通常のimportと同じように補完・型チェックできる。
`tsconfig.json`の`types`に`vitest/globals`を追加する必要もなく、本番コードにテスト用のグローバル型を持ち込まずに済む。
グローバルな`afterEach`などを前提に自動処理する外部ライブラリを導入する場合は、そのライブラリの手動設定が必要か確認する。

## テストは対象コードの近くに置く

```text
src/
  sum.ts
  sum.test.ts
  __tests__/
    helpers.ts
```

ユニットテストは対象コードと一緒に見つけやすく、変更・移動もしやすい配置を選ぶ。
Vitest公式の入門例も対象コードとテストを並べている。
複数の機能にまたがる結合テスト・E2Eテストが必要になれば、`tests/`などへの分離を検討する。

テスト専用のヘルパーは`__tests__/`に置き、本番コードと区別する。
`*.spec.ts`やルートの`tests/`を使う場合は、Vitestの探索範囲・ビルド除外・後述のLintも配置に合わせる。型チェックは後述の設定でプロジェクト全体を対象にする。

```ts
// src/sum.test.ts
import { expect, test } from "vitest";
import { sum } from "./sum.js";

test("2つの数を足す", () => {
  expect(sum(1, 2)).toBe(3);
});
```

相対importは、本番コードと同じく出力後の`.js`で書く。

## 型チェックとビルドを分ける

| 設定 | 対象・用途 |
| --- | --- |
| `tsconfig.json` | 本番コード・テスト・設定ファイル・開発用スクリプトを型チェックする |
| `tsconfig.build.json` | 本番コードをビルドする |

[TypeScriptの初期設定](tsconfig.md)から、次のように変更する。

1. `tsconfig.json`の`compilerOptions`から`rootDir`・`outDir`をビルド側へ移す。他のオプションは維持する。
2. `tsconfig.json`の`include`を置き換え、`exclude`を追加する。以下はルートの項目の抜粋。

```json
"include": ["**/*"],
"exclude": ["node_modules", "dist"]
```

型チェックはプロジェクト全体を対象にし、依存パッケージと生成物を探索から除外する。
`**/*`でも、対象になるのはTypeScriptが扱う拡張子のファイル。`allowJs`を有効にしていないため、JavaScriptは対象にしない。
`vitest.config.ts`を個別に列挙せず、今後追加する設定ファイルや`scripts/`内のTypeScriptも拾い、設定の更新忘れによる取りこぼしを防ぐ。
生成先が増えたら`exclude`に追加する。別の実行環境・コンパイラー設定が必要なコードは、専用のtsconfigに分ける。
`rootDir: "src"`を共通側に残すと、ルート直下の設定ファイルが範囲外になる。
`noEmit`は引き続きscripts側で指定する。

ルートに`tsconfig.build.json`を追加する。

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src/**/*.ts"],
  "exclude": ["src/**/*.test.ts", "src/**/__tests__/**"]
}
```

これにより、通常は本番コードだけが`dist`に出力され、`src/index.ts`は従来どおり`dist/index.js`になる。
ビルド側の`include`・`exclude`は共通側の配列を置き換える。型チェックは広く、ビルドは`src`内の本番コードに絞る構成とする。
ビルド用tsconfigを分けてテストを除外する構成は、Nest公式スターターでも採用されている。

ただし、`exclude`は対象の探索から外す設定であり、importを禁止しない。
本番コードからテストをimportすると、そのテストもビルド対象に入り得るため、次のLintで制限する。
また、tscは過去の生成物を削除しない。配置変更などで古いテストの出力が残っている場合は、`dist`を削除してビルドし直す。

## 本番コードからテストへのimportを制限する

[Biomeの設定](biome.md)に次の`overrides`を追加する。

```json
{
  "overrides": [
    {
      "includes": ["src/**", "!src/**/*.test.ts", "!src/**/__tests__/**"],
      "linter": {
        "rules": {
          "style": {
            "noRestrictedImports": {
              "level": "error",
              "options": {
                "patterns": [
                  {
                    "group": ["vitest", "vitest/**", "**/*.test.*", "**/__tests__/**"],
                    "message": "本番コードからテスト用コードをimportしないでください。"
                  }
                ]
              }
            }
          }
        }
      }
    }
  ]
}
```

`includes`はルールを適用するファイル、`group`はimportを禁止する名前・パターン。
テストとヘルパーにはこの制限を適用しないので、それらの間のimportは許可する。他のLintやFormatは引き続き適用される。
`*.test.*`は、TypeScript内で書く`./sum.test.js`にも一致させるための指定。

このルールはimportの文字列を検査する。例えば`#test-helper`という別名が`__tests__/helpers.ts`を指していても、その対応先までは判定しない。
別名を導入した場合は、その名前も禁止パターンに追加する。
テスト専用コードを通常の名前・場所に置いた場合も識別できないため、命名・配置のルールとセットで運用する。

## 初期設定で入れないもの

| 項目 | 省略する理由 |
| --- | --- |
| `setupFiles` | 共通の初期化処理が必要になってから追加する |
| `jsdom`・`happy-dom` | Node.jsのテストにDOM環境は不要 |
| カバレッジ | 計測対象・目標を決める段階で追加する。その際はテスト・ヘルパーを計測対象から除外する |
| `clearMocks`・`mockReset`・`restoreMocks` | 履歴・実装・spyの復元で役割が異なる。モックを使う際に後始末の方針を決める |
| `pool`・並列数・タイムアウト | まず既定値を使い、実際の制約に合わせて変更する |
| Vitestの`typecheck` | 通常のコードとテストの型チェックは`tsc --noEmit`にまとめる |

## 参考

- [Vitest：導入・テストの配置例・実行](https://vitest.dev/guide/)
- [Vitest：設定ファイル](https://vitest.dev/config/)
- [Vitest：globals](https://vitest.dev/config/globals)
- [Vitest：include](https://vitest.dev/config/include)
- [Vitest：passWithNoTests](https://vitest.dev/config/passwithnotests)
- [Vitest：型テストと通常のテスト実行](https://vitest.dev/guide/testing-types)
- [TypeScript：TSConfigリファレンス](https://www.typescriptlang.org/tsconfig/)
- [Nest公式スターター：ビルド用tsconfig](https://github.com/nestjs/typescript-starter/blob/master/tsconfig.build.json)
- [Biome：noRestrictedImports](https://biomejs.dev/linter/rules/no-restricted-imports/javascript/)
- [Biome：overrides](https://biomejs.dev/reference/configuration/#overrides)
