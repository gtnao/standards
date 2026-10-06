---
name: init-next
description: Scaffold a Next.js App Router project with pnpm, Mantine, next-intl, React Hook Form, Zod, PostgreSQL Compose, production Docker, CI and shared coding standards. Use when initializing a standalone Next.js application.
---

# Next.js scaffold

Create the project with the official create-next-app generator, then apply the self-contained template in this skill. Read [version selection and generation](references/setup.md), the bundled [setup index](assets/template/docs/standards/nextjs/setup/README.md), [coding guidelines](assets/template/docs/standards/base/coding-guidelines.md), and [directory rules](assets/template/docs/standards/nextjs/implementation/directory-structure.md). The [implementation index](assets/template/docs/standards/nextjs/implementation/README.md) routes later feature work to its relevant rules.

## Scope

Use the user's target directory, initially empty except for an optional `.git`. Do not apply the configuration script to an existing application. When modifying an existing project, inspect differences and apply the relevant standards manually within the requested scope.

The scaffold includes Mantine, Tabler Icons, Japanese next-intl, React Hook Form, Zod, Biome, Node.js Vitest tests, aqua-managed Lefthook/pinact, GitHub Actions, PostgreSQL Compose and a production Dockerfile. Docker Compose and Dockerfile are required initial files. Next.js itself runs locally during development.

Keep `.env` and `.env.example` empty until actual variables are needed. The server environment module is ready for Zod fields; do not invent secrets, API endpoints, database access code, forms, authentication, ORM/migrations or empty architectural layers. Implement actual product behavior only when requested. Still copy all bundled standards and link the implementation index from AGENTS.md, so later work follows the Prisma, authentication, query and table rules without installing those features in the initial scaffold.

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

Run `pnpm run lint:fix` once after configuration, then use the verifier instead of issuing each check separately:

```sh
python3 /path/to/init-next/scripts/verify.py /absolute/project/path \
  --output /absolute/workspace/verification-results
```

Keep the output outside the generated project, inside the authorized workspace. Use `--pnpm /absolute/path/to/pnpm` if needed. The script respects supplied cache environment variables; otherwise it places package-manager caches under the output directory. Reuse the same output directory and cache environment from installation to avoid downloading the toolchain twice.

The verifier runs frozen install, lint/typecheck/tests, build, development HTTP checks, Compose health checks and a production Docker smoke test. It checks Japanese HTML, Mantine markup, JS/CSS responses, non-root runtime, writable cache, absence of root .env files and graceful container shutdown. Lint/typecheck/tests run in parallel; type generation, build and server startup do not overlap. It checks Git exclusions and the executable Lefthook hook without repeating lint/typecheck through the hook. Each invocation keeps logs and a `summary.json` with per-check durations in a separate run directory; partial reruns do not overwrite earlier evidence. It stops only processes/containers it started, removes its uniquely named test image/container and preserves Compose volumes.

Read the summary; open individual logs only on failure. Do not repeat successful commands manually. After a repair, use `--only` with the affected stages:

| Change | Stages to rerun |
| --- | --- |
| Source, TypeScript, messages or framework settings | `checks build dev docker` |
| Dockerfile or .dockerignore only | `docker` |
| Compose only | `docker` |
| Dependencies, lockfile or package-manager settings | Full verification |
| Documentation only | Link checks; no application rebuild |

Partial runs verify only the selected stages; retain evidence from the preceding full run and report any unverified stages. No automatic reuse of old pass results is inferred from timestamps.

The checks stage temporarily adds a translation type probe to the existing typecheck: invalid keys and missing interpolation arguments must be rejected. It restores the original messages and regenerates their declarations afterward, including on failure. The script does not inspect publishers/build scripts or scan arbitrary application secrets; retain the earlier dependency review and review the Docker allowlist for secret exposure. Browser/UI test infrastructure is outside this baseline. No external credentials should be required for the empty scaffold.

If required tools, network access or permissions are unavailable, finish independent work and report the failed or unverified stages. Do not call the full setup verified merely because a partial run passed. Report the location, selected versions and summary of checks.

## Maintaining this skill

In the standards repository, edit canonical documents under `docs/`, then run `python3 skills/init-next/scripts/sync_standards.py`. Check with `--check` before distributing the skill. The bundle preserves Base and CLI link targets as well as Next.js documents, so generated projects do not depend on this repository being present. Do not maintain a separate summary of the same rules.
