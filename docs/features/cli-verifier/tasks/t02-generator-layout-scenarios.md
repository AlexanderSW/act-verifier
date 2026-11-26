---
id: T2
title: "Add layout map, expected_error and four layout scenarios to the fixture generator"
layer: "tests"
deps: []
blocks: ["T3", "T6"]
acs: ["AC-07", "AC-08", "AC-09", "AC-15"]
files_hint: ["scripts/generate_fixtures.py", "tests/fixtures/", "data/synthetic/", "tests/test_fixtures_integrity.py", "CLAUDE.md"]
owner: "AlexanderSW"
estimate: "M"
context_budget: "M"
status: "todo"
step: ""
---

<!-- Self-contained task. Every inlined chunk carries a provenance signature
`<file> §<section>, <identifier>, verbatim|abridged`. The source always wins over the inline.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file and follow it. Do not invent. -->

# T2 — Add layout map, expected_error and four layout scenarios to the fixture generator

## Place in the sequence

- **Blocked by:** — · **Blocks:** T3 — generator data scenarios, T6 — load_act (its tests read the layout fixtures) · **Wave:** 1 (independent of `src/`: the integrity suite reads xlsx directly with openpyxl).
- **Lane:** shares `scripts/generate_fixtures.py`, `tests/fixtures/`, `tests/test_fixtures_integrity.py`, `CLAUDE.md` with T3 — serialized (T2 first).

## Why (user story)

> **As a** project owner
> **I want** the 14 existing reference scenarios, the new layout scenarios and the expected-input-error scenario to pass, including their outcome codes
> **So that** «done» is verified by tests, not by eye
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task produces, through the generator only, the four layout scenarios (shifted header, totals not right after the table, missing label, ambiguous label) and the reference-file fields they need.

## Inlined context

> **Hard rule:** Не змінювати `expected.json` і xlsx у tests/fixtures вручну, щоб тест «пройшов». Фікстури змінюються тільки через `scripts/generate_fixtures.py`, і з поясненням чому.
>
> — `CLAUDE.md, Правила, verbatim` · full text: [CLAUDE.md](../../../../CLAUDE.md)

> **Chosen:** Option 1 (owner choice). `expected.json` gains an optional `layout` object written only by the generator from the rows it actually used; `test_expected_json_schema` accepts `layout` and `expected_error` (ADR-0002); `read_act_totals` and the contract reader take rows from `layout`, falling back to README rows. [...] The generator commit states the reason (new layout scenarios, CLAUDE.md fixture rule).
>
> — `adr/0004-record-generator-layout-map-in-reference-file.md, Decision outcome, abridged` · full text: [ADR-0004](../adr/0004-record-generator-layout-map-in-reference-file.md)

> - `layout` (optional): per input role, the rows the generator used — e.g. `{"act": {"header_row": 10, "first_data_row": 11, "subtotal_row": 24, "vat_row": 25, "total_row": 26}}`. Absent → README layout.
> - `expected_error` (optional): `{"kind": "missing_label" | "ambiguous_label", "label": "<label as written in spec>"}`. When present, `expected_verdict` and `expected_findings` are absent; the scenario test asserts `InputError` with that kind and label, the command test asserts outcome code 3 and no report files.
>
> — `sad.md §5, Reference-file extensions, verbatim` · full text: [sad.md](../sad.md)

> - shifted header — header row not at the README row; writes a `layout` map (AC-09).
> - totals not right after the table — empty / no-code rows before «Разом без ПДВ»; writes a `layout` map (AC-09).
> - missing label — one layout label absent; `expected_error.kind = missing_label` (AC-07).
> - ambiguous label — a label matching two rows; `expected_error.kind = ambiguous_label` (AC-08).
> Directory names are not fixed upstream; `implement` chooses them in the generator. Synthetic data only.
>
> — `data-model.md §Test fixtures, abridged` · full text: [data-model.md](../data-model.md)

