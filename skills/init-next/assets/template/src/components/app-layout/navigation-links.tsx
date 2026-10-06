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
