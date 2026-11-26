---
id: T2
title: "Add the outcome-code map and run-command block to the skill, with drift tests against the verifier's own contract"
layer: "ports"
deps: ["T1"]
blocks: ["T3"]
acs: ["AC-10"]
files_hint: [".claude/skills/check-act/SKILL.md", "tests/test_check_act_skill.py", "CLAUDE.md"]
owner: "AlexanderSW"
estimate: "M"           # ~2 h
context_budget: "M"     # 44 inlined lines, 2 extra files (src/act_verifier/cli.py, tests/test_cli_unit.py for the argv helper)
status: "todo"
step: ""
---

<!-- To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file for the full text and follow that.
Do not invent the missing part. -->

# T2 — Add the outcome-code map and run-command block to the skill, with drift tests against the verifier's own contract

## Place in the sequence

- **Blocked by:** T1 — skill file + identity tests · **Blocks:** T3 — skill run steps · **Wave:** 2 (needs the skill file and the test module from T1).
- **Lane:** skill lane — shares `SKILL.md` and `tests/test_check_act_skill.py` with T1 (and `SKILL.md` with T3–T5) → serialized. Owns the `CLAUDE.md` count update, because this is the last task that adds tests.

## Why (user story)

> **As the** project owner
> **I want** the test suite to fail when the check-act skill's outcome-code map, command options or identity disagree with the verifier itself
> **So that** the skill can never tell the L1 agent something the verifier no longer does
>
> — `spec.md §4, US-05, verbatim` · full text: [spec.md](../spec.md)

This task delivers the «codes and options» half of the drift guard, and the two skill sections it guards.

## Inlined context

> **Chosen:** Option 1. Import the CLI contract and parse SKILL.md. Take `cli.EXIT` and `cli.EXIT_INPUT_ERROR`. Take the option strings from `cli._parser()`, without `--help`. Take the token «перевірки не було» from the stderr of `cli.main()` when it is called on a file that does not exist. Read […] its outcome-code table rows, and the single `bash` block that holds `act-verifier`. […] no network or subprocess. […] The skill's table and its bash block must keep a parseable shape. That shape is a format rule the skill's author has to follow.
>
> — `adr/0003, Considered options 1 + Decision outcome + Consequences, abridged` · full text: [adr/0003](../adr/0003-check-drift-by-importing-cli-contract-and-parsing-skill.md)

> | outcome-code map | The table in the check-act skill pairing each verifier exit code with its verdict token (0 pass, 1 fail, 2 needs_review) or with the input-error meaning (3 — «перевірки не було») |
> | run-command block | The single fenced `bash` block in the check-act skill holding the verifier command line, with `--journal` as a marked optional part; the only place the drift test reads options from |
>
> — `sad.md §12, glossary rows, verbatim` · full text: [sad.md](../sad.md)

> **Hard rule:** Every line of the skill's outcome-code map carries the code and the verifier's own verdict token (`pass`, `fail`, `needs_review`) or the input-error meaning, so a test can compare the map with the verifier's codes.
>
> — `spec.md §1, traceability bullet 1, abridged` · full text: [spec.md](../spec.md)

> **Hard rule:** The skill says to start the command exactly with the prefix `.venv/Scripts/act-verifier` (the «as written» rule covers the prefix only; `--journal` stays optional).
>
> — `sad.md §11, risk 1 mitigation, abridged` · full text: [sad.md](../sad.md)

> **Hard rule (NFR):** Test suite outcome after the change — 304 + N passed, 0 failed, 0 xfailed (N = the new skill tests); the expected count in `CLAUDE.md` updated to 304 + N. 0 model calls and 0 network calls in the suite.
>
> — `spec.md §6, rows 1–2, abridged` · full text: [spec.md](../spec.md)

> **Risk:** The drift test imports the private `cli._parser()`; a rename breaks the test, not the skill — the failure is loud and names the import.
>
> — `sad.md §11, risk 3, abridged` · full text: [sad.md](../sad.md)

**Fallback:** insufficient or contradicted by the code → read the named file in full
([spec.md](../spec.md) · [sad.md](../sad.md) · [adr/](../adr/)) and follow it. Do not guess.