> Open question: Update the expected pre-implementation test state in CLAUDE.md («16 passed, 14 xfailed») once new scenarios exist? Default now: update in the same commit as the generator change, with the reason.
>
> — `spec.md §8, OQ 3, abridged` · full text: [spec.md](../spec.md)

> Integrity helper hard-codes rows 7/9 and breaks on shifted fixtures — Read by the generator's `layout` map, README rows as fallback (ADR-0004).
>
> — `sad.md §11, risk row 3, abridged` · full text: [sad.md](../sad.md)

Current code facts (breakdown-time snapshot): `write_act` puts the header at `HEADER_ROW = 8`, positions from row 9, totals labels in column C («Разом без ПДВ», «ПДВ 20%», «Всього з ПДВ») with values in column G; `main()` hard-codes `inputs` per scenario; `test_expected_json_schema` requires `expected_verdict`; `read_act_totals` uses `min_row=9`.

**Fallback:** insufficient or contradicted by the code → read [ADR-0004](../adr/0004-record-generator-layout-map-in-reference-file.md), [data-model.md](../data-model.md) §ReferenceScenario and `scripts/generate_fixtures.py` in full. Do not guess.

## Data delta

No DB changes. `expected.json` (generator-owned) gains two optional keys:

| Key | Type | Constraints | Change |
|---|---|---|---|
| `expected_verdict` | `str` | absent when `expected_error` present | altered (now conditional) |
| `expected_findings` | `list[{code, check, status}]` | absent when `expected_error` present | altered (now conditional) |
| `layout` | object, optional | per input role: `header_row`, `first_data_row`, `subtotal_row`, `vat_row`, `total_row`; absent → README layout | added |
| `expected_error` | `{kind, label}`, optional | `kind ∈ {missing_label, ambiguous_label}`; label as written in spec | added |

— `data-model.md §Entities, ReferenceScenario, abridged` · full text: [data-model.md](../data-model.md)

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-07 — error (missing layout label)

> **Given** an input file in which a layout label cannot be found — for the contract price: the sheet «Договірна ціна» and the header columns «Шифр», «Найменування», «Од. виміру», «Кількість», «Ціна», «Вартість»; for the current act: the sheets «КБ-2в» and «КБ-3», the same header columns, «Разом без ПДВ», «ПДВ», «Всього з ПДВ» and the four КБ-3 labels («Вартість робіт за звітний період», «ПДВ», «Всього за звітний період», «З початку виконання робіт»); for a previous act: the sheet «КБ-2в», its header columns and «Всього з ПДВ» (new reference scenario with a missing label)
> **When** the employer reviewer runs the verifier
> **Then** it stops with outcome code 3 and a message that names the missing label, the file and the sheet, and produces no verdict; a label that is present but whose value cell is empty is not this case — it is missing data and yields unknown for every check that uses that value; a missing or unreadable act number is likewise missing data (AC-11), not this case
>
> — `spec.md §5, AC-07, verbatim` · full text: [spec.md](../spec.md)

### AC-08 — error (ambiguous layout)

> **Given** an input file in which more than one row matches the same layout label after normalization (new reference scenario with an ambiguous label)
> **When** the employer reviewer runs the verifier
> **Then** it stops with outcome code 3 and a message that names the label and the competing rows, and never silently uses the first match
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

### AC-09 — happy path (shifted layout)

> **Given** an act whose header row sits in a different row than the README describes, or whose totals rows do not follow the table immediately (new reference scenarios), but whose labels match after normalization by prefix — including empty rows or rows without a position code (e.g. a note) between the last position and «Разом без ПДВ»
> **When** the employer reviewer runs the verifier
> **Then** the verifier produces the same verdict and findings as for the equivalent act in the README layout, rows without a position code are not treated as positions, and the evidence block cites the rows where the data was actually found and the rows it skipped
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

### AC-15 — happy path (reference scenarios)

