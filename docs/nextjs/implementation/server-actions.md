# Server Actionsの実装方針

クライアントからの作成・更新・削除・非同期ジョブ登録は、基本的にServer Actionを入口にする。
取得はServer Componentsから[queries](queries.md)を呼ぶ形を基本とする。
Webhook・外部向けAPI・ストリーミングはRoute Handler、[Better Authの認証フロー](better-auth.md)は既存のSDKを使う。

## 配置・命名

[ディレクトリ設計](directory-structure.md)に従い、利用するページに近い`_helpers/actions.ts`へ置く。
複数ページで共有する場合は、共通の親の`_helpers`へ寄せる。

```text
src/app/
  _helpers/
    server-action-result.ts
  posts/
    _components/
      post-form.tsx
    _helpers/
      actions.ts
      form-schema.ts
```

- Actionファイルは先頭に`"use server"`を書き、公開するasync関数に`Action`サフィックスを付ける。
- 引数は一つの`input`オブジェクトにする。引数が不要な操作は引数なしでよい。
- `Args`はActionの近くに定義し、外部から参照する必要がなければexportしない。
- スキーマ・共有型は別ファイルに置く。`"use server"`ファイルは公開するActionを揃える場所にする。
- 共通コンポーネントから特定ページのActionをimportせず、処理をpropsで受け取る。

## 責務と処理順

| Server Action | usecase |
| --- | --- |
| セッションから実行者を取得 | 対象に対する認可・業務条件を確認 |
| Zodで受信値を検証 | 業務処理・DB更新・トランザクション |
| 必要なadapterや設定を組み立てる | 渡された依存を利用 |
| 結果を画面向けに変換・翻訳 | UIや翻訳に依存しない結果を返す |
| キャッシュ更新・遷移 | Next.jsのAPIに依存しない |

