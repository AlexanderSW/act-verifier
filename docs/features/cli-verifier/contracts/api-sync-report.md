---
status: Draft
owner: "AlexanderSW"
updated_at: "2026-11-26"
feature_size: "S"
contract: cli.md
---

# API sync report — cli-verifier

- **Contract form:** `contracts/cli.md`, read from `sad.md` frontmatter `target_surfaces: [cli]` (not re-derived). There is no `openapi.yaml` or `events.md`: every flow is synchronous (sad §6 note), so there is no async actor and no idempotency key.
- **Inputs found:** `data-model.md` ✓ (no schema change, file shapes only) · `sad.md` §6 F1–F5 + Critical flow 1 ✓ · `spec.md` §4/§5 ✓ · ADR-0001…0004 ✓ · `CONTEXT.md` (repo root) ✓.
- **Size / route:** S / quick (from `.size` / `.route`).
- **HTTP defaults not applicable:** BearerAuth, cursor pagination, URL versioning and the `{code, message, details?}` envelope have no CLI counterpart. Input-error identifiers follow ADR-0002 `kind`s (deviation by ADR-0002 from the `module.error_name` default).

## A. Field origins

| schema_path | origin | confidence |
|---|---|---|
| command `act-verifier` | `pyproject.toml` `[project.scripts]` → `act_verifier.cli:main` | high |
| `main(argv) -> int` | `src/act_verifier/cli.py`; sad §5 | high |
| `--contract` (required) | `cli.py` `required=True`; spec §1 clarify «required inputs», AC-06 | high |
| `--act` (required) | `cli.py` `required=True`; spec §1 clarify, AC-06 | high |
| `--previous` (0..n) | `cli.py` `nargs="*"`; spec §1 clarify «previous acts optional» | high |
| `--out` (default `reports`) | `cli.py` `default=Path("reports")`; spec §1 clarify «option, default `reports/`» | high |
| `--journal [PATH]` | spec §1, AC-14; sad §8 «opt-in `--journal [PATH]`» | high |
| `--journal` default path | spec §1 clarify `journal/agent_errors.csv` relative to cwd | high |
| outcome 0/1/2 | data-model → `Report.verdict`; spec §1; sad F1 | high |
| outcome 3 | spec §1, AC-06; ADR-0002; sad §8 | high |
| `InputError.kind` values | ADR-0002 (`missing_label`, `ambiguous_label`, `unreadable_file`, `invocation`, `overwrite_refused`; `duplicate_code` added by the ADR-0002 amendment 2026-11-26); data-model `InputError` | high |
| `InputError.label/file/sheet/rows` | ADR-0002; data-model | high |
| kind for «input path does not exist» | sad F2 branch; `unreadable_file` by owner decision 2026-11-26 (OQ-A3) | high |
| Excel sheet «Перевірки» + 6 columns | spec §1 clarify; `report.write_excel` docstring; data-model `Finding` | high |
| Markdown report | spec §1 clarify, AC-03; data-model `Report` | high |
| report file names | **no origin** in any input | none → OQ-A1 |
| `--out` folder creation | **no origin** | none → OQ-A1 |
| stdout = evidence block | spec §1 clarify; sad Critical flow 1 | high |
| stderr = message on code 3 | sad §8 «stderr message (Ukrainian)» | high |
| evidence block lines | `docs/checks.md` «Блок доказів»; spec AC-03, AC-09, AC-11; ADR-0003; data-model `Skipped`, `Act.skipped_rows`, `Source` | high |
| journal header | `journal/agent_errors.csv:1`; data-model `JournalLine` | high |
| journal `found_by` = `act-verifier` | spec AC-14 «names the verifier»; console-script name in `pyproject.toml`; owner decision 2026-11-26 (OQ-A5) | high |
| journal `code` empty at act level | data-model `JournalLine.code` | high |
| journal escaping rule | spec AC-14, §6.1 | high |
| exit 1 on an unexpected exception | sad §8, §11 (accepted Low risk) | high (as documented risk) → OQ-A2 |

## B. Drift checklist

1. **Command ↔ data-model** *(core)* — ✓. The command reads `ContractPosition`, `Act`, `ActRow` and `Source`, and writes `Report`/`Finding`/`Skipped` (report files) and `JournalLine` (journal). Every output column maps to a data-model field.
2. **Error identifier ↔ repo error definition** *(core)* — ✓ with a note. The repo's form is the ADR-0002 `InputError.kind` set. It is not yet in code (`models.py` has no `InputError`, audit D1). The contract uses those five kinds verbatim and adds none. A non-existent input path gets `unreadable_file` (owner decision, OQ-A3), so no new kind is needed. *Amended 2026-11-26 (review 2, finding 2):* the ADR-0002 amendment adds a sixth kind, `duplicate_code` (a «Шифр» repeated in the contract); `contracts/cli.md` §4 lists it.
3. **Validation ↔ constraint** *(core)* — ✓. Required/optional options match spec §1 clarify. Status literals match the `Status` enum. The journal status subset (`fail|unknown|warning`) matches data-model `JournalLine.status`. Path equality matches the spec's case-insensitive resolved-path rule.
4. **Contract ↔ sequence** *(supporting)* — ✓ forward. Every `alt` branch of F1–F5 and Critical flow 1 has an outcome row in `cli.md` §3/§4:
   - F1: fail→1, needs_review→2, pass→0.
   - F2: invocation→3, missing path→3, overwrite→3.
   - F3: unreadable→3, missing_label→3, ambiguous→3.
   - F4: incomplete previous acts / empty values → 2 or 1.
   - F5: no option / option → journal behaviour, code unchanged.

