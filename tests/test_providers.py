from __future__ import annotations

import pytest

from tracebench.config import ModelConfig, Pricing, RunConfig, compute_cost
from tracebench.models import Usage
from tracebench.providers import UnknownProviderError, build_provider
from tracebench.providers.mock import MockProvider, MockResponse, MockScript


def model_cfg(provider: str = "mock") -> ModelConfig:
    return ModelConfig(
        provider=provider,
        model_id="mock-baseline",
        pricing=Pricing(input_per_mtok=3.0, output_per_mtok=15.0),
    )


def run_cfg(**overrides) -> RunConfig:
    defaults = dict(name="test", tasks="tasks", models=[model_cfg()], budget_usd=1.0)
    defaults.update(overrides)
    return RunConfig(**defaults)


def test_mock_is_deterministic_for_fixed_seed(task):
    provider = MockProvider()
    a = provider.complete(task, model_cfg(), seed=7)
    b = provider.complete(task, model_cfg(), seed=7)
    assert a == b


def test_mock_uses_scripted_response(task):
    script = MockScript(tasks={task.id: MockResponse(text="scripted answer")})
    provider = MockProvider(script)
    result = provider.complete(task, model_cfg(), seed=0)
    assert result.text == "scripted answer"


def test_mock_unscripted_placeholder_names_task(task):
    result = MockProvider().complete(task, model_cfg(), seed=0)
    assert task.id in result.text


def test_mock_reports_nonzero_usage(task):
    result = MockProvider().complete(task, model_cfg(), seed=0)
    assert result.usage.input_tokens > 0
    assert result.usage.output_tokens > 0


def test_build_provider_rejects_unknown():
    cfg = run_cfg()
    with pytest.raises(UnknownProviderError):
        build_provider(model_cfg(provider="openai"), cfg)


def test_compute_cost():
    usage = Usage(input_tokens=1_000_000, output_tokens=2_000_000)
    pricing = Pricing(input_per_mtok=3.0, output_per_mtok=15.0)
    assert compute_cost(usage, pricing) == pytest.approx(3.0 + 30.0)
