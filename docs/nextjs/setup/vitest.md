# Next.jsのVitest設定

[テストの共通方針](../../base/testing.md)を使い、`@/`を`src/`として解決する設定を加える。
ルートの`vitest.config.ts`：

```ts
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: {
    environment: "node",
    globals: false,
    include: ["src/**/*.test.ts"],
    passWithNoTests: true,
  },
});
```

テストの配置・scripts・本番コードからのimport制限はBaseに従う。
型チェックには[Next.jsのtsconfig](typescript.md)を使い、CLI用のビルド設定は追加しない。

Next.jsのパスエイリアスはVitestへ自動では引き継がれないため、`resolve.alias`でも設定する。
`next/headers`などNext.jsの実行コンテキストが必要なコードは、依存を分けるかテストごとに扱いを決める。

## 参考

- [Vitest：alias](https://vitest.dev/config/alias)
- [Next.js：Vitest](https://nextjs.org/docs/app/guides/testing/vitest)
