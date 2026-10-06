import type { BetterAuthOptions } from "better-auth/minimal";

export const authOptions = {
  emailAndPassword: {
    enabled: true,
    disableSignUp: true,
    minPasswordLength: 8,
    maxPasswordLength: 128,
  },
} satisfies BetterAuthOptions;
