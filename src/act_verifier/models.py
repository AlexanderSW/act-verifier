"""Структури даних. Гроші й обсяги — тільки Decimal, ніколи float."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class InputError(Exception):
    """Помилка вхідних даних: перевірка не відбулася (код виходу 3, ADR-0002).

    Ловить лише cli.main. Будь-який інший виняток — баг.
    """

    KINDS = frozenset({
        "missing_label", "ambiguous_label", "unreadable_file", "invocation", "overwrite_refused",
    })

    def __init__(
        self,
        kind: str,
        label: str | None = None,
        file: str | None = None,
        sheet: str | None = None,
        rows: list[int] | None = None,
    ) -> None:
        if kind not in self.KINDS:
            raise ValueError(f"невідомий вид помилки вхідних даних: {kind!r}")
        self.kind = kind
        self.label = label
        self.file = file
        self.sheet = sheet
        self.rows = list(rows) if rows else []
        super().__init__(kind, label, file, sheet, self.rows)


class Status(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    WARNING = "warning"


@dataclass(frozen=True)
class Source:
    """Звідки взято число: файл, аркуш, номер рядка Excel."""

    file: str
    sheet: str
    row: int | None = None

    def __str__(self) -> str:
        loc = f", рядок {self.row}" if self.row else ""
        return f"{self.file} / {self.sheet}{loc}"


@dataclass
class ContractPosition:
    code: str
    name: str
    unit: str
    qty: Decimal
    price: Decimal
    source: Source


@dataclass
class ActRow:
    row_no: int
    code: str
    name: str
    unit: str
    qty: Decimal | None
    price: Decimal | None
    amount: Decimal | None
    source: Source


@dataclass
class Act:
    number: int | None
    period: str | None
    rows: list[ActRow]
    subtotal: Decimal | None
    vat: Decimal | None
    total: Decimal | None
    kb3_period_total: Decimal | None
    kb3_cumulative_total: Decimal | None
    file: str
    # Походження кожного скалярного значення (number, subtotal, vat, total,
    # kb3_period_total, kb3_cumulative_total) — ADR-0003.
    sources: dict[str, Source] = field(default_factory=dict)
    header_row: int | None = None          # рядок заголовків КБ-2в, як знайдено
    skipped_rows: list[int] = field(default_factory=list)  # рядки таблиці без шифру


@dataclass
class Finding:
    check: str               # ID з docs/checks.md, напр. "C03_price_matches_contract"
    status: Status
    code: str | None         # шифр позиції; None — перевірка рівня акта
    expected: str | None = None
    actual: str | None = None
    message: str = ""
    sources: list[Source] = field(default_factory=list)


@dataclass(frozen=True)
class Skipped:
    """Перевірка, яку не виконано: що, для якої позиції (None — рівень акта) і чому."""

    check: str
    code: str | None
    reason: str


@dataclass
class Report:
    findings: list[Finding]
    skipped: list[Skipped]   # що не перевірено і чому
    # Джерела вхідних чисел для блоку доказів: роль -> список Source
    # ("contract", "previous", "act").
    inputs: dict[str, list[Source]] = field(default_factory=dict)
    # Рядки без шифру, пропущені при читанні: (файл, аркуш, рядки).
    skipped_rows: list[tuple[str, str, list[int]]] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        statuses = {f.status for f in self.findings}
        if Status.FAIL in statuses:
            return "fail"
        if statuses & {Status.UNKNOWN, Status.WARNING}:
            return "needs_review"
        return "pass"
