---
status: Draft
owner: "AlexanderSW"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-11-26"
feature_size: "S"
---

# Spec — cli-verifier

> **Glossary:** [CONTEXT](../../../CONTEXT.md) (repo-root; no feature-level CONTEXT)
> **Reference module / docs / channels used:** `docs/idea-brief.md` (§2–§8, outcome `ready-for-specify`), `docs/checks.md`, `README.md` («Формат вхідних файлів», «План реалізації»), `CLAUDE.md`, `src/act_verifier/*.py`, `tests/*.py`, `scripts/generate_fixtures.py`, `tests/fixtures/*/expected.json`.

## 1. Context

The verifier core is a stub: loading, checking, reporting and the command line all fail with «not implemented», and every one of the 14 reference scenarios is marked as an expected failure (brief §2, source-verified). As a result the project owner cannot verify an act at all — neither from the command line nor from tests — and the chain «preparing agent prepares the act → verifier checks → accepting person decides» (README) has no middle link.

Why now: the project owner expects real acts to arrive in an employer's test assignment (brief §4, owner-reported, no date). Before then the core must work on the synthetic data set and must not break silently on a different file layout; the employer reviewer will judge the project by exactly that.

Committed approach (owner-accepted in brief §7, 2026-11-25): implement stage 1 of the README plan — read the contract price and acts by locating layout labels instead of fixed row numbers, run checks C01–C13 from `docs/checks.md` with their skip rules, produce a report that ends with the evidence block, and expose it all as a command with distinct outcome codes for pass / fail / needs_review / input error. The «headroom for real acts» is made testable, not just declared: 2–3 new layout fixtures (shifted header, totals not right after the table, missing label) are added through the fixture generator. An independent devil's-advocate pass over the brief (this stage) found three ambiguities that would have let two engineers build different verifiers — label-vs-data on a missing label, which operands of the totals checks are read vs computed, and a silent `pass` when previous acts are missing — all three are resolved below rather than left to implementation.

Traceability and decisions taken in this specify run (owner, 2026-11-26), on top of brief §5/§7:
- Input error and invocation error share one outcome code, 3; codes 0/1/2 stay pass/fail/needs_review (brief §8 OQ 1).
- The error journal is off by default and enabled only by the explicit `--journal` option with an optional path (default location: the repository journal) (brief §8 OQ 1 + OQ 4: decision confirmed after correcting the fact that the journal file is tracked, not ignored).
- Layout labels match after normalization (trim, collapse any whitespace incl. non-breaking, ignore case) by prefix; the VAT label does not require «20%»; more than one candidate row for a label is an input error, never «take the first» (brief §8 OQ 2).
- A missing layout label (sheet, header columns, any of the three КБ-2в totals labels, any of the four КБ-3 labels) is an input error; a label present with an empty value is missing data → `unknown`.
- Fewer previous acts than the act number implies (or numbers other than 1…N−1) → C05 and C13 are `unknown`, never `pass`.
- The expected-error scenario is expressed by a new optional field in the reference file and is checked at command-outcome level as well (brief §8 OQ 3).
- An empty amount leaves C04 not checked and makes C07 unknown; a formula cell without a stored value counts as empty.
- A run whose report or journal would overwrite an input file is refused with outcome code 3.
- Journal escaping applies only to text fields that are not numbers (e.g. a position code beginning with «=», «+», «-», «@»); numbers in the expected/actual columns are written exactly as read.
- Scope extension over brief §7 («2–3 new layout fixtures»): seven new generator scenarios — shifted header, totals not right after the table, missing label, ambiguous label, empty quantity, empty amount, incomplete previous acts — so that every AC is backed by a generator scenario rather than ad-hoc temporary files (the approach the brief rejected).

Derived from the fixtures, not an owner decision (source-verified: `scripts/generate_fixtures.py` scenarios subtotal_mismatch, vat_error, kb3_mismatch, combo_three_errors):
- Totals checks compare against the values printed in the act: C08 uses the printed «Разом без ПДВ», C09 the printed subtotal and VAT, C10 the printed КБ-2в «Всього з ПДВ», C13 Σ printed КБ-2в «Всього з ПДВ» of previous acts + the current КБ-2в «Всього з ПДВ».

## 2. Goals

