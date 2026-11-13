"""Leituras como o livro as mostra: caixa, pontuação nas bordas, anúncio, abertura, conclusão e salmo em estrofes."""

import re
from functools import lru_cache

import pytest
import yaml

from vitral.caixa import build_lexicon, close_sentence, continues_sentence, lower_first, upper_first
from vitral.data_loader import DATA_DIR
from vitral.formulas import formulas, inicios, slot_kind
from vitral.proclamacao import lexicon, preparar

END = re.compile(r"[.!?…][”’)\"']*$")


@lru_cache(maxsize=1)
def lectionary_readings() -> list[tuple[str, str]]:
    """(espaço, referência) de toda leitura do Lecionário, sem repetir."""
    out: set[tuple[str, str]] = set()

    def walk(x, slot=None):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "ref" and isinstance(v, str):
                    out.add((slot or "primeira_leitura", v))
                elif k == "alternativas" and isinstance(v, list):
                    out.update((slot or "primeira_leitura", a) for a in v)
                else:
                    is_slot = k in ("evangelho", "evangelho_procissao", "salmo", "primeira_leitura", "segunda_leitura") \
                        or re.fullmatch(r"(leitura|salmo)_\d", str(k))
                    walk(v, k if is_slot else slot)
        elif isinstance(x, list):
            for i in x:
                walk(i, slot)

    for path in sorted((DATA_DIR / "lecionario").glob("*.yaml")):
        walk(yaml.safe_load(path.read_text(encoding="utf8")))
    return sorted(out)


# ------------------------------------------------------------------ caixa
def test_case_helpers():
    lex = build_lexicon(["O Senhor disse a Moisés: Deus é bom.", "Falou Deus e o Senhor ouviu Deus; Deus viu o Senhor."] * 3)
    assert lower_first("Pois será grande", lex) == "pois será grande"
    assert lower_first("Deus disse", lex) == "Deus disse"
    assert lower_first("“Eu sou”", lex) == "“Eu sou”"  # começo de fala não muda
    assert upper_first("pois será") == "Pois será"
    assert upper_first("“pois será”") == "“Pois será”"
    assert close_sentence("e o povo, ") == "e o povo."
    assert close_sentence("disse;") == "disse."
    assert close_sentence("ele disse:") == "ele disse."
    assert close_sentence("Palavra do Senhor") == "Palavra do Senhor."
    assert close_sentence("Ele disse: “Vem,”") == "Ele disse: “Vem.”"
    assert close_sentence("homens, porque todos pecaram —") == "homens, porque todos pecaram."
    assert close_sentence("Acabou.") == "Acabou." and close_sentence("Acabou?”") == "Acabou?”"
    assert continues_sentence("Ao sair,") and continues_sentence("Ao sair") and continues_sentence("foi — ")
    assert not continues_sentence("Acabou.") and not continues_sentence("Disse:")


def test_lexicon_keeps_proper_names_and_drops_common_words():
    lex = lexicon()
    assert {"Deus", "Jesus", "Cristo", "Davi"} <= lex.names
    assert "Filho" not in lex.names and "Pois" not in lex.names
    assert ("Espírito", "Santo") in lex.bigrams


