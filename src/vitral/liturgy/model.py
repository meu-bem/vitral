"""Tipos básicos do calendário litúrgico.

Os nomes dos membros seguem as Normas Universais sobre o Ano Litúrgico e o
Calendário (NUALC), especialmente a Tabela dos Dias Litúrgicos (n. 59).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum, IntEnum

__all__ = [
    "Season",
    "Color",
    "Rank",
    "Precedence",
    "Celebration",
    "LiturgicalDay",
    "WEEKDAY_KEYS",
    "WEEKDAY_NAMES",
]

# Índice = date.weekday() (segunda=0 ... domingo=6).
WEEKDAY_KEYS = ("segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo")
WEEKDAY_NAMES = (
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
)


class Season(Enum):
    ADVENT = "advento"
    CHRISTMAS = "natal"
    ORDINARY = "tempo-comum"
    LENT = "quaresma"
    TRIDUUM = "triduo-pascal"
    EASTER = "pascoa"

    @property
    def label(self) -> str:
        return {
            Season.ADVENT: "Advento",
            Season.CHRISTMAS: "Tempo do Natal",
            Season.ORDINARY: "Tempo Comum",
            Season.LENT: "Quaresma",
            Season.TRIDUUM: "Tríduo Pascal",
            Season.EASTER: "Tempo Pascal",
        }[self]


class Color(Enum):
    """Cores litúrgicas (IGMR n. 346)."""

    WHITE = "branco"
    RED = "vermelho"
    GREEN = "verde"
    VIOLET = "roxo"
    ROSE = "rosa"
    BLACK = "preto"

    @property
    def label(self) -> str:
        return self.value.capitalize()


class Rank(Enum):
    """Grau da celebração (NUALC n. 10)."""

    SOLEMNITY = "solenidade"
    FEAST = "festa"
    COMMEMORATION = "comemoracao"  # Comemoração de Todos os Fiéis Defuntos
    MEMORIAL = "memoria"
    OPTIONAL_MEMORIAL = "memoria-facultativa"
    SUNDAY = "domingo"
    WEEKDAY = "dia-de-semana"

    @property
    def label(self) -> str:
        return {
            Rank.SOLEMNITY: "Solenidade",
            Rank.FEAST: "Festa",
            Rank.COMMEMORATION: "Comemoração",
            Rank.MEMORIAL: "Memória",
            Rank.OPTIONAL_MEMORIAL: "Memória facultativa",
            Rank.SUNDAY: "Domingo",
            Rank.WEEKDAY: "Dia de semana",
        }[self]


class Precedence(IntEnum):
    """Níveis da Tabela dos Dias Litúrgicos (NUALC n. 59). Menor = mais importante.

    As subdivisões com letras (4a-d, 8a-f, 11a-b) não definem ordem entre si e
    ficam registradas apenas nos dados.
    """

    TRIDUUM = 1
    PRINCIPAL = 2  # Natal, Epifania, Ascensão, Pentecostes, domingos privilegiados etc.
    GENERAL_SOLEMNITY = 3  # inclui a Comemoração dos Fiéis Defuntos
    PROPER_SOLEMNITY = 4
    LORD_FEAST = 5
    SUNDAY = 6  # domingos do Tempo do Natal e do Tempo Comum
    GENERAL_FEAST = 7
    PROPER_FEAST = 8
    PRIVILEGED_WEEKDAY = 9  # Advento 17-24/12, oitava do Natal, Quaresma
    GENERAL_MEMORIAL = 10
    PROPER_MEMORIAL = 11
    OPTIONAL_MEMORIAL = 12
    WEEKDAY = 13


@dataclass
class Celebration:
    """Celebração (do próprio do tempo ou dos santos) candidata a um dia."""

    id: str
    name: str
    rank: Rank
    precedence: Precedence
    color: Color
    lectionary_keys: list[str] = field(default_factory=list)
    # Solenidades que, por concessão, permanecem em domingo privilegiado.
    beats_privileged_sunday: bool = False
    # Memória que prevalece sobre outra memória obrigatória no mesmo dia (memórias marianas).
    prevails_over_memorials: bool = False
    # Regra de transferência nacional (ex.: "domingo-seguinte").
    transfer: str | None = None
    status: str = "verificado"
    sources: list[str] = field(default_factory=list)
    is_temporale: bool = False


@dataclass
class LiturgicalDay:
    """Resultado final para uma data: exatamente um por dia do ano litúrgico."""

    date: date
    liturgical_year: int  # ano civil do 1º Domingo do Advento que abre o ano
    season: Season
    week: int | None  # semana do tempo (None quando não se aplica)
    sunday_cycle: str  # "A", "B" ou "C"
    weekday_cycle: str  # "I" ou "II"
    celebration: Celebration  # a que prevalece no dia e define as leituras
    alt_colors: list[Color] = field(default_factory=list)
    # Memórias do dia. Não substituem as leituras do dia: entram como nota.
    # A primeira obrigatória (se houver e não for dia privilegiado) dá a cor.
    memorials: list[Celebration] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # Motivos pelos quais algum dado do dia ainda não está verificado.
    pending: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.celebration.name

    @property
    def observed_memorial(self) -> Celebration | None:
        """Memória obrigatória celebrada no dia (define a cor), se houver."""
        for m in self.memorials:
            if m.rank is Rank.MEMORIAL:
                return m
        return None

    @property
    def color(self) -> Color:
        memorial = self.observed_memorial
        return memorial.color if memorial else self.celebration.color

    @property
    def rank(self) -> Rank:
        return self.celebration.rank

    @property
    def lectionary_keys(self) -> list[str]:
        return self.celebration.lectionary_keys

    @property
    def status(self) -> str:
        return "pendente" if self.pending else "verificado"
