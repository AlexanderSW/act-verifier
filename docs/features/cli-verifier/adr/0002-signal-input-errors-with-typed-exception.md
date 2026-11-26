---
status: Accepted
owner: "AlexanderSW"
reviewers: ["Tech Lead"]
updated_at: "2026-11-26"
feature_size: "S"
ticket: "docs/features/cli-verifier/spec.md"
---

# 0002 — Signal input errors with a typed exception

- **Status:** Accepted
- **Date:** 2026-11-26
- **Deciders:** AlexanderSW (project owner), with Claude during the design pass

## Context

The spec defines an input error as «verification did not happen» (CONTEXT glossary) with outcome code 3 for missing/ambiguous labels, unreadable workbooks, invocation errors and overwrite refusals (spec AC-06, AC-07, AC-08, AC-13). The scenario tests call `load_contract` / `load_act` / `verify` directly, the command maps the result to a code, the reference file gains an `expected_error` kind, and the stage-2 tool will reuse the same loaders. The way an input error travels therefore crosses loaders, cli, tests and fixtures.

## Decision drivers

- Quality goal 1: a half-read act must never reach the checks (spec §6 «False pass»).
- Spec AC-15: the expected-input-error scenario matches an error kind and label.
- Existing signatures `load_act(path) -> Act`, `load_contract(path) -> dict` are called by `tests/test_verifier.py` and should stay.

## Considered options

1. **Typed exception `InputError(kind, label, file, sheet, rows)`** raised at the first problem, caught once in `cli.main`.
2. **Collect all problems in a result object** — loaders return the act plus a list of layout problems; the caller must check the list.

## Decision outcome

**Chosen:** Option 1 (owner choice). `InputError` lives in `models.py`; `kind` ∈ {`missing_label`, `ambiguous_label`, `unreadable_file`, `invocation`, `overwrite_refused`}. Loaders wrap openpyxl/zip failures into `unreadable_file`; an `argparse.ArgumentParser` subclass turns parse errors into `invocation`; the overwrite guard raises `overwrite_refused`. `cli.main` is the only place that catches it: Ukrainian message on stderr naming label, file and sheet (and the competing rows for ambiguity), no report, return 3. Any other exception propagates as a bug.

**Amendment 2026-11-26 (review 2, finding 2; owner choice).** The kind set gains `duplicate_code`: a «Шифр» repeated in the contract. It was raised as `ambiguous_label`, whose message calls the code a «підпис» and says only the first match is not used; the rule (docs/checks.md) is that neither row is used. Same handling: caught only in `cli.main`, message names the code, file, sheet and rows, no report, return 3. The decision itself (typed exception, first problem stops the load) is unchanged.

## Consequences

**Positive**
- Loader signatures unchanged; scenario tests use `pytest.raises(InputError)` and compare `kind` / `label` with `expected_error`.
- Impossible to forget the check — a failed load cannot return a partial `Act`.

**Negative**
- Stops at the first problem: an act missing three labels reports one per run.

**Neutral**
- Switching to collected problems later means changing loader return types and every caller, including stage 2 — the reason this is an ADR.

## Links

- Spec: [[../spec.md]] AC-06, AC-07, AC-08, AC-13, AC-15
- SAD: [[../sad.md]] §4, §8
- Related ADR: [[0001-locate-layout-by-normalized-unique-labels]]
