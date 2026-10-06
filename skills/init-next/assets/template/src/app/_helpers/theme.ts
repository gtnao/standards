import type { MantineThemeOverride } from "@mantine/core";

export const theme: MantineThemeOverride = {
  primaryColor: "indigo",
  defaultRadius: "md",
  headings: {
    fontWeight: "600",
    sizes: {
      h1: { fontSize: "1.5rem", lineHeight: "1.4" },
      h2: { fontSize: "1.25rem", lineHeight: "1.4" },
      h3: { fontSize: "1.125rem", lineHeight: "1.4" },
    },
  },
};
