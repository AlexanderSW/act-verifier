---
id: T5
title: "Implement load_contract and the shared cell readers"
layer: "infra"
deps: ["T1", "T4"]
blocks: ["T6"]
acs: ["AC-07", "AC-08"]
files_hint: ["src/act_verifier/loaders.py", "tests/test_loaders.py"]
owner: "AlexanderSW"
estimate: "S"
context_budget: "M"
status: "todo"
step: ""
---

<!-- Self-contained task. Every inlined chunk carries a provenance signature
`<file> §<section>, <identifier>, verbatim|abridged`. The source always wins over the inline.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file and follow it. Do not invent. -->

# T5 — Implement load_contract and the shared cell readers

## Place in the sequence

- **Blocked by:** T1 — models, T4 — layout helper · **Blocks:** T6 — load_act · **Wave:** 3.
- **Lane:** shares `src/act_verifier/loaders.py` and `tests/test_loaders.py` with T6 — serialized (T5 first; T6 reuses the cell readers written here).

## Why (user story)

> **As an** employer reviewer
> **I want** an act whose labels sit in different rows to verify the same way, and an unrecognised layout to stop with an input error naming the missing label
> **So that** I can safely try the tool on real acts
>
> — `spec.md §4, US-04, verbatim` · full text: [spec.md](../spec.md)

This task reads the contract price by labels and establishes how every cell becomes a `Decimal` or `None`.

## Inlined context

> `loaders.py` load_contract(path) -> dict[str, ContractPosition]; load_act(path) -> Act (openpyxl, data_only=True, read-only)
>
> — `sad.md §5, internal decomposition, loaders.py, verbatim` · full text: [sad.md](../sad.md)

> | Numbers | `Decimal(str(cell))` on read; money quantized to 0.01 `ROUND_HALF_UP`; tolerance `TOLERANCE = 0.01`; no float arithmetic |
> | Empty values | empty cell or formula without a stored value (`data_only=True` → `None`) is `None`, never 0; `None` → `unknown` or skip, never `pass` |
>
> — `sad.md §8, Crosscutting concepts, verbatim` · full text: [sad.md](../sad.md)

> Loaders wrap openpyxl/zip failures into `unreadable_file` [...]
>
> — `adr/0002-signal-input-errors-with-typed-exception.md, Decision outcome, abridged` · full text: [ADR-0002](../adr/0002-signal-input-errors-with-typed-exception.md)

> **Hard rule:** Числа беруться лише з файлів. Не вигадувати й не підставляти значення «за змістом». Верифікатор лише читає вхідні файли. Нічого в них не записує.
>
> — `CLAUDE.md, Правила, verbatim` · full text: [CLAUDE.md](../../../../CLAUDE.md)

Current code facts (breakdown-time snapshot): the contract sheet «Договірна ціна» has headers in row 6 («№ з/п», «Шифр», «Найменування робіт», «Од. виміру», «Кількість за договором», «Ціна за од., грн без ПДВ», «Вартість, грн без ПДВ»), positions below, then «Разом без ПДВ» / «ПДВ 20%» / «Всього з ПДВ» rows in column C. The verifier does not need the contract totals.

**Fallback:** insufficient or contradicted by the code → read [data-model.md](../data-model.md) §ContractPosition, [ADR-0001](../adr/0001-locate-layout-by-normalized-unique-labels.md) and `scripts/generate_fixtures.py::write_contract`. Do not guess.

## Data delta

No DB changes. Builds `ContractPosition` (read-only of the existing type):

| Field | Type | Constraints | Change |
|---|---|---|---|
| `code` | `str` | key of the contract map; unique | read-only |
| `unit` | `str` | compared after `strip()` (C02) | read-only |
| `qty` | `Decimal` | non-null in the current type | read-only |
| `price` | `Decimal` | non-null in the current type | read-only |
| `source` | `Source` | file / sheet / row actually read (ADR-0003) | read-only |

