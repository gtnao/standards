FROM node:24.21.0-trixie-slim@sha256:8ec5d7557396cfe32d21c3f9c13072355ceab22b584578ca4bb28af31120cffe AS base
WORKDIR /app

FROM base AS install-base
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN corepack enable pnpm && pnpm --version

FROM install-base AS build
RUN --mount=type=cache,id=my-app-pnpm,target=/pnpm/store,sharing=locked \
    pnpm install --store-dir=/pnpm/store --frozen-lockfile
RUN test "$(pnpm exec node --version)" = "$(/usr/local/bin/node --version)"
COPY . .
RUN mkdir -p public && pnpm run build

FROM base AS runtime
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
COPY --from=build /app/.next/standalone ./
RUN mkdir -p .next/cache && chown -R node:node .next
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
