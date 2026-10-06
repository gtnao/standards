import { getTranslations } from "next-intl/server";
import { requireSession } from "@/auth/server";
import { PageHeader } from "@/components/page-header";

export default async function Page() {
  const session = await requireSession();
  const translate = await getTranslations();

  return (
    <PageHeader
      title={translate("pages.home.title")}
      description={translate("pages.home.greeting", {
        name: session.user.name,
      })}
    />
  );
}