> **Given** the 14 existing reference scenarios plus the seven new generator scenarios (shifted header, totals not right after the table, missing label, ambiguous label, empty quantity, empty amount, incomplete previous acts), all produced by the fixture generator, and a command-level check that points the report location at an input file
> **When** the project owner runs the test suite
> **Then** every scenario passes rather than being marked as an expected failure: verdict scenarios match their expected findings and verdict exactly, the expected-input-error scenarios match their expected error kind (missing label or ambiguous label) and the label as written in this spec (e.g. «Разом без ПДВ»), while other input errors (unreadable workbook, invocation error, overwrite refusal) are checked by outcome code only, each scenario is also run through the command and matches its outcome code (0, 1, 2 or 3), scenarios with outcome code 0, 1 or 2 also produce the evidence block while outcome code 3 produces no report, and the fixture-integrity suite stays green with its reference-file schema extended to accept the new optional expected-error field
>
> — `spec.md §5, AC-15, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Parametrize `write_act` with layout options (extra title rows → header offset; rows inserted between the last position and «Разом без ПДВ»; omit one label; duplicate one label) and make it **return** the rows it used (`header_row`, `first_data_row`, `subtotal_row`, `vat_row`, `total_row`) — `scripts/generate_fixtures.py`
- [ ] Let a scenario tuple carry optional `layout` / `expected_error` / `inputs` overrides; write `layout` only for non-README layouts; omit `expected_verdict`/`expected_findings` when `expected_error` is set — `scripts/generate_fixtures.py`
- [ ] Scenario «shifted header»: `base_act3` with the header moved (e.g. row 11); expected findings `[]`, verdict `pass` (same as `ok_many`) — `scripts/generate_fixtures.py`
- [ ] Scenario «totals not right after the table»: an empty row and a no-code note row (text must not start with any label prefix) before «Разом без ПДВ»; expected findings `[]`, verdict `pass` — `scripts/generate_fixtures.py`
- [ ] Scenario «missing label»: «Разом без ПДВ» row omitted from КБ-2в; `expected_error = {"kind": "missing_label", "label": "Разом без ПДВ"}` — `scripts/generate_fixtures.py`
- [ ] Scenario «ambiguous label»: a second row below the header whose text starts with «ПДВ»; `expected_error = {"kind": "ambiguous_label", "label": "ПДВ"}` — `scripts/generate_fixtures.py`
- [ ] Integrity suite: schema accepts `layout` + `expected_error` (and requires exactly one of verdict-block / `expected_error`); `read_act_totals` and the contract reader take rows from `layout`, README rows as fallback; add an arithmetic-consistency test for each `layout` fixture — `tests/test_fixtures_integrity.py`
- [ ] Run `.venv/Scripts/python scripts/generate_fixtures.py`; confirm the 14 existing `expected.json` files are byte-identical (`git diff --stat tests/fixtures`)
- [ ] Update the expected pre-implementation state in `CLAUDE.md` to the measured counts (expected shape: passed = 18 schema cases + the 2 existing `ok_many` tests + the new layout-consistency tests; xfailed = 18, since `load_contract` still raises `NotImplementedError` first) with a one-line reason — `CLAUDE.md`

## Edge cases

| Case | Behaviour |
|---|---|
| `test_verifier.py` on an `expected_error` fixture | still xfail: `load_contract` raises `NotImplementedError` before `expected_findings` is read — do **not** touch `test_verifier.py` here (T11 owns it) |
| re-running the generator | deterministic: identical bytes for every fixture (generator docstring) |
| note row text in «totals gap» scenario | starts with none of «Разом без ПДВ», «ПДВ», «Всього з ПДВ» — otherwise it becomes an ambiguity |
| `data/synthetic/*` | rewritten by `main()`; must stay byte-identical (integrity tests read them) |

## Definition of Done

- [ ] `.venv/Scripts/python -m pytest -q tests/test_fixtures_integrity.py` green, including the new layout-fixture consistency tests
- [ ] full suite shows exactly the new state written into `CLAUDE.md`; no existing fixture changed
- [ ] commit message states the reason (new layout scenarios, CLAUDE.md fixture rule)
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
