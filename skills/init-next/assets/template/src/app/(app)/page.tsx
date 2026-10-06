import { Title } from "@mantine/core";
import { getTranslations } from "next-intl/server";
import { requireSession } from "@/auth/server";

export default async function Page() {
  await requireSession();
  const translate = await getTranslations();

  return <Title>{translate("pages.home.title")}</Title>;
}
