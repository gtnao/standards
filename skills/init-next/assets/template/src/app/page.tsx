import { Container, Title } from "@mantine/core";
import { getTranslations } from "next-intl/server";

export default async function Page() {
  const translate = await getTranslations();
  return (
    <Container py="xl">
      <Title>{translate("home.title")}</Title>
    </Container>
  );
}
