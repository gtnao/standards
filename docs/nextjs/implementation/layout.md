# 共通レイアウト

認証済みの画面は、左にNavbarを置くMantineのAppShellで囲む。ヘッダーは置かない。
Navbarには上からロゴ、画面へのリンク、ログアウトを含むユーザーメニューを並べる。
配色や各部の見た目は[画面デザイン](design.md)に従う。

[Mantineの利用方針](mantine.md)と[ディレクトリ設計](directory-structure.md)に従う。

## 配置

```text
src/
  app/
    (app)/
      layout.tsx
      page.tsx
      _components/
        account-menu.tsx
    sign-in/
  components/
    app-layout/
      app-layout.tsx
      navigation-links.tsx
      user-menu.tsx
    app-logo.tsx
```

| ファイル | 種別 | 役割 |
| --- | --- | --- |
| `components/app-layout/app-layout.tsx` | Server | AppShellの骨組み。アプリ名・リンクの定義・ユーザーメニューを受け取る |
| `components/app-layout/navigation-links.tsx` | Client | 現在地を読み、該当するリンクをアクティブ表示にする |
| `components/app-layout/user-menu.tsx` | Client | ユーザー名のメニュー。ログアウトの操作をコールバックで通知する |
| `app/(app)/layout.tsx` | Server | セッション・リンク・翻訳済みの文言を用意し、共通レイアウトへ渡す |
| `app/(app)/_components/account-menu.tsx` | Client | ログアウトの処理をユーザーメニューへつなぐ |

認証が必要なページは、ルートグループ`(app)`の配下に置く。グループ名はURLに含まれず、配下のページへ同じ`layout.tsx`を適用できる。
ログイン画面のように共通レイアウトを適用しないページは、グループの外に置く。

## レイアウト本体

`src/components/app-layout/app-layout.tsx`：

```tsx
import {
  AppShell,
  AppShellMain,
  AppShellNavbar,
  AppShellSection,
} from "@mantine/core";
import type { ReactNode } from "react";
import { AppLogo } from "@/components/app-logo";
import { type NavigationItem, NavigationLinks } from "./navigation-links";

type Props = {
  appName: string;
  navigation: NavigationItem[];
  userMenu: ReactNode;
  children: ReactNode;
};

export function AppLayout({ appName, navigation, userMenu, children }: Props) {
  return (
    // The navbar stays beside the content at every width: there is no header
    // to hold a toggle for a collapsed navbar.
    <AppShell navbar={{ width: 240, breakpoint: 0 }} padding={0}>
      <AppShellNavbar p="xs">
        <AppShellSection p="xs">
          <AppLogo name={appName} />
        </AppShellSection>

        <AppShellSection grow component="nav">
          <NavigationLinks items={navigation} />
        </AppShellSection>

        <AppShellSection>{userMenu}</AppShellSection>
      </AppShellNavbar>

      <AppShellMain bg="gray.0">{children}</AppShellMain>
    </AppShell>
  );
}
```

レイアウト本体はServer Componentにする。`AppShell.Navbar`のような複合アクセスはServer Componentから使えないため、`AppShellNavbar`などを直接importする。
状態・イベント・現在地の参照が必要な部分だけを、Client Componentとして分ける。

`breakpoint: 0`で、画面幅によらずNavbarを本文の横に表示する。AppShellはbreakpoint未満でNavbarを全幅の開閉式に切り替えるが、ヘッダーがなく開閉ボタンを置く場所がないため、切り替えを使わない。
狭い画面への対応が必要になったら、開閉ボタンの置き場所と合わせて設計する。

