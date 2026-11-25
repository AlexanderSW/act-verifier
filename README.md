# act-verifier

Верифікатор актів виконаних робіт **КБ-2в / КБ-3**. Інструмент звіряє акт з договірною ціною та попередніми актами і видає звіт з розбіжностями та блоком доказів: що перевірено, що ні, звідки числа.

Агент готує акт, верифікатор його перевіряє, людина приймає рішення.

> Усі дані в репозиторії синтетичні. Компанії, договір і об'єкт вигадані.

## Швидкий старт

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/generate_fixtures.py   # перегенерувати data/ і tests/fixtures/
pytest                                # integrity-тести зелені, сценарії поки xfail
```

## Структура

```
act-verifier/
├── CLAUDE.md                     # правила для Claude Code в цьому репо
├── README.md
├── pyproject.toml
├── docs/
│   └── checks.md                 # каталог перевірок C01–C13, статуси, блок доказів
├── data/synthetic/               # демо-набір для CLI
│   ├── contract_boq.xlsx         # договірна ціна, 14 позицій
│   ├── act_01_2026-09.xlsx       # попередній акт №1
│   ├── act_02_2026-10.xlsx       # попередній акт №2
│   └── act_03_2026-11.xlsx       # поточний акт №3 (правильний)
├── scripts/
│   └── generate_fixtures.py      # єдине джерело правди для всіх синтетичних файлів
├── src/act_verifier/
│   ├── models.py                 # Decimal-моделі, Status, Finding, Report
│   ├── loaders.py                # читання xlsx            (TODO)
│   ├── checks.py                 # перевірки C01–C13        (TODO)
│   ├── report.py                 # Excel + блок доказів     (TODO)
│   ├── cli.py                    # act-verifier --contract … --act …  (TODO)
│   └── mcp_server.py             # етап 2: інструмент для Claude
├── tests/
│   ├── fixtures/<сценарій>/      # act_03.xlsx + expected.json (еталон)
│   ├── test_fixtures_integrity.py
│   └── test_verifier.py
└── journal/
    └── agent_errors.csv          # журнал помилок агентів
```

## Сценарії (tests/fixtures)

| Сценарій | Що зламано | Очікуваний вердикт |
| --- | --- | --- |
| ok_many | нічого, 11 позицій | pass |
| ok_single | нічого, 1 позиція | pass |
| empty_act | 0 позицій | needs_review |
| price_mismatch | ціна 3-2 не договірна | fail |
| volume_overrun | 2-1 більше залишку | fail |
| row_arithmetic | вартість 2-5 ≠ кількість × ціна | fail |
| subtotal_mismatch | «Разом» ≠ сума рядків | fail |
| vat_error | ПДВ 7% замість 20% | fail |
| kb3_mismatch | КБ-3 ≠ КБ-2в | fail |
| unknown_position | позиції 7-1 немає в договорі | fail |
| duplicate_position | 4-1 двічі | fail |
| unit_mismatch | «м» замість «м²» | fail |
| missing_price | порожня ціна 5-2 | needs_review |
| combo_three_errors | три помилки одночасно | fail |

Сценарії покривають методику з плану: нуль позицій, одна, багато, плюс навмисно зіпсовані акти.

## Формат вхідних файлів

**contract_boq.xlsx**, аркуш «Договірна ціна»: заголовки в рядку 6, дані з рядка 7.
Колонки: № з/п · Шифр · Найменування робіт · Од. виміру · Кількість за договором · Ціна за од. · Вартість.

**act_*.xlsx**, аркуш «КБ-2в»: шапка в рядках 1–6, заголовки в рядку 8, дані з рядка 9, далі рядки «Разом без ПДВ», «ПДВ 20%», «Всього з ПДВ» (значення в колонці G).
Аркуш «КБ-3»: мітки в колонці A, значення в колонці B, рядки 5–8.

Гроші округлюються до копійок (`Decimal`, ROUND_HALF_UP). Excel зберігає числа як float, тому при читанні: `Decimal(str(value))`.

## План реалізації

1. `loaders.py`: читати файли в моделі. Порожня клітинка — `None`, а не 0.
2. `checks.py`: C01–C13 по черзі, кожна з тестом зі сценаріїв.
3. `report.py`: Excel-звіт, блок доказів, журнал.
4. `cli.py`: зібрати все разом.
5. `mcp_server.py`: віддати `verify_act` як інструмент для Claude.
