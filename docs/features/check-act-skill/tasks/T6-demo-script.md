---
id: T6
title: "Write the demo script demo.md for the three scenarios, with empty actual-result fields"
layer: "docs"
deps: []
blocks: ["T8"]
acs: ["AC-12"]
files_hint: ["docs/features/check-act-skill/demo.md"]
owner: "AlexanderSW"
estimate: "S"           # ~1 h
context_budget: "S"     # 33 inlined lines, 1 extra file (tests/fixtures/combo_three_errors/expected.json)
status: "todo"
step: ""
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T6 — Write the demo script demo.md for the three scenarios, with empty actual-result fields

## Place in the sequence

- **Blocked by:** — · **Blocks:** T8 — demo rehearsal · **Wave:** 1 (written from the spec; needs no skill code).
- **Lane:** own lane in wave 1; `demo.md` is shared with T8 later (T8 depends on it anyway). Parallel with T1 and T7.

## Why (user story)

> **As the** project owner
> **I want** a demo script giving, for each of the three demo scenarios, the prompt, the expected behaviour of the L1 agent, its own report folder and a field for the actual result
> **So that** I can rehearse before the interview and show what actually happened
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task writes the script; T8 fills the actual-result fields.

## Inlined context

> | Numbers outside the report | 0 per reply | each numeric value in the reply looked up in that run's report or evidence block; result written in the demo document |
> | Input files unchanged | 0 changed input files (contract price, previous acts 1–2, the three demo acts) | a file hash of each input taken before and after the rehearsal, both written in the demo document |
> | Reply turnaround per demo scenario | ≤ 2 min from the prompt to the finished reply | stopwatch at the rehearsal, written in the demo document; an overrun is recorded as a deviation, not a blocker |
> | Permission prompts during the demo | 0 unplanned prompts (a prompt written into the demo document as an expected step is planned) | count at the rehearsal |
>
> — `spec.md §6, NFR rows 3–6, abridged` · full text: [spec.md](../spec.md)

> **Red-line violations** (a number not in the report, a claim of acceptance, an edited input file, an unasked journal entry, a finding taken from a stale report) — measurement plan: a five-item checklist filled in the «actual result» field of each scenario, target: 0 across the three runs.
>
> — `spec.md §7, KPI 2, abridged`

> `demo.md` — three scenarios: prompt, expected, report folder, actual, input hashes before/after, stopwatch, red-line checklist. `reports/demo/<scenario>/` — one report folder per demo scenario (gitignored).
>
> — `sad.md §5, Internal decomposition, abridged` · full text: [sad.md](../sad.md)

Inputs (repo paths): contract `data/synthetic/contract_boq.xlsx`; previous acts `data/synthetic/act_01_2026-09.xlsx`, `data/synthetic/act_02_2026-10.xlsx`; acts `tests/fixtures/{ok_many,combo_three_errors,missing_label}/act_03.xlsx` — `tests/test_cli_unit.py:14-16, abridged`. README «Сценарії»: combo_three_errors → fail (C03, C05, C10); missing_label → code 3, no «Разом без ПДВ».

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-12 (US-06) — happy path

> **Given** the demo document `docs/features/check-act-skill/demo.md` for the three demo scenarios «ok_many», «combo_three_errors» and «missing_label»
> **When** the project owner rehearses the demo
> **Then** for each scenario the document gives the prompt — naming the contract price, previous acts 1 and 2 and the act explicitly — the expected behaviour (verdict pass with no claim of acceptance; three discrepancies whose numbers match the report; «перевірки не було» naming «Разом без ПДВ», with the act file unchanged), its own report folder and an «actual result» field; after the rehearsal all three fields hold what the L1 agent actually did, deviations included
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Create `docs/features/check-act-skill/demo.md` (Ukrainian prose): preparation (fresh Claude Code session at repo root, `sha256sum` of the 6 input files into a «до» table).
- [ ] One section per scenario: prompt naming all four inputs and `reports/demo/<scenario>/`; expected behaviour per AC-12; planned steps (permission prompt only if `allowed-tools` fails — ADR-0002 fallback); empty fields «Фактичний результат», «Час відповіді», «Запити дозволів», five-item red-line checklist.
- [ ] Expected numbers for combo_three_errors are not written by hand — the script says «числа мають збігатися зі звітом цього запуску».
- [ ] Closing table «після» for the hashes + `git status` check of `journal/agent_errors.csv`.

## Edge cases

| Case | Behaviour |
|---|---|
| All acts are named `act_03.xlsx` | each scenario has its own `--out` folder (AC-09) |
| Rehearsal overruns 2 min | recorded as a deviation, not a blocker |
| A permission prompt appears | counted and recorded as a deviation |

## Definition of Done

- [ ] `demo.md` exists with three scenario sections, each holding prompt, expected behaviour, report folder and empty actual-result / stopwatch / prompts / checklist fields, plus before/after hash tables
- [ ] no number in `demo.md` that is not in an input path, the spec or the fixtures
- [ ] `.venv/Scripts/python -m pytest -q` unchanged (docs only)
