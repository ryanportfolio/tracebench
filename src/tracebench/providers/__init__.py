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

    def describe_version(self) -> str:
        """Version of the thing under test beyond the model id (e.g. the CLI
        product version in the agent-product lane). Empty when the model id
        alone pins the behavior."""
        return ""


class UnknownProviderError(ValueError):
    pass


def build_provider(model_cfg: ModelConfig, run_cfg: RunConfig) -> Provider:
    from tracebench.providers.cli_agents import ClaudeCodeProvider, CodexProvider
    from tracebench.providers.mock import MockProvider

    if model_cfg.provider == "mock":
        return MockProvider.from_run_config(run_cfg)
    if model_cfg.provider == "claude-code":
        return ClaudeCodeProvider()
    if model_cfg.provider == "codex":
        return CodexProvider()
    raise UnknownProviderError(
        f"unknown provider: {model_cfg.provider!r} "
        "(available: mock, claude-code, codex; raw-API providers land in phase 1+)"
    )
