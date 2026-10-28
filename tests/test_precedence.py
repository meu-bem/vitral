"""Precedência, ocorrência e transferências (NUALC 5, 14, 16, 59, 60) com os dados do repositório.

Os testes verificam regras em todos os anos de 2024 a 2060, sem datas copiadas de terceiros.
Celebrações com nome "TESTE" são fictícias e servem só para exercitar regras.
"""

from datetime import date, timedelta

import pytest

from vitral.data_loader import load_sanctorale
from vitral.liturgy import (
    Celebration, Color, Precedence, Rank, SanctoraleEntry, build_liturgical_year, year_anchors,
)

YEARS = range(2024, 2061)
JOSE, ANUNC, JOAO = "sao-jose-esposo-de-maria", "anunciacao-do-senhor", "nascimento-de-joao-batista"
PEDRO_PAULO, ASSUNCAO, TODOS = ("sao-pedro-e-sao-paulo-apostolos", "assuncao-da-bem-aventurada-virgem-maria",
                                "todos-os-santos")
FINADOS, IMACULADA = "comemoracao-de-todos-os-fieis-defuntos", "imaculada-conceicao"
MAE_IGREJA, IMAC_CORACAO = "bem-aventurada-virgem-maria-mae-da-igreja", "imaculado-coracao-de-maria"


@pytest.fixture(scope="module")
def sanct():
    return load_sanctorale()


@pytest.fixture(scope="module")
def years(br_rules, sanct):
    return {y: build_liturgical_year(y, br_rules, sanct) for y in YEARS}


def where(days, cid):
    return [d for d in days if d.celebration.id == cid]


def test_ids_used_here_exist(sanct):
    ids = {e.celebration.id for e in sanct}
    assert {JOSE, ANUNC, JOAO, PEDRO_PAULO, ASSUNCAO, TODOS, FINADOS, IMACULADA, MAE_IGREJA, IMAC_CORACAO} <= ids


@pytest.mark.parametrize("y", YEARS)
def test_every_solemnity_is_celebrated_exactly_once(years, y):
    for sid in (JOSE, ANUNC, JOAO, PEDRO_PAULO, ASSUNCAO, TODOS, IMACULADA):
        assert len(where(years[y], sid)) == 1, sid


@pytest.mark.parametrize("y", YEARS)
def test_brazil_transfers_to_the_following_sunday(years, y):
    """São Pedro e São Paulo e Assunção: no domingo seguinte, se não caírem em domingo."""
    for sid, (m, dd) in ((PEDRO_PAULO, (6, 29)), (ASSUNCAO, (8, 15))):
        own = date(y + 1, m, dd)
        expected = own if own.weekday() == 6 else own + timedelta(days=6 - own.weekday())
        assert where(years[y], sid)[0].date == expected


@pytest.mark.parametrize("y", YEARS)
def test_all_saints_and_all_souls(years, y):
    own = date(y + 1, 11, 1)
    saints = where(years[y], TODOS)[0].date
    souls = where(years[y], FINADOS)[0].date
    assert souls == date(y + 1, 11, 2)
    if own.weekday() == 5:  # domingo seguinte é Finados: Todos os Santos fica no sábado
        assert saints == own
    else:
        assert saints == (own if own.weekday() == 6 else own + timedelta(days=6 - own.weekday()))


@pytest.mark.parametrize("y", YEARS)
def test_immaculate_conception_stays_even_on_advent_sunday(years, y):
    assert where(years[y], IMACULADA)[0].date == date(y, 12, 8)


@pytest.mark.parametrize("y", YEARS)
def test_annunciation(years, y, br_rules):
    a = year_anchors(y, br_rules)
    own = date(y + 1, 3, 25)
    got = where(years[y], ANUNC)[0].date
    if a.palm_sunday <= own <= a.easter + timedelta(days=7):
        assert got == a.easter + timedelta(days=8)  # NUALC 60
    elif own.weekday() == 6:
        assert got == own + timedelta(days=1)  # domingo da Quaresma -> segunda (NUALC 5)
    else:
        assert got == own


@pytest.mark.parametrize("y", YEARS)
def test_saint_joseph(years, y, br_rules):
    a = year_anchors(y, br_rules)
    own = date(y + 1, 3, 19)
    got = where(years[y], JOSE)[0].date
    if a.palm_sunday <= own < a.easter + timedelta(days=7):
        assert got == a.palm_sunday - timedelta(days=1)  # dia livre mais próximo: sábado antes de Ramos
    elif own.weekday() == 6:
        assert got == own + timedelta(days=1)
    else:
        assert got == own


