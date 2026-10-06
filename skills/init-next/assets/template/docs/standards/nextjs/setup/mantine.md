# MantineとTabler Iconsの初期設定

UIはMantine、アイコンはTabler Iconsを使う。
`@mantine/core`・`@mantine/hooks`・`@tabler/icons-react`を実行時依存へ追加する。
Mantineのcoreとhooksは同じ版に揃え、[依存管理の方針](../../base/pnpm-workspace.md)に従って互換性と待機期間を確認し、完全固定する。

`src/app/layout.tsx`にCSS・Provider・カラーモードの初期化を追加する。既存のmetadataなどは維持する。

```tsx
import "@mantine/core/styles.css";
import {
  ColorSchemeScript,
  MantineProvider,
  mantineHtmlProps,
} from "@mantine/core";

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ja" {...mantineHtmlProps}>
      <head>
        <ColorSchemeScript defaultColorScheme="light" />
      </head>
      <body>
        <MantineProvider defaultColorScheme="light">
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
```

独自のglobal CSSを使う場合は、MantineのCSSの後に読み込む。
生成済みの背景色やresetがMantineのスタイルと競合しないか確認する。

[利用時の方針](../implementation/mantine.md)も参照する。

## スタイルとPostCSS

独自のスタイルはCSS Modulesを基本にする。
`postcss`・`postcss-preset-mantine`・`postcss-simple-vars`を開発依存に追加し、ルートに`postcss.config.mjs`を置く。

```js
export default {
  plugins: {
    "postcss-preset-mantine": {},
    "postcss-simple-vars": {
      variables: {
        "mantine-breakpoint-xs": "36em",
        "mantine-breakpoint-sm": "48em",
        "mantine-breakpoint-md": "62em",
        "mantine-breakpoint-lg": "75em",
        "mantine-breakpoint-xl": "88em",
      },
    },
  },
};
```

Mantineのコンポーネントを表示するだけならPostCSS presetは必須ではないが、公式のCSS例で使うmixinや変換を利用できるよう採用する。
`postcss-simple-vars`はbreakpoint変数を扱う。テーマのbreakpointsを変更したら、この値も揃える。
設定ファイルは[ESMの方針](../../base/package-json.md#type)に合わせて`.mjs`にする。

## カラーモードとテーマ

| 項目 | 意味・理由 |
| --- | --- |
| `MantineProvider` | テーマとカラーモードをコンポーネントへ提供する |
| `ColorSchemeScript` | hydration前にカラーモードを反映し、初期表示のちらつきを抑える |
| `mantineHtmlProps` | htmlのカラーモード属性と、初期化による意図したhydration差分への対応を設定する |
| `defaultColorScheme="light"` | 最初は既定のライトを採用する方針を明示する。保存済みの選択があればそちらが優先される |

OS設定に合わせる場合は、ScriptとProviderの両方を`auto`にする。
ライト固定にする場合は、両方に`forceColorScheme="light"`を指定する。既定値をライトにすることとは異なる。
SSR時にはブラウザーの保存値を読めないため、初期表示をカラーモードで分岐させるときはCSSで切り替える。

初期テーマはMantineの既定値を使う。
色・フォント・コンポーネントの既定propsなどを変更する段階でテーマを定義する。
関数を含むテーマや`Button.extend`などを使う場合は、Client側のProvider用コンポーネント内で組み立てる。

## import最適化

Mantine公式は`experimental.optimizePackageImports`へのcore・hooksの追加を推奨している。
一方、Next.js公式では実験的機能とされているため、初期設定には追加せず、必要性を確認して検討する。
`@tabler/icons-react`はNext.js標準の最適化対象なので、追加指定は不要。

## 他の設定との統合

[i18nのProvider](i18n.md#providerと利用方法)を併用する場合は、同じServer Componentのlayoutで組み合わせる。
React Compilerの既存設定は維持する。
[Dockerの許可リスト](docker.md#dockerignore)には`postcss.config.mjs`を含める。

## 参考

- [Mantine：Next.jsへの導入](https://mantine.dev/guides/next/)
- [Mantine：PostCSS preset](https://mantine.dev/styles/postcss-preset/)
- [Mantine：カラーモード](https://mantine.dev/theming/color-schemes/)
- [Mantine：hydration差分への対応](https://help.mantine.dev/q/color-scheme-hydration-warning)
- [Mantine：Server Components](https://help.mantine.dev/q/server-components)
- [Mantine：アイコン](https://mantine.dev/guides/icons/)
- [Tabler：Reactでの利用](https://tabler.io/guides/how-to-use-svg-icons-in-react)
- [Next.js：import最適化](https://nextjs.org/docs/app/api-reference/config/next-config-js/optimizePackageImports)
