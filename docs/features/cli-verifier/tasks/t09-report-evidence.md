---
id: T9
title: "Implement the Excel report, the Markdown report and the evidence block"
layer: "infra"
deps: ["T1"]
blocks: ["T10", "T11", "T12"]
acs: ["AC-03", "AC-09"]
files_hint: ["src/act_verifier/report.py", "tests/test_report.py"]
owner: "AlexanderSW"
estimate: "M"
context_budget: "M"
status: "done"
step: "COMMIT"
---

<!-- Self-contained task. Every inlined chunk carries a provenance signature
`<file> §<section>, <identifier>, verbatim|abridged`. The source always wins over the inline.
To the executing agent: work from what is inlined here. If a slice is insufficient, ambiguous,
or contradicts the code in front of you, open the named file and follow it. Do not invent. -->

# T9 — Implement the Excel report, the Markdown report and the evidence block

## Place in the sequence

- **Blocked by:** T1 — models · **Blocks:** T10 — error journal, T11 — scenario tests, T12 — cli.main · **Wave:** 2 (pure rendering of a `Report`; parallel with loaders and checks).
- **Lane:** shares `src/act_verifier/report.py` and `tests/test_report.py` with T10 — serialized (T9 first).

## Why (user story)

> **As an** accepting person
> **I want** every report to end with an evidence block that lists what was checked, what was not and why, and which file, sheet and row each number came from
> **So that** I can decide on the act without re-checking the arithmetic by hand
>
> — `spec.md §4, US-02, verbatim` · full text: [spec.md](../spec.md)

This task renders a `Report` into the two report files and the evidence block, using only the data in the `Report`.

## Inlined context

> Each run that reaches a verdict writes the report into the output folder (option, default `reports/`) as two files — an Excel workbook with the sheet «Перевірки» (code · check · status · expected · actual · source) and a Markdown file with the findings and the evidence block — and also prints the evidence block to the console. Report text is in Ukrainian; reasons quoted in English in this spec describe the content, not the literal wording (e.g. «empty price» = «порожня ціна»).
>
> — `spec.md §1, clarify decisions, verbatim` · full text: [spec.md](../spec.md)

> ```markdown
> ## Блок доказів
> Перевірено: <N позицій> × <перевірок рядка>, <перевірок підсумків>.
> Не перевірено: <шифр> — <check IDs> (<reason>); …            ← from Report.skipped
> Пропущено рядків без шифру: <file>, «КБ-2в», рядки <…>         ← from Act.skipped_rows (AC-09)
> Джерела чисел:
> - договірні ціни й обсяги — <file>, аркуш «Договірна ціна», рядки <as found>
> - попередні обсяги — <file>, …, аркуш «КБ-2в», рядки <as found>
> - перевірюваний акт — <file>, аркуші «КБ-2в», «КБ-3», рядки <as found>
> Розбіжностей: <count by status>. Вердикт: <pass | fail | needs_review>.
> ```
> Columns (Excel «Перевірки»): шифр (`Finding.code`, empty for act level) · перевірка · статус · очікувано · фактично (Decimal rendered as read, never float) · джерело (`Source.__str__`).
>
> — `contracts/cli.md §6.1 + §6.3, abridged` · full text: [cli.md](../contracts/cli.md)

> **Owner decision (tasks stage, 2026-11-26, closes cli.md OQ-A1):** report files are `<act-stem>_report.xlsx` and `<act-stem>_report.md` in `--out` (act-stem = current act file name without extension); a rerun overwrites them; a missing `--out` folder is created (parents too) — after the overwrite guard.
>
> — `tasks/_epic.md, Decisions, verbatim` · full text: [_epic.md](./_epic.md)

> **Chosen:** Option 1. Every value has exactly one origin record, the evidence block is a pure rendering of `Report` (`render_evidence(report) -> str`, signature unchanged) [...]
>
> — `adr/0003-carry-source-on-every-value-and-structured-skips.md, Decision outcome, abridged` · full text: [ADR-0003](../adr/0003-carry-source-on-every-value-and-structured-skips.md)

