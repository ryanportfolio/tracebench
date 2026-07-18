from __future__ import annotations

import pytest
import yaml

from tests.test_runner import TASK_YAML, make_config
from tracebench.report import generate_report
from tracebench.runner import run


@pytest.fixture
def run_output(tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "run-001.yaml").write_text(TASK_YAML.format(task_id="run-001"), encoding="utf-8")
    injection = "<script>alert('xss')</script> & magic"
    script = {"tasks": {"run-001": {"text": injection}}}
    (tmp_path / "script.yaml").write_text(yaml.safe_dump(script), encoding="utf-8")
    out = tmp_path / "out"
    run(make_config(tmp_path), out)
    return out


def test_report_renders_scores_and_transcripts(run_output, tmp_path):
    out_file = generate_report(run_output, tmp_path / "report.html", note="demo data only")
    page = out_file.read_text(encoding="utf-8")
    assert "<!doctype html>" in page
    assert "run-001" in page
    assert "mock-baseline" in page
    assert "demo data only" in page
    assert "response_contains" in page
    assert "✓ pass" in page  # the injected text contains "magic", so the check passes
    assert "discussions" in page


def test_report_escapes_model_output(run_output, tmp_path):
    page = generate_report(run_output, tmp_path / "report.html").read_text(encoding="utf-8")
    assert "<script>alert" not in page
    assert "&lt;script&gt;alert" in page


def test_report_is_self_contained(run_output, tmp_path):
    page = generate_report(run_output, tmp_path / "report.html").read_text(encoding="utf-8")
    for marker in ("src=\"http", "href=\"http://", "@import", "url("):
        # only allowed external ref is the source-repo link
        occurrences = [
            line for line in page.splitlines() if marker in line and "github.com" not in line
        ]
        assert occurrences == []


def test_report_is_deterministic(run_output, tmp_path):
    a = generate_report(run_output, tmp_path / "a.html").read_text(encoding="utf-8")
    b = generate_report(run_output, tmp_path / "b.html").read_text(encoding="utf-8")
    assert a == b


def test_report_missing_run_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        generate_report(tmp_path / "nope", tmp_path / "report.html")
