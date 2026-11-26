---
id: T8
title: "Rehearse the three demo scenarios with the live skill and record the actual results in demo.md"
layer: "tests"
deps: ["T4", "T5", "T6"]
blocks: []
acs: ["AC-12"]
files_hint: ["docs/features/check-act-skill/demo.md"]
owner: "AlexanderSW"
estimate: "M"           # ~1.5 h, manual — a live L1 agent session is required
context_budget: "S"     # 33 inlined lines, 2 files in play (demo.md, the live SKILL.md)
status: "blocked"
step: "RED — manual: owner rehearsal in a fresh session (hashes «до» filled)"
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. This task is MANUAL: the implement engine cannot play the L1 agent
for itself — it prepares the hashes and hands the three prompts to the project owner. -->

# T8 — Rehearse the three demo scenarios with the live skill and record the actual results in demo.md

## Place in the sequence

- **Blocked by:** T4 — reply format + red lines, T5 — no-verification branch, T6 — demo script · **Blocks:** — · **Wave:** 5 (last; needs the complete skill and the script).
- **Lane:** shares `demo.md` with T6 → after it.

## Why (user story)

> **As the** project owner
> **I want** a demo script giving, for each of the three demo scenarios, the prompt, the expected behaviour of the L1 agent, its own report folder and a field for the actual result
> **So that** I can rehearse before the interview and show what actually happened
>
> — `spec.md §4, US-06, verbatim` · full text: [spec.md](../spec.md)

This task delivers «show what actually happened»: the second half of AC-12, and the only evidence of agent behaviour (AC-01, AC-02, AC-03, AC-05, AC-07 observed, not asserted).

## Inlined context

> **No automated proof of agent behaviour.** The owner ruled out running a model in tests; behaviour is shown by one manual demo pass per scenario, which is not a regression guarantee.
>
> — `spec.md §3, non-goal 4, verbatim` · full text: [spec.md](../spec.md)

> **Demo scenarios behaving as expected** — target: 3 of 3 («ok_many», «combo_three_errors», «missing_label»), with actual results written in the demo document, by the interview on 2026-11-27. **Red-line violations** — target: 0 across the three runs.
>
> — `spec.md §7, KPIs 1–2, abridged`

> | The `allowed-tools` behaviour depends on the Claude Code version | Low | Verified at rehearsal; fallback = planned prompt step in `demo.md` |
> | `--journal` is covered by the pre-allow pattern; only the skill's rule (AC-08) keeps the agent from using it unasked | Low | […] the journal is tracked in git, so an append shows in `git status` |
>
> — `sad.md §11, risks 4–5, abridged` · full text: [sad.md](../sad.md)

> **QG-3. Input safety** — 0 changed input files (contract price, previous acts 1–2, the three demo acts); a file hash of each input taken before and after the rehearsal, both written in `demo.md`.
>
> — `sad.md §10, QG-3, abridged`

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-12 (US-06) — happy path

> **Given** the demo document `docs/features/check-act-skill/demo.md` for the three demo scenarios «ok_many», «combo_three_errors» and «missing_label»
> **When** the project owner rehearses the demo
> **Then** for each scenario the document gives the prompt — naming the contract price, previous acts 1 and 2 and the act explicitly — the expected behaviour (verdict pass with no claim of acceptance; three discrepancies whose numbers match the report; «перевірки не було» naming «Разом без ПДВ», with the act file unchanged), its own report folder and an «actual result» field; after the rehearsal all three fields hold what the L1 agent actually did, deviations included
>
> — `spec.md §5, AC-12, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Before: `sha256sum` the 6 inputs into the «до» table of `demo.md`; `git status journal/` clean.
- [ ] Owner, in a fresh Claude Code session at repo root: run each scenario's prompt from `demo.md`; stopwatch; count permission prompts.
- [ ] After each reply: paste the reply (or its gist) into «Фактичний результат»; look up every number in `reports/demo/<scenario>/act_03_report.md`; tick the five red-line items; record deviations.
- [ ] After all three: hashes into the «після» table; `git status journal/` still clean.
- [ ] A deviation found → record it; fix the skill only via a follow-up task (or `/sdd:fix`), then re-rehearse that scenario.

## Edge cases

| Case | Behaviour |
|---|---|
| A permission prompt appears for the verifier | recorded as a deviation; ADR-0002 fallback noted |
| Reply > 2 min | recorded as a deviation, not a blocker |
| A number not found in the report | red-line violation recorded; skill fix before the demo |
| Hash differs after the rehearsal | red-line violation; restore the file from git |

## Definition of Done

- [ ] all three «Фактичний результат» fields filled, deviations included; stopwatch and prompt counts recorded
- [ ] hash tables before/after equal for all 6 inputs; journal unchanged in `git status`
- [ ] five-item red-line checklist filled per scenario (target 0 violations)
- [ ] `.venv/Scripts/python -m pytest -q` — 304 + N passed, 0 failed, 0 xfailed
