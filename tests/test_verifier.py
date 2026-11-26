"""Еталонні сценарії: верифікатор має дати рівно ті знахідки, що в expected.json.

Сценарій з expected_error має впасти саме з цією помилкою вхідних даних (вид + підпис),
а не дати вердикт. Сценарії з layout додатково перевіряють, що блок доказів цитує
рядки, де дані справді знайдено.
"""

import pytest

from act_verifier.checks import verify
from act_verifier.loaders import load_act, load_contract
from act_verifier.models import InputError, Status
from act_verifier.report import compress_rows, render_evidence
from conftest import ROOT, load_expected, scenario_dirs

FX = ROOT / "tests" / "fixtures"
ROW_CHECKS = {"C01_position_in_contract", "C02_unit_matches", "C03_price_matches_contract",
              "C04_amount_arithmetic", "C05_within_remaining_volume", "C06_no_duplicate_positions",
              "C11_required_values_present"}
ACT_CHECKS = {"C07_subtotal", "C08_vat", "C09_total_with_vat", "C10_kb3_matches_kb2v", "C12_act_not_empty",
              "C13_kb3_cumulative"}


def non_pass(report):
    return {(f.code, f.check, f.status.value) for f in report.findings if f.status.value != "pass"}


def load_inputs(exp):
    contract = load_contract(ROOT / exp["inputs"]["contract"])
    previous = [load_act(ROOT / p, previous=True) for p in exp["inputs"]["previous_acts"]]
    act = load_act(ROOT / exp["inputs"]["act"])
    return act, contract, previous


def run_scenario(name):
    exp = load_expected(FX / name)
    act, contract, previous = load_inputs(exp)
    return verify(act, contract, previous)


@pytest.mark.parametrize("sdir", scenario_dirs(), ids=lambda p: p.name)
def test_scenario(sdir):
    exp = load_expected(sdir)
    if "expected_error" in exp:
        # сценарій помилки вхідних даних: очікуємо саме цей вид і підпис, а не вердикт
        with pytest.raises(InputError) as e:
            load_inputs(exp)
        assert (e.value.kind, e.value.label) == (exp["expected_error"]["kind"], exp["expected_error"]["label"])
        return

    report = verify(*load_inputs(exp))

    expected = {(f["code"], f["check"], f["status"]) for f in exp["expected_findings"]}
    assert non_pass(report) == expected
    assert report.verdict == exp["expected_verdict"]
    assert render_evidence(report).startswith("## Блок доказів")

    if "layout" in exp:  # AC-09: рядки як знайдено, а не README-рядки
        lay = exp["layout"]["act"]
        skipped = lay.get("skipped_rows", [])
        data = [r for r in range(lay["first_data_row"], lay["subtotal_row"]) if r not in skipped]
        act_rows = [2, *data, lay["subtotal_row"], lay["vat_row"], lay["total_row"]]
        evidence = render_evidence(report).splitlines()
        assert (f"- перевірюваний акт — act_03.xlsx, аркуш «КБ-2в», рядки {compress_rows(act_rows)}; "
                "аркуш «КБ-3», рядки 5–8") in evidence
        if skipped:
            assert f"Пропущено рядків без шифру: act_03.xlsx, «КБ-2в», рядки {compress_rows(skipped)}" in evidence
        else:
            assert not any(line.startswith("Пропущено рядків") for line in evidence)


def test_shifted_layouts_give_the_same_findings_as_readme_layout():
    ref = run_scenario("ok_many")
    key = lambda rep: [(f.code, f.check, f.status, f.expected, f.actual) for f in rep.findings]
    for name in ("shifted_header", "totals_gap"):
        assert key(run_scenario(name)) == key(ref), name


def test_ok_many_lists_every_check_of_every_position_and_the_act():
    report = run_scenario("ok_many")
    rows = [f for f in report.findings if f.code is not None]
    assert len({f.code for f in rows}) == 11
    assert {(f.code, f.check) for f in rows} == {(c, k) for c in {f.code for f in rows} for k in ROW_CHECKS}
    assert {f.check for f in report.findings if f.code is None} == ACT_CHECKS
    assert all(f.status is Status.PASS for f in report.findings)
    assert report.skipped == []


def test_missing_price_skips_c03_c04_with_reason():
    report = run_scenario("missing_price")
    assert {(s.check, s.code, s.reason) for s in report.skipped} == {
        ("C03_price_matches_contract", "5-2", "порожня ціна"), ("C04_amount_arithmetic", "5-2", "порожня ціна")}
    assert "Не перевірено: 5-2 — C03, C04 (порожня ціна)." in render_evidence(report).splitlines()


def test_volume_overrun_c05_numbers_and_sources():
    report = run_scenario("volume_overrun")
    f = next(f for f in report.findings if f.code == "2-1" and f.check == "C05_within_remaining_volume")
    assert (f.status, f.expected, f.actual) == (Status.FAIL, "334.5", "350")
    files = {s.file for s in f.sources}
    assert {"contract_boq.xlsx", "act_01_2026-09.xlsx", "act_02_2026-10.xlsx"} <= files


def test_incomplete_previous_reason():
    report = run_scenario("incomplete_previous")
    msgs = {f.message for f in report.findings if f.status is Status.UNKNOWN}
    assert msgs == {"подано попередніх актів: 1 з 2"}


def test_empty_amount_c07_names_the_position():
    report = run_scenario("empty_amount")
    f = next(f for f in report.findings if f.check == "C07_subtotal")
    assert f.status is Status.UNKNOWN and "3-3" in f.message
