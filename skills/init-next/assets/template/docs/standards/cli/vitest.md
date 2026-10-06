# Vitestの初期設定

[テストの共通方針](../base/testing.md)を、Node.jsで動くTypeScriptのユニットテストに適用する。
本番のビルドは引き続きtscを使う。Vitestは内部でViteを使うが、アプリのビルド方式を変更する必要はない。

Vitestの設定・導入・`test`と`test:watch`は[Base](../base/testing.md)をそのまま使う。
CLIでは、次のscriptsとビルド対象の分離を追加する。

## 導入・実行

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit",
    "build": "tsc -p tsconfig.build.json"
  }
}
```

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

## 型チェックとビルドを分ける

| 設定 | 対象・用途 |
| --- | --- |
| `tsconfig.json` | 本番コード・テスト・設定ファイル・開発用スクリプトを型チェックする |
| `tsconfig.build.json` | 本番コードをビルドする |

[TypeScriptの初期設定](tsconfig.md)から、次のように変更する。

1. `tsconfig.json`の`compilerOptions`から`rootDir`・`outDir`をビルド側へ移す。他のオプションは維持する。
2. `tsconfig.json`の`include`を置き換え、`exclude`を追加する。以下はルートの項目の抜粋。

```json
"include": ["**/*"],
"exclude": ["node_modules", "dist"]
```

型チェックはプロジェクト全体を対象にし、依存パッケージと生成物を探索から除外する。
`**/*`でも、対象になるのはTypeScriptが扱う拡張子のファイル。`allowJs`を有効にしていないため、JavaScriptは対象にしない。
`vitest.config.ts`を個別に列挙せず、今後追加する設定ファイルや`scripts/`内のTypeScriptも拾い、設定の更新忘れによる取りこぼしを防ぐ。
生成先が増えたら`exclude`に追加する。別の実行環境・コンパイラー設定が必要なコードは、専用のtsconfigに分ける。
`rootDir: "src"`を共通側に残すと、ルート直下の設定ファイルが範囲外になる。
`noEmit`は引き続きscripts側で指定する。

ルートに`tsconfig.build.json`を追加する。

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src/**/*.ts"],
  "exclude": ["src/**/*.test.ts", "src/**/__tests__/**"]
}
```

これにより、通常は本番コードだけが`dist`に出力され、`src/index.ts`は従来どおり`dist/index.js`になる。
ビルド側の`include`・`exclude`は共通側の配列を置き換える。型チェックは広く、ビルドは`src`内の本番コードに絞る構成とする。
ビルド用tsconfigを分けてテストを除外する構成は、Nest公式スターターでも採用されている。

ただし、`exclude`は対象の探索から外す設定であり、importを禁止しない。
本番コードからテストをimportすると、そのテストもビルド対象に入り得るため、次のLintで制限する。
また、tscは過去の生成物を削除しない。配置変更などで古いテストの出力が残っている場合は、`dist`を削除してビルドし直す。

## 本番コードからテストへのimportを制限する

[Baseのimport制限](../base/testing.md#本番コードからテストへのimportを制限する)をBiomeへ追加する。
ビルド除外と併用し、本番コードからテストやヘルパーを参照しないようにする。

## 参考

- [Vitest：導入・テストの配置例・実行](https://vitest.dev/guide/)
- [Vitest：設定ファイル](https://vitest.dev/config/)
- [Vitest：globals](https://vitest.dev/config/globals)
- [Vitest：include](https://vitest.dev/config/include)
- [Vitest：passWithNoTests](https://vitest.dev/config/passwithnotests)
- [Vitest：型テストと通常のテスト実行](https://vitest.dev/guide/testing-types)
- [TypeScript：TSConfigリファレンス](https://www.typescriptlang.org/tsconfig/)
- [Nest公式スターター：ビルド用tsconfig](https://github.com/nestjs/typescript-starter/blob/master/tsconfig.build.json)
- [Biome：noRestrictedImports](https://biomejs.dev/linter/rules/no-restricted-imports/javascript/)
- [Biome：overrides](https://biomejs.dev/reference/configuration/#overrides)
