# Attestloop site

The marketing / landing site for [Attestloop](../). Built with
[Astro 5](https://astro.build/) and [Tailwind CSS 4](https://tailwindcss.com/);
deployed to [Cloudflare Pages](https://pages.cloudflare.com/) as a static
build out of `site/dist/`.

This is part of the same git repository as the pipeline (`../src/attestloop/`),
the architectural decision records (`../docs/adr/`), and the canonical run
snapshot (`../docs/example_runs/v6_clean/`). The site uses pnpm; the
pipeline uses uv. They do not share dependencies.

## Local development

```bash
cd site
pnpm install
pnpm dev          # http://localhost:4321
```

## Build

```bash
pnpm build        # writes static output to site/dist/
pnpm check        # astro check, type-checks .astro and .ts files
pnpm preview      # serve the production build locally
```

## Deploy

Cloudflare Pages picks up `site/dist/` after each push to `main`.
Configuration in [`wrangler.toml`](./wrangler.toml). Security and redirect
behaviour in [`public/_headers`](./public/_headers) and
[`public/_redirects`](./public/_redirects) — both are copied verbatim into
the built output by Astro.

## Reading the rest of the project from here

- **Pipeline source:** [`../src/attestloop/`](../src/attestloop/)
- **Architectural decisions:** [`../docs/adr/`](../docs/adr/)
- **Canonical v6 run:** [`../docs/example_runs/v6_clean/`](../docs/example_runs/v6_clean/)
- **v5-equivalent baseline:** [`../docs/example_runs/v6_v5_equivalent_clean/`](../docs/example_runs/v6_v5_equivalent_clean/)
- **Pipeline Mermaid source:** [`../docs/orchestration/v6_pipeline.mmd`](../docs/orchestration/v6_pipeline.mmd) (regenerates from the compiled LangGraph)
- **Threat model:** [`../THREAT_MODEL.md`](../THREAT_MODEL.md)
- **Domain language:** [`../CONTEXT.md`](../CONTEXT.md)

## Tone

Charcoal-and-paper palette, serif headings, mono accents. The aesthetic
is deliberate — quiet, regulated-industry default, no visual noise.
Tokens are in [`src/styles/global.css`](./src/styles/global.css) under
the `@theme` block.
