import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const runs = defineCollection({
  loader: glob({ pattern: "**/*.json", base: "./src/content/runs" }),
  schema: z.object({
    run_id: z.string(),
    started_at: z.string(),
    regulation_id: z.string(),
    framework_id: z.string(),
    total_cost_usd: z.number(),
    total_input_tokens: z.number(),
    total_output_tokens: z.number(),
  }),
});

export const collections = { runs };
