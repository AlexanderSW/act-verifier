---
status: Draft
owner: "AlexanderSW"
reviewers: ["Tech Lead"]
updated_at: "2026-11-26"
feature_size: "S"
contract_kind: cli
contract_version: "0.1.0"
---

# CLI contract — cli-verifier

> **Derived, not hand-written.** Sources: `data-model.md` (shapes of the report, journal line and
> reference file), `sad.md` §6 flows F1–F5 and Critical flow 1 (outcome branches), `spec.md` §4
> US-01…US-06 and §5 AC-01…AC-16 (observable outcomes), ADR-0002 (input-error kinds), the current
> `src/act_verifier/cli.py` argument names and `pyproject.toml` `[project.scripts]`.
> Field-by-field origins and the drift check: [`api-sync-report.md`](api-sync-report.md).
> Surface `cli` is read from `sad.md` frontmatter `target_surfaces`; there is no HTTP, gRPC or event surface.

**Why this command exists (spec §1).** The verifier core is a stub, so the project owner cannot
verify an act at all. This command takes a contract price, the previous acts and the current act and
returns a verdict, a findings report and an evidence block, with a distinct outcome code for pass,
fail, needs_review and input error. A preparing agent branches on that code without parsing text.

## 1. Command

One command, no sub-commands.

```
act-verifier --contract PATH --act PATH [--previous [PATH ...]] [--out DIR] [--journal [PATH]]
```

| Entry point | Origin |
|---|---|
| console script `act-verifier` → `act_verifier.cli:main` | `pyproject.toml` `[project.scripts]` |
| `python -m act_verifier.cli` (same `main`, `raise SystemExit(main())`) | `src/act_verifier/cli.py` |
| `main(argv: list[str] \| None = None) -> int` — callable from tests, returns the outcome code | `src/act_verifier/cli.py`; sad §5 |

## 2. Options

| Option | Required | Value | Default | Meaning | Source |
|---|---|---|---|---|---|
| `--contract PATH` | **yes** | one path to an `.xlsx` workbook | — | contract price, sheet «Договірна ціна» | `cli.py`; spec §1 (clarify), AC-06 |
| `--act PATH` | **yes** | one path to an `.xlsx` workbook | — | current act, sheets «КБ-2в» + «КБ-3» | `cli.py`; spec §1 (clarify), AC-06 |
| `--previous [PATH ...]` | no | zero or more paths | none | previous acts, sheet «КБ-2в»; act 1 has none. Order does not matter: each act's number is read from its «Акт №» title, never from the file name | `cli.py` (`nargs="*"`); spec §1 (clarify), AC-11 |
| `--out DIR` | no | folder path | `reports` (relative to the current folder) | where the report files are written | `cli.py`; spec §1 (clarify) |
| `--journal [PATH]` | no | optional path | not given → journal untouched; given alone → `journal/agent_errors.csv` relative to the current folder | opt-in error journal | spec §1, AC-14; sad §8 |

Rules:

- Any option not listed above is an **invocation error** (outcome code 3, §4). Python's default
  `argparse` code 2 is never returned: 2 means needs_review (sad §8, §11; spec AC-06).
- A required option that is missing is an invocation error (code 3). Missing `--previous` is **not**
  an error. Too few previous acts is handled by the checks (AC-11, outcome 2), not by this layer.
- All paths are resolved to absolute paths and compared **case-insensitively** for the overwrite
  guard (§5). That is the Windows rule from spec §1 (clarify).
- `--journal` takes at most one path: the next token, if it does not start with `-`. Every input
  is passed through a named option and there are no positional arguments, so `--journal` followed by
  another option means «default location».

## 3. Outcome codes

The preparing agent reads only this code (US-03). It never has to parse text.

