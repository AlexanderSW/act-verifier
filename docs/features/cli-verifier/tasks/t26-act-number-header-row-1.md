---
id: T26
title: "No act number when the КБ-2в header is in row 1"
layer: "infra"
deps: []
blocks: []
acs: ["AC-11"]
files_hint: ["src/act_verifier/loaders.py", "tests/test_loaders.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "done"
step: "COMMIT"
---

# T26 — No act number when the КБ-2в header is in row 1

## Origin

Review follow-up: new finding 2 in [_review/review-2026-11-26-3.md](../_review/review-2026-11-26-3.md) (verdict **Fix now**).

## What

- `_act_number` returns `(None, None)` when `header <= 1`, because there is no title above the table. Today `max_row=0` reaches openpyxl, which treats it as "no limit" and searches the whole sheet.
- Unit test in `tests/test_loaders.py`: a workbook with the header in row 1 and a cell «Акт № 7 …» below the totals loads with `number is None`.

## Acceptance criteria

AC-11 (act number read only from the title above the table; an unreadable number gives C05/C13 unknown).

## Definition of Done

- [ ] the test fails before the change and passes after it
- [ ] `.venv/Scripts/python -m pytest -q` is green
