"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Button, PasswordInput, Stack, TextInput } from "@mantine/core";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Controller, useForm } from "react-hook-form";
import type { z } from "zod";
import { authClient } from "@/auth/client";
import { createFormSchema } from "../_helpers/form-schema";

export function AuthForm() {
  const translate = useTranslations();
  const router = useRouter();

  const schema = createFormSchema({
    invalidEmail: translate("validation.invalidEmail"),
    required: translate("validation.required"),
  });
  const form = useForm<
    z.input<typeof schema>,
    unknown,
    z.output<typeof schema>
  >({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  return (
    <form
      noValidate
      onSubmit={form.handleSubmit(async (values) => {
        form.clearErrors("root");
        try {
          const result = await authClient.signIn.email(values);
          if (result.error != null) {
            form.setError("root", {
              message: translate("pages.signIn.failed"),
            });
            return;
          }
          router.replace("/");
          router.refresh();
        } catch {
          form.setError("root", {
            message: translate("pages.signIn.failed"),
          });
        }
      })}
    >
      <Stack>
        <Controller
          control={form.control}
          name="email"
          render={({ field, fieldState }) => (
            <TextInput
              {...field}
              type="email"
              label={translate("models.user.email")}
              autoComplete="email"
              error={fieldState.error?.message}
            />
          )}
        />
        <Controller
          control={form.control}
          name="password"
          render={({ field, fieldState }) => (
            <PasswordInput
              {...field}
              label={translate("models.user.password")}
              autoComplete="current-password"
              error={fieldState.error?.message}
            />
          )}
        />

        {form.formState.errors.root?.message && (
          <Alert role="alert" color="red">
            {form.formState.errors.root.message}
          </Alert>
        )}
        <Button type="submit" loading={form.formState.isSubmitting}>
          {translate("pages.signIn.submit")}
        </Button>
      </Stack>
    </form>
  );
}
