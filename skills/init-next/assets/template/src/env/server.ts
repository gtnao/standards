import "server-only";
import { z } from "zod";

const serverEnvSchema = z.object({});

export function getServerEnv() {
  return serverEnvSchema.parse({});
}
