from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_runner import TASK_YAML, make_config
from tracebench.runner import run
from tracebench.uidata import export_schemas, stage_ui_data

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_committed_ui_schemas_match_models(tmp_path):
    """ui/schema/*.schema.json is the cross-language contract. If a pydantic
    model changes, regenerate with `uv run tracebench schema --out ui/schema`
    and rerun the UI codegen — this test fails until both sides agree."""
    generated = {p.name: p.read_text(encoding="utf-8") for p in export_schemas(tmp_path)}
    committed_dir = REPO_ROOT / "ui" / "schema"
    for name, content in generated.items():
        committed = committed_dir / name
        assert committed.is_file(), f"missing committed schema: {committed}"
        assert committed.read_text(encoding="utf-8") == content, (
            f"{name} is stale — run: uv run tracebench schema --out ui/schema "
            "&& npm --prefix ui run codegen"
        )


@pytest.fixture
def runs_root(tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "t.yaml").write_text(TASK_YAML.format(task_id="run-001"), encoding="utf-8")
    (tmp_path / "script.yaml").write_text(
        'tasks:\n  run-001:\n    text: "magic word"\n', encoding="utf-8"
    )
    runs = tmp_path / "runs"
    run(make_config(tmp_path), runs / "sweep-a")
    (runs / "not-a-run").mkdir()
    (runs / "not-a-run" / "junk.txt").write_text("x", encoding="utf-8")
    return runs


def test_stage_ui_data_builds_manifest_and_copies_runs(runs_root, tmp_path):
    out = tmp_path / "data"
    manifest_path = stage_ui_data(runs_root, out)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert [r["dir"] for r in manifest["runs"]] == ["sweep-a"]
    entry = manifest["runs"][0]
    assert entry["name"] == "test-run"
    assert entry["n_transcripts"] == 3
    assert entry["n_failures"] == 0
    assert entry["models"] == ["mock/mock-baseline"]
    assert (out / "sweep-a" / "results.json").is_file()
    assert (out / "sweep-a" / "transcripts.jsonl").is_file()


def test_stage_ui_data_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        stage_ui_data(tmp_path / "nope", tmp_path / "out")


def test_stage_ui_data_empty_runs_dir_writes_empty_manifest(tmp_path):
    empty = tmp_path / "runs"
    empty.mkdir()
    manifest = json.loads(stage_ui_data(empty, tmp_path / "out").read_text(encoding="utf-8"))
    assert manifest == {"runs": []}


def test_stage_ui_data_note_lands_in_manifest(tmp_path):
    empty = tmp_path / "runs"
    empty.mkdir()
    manifest_path = stage_ui_data(empty, tmp_path / "out", note="demo data")
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["note"] == "demo data"
