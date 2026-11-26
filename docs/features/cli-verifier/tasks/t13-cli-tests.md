---
id: T13
title: "Add command-level tests: every scenario's outcome code, immutability, determinism, timing, journal"
layer: "tests"
deps: ["T3", "T12"]
blocks: []
acs: ["AC-06", "AC-13", "AC-14", "AC-15"]
files_hint: ["tests/test_cli.py"]
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

# T13 — Add command-level tests: every scenario's outcome code, immutability, determinism, timing, journal

## Place in the sequence

- **Blocked by:** T3 — all 21 fixtures, T12 — cli.main · **Blocks:** — · **Wave:** 6 (last).
- **Lane:** own lane (new `tests/test_cli.py`).

## Why (user story)

> **As a** project owner
> **I want** the 14 existing reference scenarios, the new layout scenarios and the expected-input-error scenario to pass, including their outcome codes
> **So that** «done» is verified by tests, not by eye
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task runs every reference scenario through the command and pins the NFR measurements (immutability, determinism, run time) as tests.

## Inlined context

> `tests/test_cli.py` NEW: outcome codes per scenario, overwrite refusal, journal
>
> — `sad.md §5, internal decomposition, verbatim` · full text: [sad.md](../sad.md)

> | Run time for one act (11 positions, 2 previous acts — the «ok_many» scenario) | ≤ 5 s wall-clock on the developer laptop | timing of the «ok_many» scenario in the test suite |
> | Determinism | 0 differences in findings and evidence block across 2 runs on the same inputs | test comparing the outputs of two runs |
> | Input immutability | 0 bytes changed in any input file | test comparing file hashes before and after a run |
>
> — `spec.md §6, NFR table, verbatim` · full text: [spec.md](../spec.md)

> the command test asserts outcome code 3 and no report files.
>
> — `sad.md §5, Reference-file extensions, expected_error, abridged` · full text: [sad.md](../sad.md)

> Tests append to the tracked journal and dirty the tree — Journal tests always pass a `tmp_path` location; default journal never touched by tests.
>
> — `sad.md §11, risk row 5, abridged` · full text: [sad.md](../sad.md)

> **Owner decision (tasks stage, 2026-11-26):** report files are `<act-stem>_report.xlsx` and `<act-stem>_report.md` in `--out`.
>
> — `tasks/_epic.md, Decisions, abridged` · full text: [_epic.md](./_epic.md)

**Fallback:** insufficient or contradicted by the code → read [contracts/cli.md](../contracts/cli.md) §3–§7. Do not guess.

## Data delta

No DB changes. Reads fixtures; writes only into `tmp_path`.

## API contract

- `main(argv) -> int`; codes `0/1/2` from `expected_verdict`, `3` for `expected_error` scenarios.
- stdout ends with the evidence block on 0/1/2; no report files on 3.

— `contracts/cli.md §3, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

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

> **Given** a project owner runs the verifier on an act with fail, unknown or warning findings
> **When** the run is made without the journal option, with the journal option alone, or with the journal option and a chosen journal location
> **Then** without the option the journal is left untouched; with the option alone one line per fail, unknown or warning finding is appended to the default journal (`journal/agent_errors.csv` relative to the current working directory); with a location the lines are appended there, creating the file with the journal's header line if it does not exist; every line names the verifier as the finder and leaves the resolution empty; a text field that is not a number and begins with «=», «+», «-» or «@» is escaped with a leading apostrophe so it cannot become a formula, while numbers are written exactly as read
>
> — `spec.md §5, AC-14, verbatim` · full text: [spec.md](../spec.md)

### AC-15 — happy path (reference scenarios)

> **Then** [...] other input errors (unreadable workbook, invocation error, overwrite refusal) are checked by outcome code only, each scenario is also run through the command and matches its outcome code (0, 1, 2 or 3), scenarios with outcome code 0, 1 or 2 also produce the evidence block while outcome code 3 produces no report [...]
>
> — `spec.md §5, AC-15, abridged (command part; full text in T2)` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Parametrized over `scenario_dirs()`: build argv from `inputs`, `--out tmp_path/"r"`; assert code; on 0/1/2 both report files exist and stdout contains «## Блок доказів»; on 3 `r` holds no file — `tests/test_cli.py`
- [ ] Immutability: SHA-256 of every input before/after a run, for one scenario per outcome code — `tests/test_cli.py`
- [ ] Overwrite refusal: report path = an input copy in `tmp_path`; journal path = the act path in other case → 3, hashes unchanged, nothing new in `tmp_path` — `tests/test_cli.py`
- [ ] Invocation: unknown option, missing `--contract`, missing `--act` → 3 (never 2); unreadable workbook (a text file renamed `.xlsx`) → 3 — `tests/test_cli.py`
- [ ] Determinism: two `ok_many` runs → identical Markdown files and stdout — `tests/test_cli.py`
- [ ] Timing: `ok_many` run ≤ 5 s (`time.perf_counter`) — `tests/test_cli.py`
- [ ] Journal: no option → nothing created; `--journal` alone with `monkeypatch.chdir(tmp_path)` → `tmp_path/journal/agent_errors.csv` with header + one line per non-pass finding; `--journal tmp_path/j.csv` on an existing file → appended — `tests/test_cli.py`

## Edge cases

| Case | Behaviour |
|---|---|
| default journal test | always `chdir` into `tmp_path` — the tracked `journal/agent_errors.csv` must stay untouched (`git status` clean after the suite) |
| scenario with `expected_error` | code 3, stderr names the label, no report |
| Windows path case | the case-insensitive refusal test runs on Windows; on a case-sensitive FS the same comparison still applies (`normcase`) |

## Definition of Done

- [ ] `.venv/Scripts/python -m pytest -q` → all green: no xfail, every scenario passes in both `test_verifier.py` and `test_cli.py`, integrity suite green
- [ ] all four outcome codes (0, 1, 2, 3) are exercised (spec §7 KPI 4 of 4)
- [ ] `git status` shows no change under `journal/` or `tests/fixtures/` after the suite
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
