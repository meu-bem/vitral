"""Calendário litúrgico (rito romano) em Python puro, sem dependências externas."""

from .builder import SanctoraleEntry, build_liturgical_year
from .cycles import sunday_cycle, weekday_cycle
from .easter import easter_date, first_sunday_of_advent
from .model import Celebration, Color, LiturgicalDay, Precedence, Rank, Season
from .temporale import NationalRules, build_temporale, year_anchors

__all__ = [
    "Celebration",
    "Color",
    "LiturgicalDay",
    "NationalRules",
    "Precedence",
    "Rank",
    "SanctoraleEntry",
    "Season",
    "build_liturgical_year",
    "build_temporale",
    "easter_date",
    "first_sunday_of_advent",
    "sunday_cycle",
    "weekday_cycle",
    "year_anchors",
]
