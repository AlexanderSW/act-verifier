"""Юніт-тести перевірок (T7 — рядки, T8 — підсумки й verify). Лише об'єкти в пам'яті, без xlsx."""

from decimal import Decimal

import pytest

from act_verifier.checks import check_rows, previous_completeness
from act_verifier.models import Act, ActRow, ContractPosition, Skipped, Source, Status

D = Decimal
C01, C02, C03, C04, C05, C06, C11 = (
    "C01_position_in_contract", "C02_unit_matches", "C03_price_matches_contract", "C04_amount_arithmetic",
    "C05_within_remaining_volume", "C06_no_duplicate_positions", "C11_required_values_present")
ROW_CHECKS = {C01, C02, C03, C04, C05, C06, C11}


def contract(*items):
    return {code: ContractPosition(code, f"робота {code}", unit, D(qty), D(price),
                                   Source("contract_boq.xlsx", "Договірна ціна", 7 + i))
            for i, (code, unit, qty, price) in enumerate(items)}


CONTRACT = contract(("2-1", "м²", "1200", "485"), ("2-2", "м²", "950", "312.4"), ("5-2", "шт", "12", "9200"))


def row(code, qty, price, amount, unit="м²", r=9, file="act_03.xlsx"):
    dec = lambda v: None if v is None else D(v)
    return ActRow(r, code, f"робота {code}", unit, dec(qty), dec(price), dec(amount), Source(file, "КБ-2в", r))


def act(rows, number=3, file="act_03.xlsx", total=None):
    return Act(number, "листопад 2026", rows, None, None, None if total is None else D(total), None, None, file)


def prev(number, rows, file=None):
    file = file or f"act_0{number}.xlsx"
    for r in rows:
        r.source = Source(file, "КБ-2в", r.row_no)
    return act(rows, number=number, file=file, total="0")


PREVIOUS = [prev(1, [row("2-1", "410.5", "485", "199092.5", r=9)]),
            prev(2, [row("2-1", "455", "485", "220675", r=9), row("2-2", "390", "312.4", "121836", r=10)])]


def by(findings, code, check):
    hits = [f for f in findings if f.code == code and f.check == check]
    assert len(hits) == 1, (code, check, hits)
    return hits[0]


def run(rows, previous=PREVIOUS, contract_=CONTRACT, number=3):
    a = act(rows, number=number)
    return check_rows(a, contract_, previous, previous_completeness(a, previous))


# ---------------------------------------------------------------- happy path
def test_consistent_row_passes_every_check():
    findings, skipped = run([row("2-1", "300", "485", "145500")])
    assert {f.check for f in findings} == ROW_CHECKS
    assert all(f.status is Status.PASS for f in findings)
    assert skipped == []


# ---------------------------------------------------------------- C01–C04, C06
def test_c01_fail_skips_c02_c03_c05():
    findings, skipped = run([row("7-1", "2", "12500", "25000", unit="шт")])
    assert by(findings, "7-1", C01).status is Status.FAIL
    assert {f.check for f in findings} == {C01, C04, C06, C11}
    assert {(s.check, s.code) for s in skipped} == {(C02, "7-1"), (C03, "7-1"), (C05, "7-1")}


def test_c02_unit_compared_after_strip():
    findings, _ = run([row("2-2", "310", "312.4", "96844", unit=" м² ")])
    assert by(findings, "2-2", C02).status is Status.PASS
    f = by(run([row("2-2", "310", "312.4", "96844", unit="м")])[0], "2-2", C02)
    assert (f.status, f.expected, f.actual) == (Status.FAIL, "м²", "м")


def test_c03_price_exact():
    f = by(run([row("5-2", "6", "9200.00", "55200")])[0], "5-2", C03)
    assert f.status is Status.PASS
    f = by(run([row("5-2", "6", "9200.01", "55200.06")])[0], "5-2", C03)
    assert (f.status, f.expected, f.actual) == (Status.FAIL, "9200", "9200.01")


@pytest.mark.parametrize("amount,status", [("145500.01", Status.PASS), ("145499.99", Status.PASS),
                                            ("145500.02", Status.FAIL), ("147365", Status.FAIL)])
def test_c04_tolerance(amount, status):
    f = by(run([row("2-1", "300", "485", amount)])[0], "2-1", C04)
    assert f.status is status
    assert f.expected == "145500.00" and f.actual == amount


