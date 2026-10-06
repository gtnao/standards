import { redirect } from "next/navigation";
import { getSession } from "@/auth/server";
import { AuthForm } from "./_components/auth-form";

export default async function Page() {
  const session = await getSession();
  if (session != null) {
    redirect("/");
  }

  return <AuthForm />;
}
