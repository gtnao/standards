# React Hook Formの初期設定

フォームの状態管理はReact Hook Form、検証・変換はZod、入力UIは[Mantine](../setup/mantine.md)を使う。
[依存の導入](../setup/react-hook-form.md)後、次の方針でフォームを実装する。

## 配置と責務

[ディレクトリ設計](directory-structure.md)に従い、そのページの`_components/`にフォーム、`_helpers/form-schema.ts`にスキーマを置く。
スキーマはクライアント・サーバー双方から使えるようにし、next-intlやサーバー専用モジュールへ依存させない。

標準の`useForm`と`Controller`から始める。共通hookや入力ラッパーは重複が生じてから検討し、入力型・出力型・フィールド名の型を保つ。

## スキーマとエラーメッセージ

状態によって項目の有無・必須性が変わる場合は、`discriminatedUnion`で表す。
次は、日時として扱う場合だけ書式が必須になる例。

`_helpers/form-schema.ts`：

```ts
import { z } from "zod";

type FormMessages = {
  required: string;
};

export function createFormSchema(messages: FormMessages) {
  const requiredString = z.string().trim().min(1, {
    error: messages.required,
  });

  return z.object({
    byType: z.discriminatedUnion("type", [
      z.object({
        type: z.literal("string"),
        value: requiredString,
      }),
      z.object({
        type: z.literal("timestamp"),
        value: requiredString,
        format: requiredString,
      }),
    ]),
  });
}
```

検証後の値は、`byType.type === "timestamp"`の分岐内で`format: string`として扱える。
エラー参照の都合で、不要な項目を`z.unknown()`として別ブランチへ追加しない。

大小関係などの項目間検証には`refine`・`superRefine`を使い、エラーの`path`を表示対象のフィールドへ向ける。
検証条件を追加しただけでは、TypeScript上の任意項目が必須になるわけではない。

## i18nとuseFormの接続

[i18nの方針](i18n.md)に従い、`messages/ja.json`へ文言を追加する。

```json
{
  "validation": {
    "required": "入力してください",
    "invalid": "入力内容を確認してください"
  }
}
```

フォームのClient Component内で、翻訳した文言を渡してスキーマを組み立てる。

```tsx
const translate = useTranslations();

const schema = createFormSchema({
  required: translate("validation.required"),
});

type FormInput = z.input<typeof schema>;
type FormOutput = z.output<typeof schema>;

const form = useForm<FormInput, unknown, FormOutput>({
  resolver: zodResolver(schema, {
    error: () => translate("validation.invalid"),
  }),
  defaultValues: {
    byType: {
      type: "string",
      value: "",
    },
  } satisfies FormInput,
});

const type = useWatch({
  control: form.control,
  name: "byType.type",
});
```

`useForm`・`useWatch`・`Controller`は`react-hook-form`、`zodResolver`は`@hookform/resolvers/zod`からimportする。

| 指定 | 意味 |
| --- | --- |
| `FormInput` | 入力中の値。初期値・Controller・getValuesなどで使う |
| `FormOutput` | Zodによる検証・変換後の値。handleSubmitの成功コールバックが受け取る |
| 第2型引数の`unknown` | resolverへ渡すcontextの型。スキーマの`z.unknown()`とは別 |
| `satisfies FormInput` | RHF標準では部分指定できる初期値を、入力型に対して確認する |
| `useWatch` | 表示切り替えに使う値を購読する。React Compilerとの整合性からも、描画には`form.watch()`を使わない |

翻訳キーと埋め込み引数は`translate`の呼び出し時に型チェックされる。
スキーマに指定した文言が優先され、型の不一致など、それ以外のエラーはresolverの`error`で補う。
共通のエラー分類が増えたら、この関数を共通error mapへ切り出す。

フォームやリクエストごとの文言を`z.config()`でグローバルに切り替えない。
RHFへは翻訳済みのメッセージを渡し、`error.message`を翻訳キーへキャストしない。

## Mantineとの接続

入力は`Controller`で接続し、エラーは`fieldState.error?.message`を渡す。
先ほどの`type`に応じて表示するフィールドは、次のように書く。

```tsx
{type === "timestamp" && (
  <Controller
    control={form.control}
    name="byType.format"
    defaultValue=""
    render={({ field, fieldState }) => (
      <TextInput {...field} error={fieldState.error?.message} />
    )}
  />
)}
```

unionの片側にしかないフィールドも、`name`に指定できる。
`errors.byType.format`を直接参照するために型を付け替える必要はない。

| 入力 | 接続方法・値の扱い |
| --- | --- |
| TextInput・Textarea | 基本は`field`を渡す。空欄は`""`で表す |
| Checkbox・Switch | `field.value`を`checked`へ渡し、`event.currentTarget.checked`を`field.onChange`へ渡す |
| Select | 選択値と未選択の`null`を入力型で扱う |
| NumberInput | 通常モードでも`number \| string`。空欄や入力途中の文字列を扱ってから検証・変換する |

同じ入力に`Controller`と`register`を重ねない。値の形式に合わせて接続しても、`onBlur`・`name`・`ref`は維持する。
後から表示される入力にも初期値を用意し、`undefined`で開始させない。
数値変換では、`z.coerce.number()`だけだと空文字が`0`になるため、先に空欄を検証する。

## 切り替えと送信

非表示になった入力は、基本的に既定の`shouldUnregister: false`で保持し、戻ったときに復元できるようにする。
通常の`z.object()`では、選択中のブランチに定義していない項目は解析結果から除去される。
送信には`handleSubmit`が渡す検証・変換後の値を使う。

切り替え時に入力を破棄する仕様なら、登録解除を選ぶ。`shouldUnregister`は`useFieldArray`の並べ替えなどにも影響するため、一律に`true`へ変更しない。
項目間検証を入力変更時にも表示する場合は、関連項目の変更で表示先のエラーも再検証されるようにする。

[Server Action](server-actions.md)などの入口でも受信値を再検証し、検証済みの値をusecaseへ渡す。
サーバー側は`getTranslations()`から取得した文言でスキーマを組み立て、`safeParse`などの`error`オプションにも共通の文言を渡す。
RHFからは変換後の値を送るため、サーバー側もその形式を受け付けるスキーマにする。共通のスキーマを使う場合は、`transform`などを二重適用して問題がないか確認する。
予期しない保存エラーを利用者向けの文言へ置き換える場合も、原因はサーバー側のログへ残す。入力検証の失敗と内部エラーを同じ扱いで握り潰さない。
クライアント側の検証やTypeScriptの型だけで、受信値が正しいと扱わない。

## 参考

- [React Hook Form：Controller](https://react-hook-form.com/docs/usecontroller/controller)
- [React Hook Form：useForm](https://react-hook-form.com/docs/useform)
- [公式resolvers：入力型と出力型](https://github.com/react-hook-form/resolvers#typescript)
- [Zod：エラーのカスタマイズ](https://zod.dev/error-customization)
- [Zod：discriminated union](https://zod.dev/api#discriminated-unions)
- [Mantine：Checkbox](https://mantine.dev/core/checkbox/)
- [Mantine：Select](https://mantine.dev/core/select/)
- [Mantine：NumberInput](https://mantine.dev/core/number-input/)
- [React：React CompilerとuseWatch](https://react.dev/reference/eslint-plugin-react-hooks/lints/incompatible-library)
