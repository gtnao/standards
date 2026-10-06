# SQSとWorkerによる非同期ジョブ

共通のSQS StandardキューをWorkerがポーリングする。ローカルではElasticMQをComposeで起動し、Workerはホスト上の別プロセスとして動かす。
SQSは実行を促す通知、DBは状態・実行権・結果の正とする。

計算の重複は許容し、有効な実行権を持つ処理だけが業務データを確定できるようにする。

## メッセージとテーブル

メッセージには種別とIDだけを載せる。Workerは種別からハンドラーを選び、必要なデータをDBから取得する。

```json
{ "job_type": "document-extraction", "job_id": "..." }
```

受信本文はZodで検証し、登録済みの種別だけを受け付ける。
テーブル名をメッセージから組み立てず、ハンドラー内で固定する。

ジョブの種類ごとにテーブルを持ち、共通の親テーブルは作らない。
[Prismaの命名](../nextjs/implementation/prisma.md#schemaの命名)に従い、DBはsnake_case・複数形、PrismaはlowerCamelCaseのフィールドへ対応付ける。

| DBのカラム | 用途 |
| --- | --- |
| `id` | ジョブID |
| `status` | `pending` / `running` / `succeeded` / `failed` |
| `attempt_token` | 実行権の取得ごとに生成するUUID |
| `lease_until` | 実行権の期限。実行中以外はNULL |
| `created_at` / `updated_at` | 登録・更新日時 |
| `finished_at` | 成功・最終失敗の確定日時 |
| `last_error` | 秘密情報を除いた最終エラーコード・説明 |

日時はPostgreSQLの`timestamptz`で持つ。
固有の入力・結果は、検索や制約が必要ならカラム・子テーブル、まとまりとして扱うならJSONカラムに置く。
定期的な走査を導入する場合は、滞留した`pending`には`(status, created_at)`、リース切れには`(status, lease_until)`など、取得条件に合わせた索引を用意する。
SQLで更新する箇所ではPrismaの`@updatedAt`に任せず、`updated_at`も更新する。

## 登録と実行

1. 入力・権限を検証し、ジョブを`pending`で登録してCOMMITする。
2. COMMIT後にSQSへ種別とIDを送信する。
3. Workerが条件付きUPDATEで実行権を取得する。
4. DBトランザクション外で処理し、heartbeatでリースとvisibilityを延長する。
5. 短いトランザクションで実行権を検証し、業務更新と`succeeded`を同時にCOMMITする。
6. COMMIT後に、今回の受信で得たreceipt handleを使ってメッセージを削除する。

送信失敗でDB登録を取り消したことにしない。既存IDへの再送と新規登録を区別し、呼び出し側にも登録済みのIDを残す。
登録操作自体の重複防止が必要な業務では、リクエストの冪等キー・DBの一意制約を設ける。
登録後のpayloadは原則変更せず、変更した内容を処理したい場合は新しいジョブとして登録する。

## 実行権の取得と延長

条件付きUPDATE自体はPrismaの`updateMany`でも表現できる。
ここではDBの`clock_timestamp()`を条件判定・期限計算に使い、結果確定では`SELECT ... FOR UPDATE`で行ロックを取得するため、通常のPrisma APIでは直接表現できない部分にRaw SQLを使う。
アプリ側の`new Date()`で代用せず、Worker間の時計差やロック待ち中の時間経過をDB側で扱う。通常の業務更新にはPrismaのAPIを使う。

実行権は`pending`またはリース切れの`running`に対する条件付きUPDATEで取得する。
以下は`document_extraction_jobs`での例。`id`と`attempt_token`をUUIDとする。

```ts
const attemptToken = randomUUID();
const claimed = await prisma.$queryRaw<{ id: string }[]>`
  UPDATE document_extraction_jobs
  SET status = 'running',
      attempt_token = ${attemptToken}::uuid,
      lease_until = clock_timestamp() + ${leaseSeconds} * interval '1 second',
      updated_at = clock_timestamp()
  WHERE id = ${jobId}::uuid
    AND (
      status = 'pending'
      OR (status = 'running' AND lease_until <= clock_timestamp())
    )
  RETURNING id
`;
```

`randomUUID`は`node:crypto`からimportする。SQLはPrismaのタグ付きテンプレートで値をバインドし、文字列連結しない。
取得できた1件だけを実行する。事前のSELECTだけで実行可否を決めない。

取得できなければ状態を読み、次のように扱う。

| 状態 | 対応 |
| --- | --- |
| `succeeded` / `failed` | 削除する |
| 有効な`running` | 削除せず、残りリース時間を目安にvisibilityを変更する |
| IDなし・不正形式・未知の種別 | 理由を記録し、削除せずDLQへ隔離されるまで再配信に任せる |
| 読み取り中に状態が変わった・DB障害 | 削除せず、待機して再配信に任せる |

未対応の種別が混在しないよう、ハンドラーを持つWorkerのデプロイ後に、その種別の送信を開始する。

リース延長も条件付きUPDATEにする。

```ts
const renewed = await prisma.$executeRaw`
  UPDATE document_extraction_jobs
  SET lease_until = clock_timestamp() + ${leaseSeconds} * interval '1 second',
      updated_at = clock_timestamp()
  WHERE id = ${jobId}::uuid
    AND status = 'running'
    AND attempt_token = ${attemptToken}::uuid
    AND lease_until > clock_timestamp()
`;
```

更新件数が1でなければ実行権を失っている。期限切れのリースを延長して復活させない。

## heartbeatと結果確定

heartbeatは、DBリース延長の成功後にSQSのvisibilityを延長する。
両方を原子的には更新できないため、DB側の実行権で結果反映を守る。
延長できない・成功したか分からない場合は処理を中断し、結果反映とメッセージ削除を行わない。
外部呼び出しにはAbortSignalを渡す。中断に対応しない処理が完了しても、その結果を確定させない。

非同期の`setInterval`で更新を重ねず、「待機 → 延長 → 待機」の直列ループにする。
結果確定前にheartbeatを停止し、実行中の延長が終わるまで待つ。

結果確定は行ロックを取得してから、DBの現在時刻で実行権を検証する。
以下の`applyResult`は、同じ`tx`で業務更新する処理を表す。

```ts
const committed = await prisma.$transaction(async (tx) => {
  await tx.$queryRaw`
    SELECT id FROM document_extraction_jobs
    WHERE id = ${jobId}::uuid
    FOR UPDATE
  `;

  const owned = await tx.$queryRaw<{ id: string }[]>`
    SELECT id FROM document_extraction_jobs
    WHERE id = ${jobId}::uuid
      AND status = 'running'
      AND attempt_token = ${attemptToken}::uuid
      AND lease_until > clock_timestamp()
  `;
  if (owned.length === 0) return false;

  await applyResult(tx, result);
  await tx.documentExtractionJob.update({
    where: { id: jobId },
    data: {
      status: 'succeeded',
      leaseUntil: null,
      finishedAt: new Date(),
    },
  });
  return true;
});
```

リース判定にはトランザクション開始時刻の`now()`ではなく、評価時点の`clock_timestamp()`を使う。
行ロック待ちの間に期限切れになった実行権で確定しないため、検証はロック取得後に行う。
以降はCOMMITまで行ロックが他の実行権取得を防ぐ。分離レベルはDBの設定を使い、一律に変更しない。
トランザクション内で外部APIや重い計算を実行しない。

COMMIT済みなら削除する。削除失敗は業務処理を巻き戻さず、再配信時に完了状態を確認して削除する。
COMMITの成否が通信障害で不明ならDBを再確認し、確認できなければ削除しない。
**結果確定の例外を、処理失敗として`pending`へ戻すcatchに流さない。**

## 失敗と再試行

再試行可能な処理失敗では、自分の有効なトークンを条件に`pending`へ戻し、リースを解除する。
受信したメッセージのvisibilityを変更して、再配信まで待機する。
同じジョブの別メッセージにはこの待機が効かないため、予定より早い再実行は許容する。

恒久的な失敗は、実行権を検証して`failed`へ確定し、COMMIT後に削除する。
未知の処理エラーは再試行し、繰り返し受信されるメッセージはSQSの`maxReceiveCount`でDLQへ移す。エラーの分類はジョブの処理内容に応じて決める。
実行権を失ったWorkerは、失敗状態の書き込みも行わない。

試行回数はDBで管理しない。SQSの受信回数は実処理の回数とは異なり、他のWorkerが処理中の受信でも増える。
DLQへ移った後も、DBには`pending`やリース切れの`running`が残り得る。

外部APIの更新・メール送信など、DBトランザクション外の副作用には処理ごとの冪等性設計が必要。
必要なら外部サービスの冪等キーなどを使い、DBのトークンだけで外部の副作用まで防げるとは考えない。

## Workerとハンドラーの配置

```text
src/
  entrypoints/
    worker.ts
    worker/
      run-worker.ts
      process-message.ts
  ports/
    job-queue.ts
  adapters/
    sqs-job-queue.ts
  usecases/
    jobs/
      handler.ts
      document-extraction.ts
```

| 配置 | 責務 |
| --- | --- |
| `worker.ts` | 環境変数の読み込み、依存・ハンドラー登録、起動 |
| `run-worker.ts` | long polling、並列数、受信エラーのbackoff、SIGTERM/SIGINT |
| `process-message.ts` | 1受信の制御、heartbeat、結果確定後の削除 |
| `handler.ts` | 共通Workerが呼び出す取得・延長・実行・成功確定・失敗確定の契約 |
| 種別ごとのusecase | 対応テーブルの操作と業務処理。Prismaを直接使う |
| queueのport／adapter | 送信・受信・削除・visibility変更 |

ハンドラー契約は共通Workerから利用するusecaseの公開APIであり、DBを隠すrepositoryではない。
実行権取得後の操作は、取得したID・トークンを閉じ込めたオブジェクトとして返す。

```ts
export type JobAttempt<Result> = {
  renew(): Promise<boolean>;
  execute(input: { signal: AbortSignal }): Promise<Result>;
  succeed(input: { result: Result }): Promise<boolean>;
  fail(input: { error: unknown }): Promise<
    | { status: "retry"; retryAfterSeconds: number }
    | { status: "failed" }
    | { status: "lost" }
  >;
};

export type JobHandler<Result> = {
  claim(input: { jobId: string }): Promise<
    | { status: "acquired"; attempt: JobAttempt<Result> }
    | { status: "terminal" }
    | { status: "deferred"; retryAfterSeconds: number }
    | { status: "missing" }
  >;
};
```

`succeed`の`false`と`fail`の`lost`は、実行権を失って反映できなかったことを表す。
接続障害・COMMIT成否不明は例外とし、実行権喪失や成功へ読み替えない。
`fail`は処理失敗を受け、種別ごとのエラー分類から再試行か最終失敗を決める。
結果型はハンドラーごとのジェネリックで保ち、種別を登録するときに共通の処理へ結び付ける。全ジョブのpayload・結果を一つの巨大な型にまとめない。

queueの受信結果には本文とreceipt handleを含める。削除・延長にはメッセージIDではなく、その受信のreceipt handleを渡す。
SQSとElasticMQでadapterを分けず、接続設定だけを変える。

受信件数は空いている実行枠以下かつSQSの上限10件以下にする。
空きがなければ処理の終了を待ち、受信したままローカルの待ち行列に溜めない。
long pollingの待機は20秒を基本とし、HTTPのタイムアウトはそれより長くする。

SIGTERM/SIGINTでは新規受信を停止し、処理中のheartbeatを継続したまま猶予時間まで完了を待つ。
猶予後は処理とheartbeatを中断し、未確定のメッセージを削除せず終了する。
受信キャンセルと処理キャンセルは別のAbortControllerで管理し、受信を止めただけで処理中ジョブを中断しない。

## 時間と回数の設定

値は設定へまとめる。以下は初期値の例であり、処理時間・外部APIの応答時間に合わせて調整する。

| 設定 | 例 |
| --- | --- |
| Workerの同時実行数 | 2 |
| DBリース | 60秒 |
| heartbeatの待機間隔 | 15秒 |
| SQS visibility | 90秒 |
| SQSのDLQ移動までの受信回数 | 10 |
| 再試行待機 | 30秒 |
| 停止時の猶予 | 30秒 |

heartbeatの間隔だけでなく、DB・SQSへの通信時間を含めてリース内に更新できる余裕を持たせる。
各I/Oに有限のタイムアウトを設け、処理全体の期限もジョブ種別ごとに必須とする。heartbeatで永久に実行権を保持させない。
visibilityの延長には最初の受信から12時間の上限がある。これを超える処理は分割する。

## ElasticMQとローカル起動

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
pnpm add -D tsx
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

Next.jsプロジェクトのscripts：

```json
{
  "worker:dev": "pnpm run db:generate && tsx src/entrypoints/worker.ts"
}
```

Workerは明示的に起動・停止する。ファイル変更による自動再起動は初期設定に含めない。
`worker.ts`でNext.jsと同じ版の`@next/env`を使い、`loadEnvConfig(process.cwd(), process.env.NODE_ENV !== "production")`で環境変数を読み込んでから、Zodで検証する。
本番でもこの読み込みを使うなら`@next/env`は実行時依存へ移す。

### Next.jsとの共有部分

既存の`server-only`付きPrisma・envモジュールを、そのままtsxからimportしない。
Workerを追加する際は、Prisma生成部分を`src/prisma/create-client.ts`の`createPrismaClient(databaseUrl)`へ切り出す。
Next.jsの`getPrisma()`は既存の`server-only`境界と再利用処理を保ち、このfactoryを呼ぶ。
Workerはfactoryから作ったクライアントをハンドラーへ渡し、終了時に切断する。

環境変数も、Worker用の検証を`src/env/worker.ts`に置き、共通のスキーマだけ必要に応じて共有する。
WorkerへWeb専用の設定を要求せず、`next/headers`などリクエスト依存のAPIも持ち込まない。
本番WorkerはWebのstandalone出力に自動で含まれるものではないため、デプロイ時はWorker用のビルド・起動対象を別途用意する。

## 定期的な整合処理とDLQ

登録後の送信漏れを回復する定期処理はオプショナル。
未導入では、送信漏れ・キューの保持期限切れなどによりDBへジョブが残っても、自動回復は保証しない。
SQSにはDBのトークンによる結果確定とは別に、保持期間とDLQの監視を設定する。

DLQへの移動だけでDBを`failed`にはしない。初期段階では監視と手動対応にする。
再投入前にDBの状態・実行権を確認し、成功済みや有効な実行中ジョブを上書きしない。

定期再送を導入する場合は、滞留した`pending`を無条件に再送しない。DLQ隔離済みの通知まで復活させないよう、再送の上限・対象・運用を合わせて決める。
DLQからの自動失敗確定も、古い通知と現在の再実行を区別できる世代管理などを設計してから導入する。

## 参考

- [ElasticMQ：設定・SQS互換API](https://github.com/softwaremill/elasticmq)
- [SQS：重複配信](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues-at-least-once-delivery.html)
- [SQS：visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
- [SQS：long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html)
- [SQS：DLQ](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
- [SQS：receipt handleによる削除](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_DeleteMessage.html)
- [PostgreSQL：現在時刻の関数](https://www.postgresql.org/docs/current/functions-datetime.html)