基本の順序は、認証・入力検証・usecase呼び出し・成功後の表示更新とする。
認証には[既存の`getSession()`](better-auth.md#セッション)を使い、未認証時の応答をActionで決める。
ページやlayoutで認証済みでも、Actionは直接呼び出され得るため、改めて確認する。

実行者のID・権限はクライアントの自己申告を使わず、取得したセッションから決める。
対象IDに対する操作権限はusecaseで検証する。Action内のDB直接操作や、更新可否を確認するためのqueries呼び出しは避ける。

最初から`withAction`のような汎用ラッパーは設けない。
認証・検証・エラー変換の重複が実際に増えたら、共通化する範囲を決める。

## 入力検証とRHF

フォームの値と、操作対象のIDなどの文脈を分けて受け取る。

```ts
type Args = {
  itemId: string;
  formData: UpdateItemFormValues;
};
```

`formData`はフォーム値のオブジェクトを表し、ブラウザーの`FormData`型には限定しない。
フォームを伴わない操作で、空の`formData`を作る必要はない。
IDを含めて受信値全体をZodで検証し、検証後の値だけをusecaseへ渡す。
引数のTypeScript型は呼び出し側の補助であり、実際に受信する値を保証しない。

[RHFの方針](react-hook-form.md)に従い、`handleSubmit`が渡す検証・変換後の値を送る。
サーバー側のスキーマは、その送信形式を受け付けるものにする。
`trim`など再適用できる検証は共通化できるが、文字列から別の型へ変換する`transform`などを入力前提のまま二重適用しない。
必要なら入力用スキーマと送信用の出力スキーマを分け、共通の制約を再利用する。

スキーマに渡す文言は、Action側でも`getTranslations()`から取得する。
変数名は`translate`、キーは完全なキーとし、[i18nの分類](i18n.md)に従う。

## 戻り値

成功・想定内の失敗は`ServerActionResult<T>`へ揃える。
RHFから通常の関数として呼ぶことを基本とし、`useActionState`の導入は必須にしない。

`src/app/_helpers/server-action-result.ts`：

```ts
export type ServerActionResult<T> =
  | { success: true; data: T }
  | { success: false; error: { message: string } };
```

データ不要の成功は`ServerActionResult<void>`で`{ success: true, data: undefined }`を返す。
`T`はクライアントで必要な、Reactでシリアライズ可能な値にする。usecaseの戻り値をそのまま渡せる場合は利用し、内部情報を含む場合は必要な項目だけへ変換する。
PrismaのレコードやErrorオブジェクトを丸ごと返さない。

未認証・入力不正・業務上の拒否など、想定内の失敗は利用者向けの文言へ変換する。
最初はフォーム全体のエラーとして扱い、RHFの`setError("root", ...)`へ渡す。
サーバーから項目ごとのエラーを返す必要が出たら、共有型にフィールドエラーの契約を追加する。各Actionで場当たり的な交差型を作らない。

予期しない障害は想定内の失敗と区別し、原因をサーバー側へ記録する。
クライアント側でも通信・実行エラーを処理し、安全な文言を表示する。例外の`message`をそのまま表示しない。
すべての例外を`success: false`へ変換して握り潰す共通catchは設けない。

## Actionの例

[Prismaのusecase例](prisma.md#usecasesでの利用)の`publishPost`を呼び出す。
そのusecaseは、公開できた場合に`true`、対象なし・権限なし・公開済みの場合に`false`を返す。

```ts
"use server";

import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";
import { z } from "zod";
import { getSession } from "@/auth/server";
import { publishPost } from "@/usecases/publish-post";
import type { ServerActionResult } from "@/app/_helpers/server-action-result";

type Args = { postId: string };

export async function publishPostAction(
  input: Args,
): Promise<ServerActionResult<void>> {
  const session = await getSession();
  const translate = await getTranslations();
  if (!session) {
    return {
      success: false,
      error: { message: translate("pages.posts.authenticationRequired") },
    };
  }

  const parsed = z.object({ postId: z.string().min(1) }).safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: { message: translate("validation.invalid") },
    };
  }

  const published = await publishPost({
    input: { id: parsed.data.postId, authorId: session.user.id },
  });
  if (!published) {
    return {
      success: false,
      error: { message: translate("pages.posts.cannotPublish") },
    };
  }

  revalidatePath("/posts");
  return { success: true, data: undefined };
}
```

`messages/ja.json`へ追加する文言：

```json
{
  "pages": {
    "posts": {
      "authenticationRequired": "ログインしてください",
      "cannotPublish": "この投稿は公開できません"
    }
  },
  "validation": {
    "invalid": "入力内容を確認してください"
  }
}
```

例ではIDを非空文字列として検証する。実際のIDがUUIDや整数なら、その形式・範囲まで検証する。
同じ入力を複数箇所で検証する場合は、近くのスキーマファイルへ切り出す。

## 更新後の表示と遷移

業務更新が成功してから、影響する表示やキャッシュを更新する。
`revalidatePath`は対象パスの無効化、`router.push`や`redirect`は画面遷移であり、役割が異なる。
遷移するから無効化不要とは判断せず、利用しているキャッシュに合わせて選ぶ。
タグで共有したキャッシュを更新する場合は、対象タグの無効化も検討する。

パス・タグはAction側で決め、クライアントから自由に指定させない。
`redirect()`は制御用の例外を投げるため、通常の失敗を扱うcatchの外で呼ぶ。
遷移をActionが担当する場合は、成功時に戻り値を受け取る前提のUIと混在させない。

キャッシュ更新や通信に失敗しても、DB更新は既に成功している場合がある。
その失敗をDB更新失敗として自動再実行しない。再実行で重複が困る操作には、業務側の冪等性を設ける。
RHFでは送信処理をawaitし、送信中のボタンを無効にする。ただし、これだけで二重実行を防げるとは扱わない。

長時間の処理はAction内で完走させず、[非同期ジョブ](../../base/async-jobs.md)を登録してIDを返す。

## 参考

- [Next.js：更新処理](https://nextjs.org/docs/app/getting-started/mutating-data)
- [Next.js：Server Actionsのセキュリティ](https://nextjs.org/docs/app/guides/data-security)
- [Next.js：revalidatePath](https://nextjs.org/docs/app/api-reference/functions/revalidatePath)
- [Next.js：redirect](https://nextjs.org/docs/app/api-reference/functions/redirect)
- [React：Server Functionの引数と戻り値](https://react.dev/reference/rsc/use-server#serializable-parameters-and-return-values)
