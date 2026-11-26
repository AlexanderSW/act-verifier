---
id: T19
title: "Map the remaining argparse errors to Ukrainian messages naming the option"
layer: "ports"
deps: ["T16"]
blocks: []
acs: ["AC-06"]
files_hint: ["src/act_verifier/cli.py", "tests/test_cli_unit.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "todo"
step: "—"
---

# T19 — Map the remaining argparse errors to Ukrainian messages naming the option

## Origin

Review follow-up: finding 5 in [_review/review-2026-11-26.md](../_review/review-2026-11-26.md) (verdict **Fix now**). The finding cites the files and lines; open it for the full text.

## What

- «expected one argument» (e.g. `--contract` with no value) and any other argparse message → Ukrainian text that names the option; still code 3 (contracts/cli.md §3).

## Acceptance criteria

Satisfies AC-06 — full text: [spec.md](../spec.md) §5.

## Definition of Done

- [ ] no English argparse text reaches stderr for the known argparse message shapes
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
