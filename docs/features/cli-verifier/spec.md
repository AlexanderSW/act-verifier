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

Decisions taken in the clarify run (owner, 2026-11-26):
- Act number N (current and previous acts) is read only from the КБ-2в title cell whose normalized text begins with «Акт №»; the file name and the КБ-3 «до акта №» text are not used. A missing or non-numeric act number is missing data (→ `unknown` of C05/C13), never an input error.
- Required inputs are the contract price and the current act; previous acts are optional (act 1 has none). Too few previous acts goes the AC-11 path, not the invocation-error path.
- Each run that reaches a verdict writes the report into the output folder (option, default `reports/`) as two files — an Excel workbook with the sheet «Перевірки» (code · check · status · expected · actual · source) and a Markdown file with the findings and the evidence block — and also prints the evidence block to the console. Report text is in Ukrainian; reasons quoted in English in this spec describe the content, not the literal wording (e.g. «empty price» = «порожня ціна»).
- КБ-2в table: from the header row down to the first «Разом без ПДВ» row below it. A position is a row with a non-empty position code; fully empty rows and rows without a code (e.g. a note) are skipped and counted in the evidence block as «skipped rows without a code». Totals labels are searched only below the header row.
- Value cells: a КБ-2в totals value is the cell in the «Вартість» header column on the label's row; a КБ-3 value is the cell immediately to the right of the label. The four КБ-3 label prefixes, all mandatory: «Вартість робіт за звітний період», «ПДВ», «Всього за звітний період», «З початку виконання робіт».
- An empty printed total makes `unknown` every check that uses it, naming the value: «Разом без ПДВ» → C07, C08, C09; «ПДВ» → C08, C09; «Всього з ПДВ» → C09, C10, C13; КБ-3 period total → C10; КБ-3 cumulative total → C13; a previous act's «Всього з ПДВ» → C13.
- Previous acts: an empty quantity of a position in a previous act makes C05 of that position `unknown`; a position code repeated within one previous act is summed (C06 applies to the current act only).
- «Coincides with an input file» means the fully resolved absolute paths are equal, compared case-insensitively (Windows).
- Journal: the default location is `journal/agent_errors.csv` relative to the current working directory; a chosen location that does not exist is created with the existing header line; escaping is a leading apostrophe.

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

**Given** a preparing agent invokes the verifier without a required input (the contract price or the current act; previous acts are optional) or with an option the verifier does not know
**When** the verifier starts
**Then** it stops with outcome code 3, explains in plain language which input is missing or which option is unknown, and produces no report and no verdict — the code is never the needs_review code

### AC-07 (US-04) — error (missing layout label)

**Given** an input file in which a layout label cannot be found — for the contract price: the sheet «Договірна ціна» and the header columns «Шифр», «Найменування», «Од. виміру», «Кількість», «Ціна», «Вартість»; for the current act: the sheets «КБ-2в» and «КБ-3», the same header columns, «Разом без ПДВ», «ПДВ», «Всього з ПДВ» and the four КБ-3 labels («Вартість робіт за звітний період», «ПДВ», «Всього за звітний період», «З початку виконання робіт»); for a previous act: the sheet «КБ-2в», its header columns and «Всього з ПДВ» (new reference scenario with a missing label)
**When** the employer reviewer runs the verifier
**Then** it stops with outcome code 3 and a message that names the missing label, the file and the sheet, and produces no verdict; a label that is present but whose value cell is empty is not this case — it is missing data and yields unknown for every check that uses that value; a missing or unreadable act number is likewise missing data (AC-11), not this case

### AC-08 (US-04) — error (ambiguous layout)

**Given** an input file in which more than one row matches the same layout label after normalization (new reference scenario with an ambiguous label)
**When** the employer reviewer runs the verifier
**Then** it stops with outcome code 3 and a message that names the label and the competing rows, and never silently uses the first match

### AC-09 (US-04) — happy path (shifted layout)

**Given** an act whose header row sits in a different row than the README describes, or whose totals rows do not follow the table immediately (new reference scenarios), but whose labels match after normalization by prefix — including empty rows or rows without a position code (e.g. a note) between the last position and «Разом без ПДВ»
**When** the employer reviewer runs the verifier
**Then** the verifier produces the same verdict and findings as for the equivalent act in the README layout, rows without a position code are not treated as positions, and the evidence block cites the rows where the data was actually found and the rows it skipped

### AC-10 (US-01) — cross-context (remaining volume from previous acts)

