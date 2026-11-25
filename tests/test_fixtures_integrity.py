"""Тести самих фікстур: еталон теж треба перевіряти.

Проходять одразу, ще до реалізації верифікатора. Рахують незалежно від src/,
напряму через openpyxl, щоб помилка в генераторі не сховалась за помилкою в коді.
"""

from decimal import Decimal

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


def d(v):
    return Decimal(str(v)).quantize(CENT)


@pytest.mark.parametrize("sdir", scenario_dirs(), ids=lambda p: p.name)
def test_expected_json_schema(sdir):
    exp = load_expected(sdir)
    assert exp["scenario"] == sdir.name
    assert exp["expected_verdict"] in {"pass", "fail", "needs_review"}
    for f in exp["expected_findings"]:
        assert f["check"] in KNOWN_CHECKS
        assert f["status"] in {"fail", "unknown", "warning"}
    for path in [exp["inputs"]["contract"], *exp["inputs"]["previous_acts"], exp["inputs"]["act"]]:
        assert (ROOT / path).exists(), path


def read_act_totals(path):
    ws = load_workbook(path, data_only=True)["КБ-2в"]
    rows, totals = [], {}
    for r in ws.iter_rows(min_row=9, values_only=True):
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
    for r in ws.iter_rows(min_row=7, values_only=True):
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
