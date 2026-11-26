"""Пошук розкладки аркуша за підписами (ADR-0001).

Жодних жорстких номерів рядків: аркуш, рядок заголовків і рядки підсумків
знаходяться за нормалізованим підписом (trim, будь-які пробіли в один, casefold)
за префіксом. Нуль збігів -> InputError(missing_label), два й більше ->
InputError(ambiguous_label) з усіма рядками-кандидатами. «Перший збіг» не
використовується ніколи.
"""

from __future__ import annotations

import re

from .models import InputError

_WS = re.compile(r"\s+")  # у Python 3 \s охоплює й нерозривний пробіл U+00A0


def normalize(text: object) -> str:
    if text is None:
        return ""
    return _WS.sub(" ", str(text)).strip().casefold()


def find_sheet(wb, label: str, file: str):
    """Аркуш, назва якого після нормалізації починається з label."""
    key = normalize(label)
    hits = [name for name in wb.sheetnames if normalize(name).startswith(key)]
    if not hits:
        raise InputError("missing_label", label=label, file=file, sheet=label)
    if len(hits) > 1:
        raise InputError("ambiguous_label", label=label, file=file, sheet=", ".join(hits))
    return wb[hits[0]]


def _rows(ws, min_row: int | None = None, max_row: int | None = None):
    """(номер рядка, нормалізовані значення клітинок) у межах регіону."""
    start = min_row or 1
    for offset, values in enumerate(ws.iter_rows(min_row=start, max_row=max_row, values_only=True)):
        yield start + offset, [normalize(v) if isinstance(v, str) else "" for v in values]


def _matches(cells: list[str], key: str, column: int | None = None) -> list[int]:
    """Номери колонок (з 1), де текст клітинки починається з key."""
    return [i for i, c in enumerate(cells, 1)
            if c and c.startswith(key) and (column is None or i == column)]


def find_header_row(ws, labels: list[str], file: str) -> tuple[int, dict[str, int]]:
    """Рядок, у якому є всі підписи заголовків; повертає (рядок, {підпис: колонка})."""
    keys = {label: normalize(label) for label in labels}
    found: dict[str, bool] = {label: False for label in labels}
    candidates: list[tuple[int, list[str]]] = []
    for row, cells in _rows(ws):
        hit = {label: bool(_matches(cells, key)) for label, key in keys.items()}
        for label, h in hit.items():
            found[label] = found[label] or h
        if all(hit.values()):
            candidates.append((row, cells))
    if not candidates:
        # називаємо перший підпис, якого немає в жодному рядку; якщо кожен десь є,
        # але не разом, — перший, якого бракує в рядку з найбільшою кількістю збігів
        missing = next((label for label in labels if not found[label]), None)
        if missing is None:
            best = max(_rows(ws), key=lambda rc: sum(bool(_matches(rc[1], k)) for k in keys.values()))
            missing = next(label for label, k in keys.items() if not _matches(best[1], k))
        raise InputError("missing_label", label=missing, file=file, sheet=ws.title)
    if len(candidates) > 1:
        raise InputError("ambiguous_label", label=labels[0], file=file, sheet=ws.title,
                         rows=[r for r, _ in candidates])
    row, cells = candidates[0]
    cols: dict[str, int] = {}
    for label, key in keys.items():
        hits = _matches(cells, key)
        if len(hits) > 1:
            raise InputError("ambiguous_label", label=label, file=file, sheet=ws.title, rows=[row])
        cols[label] = hits[0]
    return row, cols


def _label_rows(ws, label, *, min_row, max_row, column) -> list[tuple[int, int]]:
    key = normalize(label)
    out = []
    for row, cells in _rows(ws, min_row, max_row):
        hits = _matches(cells, key, column)
        if hits:
            out.append((row, hits[0]))  # дві клітинки в одному рядку — один рядок
    return out


def find_label_row(
    ws,
    label: str,
    file: str,
    *,
    min_row: int | None = None,
    max_row: int | None = None,
    column: int | None = None,
) -> tuple[int, int]:
    """Єдиний рядок регіону, де клітинка починається з label; повертає (рядок, колонка)."""
    hits = _label_rows(ws, label, min_row=min_row, max_row=max_row, column=column)
    if not hits:
        raise InputError("missing_label", label=label, file=file, sheet=ws.title)
    if len(hits) > 1:
        raise InputError("ambiguous_label", label=label, file=file, sheet=ws.title,
                         rows=[r for r, _ in hits])
    return hits[0]


def find_optional_label_row(
    ws,
    label: str,
    *,
    min_row: int | None = None,
    max_row: int | None = None,
    column: int | None = None,
) -> tuple[int, int] | None:
    """Як find_label_row, але відсутність (або кілька кандидатів) — None, не помилка.

    Для заголовка «Акт №»: його брак — це брак даних (unknown), а не помилка вхідних даних.
    Кілька кандидатів теж None: номер не вгадується.
    """
    hits = _label_rows(ws, label, min_row=min_row, max_row=max_row, column=column)
    return hits[0] if len(hits) == 1 else None