| Code | Meaning | When | Report files | stdout | stderr | Source |
|---|---|---|---|---|---|---|
| **0** | pass | every finding is `pass` | written | evidence block | — | spec AC-01; sad F1 «every check pass» |
| **1** | fail | at least one finding is `fail` | written | evidence block | — | spec AC-02, AC-10, AC-12; sad F1 «any finding is fail» |
| **2** | needs_review | no `fail`, at least one `unknown` or `warning` | written | evidence block | — | spec AC-04, AC-05, AC-11, AC-16; sad F1, F4 |
| **3** | input error: verification did not happen | any `InputError` (§4) | **none written** | — | plain-language message (Ukrainian) | spec AC-06, AC-07, AC-08, AC-13; sad F2, F3; ADR-0002 |

The code comes from `Report.verdict` (`data-model.md` → `Report.verdict`: `fail` → 1,
`needs_review` → 2, `pass` → 0). The journal never changes it (sad F5 postcondition).

**Outside the contract.** Any exception other than `InputError` is a bug. It propagates, and the
process exits with Python's default code 1, which can be confused with fail (sad §8, §11, accepted
Low risk). The built-in `--help` exits 0 with no verdict, the same code as pass.
<!-- unresolved: OQ-A2 (owner: sequences, due: before the contract is finalized) — code clash of --help (0) and an unexpected exception (1) with pass/fail -->

## 4. Input errors (outcome code 3)

One typed exception, `InputError(kind, label, file, sheet, rows)` (ADR-0002, `data-model.md` →
`InputError`). Only `cli.main` catches it. It writes the message to stderr and returns 3, with no
report and no verdict. Identifiers are the ADR-0002 `kind` values verbatim (this is the form the
repo uses, see the sync report §B.2).

| `kind` | Raised when | The message names | sad §6 branch | Spec |
|---|---|---|---|---|
| `invocation` | unknown option; `--contract` or `--act` missing | the missing input or the unknown option | F2 «unknown option or a required input not given»; Critical flow 1 | AC-06 |
| `unreadable_file` | the file is not a readable workbook | the file | F3 «file is not a readable workbook»; Critical flow 1 | §6.1 abuse cases, AC-15 |
| `unreadable_file` (owner decision 2026-11-26, OQ-A3) | a given input path does not exist | the missing file | F2 «an input path does not exist» | AC-06 |
| `missing_label` | a required layout label has no matching row (list in spec AC-07: sheets, header columns, the three КБ-2в totals labels, the four КБ-3 labels; for a previous act: the sheet «КБ-2в», its header columns and «Всього з ПДВ») | the label, the file and the sheet | F3 «a required label has no matching row» | AC-07 |
| `ambiguous_label` | more than one row matches a label after normalization | the label, the file, the sheet and the competing rows | F3 «a label matches more than one row» | AC-08 |
| `duplicate_code` (ADR-0002 amendment 2026-11-26) | a «Шифр» appears in more than one row of the contract — neither the first nor the last row is used | the code, the file, the sheet and the rows | F3 «a label matches more than one row» | AC-08 |
| `overwrite_refused` | a report path or the journal path equals an input path (resolved, case-insensitive) | that the verifier never writes to its inputs | F2 «a report or journal path equals an input path» | AC-13 |

None of the following is an input error. Each one is missing data, so the run goes on and the
affected checks come out `unknown` (outcome 2 at best):

- a label that is present but has an empty value cell (spec AC-07);
- a missing or non-numeric act number (spec §1 clarify, AC-11);
- an empty quantity, price or amount, or a formula cell with no stored value (AC-04, AC-05);
- an incomplete set of previous acts (AC-11).

The stderr message is for people. Its wording is in Ukrainian and is **not** a stable machine
interface. Machines use the outcome code. Tests match `kind` and `label` on the exception
(`expected.json` → `expected_error`, AC-15), not the stderr text.

`InputError` stops at the first problem. An act with three missing labels reports one of them per
run (ADR-0002, accepted debt).

## 5. Order of effects and write safety

Order of effects in a run (sad F2 → F3 → F1 → F5; §4 «pure core, thin shell»):

1. Parse the options. Error → code 3, nothing read, nothing written.
2. Check that every input exists. Resolve the input paths, the report paths and the journal path (if
   given) to absolute, case-folded paths. Any output path equal to an input path → `overwrite_refused`,
   code 3, **nothing written** (AC-13).
