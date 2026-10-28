"""Montagem do ano litúrgico: próprio do tempo + próprio dos santos + precedência.

Aplica a Tabela dos Dias Litúrgicos (NUALC n. 59) e as regras de ocorrência e
transferência (NUALC nn. 5, 14, 16, 60). Regras sem fonte primária registrada
marcam o dia como pendente em vez de falhar.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta

from .cycles import sunday_cycle, weekday_cycle
from .model import Celebration, LiturgicalDay, Precedence, Rank, Season
from .temporale import NationalRules, TemporaleDay, YearAnchors, build_temporale

__all__ = [
    "SanctoraleEntry",
    "TRANSFER_NEXT_SUNDAY",
    "HOLY_WEEK_TO_MONDAY_AFTER_EASTER_2",
    "build_liturgical_year",
]

ONE_DAY = timedelta(days=1)

# Valores aceitos nos dados (data/calendario/*.yaml).
TRANSFER_NEXT_SUNDAY = "domingo-seguinte"
HOLY_WEEK_TO_MONDAY_AFTER_EASTER_2 = "segunda-apos-2-domingo-da-pascoa"

PENDING_TWO_MEMORIALS = (
    "duas memórias obrigatórias no mesmo dia (ex.: Imaculado Coração de Maria); "
    "falta fonte para a regra de ocorrência"
)
PENDING_TIE = "duas solenidades no mesmo dia; conferir decisão da CNBB/Santa Sé para o ano"


@dataclass
class SanctoraleEntry:
    """Celebração do próprio dos santos (ou móvel fora do próprio do tempo)."""

    celebration: Celebration
    month_day: tuple[int, int] | None = None
    # Data móvel: (âncora de YearAnchors, deslocamento em dias). Ex.: ("pentecost", 1).
    movable: tuple[str, int] | None = None
    # Regra especial quando cai na Semana Santa ou na Oitava da Páscoa (NUALC 60).
    holy_week_rule: str | None = None


@dataclass
class _Candidate:
    celebration: Celebration
    origin: date
    entry: SanctoraleEntry | None = None
    notes: list[str] | None = None
    pending: list[str] | None = None


def _is_privileged_sunday(t: TemporaleDay) -> bool:
    """Domingos do Advento, Quaresma e Páscoa (NUALC 5)."""
    c = t.celebration
    return c.precedence <= Precedence.PRINCIPAL and c.rank is Rank.SUNDAY


def _place_dates(entry: SanctoraleEntry, a: YearAnchors) -> list[date]:
    if entry.movable:
        anchor, offset = entry.movable
        return [getattr(a, anchor) + timedelta(days=offset)]
    assert entry.month_day, f"{entry.celebration.id}: sem data"
    month, day = entry.month_day
    out = []
    for y in (a.year, a.year + 1):
        try:
            d = date(y, month, day)
        except ValueError:  # 29 de fevereiro em ano não bissexto
            continue
        if a.advent <= d <= a.end:
            out.append(d)
    return out


def _fmt(d: date) -> str:
    return f"{d.day:02d}/{d.month:02d}"


def build_liturgical_year(
    year: int,
    rules: NationalRules,
    sanctorale: list[SanctoraleEntry] | None = None,
    date_overrides: dict[tuple[str, date], date] | None = None,
) -> list[LiturgicalDay]:
    """Gera um ``LiturgicalDay`` para cada dia do ano litúrgico ``year``.

    ``year`` é o ano civil do 1º Domingo do Advento que abre o ano litúrgico.
    ``date_overrides`` registra decisões pontuais e documentadas (ex.: a
    Natividade de São João Batista antecipada para 23/6/2022):
    ``{(id_da_celebracao, data_propria): nova_data}``.
    """
    date_overrides = date_overrides or {}
    anchors, temporale = build_temporale(year, rules)
    cyc = sunday_cycle(year)
    fer = weekday_cycle(year + 1)

    # 1. Coloca as celebrações nas datas próprias.
    placed: dict[date, list[_Candidate]] = {d: [] for d in temporale}
    transfers: list[tuple[date, SanctoraleEntry]] = []
    for entry in sanctorale or []:
        for d in _place_dates(entry, anchors):
            moved = date_overrides.get((entry.celebration.id, d))
            if moved is not None and moved in placed:
                placed[moved].append(_Candidate(
                    _with_cycle(entry.celebration, cyc), d, entry,
                    notes=[f"Neste ano, celebrada em {_fmt(moved)} (data própria: {_fmt(d)})."],
                ))
                continue
            if entry.celebration.transfer == TRANSFER_NEXT_SUNDAY and d.weekday() != 6:
                transfers.append((d, entry))
            else:
                placed[d].append(_Candidate(_with_cycle(entry.celebration, cyc), d, entry))

    # 2. Transferências nacionais para o domingo seguinte. Se o domingo já tiver
    #    celebração de grau igual ou maior (além do domingo comum), fica na data
    #    própria (caso de Todos os Santos em 2025, com Finados no domingo).
    for d, entry in transfers:
        target = d + timedelta(days=6 - d.weekday())
        occupied = target in placed and (
            any(c.celebration.precedence <= entry.celebration.precedence for c in placed[target])
            or temporale[target].celebration.precedence <= entry.celebration.precedence
        )
        if target not in temporale or occupied:
            placed[d].append(_Candidate(_with_cycle(entry.celebration, cyc), d, entry))
        else:
            placed[target].append(_Candidate(
                _with_cycle(entry.celebration, cyc), d, entry,
                notes=[f"No Brasil, celebrada no domingo (data própria: {_fmt(d)})."],
            ))

    # 3. Resolve cada dia em ordem. Solenidade impedida vai para o dia livre mais próximo
    #    (NUALC 60); se ele estiver antes, a resolução recomeça com ela já no novo dia.
    back: dict[date, list[_Candidate]] = {}
    for _ in range(10):
        carry: dict[date, list[_Candidate]] = {}
        result: list[LiturgicalDay] = []
        restart = False
        for d in sorted(temporale):
            t = temporale[d]
            candidates = placed[d] + back.get(d, []) + carry.pop(d, [])
            day, moved_back = _resolve(d, t, candidates, anchors, temporale, placed, carry, back, cyc, fer)
            restart = restart or moved_back
            result.append(day)
        if not restart:
            return result
    raise RuntimeError(f"transferências não convergiram no ano {year}")


def _with_cycle(c: Celebration, cyc: str) -> Celebration:
    """Chaves padrão do Lecionário para o próprio dos santos."""
    if c.lectionary_keys:
        return c
    return replace(c, lectionary_keys=[f"{cyc}.santos.{c.id}", f"santos.{c.id}"])


def _resolve(
    d: date,
    t: TemporaleDay,
    candidates: list[_Candidate],
    anchors: YearAnchors,
    temporale: dict[date, TemporaleDay],
    placed: dict[date, list[_Candidate]],
    carry: dict[date, list[_Candidate]],
    back: dict[date, list[_Candidate]],
    cyc: str,
    fer: str,
) -> tuple[LiturgicalDay, bool]:
    notes = list(t.notes)
    moved_back = False
    pending = list(t.pending)
    tcel = t.celebration

    # Precedência efetiva: concessões que vencem domingo privilegiado (ex.: Imaculada no Brasil).
    def eff(c: _Candidate) -> int:
        if c.celebration.beats_privileged_sunday and _is_privileged_sunday(t):
            return int(Precedence.PRINCIPAL) - 1
        return int(c.celebration.precedence)

    proper = [c for c in candidates
              if c.celebration.rank in (Rank.SOLEMNITY, Rank.FEAST, Rank.COMMEMORATION)]
    memorials = [c for c in candidates if c.celebration.rank in (Rank.MEMORIAL, Rank.OPTIONAL_MEMORIAL)]

    winner: _Candidate | None = None
    best = min(proper, key=eff, default=None)
    if best is not None and eff(best) < tcel.precedence:
        winner = best

    # Solenidades/festas que perderam.
    for c in proper:
        if c is winner:
            continue
        if c.celebration.rank is Rank.SOLEMNITY:
            # Empate entre duas celebrações do próprio dos santos: sem regra; fica pendente.
            tie = winner is not None and not winner.celebration.is_temporale and eff(c) == eff(winner)
            moved_back = _transfer(c, d, t, anchors, temporale, placed, carry, back, tie) or moved_back
        # Festas impedidas são omitidas naquele ano (NUALC 60).

    if winner is not None:
        cel = winner.celebration
        notes += winner.notes or []
        pending += winner.pending or []
        if winner.origin != d and not winner.notes:
            notes.append(f"Transferida de {_fmt(winner.origin)}.")
        if cel.status == "pendente":
            pending.append(f"celebração '{cel.id}' com status {cel.status}")
        return LiturgicalDay(
            date=d, liturgical_year=anchors.year, season=t.season, week=t.week,
            sunday_cycle=cyc, weekday_cycle=fer, celebration=cel,
            notes=notes, pending=pending,
        ), moved_back

    # Prevalece o próprio do tempo; memórias se juntam ao dia de semana.
    day_memorials: list[Celebration] = []
    if tcel.rank is Rank.WEEKDAY and tcel.precedence >= Precedence.PRIVILEGED_WEEKDAY:
        privileged = tcel.precedence == Precedence.PRIVILEGED_WEEKDAY
        for c in sorted(memorials, key=lambda c: c.celebration.precedence):
            m = c.celebration
            if privileged and m.rank is Rank.MEMORIAL:
                # NUALC 14 e 16b: em dia privilegiado, só como memória facultativa.
                m = replace(m, rank=Rank.OPTIONAL_MEMORIAL, precedence=Precedence.OPTIONAL_MEMORIAL)
            day_memorials.append(m)
            if m.status == "pendente":
                pending.append(f"celebração '{m.id}' com status {m.status}")
        obligatory = [m for m in day_memorials if m.rank is Rank.MEMORIAL]
        if len(obligatory) > 1:
            marian = [m for m in obligatory if m.prevails_over_memorials]
            if len(marian) == 1:
                # Notificação da Congregação para o Culto Divino (24/3/2018): a memória da
                # Virgem Maria prevalece; a outra é omitida neste ano.
                day_memorials = [m for m in day_memorials if m.rank is not Rank.MEMORIAL or m is marian[0]]
            else:
                pending.append(PENDING_TWO_MEMORIALS)
        # NUALC 15: sábado do Tempo Comum sem memória obrigatória.
        if (t.season is Season.ORDINARY and d.weekday() == 5
                and not any(m.rank is Rank.MEMORIAL for m in day_memorials)):
            notes.append("Pode-se celebrar a memória facultativa de Santa Maria no sábado.")
    return LiturgicalDay(
        date=d, liturgical_year=anchors.year, season=t.season, week=t.week,
        sunday_cycle=cyc, weekday_cycle=fer, celebration=tcel, alt_colors=list(t.alt_colors),
        memorials=day_memorials, notes=notes, pending=pending,
    ), moved_back


def _free(x: date, temporale: dict[date, TemporaleDay], placed: dict[date, list[_Candidate]],
          carry: dict[date, list[_Candidate]], back: dict[date, list[_Candidate]]) -> bool:
    """Dia "não listado nos nn. 1-8" da Tabela e sem outra solenidade/festa (NUALC 60)."""
    if x not in temporale or temporale[x].celebration.precedence <= Precedence.PROPER_FEAST:
        return False
    big = (Rank.SOLEMNITY, Rank.FEAST, Rank.COMMEMORATION)
    return not any(c.celebration.rank in big for c in placed[x] + back.get(x, []) + carry.get(x, []))


def _transfer(
    c: _Candidate,
    d: date,
    t: TemporaleDay,
    anchors: YearAnchors,
    temporale: dict[date, TemporaleDay],
    placed: dict[date, list[_Candidate]],
    carry: dict[date, list[_Candidate]],
    back: dict[date, list[_Candidate]],
    tie: bool,
) -> bool:
    """Transfere uma solenidade impedida (NUALC 5 e 60). Retorna True se foi para trás."""
    pending: list[str] = list(c.pending or [])
    holy_week = anchors.palm_sunday <= d < anchors.easter + timedelta(days=7)
    entry = c.entry
    if holy_week and entry and entry.holy_week_rule == HOLY_WEEK_TO_MONDAY_AFTER_EASTER_2:
        target = anchors.easter + timedelta(days=8)
    elif _is_privileged_sunday(t) and d not in (anchors.palm_sunday, anchors.easter):
        target = d + ONE_DAY  # NUALC 5: segunda-feira seguinte
    else:
        # NUALC 60: o dia livre mais próximo. Em empate, o anterior, como na resposta da
        # Congregação para o Culto Divino de 11/5/2020 (João Batista antecipado para 23/6).
        if any(x.celebration.id == c.celebration.id and x.origin == c.origin
               for xs in back.values() for x in xs):
            return False  # já colocada antes, numa passada anterior
        target = None
        for k in range(1, 60):
            before, after = d - timedelta(days=k), d + timedelta(days=k)
            if _free(before, temporale, placed, carry, back):
                target = before
                break
            if _free(after, temporale, placed, carry, back):
                target = after
                break
    if tie:
        pending.append(PENDING_TIE)
    if target is None or target not in temporale:
        return False  # cairia fora deste ano litúrgico: omitida aqui
    moved = _Candidate(c.celebration, c.origin, entry, notes=[f"Transferida de {_fmt(c.origin)}."], pending=pending)
    if target < d:
        already = any(x.celebration.id == c.celebration.id and x.origin == c.origin for x in back.get(target, []))
        if not already:
            back.setdefault(target, []).append(moved)
            return True
        return False
    carry.setdefault(target, []).append(moved)
    return False
