import { getTranslations } from "next-intl/server";
import { requireSession } from "@/auth/server";
import { PageFrame } from "@/components/page-frame";

export default async function Page() {
  await requireSession();
  const translate = await getTranslations();

  return <PageFrame title={translate("pages.home.title")} />;
}
