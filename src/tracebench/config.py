"""Run configuration: models under test, run counts, budget, seeds.

Every published score must be traceable to a committed config file — model
IDs and params are pinned here, never defaulted inside provider code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from tracebench.models import Usage


class Pricing(BaseModel):
    """USD per million tokens. Pinned in config so cost math is auditable."""

    model_config = ConfigDict(extra="forbid")

    input_per_mtok: float = Field(ge=0)
    output_per_mtok: float = Field(ge=0)


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    provider: str
    model_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    pricing: Pricing


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    tasks: str
    models: list[ModelConfig] = Field(min_length=1)
    runs_per_task: int = Field(default=3, ge=1)
    budget_usd: float = Field(gt=0)
    base_seed: int = 0
    mock_script: str | None = None


def load_run_config(path: str | Path) -> RunConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RunConfig.model_validate(raw)


def compute_cost(usage: Usage, pricing: Pricing) -> float:
    return (
        usage.input_tokens / 1_000_000 * pricing.input_per_mtok
        + usage.output_tokens / 1_000_000 * pricing.output_per_mtok
    )
