---
id: T3
title: "Write the skill's run steps: collect inputs, run the verifier, apply the verdict-source rule"
layer: "ports"
deps: ["T2"]
blocks: ["T4", "T5"]
acs: ["AC-01b", "AC-04", "AC-08", "AC-09"]
files_hint: [".claude/skills/check-act/SKILL.md"]
owner: "AlexanderSW"
estimate: "S"           # ~1.5 h
context_budget: "M"     # 58 inlined lines, 1 extra file (src/act_verifier/report.py for the report name)
status: "todo"
step: ""
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T3 — Write the skill's run steps: collect inputs, run the verifier, apply the verdict-source rule

## Place in the sequence

- **Blocked by:** T2 — outcome-code map + run-command block · **Blocks:** T4 — reply format and red lines, T5 — no-verification handling · **Wave:** 3 (the steps reference the run-command block and the code map from T2).
- **Lane:** skill lane — `SKILL.md` shared with T1, T2, T4, T5 → serialized.

## Why (user story)

> **As an** accepting person
> **I want** to ask the L1 agent to check an act and get the verifier's verdict, what was and was not checked, and where the numbers come from
> **So that** I can decide on the act without reading the raw report
>
> — `spec.md §4, US-01, verbatim` · full text: [spec.md](../spec.md)

> **As an** accepting person
> **I want** the L1 agent to leave the acceptance decision and any error-journal entry to me
> **So that** nothing is decided or recorded without my say
>
> — `spec.md §4, US-04, verbatim`

This task writes the «Кроки» section: what the agent asks before running, how it runs, and when it may read a report.

## Inlined context

> **Verdict source:** a run has a verdict only when the verifier exits with code 0, 1 or 2 **and** that run's output contains the line «Вердикт: pass|fail|needs_review». Exit code 1 without that line is a verifier crash: verification did not happen, no report is read […]. **No default inputs:** the L1 agent never substitutes a default path for the contract price, the previous acts or the act; it asks for every input the accepting person has not named. […] A report is read only after verdicts pass / fail / needs_review; on an input error nothing from any report is used, and each demo scenario writes into its own report folder.
>
> — `spec.md §1, traceability bullets 3, 4, 8, abridged` · full text: [spec.md](../spec.md)

> «Вердикт: <token>.» […] ends the evidence block's final line «Розбіжностей: … Вердикт: <token>.» (`report.py:129`), so the skill matches it anywhere in the output, not at a line start; otherwise no report is read.
>
> — `sad.md §4, choice 4, abridged` · full text: [sad.md](../sad.md)

> | Journal option | The run-command block lists `--journal` as a marked optional part; the L1 agent adds it only when the accepting person explicitly asks (AC-08) |
> | Report isolation | One `--out` folder per demo scenario (`reports/demo/<scenario>/`); the person may name the folder, else `reports/` |
> | Input handling | The L1 agent opens no input file and writes no file; the verifier writes only into `--out` and, on request, the journal |
>
> — `sad.md §8, rows Journal option, Report isolation, Input handling, verbatim` · full text: [sad.md](../sad.md)

> **Hard rule:** The skill says to start the command exactly with the prefix `.venv/Scripts/act-verifier` (no `cd … &&`, no `./`, no `python -m`).
>
> — `sad.md §11, risk 1, abridged`

Report files the verifier writes: `<out>/<act-stem>_report.md` and `<out>/<act-stem>_report.xlsx` — `src/act_verifier/report.py:30-34, report_paths(), abridged`. All three demo acts are named `act_03.xlsx` — the reason folders must not be shared (AC-09).

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Calls the verifier CLI only: `.venv/Scripts/act-verifier --contract <…> [--previous <…>…] --act <…> --out <…> [--journal]`; exit 0/1/2 + stdout evidence block, or exit 3 + stderr. — `sad.md §2, Technical, abridged`.

## Acceptance criteria

### AC-01b (US-01) — error

