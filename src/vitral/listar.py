"""Lista os dias de um ano litúrgico com as chaves do Lecionário: ``python -m vitral.listar --ano 2026``."""

from __future__ import annotations

import argparse
import sys

from .data_loader import build_year
from .lectionary import Lectionary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ano", type=int, required=True, help="ano civil do 1º Domingo do Advento")
    ap.add_argument("--leituras", action="store_true", help="mostra também as referências")
    args = ap.parse_args(argv)
    lec = Lectionary.load() if args.leituras else None
    for d in build_year(args.ano):
        flag = " [pendente]" if d.pending else ""
        print(f"{d.date.isoformat()}  {d.color.value:<9} {d.name}{flag}")
        print(f"            chaves: {', '.join(d.lectionary_keys)}")
        if lec:
            for r in lec.for_day(d).readings:
                print(f"            {r.label}: {r.display or '—'} ({r.status})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
