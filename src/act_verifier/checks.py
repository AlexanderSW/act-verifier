"""Перевірки C01–C13. Опис і допуски — docs/checks.md.

Кожна перевірка повертає Finding і для pass теж: звіт має показати,
що саме перевірено, а не лише що знайдено.
"""

from __future__ import annotations

from decimal import Decimal

from .models import Act, ContractPosition, Report

TOLERANCE = Decimal("0.01")
VAT_RATE = Decimal("0.20")


def verify(
    act: Act,
    contract: dict[str, ContractPosition],
    previous_acts: list[Act],
) -> Report:
    """Запускає всі перевірки й збирає звіт.

    Не зупиняється на першій помилці: сценарій combo_three_errors
    очікує всі три знахідки.
    """
    raise NotImplementedError
