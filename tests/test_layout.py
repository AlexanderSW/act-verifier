"""Юніт-тести пошуку розкладки (T4, ADR-0001): нормалізація, префікс, унікальність. Без файлів на диску."""

import pytest
from openpyxl import Workbook

from act_verifier.layout import (
    find_header_row,
    find_label_row,
    find_optional_label_row,
    find_sheet,
    normalize,
)
from act_verifier.models import InputError

HEADERS = ["Шифр", "Найменування", "Од. виміру", "Кількість", "Ціна", "Вартість"]
ACT_HEADERS = ["№ з/п", "Шифр позиції за договором", "Найменування робіт", "Од. виміру",
               "Кількість", "Ціна за од., грн без ПДВ", "Вартість, грн без ПДВ"]


def sheet(rows, title="КБ-2в"):
    wb = Workbook()
    ws = wb.active
    ws.title = title
    for r, row in rows.items():
        for c, v in enumerate(row, 1):
            ws.cell(r, c, v)
    return wb, ws


def act_sheet(header_row=8, totals=("Разом без ПДВ", "ПДВ 20%", "Всього з ПДВ")):
    rows = {2: ["Акт № 3 за листопад 2026 р."], header_row: ACT_HEADERS,
            header_row + 1: [1, "2-1", "Монтаж", "м²", 10, 5, 50]}
    for i, t in enumerate(totals):
        rows[header_row + 2 + i] = [None, None, t, None, None, None, 1]
    return sheet(rows)


@pytest.mark.parametrize("raw,norm", [
    ("  Разом без   ПДВ ", "разом без пдв"),
    ("ВСЬОГО З ПДВ", "всього з пдв"),
    (None, ""),
    (12, "12"),
    ("Од.\tвиміру\n", "од. виміру"),
])
def test_normalize(raw, norm):
    assert normalize(raw) == norm


def test_find_sheet_prefix_and_missing():
    wb = Workbook()
    wb.active.title = "КБ-2в "
    wb.create_sheet("КБ-3")
    assert find_sheet(wb, "КБ-2в", "a.xlsx").title == "КБ-2в "
    assert find_sheet(wb, "кб-3", "a.xlsx").title == "КБ-3"
    with pytest.raises(InputError) as e:
        find_sheet(wb, "Договірна ціна", "a.xlsx")
    assert (e.value.kind, e.value.label, e.value.file) == ("missing_label", "Договірна ціна", "a.xlsx")


def test_find_sheet_ambiguous():
    wb = Workbook()
    wb.active.title = "КБ-2в"
    wb.create_sheet("КБ-2в (копія)")
    with pytest.raises(InputError) as e:
        find_sheet(wb, "КБ-2в", "a.xlsx")
    assert e.value.kind == "ambiguous_label" and e.value.label == "КБ-2в"


@pytest.mark.parametrize("header_row", [8, 11, 3])
def test_find_header_row_shifted(header_row):
    _, ws = act_sheet(header_row)
    row, cols = find_header_row(ws, HEADERS, "a.xlsx")
    assert row == header_row
    assert cols == {"Шифр": 2, "Найменування": 3, "Од. виміру": 4, "Кількість": 5, "Ціна": 6, "Вартість": 7}


def test_find_header_row_missing_column_names_the_label_and_sheet():
    _, ws = sheet({6: ["№", "Шифр", "Найменування", "Од. виміру", "Кількість", "Вартість"]})
    with pytest.raises(InputError) as e:
        find_header_row(ws, HEADERS, "c.xlsx")
    assert (e.value.kind, e.value.label, e.value.file, e.value.sheet) == ("missing_label", "Ціна", "c.xlsx", "КБ-2в")


def test_find_header_row_two_rows_is_ambiguous():
    _, ws = sheet({6: HEADERS, 30: HEADERS})
    with pytest.raises(InputError) as e:
        find_header_row(ws, HEADERS, "c.xlsx")
    assert e.value.kind == "ambiguous_label" and e.value.rows == [6, 30]


def test_find_header_row_label_in_two_columns_is_ambiguous():
    _, ws = sheet({6: HEADERS + ["Ціна з ПДВ"]})
    with pytest.raises(InputError) as e:
        find_header_row(ws, HEADERS, "c.xlsx")
    assert e.value.kind == "ambiguous_label" and e.value.label == "Ціна" and e.value.rows == [6]


def test_find_label_row_vat_prefix_without_20_percent():
    _, ws = act_sheet(totals=("Разом без ПДВ", "ПДВ 20%", "Всього з ПДВ"))
    assert find_label_row(ws, "ПДВ", "a.xlsx", min_row=9) == (11, 3)
    assert find_label_row(ws, "Разом без ПДВ", "a.xlsx", min_row=9) == (10, 3)
    assert find_label_row(ws, "Всього з ПДВ", "a.xlsx", min_row=9) == (12, 3)


def test_find_label_row_missing():
    _, ws = act_sheet(totals=("ПДВ 20%", "Всього з ПДВ"))
    with pytest.raises(InputError) as e:
        find_label_row(ws, "Разом без ПДВ", "a.xlsx", min_row=9)
    assert (e.value.kind, e.value.label, e.value.sheet) == ("missing_label", "Разом без ПДВ", "КБ-2в")


def test_find_label_row_ambiguous_lists_every_competing_row():
    _, ws = act_sheet(totals=("Разом без ПДВ", "ПДВ 20%", "Всього з ПДВ", "ПДВ (довідково)"))
    with pytest.raises(InputError) as e:
        find_label_row(ws, "ПДВ", "a.xlsx", min_row=9)
    assert e.value.kind == "ambiguous_label" and e.value.rows == [11, 13]


def test_find_label_row_region_excludes_rows_above():
    _, ws = act_sheet()
    ws.cell(4, 1, "ПДВ: платник на загальних умовах")  # над заголовком — поза регіоном
    assert find_label_row(ws, "ПДВ", "a.xlsx", min_row=9)[0] == 11
    with pytest.raises(InputError):
        find_label_row(ws, "ПДВ", "a.xlsx")


def test_find_label_row_column_and_max_row():
    _, ws = act_sheet()
    assert find_label_row(ws, "Всього з ПДВ", "a.xlsx", column=3, max_row=12) == (12, 3)
    with pytest.raises(InputError):
        find_label_row(ws, "Всього з ПДВ", "a.xlsx", column=1)
    with pytest.raises(InputError):
        find_label_row(ws, "Всього з ПДВ", "a.xlsx", max_row=11)


def test_two_cells_in_one_row_count_as_one_row():
    _, ws = sheet({5: ["ПДВ 20%", "ПДВ"]})
    assert find_label_row(ws, "ПДВ", "a.xlsx") == (5, 1)


def test_number_cell_does_not_match_text_label():
    _, ws = sheet({5: [20, "ПДВ 20%"]})
    assert find_label_row(ws, "ПДВ", "a.xlsx") == (5, 2)


def test_optional_label_row():
    _, ws = act_sheet()
    assert find_optional_label_row(ws, "Акт №", max_row=7) == (2, 1)
    assert find_optional_label_row(ws, "Довідка", max_row=7) is None
    ws.cell(3, 1, "Акт № 4")
    assert find_optional_label_row(ws, "Акт №", max_row=7) is None  # двічі — не вгадуємо
