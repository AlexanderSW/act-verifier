---
id: T8
title: "Implement act checks C07–C10, C12, C13 and assemble verify()"
layer: "app"
deps: ["T7"]
blocks: ["T11", "T12"]
acs: ["AC-01", "AC-02", "AC-05", "AC-11", "AC-12", "AC-16"]
files_hint: ["src/act_verifier/checks.py", "tests/test_checks.py"]
owner: "AlexanderSW"
estimate: "M"
context_budget: "M"
status: "done"
step: "COMMIT"
---

<!-- Self-contained task. Every inlined chunk carries a provenance signature
`<file> §<section>, <identifier>, verbatim|abridged`. The source always wins over the inline.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file and follow it. Do not invent. -->

# T8 — Implement act checks C07–C10, C12, C13 and assemble verify()

## Place in the sequence

- **Blocked by:** T7 — row checks + completeness · **Blocks:** T11 — scenario tests, T12 — cli.main · **Wave:** 3.
- **Lane:** shares `src/act_verifier/checks.py` and `tests/test_checks.py` with T7 — serialized (after T7).

## Why (user story)

> **As a** project owner
> **I want** to run the verifier on a contract price, the previous acts and the current act
> **So that** I get the verdict, a findings report and an evidence block from one command
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

This task adds the totals and КБ-3 checks and the `verify()` entry point that returns the complete `Report`.

## Inlined context

> | C07_subtotal | «Разом без ПДВ» = Σ вартостей рядків | ±0,01 грн |
> | C08_vat | ПДВ = 20% від «Разом без ПДВ» | ±0,01 грн |
> | C09_total_with_vat | «Всього з ПДВ» = Разом + ПДВ | ±0,01 грн |
> | C10_kb3_matches_kb2v | КБ-3 «Всього за звітний період» = КБ-2в «Всього з ПДВ» | ±0,01 грн |
> | C12_act_not_empty | В акті є хоча б одна позиція (інакше `warning`) | — |
> | C13_kb3_cumulative | КБ-3 «З початку виконання» = Σ «Всього з ПДВ» попередніх актів + поточний | ±0,01 грн |
>
> — `docs/checks.md, Перевірки підсумків і КБ-3, verbatim` · full text: [checks.md](../../../checks.md)

> Totals checks compare against the values printed in the act: C08 uses the printed «Разом без ПДВ», C09 the printed subtotal and VAT, C10 the printed КБ-2в «Всього з ПДВ», C13 Σ printed КБ-2в «Всього з ПДВ» of previous acts + the current КБ-2в «Всього з ПДВ».
>
> — `spec.md §1, derived from the fixtures, verbatim` · full text: [spec.md](../spec.md)

> An empty printed total makes `unknown` every check that uses it, naming the value: «Разом без ПДВ» → C07, C08, C09; «ПДВ» → C08, C09; «Всього з ПДВ» → C09, C10, C13; КБ-3 period total → C10; КБ-3 cumulative total → C13; a previous act's «Всього з ПДВ» → C13.
>
> — `spec.md §1, clarify decisions, verbatim` · full text: [spec.md](../spec.md)

> «Кожна перевірка повертає Finding і для pass теж: звіт має показати, що саме перевірено, а не лише що знайдено.» / «Не зупиняється на першій помилці: сценарій combo_three_errors очікує всі три знахідки.»
>
> — `src/act_verifier/checks.py, module + verify() docstrings, verbatim` · full text: `src/act_verifier/checks.py`

> | Determinism | findings sorted by (row order, check ID); no timestamps in findings or evidence block |
>
> — `sad.md §8, Crosscutting concepts, verbatim` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read [docs/checks.md](../../../checks.md), [spec.md](../spec.md) §1 and [sad.md](../sad.md) §6 F1/F4. Do not guess.

## Data delta

No DB changes. `verify()` returns `Report(findings, skipped, inputs…)` (T1): findings incl. pass, `Skipped` records, and the input `Source`s the evidence block needs.

— `data-model.md §Entities, Report, abridged` · full text: [data-model.md](../data-model.md)

## API contract

Internal — no API surface. `verify(act, contract, previous_acts) -> Report` keeps its signature (`sad.md §2, Organisational, abridged`).

## Acceptance criteria

### AC-01 — happy path

