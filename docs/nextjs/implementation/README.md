# Next.jsの実装方針

[Baseのコーディング方針](../../base/coding-guidelines.md)を共通規約とし、作業対象に対応する文書を読む。
ライブラリの導入がまだなら、各文書から[セットアップ](../setup/README.md)へ進む。

| 対象 | 方針 |
| --- | --- |
| [ディレクトリ設計](directory-structure.md) | 責務・依存関係、ページへのコロケーション、共通化する場所 |
| [Mantine・Tabler Icons](mantine.md) | Server／Client境界とアイコンの使い方 |
| [i18n](i18n.md) | キーの分類、完全なキーと`translate`による呼び出し |
| [React Hook Form](react-hook-form.md) | Zod・Mantine・i18nの接続、条件付き入力と型 |
| [環境変数](env.md) | 検証する時点、公開値、Next.js外からの利用 |
| [Prisma](prisma.md) | schemaの命名、依存関係の例外、usecasesでの利用 |
| [Queries](queries.md) | find/list/search、取得条件・返却型・ページ計算 |
| [テーブル](table.md) | 共通UI、明示的な検索、ソート・ページ・URLの同期 |
| [認証](better-auth.md) | セッション確認、ユーザー作成、ログインフォーム |
| [AI SDK・Bedrock](../../base/ai-sdk.md) | 共通のLLM port、構造化出力・ストリーミング・Tool |
| [非同期ジョブ](../../base/async-jobs.md) | 共通キュー・Worker、DBによる実行権と結果確定 |

React・Next.js固有の規約は、合意したものを各文書へ追加していく。
