import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
TRACKED_JOURNAL = ROOT / "journal" / "agent_errors.csv"


def _fingerprint(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


@pytest.fixture(scope="session", autouse=True)
def tracked_journal_unchanged():
    """Тести ніколи не пишуть у відстежуваний журнал (AC-14): відбиток до і після сесії.

    Вміст журналу не перевіряється — справжні записи в ньому законні.
    """
    before = _fingerprint(TRACKED_JOURNAL)
    yield
    assert _fingerprint(TRACKED_JOURNAL) == before, "тести змінили journal/agent_errors.csv"


def scenario_dirs():
    return sorted(p for p in FIXTURES.iterdir() if (p / "expected.json").exists())


def load_expected(d: Path) -> dict:
    return json.loads((d / "expected.json").read_text(encoding="utf-8"))


@pytest.fixture
def root() -> Path:
    return ROOT
