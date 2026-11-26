"""Тести читання xlsx (T5, T6): реальні файли генератора на диску, лише читання."""

from decimal import Decimal

import pytest
from openpyxl import Workbook

from act_verifier.loaders import _dec, _text, load_contract
from act_verifier.models import InputError, Source
from conftest import ROOT

CONTRACT = ROOT / "data/synthetic/contract_boq.xlsx"


# ---------------------------------------------------------------- спільні читачі клітинок
@pytest.mark.parametrize("raw,expected", [
    (None, None), ("", None), ("   ", None), (300, Decimal("300")), (410.5, Decimal("410.5")),
    (0.1, Decimal("0.1")), ("1 250,50", None), (True, None),
])
def test_dec(raw, expected):
    v = _dec(raw)
    assert v == expected
    assert v is None or type(v) is Decimal


def test_text():
    assert _text(None) == "" and _text("  м² ") == "м²" and _text(5) == "5"


# ---------------------------------------------------------------- load_contract
def test_load_contract_reads_all_positions_with_sources():
    contract = load_contract(CONTRACT)
    assert len(contract) == 14
    assert list(contract)[0] == "2-1" and list(contract)[-1] == "6-1"
    p = contract["2-1"]
    assert (p.name, p.unit, p.qty, p.price) == (
        "Монтаж повітроводів з оцинкованої сталі, δ=0,7 мм", "м²", Decimal("1200"), Decimal("485"))
    assert p.source == Source("contract_boq.xlsx", "Договірна ціна", 7)
    assert [c.source.row for c in contract.values()] == list(range(7, 21))
    for c in contract.values():
        assert type(c.qty) is Decimal and type(c.price) is Decimal


def test_load_contract_never_reads_totals_as_positions():
    contract = load_contract(CONTRACT)
    assert not any(code.startswith(("Разом", "ПДВ", "Всього")) for code in contract)


def _contract_file(tmp_path, headers, rows=(), shift=0, title="Договірна ціна"):
    wb = Workbook()
    ws = wb.active
    ws.title = title
    for c, h in enumerate(headers, 1):
        ws.cell(6 + shift, c, h)
    for i, row in enumerate(rows, 7 + shift):
        for c, v in enumerate(row, 1):
            ws.cell(i, c, v)
    path = tmp_path / "contract.xlsx"
    wb.save(path)
    return path


HEADERS = ["№ з/п", "Шифр", "Найменування робіт", "Од. виміру", "Кількість за договором",
           "Ціна за од., грн без ПДВ", "Вартість, грн без ПДВ"]


def test_load_contract_shifted_header(tmp_path):
    path = _contract_file(tmp_path, HEADERS, [(1, "2-1", "Монтаж", "м²", 10, 5.5, 55)], shift=4)
    contract = load_contract(path)
    assert contract["2-1"].source.row == 11 and contract["2-1"].price == Decimal("5.5")


def test_load_contract_missing_price_column(tmp_path):
    path = _contract_file(tmp_path, [h for h in HEADERS if not h.startswith("Ціна")])
    with pytest.raises(InputError) as e:
        load_contract(path)
    assert (e.value.kind, e.value.label, e.value.file, e.value.sheet) == (
        "missing_label", "Ціна", "contract.xlsx", "Договірна ціна")


def test_load_contract_missing_sheet(tmp_path):
    path = _contract_file(tmp_path, HEADERS, title="Кошторис")
    with pytest.raises(InputError) as e:
        load_contract(path)
    assert e.value.kind == "missing_label" and e.value.label == "Договірна ціна"


def test_load_contract_duplicate_code_is_not_silently_resolved(tmp_path):
    path = _contract_file(tmp_path, HEADERS, [(1, "2-1", "A", "м²", 10, 5, 50), (2, "2-1", "B", "м²", 3, 5, 15)])
    with pytest.raises(InputError) as e:
        load_contract(path)
    assert (e.value.kind, e.value.label, e.value.sheet, e.value.rows) == ("duplicate_code", "2-1", "Договірна ціна", [7, 8])


