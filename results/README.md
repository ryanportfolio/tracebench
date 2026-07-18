# results/

Curated, published run results. `runs/<name>/` holds the exact artifacts the
harness wrote (`results.json` with the full pinned config, plus
`transcripts.jsonl`) and a rendered `report.html`; the GitHub Pages dashboard
serves this directory verbatim.

Working runs go to `.tmp/` or any `--out` directory and are not committed;
only curated, config-pinned results are published here. No score appears
without the exact config that produced it. Agent-product-lane runs are
product-level results (model + vendor CLI harness) and say so.
