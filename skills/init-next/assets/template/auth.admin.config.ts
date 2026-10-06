import { prismaAdapter } from "@better-auth/prisma-adapter";
import nextEnv from "@next/env";
import { PrismaPg } from "@prisma/adapter-pg";
import { betterAuth } from "better-auth/minimal";
import { z } from "zod";
import { adminOptions } from "./src/auth/admin";
import { authOptions } from "./src/auth/options";
import { PrismaClient } from "./src/prisma/generated/client";

nextEnv.loadEnvConfig(process.cwd(), process.env.NODE_ENV !== "production");

const env = z
  .object({
    DATABASE_URL: z.string().min(1),
    BETTER_AUTH_URL: z.url(),
    BETTER_AUTH_SECRET: z.string().min(32),
  })
  .parse({
    DATABASE_URL: process.env.DATABASE_URL,
    BETTER_AUTH_URL: process.env.BETTER_AUTH_URL,
    BETTER_AUTH_SECRET: process.env.BETTER_AUTH_SECRET,
  });

const prisma = new PrismaClient({
  adapter: new PrismaPg({
    connectionString: env.DATABASE_URL,
    connectionTimeoutMillis: 5_000,
  }),
});

export const auth = betterAuth({
  ...authOptions,
  ...adminOptions,
  baseURL: env.BETTER_AUTH_URL,
  secret: env.BETTER_AUTH_SECRET,
  database: prismaAdapter(prisma, { provider: "postgresql" }),
});
