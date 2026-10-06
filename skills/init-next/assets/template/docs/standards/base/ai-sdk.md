# AI SDKとAmazon Bedrock

LLMの呼び出しは[portsとadapters](directory-structure.md#portsとadapters)で分ける。
usecaseはモデル・プロンプト・出力スキーマ・Toolを指定し、adapterがBedrockに接続する。
テストではportを満たす実装を渡し、生成結果やエラーを制御する。

## 導入

AI SDK 7系を前提とする。導入する版は[pnpmの待機期間](pnpm-workspace.md)と互換性を確認して選ぶ。

```sh
pnpm add ai @ai-sdk/amazon-bedrock @aws-sdk/credential-providers zod
```

```text
src/
  ports/
    llm.ts
  adapters/
    bedrock-llm.ts
  usecases/
    ...
```

プロンプト・操作固有の出力スキーマ・Toolは利用するusecaseの近くに置く。
複数の処理で共通の意味を持つ型やルールだけ、責務に応じてdomainなどへ切り出す。

## 環境変数と認証

ローカルではAWS Profile、本番では実行環境に付与したIAM Roleを使う。
アクセスキーをアプリの設定として渡さない。

`.env.example`へ追加する項目：

```dotenv
BEDROCK_REGION=ap-northeast-1
# ローカルで使用するAWS Profile。本番では設定しない
AWS_PROFILE=
```

[環境変数の方針](env.md)に従い、既存のZodスキーマへ追加する。
Next.jsでは[サーバー用の定義](../nextjs/setup/env.md)に置く。

```ts
BEDROCK_REGION: z.string().trim().min(1),
AWS_PROFILE: z.string().trim().transform((value) => value || undefined).optional(),
```

入口で検証済みの値からadapterを作り、usecaseの`deps.llm`へ渡す。

```ts
const llm = createBedrockLlm({
  region: env.BEDROCK_REGION,
  profile: env.AWS_PROFILE,
});
```

adapter内のprovider生成は以下とする。

```ts
import { createAmazonBedrock } from "@ai-sdk/amazon-bedrock";
import { fromNodeProviderChain } from "@aws-sdk/credential-providers";

const provider = createAmazonBedrock({
  region: config.region,
  credentialProvider: fromNodeProviderChain(
    config.profile ? { profile: config.profile } : {},
  ),
});
```

`config`はadapter生成時の`{ region: string; profile?: string }`。
Profile指定時はそのProfileを使い、省略時はAWSの標準認証チェーンで実行環境の認証情報を取得する。
認証情報は一度取得して固定せず、provider関数を渡して一時認証情報の更新に対応する。
SSOのProfileなら、ローカルでは事前に`aws sso login --profile <名前>`を実行する。

本番にはローカル用Profile・静的アクセスキー・`AWS_BEARER_TOKEN_BEDROCK`を設定しない。
特にBearer tokenはBedrock providerでIAM認証より優先される。
IAM Roleには利用するモデル・推論プロファイルに必要な推論権限を付与する。

## portのメソッド

| メソッド | 返すもの | adapterで使うAPI |
| --- | --- | --- |
| `generateText` | 完成したテキスト・使用量・終了理由 | `generateText` |
| `generateObject` | Zodで検証した出力・使用量・終了理由 | `generateText` + `Output.object` |
| `streamText` | 生成イベントと完成結果 | `streamText` |
| `streamObject` | 生成途中の構造化データと完成結果 | `streamText` + `Output.object` |

Toolは各メソッドのオプションとして組み合わせる。Tool付き・構造化出力付きといった組み合わせごとにメソッドを増やさない。
portの`generateObject`という名前は独自の契約であり、SDKの旧`generateObject`・`streamObject`は使わない。

`ModelMessage`・`ToolSet`・`LanguageModelUsage`など、AI SDKの型はportで利用してよい。
目的は外部呼び出しをテストで制御できること。会話やToolの型体系を独自に作り直さない。
Bedrock固有のオプションへの変換はadapterへ閉じ込める。

共通の呼び出し条件は`ports/llm.ts`で定義する。

```ts
import type { ModelMessage, ToolSet } from "ai";

export type LlmMessage = ModelMessage & {
  cacheAfter?: { ttl: "5m" | "1h" };
};

export type LlmRequest = {
  modelId: string;
  messages: LlmMessage[];
  maxOutputTokens?: number;
  abortSignal?: AbortSignal;
  execution?: {
    tools: ToolSet;
    maxSteps: number;
  };
};
```

モデルは呼び出すたびに`modelId`で指定し、adapter内で`provider(modelId)`を作る。
モデルIDに加え、Bedrockの推論プロファイルIDも指定できる。
モデルごとに構造化出力・Tool・キャッシュの対応が異なるため、採用するモデルで必要な組み合わせを確認する。

`execution`を指定する場合は正の整数の`maxSteps`も必須にする。
adapterで検証し、`stopWhen: isStepCount(maxSteps)`へ変換する。
上限はLLMの生成ステップ数であり、Toolの実行回数や利用料金の上限ではない。

## 構造化出力

呼び出し側がZodスキーマを渡し、戻り値の型をスキーマから推論する。
完成結果は`{ output, usage, finishReason }`に揃え、`output`はテキストなら`string`、構造化出力ならスキーマの出力型とする。

```ts
const result = await deps.llm.generateObject({
  modelId: input.modelId,
  messages: [
    {
      role: "system",
      content: instructions,
      cacheAfter: { ttl: "5m" },
    },
    { role: "user", content: input.document },
  ],
  schema: extractionSchema,
  abortSignal,
});
```

adapterでは、共通条件を変換したうえで以下のAPIを使う。

```ts
import { generateText, Output } from "ai";

const result = await generateText({
  ...options,
  output: Output.object({ schema }),
});

return {
  output: result.output,
  usage: result.usage,
  finishReason: result.finishReason,
};
```

`options`はモデル・メッセージ・Tool・中断条件などをSDKの引数に変換したもの。
JSON Schemaに表現できるスキーマを基本とし、Zodの任意の変換処理までモデル側の制約になるとは考えない。
構造化出力の検証失敗を空オブジェクトや成功値へ変換しない。

## Prompt Cache

`cacheAfter`は、そのメッセージまでの共通の先頭部分をキャッシュ境界にする指定。
adapterでSDKのメッセージへ変換する。

```ts
const toModelMessage = ({ cacheAfter, ...message }: LlmMessage): ModelMessage => {
  if (!cacheAfter) return message;

  return {
    ...message,
    providerOptions: {
      ...message.providerOptions,
      bedrock: {
        ...message.providerOptions?.bedrock,
        cachePoint: { type: "default", ttl: cacheAfter.ttl },
      },
    },
  };
};
```

固定の指示や参照資料を先に置き、その後に毎回変わる入力を置く。
キャッシュは回答を保存する機能ではなく、共通のプロンプトの計算を再利用する機能。
独自の`cacheKey`は設けない。

最低トークン数・境界数・TTLの対応はモデルによって異なる。
短いプロンプトでは指定してもキャッシュが成立しないことがあり、ヒットも保証されない。
adapterはproviderの警告を捨てず、未対応の指定を検出できるようにする。

## 使用量

完成結果の`usage`はAI SDKの`LanguageModelUsage`を使う。

| フィールド | 意味 |
| --- | --- |
| `inputTokens` | キャッシュ分を含む入力トークン合計 |
| `inputTokenDetails.noCacheTokens` | キャッシュ利用・書き込みを除いた入力 |
| `inputTokenDetails.cacheReadTokens` | キャッシュから読み取った入力 |
| `inputTokenDetails.cacheWriteTokens` | キャッシュへ書き込んだ入力 |
| `outputTokens` | 出力トークン合計 |
| `outputTokenDetails.reasoningTokens` | 出力のうち推論に使われたトークン |
| `totalTokens` | 入力・出力の合計 |

AI SDKのBedrock providerは入力合計を正規化している。`inputTokens`へキャッシュ分を再度足さない。
取得できなかった値は`undefined`として扱い、0に置き換えない。
AI SDK 7の`result.usage`は全ステップの合計なので、Toolのループでもこれを返す。非推奨の`totalUsage`は使わない。

## ストリーミング

途中のイベントと完成結果を分けて返す。

```ts
export type GenerationStream<Chunk, Result> = {
  stream: AsyncIterable<Chunk>;
  result: Promise<Result>;
};
```

テキストではSDKの`result.stream`からテキスト差分・Tool呼び出し・Tool結果を扱う。
構造化出力では`partialOutputStream`の途中データを`DeepPartial<T>`相当として扱い、完成した`T`と区別する。
Toolの進捗も必要なら、部分出力とToolイベントを識別できるイベント型で返す。

最終的な検証済み出力・使用量・終了理由は`result`から取得する。
ストリーム内のエラーも失敗として扱い、正常終了へ読み替えない。
呼び出し側はストリームと完成結果の両方の失敗を処理し、画面離脱やリクエスト中断は`abortSignal`で伝播する。
イベントの消費と完成結果の待機は並行させ、未消費のストリームを放置しない。

HTTPレスポンスやNext.jsへの変換は入口の責務とし、portから`Response`を返さない。

## Toolの実行

Toolはusecase側で`tool({ inputSchema, execute })`を使って定義し、`execution.tools`へ渡す。
`execute`にはその操作で必要な依存・実行者の情報をクロージャーで渡す。
モデルが生成した引数から認可の範囲を決めず、通常の処理と同じ認可を行う。

adapterでは`generateText`・`streamText`にToolと停止条件を渡してループを実行する。
単純なループのためだけに別のAgent用portは増やさない。
構造化出力と組み合わせる場合は、Tool実行後に最終出力を生成するステップも必要になる。

`maxSteps`への到達は業務処理の成功を意味しない。終了理由・完成出力を確認する。
タイムアウト・中断をTool側の外部呼び出しにも伝播し、副作用を持つToolは再実行時の扱いを決める。

## 参考

- [AI SDK：Bedrock provider](https://ai-sdk.dev/providers/ai-sdk-providers/amazon-bedrock)
- [AI SDK：構造化出力](https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data)
- [AI SDK：Tool利用](https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling)
- [AI SDK：7系への移行](https://ai-sdk.dev/docs/migration-guides/migration-guide-7-0)
- [AWS：Node.jsの認証チェーン](https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/setting-credentials-node.html)
- [AWS：Prompt caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)
