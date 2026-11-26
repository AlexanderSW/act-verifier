---
id: T7
title: "Implement row checks C01–C06, C11 with skip rules and previous-acts completeness"
layer: "app"
deps: ["T1"]
blocks: ["T8"]
acs: ["AC-02", "AC-04", "AC-05", "AC-10", "AC-11"]
files_hint: ["src/act_verifier/checks.py", "tests/test_checks.py"]
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

# T7 — Implement row checks C01–C06, C11 with skip rules and previous-acts completeness

## Place in the sequence

- **Blocked by:** T1 — models · **Blocks:** T8 — act checks + verify · **Wave:** 2 (pure functions over hand-built `Act` objects — parallel with the loaders T4–T6 and report T9).
- **Lane:** shares `src/act_verifier/checks.py` and `tests/test_checks.py` with T8 — serialized (T7 first).

## Why (user story)

> **As an** accepting person
> **I want** every report to end with an evidence block that lists what was checked, what was not and why, and which file, sheet and row each number came from
> **So that** I can decide on the act without re-checking the arithmetic by hand
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task produces every per-position finding (pass included) and every per-position skip record, and computes previous-acts completeness once for C05 here and C13 in T8.

## Inlined context

> | C01_position_in_contract | Шифр позиції є в договірній ціні | точний збіг шифру |
> | C02_unit_matches | Одиниця виміру = договірна | точний збіг після `strip()` |
> | C03_price_matches_contract | Ціна за одиницю = договірна | 0,00 грн |
> | C04_amount_arithmetic | Вартість = кількість × ціна | ±0,01 грн |
> | C05_within_remaining_volume | Кількість ≤ договір − Σ попередніх актів | 0 |
> | C06_no_duplicate_positions | Шифр трапляється в акті один раз | — |
> | C11_required_values_present | Кількість, ціна, вартість заповнені | — |
> Правила пропуску: якщо C01 = `fail`, перевірки C02, C03, C05 для рядка не виконуються (нема з чим звіряти); якщо C11 = `unknown`, перевірки, яким бракує значення (C03, C04), не виконуються.
>
> — `docs/checks.md, Перевірки рядків КБ-2в, abridged (column «Джерело еталона» dropped)` · full text: [checks.md](../../../checks.md)

> S->>S: count K distinct previous act numbers within 1 to N-1
> alt previous acts are not exactly 1 to N-1 (fewer or none, duplicate, outside 1 to N-1, or a number not readable): mark C05 of every position and C13 unknown with the reason, e.g. «previous acts supplied: K of N-1»
> else: remaining volume = contract quantity minus sum of that position in previous acts (repeated codes summed); act quantity exceeds remaining volume → C05 fail, expected remaining volume, actual act quantity, sources contract price and each previous act; quantity of that position empty in a previous act → C05 of that position unknown
> loop each position: quantity empty → C11 unknown, C04 and C05 not checked; price empty → C11 unknown, C03 and C04 not checked with reason «empty price», no substituted price; amount empty → C11 unknown, C04 not checked, C07 unknown naming the position
>
> — `sad.md §6, F4 steps 3–12, abridged` · full text: [sad.md](../sad.md)

> Previous acts: an empty quantity of a position in a previous act makes C05 of that position `unknown`; a position code repeated within one previous act is summed (C06 applies to the current act only).
>
> — `spec.md §1, clarify decisions, verbatim` · full text: [spec.md](../spec.md)

