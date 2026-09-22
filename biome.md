# Biomeの初期設定

TypeScriptのLint・Format・import整理をBiomeにまとめる。型チェックはtscが担当する。
Gitを使い、生成物などの除外は`.gitignore`に集約する。

`biome.json`をプロジェクトのルートに置く。

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.13/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "formatter": {
    "indentStyle": "space"
  },
  "linter": {
    "rules": {
      "preset": "recommended"
    }
  }
}
```

## 導入

```sh
pnpm add -D -E @biomejs/biome@2.5.13
```

2026年9月22日の確認時点では最新版は2.5.14だが、公開から7日未満のため、[待機期間の方針](pnpm-workspace.md)に合わせて2.5.13を採用した例。
導入時には、その時点で条件を満たす版を選ぶ。

`-E`でバージョンを完全固定し、更新による整形結果や検査の変化を管理する。更新時は`$schema`のバージョンも合わせる。

## 設定の意味と採用理由

| 項目 | 意味・理由 |
| --- | --- |
| `$schema` | エディターでの設定の補完・検証に使う |
| `vcs.enabled`・`clientKind` | Git連携を有効にする |
| `vcs.useIgnoreFile` | `.gitignore`の除外を反映し、生成物などの除外設定を二重管理しない |
| `formatter.indentStyle` | スペースを採用する。既定の幅と合わせて2文字になる。ここは好みの選択 |
| `linter.rules.preset` | 推奨ルールを使う方針を明示する。既定値と同じ |

`rules.recommended: true`は非推奨になっているため、後継の`preset: "recommended"`を使う。

`.gitignore`には、少なくとも次を入れる。

```gitignore
node_modules/
dist/
```

## 実行コマンド

`package.json`に次のscriptsを追加する。

```json
{
  "scripts": {
    "lint": "biome check --error-on-warnings .",
    "lint:fix": "biome check --write --error-on-warnings ."
  }
}
```

- `check`：Lint・Format・import整理をまとめて確認する。
- `--write`：整形と、Biomeが安全と分類した自動修正を適用する。
- `--error-on-warnings`：警告も失敗扱いにする方針。修正できない指摘が残れば失敗する。

`lint`という名前だが、整形の確認も含む。型チェックは[tsconfigの設定例](tsconfig.md)の`typecheck`で別途行う。

## 初期設定で入れないもの

| 項目 | 省略する理由 |
| --- | --- |
| `formatter.enabled`・`linter.enabled` | 既定で有効 |
| `assist.actions.source.organizeImports` | import整理は既定で有効。採用方針として明示してもよい |
| `files.includes` | まず全体を対象とし、生成物などの除外は`.gitignore`に集約する |
| 引用符・セミコロン・行幅など | まずBiomeの既定値を採用する |
| 個別ルール・`all`・nursery | 推奨ルールで始め、必要性を確認してから追加する |

## 参考

- [Biome：導入とバージョン固定](https://biomejs.dev/guides/getting-started/)
- [Biome：設定リファレンス](https://biomejs.dev/reference/configuration/)
- [Biome：Gitとの連携](https://biomejs.dev/guides/integrate-in-vcs/)
- [Biome：import整理](https://biomejs.dev/assist/actions/organize-imports/javascript/)