def test_c04_rounds_half_up_before_comparing():
    f = by(run([row("2-2", "0.5", "312.45", "156.23")])[0], "2-2", C04)  # 156.225 -> 156.23
    assert f.status is Status.PASS and f.expected == "156.23"


def test_c06_duplicate_code_fails_once():
    findings, _ = run([row("2-1", "10", "485", "4850", r=9), row("2-1", "4", "485", "1940", r=10)])
    c06 = [f for f in findings if f.check == C06]
    assert [(f.code, f.status) for f in c06] == [("2-1", Status.FAIL)]


# ---------------------------------------------------------------- C11 + правила пропуску (AC-04, AC-05)
def test_empty_price_c11_unknown_c03_c04_skipped():
    findings, skipped = run([row("5-2", "6", None, "55200")])
    assert by(findings, "5-2", C11).status is Status.UNKNOWN
    assert not [f for f in findings if f.check in {C03, C04}]
    assert set(skipped) == {Skipped(C03, "5-2", "порожня ціна"), Skipped(C04, "5-2", "порожня ціна")}
    assert by(findings, "5-2", C05).status is Status.PASS  # кількість є — залишок перевіряється


def test_empty_quantity_skips_c04_c05():
    findings, skipped = run([row("2-1", None, "485", "145500")])
    assert by(findings, "2-1", C11).status is Status.UNKNOWN
    assert by(findings, "2-1", C03).status is Status.PASS
    assert set(skipped) == {Skipped(C04, "2-1", "порожня кількість"), Skipped(C05, "2-1", "порожня кількість")}


def test_empty_amount_skips_c04_only():
    findings, skipped = run([row("2-1", "300", "485", None)])
    assert by(findings, "2-1", C11).status is Status.UNKNOWN
    assert set(skipped) == {Skipped(C04, "2-1", "порожня вартість")}
    assert by(findings, "2-1", C05).status is Status.PASS


def test_c01_fail_with_empty_price():
    findings, skipped = run([row("7-1", "2", None, "25000", unit="шт")])
    assert by(findings, "7-1", C11).status is Status.UNKNOWN
    assert {s.check for s in skipped} == {C02, C03, C04, C05}


def test_no_check_passes_on_none_operand():
    findings, _ = run([row("2-1", None, None, None)])
    assert {f.check for f in findings if f.status is Status.PASS} <= {C01, C02, C06}


# ---------------------------------------------------------------- C05 (AC-10)
def test_c05_volume_overrun_numbers_and_sources():
    findings, _ = run([row("2-1", "350", "485", "169750")])
    f = by(findings, "2-1", C05)
    assert (f.status, f.expected, f.actual) == (Status.FAIL, "334.5", "350")
    assert CONTRACT["2-1"].source in f.sources
    assert {s.file for s in f.sources} == {"act_03.xlsx", "contract_boq.xlsx", "act_01.xlsx", "act_02.xlsx"}


def test_c05_at_remaining_volume_passes():
    assert by(run([row("2-1", "334.5", "485", "162232.5")])[0], "2-1", C05).status is Status.PASS


def test_c05_previous_act_without_the_code_is_still_cited():
    f = by(run([row("2-2", "560", "312.4", "174944")])[0], "2-2", C05)
    assert f.status is Status.PASS and f.expected == "560"
    assert {s.file for s in f.sources} == {"act_03.xlsx", "contract_boq.xlsx", "act_01.xlsx", "act_02.xlsx"}


def test_c05_repeated_code_in_previous_act_is_summed():
    previous = [prev(1, [row("2-1", "400", "485", "194000", r=9), row("2-1", "410.5", "485", "199092.5", r=10)]),
                prev(2, [row("2-1", "55", "485", "26675", r=9)])]
    f = by(run([row("2-1", "335", "485", "162475")], previous=previous)[0], "2-1", C05)
    assert (f.status, f.expected) == (Status.FAIL, "334.5")


def test_c05_empty_quantity_in_previous_act_is_unknown():
    previous = [prev(1, [row("2-1", None, "485", "199092.5", r=9)]), PREVIOUS[1]]
    findings, _ = run([row("2-1", "10", "485", "4850"), row("2-2", "10", "312.4", "3124", r=10)], previous=previous)
    assert by(findings, "2-1", C05).status is Status.UNKNOWN
    assert by(findings, "2-2", C05).status is Status.PASS


