# CLIのディレクトリ設計

Node.jsプログラムでは、実行の入口・処理の手順・外部機能との接続を分ける。

```text
src/
├── entrypoints/
├── usecases/
├── domain/
├── ports/
├── adapters/
└── lib/
```

層の責務・依存関係・usecaseとadapterの書き方は[共通方針](../base/directory-structure.md)に従う。

## entrypoints

実行方法に応じた入力の解析・検証、[Zodによる環境変数の検証](../base/env.md#zodによる検証変換)、adapterの生成を行い、usecaseへ`deps`と`input`を渡す。
結果は標準出力など、その入口に合う形で返す。実行形態に固有の制御もここで扱う。

`entrypoints/summarize.ts`の例：

```ts
import { z } from "zod";
import { createFileReader } from "../adapters/file-reader.js";
import { summarize } from "../usecases/summarize.js";

const env = z.object({
  INPUT_ROOT: z.string().min(1),
}).parse(process.env);

const deps = {
  fileReader: createFileReader({ root: env.INPUT_ROOT }),
};

const result = await summarize({
  deps,
  input: { path: "input.txt" },
});

console.log(result);
```

### CLI

CLIにはcittyを使い、コマンドの構造に合わせてファイルを分ける。

```text
entrypoints/cli/
├── index.ts
└── summarize.ts
```

`index.ts`でサブコマンドを登録し、選ばれたコマンドを動的importで読み込む。

```ts
import { defineCommand, runMain } from "citty";

runMain(defineCommand({
  subCommands: {
    summarize: () => import("./summarize.js").then((m) => m.default),
  },
}));
```

各コマンドは引数定義と実行処理を持つ。`summarize.ts`の例：

```ts
import { defineCommand } from "citty";
import { z } from "zod";
import { createFileReader } from "../../adapters/file-reader.js";
import { summarize } from "../../usecases/summarize.js";

export default defineCommand({
  args: {
    path: { type: "string", required: true },
  },
  run: async ({ args }) => {
    const env = z.object({
      INPUT_ROOT: z.string().min(1),
    }).parse(process.env);
    const deps = {
      fileReader: createFileReader({ root: env.INPUT_ROOT }),
    };
    const result = await summarize({ deps, input: { path: args.path } });
    console.log(result);
  },
});
```

引数の定義・解析はcittyに任せる。コマンドをグループ化する場合は、サブディレクトリの`index.ts`で同じ構造を繰り返す。
`runMain`はCLIの最上位で呼び、サブコマンドは`defineCommand`の結果をexportする。

