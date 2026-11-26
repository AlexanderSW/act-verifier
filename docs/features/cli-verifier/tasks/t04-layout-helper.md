---
id: T4
title: "Implement the layout helper: normalize and find sheet, header row and label rows"
layer: "infra"
deps: ["T1"]
blocks: ["T5"]
acs: ["AC-07", "AC-08", "AC-09"]
files_hint: ["src/act_verifier/layout.py", "tests/test_layout.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "M"
status: "done"
step: "COMMIT"
---

<!-- Self-contained task. Every inlined chunk carries a provenance signature
`<file> §<section>, <identifier>, verbatim|abridged`. The source always wins over the inline.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file and follow it. Do not invent. -->

# T4 — Implement the layout helper: normalize and find sheet, header row and label rows

## Place in the sequence

- **Blocked by:** T1 — models (`InputError`) · **Blocks:** T5 — load_contract · **Wave:** 2 (parallel with T3, T7, T9).
- **Lane:** own lane (new file `src/act_verifier/layout.py`).

## Why (user story)

> **As an** employer reviewer
> **I want** an act whose labels sit in different rows to verify the same way, and an unrecognised layout to stop with an input error naming the missing label
> **So that** I can safely try the tool on real acts
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task is the single place where a layout label is matched; both loaders call it, so the matching rule cannot drift between them.

## Inlined context

> `layout.py` NEW: normalize(text), find_sheet, find_header_row, find_label_row (prefix match, region, uniqueness → InputError) — ADR-0001
>
> — `sad.md §5, internal decomposition, layout.py, verbatim` · full text: [sad.md](../sad.md)

> **Chosen:** Option 1. Every structural place — sheet name, header row (the row holding all six header labels), КБ-2в totals rows (searched only below the header row), the four КБ-3 rows, and the КБ-2в «Акт №» title — is found by `layout.find_*` after normalization (trim, collapse whitespace incl. non-breaking, casefold) by prefix. Zero matches → `InputError(missing_label)`; two or more → `InputError(ambiguous_label)` with the competing rows (ADR-0002). Values are taken from the «Вартість» header column on a totals row and from the cell right of a КБ-3 label. The act number is the exception: a missing title is missing data, not an input error (spec §1 clarify decisions).
>
> — `adr/0001-locate-layout-by-normalized-unique-labels.md, Decision outcome, verbatim` · full text: [ADR-0001](../adr/0001-locate-layout-by-normalized-unique-labels.md)

> Layout labels match after normalization (trim, collapse any whitespace incl. non-breaking, ignore case) by prefix; the VAT label does not require «20%»; more than one candidate row for a label is an input error, never «take the first».
>
> — `spec.md §1, specify decisions, verbatim` · full text: [spec.md](../spec.md)

> | normalization | trim, collapse every whitespace run (incl. non-breaking) to one space, casefold — applied to both the label and the cell text before a prefix match |
> | search region | the rows and columns in which a label is looked up (e.g. КБ-2в totals only below the header row) |
>
> — `sad.md §12, Glossary, verbatim` · full text: [sad.md](../sad.md)

> Prefix «ПДВ» or «Всього» matches an unrelated text row — Search region limited to rows below the header (КБ-2в); ambiguity is an input error, never «first match».
>
> — `sad.md §11, risk row 6, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read [ADR-0001](../adr/0001-locate-layout-by-normalized-unique-labels.md) and [ADR-0002](../adr/0002-signal-input-errors-with-typed-exception.md) in full. Do not guess.

## Data delta

No DB changes. Reads openpyxl worksheets only; raises `InputError(kind, label, file, sheet, rows)` from T1.

## API contract

Internal — no API surface. Error kinds raised here: `missing_label`, `ambiguous_label` (`contracts/cli.md §4, Input errors, abridged` · full text: [cli.md](../contracts/cli.md)).

## Acceptance criteria

### AC-07 — error (missing layout label)

> **Given** an input file in which a layout label cannot be found [...]
> **When** the employer reviewer runs the verifier
> **Then** it stops with outcome code 3 and a message that names the missing label, the file and the sheet, and produces no verdict; a label that is present but whose value cell is empty is not this case — it is missing data and yields unknown for every check that uses that value; a missing or unreadable act number is likewise missing data (AC-11), not this case
>
> — `spec.md §5, AC-07, abridged (per-file label list → T5/T6)` · full text: [spec.md](../spec.md)

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

- [ ] `normalize(text) -> str`: `str()` of the cell, every whitespace run incl. U+00A0 → one space, strip, `casefold()`; `None` → `""` — `src/act_verifier/layout.py`
- [ ] `find_sheet(wb, label, file) -> Worksheet`: prefix match over `wb.sheetnames`; 0 → `missing_label`, ≥2 → `ambiguous_label` — `src/act_verifier/layout.py`
- [ ] `find_header_row(ws, labels, file) -> (row, {label: column})`: the row whose cells contain every label by prefix; 0 rows → `missing_label` naming the first label not found in any row; ≥2 rows → `ambiguous_label` with the rows; one label matching two columns in that row → `ambiguous_label` — `src/act_verifier/layout.py`
- [ ] `find_label_row(ws, label, file, *, min_row=None, max_row=None, column=None) -> (row, col)`: prefix match inside the region; 0 → `missing_label`, ≥2 → `ambiguous_label` with all competing rows — `src/act_verifier/layout.py`
- [ ] `find_optional_label_row(...) -> (row, col) | None` for the act-number title (no exception on 0 matches) — `src/act_verifier/layout.py`
- [ ] Unit tests on in-memory `openpyxl.Workbook`s: NBSP / double spaces / case; «ПДВ 20%» matches «ПДВ»; shifted header; missing → kind+label+sheet; duplicate → kind+rows; region excludes rows above the header — `tests/test_layout.py`

## Edge cases

| Case | Behaviour |
|---|---|
| cell value is a number or date | `normalize(str(value))`; never matches a text label by accident only if the prefix matches — test it |
| label «Разом без ПДВ» vs search for «ПДВ» | «разом без пдв» does not *start* with «пдв» → no collision |
| two cells in the **same** row both start with the label | counts as one row for row-uniqueness; for header columns it is `ambiguous_label` (which column is the value?) |
| act-number title appears twice | not fixed upstream — `find_optional_label_row` returns `None` (treated as «act number not readable», missing data → `unknown`, never a guessed number); breakdown-time reading, confirm in review |

## Definition of Done

- [ ] `tests/test_layout.py` passes
- [ ] no code path returns the first of several matches
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
