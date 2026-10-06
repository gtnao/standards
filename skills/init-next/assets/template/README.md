# __PROJECT_NAME__

```sh
git init -b main
pnpm install --frozen-lockfile
aqua install
aqua exec -- lefthook install
docker compose up -d --wait
pnpm dev
```

Add local environment values to `.env` and document their names in `.env.example`.

```sh
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run build
```

```sh
docker build -t __PROJECT_NAME__ .
docker run --rm --init -p 127.0.0.1:3000:3000 __PROJECT_NAME__
```
