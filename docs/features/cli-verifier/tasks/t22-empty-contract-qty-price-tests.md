---
id: T22
title: "Pin the empty contract quantity/price rule with tests"
layer: "tests"
deps: []
blocks: []
acs: []
files_hint: ["tests/test_checks.py", "tests/test_loaders.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "done"
step: "COMMIT"
---

# T22 — Pin the empty contract quantity/price rule with tests

## Origin

Review follow-up: new finding 1 in [_review/review-2026-11-26-2.md](../_review/review-2026-11-26-2.md) (verdict **Fix now**). The finding cites the files and lines; open it for the full text.

## What

- Unit tests in `tests/test_checks.py`: `ContractPosition(qty=None)` → C05 `unknown` «у договорі порожня кількість»; `ContractPosition(price=None)` → C03 `unknown` «у договорі порожня ціна»; neither is `pass`; `verify()` verdict `needs_review`.
- `load_contract` test: an empty «Кількість» / «Ціна» cell loads as `None`, not 0.

The behaviour already exists (`checks.py:100-101`, `:151-153`), so the first run is expected green — a characterization test. RED is proven by mutating the code locally (e.g. empty qty treated as 0) and seeing the test fail; the mutation is not committed.

## Acceptance criteria

No AC — CLAUDE.md rule «missing data → unknown, never pass» (review stage 2).

## Definition of Done

- [ ] the tests exist and fail against a mutated rule, pass against the real one
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
