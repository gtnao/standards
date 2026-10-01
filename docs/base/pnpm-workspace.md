# pnpm-workspace.yamlの初期設定

pnpm 12で、ルートに1つのパッケージを置く構成を扱う。
サプライチェーン攻撃への対策を優先し、依存の取得元・公開後の経過時間・公開方法・インストール時のスクリプトを制限する。

プロジェクトのルートに`pnpm-workspace.yaml`を置く。

```yaml
engineStrict: true

strictDepBuilds: true
blockExoticSubdeps: true

minimumReleaseAge: 10080
minimumReleaseAgeStrict: true
minimumReleaseAgeIgnoreMissingTime: false

trustPolicy: no-downgrade
trustLockfile: false
```

名前に`workspace`とあるが、単独プロジェクトでもpnpmの設定ファイルとして使う。
`packages`を省略すると、ルートのパッケージだけが対象になる。

## 各項目の意味と採用理由

### engineStrict

依存パッケージの`engines.node`と使用するNode.jsが合わなければ、インストールをエラーにする。
攻撃対策というより、対応外の依存を早期に検出するための設定。

自分のプロジェクトの`engines.node`との不一致は、この設定に関係なくエラーになる。
`true`にすることで、依存側の不一致も警告からエラーになる。
実際には動作しても、依存先の宣言が合わなければ止まる。依存パッケージ自身のバージョンを固定する設定ではない。
ただし、省略可能なoptional依存は、不適合でもインストール全体をエラーにせずスキップされる場合がある。

### strictDepBuilds

実行を許可するか判断していない依存のインストールスクリプトがあれば、実行を抑止してインストールをエラーにする。
pnpm 12では既定値も`true`だが、依存が自動でコードを実行することを許さない方針として明示する。

判断結果は`allowBuilds`に記載する。

| 値 | 挙動 |
| --- | --- |
| `true` | その依存のスクリプト実行を許可する |
| `false` | 実行しないと明示する。未判断ではなくなるが、その依存が正常動作するかは確認が必要 |
| 未指定 | 未判断として扱い、`strictDepBuilds: true`ならエラーにする |

例えばesbuildのスクリプトが必要と確認した場合に、次を追加する。

```yaml
allowBuilds:
  esbuild: true
```

名前だけの許可は更新後の版にも適用される。より厳密に管理するなら、`"esbuild@確認したバージョン": true`のように版を限定する。その分、更新時の再確認が必要になる。
`pnpm approve-builds`でも設定できる。

対象は依存側のインストールスクリプト。自分の`pnpm run build`などを承認制にする設定ではなく、通常のimportや実行時に依存コードが動くことまで防ぐものでもない。

### blockExoticSubdeps

間接依存が、任意のGitリポジトリやtarball URLなどから別の依存を取得することを制限する。
pnpm 12では既定値も`true`だが、取得元を制限する方針として明示する。

```text
自分のアプリ
└─ library-a（直接依存）
   └─ library-b（間接依存）
```

- 自分が`library-a`をGit URLで指定する：許可。
- `library-a`が`library-b`を通常のnpmレジストリから取得する：許可。
- `library-a`が`library-b`を任意のGit・tarball URLから取得する：原則拒否。

依存先を経由して想定外の配布元からコードが入る経路を制限する設定。直接指定したURLや、レジストリ上の悪意あるパッケージまで拒否するものではない。
ローカル参照など、許可される取得元には例外がある。

### minimumReleaseAge

公開から指定した分数が経過するまで、そのバージョンを採用しない。`10080`分は7日。
公開直後の攻撃や不具合が発覚するまで時間を置くため、1週間の待機を採用する。間接依存も対象になる。

緊急の脆弱性修正版も待機対象になるため、必要なら内容を確認して特定版だけ例外にする。
7日経過したこと自体が安全の証明になるわけではない。

### minimumReleaseAgeStrict

待機期間を満たす版が見つからなくても、新しい版に妥協せずエラーにする。
`minimumReleaseAge`を明示した場合は既に有効になるが、待機期間を必須条件とする方針を明示する。

### minimumReleaseAgeIgnoreMissingTime

`false`にすると、公開日時が取得できず待機期間を検証できない場合も拒否する。
「検証できない場合は通す」という抜け道を避けるため採用する。

公開日時を返さない社内レジストリやミラーでは、正常な依存でも止まることがある。

### trustPolicy

`no-downgrade`は、過去の公開版より公開元を裏付ける証拠が弱くなった版を拒否する。
比較はバージョン番号の大小ではなく公開日時に基づくため、別メジャーの公開版との比較で止まる場合もある。
例えば、以前は信頼されたCIから公開されていたのに、新しい版ではその証拠がなくなった場合など。

公開経路の不審な変化を検出するため採用する。ただし、コードの安全性を審査する機能ではなく、以前から証拠のないパッケージをすべて拒否する設定でもない。

正規の公開手順の変更や判定上の問題でも止まり得る。過去には[別メジャー間の公開方法の違い](https://github.com/pnpm/pnpm/issues/10202)や[staged publishingの誤検知](https://github.com/pnpm/pnpm/issues/11887)が報告されている。
これらがすべて現行版でも再現するという意味ではない。発生頻度は依存構成によるため、まず有効にし、エラー時に原因を確認する。

### trustLockfile

`false`は、lockfileに載っている依存も検証済みとはみなさず、待機期間や`trustPolicy`を再検証する指定。既定値も`false`だが、方針として明示する。

例えば、制限を無効にして追加された依存がlockfileに入っていても、他の開発者やCIがインストールする際に検出できる。
lockfileのバージョン固定を無視する設定ではなく、固定された版をインストールしてよいか確認する設定。

## 初期設定で入れない項目

| 項目 | 省略する理由 |
| --- | --- |
| `packages` | 単独プロジェクトなので、ルート以外のパッケージを列挙する必要がない |
| `allowBuilds` | 実際に導入する依存のスクリプトを確認してから追加する |
| `minimumReleaseAgeExclude` | 最初は待機期間の例外を設けない。空配列を書いてもよいが必須ではない |
| `trustPolicyExclude` | 最初は信頼性検証の例外を設けない |
| `trustPolicyIgnoreAfter` | 古い版を経過時間だけで検証対象外にしたくないため |
| `catalog`・`overrides` | 依存の一元管理や特定版への上書きが必要になってから追加する |

`trustPolicyIgnoreAfter: 129600`は、公開から90日を超えた版の信頼性検証を免除する設定。
運用負担を減らす妥協策ではあるが、90日経過しても安全とは限らないため、初期設定では採用しない。

## 例外の運用

エラーになったら、内容と必要性を確認し、必要な例外だけを追加する。
待機期間や信頼性検証の例外は、パッケージ名だけでなくバージョンまで限定する。

```yaml
# 書式例。実際に確認したパッケージとバージョンへ置き換える。
minimumReleaseAgeExclude:
  - "example-package@1.2.3"

trustPolicyExclude:
  - "another-package@4.5.6"
```

例外を設けた理由をコメントに残し、不要になったら削除する。
待機期間を免除しても、信頼性検証やスクリプトの許可まで免除されるわけではない。

## 参考

- [pnpm：設定とワークスペース](https://pnpm.io/settings)
- [pnpm：Node.jsの互換性検証（engineStrict）](https://pnpm.io/settings/cli#enginestrict)
- [pnpm：依存スクリプトの実行制御（strictDepBuilds・allowBuilds）](https://pnpm.io/settings/build)
- [pnpm：依存取得元・待機期間・信頼性検証と例外設定](https://pnpm.io/settings/dependency-resolution)
