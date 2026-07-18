"""Core data models: tasks, provider results, transcripts, grades.

Every task file on disk validates against `Task`. Extra fields are rejected
everywhere (`extra="forbid"`) so schema drift fails loudly instead of being
silently ignored — a grader reading a field that was never validated is how
false claims about model behavior happen.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskFamily(StrEnum):
    DISCUSSIONS = "discussions"
    TOOL_USE = "tool_use"
    LONG_HORIZON = "long_horizon"


class Provenance(BaseModel):
    """Where a task came from. Every task must tell this story.

    `source_type` is the privacy rail: "public" means the material is verbatim
    from a public source (public discussion thread, public repo);
    "synthetic_reconstruction" means a private-workflow failure inspired the
    task and it was rebuilt with public or synthetic material. Nothing from
    private repos ships, ever.
    """

    model_config = ConfigDict(extra="forbid")

    source_workflow: str
    source_type: Literal["public", "synthetic_reconstruction"]
    note: str


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ToolSpec(BaseModel):
    """JSON-schema tool definition offered to the model under test."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)


class Check(BaseModel):
    """One grading check. `type` selects a registered grader function."""

    model_config = ConfigDict(extra="forbid")

    type: str
    params: dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, gt=0)


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    family: TaskFamily
    title: str
    provenance: Provenance
    messages: list[Message] = Field(min_length=1)
    tools: list[ToolSpec] = Field(default_factory=list)
    checks: list[Check] = Field(min_length=1)
    max_turns: int = 1


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Usage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0


class ProviderResult(BaseModel):
    """What came back from one model call: text, tool calls, token usage."""

    model_config = ConfigDict(extra="forbid")

    text: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    passed: bool
    weight: float
    detail: str = ""


class Transcript(BaseModel):
    """One graded run of one task against one model. The unit of publication.

    Designed to be reusable downstream as a training-data filter: it carries
    the full input, the full output, per-check grades, and an overall score.
    """

    model_config = ConfigDict(extra="forbid")

    task_id: str
    family: TaskFamily
    provider: str
    model_id: str
    provider_version: str = ""
    run_index: int
    seed: int
    input_messages: list[Message]
    output_text: str
    tool_calls: list[ToolCall]
    usage: Usage
    cost_usd: float
    checks: list[CheckResult]
    score: float
