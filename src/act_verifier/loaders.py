"""Читання договірної ціни й актів з .xlsx (openpyxl).

Розкладка файлів описана в README, розділ «Формат вхідних файлів».
Порада: не хардкодьте номер рядка заголовків — шукайте рядок, де є «Шифр».
"""

from __future__ import annotations

from pathlib import Path

from .models import Act, ContractPosition


def load_contract(path: Path) -> dict[str, ContractPosition]:
    """Повертає {шифр: позиція} з аркуша «Договірна ціна»."""
    raise NotImplementedError


def load_act(path: Path) -> Act:
    """Читає аркуші «КБ-2в» і «КБ-3». Порожні клітинки -> None, а не 0."""
    raise NotImplementedError