- The project owner can verify any act in the README layout end-to-end and get a verdict, a findings report and an evidence block — the 14 reference scenarios turn from expected-failure into passing.
- Layout headroom is demonstrated, not claimed: acts whose labels sit in different rows still verify, and an unrecognised layout stops with a clear input error instead of a silent wrong result.
- The verifier never reports `pass` on missing data and never touches its inputs, so an accepting person can rely on a `pass`.

## 3. Non-goals

- Real employer acts — out of scope until the test assignment provides them (brief §5); stage 1 is proven on synthetic files only.
- The stage-2 assistant tool interface (README plan step 5) — explicitly a later stage.
- Numbers written as text («1 250,50»), position codes with non-standard hyphens, zero quantity and a dedicated C13 `fail` fixture — deferred by the owner to keep number parsing out of stage 1 (brief §5).
- Any change to how an act is accepted or rejected — the verifier reports, the accepting person decides (README).

## 4. User stories

### US-01: Verify an act from command line

**As a** project owner
**I want** to run the verifier on a contract price, the previous acts and the current act
**So that** I get the verdict, a findings report and an evidence block from one command

### US-02: Trust report through evidence

**As an** accepting person
**I want** every report to end with an evidence block that lists what was checked, what was not and why, and which file, sheet and row each number came from
**So that** I can decide on the act without re-checking the arithmetic by hand

### US-03: Branch on outcome code

**As a** preparing agent
**I want** a distinct outcome code for pass, fail, needs_review and input error
**So that** I can fix the act, hand it to a person, or fix my invocation without parsing text

### US-04: Verify act with different layout

**As an** employer reviewer
**I want** an act whose labels sit in different rows to verify the same way, and an unrecognised layout to stop with an input error naming the missing label
**So that** I can safely try the tool on real acts

### US-05: Log errors only on request

**As a** project owner
**I want** the error journal to be written only when I explicitly ask for it
**So that** demo and reference-scenario runs do not pollute the tracked journal

### US-06: Prove readiness on reference scenarios

**As a** project owner
**I want** the 14 existing reference scenarios, the new layout scenarios and the expected-input-error scenario to pass, including their outcome codes
**So that** «done» is verified by tests, not by eye

## 5. Acceptance criteria

### AC-01 (US-01) — happy path

**Given** a project owner has a contract price, the complete set of previous acts and a current act with no discrepancies (reference scenario «ok_many»)
**When** the project owner runs the verifier on them
**Then** the verifier reports verdict pass with outcome code 0, produces a findings report that lists every check applied to every position and to the act — including the passing ones — and ends the report with the evidence block

### AC-02 (US-01) — happy path (multiple discrepancies)

**Given** a current act with three discrepancies at once — a non-contract price on one position, an overrun of remaining volume on another, and a КБ-3 certificate that disagrees with the КБ-2в totals (reference scenario «combo_three_errors»)
**When** the project owner runs the verifier
**Then** the verifier reports all three findings with status fail, each with its expected and actual value, does not stop at the first one, and reports verdict fail with outcome code 1

### AC-03 (US-02) — happy path (evidence block)

**Given** any act the verifier was able to read
**When** the accepting person opens the report
**Then** the report ends with an evidence block that states how many positions and checks were verified, lists every check that was not performed together with the position and the reason, names the file, sheet and rows each group of numbers was actually read from (rows as found in that file, not as assumed by the README), gives the count of discrepancies by status, and repeats the verdict

### AC-04 (US-02) — domain invariant (missing data is never pass)

**Given** a current act where one position has an empty unit price but a filled amount (reference scenario «missing_price»)
**When** the project owner runs the verifier
**Then** the verifier reports that position's required-values check as unknown, lists its price and arithmetic checks under «not checked» with the reason «empty price» instead of reporting them as findings, and reports verdict needs_review with outcome code 2 — never pass and never a substituted price

### AC-05 (US-02) — domain invariant (what each missing value suppresses)

**Given** a current act where a position has an empty quantity, an empty price or an empty amount
**When** the project owner runs the verifier
**Then** an empty quantity leaves the arithmetic and remaining-volume checks of that position not checked; an empty price leaves the price and arithmetic checks not checked; an empty amount leaves the arithmetic check not checked and makes the subtotal check unknown, naming the position whose amount is missing — a formula cell without a stored value counts as empty; in every case the required-values check is unknown and the verdict is at best needs_review (new generator scenarios with an empty quantity and an empty amount)

