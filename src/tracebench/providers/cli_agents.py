"""Agent-product lane: drive local agent CLIs headlessly under a subscription.

These adapters measure the model *plus* its product harness (system prompt,
tools, scaffolding the vendor ships) — a different, honestly-labeled claim
than the raw-API lane. Consequences, documented rather than hidden:

- No temperature/seed control; the recorded seed is bookkeeping only.
- The product harness changes over time, so the CLI version is captured into
  every transcript (`provider_version`).
- Runs execute in an empty temporary directory so this repo's project context
  doesn't leak into the eval; user-level global config can still influence
  the agent and is called out in the README.
- Task-defined tools are not injectable into the product CLIs; tasks with
  `tools` are rejected loudly instead of silently mis-measured.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from tracebench.config import ModelConfig
from tracebench.models import ProviderResult, Task, Usage
from tracebench.providers import Provider

DEFAULT_TIMEOUT_S = 600

# Seam for tests: same signature as the default subprocess runner.
RunFn = Callable[[list[str], int, str | None], subprocess.CompletedProcess]


class CLIAgentError(RuntimeError):
    pass


def _scrubbed_env() -> dict[str, str]:
    """Environment for spawned CLIs, minus session/auth overrides.

    When the harness itself runs inside an agent session, vars like
    ANTHROPIC_BASE_URL and CLAUDE_CODE_* leak in and hijack the child CLI's
    auth (observed: 401s from a nested `claude -p`). Scrubbing them also
    keeps parent-session config from contaminating the eval; the child CLI
    authenticates from its own stored credentials.
    """
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("CLAUDE", "ANTHROPIC_"))
    }


def _default_run(cmd: list[str], timeout_s: int, cwd: str | None) -> subprocess.CompletedProcess:
    resolved = shutil.which(cmd[0])
    if resolved is None:
        raise CLIAgentError(f"CLI not found on PATH: {cmd[0]!r}")
    return subprocess.run(
        [resolved, *cmd[1:]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_s,
        cwd=cwd,
        env=_scrubbed_env(),
        stdin=subprocess.DEVNULL,
    )


def _split_prompt(task: Task) -> tuple[str, str]:
    """Return (system_text, user_text) from the task's messages."""
    system_parts = [m.content for m in task.messages if m.role == "system"]
    other_parts = [m.content for m in task.messages if m.role != "system"]
    return "\n\n".join(system_parts), "\n\n".join(other_parts)


class _CLIProvider(Provider):
    def __init__(self, run_fn: RunFn | None = None) -> None:
        self._run = run_fn or _default_run
        self._version: str | None = None

    version_cmd: list[str]

    def describe_version(self) -> str:
        if self._version is None:
            proc = self._run(self.version_cmd, 60, None)
            if proc.returncode != 0:
                raise CLIAgentError(
                    f"{self.version_cmd} failed (exit {proc.returncode}): {proc.stderr.strip()}"
                )
            self._version = proc.stdout.strip()
        return self._version

    def _reject_tools(self, task: Task) -> None:
        if task.tools:
            raise CLIAgentError(
                f"task {task.id!r} defines tools; the agent-product lane cannot inject "
                "task-defined tools into a product CLI — use the API lane for this task"
            )


class ClaudeCodeProvider(_CLIProvider):
    """Headless Claude Code: `claude -p --output-format json`."""

    name = "claude-code"
    version_cmd = ["claude", "--version"]

    def complete(self, task: Task, model_cfg: ModelConfig, seed: int) -> ProviderResult:
        self._reject_tools(task)
        system_text, user_text = _split_prompt(task)
        cmd = ["claude", "-p", "--output-format", "json", "--model", model_cfg.model_id]
        if system_text:
            cmd += ["--append-system-prompt", system_text]
        cmd.append(user_text)
        timeout_s = int(model_cfg.params.get("timeout_s", DEFAULT_TIMEOUT_S))

        # ignore_cleanup_errors: on Windows the CLI's child processes can
        # briefly hold the cwd handle after exit; a leaked temp dir is fine.
        tmp = tempfile.TemporaryDirectory(prefix="tracebench-claude-", ignore_cleanup_errors=True)
        with tmp as cwd:
            proc = self._run(cmd, timeout_s, cwd)
        if proc.returncode != 0:
            raise CLIAgentError(
                f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()[:2000]}"
            )
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise CLIAgentError(f"claude -p returned non-JSON output: {exc}") from exc
        if payload.get("is_error"):
            raise CLIAgentError(f"claude -p reported an error result: {payload.get('result')!r}")
        usage = payload.get("usage", {})
        return ProviderResult(
            text=payload.get("result", ""),
            usage=Usage(
                input_tokens=int(usage.get("input_tokens", 0)),
                output_tokens=int(usage.get("output_tokens", 0)),
            ),
        )


class CodexProvider(_CLIProvider):
    """Headless Codex CLI: `codex exec --output-last-message <file>`.

    Codex does not report token usage in this mode; usage stays zero and the
    lane's pricing is zero, so cost math remains truthful (subscription lane,
    no marginal cost).
    """

    name = "codex"
    version_cmd = ["codex", "--version"]

    def complete(self, task: Task, model_cfg: ModelConfig, seed: int) -> ProviderResult:
        self._reject_tools(task)
        system_text, user_text = _split_prompt(task)
        prompt = f"{system_text}\n\n{user_text}" if system_text else user_text
        timeout_s = int(model_cfg.params.get("timeout_s", DEFAULT_TIMEOUT_S))

        tmp = tempfile.TemporaryDirectory(prefix="tracebench-codex-", ignore_cleanup_errors=True)
        with tmp as cwd:
            out_file = Path(cwd) / "last-message.txt"
            cmd = [
                "codex",
                "exec",
                "--model",
                model_cfg.model_id,
                "--skip-git-repo-check",
                "--output-last-message",
                str(out_file),
                prompt,
            ]
            proc = self._run(cmd, timeout_s, cwd)
            if proc.returncode != 0:
                raise CLIAgentError(
                    f"codex exec failed (exit {proc.returncode}): {proc.stderr.strip()[:2000]}"
                )
            if not out_file.exists():
                raise CLIAgentError("codex exec finished but wrote no last-message file")
            text = out_file.read_text(encoding="utf-8").strip()
        return ProviderResult(text=text, usage=Usage())
