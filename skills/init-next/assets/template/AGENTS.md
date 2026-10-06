<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Project standards

Read [coding guidelines](docs/standards/base/coding-guidelines.md) and [directory rules](docs/standards/nextjs/implementation/directory-structure.md) before implementation. Use the [implementation index](docs/standards/nextjs/implementation/README.md) to read the rules relevant to the current feature: forms/i18n, environment, Prisma, queries, tables, authentication, AI SDK/Bedrock or asynchronous jobs. Use the [setup index](docs/standards/nextjs/setup/README.md) when adding dependencies or changing project configuration.

These documents define how to implement a requested feature; their presence does not require adding every feature to the application.

Use pnpm and the runtime versions in package.json. Run aqua-managed tools through `aqua exec --`. Preserve supply-chain restrictions and review dependency install scripts individually.

Use Mantine with CSS Modules and Tabler named imports; keep Tailwind out of the project. Keep root layout server-rendered. Use React Hook Form with Zod, not a second form-state library.

Place Node.js unit tests beside code as `*.test.ts`, with test helpers in `__tests__/`. Import Vitest APIs explicitly. Keep production code independent of tests, including through aliases. UI/browser test infrastructure is not part of the initial setup.

After relevant code/configuration changes, run `pnpm run lint`, `pnpm run typecheck`, `pnpm run test` and `pnpm run build`. When Docker or dependencies change, also verify the built container. Keep the lockfile and validate frozen installation. Lefthook checks lint/typecheck; CI additionally checks tests/build.

Docker Compose provides local PostgreSQL and Next.js runs locally during development. Keep Dockerfile and .dockerignore for standalone production builds. Include new required build inputs in the Docker allowlist and keep all .env files excluded.
