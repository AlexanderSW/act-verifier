import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def scenario_dirs():
    return sorted(p for p in FIXTURES.iterdir() if (p / "expected.json").exists())


def load_expected(d: Path) -> dict:
    return json.loads((d / "expected.json").read_text(encoding="utf-8"))


@pytest.fixture
def root() -> Path:
    return ROOT
