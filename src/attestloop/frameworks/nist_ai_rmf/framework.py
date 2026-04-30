from pathlib import Path

from attestloop.frameworks.nist_ai_rmf.controls import CONTROLS
from attestloop.registry import Framework

FRAMEWORK = Framework(
    id="nist_ai_rmf",
    name="NIST AI Risk Management Framework 1.0",
    controls=CONTROLS,
    mapper_prompt_path=Path(__file__).parent / "mapper.md",
)
