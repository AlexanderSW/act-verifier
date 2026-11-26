"""Юніт-тести доменних типів (T1): InputError, Skipped, походження значень, вердикт."""

from decimal import Decimal

import pytest

from act_verifier.models import (
    Act,
    Finding,
    InputError,
    Report,
    Skipped,
    Source,
    Status,
)


def test_input_error_carries_fields():
    e = InputError("ambiguous_label", label="ПДВ", file="a.xlsx", sheet="КБ-2в", rows=[20, 23])
    assert (e.kind, e.label, e.file, e.sheet, e.rows) == ("ambiguous_label", "ПДВ", "a.xlsx", "КБ-2в", [20, 23])
    assert isinstance(e, Exception)


def test_input_error_rows_default_empty():
    e = InputError("missing_label", label="Ціна", file="c.xlsx", sheet="Договірна ціна")
    assert e.rows == []


def test_input_error_kinds_are_the_five():
    assert InputError.KINDS == {
        "missing_label", "ambiguous_label", "unreadable_file", "invocation", "overwrite_refused",
    }


def test_input_error_refuses_unknown_kind():
    with pytest.raises(ValueError):
        InputError("missing_lable", label="x")


def test_skipped_is_hashable_and_comparable():
    a = Skipped("C03_price_matches_contract", "5-2", "порожня ціна")
    b = Skipped("C03_price_matches_contract", "5-2", "порожня ціна")
    assert a == b
    assert len({a, b}) == 1
    assert Skipped("C13_kb3_cumulative", None, "x").code is None


def test_act_has_provenance_fields_with_defaults():
    act = Act(3, "листопад 2026", [], Decimal("0"), Decimal("0"), Decimal("0"),
              Decimal("0"), Decimal("0"), "act.xlsx")
    assert act.sources == {}
    assert act.skipped_rows == []
    assert act.header_row is None
    act2 = Act(3, None, [], None, None, None, None, None, "a.xlsx",
               sources={"total": Source("a.xlsx", "КБ-2в", 24)}, header_row=11, skipped_rows=[22])
    assert act2.sources["total"].row == 24 and act2.header_row == 11 and act2.skipped_rows == [22]


def _report(*statuses):
    return Report(findings=[Finding("C01_position_in_contract", s, "2-1") for s in statuses], skipped=[])


@pytest.mark.parametrize("statuses,verdict", [
    ((Status.PASS,), "pass"),
    ((Status.PASS, Status.UNKNOWN), "needs_review"),
    ((Status.WARNING,), "needs_review"),
    ((Status.FAIL, Status.UNKNOWN), "fail"),
])
def test_verdict(statuses, verdict):
    assert _report(*statuses).verdict == verdict


def test_report_skipped_and_inputs():
    r = Report(findings=[], skipped=[Skipped("C04_amount_arithmetic", "5-2", "порожня ціна")],
               inputs={"contract": [Source("c.xlsx", "Договірна ціна", 7)]})
    assert r.skipped[0].reason == "порожня ціна"
    assert r.inputs["contract"][0].row == 7
    assert Report(findings=[], skipped=[]).inputs == {}
    assert Report(findings=[], skipped=[]).skipped_rows == []
