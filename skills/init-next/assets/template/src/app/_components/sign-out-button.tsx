"use client";
import { Button } from "@mantine/core";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { authClient } from "@/auth/client";

export function SignOutButton() {
  const translate = useTranslations();
  const router = useRouter();

  async function signOut() {
    await authClient.signOut();
    router.replace("/sign-in");
    router.refresh();
  }

  return (
    <Button variant="default" onClick={signOut}>
      {translate("pages.home.signOut")}
    </Button>
  );
}
