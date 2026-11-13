"""Fórmulas fixas do livro e consulta de busca no YouTube.

Lê ``data/formulas.yaml`` (nomes dos livros, anúncio, abertura e conclusão das leituras) e
``data/inicios.yaml`` (exceções por leitura). Nada aqui é texto bíblico nem usa IA.
"""

from __future__ import annotations

import re
from functools import lru_cache

from .bible import BOOKS, book_by_code, parse_ref
from .data_loader import DATA_DIR, load_yaml

__all__ = ["formulas", "inicios", "start_key", "book_name", "announcement", "search_query", "slot_kind"]

_BR_TO_CODE = {b.br: b.code for b in BOOKS}


@lru_cache(maxsize=1)
def formulas() -> dict:
    return load_yaml(DATA_DIR / "formulas.yaml")


@lru_cache(maxsize=1)
def inicios() -> dict:
    """Exceções por leitura, indexadas pela referência como está no Lecionário (``Lc 14,25-33``)."""
    doc = load_yaml(DATA_DIR / "inicios.yaml") or {}
    return doc.get("inicios") or {}


def start_key(ref: str) -> str | None:
    """Chave de ``inicios.yaml`` para a leitura: onde ela começa ("Jo 5,17-30" -> "Jo 5,17"; "Lc 9,11b-17" -> "Lc 9,11b")."""
    try:
        parsed = parse_ref(ref, "br")
    except ValueError:
        return None
    seg = parsed.segments[0]
    if seg.v1 is None:
        return None
    return f"{book_by_code(parsed.book).br} {seg.c1},{seg.v1}{seg.l1}"


def slot_kind(slot: str) -> str:
    """``salmo``, ``evangelho`` ou ``leitura``."""
    if slot == "salmo" or slot.startswith("salmo_"):
        return "salmo"
    if slot in ("evangelho", "evangelho_procissao"):
        return "evangelho"
    return "leitura"


def book_name(code: str) -> str:
    return formulas()["livros"][code]["nome"]


def announcement(code: str) -> str | None:
    return formulas()["livros"][code].get("anuncio")


def search_query(display: str, slot: str) -> str | None:
    """Consulta do YouTube: só o livro por extenso e a referência. Salmo: só o número ("Salmo 89(90)").

    ``display`` é a referência como o livro a mostra ("Lc 14,25-33", "Sl 89(90),3-4.5-6")."""
    m = re.match(r"^(?:cf\.\s*)?([1-3]?[A-Za-zÀ-ú]+)\s+(.+)$", display.strip())
    if not m or m.group(1) not in _BR_TO_CODE:
        return None
    code, rest = _BR_TO_CODE[m.group(1)], m.group(2)
    if code == "PSA" or slot_kind(slot) == "salmo":
        return f"Salmo {rest.split(',')[0].strip()}"
    return f"{book_name(book_by_code(code).code)} {rest}"