`AppShell`の`padding`は0にし、本文の余白は[ページの枠](design.md#ページの枠)が付ける。`AppShellMain`へ直接余白を指定しない。

## リンク

`src/components/app-layout/navigation-links.tsx`：

```tsx
"use client";
import { NavLink, Stack } from "@mantine/core";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

export type NavigationItem = {
  href: string;
  label: string;
  icon: ReactNode;
};

type Props = {
  items: NavigationItem[];
};

export function NavigationLinks({ items }: Props) {
  const pathname = usePathname();

  return (
    <Stack gap={4}>
      {items.map((item) => {
        const active = isActive(pathname, item.href);
        return (
          <NavLink
            key={item.href}
            component={Link}
            href={item.href}
            label={item.label}
            leftSection={item.icon}
            active={active}
            color="gray"
            c={active ? "bright" : "dimmed"}
            fw={500}
            bdrs="md"
          />
        );
      })}
    </Stack>
  );
}

function isActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
```

リンクの定義は使う側から受け取り、共通コンポーネントには特定の画面を書かない。
アイコンは[Tabler Iconsの方針](mantine.md#tabler-icons)に従い、Server Componentで要素を作って渡す。
現在地は`usePathname`で読む。表示のためにフレームワークから現在地を読むことは、アプリ固有の処理を持つこととは区別する。

## ユーザーメニューとログアウト

`src/components/app-layout/user-menu.tsx`：

```tsx
"use client";
import { Avatar, Menu, NavLink } from "@mantine/core";
import { IconLogout, IconSelector } from "@tabler/icons-react";

type Props = {
  user: { name: string; email: string };
  labels: { signOut: string };
  onSignOut: () => void;
};

export function UserMenu({ user, labels, onSignOut }: Props) {
  return (
    <Menu position="top-start" width="target">
      <Menu.Target>
        <NavLink
          component="button"
          label={user.name}
          description={user.email}
          noWrap
          leftSection={<Avatar name={user.name} color="initials" size={32} />}
          bdrs="md"
          rightSection={<IconSelector size={16} aria-hidden="true" />}
        />
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Item
          leftSection={<IconLogout size={16} aria-hidden="true" />}
          onClick={onSignOut}
        >
          {labels.signOut}
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
}
```

`src/app/(app)/_components/account-menu.tsx`：

```tsx
"use client";
import { useRouter } from "next/navigation";
import { authClient } from "@/auth/client";
import { UserMenu } from "@/components/app-layout/user-menu";

type Props = {
  user: { name: string; email: string };
  labels: { signOut: string };
};

export function AccountMenu({ user, labels }: Props) {
  const router = useRouter();

  async function signOut() {
    await authClient.signOut();
    router.replace("/sign-in");
    router.refresh();
  }

  return <UserMenu user={user} labels={labels} onSignOut={signOut} />;
}
```

共通コンポーネントは、認証の呼び出しや遷移先などアプリ固有の処理を持たない。表示する値・翻訳済みの文言・コールバックをpropsで受け取る。
ログアウトの処理は`(app)`の`_components`に置き、共通のメニューへ`onSignOut`として渡す。Server Componentのlayoutからは関数を渡せないため、Client Componentでつなぐ。

`authClient.signOut()`の後に`router.replace("/sign-in")`・`router.refresh()`を呼ぶ。初期構成では、失敗時の表示や処理中の状態は設けない。

## ルートグループのlayout

`src/app/(app)/layout.tsx`：

```tsx
import { IconHome } from "@tabler/icons-react";
import { getTranslations } from "next-intl/server";
import { requireSession } from "@/auth/server";
import { AppLayout } from "@/components/app-layout/app-layout";
import { AccountMenu } from "./_components/account-menu";

export default async function Layout({ children }: LayoutProps<"/">) {
  const session = await requireSession();
  const translate = await getTranslations();

  return (
    <AppLayout
      appName={translate("app.name")}
      navigation={[
        {
          href: "/",
          label: translate("pages.home.title"),
          icon: <IconHome size={18} aria-hidden="true" />,
        },
      ]}
      userMenu={
        <AccountMenu
          user={{ name: session.user.name, email: session.user.email }}
          labels={{ signOut: translate("actions.signOut") }}
        />
      }
    >
      {children}
    </AppLayout>
  );
}
```

画面を追加したら、`navigation`へリンクを足す。リンクの文言には、その画面の`pages.<ページ名>.title`を使う。
アプリ名は`app.name`、ログアウトは`actions.signOut`に定義する（[キーの分類](i18n.md#キーの分類と命名)）。

layoutでセッションを取得するのは、ユーザー名の表示と未認証時のリダイレクトのため。
layoutは画面遷移のたびに再実行されるとは限らないため、[各ページ・Server Actionでも確認する](better-auth.md#セッション)。

## 参考

- [Mantine：AppShell](https://mantine.dev/core/app-shell/)
- [Mantine：Server Components](https://help.mantine.dev/q/server-components)
- [Next.js：Route Groups](https://nextjs.org/docs/app/api-reference/file-conventions/route-groups)
- [Next.js：layout](https://nextjs.org/docs/app/api-reference/file-conventions/layout)
