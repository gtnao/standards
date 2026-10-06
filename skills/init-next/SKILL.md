---
name: init-next
description: Generate a Next.js App Router project from a reviewed, locked template with pnpm, Mantine, next-intl, React Hook Form, Zod, PostgreSQL Compose, Docker, CI and implementation standards.
---

# Next.js scaffold

Use the bundled, reviewed snapshot. Ordinary project creation needs no version research, create-next-app invocation, template inspection or full verification. Read further references only when updating the snapshot or implementing a requested feature.

## Generate and prepare

Use the user's target directory, empty except for an optional `.git`. Resolve the script relative to this SKILL.md:

```sh
python3 /path/to/init-next/scripts/generate.py /absolute/project/path
```

By default, copy the reviewed files, replace the project name, create empty `.env` and `.env.example`, initialize Git if needed, run `pnpm install --frozen-lockfile`, run `aqua install`, and register hooks with `aqua exec -- lefthook install`. Complete these steps as part of the skill; do not hand them back to the user as follow-up work. Use `--name lowercase-name` if needed.

pnpm, aqua and Git must already be available; executable paths can be supplied with `--pnpm` and `--aqua`. Use the tools’ existing configuration and standard storage locations. Preserve age/trust/build restrictions; report a blocked installation rather than weakening them or silently changing versions. Do not claim preparation is complete when a prerequisite or command failed.

Use `--files-only` only when the user explicitly requests file generation without installation. That mode needs only Python.

For an already generated project or a retry after a preparation failure:

```sh
python3 /path/to/init-next/scripts/generate.py /absolute/project/path \
  --prepare-only
```

This executes preparation without rewriting project files, `.env`, the lockfile or existing Git history. Do not stage, commit, push, change Rulesets or write outside the authorized workspace unless requested.

The template includes reviewed package versions, the lockfile, build-script decisions, Action SHAs and Docker digests. Do not run version research, create-next-app or pinact during normal setup. Do not start services or run full verification by default. Report successful preparation separately from verification; the snapshot is not a claim of latest versions.

## Verify only when requested

Generation and preparation do not imply full verification. When explicitly requested, run:

```sh
python3 /path/to/init-next/scripts/verify.py /absolute/project/path \
  --output /absolute/workspace/verification-results
```

Read the per-run summary and failure logs. `--only checks build dev docker` selects stages after a repair; report only what was checked. Docker and Compose verification starts temporary processes/containers and preserves data volumes. See [verification details](references/verification.md) for stages, cleanup and limitations.

## Implementing features

Generated AGENTS.md links to the bundled implementation rules, and CLAUDE.md references AGENTS.md. Read only the rules relevant to requested implementation work. Merely generating the scaffold does not require reading all standards or adding Prisma, authentication, tables, demo forms or empty architectural layers.

## Maintaining the snapshot

Only when the user requests a template update, follow [refreshing the snapshot](references/setup.md): research current versions, regenerate, review install scripts and run full verification before publishing the updated bundle. [snapshot.json](references/snapshot.json) records the bundled version selection; it is not a claim of current freshness.

In this repository, edit canonical rules under `docs/`, then run `python3 skills/init-next/scripts/sync_standards.py` and its `--check` mode. Keep the bundled AGENTS.md synchronized with `references/agents-append.md`. Consumers use the bundled files without needing this repository.
