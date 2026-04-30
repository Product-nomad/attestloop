from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Publication(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    title: str | None
    raw_html: str
    cleaned_text: str
    fetched_at: datetime


class ClassifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publication: Publication
    regulation_id: str


class ClassifierOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    in_scope: bool
    category: Literal["regulation", "guideline", "amendment", "press_release", "other"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class Obligation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_paragraph: str
    requirement_text: str
    scope: str
    deadline: str | None
    evidence_required: str | None


class ExtractorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publication: Publication
    regulation_id: str


class ExtractorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    obligations: list[Obligation]


class Control(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    function: str
    category: str
    subcategory_text: str


class ControlMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    obligation_id: str
    control_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ClarifierOutput(BaseModel):
    """Output of the Clarifier agent: additional context fetched from the
    publication plus the Classifier's re-classification on the augmented
    input. The initial_classification field is preserved here so the
    audit trail in clarifier.json is self-describing without having to
    cross-reference the Classifier's per-call log."""

    model_config = ConfigDict(extra="forbid")

    initial_classification: "ClassifierOutput"
    additional_context: str
    context_source: Literal[
        "table_of_contents",
        "first_5_pages",
        "section_headings",
    ]
    reclassification: "ClassifierOutput"


class CriticDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    obligation_id: str
    decision: Literal["confirm", "flag_for_review"]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    reviewed_mappings: list[str]


class CriticOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decisions: list[CriticDecision]


class MapperInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    obligations: list[Obligation]
    controls: list[Control]
    framework_id: str


class MapperOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mappings: list[ControlMapping]


class RunMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    started_at: datetime
    regulation_id: str
    framework_id: str
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int


class LLMCallLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: str
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    started_at: datetime
    prompt: str
    response: str
    metadata: dict[str, int | float | str] | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
