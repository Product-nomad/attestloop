from pathlib import Path

from attestloop.registry import Regulation

REGULATION = Regulation(
    id="eu_ai_act",
    name="EU Artificial Intelligence Act (Regulation 2024/1689)",
    jurisdiction="EU",
    classifier_prompt_path=Path(__file__).parent / "classifier.md",
    extractor_prompt_path=Path(__file__).parent / "extractor.md",
)