def test_c05_first_act_has_no_previous():
    f = by(run([row("2-1", "1200", "485", "582000")], previous=[], number=1)[0], "2-1", C05)
    assert (f.status, f.expected) == (Status.PASS, "1200")


# ---------------------------------------------------------------- повнота попередніх актів (AC-11)
@pytest.mark.parametrize("number,previous,reason", [
    (3, PREVIOUS, None),
    (1, [], None),
    (3, [PREVIOUS[0]], "подано попередніх актів: 1 з 2"),
    (3, [], "подано попередніх актів: 0 з 2"),
    (None, PREVIOUS, "номер акта не прочитано"),
    (3, [PREVIOUS[0], prev(None, [], file="x.xlsx")], "номер попереднього акта не прочитано — x.xlsx"),
    (3, [PREVIOUS[0], prev(1, [], file="dup.xlsx")], "повторюється номер попереднього акта 1"),
    (3, [PREVIOUS[0], PREVIOUS[1], prev(3, [], file="self.xlsx")], "номер попереднього акта 3 поза 1…2"),
    (3, [PREVIOUS[0], prev(5, [], file="five.xlsx")], "номер попереднього акта 5 поза 1…2"),
])
def test_previous_completeness(number, previous, reason):
    assert previous_completeness(act([], number=number), previous) == reason


def test_incomplete_previous_makes_c05_unknown_for_every_position_other_checks_run():
    rows = [row("2-1", "300", "485", "145500", r=9), row("2-2", "310", "312.4", "96844", r=10)]
    findings, skipped = run(rows, previous=[PREVIOUS[0]])
    for code in ("2-1", "2-2"):
        f = by(findings, code, C05)
        assert (f.status, f.message) == (Status.UNKNOWN, "подано попередніх актів: 1 з 2")
        assert all(by(findings, code, c).status is Status.PASS for c in (C01, C02, C03, C04, C06, C11))
    # причина потрапляє і в «Не перевірено» блоку доказів (AC-03, AC-11; review finding 1)
    assert skipped == [Skipped(C05, "2-1", "подано попередніх актів: 1 з 2"),
                       Skipped(C05, "2-2", "подано попередніх актів: 1 з 2")]


# ---------------------------------------------------------------- порядок і Decimal
def test_findings_in_row_order_then_check_id():
    findings, _ = run([row("2-2", "310", "312.4", "96844", r=9), row("2-1", "300", "485", "145500", r=10)])
    assert [f.code for f in findings] == ["2-2"] * 7 + ["2-1"] * 7
    assert [f.check for f in findings[:7]] == sorted(ROW_CHECKS)
    assert all(f.sources[0] == Source("act_03.xlsx", "КБ-2в", 9) for f in findings[:7])


# ================================================================ T8: підсумки, КБ-3, verify()
from act_verifier.checks import check_act, verify  # noqa: E402

C07, C08, C09, C10, C12, C13 = ("C07_subtotal", "C08_vat", "C09_total_with_vat", "C10_kb3_matches_kb2v",
                                "C12_act_not_empty", "C13_kb3_cumulative")
ACT_CHECKS = {C07, C08, C09, C10, C12, C13}
PREV_TOTALS = ["503093.4", "772309.2"]  # «Всього з ПДВ» попередніх актів, як надруковано


def prev_with_totals(totals=PREV_TOTALS):
    out = []
    for i, t in enumerate(totals, 1):
        p = prev(i, [row("2-1", "1", "485", "485", r=9)], file=f"act_0{i}.xlsx")
        p.total = None if t is None else D(t)
        p.sources = {"total": Source(p.file, "КБ-2в", 12)}
        out.append(p)
    return out


