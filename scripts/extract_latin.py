"""Imprime o latim (Clementina, sem as notas da Glossa) dos versículos do Lecionário que ainda faltam traduzir.

Uso: python scripts/extract_latin.py 45-WISlatVUC.usfm WIS

O 1º argumento é o arquivo em data/fontes/clementina/; o 2º, o código do livro em data/biblia/. Saída:
``capítulo:versículo | texto``, com ``[partes>=N]`` onde o Lecionário cita letras. A numeração é a da Clementina:
onde ela difere da do Lecionário (Jt 13, Est 4,17), o versículo aparece como ``<<AUSENTE>>`` ou noutro número.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vitral.translation import check_coverage  # noqa: E402


def main(filename: str, code: str) -> None:
    want = {(g.chapter, g.verse): g.parts_needed for g in check_coverage().gaps if g.book == code}
    text = (ROOT / "data" / "fontes" / "clementina" / filename).read_text(encoding="utf8")
    text = re.sub(r"\\f \+.*?\\f\*", "", text, flags=re.S)  # notas da Glossa
    chapter = 0
    verses: dict[tuple[int, int], str] = {}
    for line in text.splitlines():
        if m := re.match(r"\\c (\d+)", line):
            chapter = int(m.group(1))
        elif m := re.match(r"\\v (\d+)(?:-\d+)? (.*)", line):
            verses[(chapter, int(m.group(1)))] = m.group(2).strip().strip("[]").strip()
    for key in sorted(want):
        need = want[key]
        print(f"{key[0]}:{key[1]}" + (f" [partes>={need}]" if need else "") + " | " + verses.get(key, "<<AUSENTE>>"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
