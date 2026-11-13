"""Cada leitura como o livro a mostra: anúncio, abertura, texto e conclusão.

Tudo por regra, no build, sem IA (fórmulas em ``data/formulas.yaml``, exceções por versículo inicial em ``data/inicios.yaml``):

- **anúncio** do livro ("Leitura do Livro do Gênesis.", "Proclamação do Evangelho de Jesus Cristo segundo Lucas.");
- **abertura**: "Naquele tempo," nos evangelhos, "Naqueles dias," nos livros históricos e em Atos, "Irmãos," e
  "Caríssimos," nas cartas. Fica de fora quando o texto já começa com marca de tempo, vocativo ou o autor se
  apresentando, e na primeira frase de um livro. Evangelho que começa no meio de uma fala ganha
  "Naquele tempo, Jesus disse:";
- **bordas do trecho**: cada trecho abre com maiúscula e fecha com ponto (``caixa.py``); uma conjunção solta no
  começo ("E Maria disse") cai;
- **conclusão**: "Palavra do Senhor." (leituras) e "Palavra da Salvação." (evangelho).

Salmo: sem anúncio, abertura nem conclusão. Cada trecho da referência (os pontos de "Sl 18,2-3.4-5") é uma estrofe;
o refrão não é impresso (ver docs/LICENCIAMENTO.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from functools import lru_cache

from .caixa import Lexicon, build_lexicon, close_sentence, lower_first, upper_first
from .formulas import announcement, formulas, inicios, slot_kind, start_key
from .reading_text import VerseText, _translation, open_quotes_before, reading_book, reading_segments

__all__ = ["Proclamacao", "preparar"]

_LETTERS = "A-Za-zÀ-ÿ"


@dataclass(frozen=True)
class Proclamacao:
    kind: str  # "salmo", "leitura" ou "evangelho"
    ref: str
    anuncio: str | None
    abertura: str | None
    blocos: tuple[tuple[VerseText, ...], ...]  # estrofes (salmo) ou trechos da referência
    conclusao: str | None

    @property
    def chapter(self) -> int:
        return self.blocos[0][0].chapter


@lru_cache(maxsize=1)
def lexicon() -> Lexicon:
    return build_lexicon(e["texto"] for verses in _translation().values() for e in verses.values())


def _starts_with(text: str, phrases: list[str]) -> bool:
    head = text[:1].upper() + text[1:]
    return any(re.match(rf"^{re.escape(p)}(?![{_LETTERS}])", head) for p in phrases)


def _auto_abertura(kind: str, book: str, first: VerseText, text: str, ref: str) -> str | None:
    f = formulas()
    entry = f["livros"][book]
    if first.chapter == 1 and first.verse == 1 and not first.letters:
        return None  # primeira frase do livro: já abre sozinha
    if _starts_with(text, f["dispensam_abertura"]):
        return None
    if kind == "evangelho":
        speech = text.startswith("“") or open_quotes_before(book, first.chapter, first.verse) > 0
        return f["aberturas"]["discurso" if speech else "evangelho"]
    key = entry.get("abertura")
    if not key:
        return None
    if key in ("irmaos", "carissimo", "carissimos") and _starts_with(text, f["dispensam_abertura_nas_cartas"]):
        return None
    return f["aberturas"][key]


def _fechar(group: list[VerseText]) -> list[VerseText]:
    """Abre o trecho com maiúscula e o fecha com ponto."""
    out = list(group)
    out[0] = replace(out[0], text=upper_first(out[0].text))
    out[-1] = replace(out[-1], text=close_sentence(out[-1].text))
    return out


def _inicio(kind: str, book: str, ref: str, first: VerseText) -> tuple[VerseText, str | None]:
    """Primeiro versículo do trecho, já sem conjunção solta e com a abertura escolhida."""
    f, cfg = formulas(), inicios().get(start_key(ref) or "", {})
    conj = re.compile(rf"^(?:{'|'.join(f['conjuncoes_iniciais'])}),?\s+", re.IGNORECASE)
    text = first.text
    if not first.letters and text[:1] not in "“‘":
        text = conj.sub("", text)  # conjunção solta no começo: "E Maria disse" -> "Maria disse"
    if "troca" in cfg:
        old, new = cfg["troca"]
        old = conj.sub("", old)
        if text[:1].lower() + text[1:len(old)] != old[:1].lower() + old[1:]:
            raise ValueError(f"{ref}: a troca {old!r} não casa com o começo do versículo ({text[:40]!r})")
        text = new + text[len(old):]
    if "abertura" in cfg:
        abertura = cfg["abertura"] or None
    else:
        abertura = _auto_abertura(kind, book, first, text, ref)
    if abertura:
        discourse = abertura == f["aberturas"]["discurso"]
        if discourse and not text.startswith("“"):
            text = "“" + upper_first(text)  # a fala já vinha aberta no versículo anterior
        else:
            text = lower_first(text, lexicon())
    else:
        text = upper_first(text)
    return replace(first, text=text), abertura


def _balance_quotes(blocos: list[list[VerseText]]) -> None:
    """Fala que ficou aberta no fim do trecho (lida a partir do meio) fecha com ”."""
    opened = sum(v.text.count("“") - v.text.count("”") for g in blocos for v in g)
    if opened > 0 and blocos[-1][-1].text.endswith((".", "!", "?")):
        last = blocos[-1][-1]
        blocos[-1][-1] = replace(last, text=last.text + "”" * opened)


def preparar(slot: str, ref: str | None) -> Proclamacao | None:
    """Leitura pronta para o livro, ou None se a referência está pendente ou não tem tradução."""
    if not ref:
        return None
    segments = reading_segments(ref)
    book = reading_book(ref)
    if not segments or book is None:
        return None
    kind = slot_kind(slot)
    if kind == "salmo":
        return Proclamacao(kind, ref, None, None, tuple(tuple(_fechar(g)) for g in segments), None)
    blocos = [_fechar(g) for g in segments]
    first, abertura = _inicio(kind, book, ref, segments[0][0])
    if len(segments[0]) == 1 and len(blocos[0]) == 1:
        first = replace(first, text=close_sentence(first.text))
    blocos[0][0] = first
    _balance_quotes(blocos)
    f = formulas()
    return Proclamacao(
        kind, ref, announcement(book), abertura, tuple(tuple(g) for g in blocos),
        f["conclusoes"]["evangelho" if kind == "evangelho" else "leitura"])