### Back-feed (coverage)

| AC | Contract section | ✓ |
|---|---|---|
| AC-01 | §3 code 0, §6.1, §6.3, §7 | ✓ |
| AC-02 | §3 code 1, §7 | ✓ |
| AC-03 | §6.3 | ✓ |
| AC-04 | §3 code 2, §6.3, §7 | ✓ |
| AC-05 | §3 code 2, §4 «not an input error», §6.3 | ✓ |
| AC-06 | §2 rules, §3 code 3, §4 `invocation` | ✓ |
| AC-07 | §4 `missing_label` | ✓ |
| AC-08 | §4 `ambiguous_label` | ✓ |
| AC-09 | §6.3 rows as found, skipped rows | ✓ |
| AC-10 | §3 code 1, §6.1 `джерело` (contract + each previous act) | ✓ |
| AC-11 | §2 `--previous`, §3 code 2, §6.3 reasons | ✓ |
| AC-12 | §3 code 1 | ✓ |
| AC-13 | §4 `overwrite_refused`, §5 | ✓ |
| AC-14 | §2 `--journal`, §6.4 | ✓ |
| AC-15 | §4 tests match `kind`/`label`, §3 per-code report/no-report | ✓ |
| AC-16 | §3 code 2 | ✓ |

Every option and outcome maps to a user story: US-01 (command, codes 0–2, report), US-02 (evidence block), US-03 (codes), US-04 (`missing_label`/`ambiguous_label`), US-05 (`--journal`), US-06 (`main(argv)` callable from tests). No orphan sequence.

## C. Flags

Five flags (≥3, so the run pauses for the owner). None of them is a core ✗. Each one is a hole the contract cannot fill from its inputs without inventing a value.

| # | Flag | Kind | Proposed owner |
|---|---|---|---|
| OQ-A1 | Report file names in `--out`, whether a rerun overwrites them, and whether a missing `--out` folder is created. No input fixes any of these. The overwrite guard (AC-13) needs the full paths before any write. | contract gap (missing value) | specify |
| OQ-A2 | `--help` (argparse built-in) exits 0 with no verdict, the same code as pass. An unexpected exception or a report `OSError` exits 1, the same code as fail (sad §11 already accepts the second). No §6 flow shows either branch. | sequence gap | sequences |
| OQ-A3 | A non-existent input path (F2) has no `kind` assigned in ADR-0002: `invocation` or `unreadable_file`? | contract gap (ambiguity) | design (ADR-0002) |
| OQ-A4 | `--journal` with an optional value right after `--previous` (nargs `*`) is ambiguous on the command line, e.g. `--previous a.xlsx --journal --act b.xlsx` parses, but `--journal` placed before positional-like values may swallow them. | contract detail | api (this stage) |
| OQ-A5 | Literal `found_by` value in the journal («names the verifier as the finder»). | contract gap (missing value) | specify |

Inherited, not re-flagged: data-model audit D5 (empty cells and duplicate codes in the contract price). This sits in the loader, not on the CLI surface.

## Resolution

Owner, 2026-11-26 (shared 4-state actions):

| # | Action | Result |
|---|---|---|
| OQ-A1 | **Save as OQ**, owner `specify`, due: before the contract is finalized | `cli.md` §6.1 keeps `unresolved` markers. Fix the report file names, the rerun behaviour and the `--out` creation in spec §1. Then run `/sdd:api cli-verifier --reconcile`. |
| OQ-A2 | **Save as OQ**, owner `sequences`, due: before the contract is finalized | `cli.md` §3 keeps an `unresolved` marker. Add a §6 branch (or a spec rule) for `--help` and for an unexpected exception so neither collides with 0 or 1. |
| OQ-A3 | **Fix the contract** | `unreadable_file` for a non-existent input path. Recommended: a one-line note in ADR-0002 (via `/sdd:decide-adr` or an edit by the owner). This skill does not edit ADRs. |
| OQ-A4 | **Fix the contract** (resolved in this stage, no owner question) | There are no positional arguments, so `--journal` takes the next token only if it does not start with `-`. No ambiguity remains. |
| OQ-A5 | **Fix the contract** | `found_by` = `act-verifier`. |

Open after this run: OQ-A1 and OQ-A2. Neither is a core ✗. The core points (B.1–B.3) are ✓, so the contract is committed as Draft with these two parked.
