"""Revisão humana das traduções (data/biblia/): relatório por livro e marcação do que foi aprovado.

Uso:
  python scripts/revisao.py relatorio JER          # escreve dist/revisao/JER.md
  python scripts/revisao.py resumo                 # versículos revisados e pendentes, por livro
  python scripts/revisao.py aprovar JER 1:4 1:5    # marca versículos como revisados
  python scripts/revisao.py aprovar JER --todos    # marca o livro inteiro (só depois de revisá-lo)

O relatório traz primeiro os versículos com ``observacao`` (leituras alternativas, divergência do texto-base,
numeração), depois o livro inteiro, com o status de cada versículo. Só ``aprovar`` muda o status.
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BIBLIA = ROOT / "data" / "biblia"
OUT = ROOT / "dist" / "revisao"


def load(code: str) -> tuple[Path, dict]:
    path = BIBLIA / f"{code}.yaml"
    return path, yaml.safe_load(path.read_text(encoding="utf8"))


def key_order(key: str) -> tuple[int, int]:
    c, v = key.split(":")
    return int(c), int(v)


def relatorio(code: str) -> None:
    _, doc = load(code)
    verses = dict(sorted(doc["versiculos"].items(), key=lambda kv: key_order(kv[0])))
    pending = [k for k, v in verses.items() if v["status"] != "revisado"]
    lines = [f"# Revisão de {code} (texto-base: {doc['fonte']})", "",
             f"{len(verses) - len(pending)} de {len(verses)} versículos revisados; {len(pending)} pendentes.", ""]
    notes = [(k, v) for k, v in verses.items() if v.get("observacao") and not v["observacao"].startswith("partes:")]
    if notes:
        lines += ["## Pontos de atenção", ""]
        for k, v in notes:
            lines += [f"- **{k}** — {v['texto']}", f"  - {v['observacao']}"]
        lines.append("")
    lines += ["## Texto", ""]
    for k, v in verses.items():
        mark = "✓" if v["status"] == "revisado" else "·"
        title = f" _[{v['titulo']}]_" if v.get("titulo") else ""
        lines.append(f"{mark} **{k}**{title} {v['texto']}")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{code}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf8")
    print(f"{out.relative_to(ROOT)}: {len(pending)} pendentes, {len(notes)} pontos de atenção")


def resumo() -> None:
    for path in sorted(BIBLIA.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf8"))
        total = len(doc["versiculos"])
        done = sum(v["status"] == "revisado" for v in doc["versiculos"].values())
        print(f"{path.stem}: {done}/{total} revisados")


def aprovar(code: str, keys: list[str]) -> None:
    path, doc = load(code)
    verses = doc["versiculos"]
    targets = list(verses) if keys == ["--todos"] else keys
    missing = [k for k in targets if k not in verses]
    if missing:
        sys.exit(f"{code}: versículos inexistentes: {', '.join(missing)}")
    for k in targets:
        verses[k]["status"] = "revisado"
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf8")
    print(f"{code}: {len(targets)} versículos marcados como revisados")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["resumo"]
    if cmd == "relatorio":
        relatorio(args[0])
    elif cmd == "resumo":
        resumo()
    elif cmd == "aprovar":
        aprovar(args[0], args[1:])
    else:
        sys.exit(__doc__)
