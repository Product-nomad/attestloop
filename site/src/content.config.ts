import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

// Schemas mirror the Pydantic models in src/attestloop/schemas.py.
// Keep them strict so accidental shape drift from the pipeline-side
// snapshot fails the build, not silently corrupts the page.

const runMetadataSchema = z.object({
  run_id: z.string(),
  started_at: z.string(),
  regulation_id: z.string(),
  framework_id: z.string(),
  total_cost_usd: z.number(),
  total_input_tokens: z.number(),
  total_output_tokens: z.number(),
});

export const obligationSchema = z.object({
  id: z.string(),
  source_paragraph: z.string(),
  requirement_text: z.string(),
  scope: z.string(),
  deadline: z.string().nullable(),
  evidence_required: z.string().nullable(),
});

export const controlMappingSchema = z.object({
  obligation_id: z.string(),
  control_id: z.string(),
  confidence: z.number().min(0).max(1),
  reasoning: z.string(),
});

export const evolutionRowSchema = z.object({
  version: z.string(),
  approach: z.string(),
  obligations: z.number().int().nonnegative(),
  mappings: z.number().int().nonnegative(),
  unmapped: z.number().int().nonnegative(),
  cost_usd: z.number(),
  runtime_seconds: z.number().int().nonnegative(),
});

const runs = defineCollection({
  loader: glob({
    pattern: "*_run_metadata.json",
    base: "./src/content/runs",
  }),
  schema: runMetadataSchema,
});

const writeup = defineCollection({
  loader: glob({
    pattern: "*.md",
    base: "./src/content/writeup",
  }),
  schema: z.object({
    section: z.number().optional(),
    title: z.string().optional(),
    subtitle: z.string().optional(),
    status: z.string().optional(),
    not_published: z.boolean().optional(),
    // YAML interprets bare YYYY-MM-DD as a Date; coerce to string so
    // either form (quoted string or unquoted date) round-trips cleanly.
    updated: z.coerce.string().optional(),
  }),
});

export const obligationsFileSchema = z.object({
  obligations: z.array(obligationSchema),
});

export const mappingsFileSchema = z.object({
  mappings: z.array(controlMappingSchema),
});

export const collections = { runs, writeup };
