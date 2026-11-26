---
id: T1
title: "Extend models with InputError, Skipped and per-value provenance"
layer: "domain"
deps: []
blocks: ["T4", "T5", "T7", "T9"]
acs: ["AC-03", "AC-07", "AC-08"]
files_hint: ["src/act_verifier/models.py", "tests/test_models.py"]
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

# T1 — Extend models with InputError, Skipped and per-value provenance

## Place in the sequence

- **Blocked by:** — · **Blocks:** T4 — layout helper, T5 — load_contract, T7 — row checks, T9 — report + evidence · **Wave:** 1 (every other `src/` module imports `models`; it has no internal imports).
- **Lane:** own lane (`src/act_verifier/models.py` is touched by no other task).

## Why (user story)

> **As an** accepting person
> **I want** every report to end with an evidence block that lists what was checked, what was not and why, and which file, sheet and row each number came from
> **So that** I can decide on the act without re-checking the arithmetic by hand
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task adds the domain types that carry provenance and structured skips (the raw material of the evidence block) and the single input-error type.

## Inlined context

> `models.py` domain: Status, Source, ContractPosition, ActRow, Act, Finding, Report
> + InputError (kind, label, file, sheet, rows) — ADR-0002
> + Skipped (check, code, reason) — ADR-0003
> + Act.sources / header_row / skipped_rows — ADR-0003
>
> — `sad.md §5, internal decomposition, models.py, verbatim` · full text: [sad.md](../sad.md)

> **Chosen:** Option 1 (owner choice). `InputError` lives in `models.py`; `kind` ∈ {`missing_label`, `ambiguous_label`, `unreadable_file`, `invocation`, `overwrite_refused`}. [...] `cli.main` is the only place that catches it [...] Any other exception propagates as a bug.
>
> — `adr/0002-signal-input-errors-with-typed-exception.md, Decision outcome, abridged` · full text: [ADR-0002](../adr/0002-signal-input-errors-with-typed-exception.md)

> **Chosen:** Option 1. Every value has exactly one origin record, the evidence block is a pure rendering of `Report` (`render_evidence(report) -> str`, signature unchanged), and tests can assert skip records by `(check, code, reason)`.
> Option 1: `Act.sources: dict[str, Source]` for every scalar read (number, subtotal, vat, total, kb3_period_total, kb3_cumulative_total), `Act.header_row`, `Act.skipped_rows`; `Report.skipped: list[Skipped(check, code, reason)]`; `Report` also carries the input Sources the evidence block needs.
>
> — `adr/0003-carry-source-on-every-value-and-structured-skips.md, Considered options §1 + Decision outcome, verbatim` · full text: [ADR-0003](../adr/0003-carry-source-on-every-value-and-structured-skips.md)

> **Hard rule:** Гроші й обсяги — тільки `Decimal`. Ніякого float в арифметиці. Бракує даних → статус `unknown`, ніколи не `pass`.
>
> — `CLAUDE.md, Правила, verbatim` · full text: [CLAUDE.md](../../../../CLAUDE.md)

> Stage-2 assistant tool interface reuses this core later (roadmap step 2) — public functions `load_contract`, `load_act`, `verify` keep their signatures.
>
> — `sad.md §2, Organisational, verbatim` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read [data-model.md](../data-model.md) §Entities, [ADR-0002](../adr/0002-signal-input-errors-with-typed-exception.md), [ADR-0003](../adr/0003-carry-source-on-every-value-and-structured-skips.md) in full and follow them. Do not guess.

## Data delta

No DB changes. In-memory dataclass changes in `models.py`:

