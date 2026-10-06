# TanStack Tableとnuqsの導入

`@tanstack/react-table`・`nuqs`を実行時依存へ追加し、[依存管理方針](../../base/pnpm-workspace.md)に従って完全固定する。
以下はTanStack Table v9・nuqs v2のAPIを使う。React Compilerは有効なままにする。

`src/app/layout.tsx`の`body`内に`NuqsAdapter`を追加する。
[Mantine](mantine.md)・[i18n](i18n.md#providerと利用方法)のProviderと組み合わせると、次の形になる。既存のmetadataや追加CSSは維持する。

```tsx
import "@mantine/core/styles.css";
import {
  ColorSchemeScript,
  MantineProvider,
  mantineHtmlProps,
} from "@mantine/core";
import { NextIntlClientProvider } from "next-intl";
import { NuqsAdapter } from "nuqs/adapters/next/app";

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ja" {...mantineHtmlProps}>
      <head>
        <ColorSchemeScript defaultColorScheme="light" />
      </head>
      <body>
        <NuqsAdapter>
          <NextIntlClientProvider>
            <MantineProvider defaultColorScheme="light">
              {children}
            </MantineProvider>
          </NextIntlClientProvider>
        </NuqsAdapter>
      </body>
    </html>
  );
}
```

layoutはServer Componentのままにする。`NuqsAdapter`の配下でnuqsのhooksを利用できる。


[テーブルの実装方針](../implementation/table.md)に従って画面へ接続する。

## 参考

- [TanStack Table：v9への移行](https://tanstack.com/table/latest/docs/framework/react/guide/migrating)
- [TanStack Table：サーバー側での検索・ページ分割](https://tanstack.com/table/latest/docs/framework/react/examples/with-tanstack-query)
- [TanStack Table：React Compiler](https://tanstack.com/table/latest/docs/framework/react/guide/react-compiler)
- [nuqs：Next.js用Adapter](https://nuqs.dev/docs/adapters)
- [nuqs：サーバー側の解析](https://nuqs.dev/docs/server-side)
- [nuqs：履歴・遷移](https://nuqs.dev/docs/options)
- [Mantine：Pagination](https://mantine.dev/core/pagination/)
- [Mantine：EmptyState](https://mantine.dev/core/empty-state/)
- [Mantine：Table](https://mantine.dev/core/table/)
- [MDN：IMEとkeydownの順序](https://developer.mozilla.org/en-US/docs/Web/API/Element/keydown_event#keydown_events_with_ime)