— `data-model.md §Entities, ContractPosition, abridged` · full text: [data-model.md](../data-model.md)

> a duplicate code in the contract is <!-- TBD: input error or a C-check? spec is silent -->. An empty `qty`/`price` cell cannot be represented by the current non-`Optional` type — see the audit, drift item D5.
>
> — `data-model.md §ContractPosition, Constraints, verbatim` · full text: [data-model.md](../data-model.md)

## API contract

Internal — no API surface. Raises `InputError` kinds `missing_label`, `ambiguous_label`, `unreadable_file` (`contracts/cli.md §4, abridged` · full text: [cli.md](../contracts/cli.md)).

## Acceptance criteria

### AC-07 — error (missing layout label)

> **Given** an input file in which a layout label cannot be found — for the contract price: the sheet «Договірна ціна» and the header columns «Шифр», «Найменування», «Од. виміру», «Кількість», «Ціна», «Вартість»; [...]
> **When** the employer reviewer runs the verifier
> **Then** it stops with outcome code 3 and a message that names the missing label, the file and the sheet, and produces no verdict; a label that is present but whose value cell is empty is not this case — it is missing data and yields unknown for every check that uses that value [...]
>
> — `spec.md §5, AC-07, abridged (contract part)` · full text: [spec.md](../spec.md)

### AC-08 — error (ambiguous layout)

> **Given** an input file in which more than one row matches the same layout label after normalization (new reference scenario with an ambiguous label)
> **When** the employer reviewer runs the verifier
> **Then** it stops with outcome code 3 and a message that names the label and the competing rows, and never silently uses the first match
>
> — `spec.md §5, AC-08, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `_open(path)`: `load_workbook(path, read_only=True, data_only=True)`; any openpyxl / `zipfile.BadZipFile` / `KeyError` / `OSError` on open → `InputError("unreadable_file", file=…)` — `src/act_verifier/loaders.py`
- [ ] `_dec(value) -> Decimal | None`: `None` / `""` → `None`; `int`/`float` → `Decimal(str(value))`; text → `None` (numbers written as text are a stage-1 non-goal, spec §3 — treating them as missing data can only yield `unknown`, never a false `pass`; cite spec §3 in a code comment) — `src/act_verifier/loaders.py`
- [ ] `_text(value) -> str`: `None` → `""`, else `str(value).strip()` — `src/act_verifier/loaders.py`
- [ ] `load_contract(path)`: `find_sheet("Договірна ціна")`, `find_header_row(["Шифр","Найменування","Од. виміру","Кількість","Ціна","Вартість"])`; rows below the header with a non-empty «Шифр» until the first row whose code cell is empty and whose text starts with «Разом без ПДВ» (or sheet end); build `ContractPosition` with `Source(file_name, "Договірна ціна", row)` — `src/act_verifier/loaders.py`
- [ ] Tests: `load_contract(data/synthetic/contract_boq.xlsx)` → 14 positions, `Decimal` qty/price, sources rows 7–20; an in-memory workbook with a missing «Ціна» column → `missing_label` «Ціна»; a corrupt file → `unreadable_file` — `tests/test_loaders.py`

## Edge cases

| Case | Behaviour |
|---|---|
| contract qty or price cell empty | not fixed upstream (data-model D5: type is non-optional). Never substitute 0 and never drop the position; no fixture has it. Pass the `None` through and list it in the review notes as an open question |
| duplicate code in the contract | not fixed upstream (data-model §ContractPosition TBD); no fixture has it. Do not silently keep the first or the last — list it in the review notes as an open question |
| `Source.file` | the file **name** as given (e.g. `contract_boq.xlsx`), as in the docs/checks.md evidence example |
| file opened | read-only; never saved |

## Definition of Done

- [ ] `tests/test_loaders.py` (contract part) passes
- [ ] no `float` arithmetic; every number goes through `Decimal(str(...))`
- [ ] the two TBD cases above are listed in the review notes, not silently decided
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
