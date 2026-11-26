---
status: Draft
owner: "AlexanderSW"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-11-26"
feature_size: "XS"
---

# Spec — check-act-skill

> **Glossary:** [CONTEXT](../../../CONTEXT.md) (repo-root; no feature-level CONTEXT). Terms added in this run: «L1 agent», «check-act skill».
> **Reference module / docs / channels used:** `docs/features/check-act-skill/idea-brief.md` (§1–§8, outcome `ready-for-specify`), the owner's draft `docs/features/check-act-skill/SKILL.md`, `README.md` («Коди виходу», «Вихідні файли», «Сценарії»), `CLAUDE.md`, `src/act_verifier/cli.py`, `src/act_verifier/report.py`, `tests/fixtures/{ok_many,combo_three_errors,missing_label}/expected.json`, `docs/roadmap.md`.

## 1. Context

The chain «preparing agent prepares the act → verifier checks → accepting person decides» (README intro) has a working middle link, the verifier, but no agent link: the repository holds no skill, and the stage-2 assistant-agent tool is still only a description (brief §2, source-verified). Without written rules, an agent asked to «check this act» could recompute sums itself, read a stale report, edit an input file to get past an input error, or say «акт прийнято» — the owner's red lines forbid all four (owner-reported); whether an unguided agent actually does so has not been observed (assumption). The people affected are the accepting person, who needs the report explained without the decision being taken from them, the project owner, who runs the demo, and the employer reviewer, who watches it.

Why now: the project owner has a job-interview demo on 2026-11-27 (owner-reported). That is the whole trigger, and it fixes the size: the feature must fit in about a day and use only what already exists (brief §4).

