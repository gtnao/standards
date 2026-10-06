# ディレクトリ設計の共通方針

実行の入口・処理の手順・外部機能との接続を分ける。
具体的な配置は実行環境に合わせ、以下の責務と依存関係を保つ。

| 役割 | 責務 |
| --- | --- |
| 実行の入口 | 入力と設定を受け取り、依存を組み立て、処理を呼び出して結果を返す |
| `usecases` | 一つの目的を達成するための処理手順を組み立てる |
| `domain` | アプリが扱う概念と、それに関する型・ルール・処理を置く |
| `ports` | usecaseが利用する外部機能のインターフェースを定義する |
| `adapters` | portを満たす具体的な実装を置く |
| `lib` | アプリ固有の意味を持たない汎用処理を置く |

各層の中は、規模や処理のまとまりに応じて分割する。粒度は実装時に判断し、依存ルールを維持する。
Node.jsで直接実行する場合は[CLIの配置](../cli/directory-structure.md)に従う。
Next.jsのapp・UIの配置は[Next.jsのディレクトリ設計](../nextjs/directory-structure.md)に従う。

## 依存関係

| 参照する側 | 参照できる層 |
| --- | --- |
| 実行の入口 | usecases・adapters・ports・domain・lib |
| `usecases` | ports・domain・lib |
| `adapters` | ports・domain・lib |
| `ports` | domain・lib |
| `domain` | lib |
| `lib` | 他の層には依存しない |

[Prisma](../nextjs/prisma.md#依存関係の例外)はadapters配置の例外とする。usecasesからAPI・生成型、domainから生成型への依存を許可する。
Next.jsで表示用データを取得する層は[queriesの方針](../nextjs/queries.md)に従う。

同じ層のモジュール同士は必要に応じて参照できる。循環依存は作らない。
標準機能や外部ライブラリの利用は、各層の責務に合わせて判断する。

型も責務に合う場所に置く。例えば、外部機能の契約はports、adapterの生成設定はadaptersに定義する。
実行の入口は両方を利用できるが、usecaseがadapterの設定型を参照する形にはしない。
テストでは、検証対象やテストに必要な型・実装を参照する。

## usecases

処理を表す動詞で命名し、主となる関数単位でファイルを分ける。
処理単位の関数にし、必要な依存を`deps`、今回の処理に渡す値を`input`として受け取る。
ファイル内に`Args`を定義し、`deps`と`input`が一目で分かる形にする。外部から直接参照する必要がなければexportしない。

`input`はユースケース全体の入力として、そのユースケース内で形を定義する。
対象のデータは`input.item`など意味のある名前でまとめ、操作に必要な識別子・実行者などの文脈と区別する。
ユースケースが受け取る入力型・検証スキーマは、そのusecase側に置く。domainには操作に依存しない概念・型・制約を置き、usecaseの入力定義から利用する。

```ts
type Args = {
  input: {
    item: {
      name: string;
      status: ItemStatus;
    };
  };
};
```

`ItemStatus`はdomainの型。この操作に必要な項目の組み合わせは、usecaseの`Args`で定義する。

domainの処理と外部機能の呼び出しを組み合わせ、順序・分岐・並行実行を決める。他のusecaseを呼んで組み立ててもよい。

`usecases/summarize.ts`の例：

```ts
import { summarizeText } from "../domain/summary.js";
import type { FileReader } from "../ports/file-reader.js";

type Args = {
  deps: { fileReader: FileReader };
  input: { path: string };
};

export const summarize = async ({ deps, input }: Args) => {
  const text = await deps.fileReader.read(input.path);
  return summarizeText(text);
};
```

結果は値として返し、CLIの表示などは入口に任せる。
その処理に閉じた加工や補助関数は同じファイルに置ける。

## portsとadapters

主な目的は、usecaseのテストで外部依存を制御できるようにすること。
通常はadapterを渡し、テストでは同じportを満たす実装で返す値やエラーを制御する。

`ports/file-reader.ts`：

```ts
export interface FileReader {
  read(path: string): Promise<string>;
}
```

adapterは`createXxx`関数で設定を受け取り、返り値にportの型を明示する。
`adapters/file-reader.ts`の例：

```ts
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { FileReader } from "../ports/file-reader.js";

export const createFileReader = (
  config: { root: string },
): FileReader => ({
  read: (path) => readFile(resolve(config.root, path), "utf8"),
});
```

usecaseのテストでは、実際のファイルを用意せずに入力を渡せる。

```ts
const fileReader: FileReader = {
  read: async () => "テスト用の入力",
};

const result = await summarize({
  deps: { fileReader },
  input: { path: "example.txt" },
});
```

この結果や、必要に応じて依存への呼び出しを検証する。テストの配置は[テストの共通方針](testing.md)に従う。

portは利用側に必要な操作として定義する。複数のusecaseで共有する場合も、`ports/`にまとめてよい。
抽象度は、何を切り離したいかで決める。

- SDKや通信を切り離してテストしたいなら、製品固有の操作を残してもよい。
- 保存先などの詳細をusecaseから隠したいなら、用途に沿った操作を定義する。

名前は実際に抽象化している範囲に合わせる。製品固有の契約なら製品名を使い、名前だけを汎用化しない。
実装を差し替える余地は残すが、ローカルと本番で接続先などの設定が異なるだけなら、同じadapterを使う。

## domainとlib

`domain`には、アプリが扱う概念と、それに関する型・ルール・処理を置く。
具体的な内容はプロジェクトに合わせる。実行の入口・usecases・ports・adaptersには依存せず、他の層から利用される。

`lib`には、アプリ固有の意味を持たない汎用処理を置く。
まずは使う場所の近くに置き、実際に共有が必要になったときに切り出しを検討する。
共有できることや、ライブラリへの依存がないことだけを理由に`lib`へ置かない。使う層と責務が明確なら、その層の中で共有する。`lib`への切り出しは、特定の層に属さない処理を実際に複数の層で使う場合に検討する。
標準機能や導入済みライブラリで十分なら、自作しない。

共通で使う処理でも、業務上の意味を持つものはdomainなど、その責務に合う場所へ置く。
命名・export・ファイル内の配置は[コーディング方針](coding-guidelines.md)を参照。
