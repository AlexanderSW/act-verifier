"""Генератор синтетичних даних для act-verifier.

Створює:
  data/synthetic/contract_boq.xlsx      — договірна ціна (14 позицій ОВіК / чисті приміщення / BMS)
  data/synthetic/act_01_2026-09.xlsx    — попередній акт №1 (КБ-2в + КБ-3)
  data/synthetic/act_02_2026-10.xlsx    — попередній акт №2
  data/synthetic/act_03_2026-11.xlsx    — поточний акт №3, правильний (для демо)
  tests/fixtures/<scenario>/act_03.xlsx + expected.json — еталонні сценарії

Усі дані вигадані. Назви компаній умовні. Запуск: python scripts/generate_fixtures.py
Генерація детермінована: повторний запуск дає ті самі числа.
"""

from __future__ import annotations

import copy
import json
import shutil
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "synthetic"
FIXTURES = ROOT / "tests" / "fixtures"

VAT_RATE = Decimal("0.20")
CENT = Decimal("0.01")

CUSTOMER = "Замовник: ТОВ «Альфа-Мед» (умовна назва)"
CONTRACTOR = "Генпідрядник: ТОВ «Будмонтаж-Тест» (умовна назва)"
CONTRACT = "Договір підряду № 17/26 від 02.03.2026"
OBJECT = "Об'єкт: Медичний корпус — ОВіК, чисті приміщення, BMS (синтетичні дані)"

ACT_HEADERS = [
    "№ з/п",
    "Шифр позиції за договором",
    "Найменування робіт",
    "Од. виміру",
    "Кількість",
    "Ціна за од., грн без ПДВ",
    "Вартість, грн без ПДВ",
]
HEADER_ROW = 8  # рядок заголовків таблиці в КБ-2в
CONTRACT_HEADER_ROW = 6


