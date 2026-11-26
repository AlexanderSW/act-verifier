---
id: T18
title: "Assert the test run leaves the tracked journal unchanged instead of empty"
layer: "tests"
deps: []
blocks: []
acs: ["AC-14"]
files_hint: ["tests/test_cli.py", "tests/conftest.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "done"
step: "COMMIT"
---

# T18 — Assert the test run leaves the tracked journal unchanged instead of empty

## Origin

Review follow-up: finding 4 in [_review/review-2026-11-26.md](../_review/review-2026-11-26.md) (verdict **Fix now**). The finding cites the files and lines; open it for the full text.

## What

- Replace the header-only assertion on `journal/agent_errors.csv` with a before/after fingerprint over the test session, so real journal entries do not turn the suite red.

## Acceptance criteria

Satisfies AC-14 — full text: [spec.md](../spec.md) §5.

## Definition of Done

- [ ] suite stays green with extra lines in `journal/agent_errors.csv`; a test that wrote to it would still fail
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