def test_translation_data_follows_the_case_rule():
    """Depois de vírgula, ponto e vírgula ou travessão, o versículo seguinte começa com minúscula (salvo nome e fala)."""
    lex = lexicon()
    bad = []
    for path in sorted((DATA_DIR / "biblia").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf8"))
        keys = list(doc["versiculos"])
        for prev, cur in zip(keys, keys[1:]):
            if doc["livro"] == "PSA" and prev.split(":")[0] != cur.split(":")[0]:
                continue
            if continues_sentence(doc["versiculos"][prev]["texto"]):
                text = doc["versiculos"][cur]["texto"]
                if lower_first(text, lex) != text:
                    bad.append(f"{doc['livro']} {cur}: {text[:40]}")
    assert not bad, bad[:10]


def test_no_archaic_pronoun_contractions_left():
    pattern = re.compile(r"(?<![\w-])(?:(?:vo|no)-(?:lo|la)s?|lh[oa]s?)(?![\w-])")
    found = []
    for path in sorted((DATA_DIR / "biblia").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf8"))
        found += [f"{doc['livro']} {k}" for k, v in doc["versiculos"].items() if pattern.search(v["texto"])]
    assert not found, found


# ------------------------------------------------------------------ bordas de cada leitura
def test_every_reading_opens_with_capital_and_closes_with_a_period():
    readings = lectionary_readings()
    assert len(readings) > 2000
    bad = []
    for slot, ref in readings:
        p = preparar(slot, ref)
        if p is None:
            continue
        for block in p.blocos:
            first, last = block[0].text, block[-1].text
            letter = re.search(r"[^\W\d_]", first)
            if p.abertura is None and letter and not letter.group().isupper():
                bad.append(f"{ref}: abre com minúscula: {first[:30]}")
            if not END.search(last):
                bad.append(f"{ref}: não fecha com ponto: …{last[-30:]}")
    assert not bad, bad[:40]


def test_reading_with_opening_continues_in_lowercase():
    bad = []
    for slot, ref in lectionary_readings():
        p = preparar(slot, ref)
        if p and p.abertura and slot_kind(slot) != "salmo":
            text = p.blocos[0][0].text
            if text[:1].isupper() and text.split()[0].strip("“‘,.:;") not in lexicon().names \
                    and not text.startswith("“"):
                bad.append(f"{ref}: {p.abertura} {text[:30]}")
    assert not bad, bad[:40]


# ------------------------------------------------------------------ anúncio, abertura e conclusão
def test_gospel_frame():
    p = preparar("evangelho", "Lc 14,25-33")
    assert p.anuncio == "Proclamação do Evangelho de Jesus Cristo segundo Lucas."
    assert p.abertura == "Naquele tempo,"
    assert p.conclusao == "Palavra da Salvação."
    assert p.blocos[0][0].text.startswith("grandes multidões iam com ele")


def test_first_reading_and_letter_frames():
    p = preparar("primeira_leitura", "Is 2,1-5")
    assert p.anuncio == "Leitura do Livro do Profeta Isaías." and p.abertura is None
    assert p.conclusao == "Palavra do Senhor."
    assert p.blocos[0][0].text.startswith("Palavra que Isaías")
    assert preparar("segunda_leitura", "Rm 13,11-14").abertura == "Irmãos,"
    assert preparar("segunda_leitura", "1Pd 2,4-9").abertura == "Caríssimos,"
    assert preparar("primeira_leitura", "Gn 12,1-4a").abertura == "Naqueles dias,"
    assert preparar("primeira_leitura", "At 2,1-11").anuncio == "Leitura dos Atos dos Apóstolos."


def test_no_opening_when_text_already_has_one():
    assert preparar("evangelho", "Jo 1,1-18").abertura is None  # primeira frase do livro
    assert preparar("evangelho", "Mc 1,1-8").abertura is None
    assert preparar("evangelho", "Jo 20,19-31").abertura is None  # "Ao anoitecer daquele dia"


def test_gospel_starting_inside_a_speech():
    p = preparar("evangelho", "Jo 10,11-16")
    assert p.abertura == "Naquele tempo, Jesus disse:"
    assert p.blocos[0][0].text.startswith("“Eu sou o bom pastor")
    assert p.blocos[-1][-1].text.endswith("”") or "”" in p.blocos[-1][-1].text


def test_psalm_is_stanzas_without_refrain_or_frame():
    p = preparar("salmo", "Sl 89(90),3-4.5-6.12-13.14.17")
    assert p.kind == "salmo" and p.anuncio is None and p.abertura is None and p.conclusao is None
    assert [len(b) for b in p.blocos] == [2, 2, 2, 1, 1]
    assert p.blocos[2][0].text[0].isupper()  # a estrofe abre com maiúscula
    assert all(b[-1].text.endswith((".", "!", "?", "”")) for b in p.blocos)


def test_pending_reading_has_no_proclamation():
    assert preparar("evangelho", None) is None
    assert preparar("evangelho", "Xx 1,1") is None


def test_exceptions_file_matches_real_readings():
    from vitral.formulas import start_key

    by_start: dict[str, list[tuple[str, str]]] = {}
    for slot, ref in lectionary_readings():
        by_start.setdefault(start_key(ref), []).append((slot, ref))
    for key, cfg in inicios().items():
        assert key in by_start, f"nenhuma leitura começa em {key}"
        assert cfg.get("motivo"), f"{key}: diga o motivo da exceção"
        for slot, ref in by_start[key]:
            preparar(slot, ref)  # levanta ValueError se a troca não casar com o texto


def test_every_book_has_a_frame():
    books = formulas()["livros"]
    assert len(books) == 73
    for code, entry in books.items():
        assert code == "PSA" or entry["anuncio"].endswith(".")
