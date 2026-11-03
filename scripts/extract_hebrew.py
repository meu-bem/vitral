"""Imprime o hebraico (OSHB, sem sinais de cantilação) dos versículos do Lecionário que ainda faltam traduzir.

Uso: python scripts/extract_hebrew.py Jer JER

O 1º argumento é o nome do arquivo em data/fontes/oshb/wlc/ (sem ``.xml``); o 2º, o código do livro em
data/biblia/. Saída: ``capítulo:versículo | texto``, com ``[partes>=N]`` onde o Lecionário cita letras.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vitral.translation import check_coverage  # noqa: E402

OSIS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
_MARKS = set(range(0x591, 0x5B0)) | {0x5BD, 0x5BF, 0x5C0, 0x5C3, 0x5C4, 0x5C5}


def clean(text: str) -> str:
    return "".join(ch for ch in text if ord(ch) not in _MARKS)


def main(osis_name: str, code: str) -> None:
    want = {(g.chapter, g.verse): g.parts_needed for g in check_coverage().gaps if g.book == code}
    tree = ET.parse(ROOT / "data" / "fontes" / "oshb" / "wlc" / f"{osis_name}.xml")
    for verse in tree.iter(f"{OSIS}verse"):
        osis_id = verse.get("osisID")
        if not osis_id:
            continue
        _, c, v = osis_id.split(".")
        if (int(c), int(v)) not in want:
            continue
        words = []
        for el in verse.iter():
            tag = el.tag.removeprefix(OSIS)
            if tag == "w":
                words.append(clean("".join(el.itertext())).replace("/", ""))
            elif tag == "seg" and el.text and el.get("type") != "x-maqqef":
                words.append(clean(el.text))
        need = want[(int(c), int(v))]
        print(f"{c}:{v}" + (f" [partes>={need}]" if need else "") + " | " + " ".join(words))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
