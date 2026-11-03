"""Acrescenta versículos a data/biblia/<LIVRO>.yaml a partir de um texto simples.

Uso: python scripts/add_translation.py MRK sblgnt lote.txt

Cada linha do lote: ``capítulo:versículo | texto`` (ou separado por TAB). Para um versículo com partes (letras),
separe as partes por `` || ``. Uma linha ``capítulo:versículo! | observação`` anexa uma observação.
Versículos já existentes são substituídos; o status é sempre ``ia-sem-revisao``.
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main(code: str, source: str, batch: Path) -> None:
    path = ROOT / "data" / "biblia" / f"{code}.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf8")) if path.exists() else {
        "livro": code, "fonte": source, "versiculos": {}}
    verses = doc["versiculos"]
    for line in batch.read_text(encoding="utf8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, text = line.split("\t", 1) if "\t" in line else line.split(" | ", 1)
        if key.endswith("!"):
            verses[key[:-1]]["observacao"] = text.strip()
            continue
        parts = [p.strip() for p in text.split(" || ")]
        entry = {"texto": " ".join(parts), "status": "ia-sem-revisao"}
        if len(parts) > 1:
            entry = {"texto": entry["texto"], "partes": parts, "status": entry["status"]}
        verses[key] = entry
    doc["versiculos"] = dict(sorted(verses.items(), key=lambda kv: tuple(map(int, kv[0].split(":")))))
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf8")
    print(f"{code}: {len(verses)} versículos")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
