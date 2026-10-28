"""Estrutura do ano litúrgico (só próprio do tempo), 2024-2060, regras do Brasil."""

from collections import Counter
from datetime import date, timedelta

import pytest

from vitral.liturgy import (
    Season,
    build_liturgical_year,
    easter_date,
    first_sunday_of_advent,
    sunday_cycle,
    weekday_cycle,
    year_anchors,
)

YEARS = range(2024, 2061)


@pytest.fixture(scope="module")
def years(br_rules):
    return {y: build_liturgical_year(y, br_rules) for y in YEARS}


@pytest.mark.parametrize("year", YEARS)
def test_each_day_has_exactly_one_liturgical_day(years, year):
    days = years[year]
    dates = [d.date for d in days]
    assert len(dates) == len(set(dates))
    start, end = first_sunday_of_advent(year), first_sunday_of_advent(year + 1) - timedelta(days=1)
    assert dates[0] == start and dates[-1] == end
    assert len(dates) == (end - start).days + 1
    assert all(b - a == timedelta(days=1) for a, b in zip(dates, dates[1:]))
    assert all(d.liturgical_year == year for d in days)


@pytest.mark.parametrize("year", YEARS)
def test_year_starts_on_sunday_and_ends_on_saturday(years, year):
    days = years[year]
    assert days[0].date.weekday() == 6 and days[0].name == "1º Domingo do Advento"
    assert days[-1].date.weekday() == 5


def test_consecutive_years_are_contiguous(years):
    for y in list(YEARS)[:-1]:
        assert years[y][-1].date + timedelta(days=1) == years[y + 1][0].date


@pytest.mark.parametrize("year", YEARS)
def test_cycles(years, year):
    for d in years[year]:
        assert d.sunday_cycle == sunday_cycle(year)
        assert d.weekday_cycle == weekday_cycle(year + 1)


@pytest.mark.parametrize("year", YEARS)
def test_season_order_and_lengths(years, year):
    days = years[year]
    order = []
    for d in days:
        if not order or order[-1] != d.season:
            order.append(d.season)
    assert order == [
        Season.ADVENT, Season.CHRISTMAS, Season.ORDINARY, Season.LENT,
        Season.TRIDUUM, Season.EASTER, Season.ORDINARY,
    ]
    count = Counter(d.season for d in days)
    assert count[Season.TRIDUUM] == 2  # sexta e sábado (a quinta é dia da Semana Santa)
    assert count[Season.EASTER] == 50
    # Advento: de 22 a 28 dias.
    assert 22 <= count[Season.ADVENT] <= 28


@pytest.mark.parametrize("year", YEARS)
def test_ordinary_time_weeks(years, year):
    ordinary = [d for d in years[year] if d.season is Season.ORDINARY]
    weeks = sorted({d.week for d in ordinary})
    assert weeks[0] == 1 and weeks[-1] == 34
    missing = set(range(1, 35)) - set(weeks)
    # NUALC 43: 33 ou 34 semanas; no máximo uma semana pulada na retomada.
    assert len(missing) <= 1
    sundays = [d for d in ordinary if d.date.weekday() == 6]
    for d in sundays:
        if d.week in (1,):
            pytest.fail("1º domingo do Tempo Comum não existe (é o Batismo)")
    assert sundays[-1].name == "Nosso Senhor Jesus Cristo, Rei do Universo"
    assert sundays[-1].week == 34


@pytest.mark.parametrize("year", YEARS)
def test_anchors(br_rules, year):
    a = year_anchors(year, br_rules)
    e = easter_date(year + 1)
    assert a.easter == e
    assert a.ash_wednesday == e - timedelta(days=46) and a.ash_wednesday.weekday() == 2
    assert a.palm_sunday == e - timedelta(days=7)
    assert a.ascension == e + timedelta(days=42)  # Brasil: 7º Domingo da Páscoa
    assert a.pentecost == e + timedelta(days=49)
    assert a.trinity.weekday() == 6
    assert a.corpus_christi.weekday() == 3  # Brasil: quinta-feira
    assert a.sacred_heart.weekday() == 4
    assert 2 <= a.epiphany.day <= 8 and a.epiphany.month == 1 and a.epiphany.weekday() == 6
    assert a.holy_family.weekday() == 6 or a.holy_family == date(year, 12, 30)
    if a.epiphany.day >= 7:
        assert a.baptism == a.epiphany + timedelta(days=1)
    else:
        assert a.baptism == a.epiphany + timedelta(days=7)
    assert a.christ_the_king == first_sunday_of_advent(year + 1) - timedelta(days=7)


