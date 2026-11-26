---
id: T16
title: "Refuse abbreviated option names with outcome code 3"
layer: "ports"
deps: []
blocks: []
acs: ["AC-06"]
files_hint: ["src/act_verifier/cli.py", "tests/test_cli.py", "tests/test_cli_unit.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "todo"
step: "—"
---

# T16 — Refuse abbreviated option names with outcome code 3

## Origin

Review follow-up: finding 2 in [_review/review-2026-11-26.md](../_review/review-2026-11-26.md) (verdict **Fix now**). The finding cites the files and lines; open it for the full text.

## What

- `--contr`, `--prev`, `--o` are unknown options → invocation error, code 3, nothing written (contracts/cli.md:51).
- Pass `allow_abbrev=False` to the parser.

## Acceptance criteria

Satisfies AC-06 — full text: [spec.md](../spec.md) §5.

## Definition of Done

- [ ] `--contr …` exits 3 with the option named on stderr; no report written
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
