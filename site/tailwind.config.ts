import type { Config } from "tailwindcss";

// Tailwind v4 reads its theme tokens from the `@theme` block in
// `src/styles/global.css`. This file exists so editors and tooling can
// pick up content paths and so a future migration back to a JS-defined
// theme is a one-file change. Add tokens here only if a tool needs them.
export default {
  content: ["./src/**/*.{astro,html,ts,tsx,md,mdx}"],
} satisfies Config;
