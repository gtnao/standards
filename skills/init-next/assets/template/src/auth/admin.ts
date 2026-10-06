import { APIError, createAuthMiddleware } from "better-auth/api";
import type { BetterAuthOptions } from "better-auth/minimal";
import { admin } from "better-auth/plugins";
import { createAccessControl } from "better-auth/plugins/access";
import { defaultStatements } from "better-auth/plugins/admin/access";
import { z } from "zod";
import { authOptions } from "./options";

const ac = createAccessControl(defaultStatements);

const roles = {
  admin: ac.newRole({ user: ["create", "list", "get"] }),
  user: ac.newRole({}),
};

const passwordSchema = z
  .string()
  .min(authOptions.emailAndPassword.minPasswordLength)
  .max(authOptions.emailAndPassword.maxPasswordLength);

export const adminOptions = {
  plugins: [admin({ ac, roles })],
  hooks: {
    // Admin user creation accepts a missing or short password by default.
    before: createAuthMiddleware(async (ctx) => {
      if (ctx.path !== "/admin/create-user") {
        return;
      }
      if (!passwordSchema.safeParse(ctx.body?.password).success) {
        throw new APIError("BAD_REQUEST", {
          message: "Invalid password",
          code: "INVALID_PASSWORD",
        });
      }
    }),
  },
} satisfies BetterAuthOptions;
