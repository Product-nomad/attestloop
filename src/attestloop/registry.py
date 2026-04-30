from importlib import import_module
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from attestloop.schemas import Control


class Regulation(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str
    name: str
    jurisdiction: str
    classifier_prompt_path: Path
    extractor_prompt_path: Path


class Framework(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str
    name: str
    controls: list[Control]
    mapper_prompt_path: Path
    critic_prompt_path: Path


def get_regulation(regulation_id: str) -> Regulation:
    module = import_module(f"attestloop.regulations.{regulation_id}.regulation")
    return module.REGULATION


def get_framework(framework_id: str) -> Framework:
    module = import_module(f"attestloop.frameworks.{framework_id}.framework")
    return module.FRAMEWORK
