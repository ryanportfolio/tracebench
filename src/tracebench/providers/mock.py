"""Mock provider: deterministic, zero-cost-API stand-in for dry runs and tests.

Responses come from an optional script file (YAML mapping task id -> response).
Unscripted tasks get a deterministic placeholder. Token usage is derived from
character counts so cost accounting and budget enforcement are exercised for
real even in dry runs.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from tracebench.config import ModelConfig, RunConfig
from tracebench.models import ProviderResult, Task, ToolCall, Usage
from tracebench.providers import Provider


class MockResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    tool_calls: list[ToolCall] = Field(default_factory=list)


class MockScript(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: dict[str, MockResponse] = Field(default_factory=dict)


def _approx_tokens(text: str) -> int:
    # Crude 4-chars-per-token heuristic; only needs to be deterministic.
    return max(1, len(text) // 4)


class MockProvider(Provider):
    name = "mock"

    def __init__(self, script: MockScript | None = None) -> None:
        self.script = script or MockScript()

    @classmethod
    def from_run_config(cls, run_cfg: RunConfig) -> MockProvider:
        if run_cfg.mock_script is None:
            return cls()
        raw = yaml.safe_load(Path(run_cfg.mock_script).read_text(encoding="utf-8"))
        return cls(MockScript.model_validate(raw))

    def complete(self, task: Task, model_cfg: ModelConfig, seed: int) -> ProviderResult:
        scripted = self.script.tasks.get(task.id)
        if scripted is not None:
            text = scripted.text
            tool_calls = scripted.tool_calls
        else:
            text = f"[mock:{model_cfg.model_id} seed={seed}] no scripted response for {task.id}"
            tool_calls = []
        input_tokens = sum(_approx_tokens(m.content) for m in task.messages)
        return ProviderResult(
            text=text,
            tool_calls=tool_calls,
            usage=Usage(input_tokens=input_tokens, output_tokens=_approx_tokens(text)),
        )