@pytest.mark.parametrize("y", YEARS)
def test_john_the_baptist_and_sacred_heart(years, y, br_rules):
    """Coincidindo com solenidade do próprio do tempo (Sagrado Coração, Corpus Christi), João Batista
    vai para o dia livre mais próximo, o anterior em empate (resposta da Congregação, 2020)."""
    a = year_anchors(y, br_rules)
    got = where(years[y], JOAO)[0].date
    own = date(y + 1, 6, 24)
    impeded = own in (a.sacred_heart, a.corpus_christi, a.trinity)
    assert got == (own - timedelta(days=1) if impeded else own)


@pytest.mark.parametrize("y", YEARS)
def test_marian_movable_memorials(years, y, br_rules):
    a = year_anchors(y, br_rules)
    days = {d.date: d for d in years[y]}
    for when, mid in ((a.pentecost + timedelta(days=1), MAE_IGREJA), (a.sacred_heart + timedelta(days=1), IMAC_CORACAO)):
        d = days[when]
        if d.celebration.is_temporale:
            assert d.observed_memorial is not None and d.observed_memorial.id == mid
            # Só uma memória obrigatória por dia: a mariana prevalece (notificação de 2018).
            assert sum(m.rank is Rank.MEMORIAL for m in d.memorials) == 1


@pytest.mark.parametrize("y", YEARS)
def test_no_pending_with_real_data(years, y):
    assert [(d.date, d.pending) for d in years[y] if d.pending] == []


# ---------- mecânica, com celebrações fictícias ----------
def entry(id_, rank, prec, md):
    return SanctoraleEntry(Celebration(id=id_, name=id_.upper(), rank=rank, precedence=prec, color=Color.RED),
                           month_day=md)


def test_solemnity_on_advent_sunday_goes_to_monday(br_rules, sanct):
    test = entry("solenidade-teste", Rank.SOLEMNITY, Precedence.GENERAL_SOLEMNITY, (12, 14))
    days = {d.date: d for d in build_liturgical_year(2025, br_rules, sanct + [test])}
    assert days[date(2025, 12, 14)].name == "3º Domingo do Advento"
    assert days[date(2025, 12, 15)].celebration.id == "solenidade-teste"


def test_feast_on_privileged_sunday_is_omitted(br_rules, sanct):
    test = entry("festa-teste", Rank.FEAST, Precedence.GENERAL_FEAST, (12, 14))
    days = build_liturgical_year(2025, br_rules, sanct + [test])
    assert all(d.celebration.id != "festa-teste" for d in days)


def test_memorials_on_lent_weekday_become_optional(br_rules):
    test = entry("memoria-teste", Rank.MEMORIAL, Precedence.GENERAL_MEMORIAL, (3, 3))
    days = {d.date: d for d in build_liturgical_year(2026, br_rules, [test])}
    d = days[date(2027, 3, 3)]  # quarta-feira da Quaresma
    assert d.celebration.is_temporale and d.color is Color.VIOLET
    assert [m.rank for m in d.memorials] == [Rank.OPTIONAL_MEMORIAL]


def test_obligatory_memorial_sets_color_but_not_readings(br_rules):
    test = entry("memoria-teste", Rank.MEMORIAL, Precedence.GENERAL_MEMORIAL, (7, 7))
    days = {d.date: d for d in build_liturgical_year(2026, br_rules, [test])}
    d = days[date(2027, 7, 7)]  # quarta-feira do Tempo Comum
    assert d.color is Color.RED and d.lectionary_keys[0].startswith("I.tc-")


def test_documented_override(br_rules):
    test = entry("solenidade-teste", Rank.SOLEMNITY, Precedence.GENERAL_SOLEMNITY, (7, 7))
    days = {d.date: d for d in build_liturgical_year(
        2026, br_rules, [test], {("solenidade-teste", date(2027, 7, 7)): date(2027, 7, 8)})}
    assert days[date(2027, 7, 8)].celebration.id == "solenidade-teste"
    assert days[date(2027, 7, 7)].celebration.is_temporale


def test_saturday_marian_note(br_rules):
    days = {d.date: d for d in build_liturgical_year(2026, br_rules)}
    assert any("Santa Maria no sábado" in n for n in days[date(2027, 7, 10)].notes)
