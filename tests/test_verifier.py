"""Еталонні сценарії: верифікатор має дати рівно ті знахідки, що в expected.json.

Поки src/ не реалізовано, тести позначаються xfail (NotImplementedError).
Коли реалізуєте — вони мають стати зеленими, а не просто перестати падати.
"""

import pytest

from conftest import ROOT, load_expected, scenario_dirs


def non_pass(report):
    return {(f.code, f.check, f.status.value) for f in report.findings if f.status.value != "pass"}


@pytest.mark.xfail(raises=NotImplementedError, reason="верифікатор ще не реалізовано", strict=False)
@pytest.mark.parametrize("sdir", scenario_dirs(), ids=lambda p: p.name)
def test_scenario(sdir):
    from act_verifier.checks import verify
    from act_verifier.loaders import load_act, load_contract

    exp = load_expected(sdir)
    contract = load_contract(ROOT / exp["inputs"]["contract"])
    previous = [load_act(ROOT / p) for p in exp["inputs"]["previous_acts"]]
    act = load_act(ROOT / exp["inputs"]["act"])

    report = verify(act, contract, previous)

    expected = {(f["code"], f["check"], f["status"]) for f in exp["expected_findings"]}
    assert non_pass(report) == expected
    assert report.verdict == exp["expected_verdict"]
