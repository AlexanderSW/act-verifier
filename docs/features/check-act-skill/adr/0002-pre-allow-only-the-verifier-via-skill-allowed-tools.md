---
status: Accepted
owner: "AlexanderSW"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-11-26"
feature_size: "XS"
ticket: "spec.md §8 OQ 1"
---

# 0002 — Pre-allow only the verifier command via the skill's allowed-tools

- **Status:** Accepted
- **Date:** 2026-11-26
- **Deciders:** AlexanderSW (project owner), with Claude during the design walk

## Context

Spec §8 OQ 1 asked whether the check-act skill should pre-allow the verifier command, so the demo shows no permission prompt, and in which command form; it was due before design. The package has no `__main__.py`, so `python -m act_verifier` does not run; the console script `.venv/Scripts/act-verifier` is installed and is what the owner's draft uses. Spec §6.1 says to revisit the security review only if a command beyond the verifier is pre-allowed.

## Decision drivers

- 0 unplanned permission prompts during the demo (spec §6).
- No command other than the verifier runs, and no input file is opened (spec §1, §6.1).
- Smallest possible pre-allowed scope, in force only while the check is running.

## Considered options

1. **`allowed-tools: Bash(.venv/Scripts/act-verifier:*)` in the skill's frontmatter** — pre-allowed only while the skill is active, only for the verifier's console script.
2. **No pre-allow** — the spec's default: `demo.md` lists the permission prompt as a planned step.
3. **A `permissions.allow` rule in `.claude/settings.json`** — the same pattern, active in every session of the project.

Command form: `.venv/Scripts/act-verifier …` (chosen) versus `.venv/Scripts/python -m act_verifier.cli …`. The second runs, but its pattern would have to pre-allow `python`, which is much wider.

## Decision outcome

**Chosen:** Option 1 with the `.venv/Scripts/act-verifier` form. It meets «0 unplanned prompts» with the narrowest scope: one executable, only inside the skill. No command beyond the verifier is pre-allowed, so the spec §6.1 condition for a security review is not triggered. Option 2 puts a click into the demo. Option 3 pre-allows the command outside the check as well.

## Consequences

**Positive**
- The demo has no prompt for the verifier.
- Any other command (a script that reads xlsx, a file edit) still prompts, so a red-line breach becomes visible.

**Negative**
- The pattern matches the verifier with any arguments, `--journal` included. Only the skill's rule (AC-08) keeps the journal untouched unless the person asks.
- The pattern matches only the exact prefix. A `cd … &&` prefix or `./.venv/...` triggers a prompt (sad §11 risk 1).

**Neutral**
- If `allowed-tools` behaves differently in the installed Claude Code version, the fallback is Option 2's planned prompt step, recorded in `demo.md`.

## Links

- Spec: [[../spec.md]] §6, §6.1, §8 OQ 1
- SAD: [[../sad.md]] §4 choice 2, §8 «Permissions», §11
- Related ADR: [[0001-ship-agent-link-as-project-claude-code-skill]]
