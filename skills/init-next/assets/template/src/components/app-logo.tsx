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
