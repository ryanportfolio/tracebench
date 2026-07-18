from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tests.conftest import make_task
from tracebench.config import ModelConfig, Pricing
from tracebench.models import Message, ToolSpec
from tracebench.providers.cli_agents import (
    ClaudeCodeProvider,
    CLIAgentError,
    CodexProvider,
    _scrubbed_env,
)


def proc(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def model_cfg(provider: str, model_id: str = "some-model") -> ModelConfig:
    return ModelConfig(
        provider=provider,
        model_id=model_id,
        pricing=Pricing(input_per_mtok=0.0, output_per_mtok=0.0),
    )


def two_part_task():
    return make_task(
        messages=[
            Message(role="system", content="only verified claims"),
            Message(role="user", content="answer the discussion"),
        ]
    )


class FakeRun:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, cmd, timeout_s, cwd):
        self.calls.append({"cmd": cmd, "timeout_s": timeout_s, "cwd": cwd})
        response = self.responses.pop(0)
        return response(cmd) if callable(response) else response


CLAUDE_OK = json.dumps(
    {
        "type": "result",
        "is_error": False,
        "result": "the answer",
        "usage": {"input_tokens": 12, "output_tokens": 7},
    }
)


class TestClaudeCodeProvider:
    def test_builds_headless_command(self):
        fake = FakeRun([proc(stdout=CLAUDE_OK)])
        result = ClaudeCodeProvider(fake).complete(two_part_task(), model_cfg("claude-code"), 0)
        cmd = fake.calls[0]["cmd"]
        assert cmd[:4] == ["claude", "-p", "--output-format", "json"]
        assert cmd[cmd.index("--model") + 1] == "some-model"
        assert cmd[cmd.index("--append-system-prompt") + 1] == "only verified claims"
        assert cmd[-1] == "answer the discussion"
        assert result.text == "the answer"
        assert result.usage.input_tokens == 12
        assert result.usage.output_tokens == 7

    def test_no_system_message_omits_flag(self):
        fake = FakeRun([proc(stdout=CLAUDE_OK)])
        ClaudeCodeProvider(fake).complete(make_task(), model_cfg("claude-code"), 0)
        assert "--append-system-prompt" not in fake.calls[0]["cmd"]

    def test_runs_in_isolated_temp_cwd(self):
        fake = FakeRun([proc(stdout=CLAUDE_OK)])
        ClaudeCodeProvider(fake).complete(make_task(), model_cfg("claude-code"), 0)
        cwd = fake.calls[0]["cwd"]
        assert cwd is not None and "tracebench-claude-" in cwd

    def test_nonzero_exit_raises_with_stderr(self):
        fake = FakeRun([proc(returncode=1, stderr="not logged in")])
        with pytest.raises(CLIAgentError, match="not logged in"):
            ClaudeCodeProvider(fake).complete(make_task(), model_cfg("claude-code"), 0)

    def test_error_result_raises(self):
        payload = json.dumps({"is_error": True, "result": "boom"})
        fake = FakeRun([proc(stdout=payload)])
        with pytest.raises(CLIAgentError, match="error result"):
            ClaudeCodeProvider(fake).complete(make_task(), model_cfg("claude-code"), 0)

    def test_non_json_output_raises(self):
        fake = FakeRun([proc(stdout="plain text, not json")])
        with pytest.raises(CLIAgentError, match="non-JSON"):
            ClaudeCodeProvider(fake).complete(make_task(), model_cfg("claude-code"), 0)

    def test_task_with_tools_rejected(self):
        task = make_task(tools=[ToolSpec(name="gh_api", description="call gh")])
        with pytest.raises(CLIAgentError, match="agent-product lane"):
            ClaudeCodeProvider(FakeRun([])).complete(task, model_cfg("claude-code"), 0)

    def test_timeout_from_params(self):
        fake = FakeRun([proc(stdout=CLAUDE_OK)])
        cfg = model_cfg("claude-code")
        cfg.params["timeout_s"] = 42
        ClaudeCodeProvider(fake).complete(make_task(), cfg, 0)
        assert fake.calls[0]["timeout_s"] == 42

    def test_version_captured_and_cached(self):
        fake = FakeRun([proc(stdout="2.1.0 (Claude Code)\n")])
        provider = ClaudeCodeProvider(fake)
        assert provider.describe_version() == "2.1.0 (Claude Code)"
        assert provider.describe_version() == "2.1.0 (Claude Code)"
        assert len(fake.calls) == 1


def codex_success(cmd):
    out_file = Path(cmd[cmd.index("--output-last-message") + 1])
    out_file.write_text("codex answer\n", encoding="utf-8")
    return proc(stdout="")


class TestCodexProvider:
    def test_builds_exec_command_and_reads_last_message(self):
        fake = FakeRun([codex_success])
        result = CodexProvider(fake).complete(two_part_task(), model_cfg("codex", "gpt-thing"), 0)
        cmd = fake.calls[0]["cmd"]
        assert cmd[:2] == ["codex", "exec"]
        assert cmd[cmd.index("--model") + 1] == "gpt-thing"
        assert "--skip-git-repo-check" in cmd
        assert cmd[-1] == "only verified claims\n\nanswer the discussion"
        assert result.text == "codex answer"
        assert result.usage.input_tokens == 0  # codex exec reports no usage; pricing is zero

    def test_nonzero_exit_raises(self):
        fake = FakeRun([proc(returncode=2, stderr="auth required")])
        with pytest.raises(CLIAgentError, match="auth required"):
            CodexProvider(fake).complete(make_task(), model_cfg("codex"), 0)

    def test_missing_last_message_file_raises(self):
        fake = FakeRun([proc(stdout="ran but wrote nothing")])
        with pytest.raises(CLIAgentError, match="no last-message file"):
            CodexProvider(fake).complete(make_task(), model_cfg("codex"), 0)

    def test_task_with_tools_rejected(self):
        task = make_task(tools=[ToolSpec(name="gh_api", description="call gh")])
        with pytest.raises(CLIAgentError, match="agent-product lane"):
            CodexProvider(FakeRun([])).complete(task, model_cfg("codex"), 0)

    def test_version_failure_raises(self):
        fake = FakeRun([proc(returncode=1, stderr="no codex here")])
        with pytest.raises(CLIAgentError, match="no codex here"):
            CodexProvider(fake).describe_version()


def test_scrubbed_env_removes_session_auth_vars(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://hijack.example")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "abc")
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("UNRELATED_VAR", "keep-me")
    env = _scrubbed_env()
    assert "ANTHROPIC_BASE_URL" not in env
    assert "CLAUDE_CODE_SESSION_ID" not in env
    assert "CLAUDECODE" not in env
    assert env["UNRELATED_VAR"] == "keep-me"