## Data delta

No DB changes.

## API contract

The verifier CLI is the contract under test (read, never changed):

- Console script `.venv/Scripts/act-verifier` (entry point `act_verifier.cli:main`).
- `EXIT = {"pass": 0, "fail": 1, "needs_review": 2}`, `EXIT_INPUT_ERROR = 3` — `src/act_verifier/cli.py:27-28`.
- Options `--contract` (required), `--previous` (`nargs="*"`), `--act` (required), `--out` (default `reports`), `--journal` (`nargs="?"`, const `journal/agent_errors.csv`) — `src/act_verifier/cli.py:58-62`.
- Input-error stderr: `act-verifier: помилка вхідних даних, перевірки не було — <message>` — `src/act_verifier/cli.py:146`.

— `sad.md §2, Technical, abridged` + `src/act_verifier/cli.py, main()/_parser(), verbatim` · full text: [sad.md](../sad.md)

## Acceptance criteria

### AC-10 (US-05) — cross-context

> **Given** the check-act skill's outcome-code map and its run command
> **When** the project owner runs the test suite
> **Then** the suite passes only if every outcome the verifier defines appears in the map with the same code — pass, fail and needs_review with the verifier's own verdict token, the input error with its meaning «verification did not happen» — the map names no outcome code the verifier lacks, and the set of options in the skill's run-command block equals the set of options the verifier accepts, `--help` excepted (prose outside that block is not scanned); the input-error line carries code 3 and the token «перевірки не було» taken from the verifier's own input-error message; on any mismatch it fails and names the code, the option or the token; the expected codes and options are taken from the verifier itself, not from a copy kept in the test
>
> — `spec.md §5, AC-10, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] RED (`tests/test_check_act_skill.py`): parse the outcome-code table rows from SKILL.md (code cell + token/meaning cell); assert `{code: token}` for `cli.EXIT` items, the code-3 row carries `cli.EXIT_INPUT_ERROR` and the token; no extra codes. Messages name the code.
- [ ] RED: the input-error token is extracted from real stderr — call `cli.main([...])` with `--contract`/`--act` pointing at a non-existent file under `tmp_path` (and `--out tmp_path`), capture stderr with `capsys`, take the phrase between the prefix «помилка вхідних даних, » and « — » (today: «перевірки не було»); no string literal of the token as the expected value.
- [ ] RED: find exactly one fenced ```` ```bash ```` block containing `act-verifier`; collect `--xxx` tokens; compare with option strings from `cli._parser()._actions` minus `-h`/`--help`; messages name missing/extra options. Assert the command line starts with `.venv/Scripts/act-verifier`.
- [ ] GREEN (`.claude/skills/check-act/SKILL.md`): add a Ukrainian section with the outcome-code table (one row per code 0/1/2/3, verdict token or «перевірки не було») and the run-command block, `--journal` marked optional (e.g. `[--journal]`), placeholders `<договір>`, `<акт1> <акт2>`, `<акт>`, `<тека звіту>`.
- [ ] Run the full suite; update `CLAUDE.md` line «Очікуваний стан…» from 304 to 304 + N with the real N.

## Edge cases

| Case | Behaviour |
|---|---|
| A code row missing or wrong (e.g. `2 | fail`) | fails naming the code and both tokens |
| Map lists code 4 | fails naming the extra code |
| Run block lacks `--journal` or adds `--verbose` | fails naming the option |
| Two `bash` blocks with `act-verifier` | fails: «exactly one run-command block» |
| Options mentioned in prose outside the block | ignored |
| `cli.py` input-error wording changes | token extraction finds no «перевірки не було» → fails naming the token |

## Definition of Done

- [ ] the new drift tests were red against T1's skill and are green now; mutating a code, an option or the token in SKILL.md makes a named failure (checked by hand once, then reverted)
- [ ] `.venv/Scripts/python -m pytest -q` — 304 + N passed, 0 failed, 0 xfailed, quoted in the task report; `CLAUDE.md` shows 304 + N
- [ ] no subprocess, no network, no model call in the test module
- [ ] every Hard Rule inlined above still holds
