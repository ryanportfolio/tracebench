# tracebench

Replayable agent evals distilled from real developer workflows.

Most public evals are synthetic: invented tasks, invented failure modes. The
tasks here are distilled from one practitioner's real agent workflows, and
every task carries a provenance note tying it back to the workflow it came
from — at the strength that's actually true, stated per family. The
discussions family comes from a modest but real side workflow (agent-assisted
answering of public GitHub Discussions); it anchors v1 because it is fully
public-source and deterministically gradable. The tool-use and long-horizon
families (in progress) carry the heavier provenance: they come from months of
daily agent-driven development across live products.

**Status: phase 0.** Harness skeleton, mock provider, task schema, CI. No
model results yet — a headline results table lands here with the first
published sweep (phase 3).

## What this measures

Three task families, all derived from real workflows:

| Family | Real workflow it came from | Graded on |
|---|---|---|
| `discussions` | Side workflow: agent-assisted answering of public GitHub Discussions | Factual verification behavior, refusal when unverifiable, instruction following |
| `correction` | Frozen decision points harvested from months of real agent sessions (reconstructed, labeled) | Correction uptake, evidence-based updating vs sycophancy, capability self-modeling, trust in subagent claims, ground-truthing under pressure |
| `tool_use` | Agent workflow steps: `gh api` queries, file edits, multi-step git flows | Tool selection, argument correctness, error recovery after an injected tool failure |
| `long_horizon` | Multi-step pipelines (scout → rank → read → draft) | Completion without human rescue, budget discipline, silent step-dropping |

v1 targets 20–30 tasks total. Every task file records provenance (what real
workflow it came from), the exact prompt and context, tools available, and the
grading spec.

## Method

- **Deterministic grading first.** Exact tool-call checks, schema validation,
  citation-resolution checks. LLM-as-judge only where unavoidable (prose
  quality), and then with a committed rubric, a judge from a different
  provider than the model under test, and a human-labeled agreement set
  measuring judge reliability before the judge is trusted.
- **No single-run scores.** N≥3 runs per task per model; results report mean
  and spread. Fixed seeds where the API supports them; the seed is recorded
  either way.
- **Pinned configs.** Exact model IDs and params live in committed run
  configs. No score is reported without its full config.
- **Failures are the product.** Every failure ships as a full annotated
  transcript: what happened, a hypothesis for why, and a bucket in the
  [failure taxonomy](taxonomy.md). A run where everything passes teaches
  nothing.
- **Budget discipline.** Hard per-run spend cap in config; the runner halts
  rather than overspending, and prints a cost report every run.
- **Grader fixes never re-run models.** Transcripts store the full output;
  `tracebench regrade` rescores a stored run under the current graders with
  zero model calls, so a grader bug is corrected in place and the published
  board stays on one grader version. Both grader-bug rounds to date (and
  what they were) are documented in `results/runs/*/NOTES.md`.

Scoring outputs are designed to be reusable downstream as training-data
filters for a planned small-scale SFT/DPO post-training project, with this
suite as the before/after measuring stick.

## Two lanes: raw API vs agent product

The suite runs the same tasks through two deliberately different lanes,
because they answer different questions:

| | API lane | Agent-product lane |
|---|---|---|
| Drives | Provider APIs directly | Local agent CLIs headlessly (`claude -p`, `codex exec`) |
| Measures | The model, params pinned in config | The model **plus** its product harness (vendor system prompt, tools, scaffolding) |
| Pinned by | Exact model ID + params | Model ID + recorded CLI version (`provider_version` in every transcript) |
| Determinism | Fixed seeds where supported | None promised — no temperature/seed control; N≥3 and spread do the work |
| Cost | Metered per token, budget-capped | Subscription; zero marginal cost, modest headless volume only |

Agent-product results are confounded by the product harness by construction —
that is the point (it is how these agents are actually used day to day), and
results from this lane are always labeled as product-level, never presented
as model-level. Two residual caveats, stated plainly: product harnesses
change over time (hence the recorded CLI version), and user-level global
agent config on the machine running the sweep can influence behavior even
though each run executes in an isolated empty directory. Tasks that define
their own tools run only in the API lane, where the tool schema can actually
be injected.

## Privacy rule

Nothing from private repositories appears in any published task, fixture, or
transcript. Tasks are built from public sources (public discussion threads,
public repos) or synthetic-but-realistic reconstructions. When a real
private-workflow failure inspires a task, it is rebuilt with public or
synthetic material and the provenance note says so
(`source_type: synthetic_reconstruction`).

## Honest limits

This is a solo project. The results are one practitioner's workflow-specific
evals — useful signal about these workflows, not a general benchmark. The N
is small and the statistics are descriptive (mean and spread), not claims of
significance. Where something could not be verified, it is reported as "could
not verify", never guessed. The framing throughout is neutral and
evidence-first; the goal is understanding failure modes, not ranking vendors.

## Results UI

Two presentation layers, same artifacts, both derived only from
`results.json` + `transcripts.jsonl`:

- **Dashboard app** (`ui/`, React + TypeScript): run picker, family
  leaderboard, sortable per-task table, and a transcript explorer with
  model/family/verdict filters and full-text search. Serve it over local
  runs with one command:

  ```sh
  npm --prefix ui install && npm --prefix ui run build   # once
  uv run tracebench ui --runs-dir .tmp/runs              # http://127.0.0.1:8321
  ```

  The same build deploys to GitHub Pages on every push to `main`
  (clearly-labeled mock-data demo until the first real sweep lands):
  <https://ryanportfolio.github.io/tracebench/>

- **Static report** (`tracebench report --run-dir … --out report.html`): a
  single self-contained HTML file per run — the archival layer that gets
  committed alongside published results and works from `file://` forever.

The UI's TypeScript types are generated from the harness's pydantic models
via exported JSON Schema (`uv run tracebench schema --out ui/schema`, then
`npm --prefix ui run codegen`); CI fails if the schemas, the generated types,
or the models drift apart.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync --dev
uv run pytest                     # test the harness itself
uv run tracebench validate tasks  # validate all committed task files
uv run tracebench run --config configs/dryrun.yaml --out .tmp/dryrun
```

The dry run uses the mock provider: zero API spend, but the full pipeline —
load → complete → grade → aggregate → cost report — runs for real.

## Repository layout

```
src/tracebench/    harness: models, providers, graders, runner, budget, CLI
tasks/             task files (YAML, one per task) — see tasks/README.md
configs/           committed run configs (model IDs, params, pricing, budget)
tests/             pytest suite for the harness (graders are code; code gets tests)
results/           published scored results per run (curated, committed)
transcripts/       published annotated failure transcripts (curated, committed)
taxonomy.md        living failure taxonomy, linking to example transcripts
```

## Roadmap

- **Phase 0 (this)** — scaffold, harness skeleton, mock provider, CI, plus
  agent-product lane adapters (Claude Code, Codex CLI).
- **Phase 1** — anchor family: ~10 discussions-answering tasks from public
  threads, deterministic graders, first real API provider end-to-end.
- **Phase 2** — tool-use family with injected failures; second and third
  providers; N≥3 run protocol.
- **Phase 3** — long-horizon family; LLM-judge lane with agreement check;
  first full sweep; publish results and taxonomy v1.
- **Phase 4** — transcript annotation polish; first trace-teardown write-up
  from the best failure.

## Links

- Portfolio hub: [corewise.academy/about](https://corewise.academy/about)

## License

[MIT](LICENSE)
