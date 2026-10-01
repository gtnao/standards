## Project standards

Read these before implementing changes:

- [Coding guidelines](docs/coding-guidelines.md)
- [Directory structure](docs/directory-structure.md)
- [Forms and i18n](docs/forms-and-i18n.md)
- [Environment](docs/environment.md)

Use pnpm and the runtime versions in package.json. Run aqua-managed tools through `aqua exec --`. Preserve supply-chain restrictions and review dependency install scripts individually.

Use Mantine with CSS Modules and Tabler named imports; keep Tailwind out of the project. Keep root layout server-rendered. Use React Hook Form with Zod, not a second form-state library.

Place Node.js unit tests beside code as `*.test.ts`, with test helpers in `__tests__/`. Import Vitest APIs explicitly. Keep production code independent of tests, including through aliases. UI/browser test infrastructure is not part of the initial setup.

After relevant code/configuration changes, run `pnpm run lint`, `pnpm run typecheck`, `pnpm run test` and `pnpm run build`. When Docker or dependencies change, also verify the built container. Keep the lockfile and validate frozen installation. Lefthook checks lint/typecheck; CI additionally checks tests/build.

Docker Compose provides local PostgreSQL and Next.js runs locally during development. Keep Dockerfile and .dockerignore for standalone production builds. Include new required build inputs in the Docker allowlist and keep all .env files excluded.
