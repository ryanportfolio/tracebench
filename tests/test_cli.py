from __future__ import annotations

from tracebench.cli import main


def test_validate_committed_tasks(capsys):
    exit_code = main(["validate", "tasks"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "OK" in captured.out


def test_validate_missing_dir_fails(capsys, tmp_path):
    exit_code = main(["validate", str(tmp_path / "nope")])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "INVALID" in captured.err


def test_run_dryrun_config(capsys, tmp_path):
    exit_code = main(["run", "--config", "configs/dryrun.yaml", "--out", str(tmp_path / "out")])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "cost: $" in captured.out
    assert (tmp_path / "out" / "results.json").exists()
