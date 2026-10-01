# Directory structure

Keep page-specific code near the page and separate application workflows from external services.
Create directories when they have an implementation; do not generate empty layers.

| Location | Responsibility |
| --- | --- |
| `src/app` | Pages, layouts, Route Handlers and application entrypoints |
| Nearest `_components/` | Components used by that page or subtree |
| Nearest `_helpers/` | Server Actions, form schemas and presentation transformations for that subtree |
| `src/components` | React components shared across the application |
| `src/env` | Application environment validation; separate server and public values |
| `src/i18n` | Translation configuration and type augmentation |
| `src/usecases` | Workflows that accomplish an application purpose |
| `src/domain` | Application concepts, rules, types and operations |
| `src/ports` | Contracts for external capabilities consumed by usecases |
| `src/adapters` | Concrete implementations of ports |
| `src/lib` | Reusable utilities without application-specific meaning |

Move shared page code to the nearest common ancestor. `_helpers` contains application-specific presentation and entrypoint code; it is not another name for `src/lib`.
Private folders exclude routes, not imports. Keep server-only implementations separate from shared schemas and client code.

## Dependencies

| Importing layer | Allowed layers |
| --- | --- |
| Entrypoints | usecases, adapters, ports, domain, lib |
| usecases | ports, domain, lib |
| adapters | ports, domain, lib |
| ports | domain, lib |
| domain | lib |
| lib | No other application layers |

Same-layer imports are permitted when needed; avoid cycles. Components and Next.js-specific code stay outside the lower layers. Shared components must not import a particular page's internal helpers; receive values and callbacks as props.

Usecases are functions named for an action. Define a local `Args` type with `deps` and `input`; export it only if consumers need it. Return values and leave UI, environment access and Next.js control flow to the entrypoint.
Adapters use `createXxx(config)` factories and explicitly return the port type. Ports primarily allow controlled external behavior in usecase tests, while retaining the option to replace implementations. Choose abstraction and naming according to the contract's purpose; do not force every vendor-specific capability into a generic repository abstraction.

Domain contents depend on the application. Do not impose entities or aggregates merely to resemble DDD. Keep business rules out of entrypoints and adapters.
Do not grow `lib` as a miscellaneous folder: first keep a helper with its caller and extract only when its responsibility is clear.
Subdivide layers when their size and responsibilities justify it; preserve dependency direction.

Pages and layouts remain Server Components by default. Add Client boundaries where hooks, events or browser APIs are needed. Add `server-only` to server-only modules; `"use server"` is for Server Functions.