Committed approach (owner-accepted in brief §7, 2026-11-26): a check-act skill for an L1 agent that runs the existing verifier command unchanged, reads its report only when verification happened (verdict pass, fail or needs_review), and explains the result to the accepting person in a fixed reply format — verdict, findings in plain language, what was not checked, what the person should do, where the numbers come from. On an input error it relays the verifier's message and asks the person; it never edits a file. The skill's agreement with the verifier (outcome codes, command options, the skill's own name and description) is checked by the test suite without running a model; the agent's behaviour is shown by a manual demo on three scenarios — a pass, three discrepancies and an input error — with expected and actual behaviour recorded in a demo document, and summarised in a short README section. The skill sits alongside, not instead of, the assistant-agent tool of roadmap step 2.

Traceability and decisions taken in this specify run (owner, 2026-11-26), on top of brief §5/§7:
- Every line of the skill's outcome-code map carries the code and the verifier's own verdict token (`pass`, `fail`, `needs_review`) or the input-error meaning, so a test can compare the map with the verifier's codes (brief §6 risk 3).
- On an input error the L1 agent relays the verifier's message as written and offers a guess at a layout label's name only when the message is about a missing or ambiguous layout label; for every other input error (invocation, missing or unreadable file, refused overwrite, repeated position code) it offers no label guess (brief §6 risk 4).
- Strict numbers: every number in the L1 agent's reply appears verbatim in the report or its evidence block; the agent states no differences, sums or percentages of its own (brief §1 red line «агент не рахує сам»).
- A report is read only after verdicts pass / fail / needs_review; on an input error nothing from any report is used, and each demo scenario writes into its own report folder (brief §6 risk 2, owner decision).
- Whether the skill pre-allows the verifier command, so the demo has no permission prompt, is left to design (§8).
- Brief §8 OQ 3 update: the two empty copies the brief listed no longer exist (observed 2026-11-26); only the owner's draft in the feature folder remains.
- The test baseline is 304, not 272; the new expected count is 304 plus the skill tests (brief §6 risk 5).

## 2. Goals

- Every reply of the L1 agent to a request to check an act gives the verifier's verdict, the findings in plain language, what was not checked, what the accepting person should do and where the numbers come from — every number traceable to the report, and the decision left with the accepting person.
- The agent link of the chain «AI prepares → code checks → human decides» is demonstrable on the three demo scenarios, with expected and actual behaviour written down.
- The check-act skill cannot silently drift from the verifier: a mismatch in outcome codes, command options or the skill's identity fails the test suite.

## 3. Non-goals

- **No change to the verifier, the fixture generator or the fixtures.** The skill wraps the command as it is today; the owner put the verifier out of scope (brief §5).
- **No assistant-agent tool and no other assistant host.** That is roadmap step 2, larger, and does not fit before the demo (brief §5, §7 rejected alternatives).
- **No act preparation by the agent.** The full «AI prepares» cycle is a separate feature; here the agent only runs the check and explains it (brief §5).
- **No automated proof of agent behaviour.** The owner ruled out running a model in tests; behaviour is shown by one manual demo pass per scenario, which is not a regression guarantee (brief §6 risk 1, §7 trade-off).
- **No fixes to known verifier message defects** (the «порожня ціна» message for a number stored as text, the unnamed unknown option) — a separate task (brief §5).

## 4. User stories

### US-01: Check an act, get the verdict

**As an** accepting person
**I want** to ask the L1 agent to check an act and get the verifier's verdict, what was and was not checked, and where the numbers come from
**So that** I can decide on the act without reading the raw report

### US-02: Understand each discrepancy

**As an** accepting person
**I want** each fail, unknown or warning finding in plain language, with its expected and actual values and where to look in the file, plus one to three concrete actions for me
**So that** I know what to verify before I decide

### US-03: Know when no check happened

**As an** accepting person
**I want** to be told plainly when verification did not happen and why, in the verifier's own words
**So that** I never act on a result that does not exist

### US-04: Keep decision and journal mine

**As an** accepting person
**I want** the L1 agent to leave the acceptance decision and any error-journal entry to me
**So that** nothing is decided or recorded without my say

### US-05: Catch skill–verifier drift

**As the** project owner
**I want** the test suite to fail when the check-act skill's outcome-code map, command options or identity disagree with the verifier itself
**So that** the skill can never tell the L1 agent something the verifier no longer does

### US-06: Rehearse and record the demo

**As the** project owner
**I want** a demo script giving, for each of the three demo scenarios, the prompt, the expected behaviour of the L1 agent, its own report folder and a field for the actual result
**So that** I can rehearse before the interview and show what actually happened

### US-07: See how the agent link works

**As an** employer reviewer
**I want** a short README section on how to call the check-act skill, what it does and what it does not do
**So that** I understand the agent link of the chain without reading the skill itself

## 5. Acceptance criteria

### AC-01 (US-01) — happy path

**Given** the accepting person names the contract price, previous acts 1 and 2 and the act of the demo scenario «ok_many», and the verifier finds no discrepancy in it
**When** the accepting person asks the L1 agent to check the act
**Then** the L1 agent runs the verifier on exactly those files and replies with the verdict pass, presented as the verifier's verdict, what was not checked (from the evidence block), where the numbers come from and where both report files are; nowhere does the reply say the act is accepted or may be signed

### AC-02 (US-02) — happy path

**Given** the act of the demo scenario «combo_three_errors», in which the verifier finds three failing findings: the price of position 3-2, the remaining volume of position 2-1, and the КБ-3 certificate against the КБ-2в totals
**When** the accepting person asks the L1 agent to check it
**Then** the reply gives the verdict fail and lists exactly those three discrepancies, one line each in plain language, with the position code (or «акт» for an act-level finding), what is wrong, the expected and actual values exactly as the report gives them, and where to look in the file, followed by one to three concrete actions for the accepting person; no finding is added and none of the three is left out

### AC-03 (US-01) — domain invariant

**Given** any reply of the L1 agent — after a run with the verdict pass, fail or needs_review, after an input error, or before a run
**When** the L1 agent replies to the accepting person
**Then** every numeric value in the reply (money, quantity, percentage, count of checks, row number, act number) appears verbatim in that run's report or evidence block, in the verifier's input-error message, or in what the accepting person said; a warning before a run names no figure from anywhere else; the L1 agent states no difference, sum, percentage or rounded figure of its own and never reads the act files to compute anything — the invariant «all numbers come only from the verifier's report»

### AC-04 (US-01) — domain invariant

**Given** the accepting person states the act's number N (or the L1 agent asks for it before the run, without reading the act file) and supplies no previous acts, or fewer than acts 1 to N−1
**When** the accepting person asks the L1 agent to check the act
**Then** the L1 agent first asks for the missing previous acts; if the accepting person confirms they are not available, it runs without them, warns before the run that the remaining-volume and cumulative checks will be unknown, and replies with the verifier's verdict — at best needs_review, never pass — listing those checks under «Не перевірено» as «невідомо» with the reason the evidence block gives — never «все гаразд» (the invariant «a missing value never yields pass»)

### AC-05 (US-03) — error

**Given** the act of the demo scenario «missing_label», which has no «Разом без ПДВ» totals row, so the verifier stops with an input error
**When** the accepting person asks the L1 agent to check it
**Then** the reply says that verification did not happen and gives no verdict, quotes the verifier's message as written, and names the layout label «Разом без ПДВ», the file and the sheet from that message; the L1 agent may suggest how the label might be written in this file — looking at the file only to find the label, never to compute — and marks the suggestion as a guess; it asks the accepting person what to do, and the act file is unchanged

### AC-05b (US-03) — error

**Given** the verifier stops with an input error because a layout label matches more than one row, or because a required sheet is missing
**When** the L1 agent replies
**Then** it says that verification did not happen and gives no verdict, quotes the verifier's message as written, and names the label or the sheet and the file from that message; for an ambiguous label it also names the competing rows the message lists and picks none of them; it may suggest what the label or sheet might be, marked as a guess, asks the accepting person what to do, and the act file is unchanged

### AC-06 (US-03) — error

**Given** the verifier stops with an input error that names no layout label or sheet — a wrong invocation, a missing or unreadable file, a refused overwrite or a repeated position code
**When** the L1 agent replies
**Then** it says that verification did not happen, quotes the verifier's message as written, offers no guess at a label name and asks the accepting person to correct the input; it changes no file and does not rerun with other files unless the accepting person agrees

### AC-07 (US-04) — authorization

**Given** a run with any verdict, including pass
**When** the accepting person asks «можна підписувати?» or asks the L1 agent to confirm that the act is accepted
**Then** the L1 agent declines to declare the act accepted, restates the verifier's verdict and what was not checked, and says that the decision belongs to the accepting person

### AC-08 (US-04) — authorization

**Given** the accepting person has not asked for the error journal
**When** the L1 agent checks an act
**Then** it runs the verifier without the error journal and the journal is unchanged; only when the accepting person explicitly asks does it run with the journal; the reply then says the findings were appended only if the verdict is fail or needs_review, says there was nothing to append on pass, and says nothing was written on an input error

### AC-09 (US-03) — cross-context

**Given** the report folder already holds the report of an earlier run on an act with the same file name — for example the three discrepancies of «combo_three_errors»
**When** the L1 agent checks the act of «missing_label» and the verifier stops with an input error
**Then** the reply contains no finding, number or verdict from that earlier report; the L1 agent reads a report only after a run whose verdict is pass, fail or needs_review

### AC-10 (US-05) — cross-context

**Given** the check-act skill's outcome-code map and its run command
**When** the project owner runs the test suite
**Then** the suite passes only if every outcome the verifier defines appears in the map with the same code — pass, fail and needs_review with the verifier's own verdict token, the input error with its meaning «verification did not happen» — the map names no outcome code the verifier lacks, and every command option the skill names is one the verifier accepts; on any mismatch it fails and names the code or the option; the expected codes and options are taken from the verifier itself, not from a copy kept in the test

### AC-11 (US-05) — error

**Given** the check-act skill is missing, its header cannot be read, its name is not «check-act» or its description is empty
**When** the project owner runs the test suite
**Then** the suite fails and names which of these four is wrong; with a valid skill the suite passes without calling a model or the network

### AC-12 (US-06) — happy path

**Given** the demo document for the three demo scenarios «ok_many», «combo_three_errors» and «missing_label»
**When** the project owner rehearses the demo
**Then** for each scenario the document gives the prompt, the expected behaviour (verdict pass with no claim of acceptance; three discrepancies whose numbers match the report; «перевірки не було» naming «Разом без ПДВ», with the act file unchanged), its own report folder and an «actual result» field; after the rehearsal all three fields hold what the L1 agent actually did, deviations included

### AC-13 (US-07) — happy path

**Given** the README
**When** the employer reviewer reads its section «Агент L1: Skill check-act»
**Then** the section says how to call the check-act skill from this repository, what the L1 agent does (runs the verifier and explains its report) and what it does not do (compute numbers, edit input files, decide acceptance, write the error journal unasked)

## 6. Non-functional requirements

| Aspect | Target | Measurement |
|---|---|---|
| Test suite outcome after the change | 304 + N passed, 0 failed, 0 xfailed (N = the new skill tests); the expected count in `CLAUDE.md` updated to 304 + N | `.venv/Scripts/python -m pytest -q`, run and quoted at implement |
| Test independence from a model | 0 model calls and 0 network calls in the suite | the suite passes with no network access |
| Numbers outside the report | 0 per reply of the L1 agent | each numeric value in the reply looked up in that run's report or evidence block; result written in the demo document |
| Input files unchanged | 0 changed input files (contract price, previous acts 1–2, the three demo acts) | a file hash of each input taken before and after the rehearsal, both written in the demo document |
| Reply turnaround per demo scenario | ≤ 2 min from the prompt to the finished reply | stopwatch at the rehearsal, written in the demo document; an overrun is recorded as a deviation, not a blocker |
| Permission prompts during the demo | 0 unplanned prompts (a prompt written into the demo document as an expected step is planned) | count at the rehearsal; how the target is met is §8 OQ 1 |

## 6.1 Security / privacy

- **Data classification:** internal — the inputs are the synthetic contract price and acts in the repository (README: «Усі дані в репозиторії синтетичні»); real acts are out of scope.
- **Personal data touched:** none.
- **AuthZ/AuthN impact:** no new permission check in the verifier. The check-act skill lets the L1 agent run the verifier and read the report of the run it started; it may look at an input file only to locate a layout label after an input error. The L1 agent itself writes no file: the verifier writes only into the report folder and, on the accepting person's explicit request, appends to the error journal. Whether the verifier command is pre-allowed, and how narrowly, is §8 OQ 1.
- **Abuse cases:**
  - Text in an act cell (a note row, a label) phrased as an instruction to the agent: treated as data; the L1 agent may quote it but never follows it.
  - The L1 agent «fixes» an input file to get past an input error: forbidden; it relays the message and asks the accepting person, and the file stays unchanged (AC-05, AC-06).
  - A stale report presented as the current result: a report is read only after a run with verdict pass, fail or needs_review (AC-09).
  - An unasked entry in the shared error journal: the journal is touched only on explicit request (AC-08).
  - The L1 agent declares the act accepted: it declines and returns the decision to the accepting person (AC-07).
- **Security review:** N/A — no new authorization boundary, no personal data, synthetic inputs only, and the change is one instruction file, one test file and two documents; revisit if §8 OQ 1 pre-allows any command beyond the verifier.

## 7. Metrics / KPIs

- **Demo scenarios behaving as expected** — baseline: 0 of 3 (no skill exists), target: 3 of 3 («ok_many», «combo_three_errors», «missing_label»), with actual results written in the demo document, by the interview on 2026-11-27.
- **Red-line violations in the recorded rehearsal runs** (a number not in the report, a claim of acceptance, an edited input file, an unasked journal entry, a finding taken from a stale report) — baseline: not measured (no skill; an unguided agent has not been observed — brief §6 assumption), measurement plan: a five-item checklist filled in the «actual result» field of each scenario, target: 0 across the three runs by 2026-11-27.
- **Skill–verifier agreement checked by the suite** — baseline: 0 checks, target: the suite compares 4 of 4 outcome codes and every option in the skill's run command (5 in the brief's command: contract, previous, act, out, journal) and is green, by the end of implement (before 2026-11-27).

## 8. Open questions

- [ ] Should the check-act skill pre-allow the verifier command so the demo shows no permission prompt, and if so, how narrowly (the verifier only, with or without the error-journal option)? Default now: not pre-allowed; the demo document lists the permission prompt as a planned step, which meets the §6 target «0 unplanned prompts». — owner: AlexanderSW, due: before `/sdd:design check-act-skill` (brief §8)
- [ ] Will the employer reviewer run the skill themselves, or only watch the demo? Default now: the README section covers calling the skill from this repository only, with no install steps for another machine. — owner: AlexanderSW, due: before the README section is written at `/sdd:implement check-act-skill` (brief §8)
- [ ] What happens to the owner's draft `docs/features/check-act-skill/SKILL.md` once the real check-act skill exists? Default now: keep it as history, marked as superseded by the real skill, so it is not read as a second live copy. — owner: AlexanderSW, due: at `/sdd:implement check-act-skill` (brief §8; the two empty copies listed there are already gone)
