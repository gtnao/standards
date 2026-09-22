# 本番用Dockerイメージの初期設定

TypeScriptをtscでビルドし、生成したJavaScriptをNode.jsで実行する構成。
[Vitestの設定](vitest.md#型チェックとビルドを分ける)に合わせ、`pnpm run build`は`tsc -p tsconfig.build.json`を実行する。

ルートに`Dockerfile`を置く。

```dockerfile
FROM node:24.20.0-trixie-slim@sha256:50c3b2f6988dfc307b86e5301d69611af31f4789bdf232863b07d3b02fe55ae0 AS base
WORKDIR /app

FROM base AS install-base
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN corepack enable pnpm && pnpm --version

FROM install-base AS build
RUN --mount=type=cache,id=my-app-pnpm,target=/pnpm/store,sharing=locked \
    pnpm install --store-dir=/pnpm/store --frozen-lockfile
RUN test "$(pnpm exec node --version)" = "$(/usr/local/bin/node --version)"
COPY tsconfig.json tsconfig.build.json ./
COPY src/ ./src/
RUN pnpm run build

FROM install-base AS prod-deps
RUN --mount=type=cache,id=my-app-pnpm,target=/pnpm/store,sharing=locked \
    pnpm install --store-dir=/pnpm/store --prod --frozen-lockfile --no-runtime

FROM base AS runtime
ENV NODE_ENV=production
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER node
CMD ["node", "--enable-source-maps", "dist/index.js"]
```

Nodeのバージョン・digestは検証済みの例。導入時にはlockfileで確定したNodeに合わせ、対応するイメージのdigestを確認する。
`my-app-pnpm`はプロジェクトに合わせたキャッシュ名に置き換える。

## .dockerignore

ルートに`.dockerignore`を置き、ビルドへ渡すファイルを限定する。

```dockerignore
**

!package.json
!pnpm-lock.yaml
!pnpm-workspace.yaml
!tsconfig.json
!tsconfig.build.json
!src/
!src/**

**/.env
**/.env.*
```

最初の`**`ですべて除外し、`!`で必要なものを戻す。複数の規則が一致した場合は、後の指定が優先される。
末尾の指定で、許可した`src/`内も含めて`.env`類を除外する。

この方式なら、READMEやインフラ設定などが増えても、その都度除外を追加する必要がない。
ビルドに必要なファイルが増えたときに、許可対象とDockerfileの`COPY`を追加する。
[.gitignore](gitignore.md)とは目的が異なり、こちらはビルドへ渡す対象を絞るため許可方式を選ぶ。

`src/**`にはテストも含まれる。本番への混入は`tsconfig.build.json`と、最終ステージへコピーする対象で制御する。
ローカルの`node_modules/`や`dist/`は渡さず、コンテナ内で作成する。

## ステージを分ける理由

| ステージ | 役割 |
| --- | --- |
| `base` | ビルド・本番で共通のNodeと作業ディレクトリ |
| `install-base` | pnpmの導入と依存定義の配置 |
| `build` | 開発依存も含めてインストールし、`dist/`を生成する |
| `prod-deps` | 本番依存だけをインストールする |
| `runtime` | 本番依存・生成物・`package.json`を受け取り、実行する |

ビルド後に`pnpm prune --prod`で開発依存を削除する方法もある。
今回は、本番依存をビルド処理から独立して用意する方針で、別インストールを選ぶ。
ビルド中に`node_modules`へ加わった変更を引き継がず、ソース変更だけなら本番依存のステージはキャッシュされる。
その分、インストール処理は2回になるため、取得済みパッケージを次のキャッシュで共有する。

## キャッシュの使い分け

依存定義をソースより先に`COPY`することで、ソースだけの変更ではインストールのレイヤーを再利用できる。
`pnpm --version`も共通ステージで実行し、Corepackによるpnpmの取得を済ませておく。

インストールを実行し直す場合には、`--mount=type=cache`で取得済みパッケージを再利用する。

| 指定 | 意味 |
| --- | --- |
| `type=cache` | ビルド間で再利用できるキャッシュを使う |
| `id=my-app-pnpm` | キャッシュの識別名。両ステージで同じ名前を指定する |
| `target=/pnpm/store` | この`RUN`中にキャッシュを接続する場所 |
| `sharing=locked` | 同じキャッシュを使う他の`RUN`が終わるまで待つ |
| `--store-dir=/pnpm/store` | pnpmのストアを接続先に合わせる |

共有するのは`node_modules`ではなく、その作成に使うパッケージのストア。
`build`と`prod-deps`が同時に開始した場合、キャッシュを使うインストール処理は順番に実行される。

キャッシュは最終イメージに含まれず、なくてもビルドできる。別のビルドマシンへ自動で引き継がれるものでもない。
同じビルダーで同じIDを使う処理が共有対象になるため、信頼できないビルドと共有しない。

## バージョンと依存の管理

Node公式のDebian slimを使う。AlpineとのCライブラリの違いによる互換性への配慮を減らしつつ、OSの同梱パッケージを絞る選択。
`trixie`でDebianの世代、完全バージョンでNodeの版、digestでイメージの内容を固定する。
OSの修正を取り込むときもdigestを更新する。

pnpmはNode 24に同梱されたCorepackで導入し、[package.jsonの`packageManager`](package-json.md#packagemanager)に従う。
Dockerfileへのバージョンの重複記載や、pnpmの配布ファイルの手動コピーを避けられる。
Node 25以降にはCorepackが同梱されないため、移行時には導入方法も見直す。

| 指定 | 意味・理由 |
| --- | --- |
| `--frozen-lockfile` | コミット済みのlockfileを使い、不在・不整合をエラーにする |
| `--prod` | 本番依存だけをインストールする |
| `--no-runtime` | 本番のNodeはベースイメージにあるため、pnpmによるランタイムの取得・リンクを省略する |
| `RUN test ...` | pnpmが用意したビルド用Nodeと、本番イメージのNodeの完全バージョンを比較し、不一致なら止める |

アプリの依存には[pnpm-workspace.yamlの制限](pnpm-workspace.md)が適用される。
その制限がCorepackによるpnpmの初期取得や、ベースイメージの取得にも適用されるわけではない。

## 本番実行

| 設定 | 意味・理由 |
| --- | --- |
| `NODE_ENV=production` | 依存ライブラリなどに本番実行であることを伝える。ビルド用ステージには設定しない |
| `USER node` | 本番プロセスを非rootで実行する |
| root所有のアプリファイル | 実行ユーザーにコードへの書き込み権限を与えない |
| 配列形式の`CMD` | シェルやパッケージマネージャーを挟まず、Nodeを起動する |
| `--enable-source-maps` | `dist/`内のsource mapを使い、エラー位置をTypeScriptへ対応付ける |
| 本番への`package.json`のコピー | `"type": "module"`を反映する |

ローカルでのビルド・動作確認例：

```sh
docker build -t my-app .
docker run --rm --init --env-file .env my-app
```

`--init`は、シグナルの転送や終了した子プロセスの回収を行う軽量なinitを使う指定。
実際の処理を安全に中断するための後始末は、アプリ側で実装する。

`.env`はイメージに含めず、[環境変数の方針](env.md)に従って実行時に値を渡す。
上の`.env`はローカルの動作確認用。本番では実行環境から設定値を渡す。
秘密情報をDockerfileの`ARG`・`ENV`に埋め込まない。

バッチも想定するため、`EXPOSE`やHTTPの`HEALTHCHECK`は初期設定に含めない。
依存にネイティブビルドが必要になればOSのツール・ライブラリを追加する。
Prismaの生成処理や自作の`prepare`などを追加した場合も、インストール時に必要なファイルと本番へ渡す生成物を見直す。

## 参考

- [Docker：マルチステージビルド](https://docs.docker.com/build/building/multi-stage/)
- [Docker：キャッシュの使い方](https://docs.docker.com/build/cache/optimize/)
- [Docker：.dockerignore](https://docs.docker.com/build/concepts/context/#dockerignore-files)
- [Docker：イメージの固定](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions)
- [Node：公式イメージの種類](https://github.com/nodejs/docker-node/blob/main/README.md#image-variants)
- [Node：非root実行・シグナル・起動方法](https://github.com/nodejs/docker-node/blob/main/docs/BestPractices.md)
- [Corepack：導入とpackageManager](https://github.com/nodejs/corepack#readme)
- [pnpm：Dockerの構成例](https://pnpm.io/docker)
- [pnpm：installのオプション](https://pnpm.io/cli/install)
- [pnpm：prune](https://pnpm.io/cli/prune)
