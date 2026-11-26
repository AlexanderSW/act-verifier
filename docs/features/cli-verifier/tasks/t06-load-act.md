---
id: T6
title: "Implement load_act: КБ-2в table, totals, КБ-3 values, act number and provenance"
layer: "infra"
deps: ["T2", "T5"]
blocks: ["T11", "T12"]
acs: ["AC-05", "AC-07", "AC-08", "AC-09"]
files_hint: ["src/act_verifier/loaders.py", "tests/test_loaders.py"]
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

# T6 — Implement load_act: КБ-2в table, totals, КБ-3 values, act number and provenance

## Place in the sequence

- **Blocked by:** T2 — layout fixtures (shifted header, totals gap, missing/ambiguous label), T5 — load_contract + cell readers · **Blocks:** T11 — scenario tests, T12 — cli.main · **Wave:** 4.
- **Lane:** shares `src/act_verifier/loaders.py` and `tests/test_loaders.py` with T5 — serialized (after T5).

## Why (user story)

> **As an** employer reviewer
> **I want** an act whose labels sit in different rows to verify the same way, and an unrecognised layout to stop with an input error naming the missing label
> **So that** I can safely try the tool on real acts
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task reads a current or previous act wherever its labels sit and attaches a `Source` to every value, so the evidence block can cite rows as found.

## Inlined context

> - КБ-2в table: from the header row down to the first «Разом без ПДВ» row below it. A position is a row with a non-empty position code; fully empty rows and rows without a code (e.g. a note) are skipped and counted in the evidence block as «skipped rows without a code». Totals labels are searched only below the header row.
> - Value cells: a КБ-2в totals value is the cell in the «Вартість» header column on the label's row; a КБ-3 value is the cell immediately to the right of the label. The four КБ-3 label prefixes, all mandatory: «Вартість робіт за звітний період», «ПДВ», «Всього за звітний період», «З початку виконання робіт».
> - Act number N (current and previous acts) is read only from the КБ-2в title cell whose normalized text begins with «Акт №»; the file name and the КБ-3 «до акта №» text are not used. A missing or non-numeric act number is missing data (→ `unknown` of C05/C13), never an input error.
>
> — `spec.md §1, clarify decisions, verbatim` · full text: [spec.md](../spec.md)

> A missing layout label (sheet, header columns, any of the three КБ-2в totals labels, any of the four КБ-3 labels) is an input error; a label present with an empty value is missing data → `unknown`.
> An empty amount leaves C04 not checked and makes C07 unknown; a formula cell without a stored value counts as empty.
>
> — `spec.md §1, specify decisions, verbatim` · full text: [spec.md](../spec.md)

> S->>IN: read positions from the header row down to the first «Разом без ПДВ» row
> IN-->>S: rows with a position code, rows without a code, totals values
> S->>S: keep rows with a position code, record skipped rows without a code, attach file, sheet and row to each value
>
> — `sad.md §6, F3 steps 9–11, verbatim` · full text: [sad.md](../sad.md)

> `Act.sources: dict[str, Source]` for every scalar read (number, subtotal, vat, total, kb3_period_total, kb3_cumulative_total), `Act.header_row`, `Act.skipped_rows`
>
> — `adr/0003-carry-source-on-every-value-and-structured-skips.md, Considered options §1, abridged` · full text: [ADR-0003](../adr/0003-carry-source-on-every-value-and-structured-skips.md)

