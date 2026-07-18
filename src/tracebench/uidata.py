"""Data plumbing for the dashboard UI.

Two jobs, both deterministic:
- export the pydantic models as JSON Schema (the cross-language contract the
  TypeScript UI generates its types from; CI fails when the two drift);
- stage a directory of runs into the layout the UI fetches (per-run
  results.json + transcripts.jsonl plus a manifest.json index).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from tracebench.models import Transcript
from tracebench.report import load_run_dir
from tracebench.runner import RunReport

SCHEMA_MODELS = {
    "run_report": RunReport,
    "transcript": Transcript,
}


def export_schemas(out_dir: str | Path) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in SCHEMA_MODELS.items():
        path = out_dir / f"{name}.schema.json"
        schema = model.model_json_schema()
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def stage_ui_data(runs_dir: str | Path, out_dir: str | Path, note: str = "") -> Path:
    """Copy every run under runs_dir into out_dir and write manifest.json.

    A run is any direct subdirectory containing results.json and
    transcripts.jsonl; anything else is skipped silently (working dirs hold
    all sorts of scratch). Manifest entries carry just enough for a run
    picker; the UI fetches the full artifacts per run.
    """
    runs_dir = Path(runs_dir)
    out_dir = Path(out_dir)
    if not runs_dir.is_dir():
        raise FileNotFoundError(f"runs directory not found: {runs_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for candidate in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        if not (candidate / "results.json").is_file():
            continue
        if not (candidate / "transcripts.jsonl").is_file():
            continue
        report, transcripts = load_run_dir(candidate)
        dest = out_dir / candidate.name
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(candidate / "results.json", dest / "results.json")
        shutil.copyfile(candidate / "transcripts.jsonl", dest / "transcripts.jsonl")
        entries.append(
            {
                "dir": candidate.name,
                "name": report.config.name,
                "n_transcripts": report.n_transcripts,
                "total_cost_usd": report.total_cost_usd,
                "halted_on_budget": report.halted_on_budget,
                "models": [f"{m.provider}/{m.model_id}" for m in report.config.models],
                "n_failures": sum(1 for t in transcripts if t.score < 1.0),
            }
        )
    payload: dict = {"runs": entries}
    if note:
        payload["note"] = note
    manifest = out_dir / "manifest.json"
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest
