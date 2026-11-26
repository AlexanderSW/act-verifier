---
id: T17
title: "Cite the КБ-2в sheet title as found, not the literal «КБ-2в»"
layer: "domain"
deps: ["T15"]
blocks: []
acs: ["AC-03", "AC-09"]
files_hint: ["src/act_verifier/models.py", "src/act_verifier/loaders.py", "src/act_verifier/checks.py", "tests/test_loaders.py", "tests/test_checks.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "todo"
step: "—"
---

# T17 — Cite the КБ-2в sheet title as found, not the literal «КБ-2в»

## Origin

Review follow-up: finding 3 in [_review/review-2026-11-26.md](../_review/review-2026-11-26.md) (verdict **Fix now**). The finding cites the files and lines; open it for the full text.

## What

- `Act` keeps the КБ-2в sheet title the loader actually found (prefix match, e.g. «КБ-2в акт 3»).
- C05 sheet-level sources, C12 source and `Report.skipped_rows` use that title (ADR-0003: provenance as found).

## Acceptance criteria

Satisfies AC-03, AC-09 — full text: [spec.md](../spec.md) §5.

## Definition of Done

- [ ] an act whose sheet is «КБ-2в акт 3» is cited with that title in every source and in skipped rows
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