def test_load_contract_corrupt_file(tmp_path):
    path = tmp_path / "broken.xlsx"
    path.write_text("not a workbook", encoding="utf-8")
    with pytest.raises(InputError) as e:
        load_contract(path)
    assert e.value.kind == "unreadable_file" and e.value.file == "broken.xlsx"


def test_load_contract_missing_file(tmp_path):
    with pytest.raises(InputError) as e:
        load_contract(tmp_path / "nope.xlsx")
    assert e.value.kind == "unreadable_file"


def test_load_contract_does_not_modify_the_file():
    before = CONTRACT.read_bytes()
    load_contract(CONTRACT)
    assert CONTRACT.read_bytes() == before


# ---------------------------------------------------------------- load_act
from act_verifier.loaders import load_act  # noqa: E402
from conftest import load_expected  # noqa: E402

FX = ROOT / "tests/fixtures"
ACT_HEADERS = ["№ з/п", "Шифр позиції за договором", "Найменування робіт", "Од. виміру",
               "Кількість", "Ціна за од., грн без ПДВ", "Вартість, грн без ПДВ"]
KB3_LABELS = ["Вартість робіт за звітний період", "ПДВ", "Всього за звітний період",
              "З початку виконання робіт"]


def test_load_act_ok_many():
    act = load_act(FX / "ok_many/act_03.xlsx")
    assert act.number == 3 and act.file == "act_03.xlsx" and act.header_row == 8
    assert len(act.rows) == 11 and [r.source.row for r in act.rows] == list(range(9, 20))
    assert act.skipped_rows == []
    r = act.rows[0]
    assert (r.code, r.unit, r.qty, r.price) == ("2-1", "м²", Decimal("300"), Decimal("485"))
    assert r.source == Source("act_03.xlsx", "КБ-2в", 9)
    for v in (act.subtotal, act.vat, act.total, act.kb3_period_total, act.kb3_cumulative_total):
        assert type(v) is Decimal
    assert act.subtotal + act.vat == act.total == act.kb3_period_total
    assert act.sources["subtotal"] == Source("act_03.xlsx", "КБ-2в", 20)
    assert act.sources["vat"].row == 21 and act.sources["total"].row == 22
    assert act.sources["number"].row == 2
    assert act.sources["kb3_period_total"] == Source("act_03.xlsx", "КБ-3", 7)
    assert act.sources["kb3_cumulative_total"].row == 8


@pytest.mark.parametrize("name", ["shifted_header", "totals_gap"])
def test_load_act_rows_equal_layout_map(name):
    exp = load_expected(FX / name)
    lay = exp["layout"]["act"]
    act = load_act(ROOT / exp["inputs"]["act"])
    ref = load_act(FX / "ok_many/act_03.xlsx")
    assert act.header_row == lay["header_row"]
    assert act.rows[0].source.row == lay["first_data_row"]
    assert act.rows[-1].source.row < lay["subtotal_row"]
    assert act.skipped_rows == lay.get("skipped_rows", [])
    assert (act.sources["subtotal"].row, act.sources["vat"].row, act.sources["total"].row) == (
        lay["subtotal_row"], lay["vat_row"], lay["total_row"])
    # ті самі дані, що в README-розкладці
    assert [(r.code, r.qty, r.price, r.amount) for r in act.rows] == [
        (r.code, r.qty, r.price, r.amount) for r in ref.rows]
    assert (act.subtotal, act.vat, act.total) == (ref.subtotal, ref.vat, ref.total)


@pytest.mark.parametrize("name", ["missing_label", "ambiguous_label"])
def test_load_act_label_errors(name):
    exp = load_expected(FX / name)
    with pytest.raises(InputError) as e:
        load_act(ROOT / exp["inputs"]["act"])
    assert (e.value.kind, e.value.label) == (exp["expected_error"]["kind"], exp["expected_error"]["label"])
    assert e.value.file == "act_03.xlsx" and e.value.sheet == "КБ-2в"
    if name == "ambiguous_label":
        assert len(e.value.rows) == 2


