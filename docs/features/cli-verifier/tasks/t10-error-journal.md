---
id: T10
title: "Implement append_error_log with header creation and formula-injection escaping"
layer: "infra"
deps: ["T9"]
blocks: ["T12"]
acs: ["AC-14"]
files_hint: ["src/act_verifier/report.py", "tests/test_report.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "S"
status: "done"
step: "COMMIT"
---

<!-- Self-contained task. Every inlined chunk carries a provenance signature
`<file> §<section>, <identifier>, verbatim|abridged`. The source always wins over the inline.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file and follow it. Do not invent. -->

# T10 — Implement append_error_log with header creation and formula-injection escaping

## Place in the sequence

- **Blocked by:** T9 — report + evidence · **Blocks:** T12 — cli.main · **Wave:** 3.
- **Lane:** shares `src/act_verifier/report.py` and `tests/test_report.py` with T9 — serialized (after T9).

## Why (user story)

> **As a** project owner
> **I want** the error journal to be written only when I explicitly ask for it
> **So that** demo and reference-scenario runs do not pollute the tracked journal
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task writes the journal lines; whether it is called at all (the opt-in) is decided in T12.

## Inlined context

> | Lines | one per `fail`, `unknown` or `warning` finding; `pass` is never journaled |
> | Header (exact) | `date,act_file,code,check,status,expected,actual,found_by,resolution` |
> | `found_by` | always `act-verifier` (owner decision 2026-11-26, OQ-A5) | `resolution` | always empty |
> | `code` | position code; empty for act-level checks |
> | Escaping | a text field that is not a number and starts with `=`, `+`, `-` or `@` gets a leading apostrophe; numbers are written exactly as read |
> | File absent | created with the header line | Mode | append only |
>
> — `contracts/cli.md §6.4, Error journal, abridged` · full text: [cli.md](../contracts/cli.md)

> Tests append to the tracked journal and dirty the tree — Journal tests always pass a `tmp_path` location; default journal never touched by tests.
>
> — `sad.md §11, risk row 5, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read [contracts/cli.md](../contracts/cli.md) §6.4 and `journal/agent_errors.csv:1`. Do not guess.

## Data delta

No DB changes. Appends `JournalLine` rows (columns `date, act_file, code, check, status, expected, actual, found_by, resolution`; `status ∈ {fail, unknown, warning}`) to a CSV — `data-model.md §Entities, JournalLine, abridged` · full text: [data-model.md](../data-model.md).

## API contract

Internal — `append_error_log(report, log_path, act_file)` (existing signature).

## Acceptance criteria

### AC-14 — happy path (opt-in journal)

> **Given** a project owner runs the verifier on an act with fail, unknown or warning findings
> **When** the run is made without the journal option, with the journal option alone, or with the journal option and a chosen journal location
> **Then** without the option the journal is left untouched; with the option alone one line per fail, unknown or warning finding is appended to the default journal (`journal/agent_errors.csv` relative to the current working directory); with a location the lines are appended there, creating the file with the journal's header line if it does not exist; every line names the verifier as the finder and leaves the resolution empty; a text field that is not a number and begins with «=», «+», «-» or «@» is escaped with a leading apostrophe so it cannot become a formula, while numbers are written exactly as read
>
> — `spec.md §5, AC-14, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `append_error_log`: create parent folder + file with the exact header if absent; open in append mode, `newline=""`, UTF-8; `csv.writer`; one row per non-pass finding in report order; `date` = today ISO — `src/act_verifier/report.py`
- [ ] `_escape(field)`: if the value is not parseable as a `Decimal` and starts with `= + - @` → prefix `'`; numbers (incl. `-5.00`) untouched — `src/act_verifier/report.py`
- [ ] Tests in `tmp_path`: absent file → header + lines; existing file → appended, header not repeated; pass findings skipped; `=SUM(A1)` code → `'=SUM(A1)`; `-5.00` expected stays `-5.00` — `tests/test_report.py`

## Edge cases

| Case | Behaviour |
|---|---|
| report with only pass findings | the file is created with its header if absent (T12 only calls this when the option was given); zero lines appended |
| a field like `-2` that parses as a number | it is a number → written as is (spec §1: escaping applies only to text fields that are not numbers) |
| journal path is an input file | refused before any write by T12's overwrite guard — not handled here |

## Definition of Done

- [ ] journal tests pass and never touch `journal/agent_errors.csv`
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
