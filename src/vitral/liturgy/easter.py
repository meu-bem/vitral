"""Cálculo da data da Páscoa (calendário gregoriano).

Usa o algoritmo de Meeus/Jones/Butcher ("Anonymous Gregorian algorithm"),
válido para qualquer ano do calendário gregoriano (a partir de 1583).
"""

from datetime import date, timedelta

__all__ = ["easter_date", "first_sunday_of_advent"]


def easter_date(year: int) -> date:
    """Retorna o Domingo de Páscoa do ano civil ``year``."""
    if year < 1583:
        raise ValueError("o algoritmo só vale para o calendário gregoriano (ano >= 1583)")
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741 (nome do algoritmo original)
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def first_sunday_of_advent(year: int) -> date:
    """1º Domingo do Advento do ano civil ``year``.

    É o domingo anterior ao Natal menos três semanas, o que equivale ao
    domingo que cai em 30 de novembro ou no mais próximo dele (NUALC n. 40).
    """
    christmas = date(year, 12, 25)
    # weekday(): segunda=0 ... domingo=6. Domingo estritamente anterior ao Natal.
    days_back = (christmas.weekday() + 1) % 7 or 7
    fourth_sunday = christmas - timedelta(days=days_back)
    return fourth_sunday - timedelta(weeks=3)
