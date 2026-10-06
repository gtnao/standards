import { z } from "zod";

type FormMessages = {
  invalidEmail: string;
  required: string;
};

export function createFormSchema(messages: FormMessages) {
  return z.object({
    email: z.email(messages.invalidEmail),
    // Sign-in only checks presence: showing the password policy here would
    // disclose it, and the server decides whether the credentials are valid.
    password: z.string().min(1, messages.required),
  });
}
