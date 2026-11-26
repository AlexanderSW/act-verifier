"""Тести команди (T13, e2e): справжня точка входу, як її запускає агент-підготовник.

Кожен запуск — окремий процес `python -m act_verifier.cli` у тимчасовій робочій теці;
звіти й журнал пишуться лише туди. Еталонні фікстури — тільки читаються.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import ROOT, load_expected, scenario_dirs

HEADER = "date,act_file,code,check,status,expected,actual,found_by,resolution"
CODE = {"pass": 0, "fail": 1, "needs_review": 2}
CONTRACT = ROOT / "data/synthetic/contract_boq.xlsx"
PREV = [ROOT / "data/synthetic/act_01_2026-09.xlsx", ROOT / "data/synthetic/act_02_2026-10.xlsx"]


def run(args, cwd):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, "-m", "act_verifier.cli", *map(str, args)], cwd=cwd, env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def scenario_args(exp, out):
    a = ["--contract", ROOT / exp["inputs"]["contract"]]
    if exp["inputs"]["previous_acts"]:
        a += ["--previous", *[ROOT / p for p in exp["inputs"]["previous_acts"]]]
    return a + ["--act", ROOT / exp["inputs"]["act"], "--out", out]


def ok_args(out, act=ROOT / "tests/fixtures/ok_many/act_03.xlsx", contract=CONTRACT):
    return ["--contract", contract, "--previous", *PREV, "--act", act, "--out", out]


def listing(d: Path):
    return sorted(p.relative_to(d).as_posix() for p in d.rglob("*")) if d.exists() else []


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- кожен сценарій (AC-15)
@pytest.mark.parametrize("sdir", scenario_dirs(), ids=lambda p: p.name)
def test_scenario_outcome_code(sdir, tmp_path):
    exp = load_expected(sdir)
    out = tmp_path / "r"
    res = run(scenario_args(exp, out), tmp_path)
    if "expected_error" in exp:
        assert res.returncode == 3, res.stderr
        assert exp["expected_error"]["label"] in res.stderr
        assert res.stdout == "" and listing(out) == []
    else:
        assert res.returncode == CODE[exp["expected_verdict"]], res.stderr
        assert listing(out) == ["act_03_report.md", "act_03_report.xlsx"]
        assert res.stdout.startswith("## Блок доказів")
        assert f"Вердикт: {exp['expected_verdict']}." in res.stdout
        md = (out / "act_03_report.md").read_text(encoding="utf-8")
        assert md.rstrip().endswith(res.stdout.rstrip())
    assert not (tmp_path / "journal").exists()  # без --journal журнал не пишеться


def test_incomplete_previous_reason_reaches_stdout(tmp_path):
    exp = load_expected(ROOT / "tests/fixtures/incomplete_previous")
    res = run(scenario_args(exp, tmp_path / "r"), tmp_path)
    assert res.returncode == 2
    line = next(l for l in res.stdout.splitlines() if l.startswith("Не перевірено:"))
    assert "— C05 (подано попередніх актів: 1 з 2)" in line
    assert line.endswith("акт — C13 (подано попередніх актів: 1 з 2).")


# ---------------------------------------------------------------- незмінність входів (AC-13)
@pytest.mark.parametrize("scenario,code", [("ok_many", 0), ("combo_three_errors", 1), ("missing_price", 2),
                                           ("missing_label", 3)])
def test_inputs_are_byte_for_byte_unchanged(tmp_path, scenario, code):
    exp = load_expected(ROOT / "tests/fixtures" / scenario)
    paths = [ROOT / exp["inputs"]["contract"], *[ROOT / p for p in exp["inputs"]["previous_acts"]],
             ROOT / exp["inputs"]["act"]]
    before = {p: sha(p) for p in paths}
    assert run(scenario_args(exp, tmp_path / "r"), tmp_path).returncode == code
    assert {p: sha(p) for p in paths} == before


def test_report_location_on_an_input_is_refused(tmp_path):
    out = tmp_path / "r"
    out.mkdir()
    contract = out / "act_03_report.xlsx"
    shutil.copy(CONTRACT, contract)
    before = sha(contract)
    res = run(ok_args(out, contract=contract), tmp_path)
    assert res.returncode == 3 and "ніколи не пише" in res.stderr
    assert sha(contract) == before and listing(tmp_path) == ["r", "r/act_03_report.xlsx"]


def test_journal_location_on_the_act_in_other_case_is_refused(tmp_path):
    act = tmp_path / "in" / "act_03.xlsx"
    act.parent.mkdir()
    shutil.copy(ROOT / "tests/fixtures/ok_many/act_03.xlsx", act)
    before = sha(act)
    res = run(ok_args(tmp_path / "r", act=act) + ["--journal", tmp_path / "IN" / "Act_03.XLSX"], tmp_path)
    assert res.returncode == 3 and "ніколи не пише" in res.stderr
    assert sha(act) == before and listing(tmp_path) == ["in", "in/act_03.xlsx"]


# ---------------------------------------------------------------- помилки виклику (AC-06)
@pytest.mark.parametrize("args,needle", [
    (["--contract", CONTRACT, "--act", ROOT / "tests/fixtures/ok_many/act_03.xlsx", "--verbose"], "--verbose"),
    (["--act", ROOT / "tests/fixtures/ok_many/act_03.xlsx"], "--contract"),
    (["--contract", CONTRACT], "--act"),
    ([], "--contract"),
])
def test_invocation_errors_exit_3_never_2(tmp_path, args, needle):
    res = run(args + ["--out", tmp_path / "r"], tmp_path)
    assert res.returncode == 3 and needle in res.stderr
    assert res.stdout == "" and listing(tmp_path) == []


def test_unreadable_workbook_exits_3(tmp_path):
    bad = tmp_path / "act.xlsx"
    bad.write_text("це не книга Excel", encoding="utf-8")
    res = run(ok_args(tmp_path / "r", act=bad), tmp_path)
    assert res.returncode == 3 and "act.xlsx" in res.stderr
    assert listing(tmp_path) == ["act.xlsx"]


# ---------------------------------------------------------------- детермінованість і час (spec §6)
def test_two_runs_give_identical_reports(tmp_path):
    a, b = run(ok_args(tmp_path / "a"), tmp_path), run(ok_args(tmp_path / "b"), tmp_path)
    assert a.returncode == b.returncode == 0
    assert a.stdout == b.stdout
    for name in ("act_03_report.md", "act_03_report.xlsx"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes(), name


def test_ok_many_runs_within_5_seconds(tmp_path):
    start = time.perf_counter()
    res = run(ok_args(tmp_path / "r"), tmp_path)
    assert res.returncode == 0
    assert time.perf_counter() - start <= 5.0


# ---------------------------------------------------------------- журнал на вимогу (AC-14)
MISSING_PRICE = ROOT / "tests/fixtures/missing_price/act_03.xlsx"


def test_without_journal_option_no_journal_is_written(tmp_path):
    assert run(ok_args(tmp_path / "r", act=MISSING_PRICE), tmp_path).returncode == 2
    assert not (tmp_path / "journal").exists()


def test_journal_alone_goes_to_default_location_under_cwd(tmp_path):
    res = run(["--journal"] + ok_args(tmp_path / "r", act=MISSING_PRICE), tmp_path)
    assert res.returncode == 2
    lines = (tmp_path / "journal" / "agent_errors.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER and len(lines) == 2
    assert lines[1].split(",")[1:5] == ["act_03.xlsx", "5-2", "C11_required_values_present", "unknown"]
    assert lines[1].endswith(",act-verifier,")


def test_journal_with_location_appends_to_existing_file(tmp_path):
    j = tmp_path / "j.csv"
    j.write_text(HEADER + "\n2026-11-01,old.xlsx,1-1,C01_position_in_contract,fail,,,людина,\n", encoding="utf-8")
    combo = ROOT / "tests/fixtures/combo_three_errors/act_03.xlsx"
    assert run(ok_args(tmp_path / "r", act=combo) + ["--journal", j], tmp_path).returncode == 1
    lines = j.read_text(encoding="utf-8").splitlines()
    assert lines.count(HEADER) == 1 and len(lines) == 2 + 3


def test_journal_with_new_location_is_created_with_header(tmp_path):
    j = tmp_path / "logs" / "new.csv"
    assert run(ok_args(tmp_path / "r") + ["--journal", j], tmp_path).returncode == 0
    assert j.read_text(encoding="utf-8") == HEADER + "\n"


def test_tracked_journal_is_untouched():
    assert (ROOT / "journal/agent_errors.csv").read_text(encoding="utf-8") == HEADER + "\n"
