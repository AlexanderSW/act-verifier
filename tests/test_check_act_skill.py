"""Узгодженість skill check-act з верифікатором (check-act-skill AC-10, AC-11; ADR-0003).

Skill читається як текст: заголовок — рядки `key: value` між `---` (без YAML-бібліотеки).
Жодного виклику моделі, мережі чи підпроцесу.
"""

import re
from pathlib import Path

import pytest

from act_verifier import cli
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


# ---------------------------------------------------------------- коди виходу й команда (AC-10)
# Очікуване береться з самого верифікатора: cli.EXIT, cli.EXIT_INPUT_ERROR, cli._parser(), stderr cli.main().
CODES_HEADING = "## Коди виходу"
RUN_PREFIX = ".venv/Scripts/act-verifier"
_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]*?)\s*\|")
_FENCE = re.compile(r"^```bash[ \t]*\n(.*?)^```", re.S | re.M)
_OPTION = re.compile(r"--[a-z][a-z-]*")


def code_map(text: str) -> dict[int, str]:
    """Рядки таблиці під «## Коди виходу»: {код: токен вердикту або значення}."""
    start = text.find(CODES_HEADING)
    assert start >= 0, f"у skill немає розділу «{CODES_HEADING}» з таблицею кодів"
    section = text[start + len(CODES_HEADING):]
    nxt = re.search(r"^## ", section, re.M)
    section = section[: nxt.start()] if nxt else section
    rows: dict[int, str] = {}
    for line in section.splitlines():
        if m := _ROW.match(line.strip()):
            code = int(m.group(1))
            assert code not in rows, f"код {code} у таблиці кодів skill повторюється"
            rows[code] = m.group(2).strip().strip("`")
    assert rows, f"таблиця під «{CODES_HEADING}» не містить жодного рядка з кодом"
    return rows


def run_block(text: str) -> str:
    blocks = [b for b in _FENCE.findall(text) if "act-verifier" in b]
    assert len(blocks) == 1, f"у skill має бути рівно один блок ```bash з act-verifier, знайдено {len(blocks)}"
    return blocks[0]


@pytest.fixture
def input_error_token(tmp_path, monkeypatch, capsys) -> str:
    """Фраза «перевірки не було» з реального stderr cli.main() на неіснуючому файлі."""
    monkeypatch.chdir(tmp_path)
    missing = tmp_path / "немає.xlsx"
    code = cli.main(["--contract", str(missing), "--act", str(missing), "--out", str(tmp_path / "out")])
    assert code == cli.EXIT_INPUT_ERROR, f"неіснуючий файл мав дати код {cli.EXIT_INPUT_ERROR}, а дав {code}"
    err = capsys.readouterr().err
    m = re.search(r"помилка вхідних даних, (.+?) — ", err)
    assert m, f"у stderr верифікатора не знайдено токен помилки вхідних даних: {err!r}"
    return m.group(1)


def check_verdict_codes(text: str) -> None:
    rows = code_map(text)
    for token, code in cli.EXIT.items():
        assert code in rows, f"у таблиці кодів skill немає коду {code} ({token})"
        assert rows[code] == token, f"код {code}: верифікатор — «{token}», skill — «{rows[code]}»"


def check_input_error_code(text: str, token: str) -> None:
    rows = code_map(text)
    code = cli.EXIT_INPUT_ERROR
    assert code in rows, f"у таблиці кодів skill немає коду {code} (помилка вхідних даних)"
    assert token in rows[code], f"код {code}: очікувано токен «{token}», у skill — «{rows[code]}»"


def check_no_extra_codes(text: str) -> None:
    known = set(cli.EXIT.values()) | {cli.EXIT_INPUT_ERROR}
    extra = sorted(set(code_map(text)) - known)
    assert not extra, f"таблиця кодів skill називає коди, яких верифікатор не має: {extra}"


