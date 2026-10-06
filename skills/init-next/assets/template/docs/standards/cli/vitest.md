# Vitestの初期設定

[テストの共通方針](../base/testing.md)を、Node.jsで動くTypeScriptのユニットテストに適用する。
本番のビルドは引き続きtscを使う。Vitestは内部でViteを使うが、アプリのビルド方式を変更する必要はない。

Vitestの設定・導入・`test`と`test:watch`は[Base](../base/testing.md)をそのまま使う。
型チェック・ビルドのscriptsは[tsconfigの初期設定](tsconfig.md#開発型チェックビルドの使い分け)を使う。

## テストの配置

[テストの共通方針](../base/testing.md)に従い、対象コードの近くに`*.test.ts`、テスト専用ヘルパーを`__tests__/`へ置く。

```ts
// src/sum.test.ts
import { expect, test } from "vitest";
import { sum } from "./sum.js";

test("2つの数を足す", () => {
  expect(sum(1, 2)).toBe(3);
});
```

相対importは、本番コードと同じく出力後の`.js`で書く。

## 型チェックとビルド

[tsconfigの初期設定](tsconfig.md#型チェックとビルドを分ける)を使う。
型チェックはテスト・設定ファイルも対象にし、ビルドは本番コードに絞る。

## 本番コードからテストへのimportを制限する

[Baseのimport制限](../base/testing.md#本番コードからテストへのimportを制限する)をBiomeへ追加する。
ビルド除外と併用し、本番コードからテストやヘルパーを参照しないようにする。

## 参考

- [Vitest：導入・テストの配置例・実行](https://vitest.dev/guide/)