### AC-06 (US-03) — error (invocation error)

**Given** a preparing agent invokes the verifier without a required input or with an option the verifier does not know
**When** the verifier starts
**Then** it stops with outcome code 3, explains in plain language which input is missing or which option is unknown, and produces no report and no verdict — the code is never the needs_review code

### AC-07 (US-04) — error (missing layout label)

**Given** an input file in which a layout label cannot be found — for the contract price: the sheet «Договірна ціна» and the header columns «Шифр», «Найменування», «Од. виміру», «Кількість», «Ціна», «Вартість»; for the current act: the sheets «КБ-2в» and «КБ-3», the same header columns, «Разом без ПДВ», «ПДВ», «Всього з ПДВ» and the four КБ-3 labels; for a previous act: the sheet «КБ-2в», its header columns, «Всього з ПДВ» and the act number (new reference scenario with a missing label)
**When** the employer reviewer runs the verifier
**Then** it stops with outcome code 3 and a message that names the missing label, the file and the sheet, and produces no verdict; a label that is present but whose value cell is empty is not this case — it is missing data and yields unknown

### AC-08 (US-04) — error (ambiguous layout)

**Given** an input file in which more than one row matches the same layout label after normalization (new reference scenario with an ambiguous label)
**When** the employer reviewer runs the verifier
**Then** it stops with outcome code 3 and a message that names the label and the competing rows, and never silently uses the first match

### AC-09 (US-04) — happy path (shifted layout)

**Given** an act whose header row sits in a different row than the README describes, or whose totals rows do not follow the table immediately (new reference scenarios), but whose labels match after normalization by prefix
**When** the employer reviewer runs the verifier
**Then** the verifier produces the same verdict and findings as for the equivalent act in the README layout, and the evidence block cites the rows where the data was actually found

### AC-10 (US-01) — cross-context (remaining volume from previous acts)

**Given** a contract price, the complete set of previous acts, and a current act where one position's quantity exceeds the contracted quantity minus the sum of that position in previous acts (reference scenario «volume_overrun»)
**When** the project owner runs the verifier
**Then** the verifier reports the remaining-volume check for that position as fail, with the remaining volume as the expected value and the act quantity as the actual value, citing the contract price and each previous act as sources

### AC-11 (US-03) — cross-context (incomplete previous acts)

**Given** a current act numbered N and a set of previous acts that is not exactly acts 1…N−1 (fewer files, a duplicate number, or the act number cannot be read) (new reference scenario with incomplete previous acts)
**When** the preparing agent runs the verifier
**Then** the remaining-volume check of every position and the cumulative КБ-3 check are unknown with the reason «previous acts supplied: K of N−1» (or «act number not readable» when N is unknown, or «duplicate previous act number M» when numbers repeat), all other checks still run, and the verdict is at best needs_review with outcome code 2 — never pass

### AC-12 (US-01) — cross-context (КБ-3 against КБ-2в)

**Given** a current act whose КБ-3 «Всього за звітний період» differs from its КБ-2в «Всього з ПДВ» while the cumulative КБ-3 total equals the printed «Всього з ПДВ» of previous acts plus the current КБ-2в «Всього з ПДВ» (reference scenario «kb3_mismatch»)
**When** the project owner runs the verifier
**Then** the verifier reports only the КБ-3-matches-КБ-2в check as fail and the cumulative check as pass — totals checks compare against the values printed in the act, not against recomputed ones

### AC-13 (US-01) — authorization (inputs are never modified)

**Given** a project owner runs the verifier on any inputs, including a run where the report or journal location would coincide with one of the input files
**When** the run finishes
**Then** every input file is byte-for-byte unchanged; a run whose report or journal would overwrite an input is refused before anything is written, with outcome code 3 and an explanation that the verifier never writes to its inputs

### AC-14 (US-05) — happy path (opt-in journal)

**Given** a project owner runs the verifier on an act with fail, unknown or warning findings
**When** the run is made without the journal option, with the journal option alone, or with the journal option and a chosen journal location
**Then** without the option the journal is left untouched; with the option alone one line per fail, unknown or warning finding is appended to the default journal; with a location the lines are appended there; every line names the verifier as the finder and leaves the resolution empty; a text field that is not a number and begins with «=», «+», «-» or «@» is escaped so it cannot become a formula, while numbers are written exactly as read