def test_load_previous_act():
    act = load_act(ROOT / "data/synthetic/act_01_2026-09.xlsx", previous=True)
    assert act.number == 1 and len(act.rows) == 5 and type(act.total) is Decimal
    assert act.sources["total"].sheet == "КБ-2в"


@pytest.mark.parametrize("name,attr,code", [
    ("missing_price", "price", "5-2"), ("empty_quantity", "qty", "2-4"), ("empty_amount", "amount", "3-3")])
def test_load_act_empty_values_are_none(name, attr, code):
    act = load_act(FX / name / "act_03.xlsx")
    row = next(r for r in act.rows if r.code == code)
    assert getattr(row, attr) is None


def _act_file(tmp_path, *, title="Акт № 3 за листопад 2026 р.", rows=None, totals=None, kb3=True,
              kb3_items=None, name="act.xlsx", sheet="КБ-2в"):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    if title is not None:
        ws["A2"] = title
    for c, h in enumerate(ACT_HEADERS, 1):
        ws.cell(8, c, h)
    rows = rows if rows is not None else [[1, "2-1", "Монтаж", "м²", 10, 5, 50]]
    r = 9
    for row in rows:
        for c, v in enumerate(row, 1):
            ws.cell(r, c, v)
        r += 1
    totals = totals if totals is not None else [("Разом без ПДВ", 50), ("ПДВ 20%", 10), ("Всього з ПДВ", 60)]
    for label, value in totals:
        ws.cell(r, 3, label)
        ws.cell(r, 7, value)
        r += 1
    if kb3:
        k = wb.create_sheet("КБ-3")
        items = kb3_items if kb3_items is not None else [
            ("Вартість робіт за звітний період, грн без ПДВ", 50), ("ПДВ 20%, грн", 10),
            ("Всього за звітний період, грн з ПДВ", 60), ("З початку виконання робіт, грн з ПДВ", 160)]
        for i, (label, value) in enumerate(items, 5):
            k.cell(i, 1, label)
            k.cell(i, 2, value)
    path = tmp_path / name
    wb.save(path)
    return path


def test_formula_cell_without_cached_value_is_none(tmp_path):
    path = _act_file(tmp_path, rows=[[1, "2-1", "Монтаж", "м²", 10, 5, "=E9*F9"]])
    act = load_act(path)
    assert act.rows[0].amount is None


def test_rows_without_code_are_skipped_not_positions(tmp_path):
    path = _act_file(tmp_path, rows=[[1, "2-1", "Монтаж", "м²", 10, 5, 50], [], [None, None, "Примітка"]])
    act = load_act(path)
    assert [r.code for r in act.rows] == ["2-1"] and act.skipped_rows == [10, 11]


@pytest.mark.parametrize("title,number", [
    ("Акт № 3 за листопад 2026 р.", 3), ("Акт №3", 3), ("  акт №  12 ", 12),
    ("Акт № без номера", None), (None, None),
])
def test_act_number(tmp_path, title, number):
    act = load_act(_act_file(tmp_path, title=title))
    assert act.number == number
    assert ("number" in act.sources) == (title is not None)


def test_empty_value_cell_is_missing_data_not_error(tmp_path):
    path = _act_file(tmp_path, totals=[("Разом без ПДВ", 50), ("ПДВ 20%", None), ("Всього з ПДВ", 60)],
                     kb3_items=[("Вартість робіт за звітний період", 50), ("ПДВ", 10),
                                ("Всього за звітний період", None), ("З початку виконання робіт", 160)])
    act = load_act(path)
    assert act.vat is None and act.sources["vat"].row == 11
    assert act.kb3_period_total is None and act.sources["kb3_period_total"].row == 7


def test_current_act_requires_kb3(tmp_path):
    with pytest.raises(InputError) as e:
        load_act(_act_file(tmp_path, kb3=False))
    assert (e.value.kind, e.value.label) == ("missing_label", "КБ-3")
    act = load_act(_act_file(tmp_path, kb3=False, name="prev.xlsx"), previous=True)
    assert act.kb3_period_total is None and act.total == Decimal("60")


