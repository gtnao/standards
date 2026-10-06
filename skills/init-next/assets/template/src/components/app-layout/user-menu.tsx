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
