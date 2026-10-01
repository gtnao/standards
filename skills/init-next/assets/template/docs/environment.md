# Environment

Next.js loads root `.env` files; do not add dotenv or Node's `--env-file` to Next.js scripts.
Keep `.env` ignored and `.env.example` tracked. Both start empty; define variables only for actual requirements.

Read and validate server values in `src/env/server.ts`, protected with `server-only`. Add actual fields to the Zod schema and corresponding explicit `process.env.KEY` reads in `getServerEnv`. The initial empty schema intentionally requires no external services or secrets to build.
Call validation at the server entrypoint and pass validated settings into usecases/adapters. Do not import environment modules into usecases or domain.

Validate runtime-only secrets inside the getter rather than unconditionally at module import. A getter called during static rendering still runs during the build. Use a dynamic request path when values must be read at runtime; `connection()` is appropriate when intentionally opting out of prerendering. Use instrumentation startup validation only when required.

Create `src/env/public.ts` only when public values exist. Validate explicit `process.env.NEXT_PUBLIC_NAME` expressions; dynamic lookups and parsing all of `process.env` do not support Next.js inlining. Public values are fixed at build time. To vary public configuration at runtime, pass only public values from the server as props or via an API.
Do not combine server/public exports in an index file, expose a whole server environment object to clients, or use `next.config.env` for secrets.

Handle empty strings and defaults intentionally. Check emptiness before numeric coercion; use explicit boolean parsing rather than `Boolean("false")`. Use `@next/env` only for tools outside Next.js that need matching loading rules.
