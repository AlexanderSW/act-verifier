---
status: Accepted
owner: "AlexanderSW"
reviewers: ["Tech Lead"]
updated_at: "2026-11-26"
feature_size: "S"
ticket: "docs/features/cli-verifier/spec.md"
---

# 0001 — Locate layout by normalized unique labels

- **Status:** Accepted
- **Date:** 2026-11-26
- **Deciders:** AlexanderSW (project owner), with Claude during the design pass

## Context

The README describes fixed rows (contract header row 6, act header row 8, totals in column G, КБ-3 rows 5–8), but the feature must show headroom for real employer acts whose layout is unknown (spec §1, US-04). The spec already fixed the matching rule (normalize, prefix, more than one candidate = input error); this ADR fixes *where* that rule lives and how far it reaches, because the loaders, the fixture generator, the integrity tests and the stage-2 tool all depend on it.

## Decision drivers

- Quality goal 2: layout tolerance with a loud failure (SAD §1; spec AC-07, AC-08, AC-09).
- Quality goal 1: no false pass — a guessed row is a silent wrong verdict (spec §6 «False pass»).
- CLAUDE.md: numbers only from files, nothing substituted.

## Considered options

Fixed README rows are not an option: spec §1 already commits to locating labels instead of fixed row numbers.

1. **Label search with normalization, prefix match and uniqueness in a defined region** — one `layout` helper used by both loaders.
2. **Per-layout profile file** — a mapping file (sheet names, rows, columns) chosen per supplier; precise, but each new layout needs a profile before the first run, and there is no real layout yet to profile.

## Decision outcome

**Chosen:** Option 1. Every structural place — sheet name, header row (the row holding all six header labels), КБ-2в totals rows (searched only below the header row), the four КБ-3 rows, and the КБ-2в «Акт №» title — is found by `layout.find_*` after normalization (trim, collapse whitespace incl. non-breaking, casefold) by prefix. Zero matches → `InputError(missing_label)`; two or more → `InputError(ambiguous_label)` with the competing rows (ADR-0002). Values are taken from the «Вартість» header column on a totals row and from the cell right of a КБ-3 label. The act number is the exception: a missing title is missing data, not an input error (spec §1 clarify decisions).

## Consequences

**Positive**
- Shifted headers and gaps before the totals verify without code changes (AC-09).
- Unknown layouts fail loudly with the label name, which is exactly the measurement plan for the first real act (spec §7).

**Negative**
- A real act whose labels differ textually (e.g. «Сума» instead of «Вартість») still fails; only positional drift is tolerated.
- Prefix matching can collide with unrelated text («ПДВ…» in a note row); mitigated by search regions and the ambiguity error.

**Neutral**
- A profile file (option 2) can be layered on top later by feeding alternative label texts into the same helper.

## Links

- Spec: [[../spec.md]] §1, AC-07, AC-08, AC-09
- SAD: [[../sad.md]] §4
- Related ADR: [[0002-signal-input-errors-with-typed-exception]], [[0004-record-generator-layout-map-in-reference-file]]
