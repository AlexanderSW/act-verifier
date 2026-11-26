"""Юніт-тести cli.main (T12): параметри, захист від перезапису входів, коди виходу.

Звіти й журнал — лише в tmp_path; робоча тека — tmp_path (tracked journal не чіпається).
"""

import shutil
from pathlib import Path

import pytest

from act_verifier.cli import _same, main
from conftest import ROOT

CONTRACT = ROOT / "data/synthetic/contract_boq.xlsx"
PREV = [ROOT / "data/synthetic/act_01_2026-09.xlsx", ROOT / "data/synthetic/act_02_2026-10.xlsx"]
OK_MANY = ROOT / "tests/fixtures/ok_many/act_03.xlsx"


@pytest.fixture(autouse=True)
def _cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def argv(out, act=OK_MANY, contract=CONTRACT, previous=PREV, extra=()):
    a = []
    if contract is not None:
        a += ["--contract", str(contract)]
    if previous:
        a += ["--previous", *map(str, previous)]
    if act is not None:
        a += ["--act", str(act)]
    return a + ["--out", str(out), *extra]


def files(d: Path):
    return sorted(p.relative_to(d).as_posix() for p in d.rglob("*")) if d.exists() else []


# ---------------------------------------------------------------- щасливий шлях
def test_ok_many_exits_0_and_writes_both_reports(tmp_path, capsys):
    out = tmp_path / "r"
    assert main(argv(out)) == 0
    assert files(out) == ["act_03_report.md", "act_03_report.xlsx"]
    stdout = capsys.readouterr().out
    assert stdout.startswith("## Блок доказів") and "Вердикт: pass." in stdout
    assert (out / "act_03_report.md").read_text(encoding="utf-8").rstrip().endswith("Вердикт: pass.")


@pytest.mark.parametrize("scenario,code", [("combo_three_errors", 1), ("missing_price", 2), ("empty_act", 2)])
def test_outcome_codes(tmp_path, scenario, code):
    assert main(argv(tmp_path / "r", act=ROOT / f"tests/fixtures/{scenario}/act_03.xlsx")) == code


def test_previous_is_optional(tmp_path, capsys):
    # акт №3 без попередніх — не помилка виклику, а AC-11: C05/C13 unknown -> 2
    assert main(argv(tmp_path / "r", previous=())) == 2
    assert "подано попередніх актів: 0 з 2" in (tmp_path / "r/act_03_report.md").read_text(encoding="utf-8")


def test_missing_out_folder_is_created(tmp_path):
    out = tmp_path / "a" / "b"
    assert main(argv(out)) == 0 and (out / "act_03_report.xlsx").exists()


# ---------------------------------------------------------------- помилки виклику (AC-06)
@pytest.mark.parametrize("args,needle", [
    (dict(extra=["--fast"]), "--fast"),
    (dict(act=None), "--act"),
    (dict(contract=None), "--contract"),
])
def test_invocation_errors_exit_3_not_2(tmp_path, capsys, args, needle):
    out = tmp_path / "r"
    assert main(argv(out, **args)) == 3
    err = capsys.readouterr()
    assert needle in err.err and err.out == ""
    assert files(out) == []


@pytest.mark.parametrize("short", ["--contr", "--prev", "--o", "--jour"])
def test_abbreviated_option_is_an_invocation_error(tmp_path, capsys, short):
    """Скорочена назва — невідомий параметр (cli.md:51), а не --contract/--previous/--out/--journal."""
    out = tmp_path / "r"
    full = {"--contr": "--contract", "--prev": "--previous", "--o": "--out", "--jour": "--journal"}[short]
    a = [short if x == full else x for x in argv(out)] + ([short] if full == "--journal" else [])
    if full == "--out":
        a = argv(None) + [short, str(out)]
    assert main(a) == 3
    err = capsys.readouterr()
    assert short in err.err and err.out == ""
    assert files(out) == [] and not (tmp_path / "journal").exists()


