v5-equivalent run executed under v6 code with the orchestration
features (Critic, Clarifier, parallel Mapper) disabled via
`PipelineConfig.V5_EQUIVALENT`. Provided as a like-for-like baseline
against the canonical v6 run at [`v6_clean/`](../v6_clean/), so the
v5→v6 comparison isolates the orchestration delta from any other
v5→v6 code changes (file naming convention, classifier output
structure, etc.).

The historical v5 snapshot at [`v5_clean/`](../v5_clean/) remains the
canonical "v5" reference; this directory is the v5 *configuration*
running on the v6 *codebase*, not a re-run of v5.

Reproduce with:

```bash
uv run python -m attestloop \
    --url https://ec.europa.eu/newsroom/dae/redirection/document/112367 \
    --regulation eu_ai_act \
    --framework nist_ai_rmf \
    --config v5
```
