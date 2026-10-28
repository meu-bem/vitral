"""Próprio do Tempo: tempos litúrgicos, semanas e celebrações móveis.

Implementa as Normas Universais sobre o Ano Litúrgico e o Calendário (NUALC),
nn. 5-7, 18-44, com as opções nacionais recebidas em ``NationalRules``.

Chaves do Lecionário (``lectionary_keys``) são independentes do ano civil e
vão da mais específica para a mais genérica. Exemplos:
``B.advento-1.domingo``, ``I.tc-10.quarta``, ``quaresma-2.terca``, ``advento.12-17``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from .cycles import sunday_cycle, weekday_cycle
from .easter import easter_date, first_sunday_of_advent
from .model import (
    WEEKDAY_KEYS,
    WEEKDAY_NAMES,
    Celebration,
    Color,
    Precedence,
    Rank,
    Season,
)

__all__ = ["NationalRules", "TemporaleDay", "YearAnchors", "year_anchors", "build_temporale"]

ONE_DAY = timedelta(days=1)
MONTHS = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)

BAPTISM_MONDAY_RULE = "batismo_na_segunda_feira"


@dataclass(frozen=True)
class NationalRules:
    """Opções que a NUALC deixa às Conferências Episcopais (n. 7)."""

    epiphany_on_sunday: bool  # domingo entre 2 e 8 de janeiro
    ascension_on_sunday: bool  # 7º Domingo da Páscoa
    corpus_christi_on_sunday: bool  # domingo depois da Santíssima Trindade
    # Regras aplicadas mas ainda sem fonte verificada: id -> explicação.
    pending_rules: tuple[tuple[str, str], ...] = ()

    def pending_reason(self, rule_id: str) -> str | None:
        return dict(self.pending_rules).get(rule_id)


@dataclass
class TemporaleDay:
    season: Season
    week: int | None
    celebration: Celebration
    alt_colors: list[Color] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class YearAnchors:
    """Datas-âncora de um ano litúrgico."""

    year: int
    advent: date
    christmas: date
    holy_family: date
    mary_mother_of_god: date
    epiphany: date
    baptism: date
    ash_wednesday: date
    palm_sunday: date
    easter: date
    ascension: date
    pentecost: date
    trinity: date
    corpus_christi: date
    sacred_heart: date
    christ_the_king: date
    end: date  # sábado anterior ao Advento seguinte

    def as_dict(self) -> dict[str, date]:
        return {k: v for k, v in self.__dict__.items() if isinstance(v, date)}


def _next_weekday(d: date, weekday: int) -> date:
    """Primeiro dia com ``weekday`` (segunda=0) estritamente depois de ``d``."""
    return d + timedelta(days=(weekday - d.weekday() - 1) % 7 + 1)


def year_anchors(year: int, rules: NationalRules) -> YearAnchors:
    advent = first_sunday_of_advent(year)
    next_advent = first_sunday_of_advent(year + 1)
    christmas = date(year, 12, 25)
    # NUALC 35a: domingo dentro da oitava; se não houver, 30 de dezembro.
    sunday_in_octave = _next_weekday(christmas, 6)
    holy_family = sunday_in_octave if sunday_in_octave.year == year else date(year, 12, 30)
    jan1 = date(year + 1, 1, 1)
    if rules.epiphany_on_sunday:
        epiphany = _next_weekday(jan1, 6)  # domingo entre 2 e 8 de janeiro (NUALC 7a)
    else:
        epiphany = date(year + 1, 1, 6)
    if rules.epiphany_on_sunday and epiphany.day >= 7:
        baptism = epiphany + ONE_DAY  # segunda-feira seguinte (regra BAPTISM_MONDAY_RULE)
    else:
        baptism = _next_weekday(date(year + 1, 1, 6), 6)  # NUALC 38
    easter = easter_date(year + 1)
    pentecost = easter + timedelta(days=49)
    trinity = pentecost + timedelta(days=7)
    return YearAnchors(
        year=year,
        advent=advent,
        christmas=christmas,
        holy_family=holy_family,
        mary_mother_of_god=jan1,
        epiphany=epiphany,
        baptism=baptism,
        ash_wednesday=easter - timedelta(days=46),
        palm_sunday=easter - timedelta(days=7),
        easter=easter,
        ascension=easter + timedelta(days=42 if rules.ascension_on_sunday else 39),
        pentecost=pentecost,
        trinity=trinity,
        corpus_christi=trinity + timedelta(days=7 if rules.corpus_christi_on_sunday else 4),
        sacred_heart=pentecost + timedelta(days=19),  # sexta-feira após o 2º domingo depois de Pentecostes
        christ_the_king=next_advent - timedelta(days=7),  # NUALC 6d
        end=next_advent - ONE_DAY,
    )


def _date_label(d: date) -> str:
    return f"{d.day} de {MONTHS[d.month - 1]}"


def _mmdd(d: date) -> str:
    return f"{d.month:02d}-{d.day:02d}"


def _cel(
    id_: str,
    name: str,
    rank: Rank,
    precedence: Precedence,
    color: Color,
    keys: list[str],
) -> Celebration:
    # Toda chave com ciclo ganha a forma genérica como alternativa (ex.: A.advento-1.segunda
    # -> advento-1.segunda): o Lecionário só traz a variante do ciclo quando ela existe.
    expanded: list[str] = []
    for k in keys:
        expanded.append(k)
        generic = re.sub(r"^(A|B|C|I|II)\.", "", k)
        if generic != k and generic not in keys:
            expanded.append(generic)
    keys = list(dict.fromkeys(expanded))
    return Celebration(
        id=id_,
        name=name,
        rank=rank,
        precedence=precedence,
        color=color,
        lectionary_keys=keys,
        is_temporale=True,
        sources=["NUALC"],
    )


def build_temporale(year: int, rules: NationalRules) -> tuple[YearAnchors, dict[date, TemporaleDay]]:
    """Calcula o próprio do tempo para cada dia do ano litúrgico ``year``.

    ``year`` é o ano civil em que cai o 1º Domingo do Advento.
    """
    a = year_anchors(year, rules)
    cyc = sunday_cycle(year)
    fer = weekday_cycle(year + 1)  # o Tempo Comum inteiro cai no ano civil seguinte
    days: dict[date, TemporaleDay] = {}

    d = a.advent
    while d <= a.end:
        days[d] = _temporale_day(d, a, cyc, fer)
        d += ONE_DAY
    reason = rules.pending_reason(BAPTISM_MONDAY_RULE)
    if reason and a.baptism.weekday() == 0:
        days[a.baptism].pending.append(reason)
    return a, days


def _temporale_day(d: date, a: YearAnchors, cyc: str, fer: str) -> TemporaleDay:
    wd = d.weekday()
    wkey = WEEKDAY_KEYS[wd]
    wname = WEEKDAY_NAMES[wd]
    sunday = wd == 6
    P, R, C = Precedence, Rank, Color

    # ----- Advento (NUALC 39-42) -----
    if d < a.christmas:
        week = (d - a.advent).days // 7 + 1
        if sunday:
            alt = [C.ROSE] if week == 3 else []
            return TemporaleDay(
                Season.ADVENT, week,
                _cel(f"advento-{week}-domingo", f"{week}º Domingo do Advento", R.SUNDAY,
                     P.PRINCIPAL, C.VIOLET, [f"{cyc}.advento-{week}.domingo"]),
                alt_colors=alt,
            )
        if d.month == 12 and d.day >= 17:
            return TemporaleDay(
                Season.ADVENT, week,
                _cel(f"advento-{_mmdd(d)}", f"{wname}, {_date_label(d)} (Advento)", R.WEEKDAY,
                     P.PRIVILEGED_WEEKDAY, C.VIOLET, [f"advento.{_mmdd(d)}"]),
            )
        return TemporaleDay(
            Season.ADVENT, week,
            _cel(f"advento-{week}-{wkey}", f"{wname} da {week}ª Semana do Advento", R.WEEKDAY,
                 P.WEEKDAY, C.VIOLET, [f"{cyc}.advento-{week}.{wkey}"]),
        )

    # ----- Tempo do Natal (NUALC 32-38) -----
    if d <= a.baptism:
        if d == a.christmas:
            cel = _cel("natal-do-senhor", "Natal do Senhor", R.SOLEMNITY, P.PRINCIPAL, C.WHITE,
                       ["natal.natal-do-senhor"])
        elif d == a.holy_family:
            cel = _cel("sagrada-familia", "Sagrada Família de Jesus, Maria e José", R.FEAST,
                       P.LORD_FEAST, C.WHITE, [f"{cyc}.natal.sagrada-familia", "natal.sagrada-familia"])
        elif d.year == a.year:  # 26 a 31 de dezembro
            cel = _cel(f"natal-{_mmdd(d)}", f"{wname}, {_date_label(d)} (Oitava do Natal)", R.WEEKDAY,
                       P.PRIVILEGED_WEEKDAY, C.WHITE, [f"natal.{_mmdd(d)}"])
        elif d == a.mary_mother_of_god:
            cel = _cel("santa-maria-mae-de-deus", "Santa Maria, Mãe de Deus", R.SOLEMNITY,
                       P.GENERAL_SOLEMNITY, C.WHITE, ["natal.santa-maria-mae-de-deus"])
        elif d == a.epiphany:
            cel = _cel("epifania", "Epifania do Senhor", R.SOLEMNITY, P.PRINCIPAL, C.WHITE,
                       ["natal.epifania"])
        elif d == a.baptism:
            cel = _cel("batismo-do-senhor", "Batismo do Senhor", R.FEAST, P.LORD_FEAST, C.WHITE,
                       [f"{cyc}.natal.batismo-do-senhor", "natal.batismo-do-senhor"])
            return TemporaleDay(Season.CHRISTMAS, None, cel)
        elif sunday:  # só ocorre onde a Epifania é fixa em 6/1 (NUALC 36)
            cel = _cel("natal-2-domingo", "2º Domingo depois do Natal", R.SUNDAY, P.SUNDAY, C.WHITE,
                       [f"{cyc}.natal-2.domingo", "natal-2.domingo"])
        elif d < a.epiphany:
            cel = _cel(f"natal-{_mmdd(d)}", f"{wname}, {_date_label(d)} (Tempo do Natal)", R.WEEKDAY,
                       P.WEEKDAY, C.WHITE, [f"natal.{_mmdd(d)}"])
        else:
            cel = _cel(f"natal-depois-epifania-{wkey}", f"{wname} depois da Epifania", R.WEEKDAY,
                       P.WEEKDAY, C.WHITE, [f"natal.depois-da-epifania.{wkey}", f"natal.{_mmdd(d)}"])
        return TemporaleDay(Season.CHRISTMAS, None, cel)

    # ----- Tempo Comum, 1ª parte (NUALC 43-44) -----
    if d < a.ash_wednesday:
        anchor = a.baptism - timedelta(days=(a.baptism.weekday() + 1) % 7)  # domingo do Batismo/Epifania
        week = (d - anchor).days // 7 + 1
        return _ordinary_day(d, week, cyc, fer)

    # ----- Quaresma (NUALC 27-31) -----
    if d < a.palm_sunday:
        if d == a.ash_wednesday:
            return TemporaleDay(Season.LENT, 0, _cel(
                "quarta-feira-de-cinzas", "Quarta-feira de Cinzas", R.WEEKDAY, P.PRINCIPAL, C.VIOLET,
                ["quaresma.cinzas"]))
        week = (d - (a.ash_wednesday + timedelta(days=4))).days // 7 + 1
        if week == 0:
            return TemporaleDay(Season.LENT, 0, _cel(
                f"quaresma-0-{wkey}", f"{wname} depois das Cinzas", R.WEEKDAY,
                P.PRIVILEGED_WEEKDAY, C.VIOLET, [f"{cyc}.quaresma-0.{wkey}"]))
        if sunday:
            alt = [C.ROSE] if week == 4 else []
            return TemporaleDay(Season.LENT, week, _cel(
                f"quaresma-{week}-domingo", f"{week}º Domingo da Quaresma", R.SUNDAY, P.PRINCIPAL,
                C.VIOLET, [f"{cyc}.quaresma-{week}.domingo"]), alt_colors=alt)
        return TemporaleDay(Season.LENT, week, _cel(
            f"quaresma-{week}-{wkey}", f"{wname} da {week}ª Semana da Quaresma", R.WEEKDAY,
            P.PRIVILEGED_WEEKDAY, C.VIOLET, [f"{cyc}.quaresma-{week}.{wkey}"]))

    # ----- Semana Santa e Tríduo Pascal (NUALC 18-21, 30-31) -----
    if d < a.easter:
        offset = (d - a.palm_sunday).days
        if offset == 0:
            return TemporaleDay(Season.LENT, 6, _cel(
                "domingo-de-ramos", "Domingo de Ramos da Paixão do Senhor", R.SUNDAY, P.PRINCIPAL,
                C.RED, [f"{cyc}.semana-santa.ramos"]))
        if offset <= 3:
            return TemporaleDay(Season.LENT, 6, _cel(
                f"semana-santa-{wkey}", f"{wname} da Semana Santa", R.WEEKDAY, P.PRINCIPAL,
                C.VIOLET, [f"{cyc}.semana-santa.{wkey}"]))
        if offset == 4:
            return TemporaleDay(
                Season.LENT, 6,
                _cel("quinta-feira-santa", "Quinta-feira Santa", R.WEEKDAY, P.PRINCIPAL, C.VIOLET,
                     ["triduo.quinta-feira-santa"]),
                alt_colors=[C.WHITE],
                notes=["À tarde, Missa da Ceia do Senhor: começa o Tríduo Pascal."],
            )
        if offset == 5:
            return TemporaleDay(Season.TRIDUUM, None, _cel(
                "sexta-feira-santa", "Sexta-feira da Paixão do Senhor", R.WEEKDAY, P.TRIDUUM, C.RED,
                ["triduo.sexta-feira-santa"]))
        return TemporaleDay(
            Season.TRIDUUM, None,
            _cel("sabado-santo", "Sábado Santo", R.WEEKDAY, P.TRIDUUM, C.VIOLET,
                 [f"{cyc}.triduo.vigilia-pascal", "triduo.vigilia-pascal"]),
            alt_colors=[C.WHITE],
            notes=["À noite, Vigília Pascal."],
        )

    # ----- Tempo Pascal (NUALC 22-26) -----
    if d <= a.pentecost:
        week = (d - a.easter).days // 7 + 1
        if d == a.easter:
            return TemporaleDay(Season.EASTER, 1, _cel(
                "pascoa", "Domingo da Páscoa da Ressurreição do Senhor", R.SOLEMNITY, P.TRIDUUM,
                C.WHITE, [f"{cyc}.pascoa.domingo", "pascoa.domingo"]))
        if d == a.ascension:
            return TemporaleDay(Season.EASTER, week, _cel(
                "ascensao", "Ascensão do Senhor", R.SOLEMNITY, P.PRINCIPAL, C.WHITE,
                [f"{cyc}.pascoa.ascensao", "pascoa.ascensao"]))
        if d == a.pentecost:
            return TemporaleDay(Season.EASTER, week, _cel(
                "pentecostes", "Domingo de Pentecostes", R.SOLEMNITY, P.PRINCIPAL, C.RED,
                [f"{cyc}.pascoa.pentecostes", "pascoa.pentecostes"]))
        if week == 1:
            return TemporaleDay(Season.EASTER, 1, _cel(
                f"pascoa-1-{wkey}", f"{wname} da Oitava da Páscoa", R.SOLEMNITY, P.PRINCIPAL,
                C.WHITE, [f"{cyc}.pascoa-1.{wkey}"]))
        if sunday:
            return TemporaleDay(Season.EASTER, week, _cel(
                f"pascoa-{week}-domingo", f"{week}º Domingo da Páscoa", R.SUNDAY, P.PRINCIPAL,
                C.WHITE, [f"{cyc}.pascoa-{week}.domingo"]))
        return TemporaleDay(Season.EASTER, week, _cel(
            f"pascoa-{week}-{wkey}", f"{wname} da {week}ª Semana da Páscoa", R.WEEKDAY, P.WEEKDAY,
            C.WHITE, [f"{cyc}.pascoa-{week}.{wkey}"]))

    # ----- Tempo Comum, 2ª parte: conta para trás a partir da 34ª semana -----
    week_sunday = d - timedelta(days=(wd + 1) % 7)
    week = 34 - (a.christ_the_king - week_sunday).days // 7
    if d == a.trinity:
        return TemporaleDay(Season.ORDINARY, week, _cel(
            "santissima-trindade", "Santíssima Trindade", R.SOLEMNITY, P.GENERAL_SOLEMNITY,
            C.WHITE, [f"{cyc}.tc.santissima-trindade", "tc.santissima-trindade"]))
    if d == a.corpus_christi:
        return TemporaleDay(Season.ORDINARY, week, _cel(
            "corpo-e-sangue-de-cristo", "Santíssimo Corpo e Sangue de Cristo", R.SOLEMNITY,
            P.GENERAL_SOLEMNITY, C.WHITE, [f"{cyc}.tc.corpo-e-sangue-de-cristo", "tc.corpo-e-sangue-de-cristo"]))
    if d == a.sacred_heart:
        return TemporaleDay(Season.ORDINARY, week, _cel(
            "sagrado-coracao-de-jesus", "Sagrado Coração de Jesus", R.SOLEMNITY,
            P.GENERAL_SOLEMNITY, C.WHITE, [f"{cyc}.tc.sagrado-coracao-de-jesus", "tc.sagrado-coracao-de-jesus"]))
    if d == a.christ_the_king:
        return TemporaleDay(Season.ORDINARY, 34, _cel(
            "cristo-rei", "Nosso Senhor Jesus Cristo, Rei do Universo", R.SOLEMNITY,
            P.GENERAL_SOLEMNITY, C.WHITE, [f"{cyc}.tc.cristo-rei", "tc.cristo-rei"]))
    return _ordinary_day(d, week, cyc, fer)


def _ordinary_day(d: date, week: int, cyc: str, fer: str) -> TemporaleDay:
    wd = d.weekday()
    if wd == 6:
        cel = _cel(f"tc-{week}-domingo", f"{week}º Domingo do Tempo Comum", Rank.SUNDAY,
                   Precedence.SUNDAY, Color.GREEN, [f"{cyc}.tc-{week}.domingo"])
    else:
        wkey = WEEKDAY_KEYS[wd]
        cel = _cel(f"tc-{week}-{wkey}", f"{WEEKDAY_NAMES[wd]} da {week}ª Semana do Tempo Comum",
                   Rank.WEEKDAY, Precedence.WEEKDAY, Color.GREEN, [f"{fer}.tc-{week}.{wkey}"])
    return TemporaleDay(Season.ORDINARY, week, cel)
