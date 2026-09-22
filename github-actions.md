# GitHub ActionsのCI初期設定

pnpm 12で依存をインストールし、Biome・TypeScript・Vitestによるチェックとビルドを実行する。
[package.json](package-json.md)でランタイムを管理し、[Biome](biome.md#実行コマンド)と[Vitest](vitest.md#導入実行)のscriptsを設定しておく。

`.github/workflows/ci.yml`を作成する。

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  check:
    runs-on: ubuntu-24.04
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false

      - uses: pnpm/action-setup@ea17c68df8912ef543352723c149a84f56e3d413 # v6.1.0
        with:
          cache: true

      - run: pnpm install --frozen-lockfile
      - run: pnpm run lint
      - run: pnpm run typecheck
      - run: pnpm run test
      - run: pnpm run build
```

Actionのバージョンは設定例。導入・更新時には内容と公開日を確認し、[aquaで導入したpinact](aqua.md#ツールの利用例pinact)でSHA固定・更新する。

## 設定の意味と採用理由

| 項目 | 意味・理由 |
| --- | --- |
| `pull_request` | PRの変更をマージ前にチェックする |
| mainへの`push` | mainに反映された状態もチェックする |
| `permissions.contents: read` | リポジトリを読み取る権限だけを与える。他の権限は付与しない |
| `persist-credentials: false` | checkout後のGit操作に不要な認証情報を保持しない |
| Actionの完全なSHA | タグの付け替えによる実行内容の変更を防ぐ |
| `ubuntu-24.04` | OSの版を固定し、`latest`の移行で別のUbuntuへ切り替わることを避ける |
| `timeout-minutes: 10` | 異常な長時間実行を止める。10分は初期値としての選択で、所要時間に応じて変更する |
| `cache: true` | pnpmストアを再利用し、依存の取得時間を短縮する |
| `--frozen-lockfile` | コミット済みのlockfileでインストールし、不在や不整合をエラーにする |

`concurrency`は、同じワークフロー・同じPRまたはブランチの実行をまとめる。
追加コミットで新しいCIが起動したら古い実行をキャンセルする。別のPRのCIは並行して動く。

`ubuntu-24.04`でも、GitHub側のイメージ更新によりプリインストール済みツールなどは変わる。
固定できるのはOSの版であり、仮想マシンの内容全体ではない。

## pnpm・Node.jsのバージョン

pnpmは`pnpm/action-setup`が`packageManager`から取得するため、YAMLで重複指定しない。
pnpm 12は単体で動く実行ファイルであり、アプリ用のNode.jsは`pnpm install`が`devEngines.runtime`とlockfileに従って用意する。
後続は`pnpm run`を使い、そのランタイムで実行する。この構成では`actions/setup-node`を追加しない。

[pnpm-workspace.yaml](pnpm-workspace.md)の公開後の待機期間・信頼性検証・依存のビルド許可も、CIのインストールに適用される。
ただし、その設定がActionやpnpm自身の初期導入まで検証するわけではない。

## チェックの分担

| コマンド | 確認するもの |
| --- | --- |
| `lint` | BiomeのLint・整形・import整理 |
| `typecheck` | 本番コード・テスト・設定・開発用スクリプトの型 |
| `test` | Vitestによる動作テスト。watchせず終了する |
| `build` | 本番コードからJavaScriptを生成できること |

まず1ジョブにまとめ、セットアップやインストールの重複を避ける。
途中で失敗すると後続ステップは実行されない。

## 初期設定で入れないもの

| 項目 | 省略する理由 |
| --- | --- |
| ジョブ分割 | 実行時間や、失敗時に他の結果も確認する必要が出てから検討する |
| 複数OSやNode.js版のマトリクス | まず現在の実行環境1つで確認する |
| `workflow_dispatch` | コミットやPR更新なしで手動実行したい場合に追加する |
| `paths`による実行条件の制限 | 設定変更などをチェックから取りこぼさず、必須チェックが起動しない状況も避ける |
| カバレッジのアップロード・成果物の保存 | 計測や配布・調査で必要になってから追加する |

## CIの成功をマージ条件にする

CIを実行する設定と、その通過をマージ条件にする設定は別。Rulesetsでmainの更新に`check`を必須とする。
初回のCIで`check`ジョブが実行されることを確認してから、対象リポジトリのルートで次を実行する。
GitHub CLIで認証済みで、リポジトリのルールを管理する権限があることを前提にする。
非公開リポジトリでRulesetsを使うには、GitHub Pro・Team・Enterprise Cloudのいずれかが必要。

```sh
gh api --method POST 'repos/{owner}/{repo}/rulesets' --input - <<'JSON'
{
  "name": "require-ci",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "required_status_checks",
      "parameters": {
        "required_status_checks": [{ "context": "check" }],
        "strict_required_status_checks_policy": false
      }
    }
  ]
}
JSON
```

`{owner}`・`{repo}`はGitHub CLIが現在のリポジトリから補完する。

| 項目 | 意味 |
| --- | --- |
| `name` | ルールセットの管理用の名前 |
| `target: "branch"`・`enforcement: "active"` | ブランチに対するルールを有効にする |
| `conditions.ref_name` | mainを対象にし、除外対象は設けない |
| `type: "required_status_checks"` | `parameters`で指定したチェックの通過を必須にする |
| `context: "check"` | 必須にするジョブの名前。ジョブ名を変更したらここも合わせる |
| `strict_required_status_checks_policy: false` | CI通過後にmainが進んでも、それだけを理由にPRへmainの取り込み・再チェックを要求しない |

`strict_required_status_checks_policy`を`true`にすると、最新のmainを取り込んだ状態でのチェックが必要になる。

これは初回作成用のコマンド。同名のルールを増やさないよう、変更時は次でIDを確認し、上のリクエストを`PUT repos/{owner}/{repo}/rulesets/確認したID`へ送る。

```sh
gh api 'repos/{owner}/{repo}/rulesets' --jq '.[] | {id, name, enforcement}'
```

## 参考

- [GitHub：ワークフローの構文](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub：同時実行とキャンセル](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [GitHub：ActionのSHA固定・権限の制限](https://docs.github.com/en/actions/reference/security/secure-use)
- [actions/checkout](https://github.com/actions/checkout)
- [pnpm/action-setup](https://github.com/pnpm/action-setup)
- [pnpm：ランタイム管理](https://pnpm.io/package_json#devenginesruntime)
- [pnpm：install](https://pnpm.io/cli/install)
- [GitHub：ランナーのOSと更新方針](https://github.com/actions/runner-images)
- [GitHub：Rulesetsの作成・更新API](https://docs.github.com/en/rest/repos/rules)
- [GitHub：Rulesetsの利用条件](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [GitHub CLI：gh api](https://cli.github.com/manual/gh_api)