@pytest.mark.parametrize("year", YEARS)
def test_lectionary_keys_are_unique_within_year(years, year):
    """Cada chave principal do Lecionário aparece uma única vez por ano."""
    keys = Counter(d.lectionary_keys[0] for d in years[year])
    assert [k for k, n in keys.items() if n > 1] == []


@pytest.mark.parametrize("year", YEARS)
def test_no_pending_day_in_the_calendar(years, year):
    """Toda regra aplicada tem fonte (decreto de 1977 para o Batismo na segunda-feira etc.)."""
    assert [(d.date, d.pending) for d in years[year] if d.pending] == []


@pytest.mark.parametrize("year", YEARS)
def test_named_days_follow_the_norms(years, year, br_rules):
    """Regras da NUALC e do Brasil verificadas em todos os anos (sem datas copiadas de terceiros)."""
    a = year_anchors(year, br_rules)
    days = {d.date: d for d in years[year]}
    assert days[a.advent].name == "1º Domingo do Advento"
    assert days[a.christmas].name == "Natal do Senhor"
    assert days[a.epiphany].name == "Epifania do Senhor"
    assert days[a.baptism].name == "Batismo do Senhor"
    assert days[a.ash_wednesday].name == "Quarta-feira de Cinzas"
    assert days[a.palm_sunday].name == "Domingo de Ramos da Paixão do Senhor"
    assert days[a.easter].name == "Domingo da Páscoa da Ressurreição do Senhor"
    assert days[a.ascension].name == "Ascensão do Senhor"
    assert days[a.pentecost].name == "Domingo de Pentecostes"
    assert days[a.trinity].name == "Santíssima Trindade"
    assert days[a.corpus_christi].name == "Santíssimo Corpo e Sangue de Cristo"
    assert days[a.sacred_heart].name == "Sagrado Coração de Jesus"
    # O domingo seguinte ao Batismo (ou à Epifania, quando o Batismo vai para a segunda) é o 2º do Tempo Comum.
    second = a.baptism + timedelta(days=7 if a.baptism.weekday() == 6 else 6)
    assert days[second].name == "2º Domingo do Tempo Comum"
    # A semana do Tempo Comum que recomeça depois de Pentecostes é a que termina na 34ª.
    assert days[a.pentecost + timedelta(days=1)].week == 34 - (a.christ_the_king - a.pentecost).days // 7


@pytest.mark.parametrize("year", YEARS)
def test_temporale_colors(years, year, br_rules):
    """Cores do próprio do tempo (IGMR 346)."""
    a = year_anchors(year, br_rules)
    days = {d.date: d for d in years[year]}
    assert days[a.ash_wednesday].color.value == "roxo"
    assert days[a.palm_sunday].color.value == "vermelho"
    assert days[a.easter - timedelta(days=2)].color.value == "vermelho"  # Sexta-feira Santa
    assert days[a.pentecost].color.value == "vermelho"
    assert days[a.easter].color.value == "branco"
    gaudete = a.advent + timedelta(weeks=2)
    assert [c.value for c in days[gaudete].alt_colors] == ["rosa"]
    for d in years[year]:
        if d.season is Season.ORDINARY and d.celebration.is_temporale and d.rank.value in ("domingo", "dia-de-semana") \
                and not d.memorials:
            assert d.color.value == "verde"


@pytest.mark.parametrize("year", [2027, 2032, 2038])  # Advento em 28/11 ou 29/11
def test_late_november_advent_weekdays_are_not_dated_weekdays(years, year):
    """Regressão: dias de novembro não podem virar 'dias 17 a 24 de dezembro'."""
    for d in years[year][:7]:
        assert d.date.month == 11 or d.date.day <= 6
        assert "dezembro" not in d.name or d.date.month == 12
        assert not d.lectionary_keys[0].startswith("advento.")