> **Hard rule:** `load_act(path) -> Act` keeps its signature (stage-2 reuse).
>
> — `sad.md §2, Organisational, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read [spec.md](../spec.md) §1, [ADR-0001](../adr/0001-locate-layout-by-normalized-unique-labels.md), [ADR-0003](../adr/0003-carry-source-on-every-value-and-structured-skips.md) and `scripts/generate_fixtures.py::write_act`. Do not guess.

## Data delta

No DB changes. Builds `Act` and `ActRow` (fields from T1):

| Field | Type | Constraints | Change |
|---|---|---|---|
| `Act.number` | `int \| None` | `None` = missing / unreadable → missing data | written |
| `Act.rows` | `list[ActRow]` | only rows with a position code (AC-09) | written |
| `Act.subtotal` / `vat` / `total` | `Decimal \| None` | as printed (AC-12) | written |
| `Act.kb3_period_total` / `kb3_cumulative_total` | `Decimal \| None` | as printed | written |
| `Act.sources` / `header_row` / `skipped_rows` | `dict` / `int` / `list[int]` | new (ADR-0003) | written |
| `ActRow.qty` / `price` / `amount` | `Decimal \| None` | `None` → checks skip / unknown (AC-04/05) | written |

— `data-model.md §Entities, Act + ActRow, abridged` · full text: [data-model.md](../data-model.md)

## API contract

Internal — no API surface. Raises `InputError` kinds `missing_label`, `ambiguous_label`, `unreadable_file` (`contracts/cli.md §4, abridged` · full text: [cli.md](../contracts/cli.md)).

## Acceptance criteria

### AC-05 — domain invariant (what each missing value suppresses)

> **Given** a current act where a position has an empty quantity, an empty price or an empty amount
> **When** the project owner runs the verifier
> **Then** an empty quantity leaves the arithmetic and remaining-volume checks of that position not checked; an empty price leaves the price and arithmetic checks not checked; an empty amount leaves the arithmetic check not checked and makes the subtotal check unknown, naming the position whose amount is missing — a formula cell without a stored value counts as empty; in every case the required-values check is unknown and the verdict is at best needs_review (new generator scenarios with an empty quantity and an empty amount)
>
> — `spec.md §5, AC-05, verbatim` · full text: [spec.md](../spec.md)

### AC-07 — error (missing layout label)

> **Given** an input file in which a layout label cannot be found — [...] for the current act: the sheets «КБ-2в» and «КБ-3», the same header columns, «Разом без ПДВ», «ПДВ», «Всього з ПДВ» and the four КБ-3 labels («Вартість робіт за звітний період», «ПДВ», «Всього за звітний період», «З початку виконання робіт»); for a previous act: the sheet «КБ-2в», its header columns and «Всього з ПДВ» (new reference scenario with a missing label)
> **When** the employer reviewer runs the verifier
> **Then** it stops with outcome code 3 and a message that names the missing label, the file and the sheet, and produces no verdict; a label that is present but whose value cell is empty is not this case — it is missing data and yields unknown for every check that uses that value; a missing or unreadable act number is likewise missing data (AC-11), not this case
>
> — `spec.md §5, AC-07, abridged (act parts)` · full text: [spec.md](../spec.md)

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

## Checklist

- [ ] `load_act(path, *, previous: bool = False) -> Act` (keyword-only, default keeps the signature): `find_sheet("КБ-2в")`, `find_header_row` with the six header labels — `src/act_verifier/loaders.py`
- [ ] Totals below the header: current act → `find_label_row` for «Разом без ПДВ», «ПДВ», «Всього з ПДВ» (all required); previous act → «Всього з ПДВ» required, the other two optional — `src/act_verifier/loaders.py`
- [ ] Table rows: header+1 … first «Разом без ПДВ» row − 1 (previous act without that row: up to the «Всього з ПДВ» row − 1); code cell non-empty → `ActRow` with `Source(file, "КБ-2в", row)`; otherwise row number → `skipped_rows` — `src/act_verifier/loaders.py`
- [ ] Totals values from the «Вартість» header column on each label row; КБ-3 (current act only): `find_sheet("КБ-3")`, the four labels, value = cell right of the label; every scalar's `Source` into `Act.sources` — `src/act_verifier/loaders.py`
- [ ] Act number: `find_optional_label_row("Акт №")` above the header row; parse the first integer after «№»; absent / non-numeric → `number = None`; `Source` recorded when found — `src/act_verifier/loaders.py`
- [ ] Tests on generated fixtures: `ok_many/act_03.xlsx` → 11 rows, `header_row == 8`, number 3; the two layout fixtures from T2 → rows/sources equal their `layout` map, skipped rows listed; missing/ambiguous label fixtures → kind + label + sheet; in-memory: a row with an empty amount → `amount is None`, a formula cell without cached value → `None` — `tests/test_loaders.py`

## Edge cases

| Case | Behaviour |
|---|---|
| label present, value cell empty (e.g. «ПДВ» value blank) | value `None`, `Source` still recorded — missing data, **not** an `InputError` |
| «Акт № 3 за листопад» vs «Акт №3» | both parse to 3 (normalization collapses whitespace; first integer after «№») |
| title found but no integer | `number = None` (missing data, AC-11 «act number not readable») |
| previous act lacks КБ-3 sheet | fine — КБ-3 is not required for a previous act (AC-07) |
| previous act missing «Разом без ПДВ» | allowed; table ends above «Всього з ПДВ» — breakdown-time reading of AC-07's previous-act list, confirm in review |
| workbook not readable | `InputError("unreadable_file")` via T5's `_open` |

## Definition of Done

- [ ] `tests/test_loaders.py` passes, including rows-equal-`layout`-map assertions for both layout fixtures
- [ ] no input file is written (`read_only=True`); no `float` arithmetic
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
