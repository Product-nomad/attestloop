// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://attestloop.ai",
  output: "static",
  // Keep emitted HTML readable: matters for the pipeline-diagram grep
  // checks (each agent box on its own line) and for any human eyeballing
  // dist/index.html. The size cost is ~5 KB on this site.
  compressHTML: false,
  integrations: [sitemap()],
  vite: {
    plugins: [tailwindcss()],
  },
});
