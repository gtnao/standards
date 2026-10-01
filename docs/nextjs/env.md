# Next.jsの環境変数

[BaseのZodによる検証・変換](../base/env.md)を採用し、Next.jsでは公開範囲と検証する時点を分ける。
`.env`はプロジェクトルートに置き、読み込みはNext.jsに任せる。

## 配置

アプリ固有の環境設定は`src/env/`にまとめ、サーバー用と公開用を分ける。

```text
src/
  env/
    server.ts
    public.ts    # 公開値が必要な場合だけ作る
```

サーバー側は`@/env/server`、公開値の利用側は`@/env/public`から直接importする。
サーバー用と公開用をまとめて再exportする`index.ts`は作らない。
業務処理には検証済みの値を引数で渡し、usecases・domainから環境変数モジュールへ依存させない。
アプリ固有の設定なので、汎用処理を置く`src/lib`には配置しない。

`src/env/server.ts`：

```ts
import "server-only";
import { z } from "zod";

const serverEnvSchema = z.object({
  API_KEY: z.string().trim().min(1),
});

export function getServerEnv() {
  return serverEnvSchema.parse({
    API_KEY: process.env.API_KEY,
  });
}
```

変数は実際の用途に合わせて定義する。
数値・booleanの変換、空文字や既定値の扱いはBaseに従う。利用側には検証済みの値を渡す。

## 読み込みと公開範囲

| 対象 | 方針 |
| --- | --- |
| ローカル | ルートの`.env`で始める。dotenvやCLI向けの`--env-file`は追加しない |
| 本番・CI | 実行環境から渡す。既存の`process.env`が`.env`類より優先される |
| サーバー用の値 | サーバー専用モジュールで検証し、Client Componentから参照させない |
| 公開値 | 必要な場合だけ別モジュールを作り、`NEXT_PUBLIC_*`を明示して検証する |
| `.env.example` | [共通方針](../base/env.md#ファイルと読み込みの方針)に従って共有し、秘密情報を入れない |

`server-only`はClient側への誤importをビルドエラーにする境界。値をprops・HTML・ログへ渡す操作まで防ぐものではない。
Next.jsはこのimportを内部で扱うため、動作のためにパッケージを別途インストールすることは必須ではない。
`ProcessEnv`の型拡張や`!`で、未検証の値の存在を保証しない。

## 検証する時点

本番で使う秘密情報を、モジュールのimport時に無条件で検証しない。
Next.jsのビルド中にもモジュールが評価され得るため、実行時だけ必要な値までビルド環境へ要求することになる。
冒頭の例では関数内で検証し、利用する処理の入口から呼ぶ。

ただし、関数にすれば必ず実行時になるわけではない。静的生成対象の処理から呼べばビルド中にも実行される。
実行時の値でページを描画する場合は、動的な実行経路で読み取る。例えば`connection()`の後に検証する。

```ts
import { connection } from "next/server";
import { getServerEnv } from "@/env/server";

await connection();
const env = getServerEnv();
```

`connection`は`next/server`からimportする。環境変数の読み込み用APIではなく、以降の処理をプリレンダリングから外すためのもの。
既にリクエスト時の実行になる処理へ、機械的に追加する必要はない。

遅延検証では、値の不足が初回利用まで検出されない。
起動時に必須項目を検証したい場合は、`instrumentation.ts`の`register()`から呼ぶ。必要なランタイムに合わせてサーバー用モジュールを読み込み、検証が完了してからリクエストを受け付ける。
ビルドに必要な値と本番起動に必要な値は、用途に合わせて分ける。

## ブラウザーへ公開する値

公開値が必要な場合だけ、`src/env/public.ts`に定義する。

```ts
import { z } from "zod";

const publicEnvSchema = z.object({
  NEXT_PUBLIC_API_ORIGIN: z.url(),
});

export const publicEnv = publicEnvSchema.parse({
  NEXT_PUBLIC_API_ORIGIN: process.env.NEXT_PUBLIC_API_ORIGIN,
});
```

Next.jsが置換できるよう、`process.env.NEXT_PUBLIC_API_ORIGIN`と静的に記述する。
`parse(process.env)`や動的なキー参照、`process.env`を別変数に代入してからの参照では、期待する埋め込みにならない。

`NEXT_PUBLIC_*`はビルド時に固定される。Zodで検証しても、ビルド後の差し替えが可能になるわけではない。
同じ[Dockerイメージ](docker.md)で公開値も環境ごとに変えたい場合は、サーバーで検証した公開可能な値だけをpropsやAPIで渡す。
秘密情報を含む検証済みオブジェクト全体をClientへ渡さない。

`next.config`の`env`は使わない。接頭辞にかかわらずバンドルへの埋め込み対象になるため、サーバー用の環境変数設定として扱わない。

## テストとNext.js外の処理

[Baseのユニットテスト](../base/testing.md)では、usecaseへ必要な値を渡し、実際の秘密情報やNext.jsの環境変数モジュールに依存させない。
スキーマ自体を検証したい場合は、純粋な検証部分を分離する。

VitestやORM設定など、Next.js外でも同じ`.env`読み込み規則が必要になった場合は`@next/env`の`loadEnvConfig()`を使う。
初期設定で実際の秘密情報をテストへ自動ロードする必要はない。

## 参考

- [Next.js：環境変数と公開値の埋め込み](https://nextjs.org/docs/app/guides/environment-variables)
- [Next.js：server-only](https://nextjs.org/docs/app/getting-started/server-and-client-components#preventing-environment-poisoning)
- [Next.js：connection](https://nextjs.org/docs/app/api-reference/functions/connection)
- [Next.js：起動時のinstrumentation](https://nextjs.org/docs/app/api-reference/file-conventions/instrumentation)
- [Next.js：next.configのenv](https://nextjs.org/docs/app/api-reference/config/next-config-js/env)