> **Given** a project owner has a contract price, the complete set of previous acts and a current act with no discrepancies (reference scenario «ok_many»)
> **When** the project owner runs the verifier on them
> **Then** the verifier reports verdict pass with outcome code 0, produces a findings report that lists every check applied to every position and to the act — including the passing ones — and ends the report with the evidence block
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-02 — happy path (multiple discrepancies)

> **Given** a current act with three discrepancies at once — a non-contract price on one position, an overrun of remaining volume on another, and a КБ-3 certificate that disagrees with the КБ-2в totals (reference scenario «combo_three_errors»)
> **When** the project owner runs the verifier
> **Then** the verifier reports all three findings with status fail, each with its expected and actual value, does not stop at the first one, and reports verdict fail with outcome code 1
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

### AC-05 — domain invariant (what each missing value suppresses)

> **Then** [...] an empty amount leaves the arithmetic check not checked and makes the subtotal check unknown, naming the position whose amount is missing [...]
>
> — `spec.md §5, AC-05, abridged (C07 part; full text in T7)` · full text: [spec.md](../spec.md)

### AC-11 — cross-context (incomplete previous acts)

> **Then** the remaining-volume check of every position and the cumulative КБ-3 check are unknown with the reason «previous acts supplied: K of N−1» [...], all other checks still run, and the verdict is at best needs_review with outcome code 2 — never pass
>
> — `spec.md §5, AC-11, abridged (C13 part; full text in T7)` · full text: [spec.md](../spec.md)

### AC-12 — cross-context (КБ-3 against КБ-2в)

> **Given** a current act whose КБ-3 «Всього за звітний період» differs from its КБ-2в «Всього з ПДВ» while the cumulative КБ-3 total equals the printed «Всього з ПДВ» of previous acts plus the current КБ-2в «Всього з ПДВ» (reference scenario «kb3_mismatch»)
> **When** the project owner runs the verifier
> **Then** the verifier reports only the КБ-3-matches-КБ-2в check as fail and the cumulative check as pass — totals checks compare against the values printed in the act, not against recomputed ones
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

### AC-16 — domain invariant (empty act)

> **Given** a current act with no positions (reference scenario «empty_act»)
> **When** the project owner runs the verifier
> **Then** the verifier reports the act-not-empty check as warning and verdict needs_review with outcome code 2 — an empty act is never accepted silently
>
> — `spec.md §5, AC-16, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] C07: any row amount `None` → `unknown` naming those codes; printed subtotal `None` → `unknown` naming «Разом без ПДВ»; else `|Σ amounts − subtotal| ≤ 0.01` — `src/act_verifier/checks.py`
- [ ] C08 `|subtotal × 0.20 − vat|`, C09 `|subtotal + vat − total|`, C10 `|kb3_period_total − total|` — all on **printed** values; a `None` operand → `unknown` naming the value — `src/act_verifier/checks.py`
- [ ] C12: `len(act.rows) == 0` → `warning`, else `pass` — `src/act_verifier/checks.py`
- [ ] C13: completeness reason (T7) → `unknown` with it; any previous `total` or current `total` / `kb3_cumulative_total` `None` → `unknown` naming it; else `|Σ previous total + total − kb3_cumulative_total| ≤ 0.01` — `src/act_verifier/checks.py`
- [ ] `verify()`: completeness once → row checks (T7) → act checks; collect all findings (pass incl.), sort by (row order, check ID) with act-level after rows; fill `Report.skipped` and input sources — `src/act_verifier/checks.py`
- [ ] Tests on hand-built acts: each check pass/fail/unknown; `kb3_mismatch` numbers → C10 fail, C13 pass; empty act → only C12 warning among non-pass; two `verify()` calls give equal reports — `tests/test_checks.py`

## Edge cases

| Case | Behaviour |
|---|---|
| empty act (no rows) | C07 Σ = 0 vs printed subtotal 0 → pass; C12 warning → verdict needs_review |
| `subtotal_mismatch` fixture | only C07 fails: C08–C10, C13 use the printed (wrong) subtotal consistently → pass |
| VAT tolerance | 20% of printed subtotal quantized to 0.01 `ROUND_HALF_UP`, compare ±0.01 |
| act-level finding `code` | `None` |

## Definition of Done

- [ ] `tests/test_checks.py` passes (row + act parts)
- [ ] `verify()` never raises on `None` values; no `pass` on a `None` operand; no `float`
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
