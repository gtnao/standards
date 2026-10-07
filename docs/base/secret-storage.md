# 秘匿情報の保存

外部サービスのAPIキーなど、アプリが預かる秘匿情報は暗号化してDBに保存する。
暗号化はportで切り離し、本番ではAWS KMS、ローカルではNode.jsの`crypto`による実装を使う。
同じportの実装が複数あるため、adapterは`src/adapters/secret-cipher/`にまとめて実装ごとのファイルに分ける。

## 保存する形

暗号化した値は、復号に必要な情報をまとめて1つのJSONカラムに入れる。カラム名には`_enc`の接尾辞を付ける（例：`api_key_enc`）。
秘匿情報が複数あれば、その数だけ`_enc`カラムを作る。暗号文・IV・認証タグを別カラムに分けない。

```json
{ "scheme": "aws-kms", "keyId": "arn:aws:kms:...", "ciphertext": "..." }
{ "scheme": "aes-256-gcm", "keyId": "local", "iv": "...", "ciphertext": "...", "authTag": "..." }
```

`scheme`で実装を識別し、`keyId`で暗号化に使った鍵を記録する。鍵を切り替えたあとも古い値を復号できる。
[Prismaの命名](../nextjs/implementation/prisma.md#種別と種別ごとのテーブル)に従い、Prismaでは`Json`型のフィールドにする。読み出した値は`encryptedSecretSchema`で検証してから復号する。

## port

`src/ports/secret-cipher.ts`：

```ts
import { z } from "zod";

// Everything needed to decrypt is stored together in one JSON column (`*_enc`).
// `keyId` lets a later key rotation decrypt values written under the old key.
export const encryptedSecretSchema = z.discriminatedUnion("scheme", [
  z.object({
    scheme: z.literal("aws-kms"),
    keyId: z.string().min(1),
    ciphertext: z.string().min(1),
  }),
  z.object({
    scheme: z.literal("aes-256-gcm"),
    keyId: z.string().min(1),
    iv: z.string().min(1),
    ciphertext: z.string().min(1),
    authTag: z.string().min(1),
  }),
]);

export type EncryptedSecret = z.output<typeof encryptedSecretSchema>;

export interface SecretCipher {
  encrypt(plaintext: string): Promise<EncryptedSecret>;
  decrypt(secret: EncryptedSecret): Promise<string>;
}
```

JSONの形はportが決める。保存される形なので、adapterの都合で変えない。
平文は`string`に限る。バイナリや巨大なデータは対象にしない。

## 本番：AWS KMS

`src/adapters/secret-cipher/kms.ts`：

```ts
import { DecryptCommand, EncryptCommand, KMSClient } from "@aws-sdk/client-kms";
import { fromNodeProviderChain } from "@aws-sdk/credential-providers";
import type { EncryptedSecret, SecretCipher } from "@/ports/secret-cipher";

type Config = {
  region: string;
  keyId: string;
  profile?: string;
};

// Secrets are short, so they go straight through KMS Encrypt (4 KiB limit)
// instead of envelope encryption with a data key.
export function createKmsSecretCipher(config: Config): SecretCipher {
  const client = new KMSClient({
    region: config.region,
    credentials: fromNodeProviderChain(
      config.profile != null ? { profile: config.profile } : {},
    ),
  });

  return {
    async encrypt(plaintext) {
      const response = await client.send(
        new EncryptCommand({
          KeyId: config.keyId,
          Plaintext: Buffer.from(plaintext, "utf8"),
        }),
      );
      if (response.CiphertextBlob == null) {
        throw new Error("KMS returned no ciphertext");
      }
      return {
        scheme: "aws-kms",
        keyId: response.KeyId ?? config.keyId,
        ciphertext: Buffer.from(response.CiphertextBlob).toString("base64"),
      };
    },

    async decrypt(secret: EncryptedSecret) {
      if (secret.scheme !== "aws-kms") {
        throw new Error(`Cannot decrypt a ${secret.scheme} secret with KMS`);
      }
      const response = await client.send(
        new DecryptCommand({
          KeyId: secret.keyId,
          CiphertextBlob: Buffer.from(secret.ciphertext, "base64"),
        }),
      );
      if (response.Plaintext == null) {
        throw new Error("KMS returned no plaintext");
      }
      return Buffer.from(response.Plaintext).toString("utf8");
    },
  };
}
```

秘匿情報は短いため、データキーを使うエンベロープ暗号化ではなく、KMSの`Encrypt`・`Decrypt`に直接渡す（平文は4KiBまで）。
認証は[Bedrockと同じ](ai-sdk.md#環境変数と認証)く、本番はIAM Role、ローカルで試す場合はAWS Profileを使う。IAM Roleには対象の鍵への`kms:Encrypt`・`kms:Decrypt`だけを許可する。

```sh
pnpm add -E @aws-sdk/client-kms@3.1143.0 @aws-sdk/credential-providers@3.1143.0
```

2026年10月7日の確認では、上記が待機期間・信頼性検証を通る最新版。`@aws-sdk/*`は同じ版に揃える。

## ローカル：Node.jsのcrypto

`src/adapters/secret-cipher/local.ts`：

```ts
import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
import type { EncryptedSecret, SecretCipher } from "@/ports/secret-cipher";

type Config = {
  // 32 bytes encoded as base64, for example from `openssl rand -base64 32`.
  key: string;
};

const keyId = "local";

// Development stand-in for KMS. The key lives in .env and never leaves the machine.
export function createLocalSecretCipher(config: Config): SecretCipher {
  const key = Buffer.from(config.key, "base64");
  if (key.length !== 32) {
    throw new Error("The local secret key must be 32 bytes in base64");
  }

  return {
    async encrypt(plaintext) {
      const iv = randomBytes(12);
      const cipher = createCipheriv("aes-256-gcm", key, iv);
      const ciphertext = Buffer.concat([
        cipher.update(plaintext, "utf8"),
        cipher.final(),
      ]);
      return {
        scheme: "aes-256-gcm",
        keyId,
        iv: iv.toString("base64"),
        ciphertext: ciphertext.toString("base64"),
        authTag: cipher.getAuthTag().toString("base64"),
      };
    },

    async decrypt(secret: EncryptedSecret) {
      if (secret.scheme !== "aes-256-gcm") {
        throw new Error(
          `Cannot decrypt a ${secret.scheme} secret with the local cipher`,
        );
      }
      const decipher = createDecipheriv(
        "aes-256-gcm",
        key,
        Buffer.from(secret.iv, "base64"),
      );
      decipher.setAuthTag(Buffer.from(secret.authTag, "base64"));
      return Buffer.concat([
        decipher.update(Buffer.from(secret.ciphertext, "base64")),
        decipher.final(),
      ]).toString("utf8");
    },
  };
}
```

AES-256-GCMで、値ごとにIVを生成する。鍵は`openssl rand -base64 32`で作り、`.env`に置く。
この実装は本番で使わない。本番の環境変数に鍵を配らず、KMSの実装だけを組み立てる。

## 使い方

- 書き込むusecaseで`encrypt`し、戻り値をそのまま`_enc`カラムへ保存する。
- 使うusecaseで、必要になった時点で`decrypt`する。復号した値を画面・ログ・エラーメッセージへ出さない。
- 復号した値はその処理の中だけで使い、DB・キャッシュ・セッションへ保存しない。
- どちらの実装を使うかは[環境変数](env.md)で入口が決め、usecaseには`SecretCipher`だけを渡す。

## 参考

- [AWS KMS：Encrypt](https://docs.aws.amazon.com/kms/latest/APIReference/API_Encrypt.html)
- [AWS KMS：Decrypt](https://docs.aws.amazon.com/kms/latest/APIReference/API_Decrypt.html)
- [Node.js：crypto](https://nodejs.org/api/crypto.html)
