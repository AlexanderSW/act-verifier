"""CLI: act-verifier --contract ... --previous ... --act ... --out reports/ [--journal [PATH]]

Приклад:
    act-verifier \\
        --contract data/synthetic/contract_boq.xlsx \\
        --previous data/synthetic/act_01_2026-09.xlsx data/synthetic/act_02_2026-10.xlsx \\
        --act data/synthetic/act_03_2026-11.xlsx \\
        --out reports/

Код виходу (contracts/cli.md §3): 0 = pass, 1 = fail, 2 = needs_review,
3 = помилка вхідних даних (перевірки не було, звіт не пишеться).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from .checks import verify
from .loaders import load_act, load_contract
from .models import InputError
from .report import append_error_log, render_evidence, report_paths, write_excel, write_markdown

EXIT = {"pass": 0, "fail": 1, "needs_review": 2}
EXIT_INPUT_ERROR = 3
DEFAULT_JOURNAL = Path("journal/agent_errors.csv")


class _Parser(argparse.ArgumentParser):
    """argparse без власного виходу з кодом 2: 2 означає needs_review (cli.md §2)."""

    def error(self, message: str):
        """Текст argparse англійською не виводиться: лише українською, з назвою параметра (cli.md §3)."""
        raise InputError("invocation", label=_invocation_text(message))


_ARGPARSE = [
    (re.compile(r"the following arguments are required: (?P<opt>.+)"), "не задано обов'язкові параметри: {opt}"),
    (re.compile(r"unrecognized arguments: (?P<opt>.+)"), "невідомий параметр: {opt}"),
    (re.compile(r"argument (?P<opt>\S+?): expected (?:one|at least one) argument"), "параметр {opt} потребує значення"),
    (re.compile(r"argument (?P<opt>\S+?): .+"), "неправильне значення параметра {opt}"),
]


def _invocation_text(message: str) -> str:
    for pattern, text in _ARGPARSE:
        if m := pattern.fullmatch(message.strip()):
            return text.format(opt=m.group("opt"))
    return "неправильний виклик"


def _parser() -> _Parser:
    # allow_abbrev=False: «--contr» — невідомий параметр (cli.md:51), а не скорочення --contract
    p = _Parser(prog="act-verifier", description="Звірка акта КБ-2в / КБ-3 з договором", allow_abbrev=False)
    p.add_argument("--contract", type=Path, required=True, help="договірна ціна (.xlsx)")
    p.add_argument("--previous", type=Path, nargs="*", default=[], help="попередні акти (.xlsx)")
    p.add_argument("--act", type=Path, required=True, help="перевірюваний акт (.xlsx)")
    p.add_argument("--out", type=Path, default=Path("reports"), help="тека для звіту")
    p.add_argument("--journal", type=Path, nargs="?", const=DEFAULT_JOURNAL, default=None,
                   help="дописати fail/unknown/warning у журнал (типово journal/agent_errors.csv)")
    return p


def _key(path: Path) -> str:
    return os.path.normcase(os.path.realpath(path)).casefold()


def _same(a: Path, b: Path) -> bool:
    """Ті самі файли: повні шляхи рівні без урахування регістру (Windows, spec §1)."""
    return _key(a) == _key(b)


def _message(e: InputError) -> str:
    if e.kind == "invocation":
        return (f"помилка виклику: {e.label}. Обов'язкові параметри: --contract, --act; "
                "--previous, --out, --journal — необов'язкові.")
    if e.kind == "unreadable_file":
        return f"не вдалося прочитати файл {e.file}: файлу немає або це не книга Excel (.xlsx)."
    if e.kind == "overwrite_refused":
        return f"відмова: {e.label} збігається з вхідним файлом. Верифікатор ніколи не пише у свої вхідні файли."
    where = f"файл {e.file}"
    if e.kind == "missing_label":
        if e.label == e.sheet:
            return f"{where}: не знайдено аркуш «{e.label}»."
        return f"{where}, аркуш «{e.sheet}»: не знайдено підпис «{e.label}»."
    rows = ", ".join(map(str, e.rows))
    if e.kind == "duplicate_code":
        return (f"{where}, аркуш «{e.sheet}»: шифр «{e.label}» повторюється в рядках {rows}; "
                "не береться ні перший, ні останній рядок.")
    if e.label == e.sheet or not e.rows:
        return f"{where}: підпис «{e.label}» неоднозначний ({e.sheet}); перший збіг не використовується."
    return (f"{where}, аркуш «{e.sheet}»: підпис «{e.label}» знайдено в кількох рядках ({rows}); "
            "перший збіг не використовується.")


def _run(argv: list[str] | None) -> int:
    args = _parser().parse_args(argv)

    inputs = [args.contract, *args.previous, args.act]
    for path in inputs:
        if not path.is_file():
            raise InputError("unreadable_file", file=str(path))

    xlsx_path, md_path = report_paths(args.out, args.act)
    outputs = [xlsx_path, md_path] + ([args.journal] if args.journal is not None else [])
    for out in outputs:
        if any(_same(out, src) for src in inputs):
            raise InputError("overwrite_refused", label=str(out))

    contract = load_contract(args.contract)
    previous = [load_act(p, previous=True) for p in args.previous]
    act = load_act(args.act)

    report = verify(act, contract, previous)  # чиста функція, помилок вхідних даних не кидає

    write_excel(report, xlsx_path)
    write_markdown(report, md_path)
    if args.journal is not None:
        append_error_log(report, args.journal, act.file)
    sys.stdout.write(render_evidence(report))
    return EXIT[report.verdict]


def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    _utf8_streams()
    try:
        return _run(argv)
    except InputError as e:  # єдине місце, де ловиться InputError (ADR-0002); решта — баг
        print(f"act-verifier: помилка вхідних даних, перевірки не було — {_message(e)}", file=sys.stderr)
        return EXIT_INPUT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