**Given** a contract price, the complete set of previous acts, and a current act where one position's quantity exceeds the contracted quantity minus the sum of that position in previous acts (reference scenario «volume_overrun»)
**When** the project owner runs the verifier
**Then** the verifier reports the remaining-volume check for that position as fail, with the remaining volume as the expected value and the act quantity as the actual value, citing the contract price and each previous act as sources

### AC-11 (US-03) — cross-context (incomplete previous acts)

**Given** a current act numbered N and a set of previous acts that is not exactly acts 1…N−1 (fewer files including none, a duplicate number, a number outside 1…N−1 including N itself, or an act number that cannot be read) (new reference scenario with incomplete previous acts)
**When** the preparing agent runs the verifier
**Then** the remaining-volume check of every position and the cumulative КБ-3 check are unknown with the reason «previous acts supplied: K of N−1», where K counts distinct act numbers within 1…N−1 (or «act number not readable» when the current act's N is unknown, «previous act number not readable» naming the file, «duplicate previous act number M», or «previous act number M outside 1…N−1»), all other checks still run, and the verdict is at best needs_review with outcome code 2 — never pass

### AC-12 (US-01) — cross-context (КБ-3 against КБ-2в)

**Given** a current act whose КБ-3 «Всього за звітний період» differs from its КБ-2в «Всього з ПДВ» while the cumulative КБ-3 total equals the printed «Всього з ПДВ» of previous acts plus the current КБ-2в «Всього з ПДВ» (reference scenario «kb3_mismatch»)
**When** the project owner runs the verifier
**Then** the verifier reports only the КБ-3-matches-КБ-2в check as fail and the cumulative check as pass — totals checks compare against the values printed in the act, not against recomputed ones

### AC-13 (US-01) — authorization (inputs are never modified)

**Given** a project owner runs the verifier on any inputs, including a run where the report or journal location would coincide with one of the input files (fully resolved paths equal, compared case-insensitively)
**When** the run finishes
**Then** every input file is byte-for-byte unchanged; a run whose report or journal would overwrite an input is refused before anything is written, with outcome code 3 and an explanation that the verifier never writes to its inputs

### AC-14 (US-05) — happy path (opt-in journal)

**Given** a project owner runs the verifier on an act with fail, unknown or warning findings
**When** the run is made without the journal option, with the journal option alone, or with the journal option and a chosen journal location
**Then** without the option the journal is left untouched; with the option alone one line per fail, unknown or warning finding is appended to the default journal (`journal/agent_errors.csv` relative to the current working directory); with a location the lines are appended there, creating the file with the journal's header line if it does not exist; every line names the verifier as the finder and leaves the resolution empty; a text field that is not a number and begins with «=», «+», «-» or «@» is escaped with a leading apostrophe so it cannot become a formula, while numbers are written exactly as read

### AC-15 (US-06) — happy path (reference scenarios)

**Given** the 14 existing reference scenarios plus the seven new generator scenarios (shifted header, totals not right after the table, missing label, ambiguous label, empty quantity, empty amount, incomplete previous acts), all produced by the fixture generator, and a command-level check that points the report location at an input file
**When** the project owner runs the test suite
**Then** every scenario passes rather than being marked as an expected failure: verdict scenarios match their expected findings and verdict exactly, the expected-input-error scenarios match their expected error kind (missing label or ambiguous label) and the label as written in this spec (e.g. «Разом без ПДВ»), while other input errors (unreadable workbook, invocation error, overwrite refusal) are checked by outcome code only, each scenario is also run through the command and matches its outcome code (0, 1, 2 or 3), scenarios with outcome code 0, 1 or 2 also produce the evidence block while outcome code 3 produces no report, and the fixture-integrity suite stays green with its reference-file schema extended to accept the new optional expected-error field

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
- [ ] Update docs/checks.md with the rules fixed in this spec (C07 unknown on an empty amount, C05 not checked on an empty quantity, C05/C13 unknown on incomplete previous acts, read-vs-computed operands of C08–C13, missing or ambiguous layout label = input error, refusal to overwrite an input, and from clarify: empty printed totals → unknown of the checks using them, empty quantity in a previous act → C05 unknown — these two rules have no generator scenario in stage 1)? Default now: this spec is the source until then. — owner: AlexanderSW, due: before sdd:tasks
- [ ] Update the expected pre-implementation test state in CLAUDE.md («16 passed, 14 xfailed») once new scenarios exist? Default now: update in the same commit as the generator change, with the reason. — owner: AlexanderSW, due: before sdd:implement

## Test plan

> Inline test plan (size S, route quick). Surface: `cli` (sad.md `target_surfaces`), so no UI tiers apply. It is written before the tests exist. `implement` reads the Level column as decided and does not re-decide it.

### Levels

| Level | Scope in this feature | Strategy |
|---|---|---|
| unit | One rule with no file I/O: label normalization and matching, one check (C01–C13) with its skip and unknown rules, previous-acts completeness, evidence-block rendering, journal-line escaping, option parsing and the overwrite guard. | In-memory models and small in-memory worksheets. No xlsx file is read from disk. |
| integration | The core (`load_contract`, `load_act`, `verify`, report building) against the real dependency it owns: workbook files on disk. | Reference fixtures produced by the fixture generator are read in place, read-only. Nothing is stubbed. |
| e2e | The command's real entry point, run the way a preparing agent runs it: arguments, then reading, checks, report files, outcome code. | Reference fixtures as inputs. The report and journal go to a per-test temporary folder. |
| contract | The command's public interface in `contracts/cli.md` and the reference-file schema (`expected.json`, with the new optional `expected_error` and `layout` fields). | Assert the real behaviour against the agreed document. No hand-written stand-ins. |

### AC coverage

| AC (spec.md §5) | Test name (intent-based) | Level | Expected outcome |
|---|---|---|---|
| AC-01 happy path | every check passes on a consistent act | unit | each check returns pass for a position and an act that agree with the contract and previous acts |
| AC-01 happy path | ok_many scenario yields pass with every check listed | integration | verdict pass, no non-pass findings, every check of every position and of the act is present in the findings |
| AC-01 happy path | command on ok_many exits with the pass code and writes a report | e2e | outcome code 0, both report files exist, the report ends with the evidence block |
| AC-02 multiple discrepancies | price, volume and КБ-3 discrepancies are each detected | unit | C03, C05 and C10 each return fail with the expected and actual values |
| AC-02 multiple discrepancies | combo_three_errors reports all three findings without stopping | integration | exactly the three expected fail findings, each with expected and actual value; verdict fail |
| AC-02 multiple discrepancies | command on combo_three_errors exits with the fail code | e2e | outcome code 1, report lists all three findings |
| AC-03 evidence block | evidence block renders all five parts from the report model | unit | block is last; it states the counts of positions and checks, the not-checked list with position and reason, file, sheet and rows per group of numbers taken from provenance, counts by status, and the verdict |
| AC-03 evidence block | evidence block cites the rows actually read from the fixture | integration | for ok_many and missing_price the cited files, sheets and rows equal the rows the loader read; missing_price lists its skipped checks with the reason |
| AC-03 evidence block | two runs on the same inputs give identical findings and evidence | e2e | findings and evidence block are identical across two runs into two separate folders |
| AC-04 missing price | empty price makes C11 unknown and skips C03 and C04 | unit | C11 unknown; C03 and C04 are not findings but appear as not checked with the reason «empty price»; no price is substituted |
| AC-04 missing price | missing_price scenario yields needs_review | integration | findings match the reference exactly; verdict needs_review |
| AC-04 missing price | command on missing_price exits with the needs_review code | e2e | outcome code 2, the evidence block lists the skipped checks for that position |
| AC-05 missing-value suppression | each empty value suppresses exactly its dependent checks | unit | empty quantity skips C04 and C05; empty price skips C03 and C04; empty amount skips C04 and makes C07 unknown, naming the position; C11 unknown in all three cases; the verdict is never pass |
| AC-05 missing-value suppression | formula cell without a stored value is read as empty | integration | a formula cell with no cached value loads as empty, never as zero or an evaluated value |
| AC-05 missing-value suppression | empty-quantity and empty-amount scenarios match their reference | integration | findings and verdict match the reference exactly; verdict needs_review |
| AC-05 missing-value suppression | command on the empty-value scenarios exits with the needs_review code | e2e | outcome code 2 for both scenarios |
| AC-07 missing layout label | absent label raises a missing-label input error | unit | no matching row or sheet → input error of kind missing label, naming the label, file and sheet |
| AC-07 missing layout label | label with an empty value cell is missing data, not an input error | unit | the checks that use the value are unknown; no input error |
| AC-07 missing layout label | missing-label scenario raises the expected error | integration | input error kind and label equal `expected_error` in the reference file |
| AC-07 missing layout label | command on the missing-label scenario exits with the input-error code and writes nothing | e2e | outcome code 3, message names the label, file and sheet, no report file in the output folder |
| AC-08 ambiguous layout | label matching several rows raises an ambiguous-label error | unit | input error of kind ambiguous label, naming the label and every competing row; the first match is never used |
| AC-08 ambiguous layout | ambiguous-label scenario raises the expected error | integration | input error kind and label equal `expected_error` in the reference file |
| AC-08 ambiguous layout | command on the ambiguous-label scenario exits with the input-error code | e2e | outcome code 3, message names the competing rows, no report file |
| AC-09 shifted layout | labels are found by normalized prefix wherever they sit | unit | the header and totals rows are found when shifted; empty rows and rows without a position code before «Разом без ПДВ» are not positions |
| AC-09 shifted layout | shifted scenarios give the same verdict as the README layout | integration | findings and verdict equal those of the equivalent README-layout scenario; rows cited in the evidence block equal the reference `layout` rows, including skipped rows |
| AC-09 shifted layout | command on the shifted scenarios exits with the same code as the README layout | e2e | same outcome code as the equivalent scenario |
| AC-10 remaining volume | quantity above the remaining volume fails C05 | unit | C05 fail; expected = contracted minus the sum over previous acts, actual = act quantity; contract and each previous act cited as sources |
| AC-10 remaining volume | volume_overrun scenario reports the overrun | integration | findings match the reference exactly; C05 cites the contract and both previous acts |
| AC-10 remaining volume | command on volume_overrun exits with the fail code | e2e | outcome code 1 |
| AC-11 incomplete previous acts | each completeness defect makes C05 and C13 unknown with its own reason | unit | one case per reason: «previous acts supplied: K of N−1» (fewer files including none, K counting distinct numbers in 1…N−1), «act number not readable», «previous act number not readable» naming the file, «duplicate previous act number M», «previous act number M outside 1…N−1» (including N itself); all other checks still run; verdict at best needs_review |
| AC-11 incomplete previous acts | incomplete-previous-acts scenario matches its reference | integration | findings and verdict match the reference exactly; verdict needs_review |
| AC-11 incomplete previous acts | command on incomplete previous acts exits with the needs_review code | e2e | outcome code 2, never 0 |
| AC-12 КБ-3 vs КБ-2в | totals checks compare against printed values | unit | C10 fail when КБ-3 «Всього за звітний період» differs from the printed «Всього з ПДВ»; C13 pass when the cumulative equals the printed previous totals plus the current one; no recomputed operand is used |
| AC-12 КБ-3 vs КБ-2в | kb3_mismatch scenario fails only C10 | integration | only C10 fails; C13 passes |
| AC-12 КБ-3 vs КБ-2в | command on kb3_mismatch exits with the fail code | e2e | outcome code 1 |
| AC-16 empty act | act with no positions warns C12 | unit | C12 warning; verdict needs_review |
| AC-16 empty act | empty_act scenario yields needs_review | integration | findings and verdict match the reference exactly |
| AC-16 empty act | command on empty_act exits with the needs_review code | e2e | outcome code 2, never 0 |
| AC-06 invocation error | missing required input or unknown option is an input error | unit | no contract price → input error naming that input; no current act → the same; an unknown option → input error naming the option; no previous acts → not an error; option parsing never exits on its own with the needs_review code |
| AC-06 invocation error | command with a missing input or unknown option exits with the input-error code | e2e | outcome code 3, a plain-language explanation, no report file, no verdict |
| AC-06 invocation error | options and outcome codes match the published command contract | contract | every option documented in `contracts/cli.md` §2 is accepted with its documented meaning; outcome codes 0, 1, 2 and 3 mean what §3 says |
| AC-13 inputs never modified | output path equal to an input is refused | unit | equal fully resolved paths are refused, including relative vs absolute spelling and letter-case differences; different files are allowed |
| AC-13 inputs never modified | inputs are byte-for-byte unchanged after a run, and an overwriting run is refused | e2e | input copies have the same hashes before and after a normal run; a run whose report or journal points at an input exits with outcome code 3, says the verifier never writes to its inputs, and writes nothing |
| AC-14 opt-in journal | journal lines are complete and injection-safe | unit | a new file gets the header line; an existing file is appended without a second header; one line per fail, unknown or warning and none for pass; the finder is the verifier and the resolution is empty; text starting with «=», «+», «-» or «@» gets a leading apostrophe; numbers are written exactly as read |
| AC-14 opt-in journal | command writes the journal only on request, in all three modes | e2e | without the option the default journal is unchanged; with the option alone the lines go to `journal/agent_errors.csv` under the temporary working directory; with a location the file is created there with its header |
| AC-15 reference scenarios | every reference scenario passes at the core level | integration | the expected-failure marker is removed; each of the 21 scenarios matches its findings and verdict exactly, or its expected error kind and label; shifted-layout scenarios cite the reference `layout` rows |
| AC-15 reference scenarios | every reference scenario exits with its outcome code through the command | e2e | outcome code 0, 1, 2 or 3 as the reference implies; codes 0–2 write a report ending with the evidence block; code 3 writes no report; pointing the report location at an input exits with code 3 |
| AC-15 reference scenarios | reference-file schema accepts the extended fields and the fixtures stay consistent | contract | the fixture-integrity suite is green; the schema accepts the optional `expected_error` (kind missing label or ambiguous label, plus the label) and `layout`; when `expected_error` is present, the verdict and findings are absent |

### Edge cases / error paths

Each error or authorization AC (AC-06, AC-07, AC-08, AC-13) has its own rows above. The boundary and failure cases the spec implies are listed below. Each one becomes its own test row at the level shown.

- File that is not a readable workbook, given as the contract or the act (unit + e2e) → input error, outcome code 3, no partial report.
- Input path that does not exist (unit + e2e) → input error naming the missing file, outcome code 3, no report.
- Label present but its value cell empty, for a printed total (e.g. «Разом без ПДВ» or a КБ-3 value) (unit) → every check that uses that value is unknown; not an input error; the verdict is at best needs_review.
- Empty quantity of a position in a previous act (unit) → C05 for that position is unknown. Stage 1 has no generator scenario for it (spec §8).
- Missing or unreadable current act number (unit) → missing data per AC-11, not a missing-label input error.
- Difference exactly at the ±0.01 UAH tolerance in C04 and C07–C10, C13, and just above it (unit) → at the tolerance: pass; above it: fail.
- Only the КБ-3 sheet is missing, or only the КБ-2в sheet (unit) → missing-label input error naming that sheet.
- Prefix collision during normalization: «ПДВ» also matching «ПДВ 20%» on the same sheet, where it must stay unique (unit) → resolves to exactly one row, or is an ambiguous-label error. Never the first match.
- Journal location equal to an input, spelled with a different letter case (unit + e2e) → refused before any write, outcome code 3.
- Money and quantities stay exact decimals (unit) → every loaded and computed money or quantity value is a decimal, never a floating-point number.

### Test data

- **Seed strategy.** Reference scenarios under `tests/fixtures/<scenario>/` (xlsx plus `expected.json`) and `data/synthetic/`, all produced only by `scripts/generate_fixtures.py`. The seven new scenarios are added there as well (tasks T2, T3). Fixtures and `expected.json` are never edited by hand. Unit tests build `Position`, `Act`, `Contract` and `Report` objects in memory, plus small in-memory worksheets for the layout helper, following the shapes in `data-model.md`.
- **Integration dependency.** Real workbook files on disk, read through the real loaders. There is no database, cache or queue in this feature, so no throwaway container is needed. Nothing is stubbed in front of the workbook reader.
- **Cleanup boundary.** Per test. Each e2e test writes reports and journals into its own temporary folder and runs from a temporary working directory, so it never touches the tracked `journal/agent_errors.csv` (sad.md §11, risk 5). Tests that must exercise writing near inputs (AC-13) copy the inputs into the temporary folder first. The reference fixtures in the repository are never a write target. Integration tests read fixtures in place and write nothing.

### NFR validation (load)

- **Run time** (spec §6: ≤ 5 s wall-clock for «ok_many», 11 positions and 2 previous acts). Scenario: one sequential run of the command on «ok_many» (rate: 1 run, no concurrency; duration: a single run). Metric: wall-clock time from start to exit. Threshold: ≤ 5 s. Level: e2e, measured with the timer the suite already uses. No dedicated load tool is needed. If one is ever needed, use the load tool already in the repo, or e.g. k6 or Locust.
- The other §6 rows carry numbers but are not about load. They are covered above: determinism (0 differences) → AC-03 e2e; input immutability (0 bytes changed) → AC-13 e2e; false pass (0 runs) → AC-04, AC-05, AC-11 and the AC-15 suite; money accuracy (±0.01 UAH, 0 floating-point operations) → the tolerance and decimal edge cases, plus code review.

### CI placement

- **On every change (local, before each commit):** unit, contract and integration. Integration reads files on disk only, so it is fast enough for every run.
- **Also on every change:** e2e, including the run-time check, because the whole suite runs in seconds. If the suite grows, the run-time scenario is the first candidate to move to a pre-release run.
- The repository has no CI pipeline yet. This split is advice. `implement` and the repository own the actual wiring.
