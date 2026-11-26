---
status: Accepted
owner: "AlexanderSW"
reviewers: ["Tech Lead"]
updated_at: "2026-11-26"
feature_size: "XS"
ticket: "docs/roadmap.md — check-act-skill"
---

# 0001 — Ship the agent link as a project Claude Code skill over the unchanged verifier

- **Status:** Accepted
- **Date:** 2026-11-26
- **Deciders:** AlexanderSW (project owner), with Claude during the design walk

## Context

The chain «AI prepares → code checks → human decides» has a working verifier but no agent link: nothing tells an agent how to run the check and explain it without computing numbers, editing inputs or deciding acceptance (spec §1). The demo is on 2026-11-27, so the link must fit in about a day and use only what exists (spec §1, brief §4). The owner accepted the skill approach in brief §7; this ADR records why, so a reader does not ask «why not the assistant-agent tool?».

## Decision drivers

- Deadline 2026-11-27, ≈ one day of work (spec §1).
- No change to the verifier, the fixture generator or the fixtures (spec §3).
- Skill–verifier agreement must be testable without a model (spec §2 goal 3, §6 «Test independence from a model»).
- 0 numbers outside the report and 0 changed input files (spec §6).

## Considered options

1. **Project Claude Code skill** — `.claude/skills/check-act/SKILL.md` with red lines, steps, outcome-code map and reply format; the agent runs the existing `act-verifier` command.
2. **Assistant-agent tool (roadmap step 2)** — rejected upstream (brief §7; spec §3 non-goal), recorded for the «why not?» reader: expose the verifier through `src/act_verifier/mcp_server.py` as a tool the agent calls.
3. **A section in CLAUDE.md** — rejected upstream (brief §7; spec §1 «Skill location», AC-11), recorded for the «why not?» reader: put the same rules into the project instructions that every session loads.

## Decision outcome

**Chosen:** Option 1. It wraps the verifier unchanged and fits the deadline. Its fixed name and description give the drift test an identity to check (AC-11). Option 2 is larger and is roadmap step 2 (spec §3 non-goal), and the `mcp` extra is not installed. Option 3 loads the rules into every session, including sessions with nothing to do with checking acts, and has no separate identity to test.

## Consequences

**Positive**
- No verifier change; the CLI contract stays the single source of truth.
- The skill loads only when an act is to be checked, and it can carry its own narrow `allowed-tools` (ADR-0002).
- The file is plain Markdown, so the drift test can parse it (ADR-0003).

**Negative**
- The agent's behaviour rests on instructions, not on code, and is shown by a manual demo, not by a regression test (spec §3).
- The link is tied to Claude Code as the host; another assistant would need its own wrapper.

**Neutral**
- Roadmap step 2 can later sit alongside it; the skill could then call the tool instead of the command, and its reply format would stay as it is.

## Links

- Spec: [[../spec.md]] §1, §3, US-05
- SAD: [[../sad.md]] §4 choice 1
- Related ADR: [[0002-pre-allow-only-the-verifier-via-skill-allowed-tools]], [[0003-check-drift-by-importing-cli-contract-and-parsing-skill]]
