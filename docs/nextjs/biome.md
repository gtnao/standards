# Next.jsのBiome設定

[create-next-app](create-next-app.md)が生成する設定を土台に、[Biomeの共通方針](../base/biome.md)を反映する。

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.14/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "files": {
    "ignoreUnknown": true
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  },
  "linter": {
    "enabled": true,
    "rules": {
      "preset": "recommended"
    },
    "domains": {
      "next": "recommended",
      "react": "recommended"
    }
  },
  "assist": {
    "actions": {
      "source": {
        "organizeImports": "on"
      }
    }
  }
}
```

2026年10月1日時点で、[公開から7日間待つ方針](../base/pnpm-workspace.md#minimumreleaseage)を満たす`2.5.14`を使った例。
導入時には採用版を確認し、`@biomejs/biome`本体と`$schema`を揃える。

## 生成設定からの変更

| 項目 | 変更・理由 |
| --- | --- |
| `$schema` | 採用するBiome本体のバージョンに合わせる |
| `linter.rules.recommended` | 非推奨の`recommended: true`を、後継の`preset: "recommended"`に置き換える |
| `files.includes` | 削除し、生成物の除外を`.gitignore`に集約する |

生成される`.gitignore`には`node_modules/`・`.next/`・`build/`などの除外がある。
`dist/`など別の出力先を追加したら、そちらに追記する。

## 維持する設定と理由

| 項目 | 意味・理由 |
| --- | --- |
| `vcs` | Git連携を有効にし、`.gitignore`の除外を反映する |
| `files.ignoreUnknown` | Biomeが扱えないファイルに対する診断を抑える。既定値は`false` |
| `formatter` | Formatを有効にし、スペース2文字で整形する |
| `linter.enabled`・`rules.preset` | Lintを有効にし、Biomeの推奨ルールを採用する |
| `linter.domains` | Next.js・React向けの推奨ルールを採用する |
| `organizeImports` | import整理を有効にする |

既定値と同じかどうかだけで省略を決めず、採用する方針として明示する価値があるかで判断する。
生成済みのLint・Format・import整理の有効化やインデント幅は、その方針を示しているため残す。

`domains`は、フレームワークに適したルールをまとめて有効にする設定。
Hooksの呼び出し位置・依存配列や、Next.jsでの`<img>`使用などを検査する。
依存パッケージによる自動有効化もあるが、ここでは採用方針を明示する。
`recommended`は推奨ルールの指定であり、その分野の全ルールを有効にするものではない。

## テストコードのimport制限

[Baseのimport制限](../base/testing.md#本番コードからテストへのimportを制限する)を、冒頭の設定へ`overrides`として追加する。
本番コードからテスト用コードへの参照を防ぎ、テストファイル・ヘルパーからの参照は許可する。

## 実行コマンド

[Next.jsのpackage.json設定](package-json.md#scripts)に従い、次のscriptsを使う。

```json
{
  "scripts": {
    "lint": "biome check --error-on-warnings .",
    "lint:fix": "biome check --write --error-on-warnings ."
  }
}
```

`check`でLint・Format・import整理をまとめて確認し、警告も失敗扱いにする。
`--write`では整形と安全な自動修正を適用する。型チェックは`typecheck`で別途行う。

## 参考

- [create-next-app：Biomeの生成設定](https://github.com/vercel/next.js/blob/v16.3.8/packages/create-next-app/templates/app-empty/ts/biome.json)
- [Biome：設定リファレンス](https://biomejs.dev/reference/configuration/)
- [Biome：Next.js・ReactなどのDomains](https://biomejs.dev/linter/domains/)
- [Biome：import整理](https://biomejs.dev/assist/actions/organize-imports/javascript/)
- [npm：Biomeのバージョンと公開日時](https://registry.npmjs.org/@biomejs/biome)