> **Hard rule:** Кожен звіт закінчується блоком доказів: що перевірено, що ні, звідки числа. | Determinism: no timestamps in findings or evidence block.
>
> — `CLAUDE.md, Правила + sad.md §8, Determinism, abridged` · full text: [CLAUDE.md](../../../../CLAUDE.md)

**Fallback:** insufficient or contradicted by the code → read [contracts/cli.md](../contracts/cli.md) §6 and [docs/checks.md](../../../checks.md) «Блок доказів». Do not guess.

## Data delta

No DB changes. Reads `Report`, `Finding`, `Skipped`, `Source`, `Act.header_row` / `skipped_rows` (via the input sources in `Report`); writes `.xlsx` + `.md` files only (never an input — the guard lives in T12).

## API contract

- `write_excel(report, path)` → sheet «Перевірки», one row per finding **including pass**.
- `render_markdown(report) -> str` → findings, then the evidence block as the last section.
- `render_evidence(report) -> str` → the block above; same text goes to stdout (T12).
- `report_paths(out_dir, act_path) -> (xlsx_path, md_path)` → used by the overwrite guard before any write.

— `contracts/cli.md §6.1–§6.3, abridged` · full text: [cli.md](../contracts/cli.md)

## Acceptance criteria

### AC-03 — happy path (evidence block)

> **Given** any act the verifier was able to read
> **When** the accepting person opens the report
> **Then** the report ends with an evidence block that states how many positions and checks were verified, lists every check that was not performed together with the position and the reason, names the file, sheet and rows each group of numbers was actually read from (rows as found in that file, not as assumed by the README), gives the count of discrepancies by status, and repeats the verdict
>
> — `spec.md §5, AC-03, verbatim` · full text: [spec.md](../spec.md)

### AC-09 — happy path (shifted layout)

> **Given** an act whose header row sits in a different row than the README describes, or whose totals rows do not follow the table immediately (new reference scenarios), but whose labels match after normalization by prefix — including empty rows or rows without a position code (e.g. a note) between the last position and «Разом без ПДВ»
> **When** the employer reviewer runs the verifier
> **Then** the verifier produces the same verdict and findings as for the equivalent act in the README layout, rows without a position code are not treated as positions, and the evidence block cites the rows where the data was actually found and the rows it skipped
>
> — `spec.md §5, AC-09, verbatim` · full text: [spec.md](../spec.md)

## Checklist

- [ ] `report_paths(out_dir, act_path)` per the owner decision — `src/act_verifier/report.py`
- [ ] `write_excel(report, path)`: create parent folder, sheet «Перевірки», header row шифр · перевірка · статус · очікувано · фактично · джерело, one row per finding in report order; values as strings (never float) — `src/act_verifier/report.py`
- [ ] `render_evidence(report)`: lines exactly in the cli.md §6.3 order; «Не перевірено: —» when nothing skipped; row ranges rendered from `Source.row` values as found (compress consecutive rows `7–20`); skipped rows line only when any; discrepancies counted by status (`fail`, `unknown`, `warning`) — `src/act_verifier/report.py`
- [ ] `render_markdown(report)`: a findings table, then `render_evidence(report)` as the final section — `src/act_verifier/report.py`
- [ ] Tests with a hand-built `Report`: evidence for a pass report, a report with skips (`5-2 — C03, C04 (порожня ціна)`), shifted rows (header 11 → rows cited as 12–…), skipped rows; Excel round-trip with openpyxl (pass rows present); two renders identical — `tests/test_report.py`

## Edge cases

| Case | Behaviour |
|---|---|
| no previous acts | «попередні обсяги — —» (nothing read), never invented file names |
| several skips on one position | grouped on one entry: `<code> — C03, C04 (<reason>)` |
| act-level skip (`code is None`) | rendered with «акт» in place of the code |
| non-contiguous rows | rendered as ranges and singles, e.g. `9–15, 18` |
| Decimal rendering | `str(Decimal)` as read — `100.00` stays `100.00` |

## Definition of Done

- [ ] `tests/test_report.py` (report + evidence part) passes
- [ ] the Markdown report's last section is the evidence block in every test
- [ ] no timestamp in either file; two renders of one `Report` are identical
- [ ] every Hard Rule inlined above still holds
- [ ] lint + vet clean
