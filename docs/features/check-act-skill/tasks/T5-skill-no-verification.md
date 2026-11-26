---
id: T5
title: "Write the skill's no-verification branch: input errors by kind and verifier crashes"
layer: "ports"
deps: ["T3"]
blocks: ["T8"]
acs: ["AC-05", "AC-05b", "AC-06", "AC-06b"]
files_hint: [".claude/skills/check-act/SKILL.md"]
owner: "AlexanderSW"
estimate: "S"           # ~1 h
context_budget: "M"     # 48 inlined lines, 1 extra file (src/act_verifier/cli.py _message() for the message shapes)
status: "done"
step: ""
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T5 — Write the skill's no-verification branch: input errors by kind and verifier crashes

## Place in the sequence

- **Blocked by:** T3 — run steps + verdict-source rule · **Blocks:** T8 — demo rehearsal · **Wave:** 4 (fills the branch T3 leaves as a heading).
- **Lane:** skill lane — `SKILL.md` shared with T4 (same wave) → serialized.

## Why (user story)

> **As an** accepting person
> **I want** to be told plainly when verification did not happen and why, in the verifier's own words
> **So that** I never act on a result that does not exist
>
> — `spec.md §4, US-03, verbatim` · full text: [spec.md](../spec.md)

This task writes what the agent says and does when the run produced no verdict.

## Inlined context

> On an input error the L1 agent relays the verifier's message as written. Whether it may offer a guess depends on the verifier's error kind: for `missing_label` and `ambiguous_label` (a missing sheet is reported as `missing_label`) it may offer a guess at the label's or sheet's name; for `invocation`, `unreadable_file`, `overwrite_refused` and `duplicate_code` it offers none. The guess is built only from the verifier's message and what the accepting person says; the L1 agent never opens an input file to make it, so it runs no command other than the verifier. […] Exit code 1 without that line is a verifier crash: verification did not happen, no report is read, and the L1 agent shows the error output and asks the accepting person.
>
> — `spec.md §1, traceability bullets 2, 3, abridged` · full text: [spec.md](../spec.md)

> alt exit 3, input error — V-->>A: stderr with перевірки не було and the message; A-->>P: no verification, quotes the message, a marked guess only for a label or sheet error · else exit 1 with no Вердикт line, crash — A-->>P: no verification, shows the error output, reads no report · P->>A: decides what to do next
>
> — `sad.md §6, Critical flow 2, abridged` · full text: [sad.md](../sad.md)

Input-error stderr shape: `act-verifier: помилка вхідних даних, перевірки не було — <message>`; `missing_label` → «файл <f>, аркуш «<s>»: не знайдено підпис «<l>».» or «файл <f>: не знайдено аркуш «<s>».»; `ambiguous_label` → «…підпис «<l>» знайдено в кількох рядках (<rows>); перший збіг не використовується.» — `src/act_verifier/cli.py:75-96,146, _message()/main(), abridged`. The skill tells the agent to recognize the kind from the message wording, not from a code (all input errors exit 3).

> **Hard rule:** The L1 agent opens no input file and writes no file. Abuse case: the L1 agent «fixes» an input file to get past an input error — forbidden; it relays the message and asks the accepting person, and the file stays unchanged.
>
> — `sad.md §8, Input handling` + `spec.md §6.1, abuse case 2, abridged`

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Reads the verifier's exit code and stderr/stdout of this run only; exit 3 = input error, exit 1 without «Вердикт:» = crash. — `sad.md §2 + §4 choice 4, abridged`.

## Acceptance criteria

### AC-05 (US-03) — error

> **Given** the contract price, previous acts 1 and 2 and the act of the demo scenario «missing_label» are named, and that act has no «Разом без ПДВ» totals row, so the verifier stops with an input error
> **When** the accepting person asks the L1 agent to check it
> **Then** the reply says that verification did not happen and gives no verdict, quotes the verifier's message as written, and names the layout label «Разом без ПДВ», the file and the sheet from that message; the L1 agent may suggest how the label might be written, built only from the verifier's message and what the accepting person says — it does not open the act file — and marks the suggestion as a guess; it asks the accepting person what to do, and the act file is unchanged
>
> — `spec.md §5, AC-05, verbatim`

### AC-05b (US-03) — error

> **Given** the verifier stops with an input error of kind `ambiguous_label` (a layout label matches more than one row) or `missing_label` for a required sheet
> **When** the L1 agent replies
> **Then** it says that verification did not happen and gives no verdict, quotes the verifier's message as written, and names the label or the sheet and the file from that message; for an ambiguous label it also names the competing rows the message lists and picks none of them; it may suggest what the label or sheet might be, built only from the message and what the accepting person says and marked as a guess, without opening the file; it asks the accepting person what to do, and the act file is unchanged
>
> — `spec.md §5, AC-05b, verbatim`

### AC-06 (US-03) — error

> **Given** the verifier stops with an input error of kind `invocation` (wrong invocation), `unreadable_file` (a missing or unreadable file), `overwrite_refused` (a refused overwrite) or `duplicate_code` (a repeated position code — even though its message names a sheet and a position code)
> **When** the L1 agent replies
> **Then** it says that verification did not happen, quotes the verifier's message as written, offers no guess at a label name and asks the accepting person to correct the input; it changes no file and does not rerun with other files unless the accepting person agrees
>
> — `spec.md §5, AC-06, verbatim`

### AC-06b (US-03) — error

> **Given** the verifier exits with code 1 but its output contains no line «Вердикт: …» (a verifier crash), and the report folder may hold a report from an earlier run
> **When** the L1 agent replies
> **Then** it says that verification did not happen and gives no verdict, shows the verifier's error output as written, reads no report and states no finding or number from any report, and asks the accepting person what to do; it changes no file
>
> — `spec.md §5, AC-06b, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `SKILL.md` «Перевірки не було» section: say verification did not happen, no verdict, no five-section format; quote the message verbatim (code block); name label / sheet / file from the message.
- [ ] Guess policy by kind (recognized from the message wording): label or sheet missing / ambiguous → optional guess, marked «припущення», built only from the message and the person's words; ambiguous → list the competing rows, pick none; invocation / unreadable file / refused overwrite / repeated code («шифр … повторюється») → no guess, ask to correct the input.
- [ ] Crash (exit 1, no «Вердикт:»): show the error output as written, read no report, ask what to do.
- [ ] Always: change no file, no rerun with other files without the person's agreement, no other command (no xlsx reading script).
- [ ] Keep the T2 table and bash block shape intact; run `.venv/Scripts/python -m pytest -q tests/test_check_act_skill.py`.

## Edge cases

| Case | Behaviour |
|---|---|
| `duplicate_code` message names a sheet and a code | still no guess (AC-06) |
| Old report in the folder after exit 3 or a crash | not opened, nothing quoted from it |
| Person: «виправ мітку сам» | declines to edit; the person edits the file, then the agent reruns |
| Person suggests another file | rerun only with their explicit agreement, on the file they named |

## Definition of Done

- [ ] each of AC-05, AC-05b, AC-06, AC-06b maps to a named sentence in `SKILL.md` (mapping in the task report)
- [ ] drift tests still green: `.venv/Scripts/python -m pytest -q` — 304 + N passed, 0 failed, 0 xfailed
- [ ] agent behaviour for «missing_label» is verified at the T8 rehearsal
- [ ] every Hard Rule inlined above still holds
