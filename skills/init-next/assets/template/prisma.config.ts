import nextEnv from "@next/env";
import { defineConfig } from "prisma/config";
import { z } from "zod";

nextEnv.loadEnvConfig(process.cwd(), process.env.NODE_ENV !== "production");

const databaseUrl = z
  .string()
  .min(1)
  .optional()
  .parse(process.env.DATABASE_URL);

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: { path: "prisma/migrations" },
  ...(databaseUrl != null ? { datasource: { url: databaseUrl } } : {}),
});
