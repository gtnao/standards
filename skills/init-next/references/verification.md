# Scaffold verification

Run full verification when requested or before publishing a refreshed template.

Keep the output outside the generated project, inside the authorized workspace. Use `--pnpm /absolute/path/to/pnpm` if needed. Tool configuration and storage locations are inherited from the invoking environment.

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

