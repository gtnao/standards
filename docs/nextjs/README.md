# Next.jsの初期設定

create-next-appの生成設定へ[共通方針](../base/README.md)を反映する。
Next.js固有の設定がある項目は、その文書の完成形と変更理由に従う。

## 適用する設定

| 順序 | 項目 | 採用方法 |
| --- | --- | --- |
| 1 | [初期生成](create-next-app.md) | TypeScript・App Router・src・Biome・React Compilerで生成し、依存の自動インストールは止める |
| 2 | [package.json](package-json.md) | 共通のpnpm・Node.js管理を採用し、scriptsはNext.js向けにする |
| 3 | [pnpm-workspace](../base/pnpm-workspace.md) | 待機期間・信頼性検証などの共通設定を採用する。生成済みの`allowBuilds`も内容を確認して統合する |
| 4 | [TypeScript](typescript.md) | 共通の型チェック方針を採用し、バンドラー・JSX・Next.jsの生成型に対応する |
| 5 | [Biome](biome.md) | 共通の検査方針を採用し、Next.js・ReactのDomainsを維持する |
| 6 | [.gitignore](../base/gitignore.md) | 生成された`.next/`・`out/`・`next-env.d.ts`・`*.tsbuildinfo`などの除外を維持し、`!.env.example`を追加する |
| 7 | [コーディング方針](../base/coding-guidelines.md) | 共通規約を採用し、生成されたAGENTS.mdの管理ブロック外から参照する。React固有の追加方針は今後整理する |
| 8 | [aqua](../base/aqua.md) | pinact・Lefthookを共通で採用する。`lint`・`typecheck`はNext.jsのscriptsを使い、フックを登録する |
| 9 | [テスト](../base/testing.md) | BaseのNode.js向けVitest設定・scripts・Biomeのimport制限を採用する。対象はusecase・domainなどのユニットテストとする |
| 10 | [GitHub Actions](../base/github-actions.md) | 権限・SHA固定・実行制御・必須チェックを採用し、`lint`・`typecheck`・`test`・`build`を実行する |
| 11 | [ディレクトリ設計](directory-structure.md) | Baseの責務と依存関係を維持し、ページ固有の実装を近くの`_components`・`_helpers`、共通UIを`src/components`へ置く |
| 12 | [Mantine・Tabler Icons](mantine.md) | CSS・Provider・PostCSSを設定し、必要なアイコンを個別にimportする |
| 13 | [i18n](i18n.md) | next-intlで日本語の文言を管理し、キーと埋め込み引数を型検査する |
| 14 | [環境変数](env.md) | Zodの共通方針を使い、公開範囲と検証する時点を分ける |

初期生成文書の手順で依存をインストールし、型チェック・Lint・ビルドを確認する。
CIのActionはaqua経由のpinactでSHAに固定する。pnpmのセキュリティ設定はNext.jsでも緩めない。

## 用途に応じて採用するもの

PostgreSQLが必要なら、[Docker Compose](../base/docker-compose.md)の設定を共通で使う。
本番をコンテナ化する場合は、[Dockerの共通方針](../base/docker.md)を反映した[Next.js用Dockerfile](docker.md)を使う。

## 今後整理するもの

共通方針を引き継ぐ項目と、未確定のNext.js固有部分は以下のとおり。

| 項目 | 引き継ぐ方針 | Next.jsで整理する内容 |
| --- | --- | --- |
| コーディング方針 | [命名・関数・型・コメント](../base/coding-guidelines.md) | React・Next.js固有の規約 |

環境変数や外部サービスを追加したら、CIの型チェック・ビルドで必要になる設定も合わせて決める。
