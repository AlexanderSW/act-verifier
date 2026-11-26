---
id: T15
title: "Show the previous-acts completeness reason in the evidence block"
layer: "domain"
deps: []
blocks: []
acs: ["AC-03", "AC-11"]
files_hint: ["src/act_verifier/checks.py", "src/act_verifier/report.py", "tests/test_checks.py", "tests/test_report.py", "tests/test_verifier.py", "tests/test_cli.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "todo"
step: "—"
---

# T15 — Show the previous-acts completeness reason in the evidence block

## Origin

Review follow-up: finding 1 in [_review/review-2026-11-26.md](../_review/review-2026-11-26.md) (verdict **Fix now**). The finding cites the files and lines; open it for the full text.

## What

- When previous acts are not exactly 1…N−1, record `Skipped(C05, code, reason)` for every position whose C05 is unknown for that reason, and `Skipped(C13, None, reason)`; the unknown findings stay (AC-11).
- «Не перевірено» groups entries with the same checks and reason across positions: `2-1, 2-2 — C05 (подано попередніх актів: 1 з 2); акт — C13 (…)`.
- Assert the line in core (`incomplete_previous`) and through the command (stdout).

## Acceptance criteria

Satisfies AC-03, AC-11 — full text: [spec.md](../spec.md) §5.

## Definition of Done

- [ ] on `incomplete_previous` the evidence block on stdout names «подано попередніх актів: 1 з 2» for C05 and C13
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
