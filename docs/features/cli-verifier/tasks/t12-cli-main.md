---
id: T12
title: "Implement cli.main: options, overwrite guard, orchestration and outcome codes"
layer: "ports"
deps: ["T6", "T8", "T9", "T10"]
blocks: ["T13"]
acs: ["AC-01", "AC-06", "AC-13", "AC-14"]
files_hint: ["src/act_verifier/cli.py", "tests/test_cli_unit.py"]
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

# T12 — Implement cli.main: options, overwrite guard, orchestration and outcome codes

## Place in the sequence

- **Blocked by:** T6 — load_act, T8 — verify, T9 — report + evidence, T10 — journal · **Blocks:** T13 — command tests · **Wave:** 5.
- **Lane:** own lane (`src/act_verifier/cli.py`).

## Why (user story)

> **As a** preparing agent
> **I want** a distinct outcome code for pass, fail, needs_review and input error
> **So that** I can fix the act, hand it to a person, or fix my invocation without parsing text
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

This task is the thin shell: it validates the invocation, guards the inputs, runs the core and maps the result to 0/1/2/3.

## Inlined context

> `act-verifier --contract PATH --act PATH [--previous [PATH ...]] [--out DIR] [--journal [PATH]]`
> - Any option not listed is an invocation error (outcome code 3). Python's default `argparse` code 2 is never returned: 2 means needs_review.
> - A required option that is missing is an invocation error (code 3). Missing `--previous` is not an error.
> - `--journal` takes at most one path: the next token, if it does not start with `-`.
>
> — `contracts/cli.md §1–§2, abridged` · full text: [cli.md](../contracts/cli.md)

> 1. Parse the options. Error → code 3, nothing read, nothing written.
> 2. Check that every input exists. Resolve the input paths, the report paths and the journal path (if given) to absolute, case-folded paths. Any output path equal to an input path → `overwrite_refused`, code 3, **nothing written** (AC-13).
> 3. Load the contract, each previous act and the current act, read-only (`data_only=True`). Any `InputError` → code 3, no report.
> 4. Verify (pure). 5. Write the report files into `--out`. 6. If `--journal` was given, append the journal lines. 7. Print the evidence block to stdout and return 0, 1 or 2.
>
> — `contracts/cli.md §5, Order of effects, abridged` · full text: [cli.md](../contracts/cli.md)

> | `invocation` | unknown option; `--contract` or `--act` missing | `unreadable_file` | a given input path does not exist (owner decision OQ-A3) | `overwrite_refused` | a report path or the journal path equals an input path |
> `cli.main` is the only place that catches it: Ukrainian message on stderr naming label, file and sheet (and the competing rows for ambiguity), no report, return 3. Any other exception propagates as a bug.
>
> — `contracts/cli.md §4 + adr/0002, Decision outcome, abridged` · full text: [cli.md](../contracts/cli.md) · [ADR-0002](../adr/0002-signal-input-errors-with-typed-exception.md)

> **Owner decision (tasks stage, 2026-11-26, closes cli.md OQ-A1):** report files are `<act-stem>_report.xlsx` and `<act-stem>_report.md` in `--out`; a rerun overwrites them; a missing `--out` folder is created (parents too) — after the overwrite guard.
>
> — `tasks/_epic.md, Decisions, verbatim` · full text: [_epic.md](./_epic.md)

> **Hard rule:** Верифікатор лише читає вхідні файли. Нічого в них не записує.
>
> — `CLAUDE.md, Правила, verbatim` · full text: [CLAUDE.md](../../../../CLAUDE.md)

**Fallback:** insufficient or contradicted by the code → read [contracts/cli.md](../contracts/cli.md) in full and [sad.md](../sad.md) §6 F2/F5. Do not guess.

## Data delta

No DB changes. Writes only report files (T9) and, on request, journal lines (T10).

## API contract

- Exit codes: `0` pass · `1` fail · `2` needs_review (from `Report.verdict`) · `3` any `InputError`.
- stdout: evidence block on 0/1/2, nothing on 3. stderr: plain-language Ukrainian message on 3.
- `main(argv: list[str] | None = None) -> int` — callable from tests.

