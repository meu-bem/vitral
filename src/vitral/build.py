"""Gera os arquivos de um ano litúrgico: ``python -m vitral.build --ano 2026``.

Saída em ``dist/<ano>/``: PDF, EPUB, AZW3 (opcional), imagem do calendário (SVG e PNG)
e ``manifest.json`` com tamanhos e hashes. O build nunca falha por falta de dado:
dias incompletos saem só com o que está verificado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from .book.calendar_image import calendar_png, calendar_svg
from .book.model import build_book_year
from .book.render import write_azw3, write_epub, write_pdf
from .data_loader import ROOT

FORMATS = ("pdf", "epub", "azw3")


def file_info(path: Path) -> dict:
    data = path.read_bytes()
    return {"arquivo": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def build(year: int, out_dir: Path, formats: tuple[str, ...] = FORMATS) -> dict:
    book = build_book_year(year)
    out = out_dir / str(year)
    out.mkdir(parents=True, exist_ok=True)
    base = f"vitral-{year}-{year + 1}"
    produced: dict[str, Path] = {}
    (out / f"calendario-{year}-{year + 1}.svg").write_text(calendar_svg(book), encoding="utf-8")
    (out / f"calendario-{year}-{year + 1}.png").write_bytes(calendar_png(book))
    if "pdf" in formats:
        produced["pdf"] = write_pdf(book, out / f"{base}.pdf")
    if "epub" in formats or "azw3" in formats:
        produced["epub"] = write_epub(book, out / f"{base}.epub")
    if "azw3" in formats:
        azw3 = write_azw3(produced["epub"], out / f"{base}.azw3")
        if azw3:
            produced["azw3"] = azw3
    pending = sum(1 for bd in book.days if bd.pending)
    manifest = {
        "ano_liturgico": year,
        "titulo": book.title,
        "inicio": book.days[0].date.isoformat(),
        "fim": book.days[-1].date.isoformat(),
        "ciclo_dominical": book.sunday_cycle,
        "ciclo_ferial": book.weekday_cycle,
        "dias": len(book.days),
        "dias_com_lacuna": pending,
        "formatos": {fmt: file_info(p) for fmt, p in sorted(produced.items())},
        "calendario": {
            "svg": file_info(out / f"calendario-{year}-{year + 1}.svg"),
            "png": file_info(out / f"calendario-{year}-{year + 1}.png"),
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gera o livro de um ano litúrgico.")
    ap.add_argument("--ano", type=int, required=True, help="ano civil do 1º Domingo do Advento")
    ap.add_argument("--saida", type=Path, default=ROOT / "dist")
    ap.add_argument("--formatos", default=",".join(FORMATS), help="pdf,epub,azw3")
    args = ap.parse_args(argv)
    formats = tuple(f.strip() for f in args.formatos.split(",") if f.strip())
    manifest = build(args.ano, args.saida, formats)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
