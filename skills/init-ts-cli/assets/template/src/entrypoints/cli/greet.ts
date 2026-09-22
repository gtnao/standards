import { defineCommand } from "citty";

export default defineCommand({
  meta: { description: "Print a greeting" },
  args: {
    name: { type: "string", default: "world", description: "Name to greet" },
  },
  run: ({ args }) => {
    console.log(`Hello, ${args.name}!`);
  },
});
