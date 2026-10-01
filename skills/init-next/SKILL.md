---
name: init-next
description: Scaffold a Next.js App Router project with pnpm, Mantine, next-intl, React Hook Form, Zod, PostgreSQL Compose, production Docker, CI and shared coding standards. Use when initializing a standalone Next.js application.
---

# Next.js scaffold

Create the project with the official create-next-app generator, then apply the self-contained template in this skill. Read [version selection and generation](references/setup.md) and the template's [directory](assets/template/docs/directory-structure.md), [coding](assets/template/docs/coding-guidelines.md), [forms/i18n](assets/template/docs/forms-and-i18n.md) and [environment](assets/template/docs/environment.md) rules before implementing.

## Scope

Use the user's target directory, initially empty except for an optional `.git`. Do not apply the configuration script to an existing application. When modifying an existing project, inspect differences and apply the relevant standards manually within the requested scope.

The scaffold includes Mantine, Tabler Icons, Japanese next-intl, React Hook Form, Zod, Biome, Node.js Vitest tests, aqua-managed Lefthook/pinact, GitHub Actions, PostgreSQL Compose and a production Dockerfile. Docker Compose and Dockerfile are required initial files. Next.js itself runs locally during development.

Keep `.env` and `.env.example` empty until actual variables are needed. The server environment module is ready for Zod fields; do not invent secrets, API endpoints, database access code, forms, authentication, ORM/migrations or empty architectural layers. Implement actual product behavior only when requested.

Only write inside the authorized project/workspace. Package managers, create-next-app, Docker and aqua can write caches or settings elsewhere: configure project-local caches/configuration when required by the user's restrictions. Do not install skills globally, modify another checkout, create remote repositories, change Rulesets, commit or push unless requested.

## Generate and configure

1. On every invocation, resolve current compatible stable versions from official sources with the seven-day waiting period. Template pins are examples, not defaults to reuse. Follow [setup.md](references/setup.md) and prepare the required versions JSON outside the target directory but inside the authorized workspace.
2. Run the selected create-next-app version with TypeScript, App Router, src, Biome, React Compiler, `--empty`, no Tailwind, `@/*`, pnpm, `--skip-install`, `--disable-git` and `--agents-md`. Verify current CLI options before invoking. Preserve its generated Next.js AGENTS.md block.
3. Inspect generated configuration, including dependency build decisions, then run:

   ```sh
   python3 /path/to/init-next/scripts/configure.py /absolute/project/path --versions /absolute/versions.json
   ```

   Resolve the script relative to this SKILL.md. It merges the verified dependency versions, applies project settings, appends rules outside the generated AGENTS.md content and adds `@AGENTS.md` to CLAUDE.md. It does not install packages or initialize Git. It requires a fresh uninstalled scaffold and rejects unexpected output collisions.
4. Review generator/template differences after major upgrades. Keep useful generated metadata, remove unused starter styles/assets, and ensure the template still matches the selected APIs. Keep README and tooling messages in English. Do not add arbitrary demo forms to exercise the installed form library.
5. Install with pnpm. Review blocked dependency scripts individually and add only justified `allowBuilds` decisions, preferably version-specific. For previously tested native distributions, SWC and Parcel watcher could run without install scripts; recheck the actual resolved versions/platform. Inspect esbuild's script before allowing it for Vitest. Do not disable strict builds, age checks or trust verification to get a green install. Keep `pnpm-lock.yaml`.
6. Initialize Git with `git init -b main` only if needed and not accidentally inside another repository. Install aqua tools and register hooks with `aqua install` and `aqua exec -- lefthook install`. Resolve/review Action references with `aqua exec -- pinact run --update --min-age 7`; pinact is not a CI job. Keep Lefthook limited to lint and typecheck.

## Verify the combined result

Run from the generated project:

```sh
pnpm run lint:fix
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run build
pnpm install --frozen-lockfile
aqua exec -- lefthook run pre-commit
docker compose config --quiet
docker compose up -d --wait
docker build -t project-name .
```

Use the selected project's image name. Check the PostgreSQL health status and run the production image with an available loopback port and `--init`. Verify the Japanese page, Mantine output and JS/CSS HTTP responses, non-root runtime and graceful stop. Check development startup too. No external credentials should be required for this baseline.

Confirm that typecheck generates next-intl declarations on a clean tree and that invalid translation keys/arguments are rejected; use a temporary type probe if needed, then remove it. Ensure `.env` is ignored, `.env.example` is trackable, generated message declarations are ignored and excluded from the Docker context. Inspect the production image for accidental secrets. Do not add trivial tests merely to avoid an empty suite; `passWithNoTests` supports the initial scaffold. Browser/UI test infrastructure is outside this baseline.

Stop only the processes/containers started for verification. Do not delete user data volumes or prune unrelated Docker resources. Remove temporary version metadata and test probes once they are reflected in project files.

If required tools, network access or permissions are unavailable, complete independent file work and report the specific unverified steps. Do not label configuration as tested based solely on reading the template. Report the location, current versions selected, completed checks and remaining limitations.
