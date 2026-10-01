# CLI・バッチの初期設定

バンドラーを使わず、開発はtsx、本番はtscで生成したJavaScriptをNode.jsで実行する。
[共通方針](../base/README.md)を、以下の順で適用する。

| 順序 | 設定 | 適用する内容 |
| --- | --- | --- |
| 1 | [package.json](../base/package-json.md)・[pnpm-workspace](../base/pnpm-workspace.md) | ランタイムと依存の版管理、サプライチェーン対策 |
| 2 | [TypeScript](tsconfig.md)・[Vitest](vitest.md) | tsx・tscの実行、広い型チェック、本番ビルド対象の分離、テスト |
| 3 | [環境変数](env.md)・[.gitignore](../base/gitignore.md) | `.env`の読み込み、Zod検証、生成物と秘密情報の除外。`dist/`・`.vitest/`も追加する |
| 4 | [Biome](../base/biome.md) | Lint・Format・import整理。Vitest文書のimport制限も統合する |
| 5 | [コーディング方針](../base/coding-guidelines.md)・[ディレクトリ設計](directory-structure.md) | 規約とentrypoints・usecasesなどの配置 |
| 6 | [aqua](../base/aqua.md) | pinact・Lefthookを導入し、`aqua exec -- lefthook install`でフックを登録する |
| 7 | [GitHub Actions](../base/github-actions.md) | Lint・型チェック・テスト・ビルドを実行し、必要なRulesetsを設定する |

採用する規約は、プロジェクトの`AGENTS.md`から参照できるようにする。
依存・ツールの版を選び、`allowBuilds`は実際のインストールスクリプトを確認して判断する。

PostgreSQLが必要なら[Docker Compose](../base/docker-compose.md)、コンテナで本番実行するなら[Dockerfile](docker.md)を追加する。

## Scaffold

[init-ts-cli](../../skills/init-ts-cli/SKILL.md)で基本構成を生成できる。
Skillは持ち運べるよう、テンプレートに規約を同梱する。共通方針やCLI設定を変更するときは、テンプレートとの整合性も確認する。
