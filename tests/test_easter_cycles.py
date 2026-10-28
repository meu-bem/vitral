"""Páscoa, Advento e ciclos de leituras."""

from datetime import date, timedelta

import pytest

from vitral.liturgy import easter_date, first_sunday_of_advent, sunday_cycle, weekday_cycle

YEARS = range(2024, 2061)


def knuth_easter(year: int) -> date:
    """Algoritmo independente (Knuth, TAOCP vol. 1, 1.3.2 ex. 14), baseado em epactas."""
    golden = year % 19 + 1
    century = year // 100 + 1
    x = 3 * century // 4 - 12
    z = (8 * century + 5) // 25 - 5
    d = 5 * year // 4 - x - 10
    epact = (11 * golden + 20 + z - x) % 30
    if (epact == 25 and golden > 11) or epact == 24:
        epact += 1
    n = 44 - epact
    if n < 21:
        n += 30
    n = n + 7 - (d + n) % 7
    return date(year, 4, n - 31) if n > 31 else date(year, 3, n)


@pytest.mark.parametrize(
    "year, expected",
    [
        (2026, date(2026, 4, 5)),  # valor de referência do projeto
        (2027, date(2027, 3, 28)),  # valor de referência do projeto
    ],
)
def test_easter_reference_values(year, expected):
    assert easter_date(year) == expected


@pytest.mark.parametrize("year", YEARS)
def test_easter_matches_independent_algorithm(year):
    e = easter_date(year)
    assert e == knuth_easter(year)
    assert e.weekday() == 6
    assert date(year, 3, 22) <= e <= date(year, 4, 25)


@pytest.mark.parametrize(
    "year, expected",
    [
        (2026, date(2026, 11, 29)),  # valor de referência do projeto
        (2027, date(2027, 11, 28)),  # valor de referência do projeto
    ],
)
def test_advent_reference_values(year, expected):
    assert first_sunday_of_advent(year) == expected


@pytest.mark.parametrize("year", YEARS)
def test_advent_is_sunday_closest_to_nov_30(year):
    a = first_sunday_of_advent(year)
    assert a.weekday() == 6
    assert abs((a - date(year, 11, 30)).days) <= 3  # NUALC 40
    # Sempre quatro domingos antes do Natal.
    assert date(year, 12, 18) <= a + timedelta(weeks=3) <= date(year, 12, 24)


@pytest.mark.parametrize(
    "advent_year, cycle",
    [
        (2025, "A"),  # regra do projeto: ano divisível por 3 -> A (ex.: 2025)
        (2026, "B"),  # resto 1 -> B (ex.: 2026)
        (2027, "C"),  # resto 2 -> C
    ],
)
def test_sunday_cycle_known_years(advent_year, cycle):
    assert sunday_cycle(advent_year) == cycle


def test_sunday_cycle_rotates():
    for y in YEARS:
        assert {sunday_cycle(y), sunday_cycle(y + 1), sunday_cycle(y + 2)} == {"A", "B", "C"}


@pytest.mark.parametrize("civil_year, cycle", [(2025, "I"), (2026, "II"), (2027, "I")])
def test_weekday_cycle(civil_year, cycle):
    # Regra do projeto: ímpar -> I, par -> II.
    assert weekday_cycle(civil_year) == cycle
