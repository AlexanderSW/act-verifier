"""Узгодженість skill check-act з верифікатором (check-act-skill AC-10, AC-11; ADR-0003).

Skill читається як текст: заголовок — рядки `key: value` між `---` (без YAML-бібліотеки).
Жодного виклику моделі, мережі чи підпроцесу.
"""

from pathlib import Path

import pytest

from conftest import ROOT

SKILL = ROOT / ".claude" / "skills" / "check-act" / "SKILL.md"
SKILL_NAME = "check-act"


def read_header(path: Path) -> dict[str, str]:
    """Заголовок skill як {ключ: значення}; AssertionError називає, що саме не так."""
    assert path.is_file(), f"skill відсутній: файлу {path} немає"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"заголовок skill не читається: {path} не починається рядком «---»"
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        raise AssertionError(f"заголовок skill не читається: блок «---» у {path} не закрито") from None
    header = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        assert sep, f"заголовок skill не читається: рядок без «:» — {line!r}"
        header[key.strip()] = value.strip()
    return header


def check_identity(path: Path) -> None:
    header = read_header(path)
    name = header.get("name", "")
    assert name == SKILL_NAME, f"неправильна назва skill: очікувано «{SKILL_NAME}», фактично «{name}»"
    assert header.get("description", "").strip(), "опис skill порожній: поле description не заповнене"


# ---------------------------------------------------------------- живий skill (AC-11)
def test_live_skill_exists():
    assert SKILL.is_file(), f"skill відсутній: файлу {SKILL} немає"


def test_live_skill_identity():
    check_identity(SKILL)


# ---------------------------------------------------------------- охоронець називає випадок (AC-11)
def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "SKILL.md"
    p.write_text(text, encoding="utf-8")
    return p


@pytest.mark.parametrize(
    "text, expected",
    [
        (None, "skill відсутній"),
        ("# без заголовка\n", "заголовок skill не читається"),
        ("---\nname: check-act\ndescription: опис\n", "заголовок skill не читається"),
        ("---\nname: check_act\ndescription: опис\n---\n", "неправильна назва skill"),
        ("---\nname: check-act\ndescription:   \n---\n", "опис skill порожній"),
    ],
    ids=["missing", "no-header", "unclosed-header", "wrong-name", "empty-description"],
)
def test_identity_guard_names_the_case(tmp_path, text, expected):
    path = tmp_path / "SKILL.md" if text is None else _write(tmp_path, text)
    with pytest.raises(AssertionError, match=expected):
        check_identity(path)


def test_description_with_colon_kept_whole(tmp_path):
    path = _write(tmp_path, "---\nname: check-act\ndescription: Перевірити акт: КБ-2в / КБ-3\n---\n")
    assert read_header(path)["description"] == "Перевірити акт: КБ-2в / КБ-3"