def full_act(rows=None, subtotal="145500", vat="29100", total="174600", kb3p="174600",
             kb3c=None, number=3):
    rows = rows if rows is not None else [row("2-1", "300", "485", "145500")]
    if kb3c is None:
        kb3c = str(sum((D(t) for t in PREV_TOTALS), D(0)) + D(total))
    dec = lambda v: None if v is None else D(v)
    a = Act(number, "листопад 2026", rows, dec(subtotal), dec(vat), dec(total), dec(kb3p), dec(kb3c),
            "act_03.xlsx")
    a.sources = {k: Source("act_03.xlsx", "КБ-3" if k.startswith("kb3") else "КБ-2в", r)
                 for k, r in [("subtotal", 20), ("vat", 21), ("total", 22),
                              ("kb3_period_total", 7), ("kb3_cumulative_total", 8)]}
    return a


def act_run(a, previous=None):
    previous = prev_with_totals() if previous is None else previous
    return check_act(a, previous, previous_completeness(a, previous))


def act_by(findings, check):
    return by(findings, None, check)


def test_consistent_act_passes_every_act_check():
    findings, skipped = act_run(full_act())
    assert {f.check for f in findings} == ACT_CHECKS
    assert all(f.status is Status.PASS for f in findings) and skipped == []
    assert all(f.code is None for f in findings)


@pytest.mark.parametrize("subtotal,status", [("145500.01", Status.PASS), ("145500.02", Status.FAIL),
                                              ("135500", Status.FAIL)])
def test_c07_subtotal_tolerance(subtotal, status):
    f = act_by(act_run(full_act(subtotal=subtotal))[0], C07)
    assert (f.status, f.expected, f.actual) == (status, "145500", subtotal)


def test_c07_unknown_on_empty_amount_names_position():
    rows = [row("2-1", "300", "485", "145500", r=9), row("2-2", "10", "312.4", None, r=10)]
    f = act_by(act_run(full_act(rows=rows))[0], C07)
    assert f.status is Status.UNKNOWN and "2-2" in f.message


def test_c07_unknown_on_empty_printed_subtotal():
    findings, _ = act_run(full_act(subtotal=None))
    for check in (C07, C08, C09):
        f = act_by(findings, check)
        assert f.status is Status.UNKNOWN and "Разом без ПДВ" in f.message, check


@pytest.mark.parametrize("vat,status", [("29100.01", Status.PASS), ("29100.02", Status.FAIL), ("10185", Status.FAIL)])
def test_c08_vat_on_printed_subtotal(vat, status):
    f = act_by(act_run(full_act(vat=vat, total=str(D("145500") + D(vat)), kb3p=str(D("145500") + D(vat))))[0], C08)
    assert (f.status, f.expected, f.actual) == (status, "29100.00", vat)


def test_c08_vat_rounds_half_up():
    f = act_by(act_run(full_act(subtotal="0.25", vat="0.05", total="0.30", kb3p="0.30",
                                rows=[row("2-1", "1", "0.25", "0.25")]))[0], C08)
    assert f.status is Status.PASS and f.expected == "0.05"


def test_empty_vat_makes_c08_c09_unknown():
    findings, _ = act_run(full_act(vat=None))
    assert act_by(findings, C08).status is Status.UNKNOWN and act_by(findings, C09).status is Status.UNKNOWN
    assert act_by(findings, C07).status is Status.PASS and act_by(findings, C10).status is Status.PASS


def test_c09_total():
    f = act_by(act_run(full_act(total="174600.02", kb3p="174600.02"))[0], C09)
    assert (f.status, f.expected, f.actual) == (Status.FAIL, "174600", "174600.02")


def test_empty_total_makes_c09_c10_c13_unknown():
    findings, _ = act_run(full_act(total=None, kb3c="1450002.6"))
    for check in (C09, C10, C13):
        f = act_by(findings, check)
        assert f.status is Status.UNKNOWN and "Всього з ПДВ" in f.message, check


def test_kb3_mismatch_fails_only_c10_c13_passes():
    findings, _ = act_run(full_act(kb3p="177000"))
    assert {f.check for f in findings if f.status is not Status.PASS} == {C10}
    f = act_by(findings, C10)
    assert (f.expected, f.actual) == ("174600", "177000")


def test_empty_kb3_period_total_makes_c10_unknown():
    assert act_by(act_run(full_act(kb3p=None))[0], C10).status is Status.UNKNOWN


def test_c12_empty_act_warns():
    findings, _ = act_run(full_act(rows=[], subtotal="0", vat="0", total="0", kb3p="0"))
    assert act_by(findings, C12).status is Status.WARNING
    assert act_by(findings, C07).status is Status.PASS


