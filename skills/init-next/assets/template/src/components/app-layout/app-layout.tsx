import {
  AppShell,
  AppShellMain,
  AppShellNavbar,
  AppShellSection,
  Text,
} from "@mantine/core";
import type { ReactNode } from "react";
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
    <AppShell navbar={{ width: 240, breakpoint: 0 }} padding="md">
      <AppShellNavbar p="xs">
        <AppShellSection p="xs">
          <Text fw={700}>{appName}</Text>
        </AppShellSection>

        <AppShellSection grow component="nav">
          <NavigationLinks items={navigation} />
        </AppShellSection>

        <AppShellSection>{userMenu}</AppShellSection>
      </AppShellNavbar>

      <AppShellMain>{children}</AppShellMain>
    </AppShell>
  );
}
