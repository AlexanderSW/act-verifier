---
id: T25
title: "List every missing-data unknown under «Не перевірено» with its reason"
layer: "domain"
deps: []
blocks: []
acs: ["AC-03", "AC-05"]
files_hint: ["src/act_verifier/checks.py", "tests/test_checks.py", "tests/test_verifier.py", "tests/test_cli.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "done"
step: "COMMIT"
---

# T25 — List every missing-data unknown under «Не перевірено» with its reason

## Origin

Review follow-up: new finding 1 (stage 1) in [_review/review-2026-11-26-3.md](../_review/review-2026-11-26-3.md) (verdict **Fix now**).

## What

- In `checks.py`, every branch that turns a check `unknown` because an operand is missing also emits `Skipped(check, code, reason)` with the same reason as the finding's message. That covers C05 (empty quantity in a previous act, empty contract quantity), C03 (empty contract price), C07 (empty amount, empty printed subtotal), C08–C10 and C13 (empty printed values). It already does this for the AC-11 completeness reason.
- The T22 assertions `skipped == []` now expect the skip.
- A scenario test (`empty_amount`) and a CLI test show the «Не перевірено» line on stdout naming the position and the reason.

## Acceptance criteria

AC-03 (the evidence block lists every check that was not performed, with the position and the reason); AC-05 (an empty amount makes C07 unknown and names the position).

## Definition of Done

- [ ] the tests fail before the change and pass after it
- [ ] `.venv/Scripts/python -m pytest -q` is green
- [ ] the `CLAUDE.md` rules still hold
