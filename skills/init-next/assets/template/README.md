# __PROJECT_NAME__

```sh
git init -b main
pnpm install --frozen-lockfile
aqua install
aqua exec -- lefthook install
```

Start PostgreSQL, apply the migrations and create the first administrator. The password is entered interactively.

```sh
docker compose up -d --wait
pnpm run db:deploy
pnpm run auth:create-admin \
  --email admin@example.com \
  --name "Admin" \
  --role admin \
  --no-email-verified
pnpm dev
```

Add local environment values to `.env` and document their names in `.env.example`.
`DATABASE_URL` points at the Compose PostgreSQL; update it together with `POSTGRES_PORT`.
`BETTER_AUTH_SECRET` needs at least 32 characters, for example from `openssl rand -base64 32`.

After changing `prisma/schema.prisma`, create the migration SQL, review it, then apply it. Restart `pnpm dev` after the Prisma client is regenerated.

```sh
pnpm run db:migrate --name <name>
pnpm run db:deploy
```

```sh
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run build
```

Pass `DATABASE_URL`, `BETTER_AUTH_URL` and `BETTER_AUTH_SECRET` to the container at run time.

```sh
docker build -t __PROJECT_NAME__ .
docker run --rm --init -p 127.0.0.1:3000:3000 __PROJECT_NAME__
```
