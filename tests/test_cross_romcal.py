"""Cruzamento do calendário completo com o romcal (segunda fonte independente).

Toda divergência precisa ter uma explicação registrada (ver scripts/compare_calendar.py
e docs/relatorios/calendario-divergencias.md). Divergência nova e sem explicação falha.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from compare_calendar import compare  # noqa: E402


def test_every_divergence_from_romcal_is_explained():
    unexplained = [d for d in compare() if d[4] is None]
    assert unexplained == []


def test_divergences_are_few():
    assert len(compare()) < 100  # 13.510 dias comparados
