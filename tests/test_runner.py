from __future__ import annotations

import json

import pytest
import yaml

from tracebench.config import RunConfig
from tracebench.runner import run

TASK_YAML = """\
id: {task_id}
family: discussions
title: runner test task
provenance:
  source_workflow: test
  source_type: synthetic_reconstruction
  note: runner test fixture
messages:
  - role: user
    content: say the magic word
checks:
  - type: response_contains
    params:
      pattern: magic
"""


@pytest.fixture
def workspace(tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for task_id in ("run-001", "run-002"):
        (tasks_dir / f"{task_id}.yaml").write_text(
            TASK_YAML.format(task_id=task_id), encoding="utf-8"
        )
    script = {"tasks": {"run-001": {"text": "magic word"}, "run-002": {"text": "no dice"}}}
    script_path = tmp_path / "script.yaml"
    script_path.write_text(yaml.safe_dump(script), encoding="utf-8")
    return tmp_path


def make_config(workspace, **overrides) -> RunConfig:
    defaults = dict(
        name="test-run",
        tasks=str(workspace / "tasks"),
        models=[
            {
                "provider": "mock",
                "model_id": "mock-baseline",
                "pricing": {"input_per_mtok": 3.0, "output_per_mtok": 15.0},
            }
        ],
        runs_per_task=3,
        budget_usd=1.0,
        base_seed=42,
        mock_script=str(workspace / "script.yaml"),
    )
    defaults.update(overrides)
    return RunConfig.model_validate(defaults)


def test_end_to_end_scores_and_outputs(workspace, tmp_path):
    out = tmp_path / "out"
    report = run(make_config(workspace), out)

    assert report.n_transcripts == 6  # 2 tasks x 1 model x 3 runs
    assert not report.halted_on_budget
    assert report.total_cost_usd > 0

    by_task = {agg.task_id: agg for agg in report.by_task}
    assert by_task["run-001"].mean_score == 1.0
    assert by_task["run-002"].mean_score == 0.0
    assert by_task["run-001"].n == 3
    assert by_task["run-001"].stdev_score == 0.0

    assert len(report.by_family) == 1
    assert report.by_family[0].mean_of_task_means == pytest.approx(0.5)

    results = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert results["n_transcripts"] == 6

    lines = (out / "transcripts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6
    first = json.loads(lines[0])
    assert first["seed"] == 42
    assert first["model_id"] == "mock-baseline"
    assert first["cost_usd"] > 0
    assert first["checks"]


def test_runs_get_distinct_recorded_seeds(workspace, tmp_path):
    report = run(make_config(workspace), tmp_path / "out")
    lines = (tmp_path / "out" / "transcripts.jsonl").read_text(encoding="utf-8").splitlines()
    seeds = {json.loads(line)["seed"] for line in lines}
    assert seeds == {42, 43, 44}
    assert report.config.base_seed == 42


def test_budget_halt_writes_partial_results(workspace, tmp_path):
    tiny = make_config(workspace, budget_usd=0.000001)
    out = tmp_path / "out"
    report = run(tiny, out)

    assert report.halted_on_budget
    assert report.n_transcripts == 1  # first run blew the cap, nothing after it ran
    assert report.total_cost_usd > tiny.budget_usd
    assert (out / "results.json").exists()
    assert (out / "transcripts.jsonl").exists()


def test_determinism_same_config_same_results(workspace, tmp_path):
    report_a = run(make_config(workspace), tmp_path / "a")
    report_b = run(make_config(workspace), tmp_path / "b")
    assert report_a.by_task == report_b.by_task
    assert (tmp_path / "a" / "transcripts.jsonl").read_text(encoding="utf-8") == (
        tmp_path / "b" / "transcripts.jsonl"
    ).read_text(encoding="utf-8")
