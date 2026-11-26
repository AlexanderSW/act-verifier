---
id: T23
title: "Name a duplicated contract code as a code, with its own InputError kind"
layer: "infra"
deps: []
blocks: []
acs: []
files_hint: ["src/act_verifier/models.py", "src/act_verifier/loaders.py", "src/act_verifier/cli.py", "tests/test_models.py", "tests/test_loaders.py", "tests/test_cli_unit.py", "docs/features/cli-verifier/data-model.md", "docs/features/cli-verifier/contracts/cli.md", "docs/features/cli-verifier/adr/0002-signal-input-errors-with-typed-exception.md"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "todo"
step: "—"
---

# T23 — Name a duplicated contract code as a code, with its own InputError kind

## Origin

Review follow-up: new finding 2 in [_review/review-2026-11-26-2.md](../_review/review-2026-11-26-2.md) (verdict **Fix now**, owner chose «own InputError kind (duplicate_code)»).

## What

- `InputError.KINDS` gains `duplicate_code`; `load_contract` raises it for a repeated «Шифр» (code, file, sheet, rows).
- `cli._message`: «файл <f>, аркуш «<s>»: шифр «<code>» повторюється в рядках <rows>; не береться ні перший, ні останній рядок.» Outcome code 3, no report.
- Docs: ADR-0002 kind set (amendment note), `contracts/cli.md` §4 table row, `data-model.md` constraint.

## Acceptance criteria

No AC — message wording vs `docs/checks.md:91-92` (review stage 2). Outcome code 3 is unchanged.

## Definition of Done

- [ ] the command prints the code-wording message, exits 3, writes no report (test in `tests/test_cli_unit.py`)
- [ ] `.venv/Scripts/python -m pytest -q` green
- [ ] the `CLAUDE.md` rules still hold (Decimal only, missing data → unknown, read-only inputs)
