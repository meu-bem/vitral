"""Fase 3: leituras de cada dia a partir de data/lecionario."""

from datetime import date

import pytest

from vitral.data_loader import build_year
from vitral.lectionary import Lectionary


@pytest.fixture(scope="module")
def lec():
    return Lectionary.load()


@pytest.fixture(scope="module")
def y2025():
    return {d.date: d for d in build_year(2025)}


def test_cycle_specific_weekday_overrides_only_its_reading(lec, y2025):
    r = lec.for_day(y2025[date(2025, 12, 1)])  # segunda da 1ª semana do Advento, ano A
    assert r.get("primeira_leitura").ref == "Is 4,2-6"
    assert r.get("evangelho").ref == "Mt 8,5-11"


def test_obligatory_memorial_with_proper_readings(lec, y2025):
    day = y2025[date(2026, 6, 11)]  # São Barnabé
    r = lec.for_day(day)
    assert r.proper_memorial == "sao-barnabe-apostolo"
    assert r.get("primeira_leitura").ref.startswith("At 11,21b-26")


def test_memorial_without_proper_readings_keeps_weekday(lec, y2025):
    day = y2025[date(2026, 1, 21)]  # Santa Inês: memória com leituras do comum
    r = lec.for_day(day)
    assert r.proper_memorial is None
    assert r.keys_used[0].startswith("II.tc-")


@pytest.mark.parametrize("year", range(2025, 2061))
def test_every_day_is_complete(lec, year):
    """Sem furos: todo dia tem 1ª leitura, salmo e evangelho; domingos e solenidades, a 2ª leitura."""
    from vitral.liturgy import Rank
    for d in build_year(year):
        r = lec.for_day(d)
        assert r.pending == [], (d.date, r.pending)
        if d.celebration.id == "sabado-santo":  # Vigília Pascal: sete leituras, epístola e evangelho
            assert r.get("leitura_1") and r.get("evangelho")
            continue
        slots = {x.slot for x in r.readings}
        assert {"primeira_leitura", "salmo", "evangelho"} <= slots, (d.date, d.name, slots)
        if (d.date.weekday() == 6 or d.rank is Rank.SOLEMNITY) and not d.celebration.id.startswith("pascoa-1-"):
            assert "segunda_leitura" in slots, (d.date, d.name)
        assert all(x.ref for x in r.readings), (d.date, d.name)


def test_aparecida_has_brazilian_proper_readings(lec):
    days = {d.date: d for d in build_year(2026)}
    r = lec.for_day(days[date(2027, 10, 12)])
    assert r.get("evangelho").ref == "Jo 2,1-11"
    assert "cnbb-celebrar-em-familia-aparecida" in r.sources
