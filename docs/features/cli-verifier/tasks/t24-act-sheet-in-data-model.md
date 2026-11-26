---
id: T24
title: "List Act.sheet in data-model.md"
layer: "docs"
deps: []
blocks: []
acs: []
files_hint: ["docs/features/cli-verifier/data-model.md"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "todo"
step: "—"
---

# T24 — List Act.sheet in data-model.md

## Origin

Review follow-up: new finding 3 in [_review/review-2026-11-26-2.md](../_review/review-2026-11-26-2.md) (verdict **Fix now**).

## What

- Add the row `sheet | str | required | КБ-2в sheet title as found by prefix (ADR-0003)` to the `Act` table.

## Acceptance criteria

No AC — documentation alignment (review stage 2).

## Definition of Done

- [ ] the `Act` table matches `models.py`
- [ ] `.venv/Scripts/python -m pytest -q` green
