import { Container, Stack, Title } from "@mantine/core";
import { getTranslations } from "next-intl/server";
import { requireSession } from "@/auth/server";
import { SignOutButton } from "./_components/sign-out-button";

export default async function Page() {
  await requireSession();
  const translate = await getTranslations();

  return (
    <Container py="xl">
      <Stack align="flex-start">
        <Title>{translate("pages.home.title")}</Title>
        <SignOutButton />
      </Stack>
    </Container>
  );
}
