"""Тести звіту (T9 — Excel, Markdown, блок доказів; T10 — журнал). Лише tmp_path, ніколи journal/."""

from pathlib import Path

from openpyxl import load_workbook

from act_verifier.models import Finding, Report, Skipped, Source, Status
from act_verifier.report import (
    compress_rows,
    render_evidence,
    render_markdown,
    report_paths,
    write_excel,
    write_markdown,
)

ROW_IDS = ["C01_position_in_contract", "C02_unit_matches", "C03_price_matches_contract",
           "C04_amount_arithmetic", "C05_within_remaining_volume", "C06_no_duplicate_positions",
           "C11_required_values_present"]
ACT_IDS = ["C07_subtotal", "C08_vat", "C09_total_with_vat", "C10_kb3_matches_kb2v", "C12_act_not_empty",
           "C13_kb3_cumulative"]


def make_report(rows=(9, 10), *, act_file="act_03.xlsx", skipped=(), statuses=None, previous=True,
                skipped_rows=()):
    findings = []
    codes = ["2-1", "5-2"]
    for code, r in zip(codes, rows):
        src = Source(act_file, "КБ-2в", r)
        for check in ROW_IDS:
            st = (statuses or {}).get((code, check), Status.PASS)
            findings.append(Finding(check, st, code, "100.00", "100.00", "", [src]))
    for check in ACT_IDS:
        st = (statuses or {}).get((None, check), Status.PASS)
        findings.append(Finding(check, st, None, "1", "1", "", [Source(act_file, "КБ-2в", rows[-1] + 1)]))
    inputs = {
        "contract": [Source("contract_boq.xlsx", "Договірна ціна", r) for r in range(7, 21)],
        "previous": ([Source("act_01_2026-09.xlsx", "КБ-2в", r) for r in (9, 10, 11, 14)]
                     + [Source("act_02_2026-10.xlsx", "КБ-2в", r) for r in range(9, 17)]) if previous else [],
        "act": [Source(act_file, "КБ-2в", r) for r in (2, *rows, rows[-1] + 1)]
               + [Source(act_file, "КБ-3", r) for r in range(5, 9)],
    }
    return Report(findings, list(skipped), inputs, list(skipped_rows))


# ---------------------------------------------------------------- рядки
def test_compress_rows():
    assert compress_rows([7, 8, 9, 10]) == "7–10"
    assert compress_rows([18, 9, 10, 11, 12, 13, 14, 15]) == "9–15, 18"
    assert compress_rows([5]) == "5"
    assert compress_rows([3, 3, 4]) == "3–4"
    assert compress_rows([]) == "—"


# ---------------------------------------------------------------- блок доказів (AC-03)
def test_evidence_for_pass_report():
    text = render_evidence(make_report())
    lines = text.splitlines()
    assert lines[0] == "## Блок доказів"
    assert lines[1] == "Перевірено: 2 позиції × 7 перевірок рядка, 6 перевірок підсумків (виконано перевірок: 20)."
    assert lines[2] == "Не перевірено: —"
    assert "- договірні ціни й обсяги — contract_boq.xlsx, аркуш «Договірна ціна», рядки 7–20" in lines
    assert ("- попередні обсяги — act_01_2026-09.xlsx, аркуш «КБ-2в», рядки 9–11, 14; "
            "act_02_2026-10.xlsx, аркуш «КБ-2в», рядки 9–16") in lines
    assert "- перевірюваний акт — act_03.xlsx, аркуш «КБ-2в», рядки 2, 9–11; аркуш «КБ-3», рядки 5–8" in lines
    assert lines[-1] == "Розбіжностей: 0. Вердикт: pass."
    assert not any(line.startswith("Пропущено рядків") for line in lines)


