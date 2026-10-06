# Next.js用Dockerイメージの初期設定

`Dockerfile`・`.dockerignore`を初期構成に含める。
[Dockerの共通方針](../../base/docker.md)に従い、Next.jsのstandalone出力を非rootで実行する。

`next.config.ts`に`output: "standalone"`を追加する。
[next-intlのplugin](i18n.md#nextjs設定と型安全性)を使う場合も、そのラッパーを維持して既存設定へ追加する。

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  output: "standalone",
};

export default nextConfig;
```

ルートに`Dockerfile`を置く。

```dockerfile
FROM node:24.21.0-trixie-slim@sha256:8ec5d7557396cfe32d21c3f9c13072355ceab22b584578ca4bb28af31120cffe AS base
WORKDIR /app

FROM base AS install-base
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN corepack enable pnpm && pnpm --version

FROM install-base AS build
RUN --mount=type=cache,id=my-app-pnpm,target=/pnpm/store,sharing=locked \
    pnpm install --store-dir=/pnpm/store --frozen-lockfile
RUN test "$(pnpm exec node --version)" = "$(/usr/local/bin/node --version)"
COPY . .
RUN mkdir -p public && pnpm run build

FROM base AS runtime
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
COPY --from=build /app/.next/standalone ./
RUN mkdir -p .next/cache && chown -R node:node .next
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
```

Nodeの版・digestは検証時の例。導入時はlockfileで確定したNodeと一致させ、対応するイメージのdigestを確認する。
`my-app-pnpm`はプロジェクトに合わせたキャッシュ名にする。

## .dockerignore

共通方針と同じ許可方式で、ビルドへ渡すファイルを限定する。

```dockerignore
**

!package.json
!pnpm-lock.yaml
!pnpm-workspace.yaml
!tsconfig.json
!next.config.ts
!postcss.config.mjs
!messages/
!messages/**
!src/
!src/**
!public/
!public/**

messages/*.d.json.ts
**/.env
**/.env.*
```

この指定と組み合わせるため、`COPY . .`の対象は許可したファイルに限定される。
ローカルの`node_modules`・`.next`は持ち込まない。末尾の指定で、src・public内も含めて`.env`類を除外する。
[MantineのPostCSS設定](mantine.md#スタイルとpostcss)と[next-intlのメッセージ](i18n.md)も許可する。翻訳の型宣言はビルドで生成するため、ローカルの生成物は除外する。
ビルドに必要な設定やファイルが増えたら、許可対象に追加する。
Prismaを導入した場合は、[schema・CLI設定の追加とイメージ内での生成](prisma.md#ciとdocker)も反映する。

## 採用理由とCLI構成との差分

| 項目 | 判断・理由 |
| --- | --- |
| ベースイメージ | Node公式のDebian slimを使い、OSの世代・Nodeの完全バージョン・digestを固定する |
| `install-base` | Node 24に同梱されたCorepackで、package.jsonの`packageManager`に従ってpnpmを取得する |
| 依存のインストール | 開発依存も含めてビルド側で一度行う。standaloneに必要な実行時依存が含まれるため、CLI構成の`prod-deps`や`prune`は不要 |
| キャッシュ | 依存定義を先にコピーし、ソース変更時にインストールのレイヤーを再利用する。再インストール時にはpnpmストアのキャッシュを使う |
| Nodeの比較 | pnpmが用意したビルド用Nodeと本番のNodeの完全バージョンが異なれば、ビルドを止める |
| `mkdir -p public` | `--empty`の生成直後にはpublicがないため、最終ステージのCOPYが成立するよう空ディレクトリを用意する。既存の内容は保持する |
| standalone | 必要な依存とサーバーをまとめた成果物を本番へ渡す。元のnode_modules全体をコピーしない |
| public・`.next/static` | standaloneには自動で含まれないため別途コピーし、同じサーバーから配信する |
| 起動方法 | standaloneの`server.js`をNodeで直接起動する。コンテナでは`next start`を使わない |
| `PORT`・`HOSTNAME` | 3000番で、コンテナ外から接続できるアドレスにバインドする。`EXPOSE`自体はホストへのポート公開を行わない |
| OSパッケージ | 検証した構成では追加不要。ネイティブ依存を追加したときは、その実行要件を確認する |

インストールには[共通のpnpm設定](../../base/pnpm-workspace.md)を適用する。
`allowBuilds`は生成された設定を確認して引き継ぎ、新しい依存は個別に判断する。
CorepackはNode 25以降に同梱されないため、Nodeのメジャーを変更する際は導入方法も見直す。

## 非root実行と書き込み先

Nodeイメージの既存ユーザー`node`で実行する。
`server.js`・node_modules・publicはroot所有を維持する。

Next.js標準のディスクキャッシュを使うため、`.next`は`node`所有にする。
画像最適化は`.next/cache`、ISRは`.next/server/app`などにも書き込むので、cacheだけへの書き込み許可では足りない。
`.next/static`はその後にroot所有でコピーするが、親の`.next`は書き込み可能なので、`.next`全体を変更不可にする構成ではない。

`.next`には生成されたサーバーコードも含まれる。ここはCLI構成の「成果物全体をroot所有にする」方針との差分であり、標準のキャッシュ保存先に合わせた選択。
読み取り専用ファイルシステムや複数インスタンスで運用する場合は、キャッシュの保存先・共有・無効化を別途設計する。

## ビルド・実行

```sh
docker build -t my-app .
docker run --rm --init -p 127.0.0.1:3000:3000 my-app
```

ローカルで環境変数が必要なら、runに`--env-file .env`を追加する。本番は[Next.jsの環境変数方針](env.md)に従って渡す。
サーバー側でも静的生成時に参照する値はビルドに影響する。`NEXT_PUBLIC_*`はビルド時に埋め込まれるため、実行時の差し替えを前提にしない。
必要なビルド時変数は用途ごとに追加し、秘密情報をDockerfileの`ARG`・`ENV`へ埋め込まない。

依存や構成を変更した場合は、standaloneに必要なファイルが含まれるかと、実行時の書き込み権限を確認する。

## 参考

- [Next.js：standalone出力](https://nextjs.org/docs/app/api-reference/config/next-config-js/output)
- [Next.js：Dockerの公式例](https://github.com/vercel/next.js/blob/v16.3.6/examples/with-docker/Dockerfile)
- [Next.js：セルフホスティングとキャッシュ](https://nextjs.org/docs/app/guides/self-hosting)
- [Next.js：環境変数](https://nextjs.org/docs/app/guides/environment-variables)