### AC-15 (US-06) — happy path (reference scenarios)

**Given** the 14 existing reference scenarios plus the seven new generator scenarios (shifted header, totals not right after the table, missing label, ambiguous label, empty quantity, empty amount, incomplete previous acts), all produced by the fixture generator, and a command-level check that points the report location at an input file
**When** the project owner runs the test suite
**Then** every scenario passes rather than being marked as an expected failure: verdict scenarios match their expected findings and verdict exactly, the expected-input-error scenario matches its expected error kind and label, each scenario is also run through the command and matches its outcome code (0, 1, 2 or 3), scenarios with outcome code 0, 1 or 2 also produce the evidence block while outcome code 3 produces no report, and the fixture-integrity suite stays green with its reference-file schema extended to accept the new optional expected-error field

### AC-16 (US-01) — domain invariant (empty act)

**Given** a current act with no positions (reference scenario «empty_act»)
**When** the project owner runs the verifier
**Then** the verifier reports the act-not-empty check as warning and verdict needs_review with outcome code 2 — an empty act is never accepted silently

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Run time for one act (11 positions, 2 previous acts — the «ok_many» scenario) | ≤ 5 s wall-clock on the developer laptop | timing of the «ok_many» scenario in the test suite |
| Money and quantity accuracy | exact decimals, tolerance ±0.01 UAH as in docs/checks.md; 0 floating-point operations in arithmetic | code review + all reference scenarios |
| Determinism | 0 differences in findings and evidence block across 2 runs on the same inputs | test comparing the outputs of two runs |
| Input immutability | 0 bytes changed in any input file | test comparing file hashes before and after a run |
| False pass | 0 runs reporting pass while data is missing or a discrepancy exists | reference scenarios + AC-04, AC-05, AC-11 |
| Platform | Windows + Git Bash, Python ≥ 3.11 | `.venv/Scripts/python -m pytest -q` |

## 6.1 Security / privacy

- **Data classification:** internal — the repository data is synthetic; real acts are confidential commercial documents and stay outside the repository.
- **Personal data touched:** none — acts name legal entities, the verifier reads no personal fields.
- **AuthZ/AuthN impact:** none added — a local, read-only tool; the only enforced boundary is «never write to an input file» (AC-13).
- **Abuse cases:**
  - formula cell without a stored value: treated as an empty value → unknown, never evaluated or guessed.
  - report or journal location pointing at an input: refused before any write, input error (AC-13).
  - journal injection: a non-numeric text field beginning with «=», «+», «-» or «@» is escaped so it cannot become a formula when opened in a spreadsheet; numbers are written exactly as read (AC-14).
  - file that is not a readable workbook: input error, outcome code 3, no partial report.
- **Security review:** N/A — local read-only tool, no new authorization boundary, no personal data.

## 7. Metrics / KPIs

- **Reference scenarios passing** — baseline: 0 of 14 (all expected failures), target: 14 of 14 plus every new layout and expected-input-error scenario by the end of stage 1.
- **Outcome codes exercised by tests** — baseline: 0 of 4, target: 4 of 4 (0, 1, 2, 3) by the end of stage 1.
- **Real employer acts verified without changing how files are read** — baseline: TBD (no real act yet); measurement plan: on the first real act from the test assignment, run the verifier unchanged and record verified / input error with the missing label; target: the first real act either verifies or fails with an input error naming the label — never a silent wrong verdict.

## 8. Open questions

- [ ] What layout do the employer's real acts use? Default now: the README layout plus prefix-normalized labels. — owner: AlexanderSW, due: when the first real act arrives
- [ ] Update docs/checks.md with the rules fixed in this spec (C07 unknown on an empty amount, C05 not checked on an empty quantity, C05/C13 unknown on incomplete previous acts, read-vs-computed operands of C08–C13, missing or ambiguous layout label = input error, refusal to overwrite an input)? Default now: this spec is the source until then. — owner: AlexanderSW, due: before sdd:tasks
- [ ] Update the expected pre-implementation test state in CLAUDE.md («16 passed, 14 xfailed») once new scenarios exist? Default now: update in the same commit as the generator change, with the reason. — owner: AlexanderSW, due: before sdd:implement
