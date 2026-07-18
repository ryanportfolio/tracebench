# Task files

One YAML file per task, validated strictly against the `Task` model in
[`src/tracebench/models.py`](../src/tracebench/models.py). Unknown fields are
rejected. `uv run tracebench validate tasks` must pass (CI enforces it).

## Format

```yaml
id: disc-001-some-slug          # unique across the whole suite
family: discussions             # discussions | tool_use | long_horizon
title: One-line human title
provenance:
  source_workflow: githelp-discussions-answering
  source_type: public           # public | synthetic_reconstruction
  note: >-
    Where this task really came from. If source_type is
    synthetic_reconstruction, explain what was rebuilt and why.
messages:                       # exact prompt + context, verbatim
  - role: system
    content: ...
  - role: user
    content: ...
tools: []                       # tool schemas offered to the model, if any
checks:                         # grading spec — deterministic graders
  - type: response_contains
    params: { pattern: "docs/cli\\.md" }
    weight: 2.0
max_turns: 1
```

## Check types (phase 0)

| Type | Params | Passes when |
|---|---|---|
| `response_contains` | `pattern` (regex), `case_insensitive` | pattern matches response text |
| `response_not_contains` | `pattern` (regex), `case_insensitive` | pattern does not match |
| `tool_call_made` | `name`, optional `arguments` (subset match) | a matching tool call was made |
| `no_tool_calls` | — | zero tool calls were made |

Score = weighted fraction of passed checks, in [0, 1].

## Privacy rule (hard)

No content from private repositories, ever. `source_type: public` means the
material is verbatim from a public source; `synthetic_reconstruction` means a
private-workflow failure inspired the task and it was rebuilt from public or
synthetic material — and the provenance note must say so.
