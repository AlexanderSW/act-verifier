---
id: T20
title: "Assert expected and actual values of the three combo fails"
layer: "tests"
deps: []
blocks: []
acs: ["AC-02"]
files_hint: ["tests/test_checks.py", "tests/test_verifier.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "done"
step: "COMMIT"
---

# T20 — Assert expected and actual values of the three combo fails

## Origin

Review follow-up: finding 6 in [_review/review-2026-11-26.md](../_review/review-2026-11-26.md) (verdict **Fix now**). The finding cites the files and lines; open it for the full text.

## What

- For `combo_three_errors`, assert `expected` and `actual` of each fail equal the reference numbers read from the fixture files.

## Acceptance criteria

Satisfies AC-02 — full text: [spec.md](../spec.md) §5.

## Definition of Done

- [ ] a wrong expected/actual on any of the three combo fails turns a test red
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