> **Hard rule:** Гроші й обсяги — тільки `Decimal`. Бракує даних → статус `unknown`, ніколи не `pass`. | Determinism | findings sorted by (row order, check ID); no timestamps in findings or evidence block |
>
> — `CLAUDE.md, Правила + sad.md §8, Determinism, abridged` · full text: [CLAUDE.md](../../../../CLAUDE.md) · [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read [docs/checks.md](../../../checks.md), [spec.md](../spec.md) §1/§5 and [sad.md](../sad.md) §6 F4 in full. Do not guess.

## Data delta

No DB changes. Emits `Finding(check, status, code, expected, actual, message, sources)` and `Skipped(check, code, reason)` (T1). Reasons are Ukrainian text (spec §1 clarify: «empty price» = «порожня ціна»).

— `data-model.md §Entities, Finding + Skipped, abridged` · full text: [data-model.md](../data-model.md)

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-02 — happy path (multiple discrepancies)

> **Given** a current act with three discrepancies at once — a non-contract price on one position, an overrun of remaining volume on another, and a КБ-3 certificate that disagrees with the КБ-2в totals (reference scenario «combo_three_errors»)
> **When** the project owner runs the verifier
> **Then** the verifier reports all three findings with status fail, each with its expected and actual value, does not stop at the first one, and reports verdict fail with outcome code 1
>
> — `spec.md §5, AC-02, verbatim` · full text: [spec.md](../spec.md)

### AC-04 — domain invariant (missing data is never pass)

> **Given** a current act where one position has an empty unit price but a filled amount (reference scenario «missing_price»)
> **When** the project owner runs the verifier
> **Then** the verifier reports that position's required-values check as unknown, lists its price and arithmetic checks under «not checked» with the reason «empty price» instead of reporting them as findings, and reports verdict needs_review with outcome code 2 — never pass and never a substituted price
>
> — `spec.md §5, AC-04, verbatim` · full text: [spec.md](../spec.md)

### AC-05 — domain invariant (what each missing value suppresses)

> **Given** a current act where a position has an empty quantity, an empty price or an empty amount
> **When** the project owner runs the verifier
> **Then** an empty quantity leaves the arithmetic and remaining-volume checks of that position not checked; an empty price leaves the price and arithmetic checks not checked; an empty amount leaves the arithmetic check not checked and makes the subtotal check unknown, naming the position whose amount is missing — a formula cell without a stored value counts as empty; in every case the required-values check is unknown and the verdict is at best needs_review (new generator scenarios with an empty quantity and an empty amount)
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

### AC-10 — cross-context (remaining volume from previous acts)

> **Given** a contract price, the complete set of previous acts, and a current act where one position's quantity exceeds the contracted quantity minus the sum of that position in previous acts (reference scenario «volume_overrun»)
> **When** the project owner runs the verifier
> **Then** the verifier reports the remaining-volume check for that position as fail, with the remaining volume as the expected value and the act quantity as the actual value, citing the contract price and each previous act as sources
>
> — `spec.md §5, AC-10, verbatim` · full text: [spec.md](../spec.md)

### AC-11 — cross-context (incomplete previous acts)

> **Given** a current act numbered N and a set of previous acts that is not exactly acts 1…N−1 (fewer files including none, a duplicate number, a number outside 1…N−1 including N itself, or an act number that cannot be read) (new reference scenario with incomplete previous acts)
> **When** the preparing agent runs the verifier
> **Then** the remaining-volume check of every position and the cumulative КБ-3 check are unknown with the reason «previous acts supplied: K of N−1», where K counts distinct act numbers within 1…N−1 (or «act number not readable» when the current act's N is unknown, «previous act number not readable» naming the file, «duplicate previous act number M», or «previous act number M outside 1…N−1»), all other checks still run, and the verdict is at best needs_review with outcome code 2 — never pass
>
> — `spec.md §5, AC-11, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `previous_completeness(act, previous_acts) -> str | None`: `None` when previous numbers are exactly {1…N−1} with no duplicates; else the AC-11 reason (precedence: current N unknown → previous number unreadable → duplicate → out of range → «K of N−1») — `src/act_verifier/checks.py`
- [ ] `check_rows(act, contract, previous_acts, completeness) -> (findings, skipped)`: per row in `row_no` order — C11; C01 (fail → skip C02, C03, C05 with reason); C02 (`strip()`); C03 (price empty → skip «порожня ціна»); C04 (qty/price/amount empty → skip); C05 (qty empty → skip; completeness reason → `unknown`; any previous qty of that code empty → `unknown`; else `qty ≤ contract.qty − Σ previous`); C06 (code count > 1 → fail on that code) — `src/act_verifier/checks.py`
- [ ] Every performed check emits a `Finding`, **pass included**, with `expected`/`actual` as strings of the Decimals read and `sources` (C05: contract source + each previous act's sources for that code) — `src/act_verifier/checks.py`
- [ ] Tests with hand-built `Act`/`ContractPosition` objects (no xlsx): each skip rule → exact `Skipped(check, code, reason)`; `volume_overrun` numbers (contract 1200, previous 410.5 + 455, act 350 → expected 334.5); each AC-11 variant reason; C06 on a duplicate code — `tests/test_checks.py`

## Edge cases

| Case | Behaviour |
|---|---|
| C01 fail and price empty on the same row | C02, C03, C05 skipped for C01; C04 still runs if qty/price/amount present, else skipped; C11 `unknown` |
| N = 1, no previous acts | complete (1…0 is empty) → C05 computed against the contract only |
| previous act contains act N itself | «previous act number N outside 1…N−1» |
| tolerance | C03: exact 0,00; C04: `abs(qty×price − amount) ≤ 0.01` after quantizing to 0.01 `ROUND_HALF_UP`; C05: 0 |
| C06 duplicate rows | one `fail` finding per duplicated code (fixture `duplicate_position` expects one) |

## Definition of Done

- [ ] `tests/test_checks.py` (row part) passes
- [ ] no `float` in `checks.py`; no check reports `pass` on a `None` operand
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
