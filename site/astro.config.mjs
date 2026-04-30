// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://attestloop.ai",
  output: "static",
  vite: {
    plugins: [tailwindcss()],
  },
});
