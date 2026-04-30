"""Run-directory helpers. Pulled out of pipeline.py so orchestration nodes
can construct a run_dir without importing the CLI entrypoint."""
from datetime import datetime, timezone
from pathlib import Path

# Assumption: runs/ lives at the repo root next to src/ and tests/. The
# package itself is under src/attestloop/, so resolving up three parents
# lands at the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = _REPO_ROOT / "runs"


def create_run_dir() -> tuple[str, datetime, Path]:
    """Mint a fresh run directory under runs/<YYYYMMDD-HHMMSS>/.

    Returns (run_id, started_at, run_dir). Both run_id and started_at are
    stored on PipelineState so the report builder has a stable identifier
    and timestamp that survive across the orchestration graph.
    """
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_id, started_at, run_dir