3. Load the contract, each previous act and the current act, read-only (`data_only=True`). Any
   `InputError` → code 3, no report.
4. Verify (pure). This step never fails with an input error.
5. Write the report files into `--out`.
6. If `--journal` was given, append the journal lines.
7. Print the evidence block to stdout and return 0, 1 or 2.

Invariant on every path, including code 3: every input file is byte-for-byte unchanged (spec AC-13,
§6 «Input immutability»; sad QG-3).

## 6. Outputs

### 6.1 Report files (code 0 / 1 / 2 only)

Two files are written into `--out` on every run that reaches a verdict (spec §1 clarify; data-model
`Report` «Persisted as»):

| File | Format | Content | Source |
|---|---|---|---|
| Excel workbook | `.xlsx`, sheet «Перевірки» | one row per finding, including `pass`: columns шифр · перевірка · статус · очікувано · фактично · джерело | spec §1 (clarify); `report.write_excel` docstring; data-model `Finding` |
| Markdown | `.md` | the findings, ending with the evidence block (§6.3) | spec §1 (clarify), AC-03; data-model `Report` |

| Column (Excel) | data-model field | Notes |
|---|---|---|
| шифр | `Finding.code` | empty for act-level checks (`None`) |
| перевірка | `Finding.check` | ID from `docs/checks.md`, e.g. `C03_price_matches_contract` |
| статус | `Finding.status` | `pass` \| `fail` \| `unknown` \| `warning` |
| очікувано | `Finding.expected` | Decimal rendered as read, never float |
| фактично | `Finding.actual` | same |
| джерело | `Finding.sources` → `Source` (`file / sheet, рядок N`) | `Source.__str__` |

- **File names:** <!-- unresolved: OQ-A1 (owner: specify, due: before the contract is finalized) -->. No upstream artifact fixes
  them, and none says whether a second run overwrites the files of a first run. The overwrite guard
  (§5 step 2) needs the full paths before anything is written.
- **Folder `--out` does not exist:** <!-- unresolved: OQ-A1 (owner: specify) -->.
- **Determinism:** findings are sorted by (row order, check ID). There are no timestamps in the
  findings or the evidence block, so two runs on the same inputs give identical findings and an
  identical evidence block (spec §6; sad §8, QG-4).
- **Language:** the report text is in Ukrainian. Check IDs and status literals stay as in
  `docs/checks.md` (spec §1 clarify; sad §2).

### 6.2 stdout

- Codes 0, 1 and 2: the evidence block (§6.3) and nothing else is promised (spec §1 clarify;
  sad Critical flow 1 «evidence block on console»).
- Code 3: nothing on stdout.

### 6.3 Evidence block

The last section of the Markdown report. The same text goes to stdout. Format from
`docs/checks.md` «Блок доказів», with content per spec AC-03 / AC-09 / AC-11 and ADR-0003:

```markdown
## Блок доказів
Перевірено: <N позицій> × <перевірок рядка>, <перевірок підсумків>.
Не перевірено: <шифр> — <check IDs> (<reason>); …            ← from Report.skipped (Skipped: check, code, reason)
Пропущено рядків без шифру: <file>, «КБ-2в», рядки <…>         ← from Act.skipped_rows (AC-09)
Джерела чисел:
- договірні ціни й обсяги — <file>, аркуш «Договірна ціна», рядки <as found>
- попередні обсяги — <file>, …, аркуш «КБ-2в», рядки <as found>
- перевірюваний акт — <file>, аркуші «КБ-2в», «КБ-3», рядки <as found>
Розбіжностей: <count by status>. Вердикт: <pass | fail | needs_review>.
```

- Rows are the rows **as found** in that file (`Source.row`, `Act.header_row`), never the README rows
  (AC-03, AC-09; ADR-0003).
- Example reasons (content, not the literal wording, spec §1 clarify): «порожня ціна» (AC-04),
  «previous acts supplied: K of N−1», «act number not readable», «previous act number not readable
  — <file>», «duplicate previous act number M», «previous act number M outside 1…N−1» (AC-11).
