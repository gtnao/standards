---
name: init-ts-cli
description: Scaffold a local TypeScript CLI project with pnpm, citty, Zod, Biome, Vitest, aqua, and shared coding guidelines. Use when initializing a standalone Node.js CLI project.
---

# TypeScript CLI scaffold

Use [assets/template](assets/template) as the baseline. It includes the configuration, CLI entrypoint, CI workflow, and development rules. Read the template's `AGENTS.md` and its linked guidelines before adapting code.

## Generate

1. Identify the user's target directory. The generator accepts an empty directory or one containing only `.git`. For an existing project, inspect conflicts and agree on the scope before replacing files.
2. Resolve `scripts/scaffold.py` relative to this `SKILL.md`, and run it with the absolute target path:

   ```sh
   python3 /path/to/init-ts-cli/scripts/scaffold.py /path/to/project
   ```

   The script copies all template files, derives the package name from the target directory, and creates an empty `.env`. It does not install dependencies or initialize Git.
3. Replace the greeting command when the user has specified actual CLI behavior. Split subcommands into separate files and register them in `src/entrypoints/cli/index.ts`. Create other layers as needed; do not generate empty layer directories or invented application requirements.

Keep `.env.example` empty until actual variables are needed. Install Zod, but introduce validation when there are values to validate. Keep README text and tooling messages in English.

## Install and configure

Run commands from the generated project. These steps download packages and tools and may write to package-manager caches outside the target. Respect the user's filesystem restrictions; if those writes are prohibited, leave the installation steps unexecuted and report that limitation.

The template pins the agreed pnpm, Biome, aqua registry, CLI tools, and Action versions. Preserve them unless an update is requested or compatibility requires one. Node.js stays on 24.x. Resolve the remaining dependencies under the template's seven-day release-age and trust restrictions, saving exact versions:

```sh
pnpm add -E citty zod
pnpm add -D -E typescript@7 tsx @types/node@24 @biomejs/biome@2.5.13 vitest
```

Review blocked dependency install scripts before adding `allowBuilds` entries. For example, inspect the resolved esbuild package and its install script before permitting its build. Do not disable `strictDepBuilds`, release-age checks, or trust checks to make installation succeed. Retry after the specific build decision; stop and report unresolved failures rather than weakening the policy. Keep `pnpm-lock.yaml` in the generated project.

Initialize a new Git repository with `git init -b main` if the target is not already a repository. Do not initialize inside another repository unintentionally. Then install the configured tools and register the hooks:

```sh
aqua install
aqua exec -- lefthook install
```

Keep Lefthook limited to lint and type checking. Use `aqua exec -- pinact run --min-age 7` when changing Action references; pinact is not a CI check. Do not create GitHub repositories, change remote rulesets, commit, or push unless requested.

## Verify

```sh
pnpm run lint:fix
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run build
pnpm dev --help
pnpm dev greet --name scaffold
pnpm start greet --name scaffold
pnpm install --frozen-lockfile
aqua exec -- lefthook run pre-commit
```

Adapt the smoke commands if the greeting was replaced. Confirm the source and compiled commands behave consistently, and that `dist` contains neither tests nor `vitest.config.js`. Check that `.env` is ignored and `.env.example` is trackable. Do not add trivial tests solely to avoid an empty test suite; `passWithNoTests` supports the initial scaffold.

Report the generated location, completed checks, and any installation or verification left incomplete. The skill is complete only when the generated files are usable, or the specific blocking condition has been reported.
