# テストの共通方針

テストの配置・依存境界・型チェックの方針を共通にし、実行環境に合わせて設定する。
完成したNode.js向け設定は[CLIのVitest](../cli/vitest.md)を参照。
Next.jsのテスト構成は[今後整理する](../nextjs/README.md#今後整理するもの)。

## 実行と書き方

- `test`は一度実行して終了し、継続実行は`test:watch`に分ける。
- Vitestの`globals: false`を採用し、`test`・`expect`・`vi`などはimportする。
- 初期段階では`passWithNoTests: true`を使う。テスト追加後は実行件数も確認する。
- テスト実行と型チェックは別に行い、テストコードも型チェック対象にする。
- usecaseのテストでは、[ports](directory-structure.md#portsとadapters)を通じて外部依存の値やエラーを制御する。

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

CLIの具体例は[ビルド対象の分離](../cli/vitest.md#型チェックとビルドを分ける)と[importの制限](../cli/vitest.md#本番コードからテストへのimportを制限する)を参照。
Next.jsではTSX・バンドラー・UIの実行環境に合わせて具体化する。

## 参考

- [Vitest：導入とテスト配置](https://vitest.dev/guide/)
- [Vitest：globals](https://vitest.dev/config/globals)
- [Vitest：passWithNoTests](https://vitest.dev/config/passwithnotests)