@pytest.mark.parametrize("missing", KB3_LABELS)
def test_current_act_requires_every_kb3_label(tmp_path, missing):
    items = [(label, 1) for label in KB3_LABELS if label != missing]
    with pytest.raises(InputError) as e:
        load_act(_act_file(tmp_path, kb3_items=items))
    assert (e.value.kind, e.value.label, e.value.sheet) == ("missing_label", missing, "КБ-3")


@pytest.mark.parametrize("missing", ["Разом без ПДВ", "ПДВ", "Всього з ПДВ"])
def test_current_act_requires_every_total_label(tmp_path, missing):
    totals = [(label, 1) for label in ["Разом без ПДВ", "ПДВ 20%", "Всього з ПДВ"] if not label.startswith(missing)]
    with pytest.raises(InputError) as e:
        load_act(_act_file(tmp_path, totals=totals))
    assert (e.value.kind, e.value.label) == ("missing_label", missing)


def test_previous_act_needs_only_total(tmp_path):
    act = load_act(_act_file(tmp_path, totals=[("Всього з ПДВ", 60)], kb3=False), previous=True)
    assert act.total == Decimal("60") and act.subtotal is None and [r.code for r in act.rows] == ["2-1"]
    with pytest.raises(InputError) as e:
        load_act(_act_file(tmp_path, totals=[("Разом без ПДВ", 50)], kb3=False, name="p2.xlsx"), previous=True)
    assert (e.value.kind, e.value.label) == ("missing_label", "Всього з ПДВ")


# ---------------------------------------------------------------- назва аркуша, як знайдено (T17)
def test_sheet_title_as_found_is_cited_everywhere(tmp_path):
    """Аркуш знайдено за префіксом «КБ-2в» — у джерелах і пропущених рядках його справжня назва (ADR-0003)."""
    from act_verifier.checks import verify
    from act_verifier.models import ContractPosition, Source

    act = load_act(_act_file(tmp_path, title="Акт № 2 за листопад 2026 р.", sheet="КБ-2в акт 2",
                             rows=[[1, "2-1", "Монтаж", "м²", 10, 5, 50], []]))
    prev = load_act(_act_file(tmp_path, title="Акт № 1 за жовтень 2026 р.", sheet="КБ-2в (жовтень)",
                              rows=[[1, "3-1", "Фарбування", "м²", 1, 5, 5]],
                              totals=[("Всього з ПДВ", 6)], kb3=False, name="prev.xlsx"), previous=True)
    assert (act.sheet, prev.sheet) == ("КБ-2в акт 2", "КБ-2в (жовтень)")

    contract = {"2-1": ContractPosition("2-1", "Монтаж", "м²", Decimal("100"), Decimal("5"),
                                        Source("contract.xlsx", "Договірна ціна", 7))}
    report = verify(act, contract, [prev])
    sheets = {(s.file, s.sheet) for f in report.findings for s in f.sources}
    assert ("prev.xlsx", "КБ-2в (жовтень)") in sheets  # C05: позиції в попередньому акті немає
    assert {sh for file, sh in sheets if file == "act.xlsx"} <= {"КБ-2в акт 2", "КБ-3"}
    assert not any(sh == "КБ-2в" for _, sh in sheets)
    assert report.skipped_rows == [("act.xlsx", "КБ-2в акт 2", [10])]


def test_load_contract_empty_quantity_and_price_load_as_none_not_zero(tmp_path):
    """Порожня клітинка договору — брак даних (None), не 0 і не помилка вхідних даних (review 2, finding 1)."""
    path = _contract_file(tmp_path, HEADERS, [(1, "2-1", "A", "м²", None, 5, 50), (2, "2-2", "B", "м²", 3, None, 15)])
    contract = load_contract(path)
    assert (contract["2-1"].qty, contract["2-1"].price) == (None, Decimal("5"))
    assert (contract["2-2"].qty, contract["2-2"].price) == (Decimal("3"), None)
