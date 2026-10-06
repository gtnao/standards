import { betterAuth } from "better-auth/minimal";
import { adminOptions } from "./src/auth/admin";
import { authOptions } from "./src/auth/options";

export const auth = betterAuth({ ...authOptions, ...adminOptions });
