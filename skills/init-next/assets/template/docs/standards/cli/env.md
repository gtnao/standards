# CLIの環境変数の読み込み

[環境変数の共通方針](../base/env.md)に従い、ローカルでは`.env`を使う。
Node.js 24の標準機能で読み込み、Zodで値を検証・変換する。

`package.json`の実行コマンドは次のようにする。

```json
{
  "scripts": {
    "dev": "tsx --env-file-if-exists=.env src/index.ts",
    "start": "node --enable-source-maps dist/index.js"
  }
}
```

開発・ビルド・本番実行の構成は[tsconfigの初期設定](tsconfig.md#開発型チェックビルドの使い分け)を参照。

通常のNode.jsは、`.env`を置いただけでは自動で読み込まない。
tsxもNode.jsのCLIオプションを受け付けるため、開発用コマンドで読み込みを指定する。dotenvなどの追加パッケージは不要。

`--env-file-if-exists`は、ファイルがない場合も実行を続ける。
必要なのは設定値であり、`.env`ファイル自体ではないため、この指定を選ぶ。環境変数を直接渡していれば、ファイルなしでも動かせる。
必須値の不足はアプリ側の検証で検出する。

既に実行環境にある値と`.env`の値が重複した場合は、実行環境側が優先される。
`--env-file=.env`を使うと、ファイルが存在しない時点でエラーになる。

## 参考

- [Node.js：環境変数と.env](https://nodejs.org/docs/latest-v24.x/api/environment_variables.html)
- [Node.js：--env-file](https://nodejs.org/docs/latest-v24.x/api/cli.html#--env-filefile)
- [tsx：Node.jsのCLIオプション](https://tsx.is/node-enhancement)
- [Zod：スキーマ・型変換・既定値](https://zod.dev/api)
