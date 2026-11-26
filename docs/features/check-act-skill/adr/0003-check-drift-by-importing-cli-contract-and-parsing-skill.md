---
status: Accepted
owner: "AlexanderSW"
reviewers: ["Tech Lead"]
updated_at: "2026-11-26"
feature_size: "XS"
ticket: "spec.md US-05, AC-10, AC-11"
---

# 0003 — Check drift by importing the CLI contract and parsing the skill file

- **Status:** Accepted
- **Date:** 2026-11-26
- **Deciders:** AlexanderSW (project owner), with Claude during the design walk

## Context

AC-10 requires the suite to fail when the skill's outcome-code map, its run command's options or its input-error token disagree with the verifier. The expected values must come "from the verifier itself, not from a copy kept in the test". AC-11 adds the skill's identity checks: the file exists, the header is readable, `name` is «check-act» and `description` is not empty. The suite must make 0 model calls and 0 network calls (spec §6).

## Decision drivers

- Expected values come from the verifier, not from a copy in the test (AC-10).
- 0 model calls and 0 network calls in the suite (spec §6).
- No YAML parser among the dependencies; tests run on Windows / Git Bash (sad §2).
- A failure must name the code, option, token or field that is wrong (AC-10, AC-11).

## Considered options

1. **Import the CLI contract and parse SKILL.md.** Take `cli.EXIT` and `cli.EXIT_INPUT_ERROR`. Take the option strings from `cli._parser()`, without `--help`. Take the token «перевірки не було» from the stderr of `cli.main()` when it is called on a file that does not exist. Read the skill's frontmatter as `key: value` lines, its outcome-code table rows, and the single `bash` block that holds `act-verifier`.
2. **Subprocess.** Run `.venv/Scripts/act-verifier --help` and a failing call, then parse the help and stderr text.
3. **A machine-readable map in the skill's frontmatter.** Keep codes and options as structured frontmatter keys, and the test compares them with `cli`.

## Decision outcome

**Chosen:** Option 1. It reads the verifier's real values in-process, so it is fast and needs no network or subprocess. The token comes from a real error path, not from a string literal. Option 2 depends on the layout of the argparse help text and on the venv path. Option 3 makes a second copy of the map, and the table the agent reads would still be free to drift from it.

## Consequences

**Positive**
- A change to an exit code, an option or the input-error wording in `cli.py` breaks the suite at once and names the item.
- The table the agent actually reads is the one under test.

**Negative**
- Coupled to the private `cli._parser()`: a rename breaks the test, not the skill (sad §11).
- The skill's table and its bash block must keep a parseable shape. That shape is a format rule the skill's author has to follow.

**Neutral**
- Switching to Option 2 later touches only the test file.

## Links

- Spec: [[../spec.md]] US-05, AC-10, AC-11, §6
- SAD: [[../sad.md]] §4 choice 3, §5, §8 «Drift contract»
- Related ADR: [[0001-ship-agent-link-as-project-claude-code-skill]]