def test_missing_input_file(tmp_path, capsys):
    assert main(argv(tmp_path / "r", act=tmp_path / "nope.xlsx")) == 3
    assert "nope.xlsx" in capsys.readouterr().err
    assert files(tmp_path / "r") == []


def test_unreadable_workbook(tmp_path, capsys):
    bad = tmp_path / "bad.xlsx"
    bad.write_text("not a workbook", encoding="utf-8")
    assert main(argv(tmp_path / "r", act=bad)) == 3
    assert files(tmp_path / "r") == []


def test_missing_label_scenario(tmp_path, capsys):
    assert main(argv(tmp_path / "r", act=ROOT / "tests/fixtures/missing_label/act_03.xlsx")) == 3
    err = capsys.readouterr().err
    assert "Разом без ПДВ" in err and "act_03.xlsx" in err and "КБ-2в" in err
    assert files(tmp_path / "r") == []


def test_ambiguous_label_names_rows(tmp_path, capsys):
    assert main(argv(tmp_path / "r", act=ROOT / "tests/fixtures/ambiguous_label/act_03.xlsx")) == 3
    err = capsys.readouterr().err
    assert "ПДВ" in err and "21" in err and "24" in err


# ---------------------------------------------------------------- захист входів (AC-13)
def test_journal_equal_to_act_in_other_case_is_refused(tmp_path, capsys):
    act = tmp_path / "in" / "act_03.xlsx"
    act.parent.mkdir()
    shutil.copy(OK_MANY, act)
    before = act.read_bytes()
    journal = tmp_path / "IN" / "ACT_03.XLSX"
    assert main(argv(tmp_path / "r", act=act, extra=["--journal", str(journal)])) == 3
    assert "ніколи не пише" in capsys.readouterr().err
    assert act.read_bytes() == before
    assert files(tmp_path / "r") == [] and files(tmp_path / "in") == ["act_03.xlsx"]


def test_report_path_equal_to_input_is_refused(tmp_path):
    out = tmp_path / "r"
    out.mkdir()
    contract = out / "act_03_report.xlsx"  # договір лежить там, куди мав би лягти звіт
    shutil.copy(CONTRACT, contract)
    before = contract.read_bytes()
    assert main(argv(out, contract=contract)) == 3
    assert contract.read_bytes() == before and files(out) == ["act_03_report.xlsx"]


def test_same_resolves_relative_and_case(tmp_path):
    (tmp_path / "x").mkdir()
    a = tmp_path / "x" / "f.xlsx"
    a.write_bytes(b"")
    assert _same(a, Path("x/../x/f.xlsx"))
    assert _same(a, tmp_path / "X" / "F.XLSX")
    assert not _same(a, tmp_path / "x" / "g.xlsx")


# ---------------------------------------------------------------- журнал (AC-14)
def test_no_journal_option_writes_no_journal(tmp_path):
    assert main(argv(tmp_path / "r", act=ROOT / "tests/fixtures/missing_price/act_03.xlsx")) == 2
    assert not (tmp_path / "journal").exists()


def test_journal_alone_before_another_option_uses_default_location(tmp_path):
    a = ["--journal", "--contract", str(CONTRACT), "--previous", *map(str, PREV),
         "--act", str(ROOT / "tests/fixtures/missing_price/act_03.xlsx"), "--out", str(tmp_path / "r")]
    assert main(a) == 2
    lines = (tmp_path / "journal/agent_errors.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "date,act_file,code,check,status,expected,actual,found_by,resolution"
    assert len(lines) == 2 and ",5-2,C11_required_values_present,unknown," in lines[1]


def test_journal_with_location(tmp_path):
    j = tmp_path / "logs" / "j.csv"
    assert main(argv(tmp_path / "r", act=ROOT / "tests/fixtures/combo_three_errors/act_03.xlsx",
                     extra=["--journal", str(j)])) == 1
    assert len(j.read_text(encoding="utf-8").splitlines()) == 1 + 3
