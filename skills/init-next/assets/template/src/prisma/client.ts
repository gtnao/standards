import "server-only";
import { PrismaPg } from "@prisma/adapter-pg";
import { getServerEnv } from "@/env/server";
import { PrismaClient } from "./generated/client";

const globalForPrisma = globalThis as typeof globalThis & {
  prisma?: PrismaClient;
};
let client: PrismaClient | undefined;

export function getPrisma() {
  if (client != null) {
    return client;
  }
  if (globalForPrisma.prisma != null) {
    client = globalForPrisma.prisma;
    return client;
  }

  const { DATABASE_URL } = getServerEnv();
  client = new PrismaClient({
    adapter: new PrismaPg({
      connectionString: DATABASE_URL,
      connectionTimeoutMillis: 5_000,
    }),
  });
  if (process.env.NODE_ENV !== "production") {
    globalForPrisma.prisma = client;
  }
  return client;
}
