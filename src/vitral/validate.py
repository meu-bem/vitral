"""Valida os dados e lista as lacunas: ``python -m vitral.validate`` (ou ``make validar``).

Erros (saída 1): arquivo fora do esquema, referência ilegível, id inexistente,
conteúdo humano sem campos obrigatórios ou com licença fora da lista.
Lacunas (não falham): dias com dado pendente ou sem leituras. O build continua.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from .bible import parse_ref
from .content import check_content
from .data_loader import DATA_DIR, ROOT, build_year, load_yaml
from .lectionary import Lectionary
from .liturgy import first_sunday_of_advent
from .schema import load_schema, validate

SCHEMAS = ROOT / "schemas"
FILES = [
    (DATA_DIR / "calendario" / "santos.yaml", "santos.schema.json"),
    (DATA_DIR / "calendario" / "regras-brasil.yaml", "regras.schema.json"),
    (DATA_DIR / "calendario" / "excecoes.yaml", "excecoes.schema.json"),
    (DATA_DIR / "links.yaml", "links.schema.json"),
]


def current_liturgical_year(today: date | None = None) -> int:
    today = today or date.today()
    return today.year if today >= first_sunday_of_advent(today.year) else today.year - 1


def all_day_keys(first: int = 2024, last: int = 2060) -> set[str]:
    keys: set[str] = set()
    for y in range(first, last + 1):
        for d in build_year(y):
            keys.update(d.lectionary_keys)
            for m in d.memorials:
                keys.update({f"{d.sunday_cycle}.santos.{m.id}", f"santos.{m.id}"})
    return keys


def check_data() -> list[str]:
    errors: list[str] = []
    for path, schema_name in FILES:
        if not path.exists():
            errors.append(f"{path.relative_to(ROOT)}: arquivo ausente")
            continue
        schema = load_schema(SCHEMAS / schema_name)
        errors += [f"{path.relative_to(ROOT)}: {e}" for e in validate(load_yaml(path), schema)]
    lec_schema = load_schema(SCHEMAS / "lecionario.schema.json")
    for path in sorted((DATA_DIR / "lecionario").glob("*.yaml")):
        doc = load_yaml(path)
        errors += [f"{path.relative_to(ROOT)}: {e}" for e in validate(doc, lec_schema)]
        for key, entry in (doc.get("leituras") or {}).items():
            for slot, item in entry.items():
                if not isinstance(item, dict):
                    continue
                for ref in [item.get("ref")] + list(item.get("alternativas", [])):
                    if not ref:
                        continue
                    try:
                        again = parse_ref(ref, "br").br()
                    except ValueError as exc:
                        errors.append(f"{path.name}: {key}.{slot}: {exc}")
                        continue
                    if again != ref:
                        errors.append(f"{path.name}: {key}.{slot}: '{ref}' deveria ser escrito '{again}'")
    santos = load_yaml(DATA_DIR / "calendario" / "santos.yaml")["celebracoes"]
    ids = Counter(e["id"] for e in santos)
    errors += [f"santos.yaml: id repetido: {i}" for i, n in ids.items() if n > 1]
    rules = load_yaml(DATA_DIR / "calendario" / "regras-brasil.yaml")["regras"]
    for sid in rules.get("transferencias_para_domingo", {}).get("valor", []):
        e = next((x for x in santos if x["id"] == sid), None)
        if e is None:
            errors.append(f"regras-brasil.yaml: celebração inexistente em santos.yaml: {sid}")
        elif e.get("transferencia") != "domingo-seguinte":
            errors.append(f"santos.yaml: {sid} deveria ter 'transferencia: domingo-seguinte'")
    exc = load_yaml(DATA_DIR / "calendario" / "excecoes.yaml") or {}
    for e in exc.get("excecoes") or []:
        if e["celebracao"] not in ids:
            errors.append(f"excecoes.yaml: celebração inexistente: {e['celebracao']}")
    return errors


def gaps(first: int, years: int) -> tuple[list[str], Counter]:
    lec = Lectionary.load()
    lines: list[str] = []
    totals: Counter = Counter()
    for y in range(first, first + years):
        for d in build_year(y):
            reasons = list(d.pending) + lec.for_day(d).pending
            totals["dias"] += 1
            if reasons:
                totals["dias com lacuna"] += 1
                lines.append(f"{d.date.isoformat()}  {d.name}: " + "; ".join(reasons))
    return lines, totals


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ano", type=int, help="primeiro ano litúrgico (padrão: o atual)")
    ap.add_argument("--anos", type=int, default=1, help="quantos anos listar (padrão: 1)")
    ap.add_argument("--relatorio", type=Path, help="grava a lista de lacunas neste arquivo")
    ap.add_argument("--so-erros", action="store_true", help="não lista lacunas")
    args = ap.parse_args(argv)

    errors = check_data()
    _, content_errors = check_content(known_keys=all_day_keys())
    errors += [f"conteudo/{e}" for e in content_errors]
    for e in errors:
        print(f"ERRO  {e}")

    if not args.so_erros:
        first = args.ano or current_liturgical_year()
        lines, totals = gaps(first, args.anos)
        print(f"\nLacunas de {first} a {first + args.anos - 1}: "
              f"{totals['dias com lacuna']} de {totals['dias']} dias têm dado pendente ou ausente.")
        for line in lines:
            print(f"  {line}")
        if args.relatorio:
            args.relatorio.parent.mkdir(parents=True, exist_ok=True)
            args.relatorio.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{len(errors)} erro(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
