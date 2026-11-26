---
id: T7
title: "Add the README section «Агент L1: Skill check-act» and mark the owner's draft skill superseded"
layer: "docs"
deps: []
blocks: []
acs: ["AC-13"]
files_hint: ["README.md", "docs/features/check-act-skill/SKILL.md"]
owner: "AlexanderSW"
estimate: "S"           # ~45 min
context_budget: "S"     # 34 inlined lines, 1 extra file (README.md itself)
status: "todo"
step: ""
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T7 — Add the README section «Агент L1: Skill check-act» and mark the owner's draft skill superseded

## Place in the sequence

- **Blocked by:** — · **Blocks:** — · **Wave:** 1 (written from the spec and the ADRs; the skill's name, location and command are fixed upstream).
- **Lane:** own lane (`README.md`, the draft `SKILL.md` — no other task touches them). Parallel with T1 and T6.

## Why (user story)

> **As an** employer reviewer
> **I want** a short README section on how to call the check-act skill, what it does and what it does not do
> **So that** I understand the agent link of the chain without reading the skill itself
>
> — `spec.md §4, US-07, verbatim` · full text: [spec.md](../spec.md)

This task writes that section and removes the risk of the draft being read as a second live skill.

## Inlined context

> - [ ] Will the employer reviewer run the skill themselves, or only watch the demo? Default now: the README section covers calling the skill from this repository only, with no install steps for another machine. — due: before the README section is written at `/sdd:implement`
> - [ ] What happens to the owner's draft `docs/features/check-act-skill/SKILL.md` once the real check-act skill exists? Default now: keep it as history, marked as superseded by the real skill, so it is not read as a second live copy. — due: at `/sdd:implement`
>
> — `spec.md §8, OQ 2 and OQ 3, abridged` · full text: [spec.md](../spec.md)

> **Chosen:** `allowed-tools: Bash(.venv/Scripts/act-verifier:*)` […] pre-allowed only while the skill is active, only for the verifier's console script. Any other command (a script that reads xlsx, a file edit) still prompts.
>
> — `adr/0002, Decision outcome + Consequences, abridged` · full text: [adr/0002](../adr/0002-pre-allow-only-the-verifier-via-skill-allowed-tools.md)

> The skill is a file in the repository, picked up by Claude Code from `.claude/skills/` when a session starts in the repository root.
>
> — `sad.md §7, N/A note, abridged` · full text: [sad.md](../sad.md)

> The skill sits alongside, not instead of, the assistant-agent tool of roadmap step 2.
>
> — `spec.md §1, committed approach, verbatim`

README today has `## Зміст`, `## Розробка` → `### Тести` (a table of test files) and `## Документація` — `README.md, headings, abridged`.

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface.

## Acceptance criteria

### AC-13 (US-07) — happy path

> **Given** the README
> **When** the employer reviewer reads its section «Агент L1: Skill check-act»
> **Then** the section says how to call the check-act skill from this repository, what the L1 agent does (runs the verifier and explains its report) and what it does not do (compute numbers, edit input files, decide acceptance, write the error journal unasked)
>
> — `spec.md §5, AC-13, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] Ask the owner whether OQ 2 is resolved; if not, use the default (call from this repository only, no install steps elsewhere) and say so in the task report.
- [ ] `README.md`: add `## Агент L1: Skill check-act` (Ukrainian): how to call (Claude Code session at repo root, `/check-act` or a plain request naming the files), what it does, what it does not do (the four items of AC-13), the pre-allowed command, link to `docs/features/check-act-skill/demo.md`. Add it to `## Зміст`.
- [ ] `README.md` `### Тести` table: row `test_check_act_skill.py` — skill ↔ verifier agreement (codes, options, token, identity). `## Документація`: link to the feature's spec/sad.
- [ ] `docs/features/check-act-skill/SKILL.md` (OQ 3 default): keep the content and frontmatter as history; put the note «> Чернетка власника, історія. Живий skill — `.claude/skills/check-act/SKILL.md`.» as the first body line right after the frontmatter (a line above `---` would break the header). Claude Code does not load skills from `docs/`, so the draft's `name: check-act` cannot shadow the live one.

## Edge cases

| Case | Behaviour |
|---|---|
| OQ 2 resolved as «reviewer runs it on their machine» | add install steps (`.venv`, `pip install -e .`) — the owner's call |
| README section repeats the skill's red lines in full | keep it short — four «does not» items, link to the skill |

## Definition of Done

- [ ] README section exists under the AC-13 title and covers call / does / does-not (four items); listed in «Зміст»
- [ ] the draft `SKILL.md` carries the superseded note; OQ 2 / OQ 3 outcome stated in the task report
- [ ] `.venv/Scripts/python -m pytest -q` unchanged (docs only)
