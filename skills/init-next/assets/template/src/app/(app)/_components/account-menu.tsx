"use client";
import { useRouter } from "next/navigation";
import { authClient } from "@/auth/client";
import { UserMenu } from "@/components/app-layout/user-menu";

type Props = {
  user: { name: string; email: string };
  labels: { signOut: string };
};

export function AccountMenu({ user, labels }: Props) {
  const router = useRouter();

  async function signOut() {
    await authClient.signOut();
    router.replace("/sign-in");
    router.refresh();
  }

  return <UserMenu user={user} labels={labels} onSignOut={signOut} />;
}
