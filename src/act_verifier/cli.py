"""CLI: act-verifier --contract ... --previous ... --act ... --out reports/

Приклад:
    act-verifier \\
        --contract data/synthetic/contract_boq.xlsx \\
        --previous data/synthetic/act_01_2026-09.xlsx data/synthetic/act_02_2026-10.xlsx \\
        --act data/synthetic/act_03_2026-11.xlsx \\
        --out reports/
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="act-verifier", description="Звірка акта КБ-2в / КБ-3 з договором")
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--previous", type=Path, nargs="*", default=[])
    p.add_argument("--act", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("reports"))
    args = p.parse_args(argv)
    # TODO: load_contract -> load_act -> verify -> write_excel + render_evidence + append_error_log
    # Код виходу: 0 = pass, 1 = fail, 2 = needs_review
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