def money(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class Position:
    code: str
    name: str
    unit: str
    qty: Decimal
    price: Decimal

    @property
    def amount(self) -> Decimal:
        return money(self.qty * self.price)


D = Decimal
CONTRACT_POSITIONS = [
    Position("2-1", "Монтаж повітроводів з оцинкованої сталі, δ=0,7 мм", "м²", D("1200"), D("485.00")),
    Position("2-2", "Ізоляція повітроводів мінераловатними матами 50 мм", "м²", D("950"), D("312.40")),
    Position("2-3", "Монтаж припливно-витяжної установки до 5000 м³/год", "шт", D("4"), D("38500.00")),
    Position("2-4", "Монтаж канальних вентиляторів", "шт", D("18"), D("2150.00")),
    Position("2-5", "Встановлення вентиляційних решіток і дифузорів", "шт", D("260"), D("186.50")),
    Position("3-1", "Прокладання трубопроводів холодопостачання Ø28 мм", "м", D("640"), D("420.00")),
    Position("3-2", "Монтаж касетних фанкойлів", "шт", D("36"), D("4800.00")),
    Position("3-3", "Гідравлічне випробування трубопроводів", "м", D("640"), D("35.20")),
    Position("4-1", "Монтаж HEPA-фільтрів чистих приміщень", "шт", D("42"), D("3650.00")),
    Position("4-2", "Монтаж стельових панелей чистих приміщень", "м²", D("380"), D("1240.00")),
    Position("5-1", "Прокладання кабелю BMS КВВГ 4×1,5", "м", D("2100"), D("64.80")),
    Position("5-2", "Монтаж контролерів BMS", "шт", D("12"), D("9200.00")),
    Position("5-3", "Пусконалагодження системи BMS", "компл", D("1"), D("145000.00")),
    Position("6-1", "Демонтаж існуючих повітроводів", "м²", D("300"), D("98.00")),
]
BY_CODE = {p.code: p for p in CONTRACT_POSITIONS}

# Виконані обсяги по актах: code -> qty
ACT_01 = {"6-1": D("300"), "2-1": D("410.5"), "2-2": D("180"), "3-1": D("220"), "5-1": D("650")}
ACT_02 = {"2-1": D("455"), "2-2": D("390"), "2-3": D("2"), "2-4": D("8"), "3-1": D("260"),
          "3-3": D("220"), "5-1": D("820"), "5-2": D("4")}
# Поточний акт №3 — у межах залишків
ACT_03 = {"2-1": D("300"), "2-2": D("310"), "2-3": D("2"), "2-4": D("10"), "2-5": D("140"),
          "3-1": D("150"), "3-2": D("20"), "3-3": D("380"), "4-1": D("18"), "5-1": D("540"),
          "5-2": D("6")}


@dataclass
class ActRow:
    code: str
    name: str
    unit: str
    qty: Decimal | None
    price: Decimal | None
    amount: Decimal | None


@dataclass
class Act:
    number: int
    period: str  # "листопад 2026"
    rows: list[ActRow]
    subtotal: Decimal
    vat: Decimal
    total: Decimal
    kb3_period_total: Decimal
    kb3_cumulative_total: Decimal


def rows_from(volumes: dict[str, Decimal]) -> list[ActRow]:
    out = []
    for p in CONTRACT_POSITIONS:  # порядок як у договорі
        if p.code in volumes:
            q = volumes[p.code]
            out.append(ActRow(p.code, p.name, p.unit, q, p.price, money(q * p.price)))
    return out


def finalize(number: int, period: str, rows: list[ActRow], prev_cumulative: Decimal) -> Act:
    """Рахує підсумки з того, що написано в рядках (як зробив би акуратний кошторисник)."""
    subtotal = money(sum((r.amount or D(0) for r in rows), D(0)))
    vat = money(subtotal * VAT_RATE)
    total = subtotal + vat
    return Act(number, period, rows, subtotal, vat, total, total, prev_cumulative + total)


# ---------------------------------------------------------------- Excel writers
THIN = Side(style="thin")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
NUM = "#,##0.00"
QTY = "#,##0.###"


def _set_widths(ws, widths):
    for col, w in zip("ABCDEFG", widths):
        ws.column_dimensions[col].width = w
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def write_contract(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Договірна ціна"
    ws["A1"] = "ДОГОВІРНА ЦІНА (відомість обсягів і цін)"
    ws["A1"].font = Font(bold=True, size=12)
    ws["A2"] = CONTRACT
    ws["A3"] = OBJECT
    ws["A4"] = "Ціни в гривнях без ПДВ. Синтетичні дані для навчального проєкту."
    headers = ["№ з/п", "Шифр", "Найменування робіт", "Од. виміру",
               "Кількість за договором", "Ціна за од., грн без ПДВ", "Вартість, грн без ПДВ"]
    for i, h in enumerate(headers, 1):
        c = ws.cell(CONTRACT_HEADER_ROW, i, h)
        c.font = Font(bold=True)
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BOX
    r = CONTRACT_HEADER_ROW + 1
    total = D(0)
    for n, p in enumerate(CONTRACT_POSITIONS, 1):
        vals = [n, p.code, p.name, p.unit, float(p.qty), float(p.price), float(p.amount)]
        for i, v in enumerate(vals, 1):
            c = ws.cell(r, i, v)
            c.border = BOX
        ws.cell(r, 5).number_format = QTY
        ws.cell(r, 6).number_format = NUM
        ws.cell(r, 7).number_format = NUM
        total += p.amount
        r += 1
    ws.cell(r, 3, "Разом без ПДВ").font = Font(bold=True)
    ws.cell(r, 7, float(total)).number_format = NUM
    vat = money(total * VAT_RATE)
    ws.cell(r + 1, 3, "ПДВ 20%")
    ws.cell(r + 1, 7, float(vat)).number_format = NUM
    ws.cell(r + 2, 3, "Всього з ПДВ").font = Font(bold=True)
    ws.cell(r + 2, 7, float(total + vat)).number_format = NUM
    _set_widths(ws, [7, 10, 55, 10, 14, 16, 18])
    wb.save(path)


def _num(v):
    return None if v is None else float(v)


def write_act(path: Path, act: Act) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "КБ-2в"
    ws["A1"] = "АКТ ПРИЙМАННЯ ВИКОНАНИХ БУДІВЕЛЬНИХ РОБІТ (типова форма № КБ-2в)"
    ws["A1"].font = Font(bold=True, size=12)
    ws["A2"] = f"Акт № {act.number} за {act.period} р."
    ws["A3"] = CUSTOMER
    ws["A4"] = CONTRACTOR
    ws["A5"] = CONTRACT
    ws["A6"] = OBJECT
    for i, h in enumerate(ACT_HEADERS, 1):
        c = ws.cell(HEADER_ROW, i, h)
        c.font = Font(bold=True)
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BOX
    r = HEADER_ROW + 1
    for n, row in enumerate(act.rows, 1):
        vals = [n, row.code, row.name, row.unit, _num(row.qty), _num(row.price), _num(row.amount)]
        for i, v in enumerate(vals, 1):
            ws.cell(r, i, v).border = BOX
        ws.cell(r, 5).number_format = QTY
        ws.cell(r, 6).number_format = NUM
        ws.cell(r, 7).number_format = NUM
        r += 1
    ws.cell(r, 3, "Разом без ПДВ").font = Font(bold=True)
    ws.cell(r, 7, float(act.subtotal)).number_format = NUM
    ws.cell(r + 1, 3, "ПДВ 20%")
    ws.cell(r + 1, 7, float(act.vat)).number_format = NUM
    ws.cell(r + 2, 3, "Всього з ПДВ").font = Font(bold=True)
    ws.cell(r + 2, 7, float(act.total)).number_format = NUM
    _set_widths(ws, [7, 12, 55, 10, 12, 16, 18])

    kb3 = wb.create_sheet("КБ-3")
    kb3["A1"] = "ДОВІДКА ПРО ВАРТІСТЬ ВИКОНАНИХ БУДІВЕЛЬНИХ РОБІТ ТА ВИТРАТ (типова форма № КБ-3)"
    kb3["A1"].font = Font(bold=True, size=12)
    kb3["A2"] = f"За {act.period} р. до акта № {act.number}"
    kb3["A3"] = CONTRACT
    items = [
        ("Вартість робіт за звітний період, грн без ПДВ", act.subtotal),
        ("ПДВ 20%, грн", act.vat),
        ("Всього за звітний період, грн з ПДВ", act.kb3_period_total),
        ("З початку виконання робіт, грн з ПДВ", act.kb3_cumulative_total),
    ]
    for i, (label, value) in enumerate(items, 5):
        kb3.cell(i, 1, label)
        kb3.cell(i, 2, float(value)).number_format = NUM
    kb3.column_dimensions["A"].width = 50
    kb3.column_dimensions["B"].width = 18
    wb.save(path)


# ---------------------------------------------------------------- scenarios
def base_act3(prev_cum: Decimal) -> Act:
    return finalize(3, "листопад 2026", rows_from(ACT_03), prev_cum)


def find(rows, code):
    return next(r for r in rows if r.code == code)


def scenarios(prev_cum: Decimal):
    """Повертає список (name, description, Act, expected_findings).

    expected_findings — лише перевірки зі статусом, відмінним від pass.
    Порожній список = акт має пройти всі перевірки.
    """
    out = []

    # 1. Правильний акт, багато позицій
    out.append(("ok_many", "Правильний акт, 11 позицій. Усі перевірки pass.",
                base_act3(prev_cum), []))

    # 2. Одна позиція
    rows = rows_from({"4-1": D("10")})
    out.append(("ok_single", "Правильний акт з однією позицією.",
                finalize(3, "листопад 2026", rows, prev_cum), []))

    # 3. Нуль позицій
    out.append(("empty_act", "Акт без жодної позиції. Не помилка арифметики, але акт не можна приймати мовчки.",
                finalize(3, "листопад 2026", [], prev_cum),
                [{"code": None, "check": "C12_act_not_empty", "status": "warning"}]))

    # 4. Ціна не збігається з договірною
    act = base_act3(prev_cum)
    r = find(act.rows, "3-2")
    r.price = D("5100.00")
    r.amount = money(r.qty * r.price)
    act = finalize(3, act.period, act.rows, prev_cum)
    out.append(("price_mismatch", "Позиція 3-2: ціна 5100,00 замість договірних 4800,00; вартість і підсумки перераховані під неправильну ціну.",
                act, [{"code": "3-2", "check": "C03_price_matches_contract", "status": "fail"}]))

    # 5. Перевищення залишку обсягу
    act = base_act3(prev_cum)
    r = find(act.rows, "2-1")  # договір 1200, вже 410.5+455=865.5, залишок 334.5
    r.qty = D("350")
    r.amount = money(r.qty * r.price)
    act = finalize(3, act.period, act.rows, prev_cum)
    out.append(("volume_overrun", "Позиція 2-1: 350 м² при залишку 334,5 м² (1200 − 410,5 − 455).",
                act, [{"code": "2-1", "check": "C05_within_remaining_volume", "status": "fail"}]))

    # 6. Арифметика рядка
    act = base_act3(prev_cum)
    r = find(act.rows, "2-5")
    r.amount = r.amount + D("1865.00")  # як ніби 150 шт замість 140
    act = finalize(3, act.period, act.rows, prev_cum)
    out.append(("row_arithmetic", "Позиція 2-5: вартість не дорівнює кількість × ціна (різниця 1865,00). Підсумок рахується з написаних вартостей.",
                act, [{"code": "2-5", "check": "C04_amount_arithmetic", "status": "fail"}]))

    # 7. Підсумок «Разом» неправильний
    act = base_act3(prev_cum)
    act.subtotal = act.subtotal - D("10000.00")
    act.vat = money(act.subtotal * VAT_RATE)
    act.total = act.subtotal + act.vat
    act.kb3_period_total = act.total
    act.kb3_cumulative_total = prev_cum + act.total
    out.append(("subtotal_mismatch", "«Разом без ПДВ» на 10 000,00 менше за суму рядків. ПДВ, всього і КБ-3 узгоджені з неправильним підсумком.",
                act, [{"code": None, "check": "C07_subtotal", "status": "fail"}]))

    # 8. ПДВ неправильний
    act = base_act3(prev_cum)
    act.vat = money(act.subtotal * D("0.07"))
    act.total = act.subtotal + act.vat
    act.kb3_period_total = act.total
    act.kb3_cumulative_total = prev_cum + act.total
    out.append(("vat_error", "ПДВ пораховано за ставкою 7% замість 20%.",
                act, [{"code": None, "check": "C08_vat", "status": "fail"}]))

    # 9. КБ-3 не збігається з КБ-2в
    act = base_act3(prev_cum)
    act.kb3_period_total = act.total + D("2400.00")
    act.kb3_cumulative_total = prev_cum + act.total  # накопичувальний правильний
    out.append(("kb3_mismatch", "КБ-3 «Всього за звітний період» на 2400,00 більше за КБ-2в «Всього з ПДВ».",
                act, [{"code": None, "check": "C10_kb3_matches_kb2v", "status": "fail"}]))

    # 10. Позиції немає в договорі
    act = base_act3(prev_cum)
    act.rows.append(ActRow("7-1", "Монтаж зволожувача повітря (додаткові роботи)", "шт", D("2"),
                           D("12500.00"), D("25000.00")))
    act = finalize(3, act.period, act.rows, prev_cum)
    out.append(("unknown_position", "Додано позицію 7-1, якої немає в договорі. Перевірки ціни, одиниці й залишку для неї не виконуються.",
                act, [{"code": "7-1", "check": "C01_position_in_contract", "status": "fail"}]))

    # 11. Дубль позиції
    act = base_act3(prev_cum)
    dup = copy.deepcopy(find(act.rows, "4-1"))
    dup.qty = D("4")
    dup.amount = money(dup.qty * dup.price)
    act.rows.append(dup)  # 18 + 4 = 22 ≤ 42, залишок не перевищено
    act = finalize(3, act.period, act.rows, prev_cum)
    out.append(("duplicate_position", "Позиція 4-1 двічі в акті (18 і 4 шт). Сумарно в межах залишку, але дубль треба показати людині.",
                act, [{"code": "4-1", "check": "C06_no_duplicate_positions", "status": "fail"}]))

    # 12. Одиниця виміру
    act = base_act3(prev_cum)
    find(act.rows, "2-2").unit = "м"
    out.append(("unit_mismatch", "Позиція 2-2: одиниця «м» замість договірної «м²».",
                act, [{"code": "2-2", "check": "C02_unit_matches", "status": "fail"}]))

    # 13. Порожня ціна
    act = base_act3(prev_cum)
    find(act.rows, "5-2").price = None  # вартість лишилась
    out.append(("missing_price", "Позиція 5-2: клітинка ціни порожня, вартість заповнена. Очікуємо unknown, а не pass і не вигадану ціну.",
                act, [{"code": "5-2", "check": "C11_required_values_present", "status": "unknown"}]))

    # 14. Кілька помилок разом
    act = base_act3(prev_cum)
    r = find(act.rows, "3-2"); r.price = D("5100.00"); r.amount = money(r.qty * r.price)
    r = find(act.rows, "2-1"); r.qty = D("350"); r.amount = money(r.qty * r.price)
    act = finalize(3, act.period, act.rows, prev_cum)
    act.kb3_period_total = act.total + D("2400.00")
    out.append(("combo_three_errors", "Три помилки одночасно: ціна 3-2, залишок 2-1, КБ-3. Верифікатор має знайти всі три, а не зупинитися на першій.",
                act, [
                    {"code": "3-2", "check": "C03_price_matches_contract", "status": "fail"},
                    {"code": "2-1", "check": "C05_within_remaining_volume", "status": "fail"},
                    {"code": None, "check": "C10_kb3_matches_kb2v", "status": "fail"},
                ]))
    return out


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    if FIXTURES.exists():
        shutil.rmtree(FIXTURES)
    FIXTURES.mkdir(parents=True)

    write_contract(DATA / "contract_boq.xlsx")

    act1 = finalize(1, "вересень 2026", rows_from(ACT_01), D(0))
    act2 = finalize(2, "жовтень 2026", rows_from(ACT_02), act1.kb3_cumulative_total)
    write_act(DATA / "act_01_2026-09.xlsx", act1)
    write_act(DATA / "act_02_2026-10.xlsx", act2)
    prev_cum = act2.kb3_cumulative_total
    write_act(DATA / "act_03_2026-11.xlsx", base_act3(prev_cum))

    index = []
    for name, desc, act, findings in scenarios(prev_cum):
        d = FIXTURES / name
        d.mkdir()
        write_act(d / "act_03.xlsx", act)
        expected = {
            "scenario": name,
            "description": desc,
            "inputs": {
                "contract": "data/synthetic/contract_boq.xlsx",
                "previous_acts": ["data/synthetic/act_01_2026-09.xlsx",
                                  "data/synthetic/act_02_2026-10.xlsx"],
                "act": f"tests/fixtures/{name}/act_03.xlsx",
            },
            "expected_verdict": (
                "pass" if not findings
                else "fail" if any(f["status"] == "fail" for f in findings)
                else "needs_review"
            ),
            "expected_findings": findings,
        }
        (d / "expected.json").write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
        index.append((name, expected["expected_verdict"], len(findings)))

    print("data/synthetic:", ", ".join(sorted(p.name for p in DATA.glob("*.xlsx"))))
    for name, verdict, n in index:
        print(f"  {name:<22} verdict={verdict:<13} findings={n}")


if __name__ == "__main__":
    main()