— `contracts/cli.md §3, Outcome codes, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-01 — happy path

> **Given** a project owner has a contract price, the complete set of previous acts and a current act with no discrepancies (reference scenario «ok_many»)
> **When** the project owner runs the verifier on them
> **Then** the verifier reports verdict pass with outcome code 0, produces a findings report that lists every check applied to every position and to the act — including the passing ones — and ends the report with the evidence block
>
> — `spec.md §5, AC-01, verbatim` · full text: [spec.md](../spec.md)

### AC-06 — error (invocation error)

> **Given** a preparing agent invokes the verifier without a required input (the contract price or the current act; previous acts are optional) or with an option the verifier does not know
> **When** the verifier starts
> **Then** it stops with outcome code 3, explains in plain language which input is missing or which option is unknown, and produces no report and no verdict — the code is never the needs_review code
>
> — `spec.md §5, AC-06, verbatim` · full text: [spec.md](../spec.md)

### AC-13 — authorization (inputs are never modified)

> **Given** a project owner runs the verifier on any inputs, including a run where the report or journal location would coincide with one of the input files (fully resolved paths equal, compared case-insensitively)
> **When** the run finishes
> **Then** every input file is byte-for-byte unchanged; a run whose report or journal would overwrite an input is refused before anything is written, with outcome code 3 and an explanation that the verifier never writes to its inputs
>
> — `spec.md §5, AC-13, verbatim` · full text: [spec.md](../spec.md)

### AC-14 — happy path (opt-in journal)

> **When** the run is made without the journal option, with the journal option alone, or with the journal option and a chosen journal location
> **Then** without the option the journal is left untouched; with the option alone one line per fail, unknown or warning finding is appended to the default journal (`journal/agent_errors.csv` relative to the current working directory); with a location the lines are appended there [...]
>
> — `spec.md §5, AC-14, abridged (option handling; line format → T10)` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `_Parser(argparse.ArgumentParser)` overriding `error()` to raise `InputError("invocation", label=<option>)`; add `--journal` with `nargs="?"`, `const=Path("journal/agent_errors.csv")`, default `None` — `src/act_verifier/cli.py`
- [ ] Input existence check → `unreadable_file`; `_same(a, b)`: `os.path.normcase(os.path.realpath(...))` equality; guard compares both report paths and the journal path with every input → `overwrite_refused` — `src/act_verifier/cli.py`
- [ ] Orchestrate: `load_contract` → `load_act(p, previous=True)` for each previous → `load_act(act)` → `verify` → `write_excel` + Markdown file → `append_error_log` (only if `--journal`) → print `render_evidence` → return `{"pass": 0, "fail": 1, "needs_review": 2}[verdict]` — `src/act_verifier/cli.py`
- [ ] Single `except InputError` in `main`: Ukrainian message to stderr naming kind-specific details, return 3; no other `except` — `src/act_verifier/cli.py`
- [ ] Unit tests calling `main([...])` with `tmp_path` / `capsys`: unknown option → 3; missing `--act` → 3; `--journal` = the act path in different letter case → 3 and act bytes unchanged; the contract copied to `<out>/<act-stem>_report.xlsx` (report path = an input) → 3 and contract bytes unchanged; `ok_many` → 0 and both report files exist — `tests/test_cli_unit.py`

## Edge cases

| Case | Behaviour |
|---|---|
| `--journal` followed by `--act …` | default journal location (next token starts with `-`) |
| journal path given in different case from an input | refused, code 3 (case-insensitive) |
| `--help` | argparse prints help and exits 0 — known clash with pass (cli.md OQ-A2, open); do not change here |
| `OSError` while writing a report | propagates as a bug (sad §11 accepted Low risk), not code 3 |

## Definition of Done

- [ ] `tests/test_cli_unit.py` passes; exit code 2 never produced for an invocation error
- [ ] on code 3 no file is created or changed (asserted via `tmp_path` listing + input hashes)
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
