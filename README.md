# Standards

TypeScriptプロジェクトを立ち上げるための設定と、その採用理由をまとめる。
共通方針を土台に、実行環境ごとの設定を適用する。

| 入口 | 内容 |
| --- | --- |
| [Base](docs/base/README.md) | 依存管理・品質・開発ツールなどの共通方針 |
| [CLI](docs/cli/README.md) | Node.jsで直接実行するCLI・バッチの初期設定 |
| [Next.js](docs/nextjs/README.md) | セットアップ手順と、画面・DB・認証などの実装方針 |
| [init-ts-cli](skills/init-ts-cli/SKILL.md) | CLIの土台を生成するSkill |
| [init-next](skills/init-next/SKILL.md) | Next.jsの土台を生成するSkill |

新規作成時はCLIまたはNext.jsの入口から進める。各項目から必要な共通方針へ辿れる。
バージョン・digest・SHAは確認時点の例なので、導入時には公開後の待機期間と互換性を確認して選び直す。
