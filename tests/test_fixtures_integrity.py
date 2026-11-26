"""Тести самих фікстур: еталон теж треба перевіряти.

Проходять одразу, ще до реалізації верифікатора. Рахують незалежно від src/,
напряму через openpyxl, щоб помилка в генераторі не сховалась за помилкою в коді.
"""

from decimal import Decimal

import re

import pytest
from openpyxl import load_workbook

from conftest import ROOT, load_expected, scenario_dirs

KNOWN_CHECKS = {
    "C01_position_in_contract", "C02_unit_matches", "C03_price_matches_contract",
    "C04_amount_arithmetic", "C05_within_remaining_volume", "C06_no_duplicate_positions",
    "C07_subtotal", "C08_vat", "C09_total_with_vat", "C10_kb3_matches_kb2v",
    "C11_required_values_present", "C12_act_not_empty", "C13_kb3_cumulative",
}
CENT = Decimal("0.01")
LAYOUT_KEYS = {"header_row", "first_data_row", "subtotal_row", "vat_row", "total_row", "skipped_rows"}
LAYOUT_SCENARIOS = {"shifted_header", "totals_gap", "missing_label", "ambiguous_label"}
# README-розкладка (fallback, коли в expected.json немає layout)
README_ACT_HEADER_ROW = 8
README_CONTRACT_FIRST_ROW = 7


def d(v):
    return Decimal(str(v)).quantize(CENT)


@pytest.mark.parametrize("sdir", scenario_dirs(), ids=lambda p: p.name)
def test_expected_json_schema(sdir):
    exp = load_expected(sdir)
    assert exp["scenario"] == sdir.name
    # рівно одне з двох: вердикт зі знахідками або очікувана помилка вхідних даних
    if "expected_error" in exp:
        assert "expected_verdict" not in exp and "expected_findings" not in exp
        err = exp["expected_error"]
        assert set(err) == {"kind", "label"}
        assert err["kind"] in {"missing_label", "ambiguous_label"}
        assert isinstance(err["label"], str) and err["label"]
    else:
        assert exp["expected_verdict"] in {"pass", "fail", "needs_review"}
        for f in exp["expected_findings"]:
            assert f["check"] in KNOWN_CHECKS
            assert f["status"] in {"fail", "unknown", "warning"}
    for role, rows in exp.get("layout", {}).items():
        assert role in {"contract", "act"}, role
        assert set(rows) <= LAYOUT_KEYS, rows
    for path in [exp["inputs"]["contract"], *exp["inputs"]["previous_acts"], exp["inputs"]["act"]]:
        assert (ROOT / path).exists(), path


def read_act_totals(path, layout=None):
    """Рядки й підсумки КБ-2в. Рядки — з layout генератора, README-рядки як fallback (ADR-0004)."""
    ws = load_workbook(path, data_only=True)["КБ-2в"]
    header = (layout or {}).get("header_row", README_ACT_HEADER_ROW)
    rows, totals = [], {}
    for r in ws.iter_rows(min_row=header + 1, values_only=True):
        if r[1]:
            rows.append(r)
        elif r[2] in {"Разом без ПДВ", "ПДВ 20%", "Всього з ПДВ"}:
            totals[r[2]] = d(r[6])
    return rows, totals


def test_ok_many_is_internally_consistent():
    rows, totals = read_act_totals(ROOT / "tests/fixtures/ok_many/act_03.xlsx")
    assert len(rows) == 11
    for r in rows:
        assert d(Decimal(str(r[4])) * Decimal(str(r[5]))) == d(r[6]), r[1]
    assert sum(d(r[6]) for r in rows) == totals["Разом без ПДВ"]
    assert d(totals["Разом без ПДВ"] * Decimal("0.2")) == totals["ПДВ 20%"]


