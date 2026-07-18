from __future__ import annotations

import json

import pytest

from tests.test_runner import TASK_YAML, make_config
from tracebench.regrade import RegradeError, regrade_run
from tracebench.runner import run


@pytest.fixture
def graded_run(tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "t.yaml").write_text(TASK_YAML.format(task_id="run-001"), encoding="utf-8")
    (tmp_path / "script.yaml").write_text(
        'tasks:\n  run-001:\n    text: "MAGIC word"\n', encoding="utf-8"
    )
    out = tmp_path / "out"
    run(make_config(tmp_path), out)
    return tmp_path, tasks_dir, out


def test_regrade_same_graders_reproduces_scores(graded_run, tmp_path):
    _, tasks_dir, out = graded_run
    report = regrade_run(out, tasks_dir, tmp_path / "regraded")
    original = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert report.model_dump(mode="json")["by_task"] == original["by_task"]
    assert report.n_transcripts == original["n_transcripts"]


def test_regrade_applies_grader_fix_without_model_calls(graded_run, tmp_path):
    root, tasks_dir, out = graded_run
    # Original check pattern "magic" is case-sensitive -> "MAGIC word" scored 0.
    original = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert original["by_task"][0]["mean_score"] == 0.0

    # "Fix the grader": make the check case-insensitive, then regrade.
    task_file = tasks_dir / "t.yaml"
    task_file.write_text(
        task_file.read_text(encoding="utf-8").replace(
            "      pattern: magic",
            "      pattern: magic\n      case_insensitive: true",
        ),
        encoding="utf-8",
    )
    report = regrade_run(out, tasks_dir, tmp_path / "regraded")
    assert report.by_task[0].mean_score == 1.0

    # Outputs must be byte-identical to the original run — only grades moved.
    old_outputs = [
        json.loads(line)["output_text"]
        for line in (out / "transcripts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    new_outputs = [
        json.loads(line)["output_text"]
        for line in (tmp_path / "regraded" / "transcripts.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert new_outputs == old_outputs


def test_regrade_missing_task_raises(graded_run, tmp_path):
    _, _, out = graded_run
    other_tasks = tmp_path / "other-tasks"
    other_tasks.mkdir()
    (other_tasks / "x.yaml").write_text(TASK_YAML.format(task_id="different"), encoding="utf-8")
    with pytest.raises(RegradeError, match="run-001"):
        regrade_run(out, other_tasks, tmp_path / "regraded")
