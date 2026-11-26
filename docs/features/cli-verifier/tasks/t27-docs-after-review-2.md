---
id: T27
title: "Align the ER diagram, the sync report and the cli.md changelog with the review-2 changes"
layer: "docs"
deps: []
blocks: []
acs: []
files_hint: ["docs/features/cli-verifier/data-model.md", "docs/features/cli-verifier/contracts/api-sync-report.md", "docs/features/cli-verifier/contracts/cli.md"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "done"
step: "COMMIT"
---

# T27 — Align the ER diagram, the sync report and the cli.md changelog with the review-2 changes

## Origin

Review follow-up: new finding 3 in [_review/review-2026-11-26-3.md](../_review/review-2026-11-26-3.md) (verdict **Fix now**).

## What

- `data-model.md` ER diagram: mark `CONTRACT_POSITION` qty/price as nullable, and add `sheet` to `ACT`.
- `contracts/api-sync-report.md`: list `duplicate_code` among the `InputError` kinds.
- `contracts/cli.md`: add a changelog line for the new `duplicate_code` kind.

## Acceptance criteria

No AC — documentation matches the code (ADR-0002 amendment).

## Definition of Done

- [ ] the docs match `models.py` and `loaders.py`
- [ ] `.venv/Scripts/python -m pytest -q` is green
