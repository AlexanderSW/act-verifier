---
id: T3
title: "Add empty-quantity, empty-amount and incomplete-previous-acts scenarios to the generator"
layer: "tests"
deps: ["T2"]
blocks: ["T11", "T13"]
acs: ["AC-05", "AC-11", "AC-15"]
files_hint: ["scripts/generate_fixtures.py", "tests/fixtures/", "data/synthetic/", "tests/test_fixtures_integrity.py", "CLAUDE.md"]
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

# T3 — Add empty-quantity, empty-amount and incomplete-previous-acts scenarios to the generator

## Place in the sequence

- **Blocked by:** T2 — generator layout map + layout scenarios · **Blocks:** T11 — scenario tests, T13 — command tests · **Wave:** 2 (needs T2's per-scenario `inputs` override).
- **Lane:** shares `scripts/generate_fixtures.py`, `tests/fixtures/`, `tests/test_fixtures_integrity.py`, `CLAUDE.md` with T2 — serialized (after T2).

## Why (user story)

> **As a** project owner
> **I want** the 14 existing reference scenarios, the new layout scenarios and the expected-input-error scenario to pass, including their outcome codes
> **So that** «done» is verified by tests, not by eye
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task adds the last three of the seven new generator scenarios — the missing-data ones — so AC-05 and AC-11 are backed by fixtures, not ad-hoc files.

## Inlined context

> **Hard rule:** Фікстури змінюються тільки через `scripts/generate_fixtures.py`, і з поясненням чому.
>
> — `CLAUDE.md, Правила, verbatim` · full text: [CLAUDE.md](../../../../CLAUDE.md)

> Scope extension over brief §7 («2–3 new layout fixtures»): seven new generator scenarios — shifted header, totals not right after the table, missing label, ambiguous label, empty quantity, empty amount, incomplete previous acts — so that every AC is backed by a generator scenario rather than ad-hoc temporary files (the approach the brief rejected).
>
> — `spec.md §1, specify decisions, verbatim` · full text: [spec.md](../spec.md)

> - An empty amount leaves C04 not checked and makes C07 unknown; a formula cell without a stored value counts as empty.
> - Fewer previous acts than the act number implies (or numbers other than 1…N−1) → C05 and C13 are `unknown`, never `pass`.
>
> — `spec.md §1, specify decisions, verbatim` · full text: [spec.md](../spec.md)

> Act number N (current and previous acts) is read only from the КБ-2в title cell whose normalized text begins with «Акт №»; the file name and the КБ-3 «до акта №» text are not used.
>
> — `spec.md §1, clarify decisions, verbatim` · full text: [spec.md](../spec.md)

> якщо C11 = `unknown`, перевірки, яким бракує значення (C03, C04), не виконуються. Пропущені перевірки потрапляють у розділ «що не перевірено» блоку доказів.
>
> — `docs/checks.md, Перевірки рядків КБ-2в / Правила пропуску, verbatim` · full text: [checks.md](../../../checks.md)

Current code facts (breakdown-time snapshot): `expected_findings` lists **non-pass findings only**; skip records are not findings and do not appear there (see `missing_price`: only `C11_required_values_present` `unknown`). `finalize()` computes the subtotal as `Σ (amount or 0)`. Act 3's title is written as `Акт № 3 за … р.` in `A2`.

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md) §1/§5 and `scripts/generate_fixtures.py` in full. Do not guess.

## Data delta

No DB changes. Three new `tests/fixtures/<scenario>/` directories (`act_03.xlsx` + `expected.json`); the incomplete-previous-acts scenario uses the per-scenario `inputs.previous_acts` override from T2.

— `data-model.md §Test fixtures, abridged` · full text: [data-model.md](../data-model.md)

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-05 — domain invariant (what each missing value suppresses)

