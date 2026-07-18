# Commands

> Build / dev / test / deploy commands for this project.

## Core CLI (uv-managed Python 3.12)

- `uv run tracebench validate tasks` — schema-validate all task YAML
- `uv run tracebench run --config configs/<name>.yaml --out results/runs/<dir>` — model sweep (CLI lanes cost real subscription quota)
- `uv run tracebench regrade --run-dir <dir> --tasks <tasks_dir> --out <dir>` — rescore stored transcripts with graders at HEAD, zero model calls
- `uv run tracebench report --run-dir <dir> --out <dir>/report.html --title "..."` — static HTML report
- `uv run tracebench schema --out ui/schema` then `npm --prefix ui run codegen` — regenerate the UI type contract (CI fails on drift)
- `uv run pytest -q`, `uv run ruff check .` — tests + lint
- `uv run python scripts/check_regrade_drift.py` — assert every published run dir reproduces exactly under graders at HEAD (also a CI gate)

## Automation

- CI (`.github/workflows/ci.yml`): push/PR + weekly cron (Mon 08:00 UTC) — lint, tests, validate, regrade-drift, schema/codegen drift. No model calls.
- Weekly sweeps: `scripts/scheduled-sweep.ps1` runs both CLI lanes over `tasks/correction` (configs/scheduled-*.yaml), self-checks drift, commits dated `results/runs/sched-YYYY-MM-DD-*` dirs, opens + merges a PR. Registered in Windows Task Scheduler as `tracebench-weekly-sweep` (Mon 09:00 local, catch-up on missed runs) via `scripts/register-sweep-task.ps1`. Requires this machine's logged-in `claude`/`codex`/`gh` CLIs — consumes real quota.
