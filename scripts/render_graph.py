"""Render the v6 pipeline graph to disk for the writeup and the site.

Writes Mermaid source to docs/orchestration/v6_pipeline.mmd unconditionally
(no extra deps, deterministic), and attempts a PNG export via Mermaid Ink
(LangGraph's draw_mermaid_png default backend) — which requires network
access and falls back to skipping if it isn't available.

Run with: uv run python scripts/render_graph.py
"""
from pathlib import Path

from attestloop.orchestration import build_pipeline_graph

OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "orchestration"
OUT_DIR.mkdir(parents=True, exist_ok=True)

graph = build_pipeline_graph().get_graph()

mmd_path = OUT_DIR / "v6_pipeline.mmd"
mmd_path.write_text(graph.draw_mermaid())
print(f"wrote {mmd_path}")

png_path = OUT_DIR / "v6_pipeline.png"
try:
    png_bytes = graph.draw_mermaid_png()
except Exception as e:  # noqa: BLE001 — Mermaid Ink network failures are varied
    print(f"skipping PNG export ({e!r}); .mmd source is sufficient for the site.")
else:
    png_path.write_bytes(png_bytes)
    print(f"wrote {png_path}")
