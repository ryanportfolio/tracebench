"""Provider adapters. One adapter per API vendor, all behind one interface.

Real adapters (Anthropic, OpenAI, open-weights host) land in later phases.
Phase 0 ships the interface plus the mock provider so the whole harness runs
end-to-end with zero spend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from tracebench.config import ModelConfig, RunConfig
from tracebench.models import ProviderResult, Task


class Provider(ABC):
    name: str

    @abstractmethod
    def complete(self, task: Task, model_cfg: ModelConfig, seed: int) -> ProviderResult:
        """Run one task once. Must be deterministic for a fixed seed where the
        underlying API supports it; the seed is always recorded either way."""


class UnknownProviderError(ValueError):
    pass


def build_provider(model_cfg: ModelConfig, run_cfg: RunConfig) -> Provider:
    from tracebench.providers.mock import MockProvider

    if model_cfg.provider == "mock":
        return MockProvider.from_run_config(run_cfg)
    raise UnknownProviderError(
        f"unknown provider: {model_cfg.provider!r} (phase 0 ships only 'mock')"
    )
