import { IconHome } from "@tabler/icons-react";
import { getTranslations } from "next-intl/server";
import { requireSession } from "@/auth/server";
import { AppLayout } from "@/components/app-layout/app-layout";
import { AccountMenu } from "./_components/account-menu";

export default async function Layout({ children }: LayoutProps<"/">) {
  const session = await requireSession();
  const translate = await getTranslations();

  return (
    <AppLayout
      appName={translate("app.name")}
      navigation={[
        {
          href: "/",
          label: translate("pages.home.title"),
          icon: <IconHome size={18} aria-hidden="true" />,
        },
      ]}
      userMenu={
        <AccountMenu
          user={{ name: session.user.name, email: session.user.email }}
          labels={{ signOut: translate("actions.signOut") }}
        />
      }
    >
      {children}
    </AppLayout>
  );
}
