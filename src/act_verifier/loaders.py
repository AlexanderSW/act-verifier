"""Читання договірної ціни й актів з .xlsx (openpyxl).

Розкладка не захардкоджена: аркуші, рядок заголовків і підсумки знаходяться
за підписами (layout.py, ADR-0001). Файли відкриваються лише для читання
(read_only=True, data_only=True) і ніколи не зберігаються.
"""

from __future__ import annotations

import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from openpyxl import load_workbook

from .layout import find_header_row, find_optional_label_row, find_sheet
from .models import Act, ContractPosition, InputError, Source

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
                # Порожня кількість/ціна в договорі не підставляється нулем (data-model D5, відкрите питання):
                # None іде далі, а перевірки, яким вона потрібна, дають unknown.
                qty=_dec(_cell(row, cols["Кількість"])),
                price=_dec(_cell(row, cols["Ціна"])),
                source=Source(file, ws.title, r),
            )
        # Дубль шифру в договорі: не беремо ні перший, ні останній (data-model §ContractPosition TBD).
        dups = {c: rows for c, rows in rows_by_code.items() if len(rows) > 1}
        if dups:
            code, rows = next(iter(dups.items()))
            raise InputError("ambiguous_label", label=code, file=file, sheet=ws.title, rows=rows)
        return out


def load_act(path: Path) -> Act:
    """Читає аркуші «КБ-2в» і «КБ-3». Порожні клітинки -> None, а не 0."""
    raise NotImplementedError
