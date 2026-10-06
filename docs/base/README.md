# 共通方針

CLI・Next.jsの両方で採用する土台。実行環境ごとの完成した設定は、[CLI](../cli/README.md)・[Next.js](../nextjs/README.md)から参照する。

| 項目 | 共通にするもの |
| --- | --- |
| [package.json](package-json.md) | pnpm・Node.jsの管理、モジュール方式、非公開設定 |
| [pnpm-workspace](pnpm-workspace.md) | 待機期間・信頼性検証・取得元とインストールスクリプトの制限 |
| [TypeScript](typescript.md) | 型安全性、チェック対象、設定を明示・省略する判断基準 |
| [Biome](biome.md) | Lint・Format・import整理、警告も失敗とする実行方針 |
| [コーディング方針](coding-guidelines.md) | 関数と型、命名、並び順、コメント |
| [ディレクトリ設計](directory-structure.md) | 各層の責務・依存方向・テストしやすい依存の渡し方 |
| [テスト](testing.md) | Node.js上のVitest設定、近接配置、明示的import、本番コードとの境界 |
| [環境変数](env.md) | 秘密情報の扱い、Zodによる検証・変換 |
| [AI SDK・Bedrock](ai-sdk.md) | LLMのports/adapters、認証、構造化出力・Tool・キャッシュ |
| [.gitignore](gitignore.md) | 生成物とローカル設定の除外、雛形の共有 |
| [aqua](aqua.md) | 開発ツールの版管理、pinact、Lefthook |
| [GitHub Actions](github-actions.md) | CIの実行、権限・SHA固定・必須チェック |

Docker関連の共通方針も用意する。Next.jsでは両方を初期構成に含め、CLIでは用途に応じて採用する。

| 項目 | 用途 |
| --- | --- |
| [Docker Compose](docker-compose.md) | ローカル開発用のPostgreSQL |
| [Docker](docker.md) | 本番用コンテナイメージ |

共通方針は各構成から参照し、実行環境に依存する設定値は各構成側で具体化する。
同じファイルへ反映する設定は統合し、生成済みの設定を共通の例で丸ごと上書きしない。