- An empty amount makes C07 `unknown` and names the position (AC-05). An empty printed total makes
  every check that uses it `unknown` and names the value (spec §1 clarify).

### 6.4 Error journal (`--journal` only)

| Aspect | Contract | Source |
|---|---|---|
| When | only if `--journal` is given and the run reached a verdict (code 0/1/2) | spec AC-14; sad F5 |
| Where | `--journal` alone → `journal/agent_errors.csv` relative to the current folder; `--journal PATH` → `PATH` | spec §1 (clarify), AC-14 |
| File absent | created with the header line below | spec AC-14; sad F5 |
| Mode | append only | data-model `JournalLine` |
| Lines | one per `fail`, `unknown` or `warning` finding; `pass` is never journaled | spec AC-14; sad F5 |
| Header (exact) | `date,act_file,code,check,status,expected,actual,found_by,resolution` | `journal/agent_errors.csv:1`; data-model `JournalLine` |
| `found_by` | always `act-verifier` (the console-script name; owner decision 2026-11-26, OQ-A5) | spec AC-14; `pyproject.toml` |
| `resolution` | always empty | spec AC-14 |
| `code` | position code; empty for act-level checks | data-model `JournalLine.code` |
| Escaping | a text field that is not a number and starts with `=`, `+`, `-` or `@` gets a leading apostrophe; numbers are written exactly as read | spec AC-14, §6.1 |
| Outcome code | unchanged by the journal | sad F5 |

Example line (placeholder data only):

```csv
2026-11-26,act_03_example.xlsx,5-2,C03_price_matches_contract,fail,100.00,120.00,act-verifier,
```

## 7. Examples

Placeholder files only. Paths are illustrative.

**Pass, code 0** (AC-01, scenario «ok_many»)

```console
$ act-verifier --contract tests/fixtures/ok_many/contract_boq.xlsx \
    --previous tests/fixtures/ok_many/act_01.xlsx tests/fixtures/ok_many/act_02.xlsx \
    --act tests/fixtures/ok_many/act_03.xlsx --out <tmp>/reports
## Блок доказів
Перевірено: 11 позицій × 7 перевірок, 6 перевірок підсумків.
Не перевірено: —
Джерела чисел:
- договірні ціни й обсяги — contract_boq.xlsx, аркуш «Договірна ціна», рядки 7–…
…
Розбіжностей: 0. Вердикт: pass.
$ echo $?
0
```

**Fail, code 1** (AC-02, scenario «combo_three_errors»). Three `fail` findings, each with expected
and actual. The run does not stop at the first one. Exit `1`.

**Needs review, code 2** (AC-04, scenario «missing_price»). C11 is `unknown`. The not-checked list has
`<шифр> — C03, C04 (порожня ціна)`. Exit `2`.

**Invocation error, code 3** (AC-06)

```console
$ act-verifier --act act_03_example.xlsx
<message naming the missing input «--contract»>          (stderr)
$ echo $?
3
```

**Missing label, code 3** (AC-07)

```console
$ act-verifier --contract contract_example.xlsx --act act_missing_label.xlsx
<message naming the label «Разом без ПДВ», the file act_missing_label.xlsx and the sheet «КБ-2в»>   (stderr)
$ echo $?
3
```

No report files are written in `--out`.

**Overwrite refused, code 3** (AC-13)

```console
$ act-verifier --contract contract_example.xlsx --act act_example.xlsx --journal ACT_EXAMPLE.XLSX
<message: the verifier never writes to its inputs>        (stderr)
$ echo $?
3
```

Nothing is written, and `act_example.xlsx` is byte-for-byte unchanged.

## 8. Stability

- Stable in v0.1: the option names (§2), the outcome codes (§3), the `InputError.kind` values (§4),
  the Excel sheet name and columns (§6.1), the journal header and its rules (§6.4).
- Not stable: the stderr wording, the console layout around the evidence block.
- The stage-2 assistant tool (roadmap step 2) reuses `load_contract`, `load_act` and `verify`, not this
  command (sad §2). This contract does not bind it.
- `contract_version` is bumped only by the owner, with a changelog line.
