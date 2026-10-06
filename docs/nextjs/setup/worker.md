# Next.jsプロジェクトのWorker

[非同期ジョブの実行方針](../../base/async-jobs.md)に従い、Webとは別のプロセスで共通キューをポーリングする。
[SQS接続とElasticMQ](../../base/elasticmq.md)を用意し、ローカルではWorkerをホストで起動する。

Next.jsと同じ版の`@next/env`と、tsxを開発依存へ追加する。[Prisma](prisma.md)の生成コマンドを使う。

```sh
pnpm add -D -E tsx@<version> @next/env@<Next.jsと同じversion>
```

`package.json`のscriptsへ追加する。

```json
{
  "worker:dev": "pnpm run db:generate && tsx src/entrypoints/worker.ts"
}
```

Workerは明示的に起動・停止する。ファイル変更による自動再起動は初期設定に含めない。
`worker.ts`でNext.jsと同じ版の`@next/env`を使い、`loadEnvConfig(process.cwd(), process.env.NODE_ENV !== "production")`で環境変数を読み込んでから、Zodで検証する。
本番でもこの読み込みを使うなら`@next/env`は実行時依存へ移す。

## Next.jsとの共有部分

既存の`server-only`付きPrisma・envモジュールを、そのままtsxからimportしない。
Workerを追加する際は、Prisma生成部分を`src/prisma/create-client.ts`の`createPrismaClient(databaseUrl)`へ切り出す。
Next.jsの`getPrisma()`は既存の`server-only`境界と再利用処理を保ち、このfactoryを呼ぶ。
Workerはfactoryから作ったクライアントをハンドラーへ渡し、終了時に切断する。

環境変数も、Worker用の検証を`src/env/worker.ts`に置き、共通のスキーマだけ必要に応じて共有する。
WorkerへWeb専用の設定を要求せず、`next/headers`などリクエスト依存のAPIも持ち込まない。
本番WorkerはWebのstandalone出力に自動で含まれるものではないため、デプロイ時はWorker用のビルド・起動対象を別途用意する。

## 参考

- [Next.js：Next.js外での環境変数の読み込み](https://nextjs.org/docs/app/guides/environment-variables#loading-environment-variables-with-nextenv)
