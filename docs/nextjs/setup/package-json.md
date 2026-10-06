# Next.jsのpackage.json設定

[create-next-appの生成結果](create-next-app.md)に、[package.jsonの共通方針](../../base/package-json.md)と実行コマンドを反映する。

```json
{
  "name": "my-app",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@12.0.0",
  "devEngines": {
    "runtime": {
      "name": "node",
      "version": "^24.4.0",
      "onFail": "download"
    }
  },
  "scripts": {
    "dev": "pnpm run db:generate && next dev",
    "build": "pnpm run db:generate && next build",
    "start": "next start",
    "typecheck": "pnpm run db:generate && next typegen && tsc --noEmit",
    "lint": "biome check --error-on-warnings .",
    "lint:fix": "biome check --write --error-on-warnings .",
    "test": "vitest run",
    "test:watch": "vitest",
    "db:generate": "prisma generate",
    "db:migrate": "prisma migrate dev --create-only",
    "db:deploy": "prisma migrate deploy",
    "auth:generate": "auth generate --config ./auth.schema.config.ts --adapter prisma --dialect postgresql",
    "auth:create-admin": "auth create-admin --config ./auth.admin.config.ts"
  }
}
```

依存欄を除いた設定例。バージョン番号は共通方針の書式例であり、導入時に採用する版へ置き換える。
生成された`dependencies`・`devDependencies`は残し、インストール前にバージョンを調整する。

## 生成設定からの変更

| 項目 | 生成時 | 方針・理由 |
| --- | --- | --- |
| `name` | ディレクトリ名 | 維持する |
| `version` | `"0.1.0"` | publishせず、アプリのバージョン管理にも使わない構成なので削除する |
| `private` | `true` | 維持し、誤ったpublishを防ぐ |
| `type` | なし | `"module"`を追加し、設定ファイルやスクリプトもESMに揃える |
| `packageManager` | 生成時に使ったpnpmの版 | 採用するpnpmの完全バージョンに揃える |
| `devEngines.runtime` | なし | 使用するNode.jsを指定し、pnpmで取得・管理する |
| 依存バージョン | 完全固定と範囲指定が混在 | 待機期間と互換性を確認した版に完全固定する |

`type: "module"`はNext.jsを動かすための必須項目ではないが、プロジェクトのモジュール方式を明示するため採用する。
Next.jsもESMの`next.config.ts`に対応している。CommonJSが必要な設定ファイルは`.cjs`などで区別する。

`packageManager`・`devEngines.runtime`の役割や、`engines`などを省略する理由は[共通方針](../../base/package-json.md)に従う。
本番環境でpnpmを経由しない場合、Node.jsの版は本番側でも揃える。

## scripts

| 項目 | 生成時からの変更・理由 |
| --- | --- |
| `dev` | 生成時の`next dev`の前にPrisma Clientを生成する。変更を反映する開発サーバーを起動する |
| `build` | 生成時の`next build`の前にPrisma Clientを生成する。本番向けにビルドする |
| `start` | 通常のビルドでは`next start`で本番モードを起動する。[Dockerのstandalone構成](docker.md)では、DockerfileのCMDで`node server.js`を直接実行する |
| `typecheck` | 追加する。Prisma ClientとNext.jsの型を生成してから、ビルドせず型チェックする |
| `lint` | 生成時の`biome check`に`--error-on-warnings .`を加え、警告も失敗扱いにする |
| `lint:fix` | 生成時の`format: "biome format --write"`を置き換える。整形・import整理・安全なLint修正をまとめて適用する |
| `db:*` | 追加する。Prisma Clientの生成、マイグレーションSQLの作成、作成済みSQLの適用を分ける |
| `auth:*` | 追加する。認証用schemaの生成と初期管理者の作成で、用途別のCLI設定を指定する |

型生成と型チェックの詳細は[Next.jsのTypeScript設定](typescript.md#実行コマンド)、Biomeの設定とコマンドは[Next.jsのBiome設定](biome.md)を参照。
`test`・`test:watch`は[Next.jsのVitest設定](vitest.md)と併せて追加する。Next.jsでもNode.js上のユニットテストには共通設定を使う。
`db:*`の使い分けと、起動・型チェック・ビルドの前に生成する理由は[Prismaの生成とマイグレーション](prisma.md#生成とマイグレーション)を参照。
`auth:*`が使う設定ファイルは[Better Authの配置](better-auth.md#依存と配置)を参照。

## 依存バージョンの調整

[公開後の待機期間・信頼性検証](../../base/pnpm-workspace.md)を適用し、互換性のある最新安定版を確認して完全固定する。
Next.js・React・React DOMの対応を確認し、ReactとReact DOMは同じ版に揃える。
`@types/node`は実行するNode.js、React向けの型はReactのメジャーに合わせる。

TypeScriptは[Next.js側の対応](typescript.md#typescriptと型パッケージの版)も確認する。
Biomeを更新したら`biome.json`の`$schema`も揃える。
[Mantine・Tabler IconsとPostCSS](mantine.md)、[next-intl](i18n.md)、[環境変数検証のZod](env.md)、[Prisma](prisma.md)、[Better Auth](better-auth.md)も各文書に従って追加する。
依存の解決結果は`pnpm-lock.yaml`で共有する。

## 参考

- [create-next-app：package.jsonの生成処理](https://github.com/vercel/next.js/blob/v16.3.8/packages/create-next-app/templates/index.ts)
- [Next.js：ESMの設定ファイル](https://nextjs.org/docs/app/api-reference/config/typescript#for-esm-projects)
- [Next.js：実行コマンド](https://nextjs.org/docs/app/api-reference/cli/next)