> **Given** a current act where a position has an empty quantity, an empty price or an empty amount
> **When** the project owner runs the verifier
> **Then** an empty quantity leaves the arithmetic and remaining-volume checks of that position not checked; an empty price leaves the price and arithmetic checks not checked; an empty amount leaves the arithmetic check not checked and makes the subtotal check unknown, naming the position whose amount is missing — a formula cell without a stored value counts as empty; in every case the required-values check is unknown and the verdict is at best needs_review (new generator scenarios with an empty quantity and an empty amount)
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

### AC-11 — cross-context (incomplete previous acts)

> **Given** a current act numbered N and a set of previous acts that is not exactly acts 1…N−1 (fewer files including none, a duplicate number, a number outside 1…N−1 including N itself, or an act number that cannot be read) (new reference scenario with incomplete previous acts)
> **When** the preparing agent runs the verifier
> **Then** the remaining-volume check of every position and the cumulative КБ-3 check are unknown with the reason «previous acts supplied: K of N−1», where K counts distinct act numbers within 1…N−1 (or «act number not readable» when the current act's N is unknown, «previous act number not readable» naming the file, «duplicate previous act number M», or «previous act number M outside 1…N−1»), all other checks still run, and the verdict is at best needs_review with outcome code 2 — never pass
>
> — `spec.md §5, AC-11, verbatim` · full text: [spec.md](../spec.md)

### AC-15 — happy path (reference scenarios)

> **Given** the 14 existing reference scenarios plus the seven new generator scenarios [...], all produced by the fixture generator [...]
> **Then** every scenario passes rather than being marked as an expected failure: verdict scenarios match their expected findings and verdict exactly [...] and the fixture-integrity suite stays green [...]
>
> — `spec.md §5, AC-15, abridged (full text inlined in T2)` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Scenario «empty quantity»: one position of `base_act3` with `qty = None`, amount kept; expected findings `[{code, "C11_required_values_present", "unknown"}]`, verdict `needs_review` (C04, C05 of that position are skip records, not findings) — `scripts/generate_fixtures.py`
- [ ] Scenario «empty amount»: one position with `amount = None`, run through `finalize()` so printed totals are internally consistent; expected findings C11 `unknown` (that code) + `C07_subtotal` `unknown` (code `None`), verdict `needs_review` — `scripts/generate_fixtures.py`
- [ ] Scenario «incomplete previous acts»: `base_act3` (N = 3) with `inputs.previous_acts = ["data/synthetic/act_01_2026-09.xlsx"]` (K = 1 of 2); expected findings `C05_within_remaining_volume` `unknown` for **every** position code of the act + `C13_kb3_cumulative` `unknown` (code `None`), verdict `needs_review` — `scripts/generate_fixtures.py`
- [ ] Make sure the integrity tests that read xlsx tolerate `None` cells in the two empty-value fixtures (e.g. `test_expected_json_schema` only; no arithmetic test assumes all cells filled) — `tests/test_fixtures_integrity.py`
- [ ] Regenerate; confirm all earlier fixtures and `data/synthetic/*` byte-identical (`git diff --stat`)
- [ ] Update `CLAUDE.md` expected pre-implementation state to the measured counts (xfailed = 21) with a one-line reason — `CLAUDE.md`

## Edge cases

| Case | Behaviour |
|---|---|
| empty-amount fixture's printed «Разом без ПДВ» | equals Σ of the filled amounts (`finalize()`); C07 is still `unknown`, never `pass`/`fail`, because one operand is missing |
| incomplete previous acts: C04, C07–C10 | unaffected — «all other checks still run» → pass in this fixture |
| incomplete previous acts: duplicate / out-of-range / unreadable number variants | not separate fixtures in stage 1 (spec lists one scenario) — T7 unit-tests them |
| generator writes `None` | `_num(None)` → empty cell, never 0 |

## Definition of Done

- [ ] `.venv/Scripts/python -m pytest -q tests/test_fixtures_integrity.py` green over all 21 fixtures
- [ ] full suite matches the new state written into `CLAUDE.md` (21 xfailed scenario cases)
- [ ] commit message states the reason (missing-data scenarios, CLAUDE.md fixture rule)
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
