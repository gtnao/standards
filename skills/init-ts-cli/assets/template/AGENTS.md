# Development guidelines

Before making changes, read and follow:

- [Directory structure](docs/directory-structure.md)
- [Coding guidelines](docs/coding-guidelines.md)

## Tooling

- Use pnpm for package management and project scripts.
- Use the Node.js and pnpm versions configured in `package.json`.
- Run tools managed by aqua through `aqua exec --`.
- Use citty for CLI commands and Zod for environment variable validation.
- Write relative TypeScript imports with the output `.js` extension.

## Dependencies

- Prefer built-in APIs and existing dependencies before adding packages.
- Preserve the restrictions in `pnpm-workspace.yaml`.
- Review dependency install scripts before allowing them.

## Environment

- Keep local configuration in `.env` and update `.env.example` when adding variables.
- Read, validate, and convert application environment variables with Zod at the entrypoint boundary. Pass validated values to the code that needs them.
- Define variables for actual requirements; do not add sample variables just to use Zod.
- Never commit secrets.

## Testing

- Place unit tests beside the code as `*.test.ts`, and test-only helpers in `__tests__/`.
- Import test APIs from Vitest explicitly.
- Keep production code independent of test code. When adding import aliases, extend the restricted import patterns to cover aliases pointing to test code.
- Keep project-wide type checking separate from the production build in `tsconfig.build.json`.

## Validation

After changing code or configuration, run:

```sh
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run build
```

When changing CLI behavior or build configuration, also verify the affected command with tsx and the compiled JavaScript.
Add or update tests when needed to cover behavioral changes.
