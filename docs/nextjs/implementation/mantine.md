# MantineとTabler Iconsの利用方針

[導入と設定](../setup/mantine.md)を前提とする。

## ServerとClientの境界

root layoutはServer Componentのままにする。Mantine側にClient境界があるため、表示するだけでpageやlayout全体へ`"use client"`を付ける必要はない。
childrenとして渡すServer Componentも、それだけでClient Componentにはならない。

hooks・イベント処理・ブラウザーAPIを使う部分は、[配置方針](directory-structure.md#serverとclientの境界)に従ってClient Componentへ分ける。
Server Componentから`Tabs.List`などの複合アクセスを使う場合は、`TabsList`を直接importするか、そのUIをClient側へ切り出す。

## Tabler Icons

必要なアイコンをnamed importする。

```tsx
import { Button } from "@mantine/core";
import { IconPlus } from "@tabler/icons-react";

export function AddButton() {
  return (
    <Button leftSection={<IconPlus size={16} aria-hidden="true" />}>
      追加
    </Button>
  );
}
```

文字と併用する装飾的なアイコンは`aria-hidden`にし、アイコンだけのボタンにはボタン側に`aria-label`を付ける。
色は既定の`currentColor`で文字色へ追従する。全アイコンを読み込む辞書は作らず、使用するものを明示する。

## 参考

- [Mantine：Next.jsへの導入](https://mantine.dev/guides/next/)
- [Mantine：PostCSS preset](https://mantine.dev/styles/postcss-preset/)
- [Mantine：カラーモード](https://mantine.dev/theming/color-schemes/)
- [Mantine：hydration差分への対応](https://help.mantine.dev/q/color-scheme-hydration-warning)
- [Mantine：Server Components](https://help.mantine.dev/q/server-components)
- [Mantine：アイコン](https://mantine.dev/guides/icons/)
- [Tabler：Reactでの利用](https://tabler.io/guides/how-to-use-svg-icons-in-react)
- [Next.js：import最適化](https://nextjs.org/docs/app/api-reference/config/next-config-js/optimizePackageImports)
