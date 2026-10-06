import "server-only";
import { prismaAdapter } from "@better-auth/prisma-adapter";
import { betterAuth } from "better-auth/minimal";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { getServerEnv } from "@/env/server";
import { getPrisma } from "@/prisma/client";
import { adminOptions } from "./admin";
import { authOptions } from "./options";

let auth: ReturnType<typeof createAuth> | undefined;

export function getAuth() {
  auth ??= createAuth();
  return auth;
}

export async function getSession() {
  // Read the request first so that Next.js treats this as request-time work
  // before the auth settings read secrets from the environment.
  const requestHeaders = await headers();
  return getAuth().api.getSession({ headers: requestHeaders });
}

export async function requireSession() {
  const session = await getSession();
  if (session == null) {
    redirect("/sign-in");
  }
  return session;
}

function createAuth() {
  const env = getServerEnv();
  return betterAuth({
    ...authOptions,
    ...adminOptions,
    baseURL: env.BETTER_AUTH_URL,
    secret: env.BETTER_AUTH_SECRET,
    database: prismaAdapter(getPrisma(), { provider: "postgresql" }),
  });
}
