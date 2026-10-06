# 環境変数の利用と検証

[導入と設定](../setup/env.md)を前提とする。

## 検証する時点

本番で使う秘密情報を、モジュールのimport時に無条件で検証しない。
Next.jsのビルド中にもモジュールが評価され得るため、実行時だけ必要な値までビルド環境へ要求することになる。
[サーバー用の定義](../setup/env.md#配置)では関数内で検証し、利用する処理の入口から呼ぶ。

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
同じ[Dockerイメージ](../setup/docker.md)で公開値も環境ごとに変えたい場合は、サーバーで検証した公開可能な値だけをpropsやAPIで渡す。
秘密情報を含む検証済みオブジェクト全体をClientへ渡さない。

`next.config`の`env`は使わない。接頭辞にかかわらずバンドルへの埋め込み対象になるため、サーバー用の環境変数設定として扱わない。

## テストとNext.js外の処理

[Baseのユニットテスト](../../base/testing.md)では、usecaseへ必要な値を渡し、実際の秘密情報やNext.jsの環境変数モジュールに依存させない。
スキーマ自体を検証したい場合は、純粋な検証部分を分離する。

VitestやORM設定など、Next.js外でも同じ`.env`読み込み規則が必要になった場合は`@next/env`の`loadEnvConfig()`を使う。
初期設定で実際の秘密情報をテストへ自動ロードする必要はない。

## 参考

- [Next.js：環境変数と公開値の埋め込み](https://nextjs.org/docs/app/guides/environment-variables)
- [Next.js：server-only](https://nextjs.org/docs/app/getting-started/server-and-client-components#preventing-environment-poisoning)
- [Next.js：connection](https://nextjs.org/docs/app/api-reference/functions/connection)
- [Next.js：起動時のinstrumentation](https://nextjs.org/docs/app/api-reference/file-conventions/instrumentation)
- [Next.js：next.configのenv](https://nextjs.org/docs/app/api-reference/config/next-config-js/env)
