# テストの共通方針

CLI・Next.jsともに、Node.jsで動くusecase・domainなどのユニットテストには同じVitest設定を使う。
当面はUI・ブラウザーテストを対象にせず、`*.test.ts`で検証する。

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

Vitestを開発依存へ追加する。[依存管理の方針](pnpm-workspace.md)に従い、待機期間と互換性を確認した版に完全固定する。

`package.json`に次のscriptsを追加する。

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

`test`は一度実行して終了し、変更時に再実行したい場合だけ`test:watch`を使う。
通常のテスト実行では型チェックしないため、各構成の`typecheck`も実行する。
[CI](github-actions.md)では`lint`・`typecheck`・`test`・`build`を実行し、`.gitignore`には`.vitest/`を追加する。

## 設定の意味と採用理由

| 項目 | 意味・理由 |
| --- | --- |
| `environment: "node"` | Node.js向けのテストであることを明示する。既定値と同じ |
| `globals: false` | `test`・`expect`・`vi`などを必要なファイルでimportする方針。既定値と同じ |
| `include` | `src`内の`*.test.ts`に統一する。生成物を探索対象にせず、テストの命名・配置も明確にする |
| `passWithNoTests: true` | テスト未作成の初期段階でもCIを通せるよう、テスト0件を成功扱いにする |

設定ファイルなしでもVitestは動くが、実行環境とテストの書き方・配置を明示しておく。
`passWithNoTests`は探索設定の誤りで0件になった場合も成功するため、テストの追加後は実行件数も確認する。

`globals: false`なら、テストAPIの出所がコードから分かり、通常のimportと同じように補完・型チェックできる。
`tsconfig.json`の`types`に`vitest/globals`を追加する必要もなく、本番コードにテスト用のグローバル型を持ち込まずに済む。
グローバルな`afterEach`などを前提に自動処理する外部ライブラリを導入する場合は、そのライブラリの手動設定が必要か確認する。

usecaseのテストでは、[ports](directory-structure.md#portsとadapters)を通じて外部依存の値やエラーを制御する。

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
`*.spec.ts`やルートの`tests/`を使う場合は、テストの探索範囲・ビルド対象・Lintも配置に合わせる。型チェックは[共通方針](typescript.md#型チェックの対象)に従い、プロジェクト全体を対象にする。

## 本番コードとの境界

本番コードからテストやテスト専用ヘルパーをimportしない。
探索・ビルド対象からの除外だけではimportを禁止できないため、Lintでも制限する。
import文字列を制限する場合は、パスエイリアスでも迂回できないよう対象を合わせる。

CLIでは[ビルド用tsconfig](../cli/tsconfig.md#型チェックとビルドを分ける)でテストの出力を除外する。
Next.jsは[既存の型チェック設定](../nextjs/setup/typescript.md)にテストも含め、CLI用の`tsconfig.build.json`は追加しない。
Next.jsの[Vitest設定](../nextjs/setup/vitest.md)では、`@/`も解決できるようにする。Next.js専用の実行コンテキストが必要なコードは、依存を分けるか個別にテスト設定を検討する。

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
                    "message": "Do not import test code from production code."
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
| Vitestの`typecheck` | 通常のコードとテストの型チェックは、各構成の`typecheck`にまとめる |

## 参考

- [Vitest：導入とテスト配置](https://vitest.dev/guide/)
- [Vitest：globals](https://vitest.dev/config/globals)
- [Vitest：passWithNoTests](https://vitest.dev/config/passwithnotests)
- [Biome：noRestrictedImports](https://biomejs.dev/linter/rules/no-restricted-imports/javascript/)
- [Biome：overrides](https://biomejs.dev/reference/configuration/#overrides)
