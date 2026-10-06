# SQS接続とローカルのElasticMQ

[非同期ジョブの実行方針](async-jobs.md)に従い、ローカルではElasticMQを使う。

[PostgreSQLのCompose](docker-compose.md)へ次のサービスを追加し、ルートに`elasticmq.conf`を置く。

```yaml
services:
  elasticmq:
    image: softwaremill/elasticmq-native:1.7.1@sha256:e4580ab9ad1bd5cd37b4ba04911bc5ccc8cd2d9ab4de56ece65acee71c24e05c
    ports:
      - "127.0.0.1:${SQS_PORT:-9324}:9324"
    volumes:
      - ./elasticmq.conf:/opt/elasticmq.conf:ro
```

```hocon
include classpath("application.conf")
node-address.host = "*"
rest-sqs.bind-hostname = "0.0.0.0"
queues {
  jobs {
    defaultVisibilityTimeout = 90 seconds
    receiveMessageWait = 20 seconds
    deadLettersQueue {
      name = "jobs-dlq"
      maxReceiveCount = 10
    }
  }
  jobs-dlq {}
}
```

起動時に共通キューとDLQを作る。ローカルのキューは使い捨てとし、この例では永続化しない。
再作成するとDBに残るジョブの通知が失われ得るため、開発時は対象IDを再送するか、テスト用データを作り直す。
イメージは[Dockerの固定方針](docker.md#バージョンと依存の管理)に従って更新する。

`.env.example`へ追加する。

```dotenv
SQS_REGION=ap-northeast-1
SQS_ENDPOINT=http://127.0.0.1:9324
SQS_QUEUE_URL=http://127.0.0.1:9324/000000000000/jobs
```

ポートを変更する場合は`SQS_PORT`・endpoint・queue URLを揃える。
Zodでregionを非空文字列、endpointとqueue URLをURLとして検証する。endpointは省略可能にし、空文字は未指定へ変換する。

```sh
pnpm add @aws-sdk/client-sqs
```

adapterで生成するクライアント：

```ts
const client = new SQSClient({
  region: config.region,
  ...(config.endpoint
    ? {
        endpoint: config.endpoint,
        credentials: { accessKeyId: "local", secretAccessKey: "local" },
      }
    : {}),
});
```

`SQS_ENDPOINT`はローカルのElasticMQ専用とし、本番では未指定にする。
本番はAWS SDKの標準認証チェーンでIAM Roleを使う。ローカルの仮認証情報はSQSクライアントにだけ渡し、環境変数のAWS認証情報を上書きしない。
これにより、同じWorkerから[Bedrock](ai-sdk.md#環境変数と認証)へProfile認証で接続できる。

adapterは`SendMessageCommand`・`ReceiveMessageCommand`・`DeleteMessageCommand`・`ChangeMessageVisibilityCommand`へ対応付ける。
Workerの受信ループを開始する前に`GetQueueAttributesCommand`で接続先キューを確認する。Composeの起動完了だけでAPIの準備完了と判断しない。

WorkerをNext.jsと同じプロジェクトで動かす場合は、[Workerの設定](../nextjs/setup/worker.md)も適用する。

## 参考

- [ElasticMQ：設定・SQS互換API](https://github.com/softwaremill/elasticmq)
- [AWS SDK：認証情報の標準チェーン](https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/setting-credentials-node.html)
