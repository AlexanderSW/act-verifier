---
id: T11
title: "Turn the scenario tests green: drop xfail, assert expected_error and layout rows"
layer: "tests"
deps: ["T3", "T6", "T8", "T9"]
blocks: []
acs: ["AC-01", "AC-02", "AC-04", "AC-09", "AC-10", "AC-15"]
files_hint: ["tests/test_verifier.py", "CLAUDE.md"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "M"
status: "todo"
step: ""
---

<!-- Self-contained task. Every inlined chunk carries a provenance signature
`<file> §<section>, <identifier>, verbatim|abridged`. The source always wins over the inline.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file and follow it. Do not invent. -->

# T11 — Turn the scenario tests green: drop xfail, assert expected_error and layout rows

## Place in the sequence

- **Blocked by:** T3 — all 21 fixtures, T6 — load_act, T8 — verify, T9 — evidence block · **Blocks:** — · **Wave:** 5 (needs the whole read → verify → render core).
- **Lane:** shares `CLAUDE.md` with T2/T3 (both finished by then) — otherwise own lane.

## Why (user story)

> **As a** project owner
> **I want** the 14 existing reference scenarios, the new layout scenarios and the expected-input-error scenario to pass, including their outcome codes
> **So that** «done» is verified by tests, not by eye
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task makes every reference scenario pass at the core level (loaders + verify), including the input-error and layout scenarios.

## Inlined context

> Готово = усі сценарії в test_verifier.py зелені (не xfail) і test_fixtures_integrity.py зелений.
>
> — `CLAUDE.md, Як перевіряти свою роботу, verbatim` · full text: [CLAUDE.md](../../../../CLAUDE.md)

> Scenario tests stay `xfail(strict=False)` and silently become «xpassed», not «passed» — Remove the xfail marker in the same change that makes them green (CLAUDE.md «Готово» = not xfail).
>
> — `sad.md §11, risk row 2, abridged` · full text: [sad.md](../sad.md)

> `expected_error` (optional): `{"kind": "missing_label" | "ambiguous_label", "label": "<label as written in spec>"}`. When present, `expected_verdict` and `expected_findings` are absent; the scenario test asserts `InputError` with that kind and label [...]
> Scenario tests for shifted layouts assert that the evidence block's cited rows equal the `layout` rows.
>
> — `sad.md §5, Reference-file extensions + adr/0004, Decision outcome, abridged` · full text: [sad.md](../sad.md) · [ADR-0004](../adr/0004-record-generator-layout-map-in-reference-file.md)

Current test (breakdown-time snapshot): `test_scenario` is `@pytest.mark.xfail(raises=NotImplementedError, strict=False)`, loads contract → previous → act, calls `verify`, compares `non_pass(report)` (set of `(code, check, status)`) to `expected_findings` and `report.verdict` to `expected_verdict`.

**Fallback:** insufficient or contradicted by the code → read `tests/test_verifier.py`, [ADR-0004](../adr/0004-record-generator-layout-map-in-reference-file.md) and [spec.md](../spec.md) AC-15. Do not guess.

## Data delta

No DB changes. Reads `expected.json` keys `expected_findings`, `expected_verdict`, `expected_error`, `layout` (read-only; never edited by hand).

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-01 — happy path

> **Given** a project owner has a contract price, the complete set of previous acts and a current act with no discrepancies (reference scenario «ok_many»)
> **When** the project owner runs the verifier on them
> **Then** the verifier reports verdict pass with outcome code 0, produces a findings report that lists every check applied to every position and to the act — including the passing ones — and ends the report with the evidence block
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-02 — happy path (multiple discrepancies)

> **Given** a current act with three discrepancies at once [...] (reference scenario «combo_three_errors»)
> **Then** the verifier reports all three findings with status fail, each with its expected and actual value, does not stop at the first one, and reports verdict fail with outcome code 1
>
> — `spec.md §5, AC-02, abridged` · full text: [spec.md](../spec.md)

### AC-04 — domain invariant (missing data is never pass)

> **Given** a current act where one position has an empty unit price but a filled amount (reference scenario «missing_price»)
> **Then** the verifier reports that position's required-values check as unknown, lists its price and arithmetic checks under «not checked» with the reason «empty price» instead of reporting them as findings, and reports verdict needs_review with outcome code 2 — never pass and never a substituted price
>
> — `spec.md §5, AC-04, abridged` · full text: [spec.md](../spec.md)

### AC-09 — happy path (shifted layout)

> **Then** the verifier produces the same verdict and findings as for the equivalent act in the README layout, rows without a position code are not treated as positions, and the evidence block cites the rows where the data was actually found and the rows it skipped
>
> — `spec.md §5, AC-09, abridged (Then part)` · full text: [spec.md](../spec.md)

### AC-10 — cross-context (remaining volume from previous acts)

> **Given** [...] (reference scenario «volume_overrun»)
> **Then** the verifier reports the remaining-volume check for that position as fail, with the remaining volume as the expected value and the act quantity as the actual value, citing the contract price and each previous act as sources
>
> — `spec.md §5, AC-10, abridged` · full text: [spec.md](../spec.md)

### AC-15 — happy path (reference scenarios)

> **Then** every scenario passes rather than being marked as an expected failure: verdict scenarios match their expected findings and verdict exactly, the expected-input-error scenarios match their expected error kind (missing label or ambiguous label) and the label as written in this spec (e.g. «Разом без ПДВ») [...]
>
> — `spec.md §5, AC-15, abridged (core-level part; command part → T13)` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Remove the `xfail` marker from `test_scenario` — `tests/test_verifier.py`
- [ ] Branch on `expected_error`: `pytest.raises(InputError)` around the loads; assert `exc.kind` and `exc.label` equal the reference — `tests/test_verifier.py`
- [ ] For scenarios with `layout`: assert the evidence block (`render_evidence(report)`) cites the `layout` rows for the act (header+1 … last data row, skipped rows) — `tests/test_verifier.py`
- [ ] Add targeted asserts: `ok_many` report contains pass findings for every row check × position; `missing_price` skipped has `5-2` C03 + C04 with «порожня ціна»; `volume_overrun` C05 expected `334.5`/actual `350` with contract + both previous sources — `tests/test_verifier.py`
- [ ] Update `CLAUDE.md` «Очікуваний стан» line to the post-implementation state measured by the suite, with a one-line reason — `CLAUDE.md`

## Edge cases

| Case | Behaviour |
|---|---|
| a scenario xpasses instead of passing | impossible after the marker is removed — the suite must report «passed» |
| `expected_error` scenario loads successfully | test fails (no silent pass) |
| previous acts in `inputs` | loaded with `previous=True` (T6) |

## Definition of Done

- [ ] `.venv/Scripts/python -m pytest -q tests/test_verifier.py` → 21 passed, 0 xfailed
- [ ] `tests/test_fixtures_integrity.py` still green; no fixture changed
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
