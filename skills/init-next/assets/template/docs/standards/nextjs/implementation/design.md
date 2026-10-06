# 画面デザイン

Mantineの既定値を土台に、テーマの数項目と面の塗り分けだけで全体の印象を揃える。
独自のCSSやコンポーネントごとの色指定を増やさず、変更はテーマへ集める。

[Mantineの利用方針](mantine.md)と[共通レイアウト](layout.md)に従う。

## テーマ

`src/app/_helpers/theme.ts`：

```ts
import type { MantineThemeOverride } from "@mantine/core";

export const theme: MantineThemeOverride = {
  primaryColor: "indigo",
  defaultRadius: "md",
  headings: {
    fontWeight: "600",
    sizes: {
      h1: { fontSize: "1.5rem", lineHeight: "1.4" },
      h2: { fontSize: "1.25rem", lineHeight: "1.4" },
      h3: { fontSize: "1.125rem", lineHeight: "1.4" },
    },
  },
};
```

root layoutの`MantineProvider`へ渡す。

```tsx
import { theme } from "./_helpers/theme";

<MantineProvider theme={theme} defaultColorScheme="light">
  {children}
</MantineProvider>
```

| 項目 | 値・理由 |
| --- | --- |
| `primaryColor` | `indigo`。ボタンやロゴなど、操作と識別の要所にだけ使う基調色。プロジェクトに合わせて変更する |
| `defaultRadius` | `md`。入力欄・ボタン・カードの角丸を揃える |
| `headings` | 既定の見出しは管理画面には大きいため、h1を1.5remに抑え、太さを600にする |
| フォント | Mantineの既定(OSのフォント)のまま。Webフォントは追加しない |

テーマは関数を含まない値だけのオブジェクトにし、Server Componentのroot layoutからそのまま渡す。
`Button.extend`など関数を含む設定が必要になったら、[Client側のProvider用コンポーネントで組み立てる](../setup/mantine.md#カラーモードとテーマ)。

日本語のWebフォントは文字の範囲ごとに分割された多数のファイルになり、ビルド時の取得と初回表示の転送量が増える。見た目を揃える必要が出てから検討する。
色・角丸・見出しの大きさを変えるときは、個々のコンポーネントのpropsではなくテーマを変更する。

## 面の塗り分け

本文の領域とログイン画面の背景を薄いグレー(`gray.0`)にし、Navbarやカードを白い面として載せる。

| 場所 | 指定 |
| --- | --- |
| 認証済みの画面の本文 | [共通レイアウト](layout.md#レイアウト本体)の`AppShellMain`に`bg="gray.0"` |
| Navbar | 既定の白のまま |
| ログイン画面 | 外枠に`bg="gray.0"`、フォームは枠線つきの`Paper` |

bodyの背景色は変更しない。Navbarなど既定の背景色を使う面まで同じ色になるため、グレーにする領域へ個別に指定する。
本文の中身を`Paper`へ載せるかは画面ごとに判断する。

## ページの見出し

`src/components/page-header.tsx`：

```tsx
import { Stack, Text, Title } from "@mantine/core";

type Props = {
  title: string;
  description?: string;
};

export function PageHeader({ title, description }: Props) {
  return (
    <Stack gap={4} mb="lg">
      <Title>{title}</Title>
      {description != null && (
        <Text c="dimmed" fz="sm">
          {description}
        </Text>
      )}
    </Stack>
  );
}
```

認証済みの画面は、タイトルと補足の1行をこのコンポーネントで表示して書き出しを揃える。補足が不要な画面では`description`を省略する。

```tsx
import { getTranslations } from "next-intl/server";
import { requireSession } from "@/auth/server";
import { PageHeader } from "@/components/page-header";

export default async function Page() {
  const session = await requireSession();
  const translate = await getTranslations();

  return (
    <PageHeader
      title={translate("pages.home.title")}
      description={translate("pages.home.greeting", {
        name: session.user.name,
      })}
    />
  );
}
```

## ロゴ

`src/components/app-logo.tsx`：

```tsx
import { Group, Text, ThemeIcon } from "@mantine/core";

type Props = {
  name: string;
};

export function AppLogo({ name }: Props) {
  return (
    <Group gap="xs" wrap="nowrap">
      <ThemeIcon size={28} aria-hidden="true">
        <Text span fw={700} fz="sm">
          {name.charAt(0).toUpperCase()}
        </Text>
      </ThemeIcon>
      <Text fw={600} truncate>
        {name}
      </Text>
    </Group>
  );
}
```

アプリ名の頭文字を基調色の`ThemeIcon`に載せ、Navbarの上部とログイン画面で共有する。
実際のロゴ画像を用意したら、このコンポーネントの中身を差し替える。

## Navbar

[リンク](layout.md#リンク)は角丸を付け、現在地は薄いグレーの背景と濃い文字で示す。それ以外のリンクは文字を薄くする。基調色は使わない。
[ユーザーメニュー](layout.md#ユーザーメニューとログアウト)には、名前から生成するイニシャルの`Avatar`を添え、メールアドレスは1行に収める。

## ログイン画面

画面の中央に、幅400pxまでの枠線つきの`Paper`を置き、ロゴ・入力欄・ボタンだけを載せる。
ボタンの文言と重複するため、「ログイン」の見出しは置かない。

`src/app/sign-in/page.tsx`：

```tsx
import { Center, Paper, Stack } from "@mantine/core";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { getSession } from "@/auth/server";
import { AppLogo } from "@/components/app-logo";
import { AuthForm } from "./_components/auth-form";

export default async function Page() {
  const session = await getSession();
  if (session != null) {
    redirect("/");
  }
  const translate = await getTranslations();

  return (
    <Center mih="100dvh" bg="gray.0" p="md">
      <Paper withBorder shadow="sm" p="xl" w="100%" maw={400}>
        <Stack gap="lg">
          <AppLogo name={translate("pages.shared.appName")} />
          <AuthForm />
        </Stack>
      </Paper>
    </Center>
  );
}
```

## 参考

- [Mantine：テーマ](https://mantine.dev/theming/theme-object/)
- [Mantine：色](https://mantine.dev/theming/colors/)
- [Mantine：Avatar](https://mantine.dev/core/avatar/)
- [Mantine：NavLink](https://mantine.dev/core/nav-link/)
