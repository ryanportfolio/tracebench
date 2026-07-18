from __future__ import annotations

import pytest

from tracebench.models import (
    Check,
    Message,
    Provenance,
    ProviderResult,
    Task,
    TaskFamily,
    ToolCall,
    Usage,
)


def make_task(**overrides) -> Task:
    defaults = dict(
        id="test-task",
        family=TaskFamily.DISCUSSIONS,
        title="test task",
        provenance=Provenance(
            source_workflow="test",
            source_type="synthetic_reconstruction",
            note="test fixture",
        ),
        messages=[Message(role="user", content="hello")],
        checks=[Check(type="response_contains", params={"pattern": "hello"})],
    )
    defaults.update(overrides)
    return Task(**defaults)


def make_result(text: str = "hello world", tool_calls: list[ToolCall] | None = None):
    return ProviderResult(
        text=text,
        tool_calls=tool_calls or [],
        usage=Usage(input_tokens=100, output_tokens=50),
    )


@pytest.fixture
def task() -> Task:
    return make_task()