def test_c13_cumulative_tolerance():
    good = str(sum((D(t) for t in PREV_TOTALS), D(0)) + D("174600"))
    assert act_by(act_run(full_act(kb3c=good))[0], C13).status is Status.PASS
    f = act_by(act_run(full_act(kb3c=str(D(good) + D("0.02"))))[0], C13)
    assert (f.status, f.expected) == (Status.FAIL, good)


def test_c13_unknown_on_incomplete_previous():
    findings, skipped = act_run(full_act(), previous=prev_with_totals()[:1])
    f = act_by(findings, C13)
    assert (f.status, f.message) == (Status.UNKNOWN, "подано попередніх актів: 1 з 2")
    assert skipped == [Skipped(C13, None, "подано попередніх актів: 1 з 2")]


def test_c13_unknown_on_empty_previous_total_names_file():
    f = act_by(act_run(full_act(), previous=prev_with_totals(["503093.4", None]))[0], C13)
    assert f.status is Status.UNKNOWN and "act_02.xlsx" in f.message


def test_c13_unknown_on_empty_cumulative():
    act_ = full_act()
    act_.kb3_cumulative_total = None
    assert act_by(act_run(act_)[0], C13).status is Status.UNKNOWN


# ---------------------------------------------------------------- verify()
def test_verify_lists_every_check_and_puts_act_level_last():
    rows = [row("2-1", "300", "485", "145500", r=9), row("2-2", "310", "312.4", "96844", r=10)]
    a = full_act(rows=rows, subtotal="242344", vat="48468.8", total="290812.8", kb3p="290812.8")
    rep = verify(a, CONTRACT, prev_with_totals())
    assert rep.verdict == "pass"
    assert [f.code for f in rep.findings] == ["2-1"] * 7 + ["2-2"] * 7 + [None] * 6
    assert [f.check for f in rep.findings[-6:]] == sorted(ACT_CHECKS)
    assert rep.inputs["contract"] == [p.source for p in CONTRACT.values()]
    assert {s.file for s in rep.inputs["previous"]} == {"act_01.xlsx", "act_02.xlsx"}
    assert Source("act_03.xlsx", "КБ-2в", 9) in rep.inputs["act"]
    assert Source("act_03.xlsx", "КБ-3", 8) in rep.inputs["act"]


def test_verify_empty_act_only_c12_warning():
    rep = verify(full_act(rows=[], subtotal="0", vat="0", total="0", kb3p="0"), CONTRACT, prev_with_totals())
    assert [(f.check, f.status) for f in rep.findings if f.status is not Status.PASS] == [(C12, Status.WARNING)]
    assert rep.verdict == "needs_review"


def test_verify_combo_does_not_stop_at_first_error():
    # попередні акти prev_with_totals() мають по 1 од. 2-1 -> залишок 1198
    rows = [row("2-1", "1199", "485", "581515", r=9), row("5-2", "6", "9700", "58200", unit="шт", r=10)]
    a = full_act(rows=rows, subtotal="639715", vat="127943", total="767658", kb3p="770058")
    rep = verify(a, CONTRACT, prev_with_totals())
    # кожна з трьох — з очікуваним і фактичним значенням (AC-02)
    assert {(f.code, f.check, f.expected, f.actual) for f in rep.findings if f.status is Status.FAIL} == {
        ("2-1", C05, "1198", "1199"), ("5-2", C03, "9200", "9700"), (None, C10, "767658", "770058")}
    assert rep.verdict == "fail"


def test_verify_carries_skips_and_skipped_rows():
    a = full_act(rows=[row("5-2", "6", None, "55200", unit="шт")], subtotal="55200", vat="11040",
                 total="66240", kb3p="66240")
    a.skipped_rows = [20, 21]
    rep = verify(a, CONTRACT, prev_with_totals())
    assert set(rep.skipped) == {Skipped(C03, "5-2", "порожня ціна"), Skipped(C04, "5-2", "порожня ціна")}
    assert ("act_03.xlsx", "КБ-2в", [20, 21]) in rep.skipped_rows
    assert rep.verdict == "needs_review"


def test_verify_is_deterministic():
    a = full_act()
    assert verify(a, CONTRACT, prev_with_totals()) == verify(a, CONTRACT, prev_with_totals())
