# package.jsonの初期設定

新規の非公開プロジェクトで、pnpmとNode.jsを使う場合の推奨例。
バージョン番号は設定例であり、導入時に採用するバージョンへ置き換える。

```json
{
  "name": "my-app",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@12.0.0",
  "devEngines": {
    "runtime": {
      "name": "node",
      "version": "^24.4.0",
      "onFail": "download"
    }
  }
}
```

`scripts`・`dependencies`・`devDependencies`は、実際に使用するコマンドやパッケージに合わせて追加する。

## 各項目の意味と採用理由

### name

プロジェクトの名前。非公開なら必須ではないが、識別用に入れておく。
モノレポでは、`pnpm --filter 名前`での操作や内部パッケージの参照にも使う。

### private

`true`にすると、誤ってnpmへpublishするのを防げる。
「非公開」は、ここではレジストリへpublishしないという意味。Gitリポジトリの公開範囲を変える設定ではない。

### type

`"module"`は、このパッケージの`.js`ファイルをES Modules（ESM）として扱う指定。
新規プロジェクトでは、JavaScript標準の`import`・`export`を使う方針で採用する。Node.jsで直接実行でき、バンドラーは必須ではない。

| 方式 | 読み込み | 公開 |
| --- | --- | --- |
| ESM | `import { foo } from "./foo.js"` | `export const foo = ...` |
| CommonJS | `const foo = require("./foo.cjs")` | `module.exports = ...` |

`.mjs`は常にESM、`.cjs`は常にCommonJSになる。古いツールの設定だけCommonJSが必要なら、そのファイルを`.cjs`にできる。
依存パッケージはそれぞれの設定に従うため、自分の`type`で依存先の方式まで変わることはない。

Node.jsのESMでは、相対importに`./foo.js`のように拡張子を書く。ブラウザーと同様に明示されたパスで読み込むためで、CommonJSやバンドラーのような拡張子・`index.js`の補完は行わない。
`type`はコードを変換する設定ではなく、TypeScriptの変換設定とも別のもの。

### packageManager

使用するpnpmのバージョンを完全固定する。
通常の設定では、起動したpnpmと指定版が違えば、指定版を自動取得して実行する。グローバルに入っているpnpm自体を置き換えるわけではない。

pnpm 11以降では`devEngines.packageManager`でも指定できるが、完全固定ならトップレベルに1行で書けるため、こちらを採用する。両方を書く必要はない。

| 指定方法 | 特徴 |
| --- | --- |
| `packageManager: "pnpm@12.0.0"` | package.jsonで使用版を完全固定する |
| `devEngines.packageManager` | バージョン範囲も指定でき、確定版をlockfileに保存する |

### devEngines.runtime

開発で実際に使うNode.jsを指定し、pnpmに取得・管理させる。pnpm 10.14以降で対応している。

この例では、`pnpm install`時に指定範囲のNode.jsを解決・取得し、確定したバージョンとチェックサムを`pnpm-lock.yaml`に保存する。
`pnpm run`のスクリプトは、そのNode.jsを使う。lockfileをコミットして、開発者間やCIでも使用版を揃える。

| 項目 | 意味 |
| --- | --- |
| `name: "node"` | Node.jsを使う |
| `version: "^24.4.0"` | 24.4.0以上、25.0.0未満を許可する |
| `onFail: "download"` | 必要なランタイムを自動取得する |

`version`を`"24.4.0"`とすれば完全固定になる。`^`でも毎回最新版へ切り替わるわけではなく、通常はlockfileに記録した版を使う。
この例では、同じメジャー内の更新を許容しつつ、実際の使用版はlockfileで固定する方針を選んでいる。

直接実行する`node`への反映はpnpmのバージョンと導入方法による。pnpm 10・11では自動切り替えを前提にせず、pnpm 12ではpnpmのshimが有効ならプロジェクト内の直接実行にも反映される。

## 併せて設定するもの

依存パッケージ側の`engines.node`も検証するため、`pnpm-workspace.yaml`で`engineStrict: true`を指定する。自分の`engines`を省略していても有効。
詳しい挙動やその他の推奨設定は、[pnpm-workspace.yamlの初期設定](pnpm-workspace.md)を参照。

## 初期設定で入れない項目

| 項目 | 省略する理由 |
| --- | --- |
| `version` | publishせず、アプリのバージョン管理にも使わないなら不要 |
| `description` | READMEなどに説明があれば十分 |
| `engines` | この構成では`devEngines.runtime`で使用環境を揃える。別途対応範囲を宣言したい場合に追加する |
| `devEngines.packageManager` | トップレベルの`packageManager`でpnpmを固定するため |
| `workspaces` | pnpmでは`pnpm-workspace.yaml`の`packages`で定義するため |
| `main`・`exports`・`files` | 他のパッケージから読み込ませる入口や配布対象を、現時点では定義する必要がないため |

`engines.node`は「対応するNode.jsの条件」、`devEngines.runtime`は「実際に使うNode.js」の指定。
例えば、対応条件もNode 24系と明示したければ、`"engines": { "node": "24.x" }`を追加できる。

pnpmのインストール時には、自分のプロジェクトの`engines.node`との不一致はエラーになる。

## 参考

- [npm：package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/)
- [pnpm：package.jsonとdevEngines](https://pnpm.io/package_json)
- [pnpm：設定とワークスペース](https://pnpm.io/settings)
- [pnpm：engineStrictとpnpmの自動切り替え](https://pnpm.io/settings/cli)
- [Node.js：パッケージとモジュール形式](https://nodejs.org/api/packages.html)
- [Node.js：ESMの拡張子指定](https://nodejs.org/api/esm.html#mandatory-file-extensions)