def test_evidence_lists_skips_grouped_by_position_and_reason():
    skipped = [Skipped("C03_price_matches_contract", "5-2", "порожня ціна"),
               Skipped("C04_amount_arithmetic", "5-2", "порожня ціна"),
               Skipped("C02_unit_matches", "7-1", "позиції немає в договорі"),
               Skipped("C13_kb3_cumulative", None, "приклад")]
    statuses = {("5-2", "C11_required_values_present"): Status.UNKNOWN}
    text = render_evidence(make_report(skipped=skipped, statuses=statuses))
    assert ("Не перевірено: 5-2 — C03, C04 (порожня ціна); 7-1 — C02 (позиції немає в договорі); "
            "акт — C13 (приклад).") in text.splitlines()
    assert text.splitlines()[-1] == "Розбіжностей: 1 unknown. Вердикт: needs_review."


def test_evidence_counts_discrepancies_by_status():
    statuses = {("2-1", "C03_price_matches_contract"): Status.FAIL, ("5-2", "C11_required_values_present"):
                Status.UNKNOWN, (None, "C12_act_not_empty"): Status.WARNING, (None, "C10_kb3_matches_kb2v"):
                Status.FAIL}
    assert render_evidence(make_report(statuses=statuses)).splitlines()[-1] == (
        "Розбіжностей: 2 fail, 1 unknown, 1 warning. Вердикт: fail.")


def test_evidence_cites_rows_as_found_for_shifted_layout():
    text = render_evidence(make_report(rows=(12, 13), skipped_rows=[("act_03.xlsx", "КБ-2в", [14, 15])]))
    assert "- перевірюваний акт — act_03.xlsx, аркуш «КБ-2в», рядки 2, 12–14; аркуш «КБ-3», рядки 5–8" in text
    assert "Пропущено рядків без шифру: act_03.xlsx, «КБ-2в», рядки 14–15" in text.splitlines()


def test_evidence_without_previous_acts():
    assert "- попередні обсяги — —" in render_evidence(make_report(previous=False)).splitlines()


def test_render_is_deterministic():
    rep = make_report(skipped=[Skipped("C03_price_matches_contract", "5-2", "порожня ціна")])
    assert render_evidence(rep) == render_evidence(rep)
    assert render_markdown(rep) == render_markdown(rep)


# ---------------------------------------------------------------- Markdown
def test_markdown_ends_with_evidence_block_and_lists_pass_findings():
    rep = make_report()
    md = render_markdown(rep)
    assert md.rstrip("\n").endswith(render_evidence(rep).rstrip("\n"))
    assert md.count("| pass |") == 20
    assert md.index("## Блок доказів") > md.index("C01_position_in_contract")


def test_markdown_escapes_pipe(tmp_path):
    rep = make_report()
    rep.findings[0].message = "a | b"
    assert "a \\| b" in render_markdown(rep)


# ---------------------------------------------------------------- файли
def test_report_paths():
    xlsx, md = report_paths(Path("out"), Path("data/act_03_2026-11.xlsx"))
    assert (xlsx, md) == (Path("out/act_03_2026-11_report.xlsx"), Path("out/act_03_2026-11_report.md"))


def test_write_excel_round_trip(tmp_path):
    rep = make_report()
    rep.findings[0].code = "=SUM(A1)"  # текст, не формула
    path = tmp_path / "nested" / "r.xlsx"
    write_excel(rep, path)
    ws = load_workbook(path)["Перевірки"]
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0] == ("шифр", "перевірка", "статус", "очікувано", "фактично", "джерело")
    assert len(rows) == 1 + len(rep.findings)
    assert rows[1] == ("=SUM(A1)", "C01_position_in_contract", "pass", "100.00", "100.00", "act_03.xlsx / КБ-2в, рядок 9")
    assert ws.cell(2, 1).data_type == "s"
    assert rows[-1][0] is None and rows[-1][1] == "C13_kb3_cumulative"
    assert all(not isinstance(v, float) for r in rows for v in r)


def test_write_excel_is_byte_identical_across_runs(tmp_path):
    rep = make_report()
    write_excel(rep, tmp_path / "a.xlsx")
    write_excel(rep, tmp_path / "b.xlsx")
    assert (tmp_path / "a.xlsx").read_bytes() == (tmp_path / "b.xlsx").read_bytes()


def test_write_markdown(tmp_path):
    rep = make_report()
    path = tmp_path / "x" / "r.md"
    write_markdown(rep, path)
    assert path.read_text(encoding="utf-8") == render_markdown(rep)