| Field | Type | Constraints | Change |
|---|---|---|---|
| `Act.sources` | `dict[str, Source]` | provenance of each totals / КБ-3 / title value | added |
| `Act.header_row` | `int` | header row as found, for the evidence block | added |
| `Act.skipped_rows` | `list[int]` | empty rows / rows without a code between table and totals (AC-09) | added |
| `Report.skipped` | `list[Skipped]` | the «not checked» list of the evidence block | altered (`list[str]` →) |
| `Skipped.check` / `.code` / `.reason` | `str` / `str \| None` / `str` | `code` `None` = act level; `reason` required | added (new type) |
| `InputError` | exception (`kind, label, file, sheet, rows`) | never reaches a store | added (new type) |

— `data-model.md §Entities, Act + Report + Skipped + aggregate map, abridged` · full text: [data-model.md](../data-model.md)

## API contract

Internal — no API surface. (`InputError.kind` values are stable in v0.1 — `contracts/cli.md §8, Stability, abridged` · full text: [cli.md](../contracts/cli.md).)

## Acceptance criteria

### AC-03 — happy path (evidence block)

> **Given** any act the verifier was able to read
> **When** the accepting person opens the report
> **Then** the report ends with an evidence block that states how many positions and checks were verified, lists every check that was not performed together with the position and the reason, names the file, sheet and rows each group of numbers was actually read from (rows as found in that file, not as assumed by the README), gives the count of discrepancies by status, and repeats the verdict
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-07 — error (missing layout label)

> **Given** an input file in which a layout label cannot be found [...]
> **When** the employer reviewer runs the verifier
> **Then** it stops with outcome code 3 and a message that names the missing label, the file and the sheet, and produces no verdict [...]
>
> — `spec.md §5, AC-07, abridged (label list → T4/T5/T6)` · full text: [spec.md](../spec.md)

### AC-08 — error (ambiguous layout)

> **Given** an input file in which more than one row matches the same layout label after normalization (new reference scenario with an ambiguous label)
> **When** the employer reviewer runs the verifier
> **Then** it stops with outcome code 3 and a message that names the label and the competing rows, and never silently uses the first match
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Add `InputError(Exception)` with attributes `kind`, `label`, `file`, `sheet`, `rows` (`rows: list[int]`, default empty) and a `KINDS` set of the five values; reject an unknown `kind` — `src/act_verifier/models.py`
- [ ] Add frozen dataclass `Skipped(check: str, code: str | None, reason: str)` — `src/act_verifier/models.py`
- [ ] Add `Act.sources: dict[str, Source]`, `Act.header_row: int`, `Act.skipped_rows: list[int]` with defaults that keep positional construction by `scripts/generate_fixtures.py`'s own `Act` untouched (the generator has its own dataclass — confirm it does not import `act_verifier.models`) — `src/act_verifier/models.py`
- [ ] Change `Report.skipped` to `list[Skipped]`; add the input-source field(s) the evidence block needs (e.g. `inputs: dict[str, list[Source]]` keyed by role contract / previous / act) — `src/act_verifier/models.py`
- [ ] Keep `Report.verdict` logic unchanged (fail → needs_review → pass)
- [ ] Unit tests: `InputError` carries its fields and refuses an unknown kind; `Skipped` is hashable/comparable; `verdict` for {pass}, {pass, unknown}, {warning}, {fail, unknown} — `tests/test_models.py`

## Edge cases

| Case | Behaviour |
|---|---|
| `InputError` with a kind outside the five | `ValueError` at construction (a typo must not become an unmapped exit code) |
| `Report` with no findings | `verdict == "pass"` is today's behaviour; do not change it here — C12 (T8) always emits a finding, so an empty findings list cannot reach the CLI |
| `Source.row is None` | rendered as sheet-level (existing `__str__`) |

## Definition of Done

- [ ] `tests/test_models.py` passes (`.venv/Scripts/python -m pytest -q tests/test_models.py`)
- [ ] `.venv/Scripts/python -m pytest -q` still shows the pre-implementation state (no new failures; scenario tests still xfail)
- [ ] no `float` anywhere in `models.py`; every Hard Rule inlined above still holds
- [ ] lint + vet clean
