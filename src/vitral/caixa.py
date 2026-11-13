"""Maiúsculas, minúsculas e pontuação nas bordas dos trechos.

Dois usos, mesma regra:

- ``scripts/ajustar_caixa.py`` corrige ``data/biblia/``: versículo que continua a frase do anterior
  (este termina em vírgula, ponto e vírgula ou sem pontuação) começa com minúscula;
- o livro, ao montar uma leitura, abre cada trecho com maiúscula, fecha com ponto e, quando
  põe "Naquele tempo," antes, baixa a primeira letra.

Nomes próprios mantêm a maiúscula. A lista sai do próprio texto traduzido (``Lexicon``): palavra que, no meio
de frase, aparece quase sempre com maiúscula (Deus, Jesus, Davi...) e dupla de palavras maiúsculas que se repete
(Espírito Santo, Mar Vermelho...). Nada aqui usa IA nem consulta outra tradução.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

__all__ = ["Lexicon", "build_lexicon", "lower_first", "upper_first", "close_sentence", "continues_sentence"]

_OPEN = "“‘(\"'["
_CLOSE = "”’)]\"'"
_SENTENCE_END = re.compile(r"[.!?…][" + re.escape(_CLOSE) + r"]*$")
_OPENING = re.compile(r"^[" + re.escape(_OPEN) + r"]+")
_TRAILING = re.compile(r"[,.;:!?" + re.escape(_CLOSE) + r"—…]+$")

# Nome próprio quando, no meio de frase, a forma maiúscula aparece ao menos 3 vezes e 10 vezes mais
# que a minúscula ("Deus": 2160 x 27; "Filho": 209 x 404, então "filho" abre minúscula).
MIN_CAPITALIZED = 3
RATIO = 10
MIN_BIGRAM = 2


def _word(token: str) -> str:
    return _TRAILING.sub("", _OPENING.sub("", token))


@dataclass
class Lexicon:
    names: frozenset[str] = frozenset()
    bigrams: frozenset[tuple[str, str]] = frozenset()
    stats: dict[str, tuple[int, int]] = field(default_factory=dict)  # palavra -> (maiúscula, minúscula)


def build_lexicon(texts: Iterable[str]) -> Lexicon:
    capitalized: dict[str, int] = {}
    lowered: dict[str, int] = {}
    pairs: dict[tuple[str, str], int] = {}
    for text in texts:
        tokens = text.split()
        for i, tok in enumerate(tokens):
            if i == 0 or _SENTENCE_END.search(tokens[i - 1]) or tokens[i - 1].endswith(":") or tok[0] in _OPEN:
                continue  # início de frase ou de citação: a maiúscula não diz nada
            w = _word(tok)
            if not w or not w[0].isalpha():
                continue
            if w[0].isupper():
                capitalized[w] = capitalized.get(w, 0) + 1
                if i + 1 < len(tokens):
                    nxt = _word(tokens[i + 1])
                    if nxt and nxt[0].isupper():
                        pairs[(w, nxt)] = pairs.get((w, nxt), 0) + 1
            else:
                lowered[w] = lowered.get(w, 0) + 1
    names = {w for w, n in capitalized.items()
             if n >= MIN_CAPITALIZED and n >= RATIO * lowered.get(w.lower(), 0)}
    bigrams = {p for p, n in pairs.items() if n >= MIN_BIGRAM}
    stats = {w: (n, lowered.get(w.lower(), 0)) for w, n in capitalized.items()}
    return Lexicon(frozenset(names), frozenset(bigrams), stats)


def _first_letter(text: str) -> int:
    """Índice da primeira letra, depois de aspas e parênteses de abertura; -1 se o texto não começa por letra."""
    m = _OPENING.match(text)
    i = m.end() if m else 0
    return i if i < len(text) and text[i].isalpha() else -1


def lower_first(text: str, lex: Lexicon) -> str:
    """Baixa a primeira letra, salvo nome próprio. Texto que abre com aspas (começo de fala) não muda."""
    if not text or text[0] in _OPEN:
        return text
    i = _first_letter(text)
    if i < 0 or not text[i].isupper():
        return text
    tokens = text.split()
    first = _word(tokens[0])
    if len(first) > 1 and first.isupper():  # sigla (YHWH)
        return text
    if first in lex.names:
        return text
    if len(tokens) > 1 and (first, _word(tokens[1])) in lex.bigrams:
        return text
    return text[:i] + text[i].lower() + text[i + 1:]


def upper_first(text: str) -> str:
    i = _first_letter(text)
    if i < 0 or text[i].isupper():
        return text
    return text[:i] + text[i].upper() + text[i + 1:]


_OPEN_END = re.compile(r"[,;:][" + re.escape(_CLOSE) + r"]*$")


def close_sentence(text: str) -> str:
    """Fecha o trecho com ponto: vírgula, ponto e vírgula e dois-pontos finais viram ponto; sem pontuação, ganha ponto."""
    t = text.rstrip()
    if _OPEN_END.search(t):
        return re.sub(r"[,;:]([" + re.escape(_CLOSE) + r"]*)$", r".\1", t)
    if _SENTENCE_END.search(t):
        return t
    last = t[-1:] if t else ""
    if last.isalnum():
        return t + "."
    return t


def continues_sentence(previous: str) -> bool:
    """O versículo seguinte continua a frase? Sim se este termina em vírgula, ponto e vírgula ou sem pontuação."""
    t = previous.rstrip()
    if not t:
        return False
    core = t.rstrip(_CLOSE)
    return core.endswith((",", ";")) or core[-1:].isalnum()
