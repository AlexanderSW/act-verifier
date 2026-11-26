---
id: T1
title: "Create the check-act skill file with its identity header and the identity drift tests"
layer: "ports"
deps: []
blocks: ["T2"]
acs: ["AC-11"]
files_hint: [".claude/skills/check-act/SKILL.md", "tests/test_check_act_skill.py"]
owner: "AlexanderSW"
estimate: "S"           # ~1 h
context_budget: "S"     # 36 inlined lines, 1 extra file (src/act_verifier/cli.py is not needed yet)
status: "todo"
step: ""
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T1 — Create the check-act skill file with its identity header and the identity drift tests

## Place in the sequence

- **Blocked by:** — · **Blocks:** T2 — outcome-code map, run-command block and their drift tests · **Wave:** 1 (starts the skill lane; nothing upstream).
- **Lane:** skill lane — shares `.claude/skills/check-act/SKILL.md` with T2–T5 and `tests/test_check_act_skill.py` with T2 → serialized. Runs in parallel with T6 and T7.

## Why (user story)

> **As the** project owner
> **I want** the test suite to fail when the check-act skill's outcome-code map, command options or identity disagree with the verifier itself
> **So that** the skill can never tell the L1 agent something the verifier no longer does
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task delivers the «identity» half: the live skill file exists with a valid header, and the suite proves it.

## Inlined context

> Skill host: Claude Code project skills — `.claude/skills/<name>/SKILL.md` with frontmatter `name`, `description`, optional `allowed-tools`. […] No YAML parser among the dependencies — the test reads the skill's frontmatter as plain `key: value` lines.
>
> — `sad.md §2, Technical, abridged` · full text: [sad.md](../sad.md)

> **Chosen:** Option 1 with the `.venv/Scripts/act-verifier` form. […] `allowed-tools: Bash(.venv/Scripts/act-verifier:*)` in the skill's frontmatter — pre-allowed only while the skill is active, only for the verifier's console script.
>
> — `adr/0002, Decision outcome + Option 1, abridged` · full text: [adr/0002](../adr/0002-pre-allow-only-the-verifier-via-skill-allowed-tools.md)

> Read the skill's frontmatter as `key: value` lines […]. A failure must name the code, option, token or field that is wrong. 0 model calls and 0 network calls in the suite.
>
> — `adr/0003, Option 1 + Decision drivers, abridged` · full text: [adr/0003](../adr/0003-check-drift-by-importing-cli-contract-and-parsing-skill.md)

> **Hard rule:** the live check-act skill is `.claude/skills/check-act/SKILL.md`; the owner's draft in the feature folder is not a live copy.
>
> — `spec.md §1, «Skill location», abridged` · full text: [spec.md](../spec.md)

> **Hard rule:** Identifiers in English; docstrings, comments and user-facing text in Ukrainian. The skill's body and its reply headings are Ukrainian.
>
> — `sad.md §2, Conventions, verbatim` · full text: [sad.md](../sad.md)

Seed for the `description` (owner's draft, history only — copy the wording, not the file): «Перевірити акт КБ-2в / КБ-3 проти договірної ціни й попередніх актів через act-verifier і пояснити розбіжності людині. Використовувати, коли просять перевірити, звірити або «подивитися» акт.» — `docs/features/check-act-skill/SKILL.md, frontmatter description, verbatim`.

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

Internal — no API surface. (The skill header is read by Claude Code; the test reads it as text.)

## Acceptance criteria

### AC-11 (US-05) — error

> **Given** the check-act skill at `.claude/skills/check-act/SKILL.md` is missing, its header cannot be read, its name is not «check-act» or its description is empty
> **When** the project owner runs the test suite
> **Then** the suite fails and names which of these four is wrong; with a valid skill the suite passes without calling a model or the network
>
> — `spec.md §5, AC-11, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] RED: create `tests/test_check_act_skill.py` (pytest, `ROOT` from `conftest`); a helper reads `ROOT / ".claude/skills/check-act/SKILL.md"`, splits the `---` … `---` header and parses `key: value` lines (no YAML library).
- [ ] RED: four separate assertions/tests, each with a message naming its case — file missing · header unreadable (no leading `---` block) · `name` ≠ `check-act` · `description` empty. No subprocess, no network.
- [ ] GREEN: create `.claude/skills/check-act/SKILL.md` with frontmatter `name: check-act`, a one-line Ukrainian `description`, `allowed-tools: Bash(.venv/Scripts/act-verifier:*)`, and a placeholder H1 body (T2–T5 fill it).
- [ ] Do not touch the owner's draft `docs/features/check-act-skill/SKILL.md` (T7 marks it superseded).

## Edge cases

| Case | Behaviour |
|---|---|
| Skill file absent | test fails with a message naming «missing» and the path |
| File has no `---` header, or it is not closed | test fails naming «header cannot be read» |
| `name: check_act` / other name | test fails naming the expected `check-act` and the actual value |
| `description:` with only whitespace | test fails naming «description is empty» |
| `description` value contains `:` (Ukrainian prose) | parser splits on the first `: ` only, value kept whole |

## Definition of Done

- [ ] `tests/test_check_act_skill.py` identity tests were red before the skill file existed and are green now
- [ ] `.venv/Scripts/python -m pytest -q` — 304 + new identity tests passed, 0 failed, 0 xfailed
- [ ] suite makes no model, network or subprocess call (grep the test for `subprocess`, `requests`, `http`)
- [ ] every Hard Rule inlined above still holds
