"""Pipeline configuration.

Single source of truth for the v5↔v6 orchestration toggles. v6's three
orchestration features (Critic, Clarifier routing, parallel Mapper) are
each gated by a flag here so a v5-equivalent run can be reproduced
under v6 code by passing V5_EQUIVALENT to build_pipeline_graph().

The CLI's `--config v5|v6` flag selects between V5_EQUIVALENT and
V6_CANONICAL. Internal callers should construct PipelineConfig
explicitly when they need a non-canonical combination."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    mapper_concurrency: int = 8
    enable_critic: bool = True
    enable_clarifier_routing: bool = True
    critic_confidence_threshold: float = 0.80
    classifier_low_confidence_threshold: float = 0.70


V5_EQUIVALENT = PipelineConfig(
    mapper_concurrency=1,
    enable_critic=False,
    enable_clarifier_routing=False,
)

V6_CANONICAL = PipelineConfig()

DEFAULT = V6_CANONICAL