def check_run_options(text: str) -> None:
    found = set(_OPTION.findall(run_block(text)))
    expected = {s for a in cli._parser()._actions for s in a.option_strings} - {"-h", "--help"}
    missing, extra = sorted(expected - found), sorted(found - expected)
    assert not missing, f"у блоці запуску skill бракує параметрів верифікатора: {missing}"
    assert not extra, f"блок запуску skill має параметри, яких верифікатор не приймає: {extra}"


def check_run_prefix(text: str) -> None:
    first = run_block(text).strip().splitlines()[0].strip()
    assert first.startswith(RUN_PREFIX + " "), f"команда в блоці запуску має починатися з «{RUN_PREFIX}»: {first!r}"


@pytest.fixture
def live_text() -> str:
    assert SKILL.is_file(), f"skill відсутній: файлу {SKILL} немає"
    return SKILL.read_text(encoding="utf-8")


def test_code_map_matches_verifier_verdicts(live_text):
    check_verdict_codes(live_text)


def test_code_map_input_error_row(live_text, input_error_token):
    check_input_error_code(live_text, input_error_token)


def test_code_map_has_no_extra_codes(live_text):
    check_no_extra_codes(live_text)


def test_run_block_options_match_verifier(live_text):
    check_run_options(live_text)


def test_run_block_starts_with_console_script(live_text):
    check_run_prefix(live_text)


def test_input_error_token_comes_from_verifier(input_error_token):
    # не копія в тесті: токен витягнуто з повідомлення верифікатора, тут лише перевірка, що він не порожній
    assert input_error_token.strip(), "токен помилки вхідних даних порожній"


# ---------------------------------------------------------------- охоронець називає розбіжність (AC-10)
_GOOD = f"""{CODES_HEADING}

| Код | Вердикт або значення |
|---|---|
| 0 | `pass` |
| 1 | `fail` |
| 2 | `needs_review` |
| 3 | перевірки не було |

## Запуск

Параметри поза блоком не читаються: --verbose.

```bash
{RUN_PREFIX} --contract <д> --previous <а1> --act <а> --out <т> [--journal]
```
"""

_ALL_CHECKS = [check_verdict_codes, check_no_extra_codes, check_run_options, check_run_prefix]


def test_drift_guard_accepts_good_skill(input_error_token):
    for check in _ALL_CHECKS:
        check(_GOOD)
    check_input_error_code(_GOOD, input_error_token)


@pytest.mark.parametrize(
    "old, new, check, expected",
    [
        ("| 2 | `needs_review` |", "| 2 | `fail` |", check_verdict_codes, "код 2"),
        ("| 1 | `fail` |\n", "", check_verdict_codes, "немає коду 1"),
        ("| 3 | перевірки не було |", "| 3 | помилка |", None, "код 3"),
        ("| 3 | перевірки не було |\n", "", None, "немає коду 3"),
        ("| 3 | перевірки не було |", "| 3 | перевірки не було |\n| 4 | інше |", check_no_extra_codes, r"\[4\]"),
        (" [--journal]", "", check_run_options, "--journal"),
        (" [--journal]", " [--journal] --verbose", check_run_options, "--verbose"),
        (f"{RUN_PREFIX} ", "cd x && act-verifier ", check_run_prefix, RUN_PREFIX),
        ("```\n", "```\n\n```bash\nact-verifier --act a\n```\n", check_run_options, "рівно один блок"),
    ],
    ids=["wrong-token", "missing-code", "wrong-input-token", "missing-input-code", "extra-code",
         "missing-option", "extra-option", "wrong-prefix", "two-blocks"],
)
def test_drift_guard_names_the_item(input_error_token, old, new, check, expected):
    text = _GOOD.replace(old, new, 1)
    assert text != _GOOD, "мутація не застосувалась"
    with pytest.raises(AssertionError, match=expected):
        if check is None:
            check_input_error_code(text, input_error_token)
        else:
            check(text)
