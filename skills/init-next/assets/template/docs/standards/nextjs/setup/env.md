# Next.jsの環境変数

[BaseのZodによる検証・変換](../../base/env.md)を採用し、Next.jsでは公開範囲と検証する時点を分ける。
`.env`はプロジェクトルートに置き、読み込みはNext.jsに任せる。

[利用時の方針](../implementation/env.md)も参照する。

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
| `.env.example` | [共通方針](../../base/env.md#ファイルと読み込みの方針)に従って共有し、秘密情報を入れない |

`server-only`はClient側への誤importをビルドエラーにする境界。値をprops・HTML・ログへ渡す操作まで防ぐものではない。
Next.jsはこのimportを内部で扱うため、動作のためにパッケージを別途インストールすることは必須ではない。
`ProcessEnv`の型拡張や`!`で、未検証の値の存在を保証しない。

## 参考

- [Next.js：環境変数と公開値の埋め込み](https://nextjs.org/docs/app/guides/environment-variables)
- [Next.js：server-only](https://nextjs.org/docs/app/getting-started/server-and-client-components#preventing-environment-poisoning)
- [Next.js：connection](https://nextjs.org/docs/app/api-reference/functions/connection)
- [Next.js：起動時のinstrumentation](https://nextjs.org/docs/app/api-reference/file-conventions/instrumentation)
- [Next.js：next.configのenv](https://nextjs.org/docs/app/api-reference/config/next-config-js/env)
