---
status: Accepted
owner: "AlexanderSW"
reviewers: ["Tech Lead"]
updated_at: "2026-11-26"
feature_size: "S"
ticket: "docs/features/cli-verifier/spec.md"
---

# 0004 — Record the generator's layout map in the reference file

- **Status:** Accepted
- **Date:** 2026-11-26
- **Deciders:** AlexanderSW (project owner), with Claude during the design pass

## Context

`tests/test_fixtures_integrity.py` checks the reference files independently of `src/` (so a generator bug cannot hide behind a verifier bug) by reading xlsx at hard-coded rows (`min_row=9`, contract `min_row=7`). The seven new generator scenarios move the header and the totals rows, so this helper would read the wrong cells or fail. AC-09 also needs a reference for «the evidence block cites the rows where the data was actually found». The choice touches the generator, `expected.json`, the integrity tests and the scenario tests.

## Decision drivers

- CLAUDE.md: fixtures change only through `scripts/generate_fixtures.py`, with a stated reason; integrity suite must stay green (spec AC-15).
- Integrity tests must stay independent of `src/` (`tests/test_fixtures_integrity.py` docstring).
- Spec AC-09: rows actually found must be checkable.

## Considered options

1. **Generator writes a `layout` map into `expected.json`** — header, first data, subtotal/VAT/total rows per input; integrity tests read by it, README rows when absent.
2. **A second, minimal label search inside the integrity tests** — no schema change, but it re-implements the same heuristic, so a flaw in the idea repeats on both sides, and AC-09 has nothing to compare against.
3. **Skip arithmetic integrity checks for the new fixtures** — simplest, but exactly the new fixtures lose independent verification.

## Decision outcome

**Chosen:** Option 1 (owner choice). `expected.json` gains an optional `layout` object written only by the generator from the rows it actually used; `test_expected_json_schema` accepts `layout` and `expected_error` (ADR-0002); `read_act_totals` and the contract reader take rows from `layout`, falling back to README rows. Scenario tests for shifted layouts assert that the evidence block's cited rows equal the `layout` rows. The generator commit states the reason (new layout scenarios, CLAUDE.md fixture rule).

## Consequences

**Positive**
- Integrity checks stay independent of `src/` and cover every fixture, including shifted ones.
- AC-09 becomes an exact assertion, not «looks plausible».

**Negative**
- `expected.json` schema grows by one optional field to maintain in the generator and schema test.

**Neutral**
- Real employer acts have no `layout` map; for them the evidence block's rows are the only record — which is the intended behaviour.

## Links

- Spec: [[../spec.md]] AC-09, AC-15
- SAD: [[../sad.md]] §4, §5
- Related ADR: [[0001-locate-layout-by-normalized-unique-labels]], [[0003-carry-source-on-every-value-and-structured-skips]]
