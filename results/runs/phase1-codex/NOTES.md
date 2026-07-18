# phase1-codex — run notes

- **Date:** 2026-07-18
- **Lane:** agent-product (Codex CLI headless, ChatGPT subscription).
  Product-level result: measures the model *plus* its vendor harness.
  `provider_version` in every transcript: `codex-cli 0.144.0`, model
  `gpt-5.6-sol`. No temperature/seed control in this lane.
- **Tasks:** 10 discussions-family tasks (6 answerable from curated context,
  4 refusal-when-unverifiable). Full provenance in each task file.
- **Result:** 10/10 tasks at mean 1.00, N=3, stdev 0.00 throughout.

## What the first sweep actually taught us

The first sweep of this exact config scored two tasks below 1.00. Transcript
review showed **both were grader bugs, not model failures**:

- `disc-103`: the model answered correctly ("Remove both
  `@vitejs/plugin-react` and the Babel plugin... Babel is unnecessary") but
  the check regex was case-sensitive and missed the "unnecessary" phrasing.
- `disc-110`: the model refused correctly ("could not verify **whether the
  note is outdated**...") and the negative check matched the *mention* of
  outdatedness inside the refusal, not an assertion of it.

Both graders were fixed (fix rationale committed as comments in the task
files), verified against the failing outputs, and the full sweep was rerun.
This is the discipline the project claims: graders are code, grader bugs are
false claims about model behavior, and transcripts get read before scores
get published.

## Honest read of the 1.00 board

A clean board is a statement about the *suite*, not just the model: at this
difficulty, this family does not discriminate for this product. The refusal
tasks confirm real verification discipline (it declined to invent config
flags on all 4 bait tasks, 3/3 runs each), which is genuinely notable — but
the next steps that would make this board informative are a second model on
the same tasks and harder answerable tasks (multi-fact answers, conflicting
context).
