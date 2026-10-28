"""Dados de cada página do livro, prontos para os formatos (PDF, EPUB)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from urllib.parse import quote_plus

from ..content import ContentItem, load_content
from ..data_loader import build_year, load_yaml, DATA_DIR
from ..lectionary import DayReadings, Lectionary, Reading
from ..liturgy import LiturgicalDay, Rank, Season, first_sunday_of_advent
from ..liturgy.temporale import MONTHS
from ..liturgy.model import WEEKDAY_NAMES

__all__ = ["BookDay", "BookYear", "build_book_year", "youtube_search"]

YOUTUBE = "https://www.youtube.com/results?search_query="


def youtube_search(query: str) -> str:
    """URL de busca no YouTube (endereço estável; o resultado muda, o formato não)."""
    return YOUTUBE + quote_plus(query)


@dataclass
class Search:
    label: str
    query: str

    @property
    def url(self) -> str:
        return youtube_search(self.query)


@dataclass
class BookDay:
    day: LiturgicalDay
    readings: DayReadings
    content: list[ContentItem] = field(default_factory=list)

    @property
    def date(self) -> date:
        return self.day.date

    @property
    def date_label(self) -> str:
        d = self.day.date
        return f"{WEEKDAY_NAMES[d.weekday()]}, {d.day} de {MONTHS[d.month - 1]} de {d.year}"

    @property
    def season_label(self) -> str:
        s = self.day.season.label
        if self.day.week and self.day.season in (Season.ADVENT, Season.LENT, Season.EASTER, Season.ORDINARY):
            return f"{s} · {self.day.week}ª semana"
        return s

    @property
    def rank_label(self) -> str | None:
        r = self.day.rank
        return r.label if r in (Rank.SOLEMNITY, Rank.FEAST, Rank.COMMEMORATION) else None

    @property
    def cycle_label(self) -> str:
        d = self.day
        if d.season is Season.ORDINARY and d.date.weekday() != 6 and d.rank is Rank.WEEKDAY:
            return f"Ano {d.sunday_cycle} · ciclo ferial {d.weekday_cycle}"
        return f"Ano {d.sunday_cycle}"

    @property
    def notes(self) -> list[str]:
        out = []
        for m in self.day.memorials:
            out.append(f"{m.rank.label}: {m.name}.")
        if self.readings.proper_memorial:
            out.append("Leituras próprias da memória.")
        out += self.day.notes
        return out

    @property
    def pending(self) -> list[str]:
        return list(self.day.pending) + self.readings.pending

    def _search_name(self) -> str:
        d = self.day
        name = d.name
        if d.date.weekday() == 6 or d.rank in (Rank.SOLEMNITY, Rank.FEAST):
            name += f" ano {d.sunday_cycle}"
        return name

    @property
    def psalm_search(self) -> Search | None:
        psalm = self.readings.get("salmo")
        if not psalm or not psalm.display:
            return None
        # Só a referência e o dia litúrgico: nunca o texto do refrão.
        return Search("Salmo responsorial", f"salmo responsorial {psalm.display} {self._search_name()}")

    @property
    def gospel_search(self) -> Search | None:
        gospel = self.readings.get("evangelho")
        if not gospel or not gospel.display:
            return None
        return Search("Evangelho", f"evangelho {gospel.display} {self._search_name()}")

    def reading_list(self) -> list[Reading]:
        return self.readings.readings


@dataclass
class BookYear:
    year: int
    days: list[BookDay]
    links: list[dict]

    @property
    def sunday_cycle(self) -> str:
        return self.days[0].day.sunday_cycle

    @property
    def weekday_cycle(self) -> str:
        return self.days[0].day.weekday_cycle

    @property
    def title(self) -> str:
        return f"Vitral {self.year}–{self.year + 1}"

    @property
    def subtitle(self) -> str:
        return f"Leituras do ano litúrgico {self.year}–{self.year + 1} · Ano {self.sunday_cycle}"

    @property
    def start(self) -> date:
        return first_sunday_of_advent(self.year)

    def months(self) -> list[tuple[str, list[BookDay]]]:
        out: list[tuple[str, list[BookDay]]] = []
        for bd in self.days:
            label = f"{MONTHS[bd.date.month - 1].capitalize()} de {bd.date.year}"
            if not out or out[-1][0] != label:
                out.append((label, []))
            out[-1][1].append(bd)
        return out

    def highlights(self) -> list[BookDay]:
        """Domingos, solenidades e festas (tabela da abertura)."""
        return [bd for bd in self.days
                if bd.date.weekday() == 6 or (bd.day.rank in (Rank.SOLEMNITY, Rank.FEAST)
                                              and not bd.day.celebration.id.startswith("pascoa-1-"))]

    def contributors(self) -> list[ContentItem]:
        return [c for bd in self.days for c in bd.content]


def build_book_year(year: int) -> BookYear:
    lec = Lectionary.load()
    content = load_content()
    days = []
    for d in build_year(year):
        keys = list(d.lectionary_keys) + [f"santos.{m.id}" for m in d.memorials]
        items = [c for k in dict.fromkeys(keys) for c in content.get(k, [])]
        days.append(BookDay(d, lec.for_day(d), items))
    links = load_yaml(DATA_DIR / "links.yaml")["links"]
    return BookYear(year, days, links)
