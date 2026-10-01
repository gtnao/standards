# Dockerイメージの共通方針

コンテナで本番実行する場合に採用する。ビルド成果物・必要ファイル・起動方法はアプリの構成に合わせる。
具体的なDockerfileは[CLI](../cli/docker.md)を参照。Next.js向けのDockerfileは[今後整理する](../nextjs/README.md#今後整理するもの)。

## バージョンと依存の管理

- ベースイメージはOSの世代・完全バージョン・digestを固定する。修正を取り込む際は固定値も更新する。
- Node.jsのビルド環境と本番環境のバージョンを揃える。
- pnpmの版は[package.json](package-json.md#packagemanager)、依存の解決結果はlockfileで管理する。
- インストールは`--frozen-lockfile`を使い、[pnpmのセキュリティ設定](pnpm-workspace.md)を適用する。
- pnpmの制限は、ベースイメージやpnpm自体の取得には適用されない。取得元と版を別途確認する。

## ビルドと本番実行

マルチステージビルドで、ビルドに必要なものと本番へ渡すものを分ける。
本番には必要な依存と成果物を渡し、開発用ツールや不要なソースを持ち込まない。
本番プロセスは非rootで実行し、秘密情報はイメージへ埋め込まない。

依存定義をソースより先にコピーし、ソース変更だけで依存のインストールをやり直さない構成にする。
パッケージ取得のキャッシュはビルドの高速化に使い、キャッシュがなくてもビルドできるようにする。

## .dockerignore

すべてを除外して、ビルドに必要なファイルだけを`!`で戻す許可方式を採用する。
必要ファイルの追加時にDockerfileの`COPY`と併せて更新する。
許可したディレクトリ内も含め、`.env`類は除外する。ローカルの依存や生成物も持ち込まない。

新しいソースの追跡漏れを避ける[.gitignore](gitignore.md)とは目的が異なるため、方式を分ける。
許可する具体的なファイルは、各構成のDockerfileに合わせる。

## 参考

- [Docker：マルチステージビルド](https://docs.docker.com/build/building/multi-stage/)
- [Docker：イメージの固定](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions)
- [Docker：ビルドキャッシュ](https://docs.docker.com/build/cache/optimize/)
- [Docker：.dockerignore](https://docs.docker.com/build/concepts/context/#dockerignore-files)
