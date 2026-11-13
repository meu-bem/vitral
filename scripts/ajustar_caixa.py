"""Põe em minúscula o versículo que continua a frase do anterior (regra de docs/TRADUCAO.md).

Uso: python scripts/ajustar_caixa.py            # mostra o que mudaria
     python scripts/ajustar_caixa.py --gravar   # grava em data/biblia/

Um versículo muda quando o anterior (no mesmo capítulo; nos salmos, nunca entre salmos) termina em vírgula,
ponto e vírgula ou sem pontuação e ele começa com maiúscula. Nomes próprios e começo de fala (aspas) ficam
como estão. ``partes[0]`` acompanha o ``texto``. É idempotente: rodar de novo não muda mais nada.
"""

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vitral.caixa import build_lexicon, continues_sentence, lower_first  # noqa: E402


def main(write: bool) -> None:
    docs = {p: yaml.safe_load(p.read_text(encoding="utf8")) for p in sorted((ROOT / "data" / "biblia").glob("*.yaml"))}
    lex = build_lexicon(v["texto"] for d in docs.values() for v in d["versiculos"].values())
    changed_total = 0
    kept: dict[str, int] = {}
    for path, doc in docs.items():
        verses = doc["versiculos"]
        keys = list(verses)
        changed = 0
        for prev, cur in zip(keys, keys[1:]):
            if doc["livro"] == "PSA" and prev.split(":")[0] != cur.split(":")[0]:
                continue
            if not continues_sentence(verses[prev]["texto"]):
                continue
            entry = verses[cur]
            new = lower_first(entry["texto"], lex)
            if new == entry["texto"]:
                first = entry["texto"].split()[0].strip("“‘(,.;:")
                if entry["texto"][:1].isupper():
                    kept[first] = kept.get(first, 0) + 1
                continue
            parts = entry.get("partes")
            idx = next(i for i, (a, b) in enumerate(zip(entry["texto"], new)) if a != b)
            if parts and parts[0] != entry.get("titulo") and parts[0][idx:idx + 1] == entry["texto"][idx]:
                parts[0] = parts[0][:idx] + new[idx] + parts[0][idx + 1:]
            entry["texto"] = new
            changed += 1
        if changed and write:
            path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf8")
        changed_total += changed
    verb = "alterados" if write else "a alterar"
    print(f"{changed_total} versículos {verb}")
    print("mantidos com maiúscula (nome próprio ou início de fala):",
          ", ".join(f"{w} ({n})" for w, n in sorted(kept.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    main(ap.parse_args().gravar)
