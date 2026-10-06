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
