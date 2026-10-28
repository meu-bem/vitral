"""Ciclos de leituras do Lecionário.

- Domingos e solenidades: ciclo trienal A/B/C, que muda no 1º Domingo do Advento.
- Dias de semana do Tempo Comum: ciclo bienal I (anos ímpares) / II (anos pares).

Referências para conferência estão em ``docs/FONTES.md`` e nos testes.
"""

__all__ = ["sunday_cycle", "weekday_cycle"]


def sunday_cycle(advent_year: int) -> str:
    """Ciclo dominical do ano litúrgico que começa no Advento de ``advent_year``.

    Resto 0 -> A (ex.: 2025), 1 -> B (ex.: 2026), 2 -> C (ex.: 2024).
    """
    return "ABC"[advent_year % 3]


def weekday_cycle(civil_year: int) -> str:
    """Ciclo ferial do Tempo Comum que cai no ano civil ``civil_year``."""
    return "I" if civil_year % 2 else "II"
