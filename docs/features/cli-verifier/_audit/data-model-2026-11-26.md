# Audit — data-model — cli-verifier — 2026-11-26

## Outcome

**No schema change: zero staged migrations.** This is a valid result under the size-matrix fast lane. The repo has no database (`docs/architecture-map.md` §Conventions: «Migrations: none (no database)», frontmatter `migration_tool: ""`). Every store is a file (sad §3/§5). `docs/features/cli-verifier/migrations/` is not created, and nothing was written to a live `migrations/` tree, which does not exist.

- Size **S**, route **quick** (from `.size` / `.route`).
- `target_surfaces: [cli]` (from sad.md frontmatter).
- Output: `docs/features/cli-verifier/data-model.md`, covering the file-based entities and domain dataclasses the feature reads and writes.

## Convention sources

| Topic | Decision | Source |
|---|---|---|
| Store | files only: xlsx in (read-only), xlsx + md report out, CSV journal, JSON reference files | architecture-map §Datastores; sad §3, §5 |
| Types | Python type hints, `Decimal` for money and volume, `None` for empty cells (never 0) | CLAUDE.md; sad §8; `src/act_verifier/models.py` |
| Identity | natural keys (position `code`, act `number`, Excel row numbers), no surrogate IDs | `models.py`; docs/checks.md |
| Promote-time hint | N/A, no migration tool. `implement` has nothing to promote | — |

No divergence between the architecture and the repo.

## Drift: domain layer (`models.py`) vs designed shapes (sad §5, ADRs)

No `_drift/*.sql` was written because there is no SQL. Each item below is a code delta for `tasks` / `implement`.

| # | Kind | Item | Designed in | Current code |
|---|---|---|---|---|
| D1 | field-without-type | `InputError(kind, label, file, sheet, rows)` | ADR-0002, sad §5 | absent from `models.py` |
| D2 | type-mismatch | `Report.skipped: list[Skipped]` with `Skipped(check, code, reason)` | ADR-0003 | `list[str]` (`models.py`, `Report`) |
| D3 | field-without-type | `Act.sources`, `Act.header_row`, `Act.skipped_rows` | ADR-0003, sad §5 | absent |
| D4 | schema gap | optional `layout` and `expected_error` in `expected.json`; `expected_verdict` / `expected_findings` absent when `expected_error` is present | ADR-0004, sad §5, AC-15 | `tests/test_fixtures_integrity.py::test_expected_json_schema` requires `expected_findings` |
| D5 | nullability question | `ContractPosition.qty` / `price` are non-`Optional` `Decimal`. An empty contract cell cannot be represented | CLAUDE.md «missing data → unknown» | spec is silent on empty contract cells |

## Open items (`<!-- TBD -->`)

- **D5 / contract empty cells and duplicate codes.** The spec does not say whether an empty `qty`/`price` in the contract price is missing data (→ `unknown` of the dependent checks) or an input error. It also does not say how a duplicate contract code should be handled. Owner: AlexanderSW. Resolve before `implement` writes `load_contract` (candidate for `/sdd:clarify cli-verifier` or a spec patch).

## Self-check (4 mandatory)

| Check | Result |
|---|---|
| Naming matches repo convention | pass. Field names are taken verbatim from `models.py`, sad §5 and the journal header |
| Down reversibility | N/A, zero migrations |
| FK indexes | N/A, no database |
| Convention adherence | pass. Only `Decimal` for numbers and `None` for empty values; no house style imposed |

Mermaid `erDiagram`: `mmdc` is not installed, so the diagram got the structural lint instead. All cardinality glyphs are valid (`||--||`, `||--o{`, `}o--o{`, `||--o|`) and every attribute line has the form `type name [PK] ["comment"]`. Pass.

## Next stage

`api` is evaluated on the quick route. The feature introduces a CLI command (flags, outcome codes 0/1/2/3, report and journal formats), and the fast-lane table counts a new CLI command as a contract change, so `api` is **not** skipped. Next: `/sdd:api cli-verifier`.
