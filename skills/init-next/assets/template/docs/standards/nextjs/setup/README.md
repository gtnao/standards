# Next.jsのセットアップ

create-next-appの生成設定へ[Base](../../base/README.md)の共通方針を反映する。

## 初期構成

| 順序 | 項目 | 採用方法 |
| --- | --- | --- |
| 1 | [初期生成](create-next-app.md) | TypeScript・App Router・src・Biome・React Compiler、空の構成で生成する |
| 2 | [package.json](package-json.md) | pnpm・Node.jsを管理し、Next.js向けのscriptsを設定する |
| 3 | [pnpm-workspace](../../base/pnpm-workspace.md) | 待機期間・信頼性検証を採用し、依存のinstall scriptを個別に判断する |
| 4 | [TypeScript](typescript.md)・[Biome](biome.md) | Next.jsの生成型とReactを含めて検査する |
| 5 | [.gitignore](../../base/gitignore.md) | 生成された除外設定を維持し、`.env.example`を共有対象にする |
| 6 | [aqua](../../base/aqua.md) | pinact・Lefthookを導入し、lint・typecheckのフックを登録する |
| 7 | [テスト](../../base/testing.md) | BaseのNode.js向けVitest設定を採用する |
| 8 | [GitHub Actions](../../base/github-actions.md) | ActionをSHA固定し、lint・typecheck・test・buildを実行する |
| 9 | [Mantine・Tabler Icons](mantine.md) | CSS・Provider・PostCSSを設定する |
| 10 | [i18n](i18n.md) | 日本語のnext-intlと、キー・埋め込み引数の型検査を設定する |
| 11 | [React Hook Form](react-hook-form.md) | RHF・resolver・Zodを用意し、フォーム実装時に利用方針へ従う |
| 12 | [環境変数](env.md) | Zodによる検証の配置と、サーバー用・公開用の境界を用意する |
| 13 | [Docker Compose](../../base/docker-compose.md) | ローカルPostgreSQLを用意する。Next.jsはローカルで実行する |
| 14 | [Dockerfile](docker.md) | 本番用standaloneイメージをビルドできる状態にする |

[コーディング方針](../../base/coding-guidelines.md)と[実装方針](../implementation/README.md)を、生成されたAGENTS.mdの管理ブロック外から参照する。
依存のインストール後にlint・型チェック・テスト・ビルド、PostgreSQLと本番イメージの起動を確認する。

## 機能を追加するときの導入

| 項目 | 設定するもの |
| --- | --- |
| [Prisma](prisma.md) | PostgreSQLへのアクセス、型生成、マイグレーション |
| [Better Auth](better-auth.md) | メール・パスワード認証、Admin、DBセッション |
| [TanStack Table・nuqs](table.md) | テーブル操作とURL同期に必要な依存・Provider |

導入時にはそれぞれの実装方針も適用し、CI・Dockerに必要な設定を反映する。
