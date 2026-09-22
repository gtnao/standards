import { defineCommand, runMain } from "citty";

runMain(
  defineCommand({
    meta: { name: "__PROJECT_NAME__" },
    subCommands: {
      greet: () => import("./greet.js").then((m) => m.default),
    },
  }),
);
