"""Вивід результату: Excel з розбіжностями + Markdown з блоком доказів."""

from __future__ import annotations

from pathlib import Path

from .models import Report


def write_excel(report: Report, path: Path) -> None:
    """Аркуш «Перевірки»: шифр | перевірка | статус | очікувано | фактично | джерело."""
    raise NotImplementedError


def render_evidence(report: Report) -> str:
    """Блок доказів: що перевірено, що ні, звідки числа (формат — docs/checks.md)."""
    raise NotImplementedError


def append_error_log(report: Report, log_path: Path, act_file: str) -> None:
    """Дописує fail/unknown/warning у journal/agent_errors.csv."""
    raise NotImplementedError
