"""Читання договірної ціни й актів з .xlsx (openpyxl).

Розкладка не захардкоджена: аркуші, рядок заголовків і підсумки знаходяться
за підписами (layout.py, ADR-0001). Файли відкриваються лише для читання
(read_only=True, data_only=True) і ніколи не зберігаються.
"""

from __future__ import annotations

import re
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from openpyxl import load_workbook

from .layout import find_header_row, find_label_row, find_optional_label_row, find_sheet, normalize
from .models import Act, ActRow, ContractPosition, InputError, Source

CONTRACT_SHEET = "Договірна ціна"
HEADER_LABELS = ["Шифр", "Найменування", "Од. виміру", "Кількість", "Ціна", "Вартість"]


# ---------------------------------------------------------------- спільні читачі
class _Workbook:
    """Контекст: відкрити книгу лише для читання, будь-яка помилка відкриття -> unreadable_file."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.wb = None

    def __enter__(self):
        try:
            self.wb = load_workbook(self.path, read_only=True, data_only=True)
        except (OSError, zipfile.BadZipFile, KeyError, ValueError, InvalidOperation) as exc:
            raise InputError("unreadable_file", file=self.path.name) from exc
        except Exception as exc:  # openpyxl кидає й власні типи на зламаних файлах
            if type(exc).__module__.startswith(("openpyxl", "xml", "zipfile")):
                raise InputError("unreadable_file", file=self.path.name) from exc
            raise
        return self.wb

    def __exit__(self, *exc) -> None:
        if self.wb is not None:
            self.wb.close()  # read_only тримає файл відкритим — звільняємо


def _dec(value: object) -> Decimal | None:
    """Число з клітинки як Decimal; порожня клітинка або формула без значення -> None, не 0.

    Числа, записані текстом («1 250,50»), — поза межами етапу 1 (spec §3): вони
    стають None, тобто браком даних, що дає лише unknown, ніколи не хибний pass.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, Decimal):
        return value
    return None


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _cell(row: tuple, col: int):
    return row[col - 1] if len(row) >= col else None


# ---------------------------------------------------------------- договірна ціна
def load_contract(path: Path) -> dict[str, ContractPosition]:
    """Повертає {шифр: позиція} з аркуша «Договірна ціна»."""
    path = Path(path)
    file = path.name
    with _Workbook(path) as wb:
        ws = find_sheet(wb, CONTRACT_SHEET, file)
        header, cols = find_header_row(ws, HEADER_LABELS, file)
        end = find_optional_label_row(ws, "Разом без ПДВ", min_row=header + 1)
        max_row = end[0] - 1 if end else None
        out: dict[str, ContractPosition] = {}
        rows_by_code: dict[str, list[int]] = {}
        start = header + 1
        for offset, row in enumerate(ws.iter_rows(min_row=start, max_row=max_row, values_only=True)):
            r = start + offset
            code = _text(_cell(row, cols["Шифр"]))
            if not code:
                continue
            rows_by_code.setdefault(code, []).append(r)
            out[code] = ContractPosition(
                code=code,
                name=_text(_cell(row, cols["Найменування"])),
                unit=_text(_cell(row, cols["Од. виміру"])),
                # Порожня кількість/ціна в договорі не підставляється нулем (data-model D5):
                # None іде далі, а перевірки, яким вона потрібна, дають unknown.
                qty=_dec(_cell(row, cols["Кількість"])),
                price=_dec(_cell(row, cols["Ціна"])),
                source=Source(file, ws.title, r),
            )
        # Дубль шифру в договорі: не беремо ні перший, ні останній -> код 3 (data-model §ContractPosition).
        dups = {c: rows for c, rows in rows_by_code.items() if len(rows) > 1}
        if dups:
            code, rows = next(iter(dups.items()))
            raise InputError("duplicate_code", label=code, file=file, sheet=ws.title, rows=rows)
        return out


def _value(ws, row: int, col: int):
    for values in ws.iter_rows(min_row=row, max_row=row, min_col=col, max_col=col, values_only=True):
        return values[0] if values else None
    return None


