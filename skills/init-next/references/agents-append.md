## Project standards

Read [coding guidelines](docs/standards/base/coding-guidelines.md) and [directory rules](docs/standards/nextjs/implementation/directory-structure.md) before implementation. Use the [implementation index](docs/standards/nextjs/implementation/README.md) to read the rules relevant to the current feature: forms/i18n, environment, Prisma, queries, tables, authentication, AI SDK/Bedrock or asynchronous jobs. Use the [setup index](docs/standards/nextjs/setup/README.md) when adding dependencies or changing project configuration.

These documents define how to implement a requested feature; their presence does not require adding every feature to the application.

Use pnpm and the runtime versions in package.json. Run aqua-managed tools through `aqua exec --`. Preserve supply-chain restrictions and review dependency install scripts individually.

Use Mantine with CSS Modules and Tabler named imports; keep Tailwind out of the project. Keep root layout server-rendered. Use React Hook Form with Zod, not a second form-state library.

Place Node.js unit tests beside code as `*.test.ts`, with test helpers in `__tests__/`. Import Vitest APIs explicitly. Keep production code independent of tests, including through aliases. UI/browser test infrastructure is not part of the initial setup.

After relevant code/configuration changes, run `pnpm run lint`, `pnpm run typecheck`, `pnpm run test` and `pnpm run build`. When Docker or dependencies change, also verify the built container. Keep the lockfile and validate frozen installation. Lefthook checks lint/typecheck; CI additionally checks tests/build.

Prisma is part of the initial setup; the schema starts with the authentication models. Add models to `prisma/schema.prisma` when a feature needs them, create the migration SQL with `pnpm run db:migrate --name <name>`, review it, then apply it with `pnpm run db:deploy`. Restart the dev server after the client is regenerated. Do not edit generated code under `src/prisma/generated` or migrations that were already applied.

Authenticated pages live under the `src/app/(app)` route group and share the AppShell layout in `src/components/app-layout`; add a navigation entry in the group's layout for each new page. Shared components take values, translated labels and callbacks through props, and leave auth calls and navigation targets to the route's own `_components`. Put messages that belong to no single page under `pages.shared`. Start each page with `PageHeader`, and change colours, radius and heading sizes in `src/app/_helpers/theme.ts` rather than per component; the design rules explain the grey content background and white surfaces.

Authentication uses Better Auth with email and password, the Admin plugin and database sessions. Protect pages with `requireSession()`, and check `getSession()` in Server Actions and Route Handlers before doing work. Public sign-up stays disabled: create users through the Admin API with the request headers, or the first administrator with `pnpm run auth:create-admin`. `auth.schema.config.ts` and `auth.admin.config.ts` are for the CLI only; do not import them from the application. After changing auth options, run `pnpm run auth:generate` and restore the table and column mappings before creating a migration.

Docker Compose provides local PostgreSQL and Next.js runs locally during development. Keep Dockerfile and .dockerignore for standalone production builds. Include new required build inputs in the Docker allowlist and keep all .env files excluded.
