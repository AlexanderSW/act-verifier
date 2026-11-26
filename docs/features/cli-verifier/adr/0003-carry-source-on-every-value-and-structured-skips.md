---
status: Accepted
owner: "AlexanderSW"
reviewers: ["Tech Lead"]
updated_at: "2026-11-26"
feature_size: "S"
ticket: "docs/features/cli-verifier/spec.md"
---

# 0003 — Carry a Source on every value and record skips as structured entries

- **Status:** Accepted
- **Date:** 2026-11-26
- **Deciders:** AlexanderSW (project owner), with Claude during the design pass (easy depth — default accepted via the assumptions ledger)

## Context

The evidence block must name the file, sheet and rows each group of numbers was actually read from — rows as found, not as assumed by the README — and list every check not performed with position and reason (spec AC-03, AC-09, US-02). Today `ContractPosition` and `ActRow` carry a `Source`, but `Act` totals, КБ-3 values, the act number, the header row and skipped rows do not, and `Report.skipped` is a plain `list[str]`. The shape chosen here is shared by models, loaders, checks and report.

## Decision drivers

- CLAUDE.md: every report ends with the evidence block; numbers only from files.
- Spec AC-03 / AC-09: rows as actually found; spec AC-04 / AC-05: «not checked» with the reason.
- Quality goal 1: an unverifiable claim in the evidence block is itself a false assurance.

## Considered options

1. **Per-value provenance + structured skips** — `Act.sources: dict[str, Source]` for every scalar read (number, subtotal, vat, total, kb3_period_total, kb3_cumulative_total), `Act.header_row`, `Act.skipped_rows`; `Report.skipped: list[Skipped(check, code, reason)]`; `Report` also carries the input Sources the evidence block needs.
2. **One layout summary per file** — loaders return a separate «layout found» object (header row, data range, totals rows) and checks keep free-text skip strings; less model change, but the evidence block must re-join numbers to rows and skip reasons cannot be counted or tested structurally.

## Decision outcome

**Chosen:** Option 1. Every value has exactly one origin record, the evidence block is a pure rendering of `Report` (`render_evidence(report) -> str`, signature unchanged), and tests can assert skip records by `(check, code, reason)`.

## Consequences

**Positive**
- Evidence-block rows are testable against the generator's layout map (ADR-0004).
- Skip counts in «Перевірено / Не перевірено» come from data, not string parsing.

**Negative**
- `Report.skipped` changes type (`list[str]` → `list[Skipped]`); `models.py` grows.

**Neutral**
- Stage 2 can serialise `Report` to the tool response without re-reading files.

## Links

- Spec: [[../spec.md]] AC-03, AC-04, AC-05, AC-09
- SAD: [[../sad.md]] §4, §8
- Related ADR: [[0004-record-generator-layout-map-in-reference-file]]