def _act_number(ws, header: int, file: str, sources: dict[str, Source]) -> tuple[int | None, str | None]:
    """Номер і період акта з заголовка «Акт № N за … р.» над таблицею.

    Немає заголовка або в ньому немає числа — брак даних (None), не помилка вхідних даних (AC-11).
    """
    if header <= 1:  # над шапкою рядків немає; max_row=0 openpyxl читає як «без межі»
        return None, None
    hit = find_optional_label_row(ws, "Акт №", max_row=header - 1)
    if hit is None:
        return None, None
    row, col = hit
    sources["number"] = Source(file, ws.title, row)
    text = normalize(_value(ws, row, col))
    m = _NUMBER.search(text)
    number = int(m.group(1)) if m else None
    p = _PERIOD.search(text)
    return number, (p.group(1) if p else None)


_NUMBER = re.compile(r"№\s*(\d+)")
_PERIOD = re.compile(r"\bза\s+(.+?)\s*р\.?\s*$")
KB2V_SHEET = "КБ-2в"
KB3_SHEET = "КБ-3"
TOTALS = [("subtotal", "Разом без ПДВ"), ("vat", "ПДВ"), ("total", "Всього з ПДВ")]
KB3_VALUES = [("kb3_subtotal", "Вартість робіт за звітний період"), ("kb3_vat", "ПДВ"),
              ("kb3_period_total", "Всього за звітний період"),
              ("kb3_cumulative_total", "З початку виконання робіт")]


def load_act(path: Path, *, previous: bool = False) -> Act:
    """Читає аркуші «КБ-2в» і «КБ-3». Порожні клітинки -> None, а не 0.

    previous=True — попередній акт: потрібні лише аркуш «КБ-2в», заголовки й «Всього з ПДВ»
    (AC-07); «Разом без ПДВ», «ПДВ» і аркуш «КБ-3» не обов'язкові.
    """
    path = Path(path)
    file = path.name
    sources: dict[str, Source] = {}
    values: dict[str, Decimal | None] = {}
    with _Workbook(path) as wb:
        ws = find_sheet(wb, KB2V_SHEET, file)
        header, cols = find_header_row(ws, HEADER_LABELS, file)
        number, period = _act_number(ws, header, file, sources)

        # Підсумки шукаються лише під рядком заголовків (ADR-0001); значення — у колонці «Вартість».
        label_rows: dict[str, int] = {}
        for key, label in TOTALS:
            if previous and key != "total":
                hit = find_optional_label_row(ws, label, min_row=header + 1)
            else:
                hit = find_label_row(ws, label, file, min_row=header + 1)[0], None
            if hit is None:
                continue
            label_rows[key] = hit[0]
            sources[key] = Source(file, ws.title, hit[0])
            values[key] = _dec(_value(ws, hit[0], cols["Вартість"]))

        # Таблиця: від заголовків до першого рядка підсумків. Рядок без шифру — не позиція.
        end = min(label_rows.values()) - 1
        rows: list[ActRow] = []
        skipped: list[int] = []
        start = header + 1
        seen = start
        for offset, row in enumerate(ws.iter_rows(min_row=start, max_row=end, values_only=True)):
            r = start + offset
            seen = r + 1
            code = _text(_cell(row, cols["Шифр"]))
            if not code:
                skipped.append(r)
                continue
            rows.append(ActRow(
                row_no=r,  # номер рядка Excel, як знайдено
                code=code,
                name=_text(_cell(row, cols["Найменування"])),
                unit=_text(_cell(row, cols["Од. виміру"])),
                qty=_dec(_cell(row, cols["Кількість"])),
                price=_dec(_cell(row, cols["Ціна"])),
                amount=_dec(_cell(row, cols["Вартість"])),
                source=Source(file, ws.title, r),
            ))
        # read_only може віддати менше рядків, ніж end (порожній хвіст) — вони теж пропущені
        skipped.extend(range(seen, end + 1))

        if not previous:
            kb3 = find_sheet(wb, KB3_SHEET, file)
            for key, label in KB3_VALUES:
                r, c = find_label_row(kb3, label, file)
                sources[key] = Source(file, kb3.title, r)
                values[key] = _dec(_value(kb3, r, c + 1))  # значення — праворуч від підпису

    return Act(
        number=number,
        period=period,
        rows=rows,
        subtotal=values.get("subtotal"),
        vat=values.get("vat"),
        total=values.get("total"),
        kb3_period_total=values.get("kb3_period_total"),
        kb3_cumulative_total=values.get("kb3_cumulative_total"),
        file=file,
        sources=sources,
        header_row=header,
        skipped_rows=skipped,
        sheet=ws.title,
    )
