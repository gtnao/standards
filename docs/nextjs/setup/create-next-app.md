# Next.jsの初期生成

公式の`create-next-app`で、TypeScript・App Router・Biomeを使う土台を生成する。
共通規約・aqua・CIまで含む適用順序は[Next.jsの初期設定](../README.md)を参照。

```sh
pnpm create next-app@16.3.5 my-app \
  --ts \
  --app \
  --src-dir \
  --biome \
  --react-compiler \
  --no-tailwind \
  --import-alias '@/*' \
  --empty \
  --use-pnpm \
  --skip-install \
  --disable-git \
  --agents-md
```

`my-app`は作成するディレクトリ名。現在のディレクトリに生成する場合は`.`に置き換える。
生成後に依存バージョンとpnpmの設定を調整し、インストールする。

2026年9月23日の確認時点で最新安定版は`16.3.6`だが、公開から7日未満のため、例では`16.3.5`を使う。
導入時には、[公開から7日間待つ方針](../../base/pnpm-workspace.md#minimumreleaseage)と互換性・修正内容を確認して採用版を更新する。生成先に後から置くpnpm設定が、生成ツール自身の取得まで制御するわけではない。

## 採用するオプション

| オプション | 意味・採用理由 |
| --- | --- |
| `--ts` | TypeScriptで生成する。既定でも有効だが、言語の選択を明示する |
| `--app` | App Routerを使う。新規ではNext.jsが推奨する構成を採用する |
| `--src-dir` | コードを`src/`に置き、ルートの設定ファイルと分ける。App Routerは`src/app/`になる |
| `--biome` | Lint・FormatにBiomeを使う。[既存の方針](../../base/biome.md)に揃える |
| `--react-compiler` | React Compilerによる自動メモ化を有効にする |
| `--no-tailwind` | Tailwind CSSの設定・依存を追加しない |
| `--import-alias '@/*'` | `@/`から`src/`を参照できるようにする。引用符はシェルの`*`展開を防ぐ |
| `--empty` | 装飾や案内を省いた簡素なテンプレートにする。ページ・レイアウト・設定ファイルは生成される |
| `--use-pnpm` | パッケージマネージャーをpnpmに指定する |
| `--skip-install` | 自動インストールを止め、依存バージョンとセキュリティ設定を先に整える |
| `--disable-git` | 自動のGit初期化・初回コミットを止める。設定調整後に行う |
| `--agents-md` | Next.js向けの`AGENTS.md`と、それを参照する`CLAUDE.md`を生成する |

### React Compiler

コンポーネントやHookを解析し、再レンダリング時の不要な計算などを省くためのメモ化を行う。
新規コードではコンパイラーを利用し、必要な場合に`useMemo`・`useCallback`で制御する方針とする。

生成時には`babel-plugin-react-compiler`と、`next.config.ts`の`reactCompiler: true`が追加される。
ビルド処理は増えるが、Next.jsは対象ファイルを絞って適用する。Reactのルールを守る必要があり、ライブラリとの動作確認も引き続き行う。

### Tailwind CSSを使わない理由

AIが生成したコードを人が確認するときの読みやすさを重視する。
多数のユーティリティクラスを読み解くスタイルが好みに合わないため、UIはMantineを基準とし、Tailwind CSSは追加しない。
Mantineの導入自体は、生成後に行う。

### バンドラー

既定のTurbopackを使う。生成されるscriptsは`next dev`・`next build`で、追加フラグは不要。
Rspackは実験的な連携のため、初期設定では選ばない。

### AGENTS.md

生成されるファイルを使う。インストールしたNext.jsと同じ版のドキュメントを、`node_modules/next/dist/docs/`から参照するよう指示する内容になっている。
`CLAUDE.md`は`@AGENTS.md`で同じ内容を参照する。

プロジェクト固有の規約が必要になったら、`AGENTS.md`のNext.js管理ブロックの外に追記する。

## その他の全オプション

採用した項目以外のオプション・別名・実装上の否定形は次のとおり。
`16.3.5`・`16.3.6`の配布パッケージの`--help`とソースを確認した。

| オプション | 意味・今回の扱い |
| --- | --- |
| `--typescript` | `--ts`の別名 |
| `--js`・`--javascript` | JavaScriptで生成する。今回はTypeScriptを使う |
| `--tailwind` | Tailwind CSSを追加する。今回は無効にする |
| `--no-react-compiler` | React Compilerを無効にする。今回は有効にする |
| `--eslint` | ESLintとNext.js向け設定を追加する。今回はBiomeを選ぶ |
| `--no-linter` | Linterを生成しない。今回は使わない |
| `--no-eslint` | Linterを生成しない旧来の指定。使うなら`--no-linter`を選ぶ |
| `--no-app` | Pages Routerで生成する。今回はApp Routerを選ぶ |
| `--api` | Route HandlersだけのAPI用テンプレートを生成する。画面を持つアプリなので使わない |
| `--no-src-dir` | ルートに`app/`などを置く。今回は`src/`を使う |
| `--rspack` | `next-rspack`を追加してRspack連携を設定する。今回は使わない |
| `--no-import-alias` | 別名のカスタマイズを省く。別名自体を削除する指定ではなく、`@/*`が残る |
| `--use-npm`・`--use-yarn`・`--use-bun` | 他のパッケージマネージャーを使う。今回はpnpmを選ぶ |
| `-e`・`--example <名前またはGitHub URL>` | 公式exampleまたは公開GitHubリポジトリから生成する。今回は標準テンプレートを使う |
| `--example-path <パス>` | exampleの場所を別指定する。ブランチ名に`/`を含み、URLの解釈が曖昧になる場合などに使う |
| `--reset`・`--reset-preferences` | 保存済み設定をリセットする。確認後に終了する別操作なので、生成コマンドには混ぜない |
| `--no-agents-md` | エージェント向けファイルの生成を省く。今回は生成する |
| `--yes` | 保存済み設定または既定値で質問を省略する。今回のコマンドでは使わない |
| `-v`・`--version` | `create-next-app`自身の版を表示する |
| `-h`・`--help` | その版のオプション一覧を表示する |

`--example`では取得先の設定が基準になる。標準テンプレート用のTypeScript・Biomeなどのフラグで、exampleの内容まで変更されるとは考えない。

### --yesと保存済み設定

`--yes`は「推奨設定で固定」ではなく、過去の選択を再利用する場合がある。
確認した版では、ディレクトリ名と`--`で始まる設定オプションを渡すと質問を省略し、`--yes`なしなら未指定項目には推奨既定値を使う。
そのため、必要な設定を明示した冒頭のコマンドで生成する。

### 公式ページと配布物の差

確認した版には、公式ページの説明と異なる挙動があった。

- `--turbopack`・`--webpack`は生成CLIに実装されていない。`--webpack`を渡してもscriptsは変わらなかった。Webpackが必要なら、生成後の`next dev --webpack`・`next build --webpack`で指定する。
- `--no-*`が任意の設定を反転するわけではない。公式ページにある`--no-ts`ではJavaScriptにならなかった。JavaScriptを選ぶなら`--js`を使う。
- `--cache-components`は調査時点のcanaryソースにはあるが、今回の安定版にはない。

未対応のフラグでもエラーにならないため、コマンドの成功だけで指定が有効だったとは判断しない。
版を更新するときも、`--help`・対応版の実装・生成結果を確認する。

## 生成後、インストール前に調整すること

生成ツールが新しくても、生成される依存がすべて最新版になるわけではない。
今回の`16.3.5`では、Next.jsは`16.3.5`、Reactは`19.2.8`、Biomeは`2.4.2`、TypeScriptは`^5`、`@types/node`は`^20`だった。

1. [Next.jsのpackage.json設定](package-json.md)に合わせてpnpm・Node.js・scriptsを調整する。生成される`packageManager`は手元のpnpmの版なので、採用版と一致するか確認する。
2. 生成された`pnpm-workspace.yaml`に、[待機期間・信頼性検証などの設定](../../base/pnpm-workspace.md)を反映する。
3. 各依存は、待機期間を満たす互換性のある最新安定版を確認して完全固定する。ReactとReact DOMは同じ版、Node.jsの型は使用するランタイムのメジャーに揃える。
4. [Next.jsのBiome設定](biome.md)に合わせて、`$schema`・推奨ルールの指定・除外設定を調整する。

pnpm 11以降を使った生成では、`allowBuilds`に`sharp: false`と`unrs-resolver: false`が入る。
パッケージ自体を無効にする指定ではなく、インストールスクリプトを実行しない指定。内容を確認して引き継ぎ、他の依存も必要性を確認して個別に判断する。

TypeScriptはNext.jsの対応を確認して採用版を選び、[生成されたtsconfigを土台に調整する](typescript.md)。
[Node.js CLI向けの設定](../../cli/tsconfig.md)で上書きしない。Next.jsではバンドラーによる解決・DOM型・JSX・Next.jsの型生成が必要で、`noEmit: true`にも役割がある。

`.gitignore`にはNext.jsの生成物の除外を残し、[環境変数の方針](../../base/gitignore.md)に合わせて`!.env.example`を追加する。

調整後は生成先でGitを初期化し、依存をインストールする。既にGit管理下なら初期化は不要。

```sh
cd my-app
git init -b main
pnpm install
pnpm exec next typegen
pnpm exec tsc --noEmit
pnpm run lint
pnpm run build
pnpm run dev
```

`--skip-install`では型生成も省略される。生成されたレイアウトが使う`LayoutProps`などのため、独立した型チェックの前に`next typegen`を実行する。

## 参考

- [create-next-app：公式オプション一覧](https://nextjs.org/docs/app/api-reference/cli/create-next-app)
- [npm：create-next-appのバージョンと公開日時](https://registry.npmjs.org/create-next-app)
- [v16.3.6：オプションと設定解決の実装](https://github.com/vercel/next.js/blob/v16.3.6/packages/create-next-app/index.ts)
- [v16.3.5：テンプレートと依存の生成処理](https://github.com/vercel/next.js/blob/v16.3.5/packages/create-next-app/templates/index.ts)
- [React Compiler：新規コードでの使い方](https://react.dev/learn/react-compiler/introduction)
- [Next.js：React Compilerの設定](https://nextjs.org/docs/app/api-reference/config/next-config-js/reactCompiler)
- [Next.js：Rspack連携](https://nextjs.org/docs/community/rspack)
- [Next.js：エージェント向けファイルと同梱ドキュメント](https://nextjs.org/docs/app/guides/ai-agents)
- [next CLI：バンドラーの指定と型生成](https://nextjs.org/docs/app/api-reference/cli/next)
