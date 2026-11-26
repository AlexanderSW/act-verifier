---
id: T21
title: "Align ContractPosition types and record the duplicate-code rule"
layer: "docs"
deps: ["T17"]
blocks: []
acs: []
files_hint: ["src/act_verifier/models.py", "docs/features/cli-verifier/data-model.md", "docs/checks.md"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "todo"
step: "—"
---

# T21 — Align ContractPosition types and record the duplicate-code rule

## Origin

Review follow-up: finding 7 in [_review/review-2026-11-26.md](../_review/review-2026-11-26.md) (verdict **Fix now**). The finding cites the files and lines; open it for the full text.

## What

- `ContractPosition.qty/price` typed `Decimal | None` (an empty contract cell is read as None).
- Record in data-model.md and docs/checks.md: a duplicate code in the contract is an input error (code 3) naming the rows.

## Acceptance criteria

No AC — documentation/type alignment (review stage 2).

## Definition of Done

- [ ] types match what the loader stores; the duplicate-code rule appears in both documents
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
