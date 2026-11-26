---
id: T14
title: "Update docs/checks.md with the skip, unknown and input-error rules fixed by the spec"
layer: "docs"
deps: []
blocks: []
acs: ["AC-05", "AC-07", "AC-11", "AC-12"]
files_hint: ["docs/checks.md"]
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

# T14 — Update docs/checks.md with the skip, unknown and input-error rules fixed by the spec

## Place in the sequence

- **Blocked by:** — · **Blocks:** — · **Wave:** 1 (documentation only; can land any time).
- **Lane:** own lane (`docs/checks.md`).

## Why (user story)

> **As an** accepting person
> **I want** every report to end with an evidence block that lists what was checked, what was not and why, and which file, sheet and row each number came from
> **So that** I can decide on the act without re-checking the arithmetic by hand
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task makes the check catalog — the document the accepting person and the code both cite — say what the spec now fixes, so the catalog and the verifier cannot disagree.

## Inlined context

> Update docs/checks.md with the rules fixed in this spec (C07 unknown on an empty amount, C05 not checked on an empty quantity, C05/C13 unknown on incomplete previous acts, read-vs-computed operands of C08–C13, missing or ambiguous layout label = input error, refusal to overwrite an input, and from clarify: empty printed totals → unknown of the checks using them, empty quantity in a previous act → C05 unknown — these two rules have no generator scenario in stage 1)? Default now: this spec is the source until then. — owner: AlexanderSW, due: before sdd:tasks
>
> — `spec.md §8, OQ 2, verbatim` · full text: [spec.md](../spec.md)

> Totals checks compare against the values printed in the act: C08 uses the printed «Разом без ПДВ», C09 the printed subtotal and VAT, C10 the printed КБ-2в «Всього з ПДВ», C13 Σ printed КБ-2в «Всього з ПДВ» of previous acts + the current КБ-2в «Всього з ПДВ».
> An empty printed total makes `unknown` every check that uses it, naming the value: «Разом без ПДВ» → C07, C08, C09; «ПДВ» → C08, C09; «Всього з ПДВ» → C09, C10, C13; КБ-3 period total → C10; КБ-3 cumulative total → C13; a previous act's «Всього з ПДВ» → C13.
>
> — `spec.md §1, derived from fixtures + clarify decisions, verbatim` · full text: [spec.md](../spec.md)

> «Наступні сценарії (ще не в фікстурах)»: … рядок «Разом» стоїть не одразу після таблиці; …
>
> — `docs/checks.md, Наступні сценарії, abridged` · full text: [checks.md](../../../checks.md)

> **Hard rule:** Check IDs exactly as in `docs/checks.md` (`C01_position_in_contract` … `C13_kb3_cumulative`). User-facing text in Ukrainian.
>
> — `sad.md §2, Conventions, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient → read [spec.md](../spec.md) §1 and §5 in full. Do not guess or add rules the spec does not state.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-05 — domain invariant (what each missing value suppresses)

> **Then** an empty quantity leaves the arithmetic and remaining-volume checks of that position not checked; an empty price leaves the price and arithmetic checks not checked; an empty amount leaves the arithmetic check not checked and makes the subtotal check unknown, naming the position whose amount is missing — a formula cell without a stored value counts as empty; in every case the required-values check is unknown and the verdict is at best needs_review
>
> — `spec.md §5, AC-05, abridged (Then part)` · full text: [spec.md](../spec.md)

### AC-07 — error (missing layout label)

> **Then** it stops with outcome code 3 and a message that names the missing label, the file and the sheet, and produces no verdict; a label that is present but whose value cell is empty is not this case — it is missing data and yields unknown for every check that uses that value; a missing or unreadable act number is likewise missing data (AC-11), not this case
>
> — `spec.md §5, AC-07, abridged (Then part)` · full text: [spec.md](../spec.md)

### AC-11 — cross-context (incomplete previous acts)

> **Then** the remaining-volume check of every position and the cumulative КБ-3 check are unknown with the reason «previous acts supplied: K of N−1», where K counts distinct act numbers within 1…N−1 [...], all other checks still run, and the verdict is at best needs_review with outcome code 2 — never pass
>
> — `spec.md §5, AC-11, abridged (Then part)` · full text: [spec.md](../spec.md)

### AC-12 — cross-context (КБ-3 against КБ-2в)

> **Then** the verifier reports only the КБ-3-matches-КБ-2в check as fail and the cumulative check as pass — totals checks compare against the values printed in the act, not against recomputed ones
>
> — `spec.md §5, AC-12, abridged (Then part)` · full text: [spec.md](../spec.md)

## Checklist

- [ ] «Правила пропуску»: add empty quantity → C04, C05 not checked; empty amount → C04 not checked + C07 `unknown` naming the position; formula without stored value = empty — `docs/checks.md`
- [ ] «Перевірки підсумків і КБ-3»: state that C08–C10, C13 use printed values; add the empty-printed-total → `unknown` mapping — `docs/checks.md`
- [ ] New short section on previous acts: N from «Акт №»; not exactly 1…N−1 → C05 (all positions) + C13 `unknown` with the AC-11 reasons; empty previous quantity → C05 of that position `unknown`; repeated code in a previous act summed — `docs/checks.md`
- [ ] New short section «Помилка вхідних даних (код 3)»: missing / ambiguous layout label, unreadable file, invocation error, refusal to write to an input — no verdict, no report — `docs/checks.md`
- [ ] «Наступні сценарії»: remove «рядок «Разом» стоїть не одразу після таблиці» (now a fixture) — `docs/checks.md`

## Edge cases

| Case | Behaviour |
|---|---|
| a rule not in spec §1/§5 | not added — the spec is the source (spec §8 OQ 2 default) |
| check IDs | unchanged; no new ID |

## Definition of Done

- [ ] every rule listed in spec §8 OQ 2 appears in `docs/checks.md`, in Ukrainian, with no rule beyond the spec
- [ ] `.venv/Scripts/python -m pytest -q` unchanged (docs only)
- [ ] every Hard Rule inlined above still holds
