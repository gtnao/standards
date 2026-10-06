"use client";
import { NavLink } from "@mantine/core";
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

  return items.map((item) => (
    <NavLink
      key={item.href}
      component={Link}
      href={item.href}
      label={item.label}
      leftSection={item.icon}
      active={isActive(pathname, item.href)}
    />
  ));
}

function isActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
