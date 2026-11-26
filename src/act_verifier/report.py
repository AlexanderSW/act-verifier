"""Вивід результату: Excel з розбіжностями + Markdown з блоком доказів.

Звіт — чиста функція від Report: жодних часових міток, тож два прогони на тих
самих даних дають однакові файли (spec §6, «Determinism»).
"""

from __future__ import annotations

import datetime as _dt
import io
import zipfile
from pathlib import Path

from openpyxl import Workbook

from .models import Report, Source, Status

SHEET = "Перевірки"
COLUMNS = ("шифр", "перевірка", "статус", "очікувано", "фактично", "джерело")
_FIXED_TIME = _dt.datetime(2000, 1, 1)  # властивості книги без поточного часу
_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


# ---------------------------------------------------------------- допоміжне
def report_paths(out_dir: Path, act_path: Path) -> tuple[Path, Path]:
    """<act-stem>_report.xlsx і <act-stem>_report.md у теці --out (рішення власника, cli.md OQ-A1)."""
    stem = Path(act_path).stem
    out_dir = Path(out_dir)
    return out_dir / f"{stem}_report.xlsx", out_dir / f"{stem}_report.md"


def compress_rows(rows) -> str:
    """[9, 10, 11, 18] -> «9–11, 18»."""
    nums = sorted(set(rows))
    if not nums:
        return "—"
    parts, start, prev = [], nums[0], nums[0]
    for n in nums[1:] + [None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        parts.append(str(start) if start == prev else f"{start}–{prev}")
        if n is not None:
            start = prev = n
    return ", ".join(parts)


def _plural(n: int, forms: tuple[str, str, str]) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return forms[1]
    return forms[2]


POSITION = ("позиція", "позиції", "позицій")
CHECK = ("перевірка", "перевірки", "перевірок")


def _short(check: str) -> str:
    return check.split("_", 1)[0]


def _sources_text(sources: list[Source]) -> str:
    """Групує джерела: файл -> аркуш -> рядки, як знайдено, у порядку появи."""
    if not sources:
        return "—"
    by_file: dict[str, dict[str, list[int]]] = {}
    for s in sources:
        rows = by_file.setdefault(s.file, {}).setdefault(s.sheet, [])
        if s.row is not None:
            rows.append(s.row)
    out = []
    for file, sheets in by_file.items():
        parts = [f"аркуш «{sheet}»" + (f", рядки {compress_rows(rows)}" if rows else "")
                 for sheet, rows in sheets.items()]
        out.append(f"{file}, " + "; ".join(parts))
    return "; ".join(out)


# ---------------------------------------------------------------- блок доказів
def render_evidence(report: Report) -> str:
    """Блок доказів: що перевірено, що ні, звідки числа (формат — docs/checks.md, cli.md §6.3)."""
    row_findings = [f for f in report.findings if f.code is not None]
    positions = {(f.code, f.sources[0] if f.sources else None) for f in row_findings}
    row_checks = {f.check for f in row_findings} | {s.check for s in report.skipped if s.code is not None}
    act_checks = {f.check for f in report.findings if f.code is None}
    n, k, m = len(positions), len(row_checks), len(act_checks)
    lines = [
        "## Блок доказів",
        f"Перевірено: {n} {_plural(n, POSITION)} × {k} {_plural(k, CHECK)} рядка, "
        f"{m} {_plural(m, CHECK)} підсумків (виконано перевірок: {len(report.findings)}).",
    ]

    groups: dict[tuple[str | None, str], list[str]] = {}
    for s in report.skipped:
        ids = groups.setdefault((s.code, s.reason), [])
        if _short(s.check) not in ids:
            ids.append(_short(s.check))
    if groups:
        items = [f"{code if code is not None else 'акт'} — {', '.join(ids)} ({reason})"
                 for (code, reason), ids in groups.items()]
        lines.append("Не перевірено: " + "; ".join(items) + ".")
    else:
        lines.append("Не перевірено: —")

    if report.skipped_rows:
        lines.append("Пропущено рядків без шифру: " + "; ".join(
            f"{file}, «{sheet}», рядки {compress_rows(rows)}" for file, sheet, rows in report.skipped_rows))

    lines += [
        "Джерела чисел:",
        "- договірні ціни й обсяги — " + _sources_text(report.inputs.get("contract", [])),
        "- попередні обсяги — " + _sources_text(report.inputs.get("previous", [])),
        "- перевірюваний акт — " + _sources_text(report.inputs.get("act", [])),
    ]

    counts = [(st.value, sum(f.status is st for f in report.findings))
              for st in (Status.FAIL, Status.UNKNOWN, Status.WARNING)]
    found = ", ".join(f"{c} {name}" for name, c in counts if c)
    lines.append(f"Розбіжностей: {found or 0}. Вердикт: {report.verdict}.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- Markdown
def _md(v: object) -> str:
    return "" if v is None else str(v).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: Report) -> str:
    act_files = sorted({s.file for s in report.inputs.get("act", [])})
    lines = [
        "# Звіт перевірки акта" + (f" {', '.join(act_files)}" if act_files else ""),
        "",
        f"Вердикт: **{report.verdict}**",
        "",
        "## Перевірки",
        "",
        "| Шифр | Перевірка | Статус | Очікувано | Фактично | Джерело | Примітка |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for f in report.findings:
        lines.append("| " + " | ".join(_md(v) for v in (
            f.code if f.code is not None else "акт", f.check, f.status.value, f.expected, f.actual,
            "; ".join(str(s) for s in f.sources), f.message)) + " |")
    lines.append("")
    return "\n".join(lines) + "\n" + render_evidence(report)


def write_markdown(report: Report, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- Excel
def write_excel(report: Report, path: Path) -> None:
    """Аркуш «Перевірки»: шифр | перевірка | статус | очікувано | фактично | джерело."""
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET
    wb.properties.created = wb.properties.modified = _FIXED_TIME
    rows = [COLUMNS] + [
        (f.code, f.check, f.status.value, f.expected, f.actual, "; ".join(str(s) for s in f.sources))
        for f in report.findings
    ]
    for r, values in enumerate(rows, 1):
        for c, v in enumerate(values, 1):
            if v is None:
                continue
            cell = ws.cell(r, c)
            cell.value = str(v)
            cell.data_type = "s"  # текст, ніколи формула («=…» у шифрі не виконується)
    for col, width in zip("ABCDEF", (10, 30, 10, 16, 16, 40)):
        ws.column_dimensions[col].width = width

    buf = io.BytesIO()
    wb.save(buf)
    # перепаковуємо zip з фіксованим часом членів, щоб два прогони дали ті самі байти
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as src, \
            zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            zi = zipfile.ZipInfo(info.filename, date_time=_ZIP_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            dst.writestr(zi, src.read(info.filename))


# ---------------------------------------------------------------- журнал
def append_error_log(report: Report, log_path: Path, act_file: str) -> None:
    """Дописує fail/unknown/warning у journal/agent_errors.csv."""
    raise NotImplementedError
