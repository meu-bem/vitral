"""Texto das leituras: junta a referência do Lecionário com a tradução de ``data/biblia/``.

Os versículos citados com letras (``16b``, ``4ac``, ``6c-8a``) trazem só as partes pedidas, quando o versículo
tem ``partes``; sem ``partes``, trazem o versículo inteiro. Versículos omitidos pelo texto-base não aparecem.
O ``titulo`` dos salmos (“De Davi.”, “Aleluia.”) não é lido: fica fora do texto do versículo e, quando entra em
``partes`` como parte ``a``, é descartado.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .bible import Ref, Segment, default_versification, parse_ref
from .data_loader import ROOT
from .translation import load_translation


@dataclass(frozen=True)
class VerseText:
    chapter: int
    verse: int
    letters: str  # "" = versículo inteiro
    text: str

    @property
    def label(self) -> str:
        return f"{self.verse}{self.letters}"


@lru_cache(maxsize=1)
def _translation() -> dict:
    return load_translation(ROOT / "data" / "biblia")


@lru_cache(maxsize=1)
def _max_verses() -> dict:
    return default_versification(str(ROOT)).max_verses


def _letters(seg: Segment, c: int, v: int) -> str:
    """Letras pedidas pelo segmento no versículo (c, v); vazio = inteiro."""
    first, last = (seg.c1, seg.v1) == (c, v), (seg.end_chapter, seg.end_verse) == (c, v)
    if seg.v2 is None and seg.c2 is None:  # versículo único: "4ac", "18bcd"
        return seg.l1 if first else ""
    if first and last:  # "17k-m": da letra inicial à final
        return _span(seg.l1[:1] or "a", seg.l2[-1:] or "z")
    if first and seg.l1:
        return _span(seg.l1[0], "z")
    if last and seg.l2:
        return _span("a", seg.l2[-1])
    return ""


def _span(a: str, b: str) -> str:
    return "".join(chr(i) for i in range(ord(a), ord(b) + 1))


def reading_verses(ref_text: str) -> list[VerseText]:
    """Versículos da referência, na ordem do Lecionário. Lista vazia se a referência não pode ser lida."""
    try:
        ref = parse_ref(ref_text, "br")
    except ValueError:
        return []
    verses = _translation().get(ref.book, {})
    out: list[VerseText] = []
    seen: set[tuple[int, int, str]] = set()
    for seg in ref.segments:
        for c, v in sorted(Ref(ref.book, (seg,)).verses(_max_verses())):
            entry = verses.get((c, v))
            if not entry or not entry.get("texto"):
                continue
            letters = _letters(seg, c, v)
            parts = entry.get("partes")
            if letters and parts:
                shown = "".join(ch for ch in letters if ord(ch) - 97 < len(parts))
                text = " ".join(p for p in (parts[ord(ch) - 97] for ch in shown) if p != entry.get("titulo"))
            else:
                text, shown = entry["texto"], ""
            if not text or (c, v, shown) in seen:
                continue
            seen.add((c, v, shown))
            out.append(VerseText(c, v, shown, text))
    return out