def test_ok_many_respects_remaining_volumes():
    contract = {}
    ws = load_workbook(ROOT / "data/synthetic/contract_boq.xlsx")["Договірна ціна"]
    for r in ws.iter_rows(min_row=README_CONTRACT_FIRST_ROW, values_only=True):
        if r[1]:
            contract[r[1]] = Decimal(str(r[4]))
    used = {}
    for name in ["act_01_2026-09.xlsx", "act_02_2026-10.xlsx"]:
        rows, _ = read_act_totals(ROOT / "data/synthetic" / name)
        for r in rows:
            used[r[1]] = used.get(r[1], Decimal(0)) + Decimal(str(r[4]))
    rows, _ = read_act_totals(ROOT / "tests/fixtures/ok_many/act_03.xlsx")
    for r in rows:
        assert Decimal(str(r[4])) <= contract[r[1]] - used.get(r[1], 0), r[1]


def _norm(v):
    return re.sub(r"\s+", " ", str(v or "")).strip().casefold()


def _by_name():
    return {p.name: p for p in scenario_dirs()}


def test_layout_scenarios_present():
    assert LAYOUT_SCENARIOS <= set(_by_name())


def _layout_dirs():
    return [p for p in scenario_dirs() if "layout" in load_expected(p)]


@pytest.mark.parametrize("sdir", _layout_dirs(), ids=lambda p: p.name)
def test_layout_fixture_matches_its_layout_map(sdir):
    """Рядки з layout справді містять заголовок, позиції й підсумки, а арифметика узгоджена."""
    exp = load_expected(sdir)
    lay = exp["layout"]["act"]
    ws = load_workbook(ROOT / exp["inputs"]["act"], data_only=True)["КБ-2в"]
    cell = lambda r, c: ws.cell(r, c).value
    assert _norm(cell(lay["header_row"], 2)).startswith("шифр")
    assert _norm(cell(lay["subtotal_row"], 3)).startswith("разом без пдв")
    assert _norm(cell(lay["vat_row"], 3)).startswith("пдв")
    assert _norm(cell(lay["total_row"], 3)).startswith("всього з пдв")
    data_rows = [r for r in range(lay["first_data_row"], lay["subtotal_row"]) if cell(r, 2)]
    assert data_rows and data_rows[0] == lay["first_data_row"]
    skipped = [r for r in range(lay["first_data_row"], lay["subtotal_row"]) if not cell(r, 2)]
    assert skipped == lay.get("skipped_rows", [])
    amounts = [d(cell(r, 7)) for r in data_rows]
    for r in data_rows:
        assert d(Decimal(str(cell(r, 5))) * Decimal(str(cell(r, 6)))) == d(cell(r, 7)), r
    assert sum(amounts) == d(cell(lay["subtotal_row"], 7))
    assert d(d(cell(lay["subtotal_row"], 7)) * Decimal("0.2")) == d(cell(lay["vat_row"], 7))
    rows, totals = read_act_totals(ROOT / exp["inputs"]["act"], lay)
    assert len(rows) == len(data_rows)
    assert totals["Разом без ПДВ"] == d(cell(lay["subtotal_row"], 7))


def test_shifted_header_is_not_at_readme_row():
    lay = load_expected(_by_name()["shifted_header"])["layout"]["act"]
    assert lay["header_row"] != README_ACT_HEADER_ROW


def test_totals_gap_has_rows_without_code_before_subtotal():
    lay = load_expected(_by_name()["totals_gap"])["layout"]["act"]
    assert lay.get("skipped_rows")


def _kb2v_labels(sdir):
    exp = load_expected(sdir)
    ws = load_workbook(ROOT / exp["inputs"]["act"], data_only=True)["КБ-2в"]
    header = next(r for r in range(1, ws.max_row + 1) if _norm(ws.cell(r, 2).value).startswith("шифр"))
    return [(r, _norm(ws.cell(r, 3).value)) for r in range(header + 1, ws.max_row + 1)]


def test_missing_label_fixture_lacks_the_label():
    sdir = _by_name()["missing_label"]
    label = load_expected(sdir)["expected_error"]["label"]
    assert not [r for r, t in _kb2v_labels(sdir) if t.startswith(_norm(label))]


def test_ambiguous_label_fixture_has_two_rows():
    sdir = _by_name()["ambiguous_label"]
    label = load_expected(sdir)["expected_error"]["label"]
    assert len([r for r, t in _kb2v_labels(sdir) if t.startswith(_norm(label))]) >= 2
