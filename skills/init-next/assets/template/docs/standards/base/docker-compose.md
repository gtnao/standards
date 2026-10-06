# Docker Composeで開発用PostgreSQLを起動する

アプリはローカルで実行し、PostgreSQLをComposeで用意する。
ルートに`compose.yaml`を置く。

```yaml
services:
  postgres:
    image: postgres:18.6-trixie@sha256:86c951e05bf56c93d95d397747fb8820ac76cc3bedb78f43abd83eedbe3666ae
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: local-password
      POSTGRES_DB: app
    ports:
      - "127.0.0.1:${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql
    shm_size: 128mb
    healthcheck:
      test:
        - CMD-SHELL
        - pg_isready -h 127.0.0.1 -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"
      interval: 10s
      timeout: 10s
      retries: 5
      start_period: 30s

volumes:
  postgres-data:
```

バージョン・digestは動作確認済みの例。導入先の本番環境に合わせてPostgreSQLのメジャーバージョンを選び、完全バージョンとdigestを固定する。
固定後も修正を取り込むために更新する。固定の考え方は[Dockerイメージの設定](docker.md#バージョンと依存の管理)を参照。

## 接続と起動

[環境変数の方針](env.md)に合わせ、`.env.example`に接続先の例を載せ、ローカルの`.env`へ反映する。

```dotenv
DATABASE_URL=postgresql://app:local-password@127.0.0.1:5432/app
```

ここで使うユーザー名・パスワードは、開発用DBだけに使う公開の仮の値。本番の認証情報を流用しない。
アプリはホストで動くため、接続先はサービス名の`postgres`ではなく`127.0.0.1`になる。

```sh
docker compose up --wait
pnpm dev
```

`--wait`はヘルスチェックの成功まで待ち、コンテナをバックグラウンドで起動する。
正常終了を確認してからアプリを実行する。アプリはComposeの管理外なので、`depends_on`では起動を待たせられない。

ポートが競合したら、`.env`に`POSTGRES_PORT=5433`などを追加し、`DATABASE_URL`のポートも合わせる。
Composeは`.env`を設定の変数展開に使うが、その全項目を自動でコンテナに渡すわけではない。

## 設定の意味と理由

| 項目 | 意味・理由 |
| --- | --- |
| `image` | PostgreSQL公式のDebian系イメージを使い、DB・OSの版と内容を固定する |
| `POSTGRES_USER`・`POSTGRES_PASSWORD` | 初期ユーザーとパスワード。ユーザーはスーパーユーザーとして作られる |
| `POSTGRES_DB` | 初期作成するDB名。ユーザー名と同じでも、用途を明示するため指定する |
| `127.0.0.1:…:5432` | ホストのループバックに公開する。ホスト側のポートは変更できる |
| 名前付きボリューム | コンテナを作り直してもデータを保持する。リポジトリ内のディレクトリを直接マウントせず、保存場所・所有権の管理をDockerに任せる |
| `shm_size: 128mb` | `/dev/shm`の上限をDockerの既定値64MiBから増やす。公式イメージのCompose例に合わせた初期値 |

PostgreSQLは並列クエリなどで動的共有メモリを使う。`shm_size`は必須ではないが、その不足による失敗を減らすため指定する。
128MBを起動時にすべて消費する指定ではなく、負荷によってはさらに増やす必要がある。

この構成はDBの起動を簡単にするため、初期ユーザーで接続する。
本番の権限制御やRLSを検証する場合は、マイグレーション用とアプリ実行用のロールを分け、アプリには必要な権限だけを与える。スーパーユーザーでの動作確認では代用できない。

## 起動確認

`pg_isready`で、PostgreSQLが接続を受け付ける状態か確認する。
`-h 127.0.0.1`でTCP接続にするのは、初期化中にUnixソケットだけで動く一時サーバーを、準備完了と判定しないため。
`$$`はComposeによる展開を避け、コンテナ内のシェルで環境変数を展開する指定。

時間設定はDocker公式のPostgreSQL用Compose例に合わせる。性能上の最適値ではなく、初期値として採用する。

| 項目 | 意味 |
| --- | --- |
| `interval: 10s` | 通常時のチェック間隔 |
| `timeout: 10s` | 1回のチェックの実行時間上限 |
| `retries: 5` | 連続して5回失敗すると異常と判定する |
| `start_period: 30s` | 起動直後の失敗をカウントしない猶予。途中でも成功すれば正常になる |

このチェックは認証情報やスキーマの正しさまでは保証しない。DBスキーマの準備は、アプリで採用するマイグレーションツールなどで別途行う。

## データの保持と初期化

```sh
# コンテナを削除する。DBデータは残る
docker compose down

# DBデータも削除する。初期化し直す場合だけ実行する
docker compose down --volumes
```

`POSTGRES_*`の設定は、データディレクトリが空のときの初期化に使われる。
既存データがある状態でYAMLを書き換えても、DB名・ユーザー・パスワードは変更されない。
`/docker-entrypoint-initdb.d`のスクリプトも初回だけ実行されるため、継続的なスキーマ変更の仕組みとしては使わない。

PostgreSQL 18以降の公式イメージでは、ボリュームを`/var/lib/postgresql`へ接続する。
17以前では通常`/var/lib/postgresql/data`を使うため、採用する版に合わせる。
メジャーバージョンを変更するときは、イメージの差し替えだけで既存データを引き継がず、データ移行か開発用DBの作り直しを行う。

## 初期設定に含めないもの

- `container_name`・明示的なネットワーク名：Composeがプロジェクトごとに管理する名前を使う。
- `restart: always`：開発者が必要なときに起動する用途なので、自動再起動を初期設定にはしない。
- `user`：公式イメージの初期化処理に任せる。DBプロセスは専用のOSユーザーで動く。

## 参考

- [PostgreSQL公式イメージ：環境変数・永続化・初期化](https://github.com/docker-library/docs/blob/master/postgres/README.md)
- [公式イメージの起動スクリプト](https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh)
- [Docker：PostgreSQLのヘルスチェック例](https://docs.docker.com/compose/how-tos/startup-order/)
- [Docker：Composeのサービス設定](https://docs.docker.com/reference/compose-file/services/)
- [Docker：up --wait](https://docs.docker.com/reference/cli/docker/compose/up/)
- [Docker：.envによる変数展開](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
- [Docker：共有メモリの上限](https://docs.docker.com/engine/containers/run/#runtime-constraints-on-resources)
- [PostgreSQL：pg_isready](https://www.postgresql.org/docs/current/app-pg-isready.html)
- [PostgreSQL：共有メモリの設定](https://www.postgresql.org/docs/current/runtime-config-resource.html)
