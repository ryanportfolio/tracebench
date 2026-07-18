"""Fail if any published run's artifacts don't reproduce under the graders at HEAD.

For every results/runs/*/results.json, regrade the run against the tasks dir
recorded in its own config and compare results.json + transcripts.jsonl for
exact equality. Any mismatch means graders and published scores have drifted
apart (a grader change without a regrade, or a hand-edited artifact).

Usage: uv run python scripts/check_regrade_drift.py [runs_dir]
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from tracebench.regrade import regrade_run


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    runs_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "results/runs")
    failures = 0
    checked = 0
    for run_dir in sorted(p.parent for p in runs_dir.glob("*/results.json")):
        published = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
        tasks_dir = published["config"]["tasks"]
        if not Path(tasks_dir).is_dir():
            print(f"SKIP {run_dir}: tasks dir {tasks_dir!r} not present at HEAD")
            continue
        checked += 1
        with tempfile.TemporaryDirectory() as tmp:
            regrade_run(str(run_dir), tasks_dir, tmp)
            regraded = json.loads((Path(tmp) / "results.json").read_text(encoding="utf-8"))
            if regraded != published:
                failures += 1
                print(f"DRIFT {run_dir}: results.json does not reproduce under graders at HEAD")
            pub_t = load_jsonl(run_dir / "transcripts.jsonl")
            new_t = load_jsonl(Path(tmp) / "transcripts.jsonl")
            if pub_t != new_t:
                failures += 1
                print(f"DRIFT {run_dir}: transcripts.jsonl does not reproduce at HEAD")
    print(f"checked {checked} run dir(s), {failures} drift failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
