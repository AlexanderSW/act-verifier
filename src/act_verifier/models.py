"""Структури даних. Гроші й обсяги — тільки Decimal, ніколи float."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


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


@dataclass
class Finding:
    check: str               # ID з docs/checks.md, напр. "C03_price_matches_contract"
    status: Status
    code: str | None         # шифр позиції; None — перевірка рівня акта
    expected: str | None = None
    actual: str | None = None
    message: str = ""
    sources: list[Source] = field(default_factory=list)


@dataclass
class Report:
    findings: list[Finding]
    skipped: list[str]       # що не перевірено і чому

    @property
    def verdict(self) -> str:
        statuses = {f.status for f in self.findings}
        if Status.FAIL in statuses:
            return "fail"
        if statuses & {Status.UNKNOWN, Status.WARNING}:
            return "needs_review"
        return "pass"
