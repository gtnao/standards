import { Center, Paper, Stack } from "@mantine/core";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { getSession } from "@/auth/server";
import { AppLogo } from "@/components/app-logo";
import { AuthForm } from "./_components/auth-form";

export default async function Page() {
  const session = await getSession();
  if (session != null) {
    redirect("/");
  }
  const translate = await getTranslations();

  return (
    <Center mih="100dvh" bg="gray.0" p="md">
      <Paper withBorder shadow="sm" p="xl" w="100%" maw={400}>
        <Stack gap="lg">
          <AppLogo name={translate("pages.shared.appName")} />
          <AuthForm />
        </Stack>
      </Paper>
    </Center>
  );
}
