---
name: init-next
description: Generate a Next.js App Router project from a reviewed, locked template with pnpm, Mantine, next-intl, React Hook Form, Zod, PostgreSQL Compose, Docker, CI and implementation standards.
---

# Next.js scaffold

Use the bundled, reviewed snapshot. Ordinary project creation needs no version research, create-next-app invocation, template inspection or full verification. Read further references only when updating the snapshot or implementing a requested feature.

## Generate

Use the user's target directory, empty except for an optional `.git`. Resolve the script relative to this SKILL.md:

```sh
python3 /path/to/init-next/scripts/generate.py /absolute/project/path
```

This is the default: copy files, replace the project name and create empty `.env` and `.env.example`. It needs only Python and does not access the network, install tools, initialize Git, start services or run checks. Use `--name lowercase-name` if the directory name is not suitable as a package name.

The template includes the reviewed package versions, pnpm lockfile, version-specific build-script decisions, Action SHAs and Docker digests. Do not run pinact or replace these pins during normal generation. Report that the files were generated from the bundled snapshot, not that they are the latest versions or that the new project was fully verified.

## Prepare when requested

When the user requests installed dependencies and usable local tooling, add:

```sh
python3 /path/to/init-next/scripts/generate.py /absolute/project/path \
  --prepare --cache-dir /absolute/workspace/init-next-cache
```

This additionally initializes Git if needed, runs frozen install, installs pinned aqua tools and registers Lefthook. pnpm, aqua and Git must already be available; executable paths can be supplied with `--pnpm` and `--aqua`. Use an authorized cache directory outside the target and reuse it across projects. Download time remains on the first run. Preserve age/trust/build restrictions; report an install failure rather than weakening them or silently changing versions.

For an already generated project, run the preparation commands from its README with the same cache settings; do not rerun generation over existing files. Do not stage, commit, push, change Rulesets or write outside the authorized workspace unless requested.

## Verify only when requested

Generation and preparation do not imply full verification. When explicitly requested, run:

```sh
python3 /path/to/init-next/scripts/verify.py /absolute/project/path \
  --output /absolute/workspace/verification-results
```

Supply the cache environment used during preparation to reuse downloads. Read the per-run summary and failure logs. `--only checks build dev docker` selects stages after a repair; report only what was checked. Docker and Compose verification starts temporary processes/containers and preserves data volumes. See [verification details](references/verification.md) for stages, cleanup and limitations.

## Implementing features

Generated AGENTS.md links to the bundled implementation rules, and CLAUDE.md references AGENTS.md. Read only the rules relevant to requested implementation work. Merely generating the scaffold does not require reading all standards or adding Prisma, authentication, tables, demo forms or empty architectural layers.

## Maintaining the snapshot

Only when the user requests a template update, follow [refreshing the snapshot](references/setup.md): research current versions, regenerate, review install scripts and run full verification before publishing the updated bundle. [snapshot.json](references/snapshot.json) records the bundled version selection; it is not a claim of current freshness.

In this repository, edit canonical rules under `docs/`, then run `python3 skills/init-next/scripts/sync_standards.py` and its `--check` mode. Keep the bundled AGENTS.md synchronized with `references/agents-append.md`. Consumers use the bundled files without needing this repository.
