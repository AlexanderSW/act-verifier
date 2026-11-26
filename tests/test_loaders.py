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
    assert e.value.kind == "ambiguous_label" and e.value.label == "2-1" and e.value.rows == [7, 8]


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