> **Given** the accepting person names the act but not the contract price, or names no previous acts and has not said the act is act 1
> **When** the accepting person asks the L1 agent to check the act
> **Then** the L1 agent asks for the missing inputs before running and substitutes no default path; it runs the verifier only on files the accepting person has named (previous acts then follow AC-04)
>
> — `spec.md §5, AC-01b, verbatim`

### AC-04 (US-01) — domain invariant

> **Given** the accepting person states the act's number N (or, only when they have not stated it, the L1 agent asks for it once before the run, without reading the act file) and, by the accepting person's own account, supplies no previous acts or fewer than acts 1 to N−1 — completeness is judged from what the accepting person says, never from file names
> **When** the accepting person asks the L1 agent to check the act
> **Then** the L1 agent first asks for the missing previous acts; if the accepting person confirms they are not available, it runs without them, warns before the run that the remaining-volume and cumulative checks will be unknown, and replies with the verifier's verdict — at best needs_review, never pass — listing those checks under «Не перевірено» as «невідомо» with the reason the evidence block gives — never «все гаразд» (the invariant «a missing value never yields pass»)
>
> — `spec.md §5, AC-04, verbatim`

### AC-08 (US-04) — authorization

> **Given** the accepting person has not asked for the error journal
> **When** the L1 agent checks an act
> **Then** it runs the verifier without the error journal and the journal is unchanged; only when the accepting person explicitly asks does it run with the journal; the reply then says the findings were appended only if the verdict is fail or needs_review, says there was nothing to append on pass, and says nothing was written on an input error
>
> — `spec.md §5, AC-08, verbatim`

### AC-09 (US-03) — cross-context

> **Given** the report folder already holds the report of an earlier run on an act with the same file name — for example the three discrepancies of «combo_three_errors»
> **When** the L1 agent checks the act of «missing_label» and the verifier stops with an input error
> **Then** the reply contains no finding, number or verdict from that earlier report; the L1 agent reads a report only after a run that has a verdict — exit code 0, 1 or 2 together with the line «Вердикт: …» in that run's output (§1 «Verdict source»)
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `SKILL.md` «Кроки» step 1 — inputs: ask for each of contract / previous acts / act not named; never a default path; ask act number N once if unstated (no file reading); previous-acts completeness from the person's words; on «нема» warn before the run that remaining-volume and cumulative checks will be «невідомо».
- [ ] step 2 — run: the T2 run-command block as written, prefix `.venv/Scripts/act-verifier` exactly; `--out` = the folder the person named, else `reports/`; `--journal` only on explicit request.
- [ ] step 3 — verdict source: verdict only for exit 0/1/2 **and** «Вердикт: pass|fail|needs_review.» anywhere in that run's stdout; only then read `<out>/<act-stem>_report.md`; otherwise go to the no-verification branch (T5 writes its body — leave a heading).
- [ ] journal reply rule (AC-08): appended only on fail/needs_review, nothing to append on pass, nothing written on input error.
- [ ] Keep the T2 table and bash block shape intact; run `.venv/Scripts/python -m pytest -q tests/test_check_act_skill.py`.

## Edge cases

| Case | Behaviour |
|---|---|
| Person says «це акт 1» | no previous acts needed, run without `--previous` |
| Person names acts 1 only for act 3 | ask for act 2; on «нема» warn, run, verdict at best needs_review |
| Report folder has an old `act_03_report.md`, run exits 3 | old report is not opened |
| Exit 1 without «Вердикт:» in stdout | crash → no report read (T5) |
| Person asks for the journal on a run that ends with exit 3 | reply says nothing was written |

## Definition of Done

- [ ] each of AC-01b, AC-04, AC-08, AC-09 maps to a named sentence in `SKILL.md` (list the mapping in the task report)
- [ ] drift tests still green: `.venv/Scripts/python -m pytest -q` — 304 + N passed, 0 failed, 0 xfailed
- [ ] agent behaviour is not automated (spec §3 non-goal) — verified at T8 rehearsal
- [ ] every Hard Rule inlined above still holds
