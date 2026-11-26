"""Перевірки C01–C13. Опис і допуски — docs/checks.md.

Кожна перевірка повертає Finding і для pass теж: звіт має показати,
що саме перевірено, а не лише що знайдено. Перевірка, яку неможливо виконати,
стає Skipped (що, для якої позиції, чому) — у розділ «не перевірено» блоку доказів.
Брак даних ніколи не дає pass.
"""

from __future__ import annotations

from collections import Counter
from decimal import ROUND_HALF_UP, Decimal

from .models import Act, ActRow, ContractPosition, Finding, Report, Skipped, Source, Status

TOLERANCE = Decimal("0.01")
VAT_RATE = Decimal("0.20")
CENT = Decimal("0.01")

C01 = "C01_position_in_contract"
C02 = "C02_unit_matches"
C03 = "C03_price_matches_contract"
C04 = "C04_amount_arithmetic"
C05 = "C05_within_remaining_volume"
C06 = "C06_no_duplicate_positions"
C11 = "C11_required_values_present"

REASON_EMPTY = {"qty": "порожня кількість", "price": "порожня ціна", "amount": "порожня вартість"}
REASON_NOT_IN_CONTRACT = "позиції немає в договорі"


def money(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def _s(v: Decimal | str | None) -> str | None:
    return None if v is None else str(v)


# ---------------------------------------------------------------- повнота попередніх актів
def previous_completeness(act: Act, previous_acts: list[Act]) -> str | None:
    """None, якщо попередні акти — рівно 1…N−1 без повторів; інакше причина для C05/C13 unknown (AC-11)."""
    n = act.number
    if n is None:
        return "номер акта не прочитано"
    for p in previous_acts:
        if p.number is None:
            return f"номер попереднього акта не прочитано — {p.file}"
    numbers = Counter(p.number for p in previous_acts)
    dups = sorted(m for m, k in numbers.items() if k > 1)
    if dups:
        return f"повторюється номер попереднього акта {dups[0]}"
    outside = sorted(m for m in numbers if not 1 <= m <= n - 1)
    if outside:
        return f"номер попереднього акта {outside[0]} поза 1…{n - 1}"
    k = len(numbers)
    if k != n - 1:
        return f"подано попередніх актів: {k} з {n - 1}"
    return None


# ---------------------------------------------------------------- перевірки рядків
class _Out:
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.skipped: list[Skipped] = []

    def add(self, check, status, row: ActRow, expected=None, actual=None, message="", sources=None):
        self.findings.append(Finding(check, status, row.code, _s(expected), _s(actual), message,
                                     sources or [row.source]))

    def skip(self, check, row: ActRow, reason: str):
        self.skipped.append(Skipped(check, row.code, reason))


def _empty(row: ActRow) -> list[str]:
    return [k for k in ("qty", "price", "amount") if getattr(row, k) is None]


def _c05(out: _Out, row: ActRow, pos: ContractPosition, previous_acts: list[Act], completeness: str | None):
    if row.qty is None:
        out.skip(C05, row, REASON_EMPTY["qty"])
        return
    sources = [row.source, pos.source]
    used = Decimal(0)
    unknown = None
    for p in previous_acts:
        hits = [r for r in p.rows if r.code == row.code]
        if hits:
            sources.extend(r.source for r in hits)
        else:  # акт переглянуто, позиції в ньому немає — теж джерело
            sources.append(Source(p.file, "КБ-2в"))
        for r in hits:
            if r.qty is None:
                unknown = unknown or f"у попередньому акті {p.file} порожня кількість {row.code}"
            else:
                used += r.qty
    if completeness:
        unknown = completeness
    elif pos.qty is None:
        unknown = "у договорі порожня кількість"
    if unknown:
        out.add(C05, Status.UNKNOWN, row, actual=row.qty, message=unknown, sources=sources)
        return
    remaining = pos.qty - used
    status = Status.PASS if row.qty <= remaining else Status.FAIL
    out.add(C05, status, row, expected=remaining, actual=row.qty, sources=sources,
            message="" if status is Status.PASS else f"кількість {row.qty} більша за залишок {remaining}")


def check_rows(
    act: Act,
    contract: dict[str, ContractPosition],
    previous_acts: list[Act],
    completeness: str | None,
) -> tuple[list[Finding], list[Skipped]]:
    """C01–C06, C11 для кожного рядка акта, у порядку рядків; в межах рядка — за ID перевірки."""
    out = _Out()
    counts = Counter(r.code for r in act.rows)
    seen_dup: set[str] = set()
    for row in sorted(act.rows, key=lambda r: r.row_no):
        start = len(out.findings)
        empty = _empty(row)
        pos = contract.get(row.code)

        # C11 — обов'язкові значення
        if empty:
            out.add(C11, Status.UNKNOWN, row, message="порожні: " + ", ".join(REASON_EMPTY[k] for k in empty))
        else:
            out.add(C11, Status.PASS, row)

        # C01 — позиція є в договорі; fail -> C02, C03, C05 не виконуються
        if pos is None:
            out.add(C01, Status.FAIL, row, expected="позиція з договірної ціни", actual=row.code,
                    message=REASON_NOT_IN_CONTRACT)
            for check in (C02, C03, C05):
                out.skip(check, row, REASON_NOT_IN_CONTRACT)
        else:
            out.add(C01, Status.PASS, row, expected=row.code, actual=row.code, sources=[row.source, pos.source])

            # C02 — одиниця виміру
            ok = row.unit.strip() == pos.unit.strip()
            out.add(C02, Status.PASS if ok else Status.FAIL, row, expected=pos.unit, actual=row.unit,
                    sources=[row.source, pos.source])

            # C03 — ціна = договірна, допуск 0,00
            if row.price is None:
                out.skip(C03, row, REASON_EMPTY["price"])
            elif pos.price is None:
                out.add(C03, Status.UNKNOWN, row, actual=row.price, message="у договорі порожня ціна",
                        sources=[row.source, pos.source])
            else:
                ok = row.price == pos.price
                out.add(C03, Status.PASS if ok else Status.FAIL, row, expected=pos.price, actual=row.price,
                        sources=[row.source, pos.source])

        # C04 — вартість = кількість × ціна, ±0,01
        if empty:
            out.skip(C04, row, ", ".join(REASON_EMPTY[k] for k in empty))
        else:
            calc = money(row.qty * row.price)
            ok = abs(calc - row.amount) <= TOLERANCE
            out.add(C04, Status.PASS if ok else Status.FAIL, row, expected=calc, actual=row.amount)

        # C05 — у межах залишку обсягу
        if pos is not None:
            _c05(out, row, pos, previous_acts, completeness)

        # C06 — шифр один раз в акті (одна знахідка на шифр)
        if counts[row.code] > 1:
            if row.code not in seen_dup:
                seen_dup.add(row.code)
                dup_sources = [r.source for r in act.rows if r.code == row.code]
                out.add(C06, Status.FAIL, row, expected="1", actual=str(counts[row.code]),
                        message="шифр трапляється в акті кілька разів", sources=dup_sources)
        else:
            out.add(C06, Status.PASS, row, expected="1", actual="1")

        out.findings[start:] = sorted(out.findings[start:], key=lambda f: f.check)
    return out.findings, out.skipped


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
