# aquaの初期設定

aquaで開発・インフラ運用に使うCLIのバージョンをプロジェクトごとに管理する。
Node.js・pnpm・npmパッケージは、引き続き[package.json](package-json.md)とpnpmで管理する。

ルートに`aqua.yaml`を置く。

```yaml
registries:
  - type: standard
    ref: v4.562.0 # renovate: depName=aquaproj/aqua-registry
```

`ref`は2026年9月22日時点の設定例。導入・更新時に採用する版を確認する。

aqua本体の導入は[公式の導入手順](https://aquaproj.github.io/docs/install/)を参照。

## 設定の意味

| 項目 | 意味・理由 |
| --- | --- |
| `type: standard` | CLIの取得方法を定義した公式レジストリを使う |
| `ref` | CLIの取得方法を定義するレジストリの版。CLI本体の版とは別に固定する。コメントはRenovate向けの更新情報 |

## ツールの追加・実行

```sh
# 例：ツールと版をaqua.yamlに追記する
aqua generate -i suzuki-shunsuke/pinact@v5.0.0

# インストールする
aqua install
```

`generate -i`で`packages`にツールと版を追記し、`install`で導入する。
更新時は`packages`のバージョンを変更して再度`install`する。

実行は`aqua exec -- コマンド 引数`に統一する。プロジェクト内で実行すると、`aqua.yaml`に指定した版が使われる。

[pnpmの待機期間](pnpm-workspace.md#minimumreleaseage)はaquaには適用されないため、CLIやレジストリの公開日も別途確認する。

## ツールの利用例：pinact

GitHub Actionsの`uses:`をコミットSHAに固定するツール。タグの付け替えで実行内容が変わることを防ぐ。

```sh
# 記述したタグをSHAに変換し、バージョンをコメントに残す
aqua exec -- pinact run --min-age 7

# 新しい版へ更新してSHA固定する
aqua exec -- pinact run --update --min-age 7
```

ワークフローの作成・更新時にローカルで実行する。`--update`はメジャー更新も含み得るため、差分を確認する。
`--min-age 7`は、[pnpmと同じ7日間の待機期間](pnpm-workspace.md#minimumreleaseage)を設ける場合の指定例。
GitHub Releaseがある場合は公開日時、タグだけの場合はコミット日時が判定基準になる。

## ツールの利用例：Lefthook

Gitのコミット前にチェックを実行するツール。言語に依存しないCLIとしてaquaで管理する。

```sh
aqua generate -i evilmartians/lefthook@v2.1.14
aqua install
```

`v2.1.14`は2026年9月22日時点で公開から7日以上経過した版の例。
ルートに`lefthook.yml`を置く。

```yaml
lefthook: aqua exec -- lefthook

pre-commit:
  parallel: true
  jobs:
    - name: lint
      run: pnpm run lint
    - name: typecheck
      run: pnpm run typecheck
```

[Biomeの`lint`](biome.md#実行コマンド)と[TypeScriptの`typecheck`](tsconfig.md)を並行実行する。
先頭の`lefthook`で、Gitフックからの呼び出しもaqua経由に揃える。
自動修正はせず、失敗したら修正・ステージしてから再度コミットする。
検査対象は作業ツリーなので、部分ステージしたコミットの内容だけを検査するものではない。

設定後、Gitフックを登録する。

```sh
aqua exec -- lefthook install
```

これで`git commit`時にチェックが走り、失敗するとコミットが止まる。
フック本体はGitで共有されないため、各開発者もclone後に`aqua install`とこの登録を行う。
手動で確認する場合は`aqua exec -- lefthook run pre-commit`を使う。

テスト・ビルドはまず[CI](github-actions.md)で実行する。
フックは`--no-verify`などで回避できるため、マージ条件としての強制はCIとRulesetsで行う。

## 参考

- [aqua：設定と基本操作](https://aquaproj.github.io/docs/tutorial/)
- [aqua：exec](https://aquaproj.github.io/docs/reference/usage/#aqua-exec)
- [pinact：使い方](https://github.com/suzuki-shunsuke/pinact/blob/v5.0.0/docs/usage.md)
- [pinact：更新と待機期間](https://github.com/suzuki-shunsuke/pinact/blob/v5.0.0/docs/update.md)
- [Lefthook：フックの登録](https://lefthook.dev/usage/commands/install/)
- [Lefthook：実行コマンドの指定](https://lefthook.dev/configuration/lefthook/)
- [Lefthook：並行実行](https://lefthook.dev/configuration/parallel/)
