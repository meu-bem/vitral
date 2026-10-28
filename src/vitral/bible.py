"""Referências bíblicas: leitura, normalização, versificação e formato brasileiro.

Formato de saída (padrão dos lecionários brasileiros):
``Is 63,16b-17.19b;64,2b-7``, ``Sl 79(80),2ac.3b.15-16``, ``Gn 1,1-2,2``.

- vírgula separa capítulo e versículo; ponto separa versículos; ponto e
  vírgula separa capítulos; hífen indica intervalo;
- salmos com a numeração grega (litúrgica) seguida da hebraica entre parênteses;
- versículos na numeração hebraica (versificação "org"), a das Bíblias
  católicas brasileiras.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

__all__ = ["Book", "BOOKS", "Segment", "Ref", "parse_ref", "book_by_code", "Versification"]


@dataclass(frozen=True)
class Book:
    code: str  # código USFM (GEN, PSA, MAT...)
    br: str  # abreviação brasileira
    en: tuple[str, ...]  # nomes ingleses aceitos na leitura de fontes
    br_checked: bool = True  # abreviação conferida no Diretório (docs/FONTES.md)


_B = Book
# Ordem do cânon católico. Abreviações com br_checked=False não apareceram nos
# Diretórios consultados e seguem o mesmo padrão; conferir quando houver fonte.
BOOKS: tuple[Book, ...] = (
    _B("GEN", "Gn", ("Genesis",)), _B("EXO", "Ex", ("Exodus",)), _B("LEV", "Lv", ("Leviticus",)),
    _B("NUM", "Nm", ("Numbers",)), _B("DEU", "Dt", ("Deuteronomy",)), _B("JOS", "Js", ("Joshua",)),
    _B("JDG", "Jz", ("Judges",)), _B("RUT", "Rt", ("Ruth",), False),
    _B("1SA", "1Sm", ("1 Samuel",)), _B("2SA", "2Sm", ("2 Samuel",)),
    _B("1KI", "1Rs", ("1 Kings",)), _B("2KI", "2Rs", ("2 Kings",)),
    _B("1CH", "1Cr", ("1 Chronicles",)), _B("2CH", "2Cr", ("2 Chronicles",)),
    _B("EZR", "Esd", ("Ezra",)), _B("NEH", "Ne", ("Nehemiah",)), _B("TOB", "Tb", ("Tobit",)),
    _B("JDT", "Jt", ("Judith",), False), _B("EST", "Est", ("Esther",)),
    _B("1MA", "1Mc", ("1 Maccabees",)), _B("2MA", "2Mc", ("2 Maccabees",)),
    _B("JOB", "Jó", ("Job",)), _B("PSA", "Sl", ("Psalm", "Psalms")), _B("PRO", "Pr", ("Proverbs",)),
    _B("ECC", "Ecl", ("Ecclesiastes",)), _B("SNG", "Ct", ("Song of Songs", "Song of Solomon")),
    _B("WIS", "Sb", ("Wisdom",)), _B("SIR", "Eclo", ("Sirach", "Ecclesiasticus")),
    _B("ISA", "Is", ("Isaiah",)), _B("JER", "Jr", ("Jeremiah",)), _B("LAM", "Lm", ("Lamentations",), False),
    _B("BAR", "Br", ("Baruch",)), _B("EZK", "Ez", ("Ezekiel",)), _B("DAN", "Dn", ("Daniel",)),
    _B("HOS", "Os", ("Hosea",)), _B("JOL", "Jl", ("Joel",)), _B("AMO", "Am", ("Amos",)),
    _B("OBA", "Ab", ("Obadiah",), False), _B("JON", "Jn", ("Jonah",)), _B("MIC", "Mq", ("Micah",)),
    _B("NAM", "Na", ("Nahum",)), _B("HAB", "Hab", ("Habakkuk",)), _B("ZEP", "Sf", ("Zephaniah",)),
    _B("HAG", "Ag", ("Haggai",)), _B("ZEC", "Zc", ("Zechariah",)), _B("MAL", "Ml", ("Malachi",)),
    _B("MAT", "Mt", ("Matthew",)), _B("MRK", "Mc", ("Mark",)), _B("LUK", "Lc", ("Luke",)),
    _B("JHN", "Jo", ("John",)), _B("ACT", "At", ("Acts",)), _B("ROM", "Rm", ("Romans",)),
    _B("1CO", "1Cor", ("1 Corinthians",)), _B("2CO", "2Cor", ("2 Corinthians",)),
    _B("GAL", "Gl", ("Galatians",)), _B("EPH", "Ef", ("Ephesians",)), _B("PHP", "Fl", ("Philippians",)),
    _B("COL", "Cl", ("Colossians",)), _B("1TH", "1Ts", ("1 Thessalonians",)),
    _B("2TH", "2Ts", ("2 Thessalonians",)), _B("1TI", "1Tm", ("1 Timothy",)),
    _B("2TI", "2Tm", ("2 Timothy",)), _B("TIT", "Tt", ("Titus",)), _B("PHM", "Fm", ("Philemon",)),
    _B("HEB", "Hb", ("Hebrews",)), _B("JAS", "Tg", ("James",)), _B("1PE", "1Pd", ("1 Peter",)),
    _B("2PE", "2Pd", ("2 Peter",)), _B("1JN", "1Jo", ("1 John",)), _B("2JN", "2Jo", ("2 John",)),
    _B("3JN", "3Jo", ("3 John",)), _B("JUD", "Jd", ("Jude",), False), _B("REV", "Ap", ("Revelation",)),
)
_BY_CODE = {b.code: b for b in BOOKS}
_BY_BR = {b.br: b for b in BOOKS}
_BY_EN = {name.lower(): b for b in BOOKS for name in b.en}


def book_by_code(code: str) -> Book:
    return _BY_CODE[code]


@dataclass(frozen=True)
class Segment:
    """Trecho contínuo: de c1,v1(l1) até c2,v2(l2). v1=None indica capítulo inteiro."""

    c1: int
    v1: int | None
    l1: str = ""
    c2: int | None = None
    v2: int | None = None
    l2: str = ""

    @property
    def end_chapter(self) -> int:
        return self.c2 if self.c2 is not None else self.c1

    @property
    def end_verse(self) -> int | None:
        return self.v2 if self.v2 is not None else self.v1


@dataclass(frozen=True)
class Ref:
    book: str  # código USFM
    segments: tuple[Segment, ...]
    cf: bool = False

    # ---------- saída ----------
    def br(self) -> str:
        """Formato brasileiro, ex.: ``Is 63,16b-17.19b;64,2b-7``."""
        b = _BY_CODE[self.book]
        parts: list[str] = []
        current: int | None = None
        for s in self.segments:
            if s.v1 is None:
                parts.append(("; " if parts else "") + str(s.c1))
                current = s.c1
                continue
            start = f"{s.v1}{s.l1}"
            if s.c2 is not None and s.c2 != s.c1:
                end = f"-{s.c2},{s.v2}{s.l2}"
            elif s.v2 is not None and (s.v2 != s.v1 or s.l2 != s.l1):
                end = f"-{s.v2}{s.l2}" if s.v2 != s.v1 else f"-{s.l2}"
            else:
                end = ""
            if s.c1 != current:
                chap = str(s.c1)
                if self.book == "PSA" and parts:  # outro salmo na mesma referência: "Sl 42(43),3.4"
                    chap = "Sl " + psalm_label(Ref("PSA", (s,)))
                parts.append((";" if parts else "") + f"{chap},{start}{end}")
            else:
                parts.append(f".{start}{end}")
            current = s.end_chapter
        body = "".join(parts)
        if self.book in SINGLE_CHAPTER and body.startswith("1,"):
            body = body[2:]
        prefix = "cf. " if self.cf else ""
        if self.book == "PSA":
            return prefix + f"Sl {psalm_label(self)}" + body[len(str(self.segments[0].c1)):]
        return prefix + f"{b.br} {body}"

    def chapter_level(self) -> str:
        """Só livro e capítulo(s), ex.: ``Os 6`` ou ``Ml 3-4`` (usado quando versículos divergem)."""
        chapters = sorted({c for s in self.segments for c in range(s.c1, s.end_chapter + 1)})
        if self.book == "PSA":
            return f"Sl {psalm_label(self)}"
        b = _BY_CODE[self.book]
        if len(chapters) == 1:
            return f"{b.br} {chapters[0]}"
        if chapters == list(range(chapters[0], chapters[-1] + 1)):
            return f"{b.br} {chapters[0]}-{chapters[-1]}"
        return f"{b.br} " + "; ".join(map(str, chapters))

    # ---------- comparação ----------
    def verses(self, max_verses: dict[str, list[int]]) -> frozenset[tuple[int, int]]:
        """Conjunto de versículos inteiros tocados (letras de meio-versículo ignoradas)."""
        mv = max_verses.get(self.book, [])
        out: set[tuple[int, int]] = set()
        for s in self.segments:
            if s.v1 is None:
                last = mv[s.c1 - 1] if s.c1 - 1 < len(mv) else 0
                out.update((s.c1, v) for v in range(1, last + 1))
                continue
            c, v = s.c1, s.v1
            ec, ev = s.end_chapter, s.end_verse
            while (c, v) <= (ec, ev):
                out.add((c, v))
                last = mv[c - 1] if c - 1 < len(mv) else ev
                if v >= last and c < ec:
                    c, v = c + 1, 1
                else:
                    v += 1
        return frozenset(out)

    @classmethod
    def from_verses(cls, book: str, verses: frozenset[tuple[int, int]],
                    max_verses: dict[str, list[int]], cf: bool = False) -> "Ref":
        """Monta a referência mais compacta para um conjunto de versículos inteiros."""
        mv = max_verses.get(book, [])
        segs: list[Segment] = []
        start = prev = None
        for c, v in sorted(verses):
            if prev is not None:
                pc, pv = prev
                contiguous = (c == pc and v == pv + 1) or (
                    c == pc + 1 and v == 1 and pc - 1 < len(mv) and pv == mv[pc - 1])
                if contiguous:
                    prev = (c, v)
                    continue
                segs.append(_seg(start, prev))
            start = prev = (c, v)
        if start is not None:
            segs.append(_seg(start, prev))
        return cls(book, tuple(segs), cf)

    def normalized(self, max_verses: dict[str, list[int]] | None = None) -> tuple:
        """Forma canônica para comparar fontes: junta trechos contíguos."""
        segs: list[list] = []
        for s in self.segments:
            cur = [s.c1, s.v1, s.l1, s.end_chapter, s.end_verse, s.l2 if s.v2 is not None else s.l1]
            if segs:
                p = segs[-1]
                if (p[5] == "" and cur[2] == "" and cur[1] is not None and p[4] is not None
                        and _follows(self.book, p[3], p[4], cur[0], cur[1], max_verses)):
                    p[3], p[4], p[5] = cur[3], cur[4], cur[5]
                    continue
            segs.append(cur)
        return (self.book, tuple(tuple(x) for x in segs))


def _seg(start: tuple[int, int], end: tuple[int, int]) -> Segment:
    if start == end:
        return Segment(start[0], start[1])
    if start[0] == end[0]:
        return Segment(start[0], start[1], "", None, end[1])
    return Segment(start[0], start[1], "", end[0], end[1])


def _follows(book, c, v, c2, v2, max_verses) -> bool:
    if c == c2:
        return v2 == v + 1
    if c2 == c + 1 and v2 == 1 and max_verses and book in max_verses:
        mv = max_verses[book]
        return c - 1 < len(mv) and v == mv[c - 1]
    return False


# ---------------------------------------------------------------- salmos
def greek_psalm(hebrew: int, first_verse: int | None) -> str:
    """Número grego/litúrgico do salmo, com A/B quando um salmo hebraico se divide."""
    v = first_verse or 1
    if hebrew <= 8 or hebrew >= 148:
        return str(hebrew)
    if hebrew == 9:
        return "9A"
    if hebrew == 10:
        return "9B"
    if hebrew == 114:
        return "113A"
    if hebrew == 115:
        return "113B"
    if hebrew == 116:
        return "114" if v <= 9 else "115"
    if hebrew == 147:
        return "146" if v <= 11 else "147"
    return str(hebrew - 1)


def psalm_label(ref: Ref) -> str:
    """Ex.: ``79(80)``, ``113A(114)``, ``115(116B)``, ``146(147A)``."""
    h = ref.segments[0].c1
    g = greek_psalm(h, ref.segments[0].v1)
    if h <= 8 or h >= 148:  # mesma numeração nas duas tradições
        return g
    heb = str(h)
    if h == 116:
        heb += "A" if g == "114" else "B"
    elif h == 147:
        heb += "A" if g == "146" else "B"
    return f"{g}({heb})"


# ---------------------------------------------------------------- leitura
_VERSE = r"(\d+)([a-z]*)"


def parse_ref(text: str, style: str) -> Ref:
    """Lê uma referência.

    ``style``: ``"br"`` (Is 63,16b-17.19b), ``"en"`` (Isaiah 63:16b-17, 19b) ou
    ``"ta"`` (já com o código do livro resolvido: ``ISA|2:1-5``).
    """
    text = text.strip()
    cf = False
    if style == "en" and text.lower().startswith("cf."):
        cf, text = True, text[3:].strip()
    if style == "br" and text.lower().startswith("cf."):
        cf, text = True, text[3:].strip()
    if style == "ta":
        code, spec = text.split("|", 1)
        return Ref(code, _parse_spec(spec, ":", ",.", code), cf="காண்க" in spec)
    if style == "en":
        m = re.match(r"^((?:[1-3] )?[A-Za-z][A-Za-z ]*?)\s*(\d.*)?$", text)
        if not m:
            raise ValueError(f"referência inválida: {text!r}")
        name, spec = m.group(1).strip().lower(), (m.group(2) or "")
        if name not in _BY_EN:
            raise ValueError(f"livro desconhecido: {text!r}")
        spec = spec.replace(" and ", ",")
        if _BY_EN[name].code == "PSA":  # "18 (19)": numeração grega com a hebraica entre parênteses
            spec = re.sub(r"^\d+\s*\((\d+)\)", r"\1", spec)
        return Ref(_BY_EN[name].code, _parse_spec(spec, ":", ",", _BY_EN[name].code), cf)
    if style == "br":
        m = re.match(r"^([1-3]?[A-Za-zÀ-ú]+)\s+(.*)$", text)
        if not m or m.group(1) not in _BY_BR:
            raise ValueError(f"referência inválida: {text!r}")
        book = _BY_BR[m.group(1)]
        spec = m.group(2).replace(" e ", ".")
        if book.code == "PSA":  # "79(80),2-3" -> usa o número hebraico
            pm = re.match(r"^\d+[AB]?\((\d+)[AB]?\)(.*)$", spec)
            if not pm and re.match(r"^([1-8]|14[89]|150)(,|$)", spec):
                pm = re.match(r"^(\d+)(.*)$", spec)
            if not pm:
                raise ValueError(f"salmo sem numeração hebraica: {text!r}")
            spec = pm.group(1) + re.sub(r";\s*Sl\s*\d+[AB]?\((\d+)[AB]?\)", r";\1", pm.group(2))
        return Ref(book.code, _parse_spec(spec, ",", ".", book.code), cf)
    raise ValueError(style)


SINGLE_CHAPTER = {"OBA", "PHM", "2JN", "3JN", "JUD"}


def _parse_spec(spec: str, chv: str, seps: str, book: str = "") -> tuple[Segment, ...]:
    spec = re.sub(r"~.*$", "", spec)  # ponteiros internos da fonte tâmil
    spec = re.sub(r"[^\d a-z:;,.\-]", "", spec.replace("–", "-")).replace(" ", "")
    if book in SINGLE_CHAPTER and chv not in spec:  # "Fm 7-20" = capítulo único
        spec = f"1{chv}{spec}"
    if not spec:
        return ()
    segments: list[Segment] = []
    for group in filter(None, spec.split(";")):
        if chv in group:
            chap_str, rest = group.split(chv, 1)
        else:
            chap_str, rest = group, ""
        if not chap_str.isdigit():
            raise ValueError(f"capítulo inválido em {spec!r}")
        chapter = int(chap_str)
        if not rest:
            segments.append(Segment(chapter, None))
            continue
        # Em "en" e "ta" a vírgula separa itens; em "br" a vírgula é capítulo:versículo.
        items = re.split("[" + re.escape(seps) + "]", rest) if chv != "," else rest.split(".")
        last_verse: int | None = None
        for item in filter(None, items):
            lm = re.fullmatch(r"([a-z]+)(?:-([a-z]+))?", item)
            if lm and last_verse is not None:  # só letras: mesmo versículo, ex.: "4,17k-m.r-t"
                segments.append(Segment(chapter, last_verse, lm[1], None,
                                        last_verse if lm[2] else None, lm[2] or ""))
                continue
            if chv != "," and chv in item and not re.match(r"^\d+[a-z]*-", item):
                # novo capítulo dentro da lista, ex.: "15:41-16:5, 16:22b"
                chap_str, item = item.split(chv, 1)
                chapter = int(chap_str)
            seg, chapter = _parse_item(item, chapter, chv)
            if seg is not None:
                last_verse = seg.end_verse
            if seg is None:  # continuação "-2" depois de um intervalo entre capítulos
                last = segments.pop()
                segments.append(Segment(last.c1, last.v1, last.l1, last.c2, int(item.lstrip("-")), ""))
                continue
            segments.append(seg)
    return tuple(segments)


def _parse_item(item: str, chapter: int, chv: str) -> tuple[Segment | None, int]:
    if re.fullmatch(r"-\d+", item):
        return None, chapter
    m = re.fullmatch(
        _VERSE + r"(?:-(?:(\d+)" + re.escape(chv) + r")?(\d*)([a-z]*))?(?:-(\d+))?", item)
    if not m:
        raise ValueError(f"trecho inválido: {item!r}")
    v1, l1 = int(m.group(1)), m.group(2)
    if m.group(3):  # intervalo entre capítulos, ex.: 1,14b-2,2
        c2, v2, l2 = int(m.group(3)), int(m.group(4)), m.group(5)
        if m.group(6):  # forma "1:14b-2:1-2" = até 2:2
            v2, l2 = int(m.group(6)), ""
        return Segment(chapter, v1, l1, c2, v2, l2), c2
    if m.group(4) or m.group(5):
        v2 = int(m.group(4)) if m.group(4) else v1
        return Segment(chapter, v1, l1, None, v2, m.group(5)), chapter
    return Segment(chapter, v1, l1), chapter


# ---------------------------------------------------------------- versificação
class Versification:
    """Converte versículos de uma versificação (ex.: "eng") para a hebraica ("org").

    Usa os mapeamentos da Copenhagen Alliance (CC BY-SA 4.0), em data/fontes/versificacao.
    """

    def __init__(self, mapping_file: Path, org_file: Path):
        doc = json.loads(mapping_file.read_text(encoding="utf-8"))
        org = json.loads(org_file.read_text(encoding="utf-8"))
        # Acréscimos gregos de Daniel numerados como livro à parte -> Daniel grego (DAG = Dn 3 católico).
        self.org_map = {a: b for src, dst in org["mappedVerses"].items() for a, b in zip(_expand(src), _expand(dst))}
        # Daniel 3 nas Bíblias católicas segue a Vulgata (com os acréscimos gregos): hebraico
        # 3,24-33 = católico 3,91-100 (mapa "vul" da Copenhagen Alliance).
        vul = json.loads((org_file.parent / "vul.json").read_text(encoding="utf-8"))
        self.dan3_catholic = {(c2, v2): (c1, v1) for src, dst in vul["mappedVerses"].items()
                              for (b1, c1, v1), (b2, c2, v2) in zip(_expand(src), _expand(dst))
                              if b1 == "DAN" and b2 == "DAN" and c1 == 3 and c2 == 3}
        self.max_verses = {b: [int(x) for x in v] for b, v in org["maxVerses"].items()}
        self.map: dict[tuple[str, int, int], tuple[str, int, int]] = {}
        for src, dst in doc["mappedVerses"].items():
            for a, b in zip(_expand(src), _expand(dst)):
                self.map[a] = b
        # Capítulos com numeração diferente (para achar versículos sem mapa próprio).
        self.shifted = {(b, c) for (b, c, v), (_, c2, v2) in self.map.items() if (c, v) != (c2, v2)}

    def _shifted_at(self, book: str, c: int, v: int) -> bool:
        m = self.map.get((book, c, v))
        return m is not None and (m[1], m[2]) != (c, v)

    def convert_verse(self, book: str, c: int, v: int) -> tuple[int, int]:
        """Converte um versículo. Sem mapa próprio mas vizinho de um versículo deslocado
        (ex.: Is 64,1 inglês, antes de 64,2 -> 64,1), deduz pela posição do vizinho:
        Is 64,1 (inglês) -> Is 63,19 (hebraico)."""
        if (book, c, v) in self.map:
            _, c2, v2 = self.map[(book, c, v)]
            return c2, v2
        if self._shifted_at(book, c, v + 1):
            _, nc, nv = self.map[(book, c, v + 1)]
            if nv > 1:
                return nc, nv - 1
            prev = self.max_verses.get(book, [])
            return nc - 1, int(prev[nc - 2]) if nc - 2 < len(prev) else v
        if self._shifted_at(book, c, v - 1):
            _, pc, pv = self.map[(book, c, v - 1)]
            last = self.max_verses.get(book, [])
            limit = int(last[pc - 1]) if pc - 1 < len(last) else pv + 1
            return pc, min(pv + 1, limit)  # ex.: Sl 13,6 inglês -> 13,6 hebraico (último versículo)
        return c, v

    def uncertain(self, ref: Ref) -> bool:
        """Mantido para relatórios: versículo deduzido pelo vizinho (não listado no mapa)."""
        for s in ref.segments:
            for c, v in ((s.c1, s.v1), (s.end_chapter, s.end_verse)):
                if v is not None and (ref.book, c, v) not in self.map and (
                        self._shifted_at(ref.book, c, v + 1) or self._shifted_at(ref.book, c, v - 1)):
                    return True
        return False

    def to_org(self, ref: Ref) -> Ref:
        segs: list[Segment] = []
        for s in ref.segments:
            if s.v1 is None:
                segs.append(s)
                continue
            c1, v1 = self.convert_verse(ref.book, s.c1, s.v1)
            if s.c2 is None and s.v2 is None:
                seg = Segment(c1, v1, s.l1)
            else:
                c2, v2 = self.convert_verse(ref.book, s.end_chapter, s.end_verse)
                seg = Segment(c1, v1, s.l1, c2 if c2 != c1 else None, v2, s.l2)
            if segs and segs[-1] == seg:  # dois versículos ingleses no mesmo hebraico (ex.: Sl 13,5-6)
                continue
            segs.append(seg)
        if ref.book == "DAN":
            segs = [self._dan3(seg) for seg in segs]
        return Ref(ref.book, tuple(segs), ref.cf)

    def _dan3(self, s: Segment) -> Segment:
        def conv(c, v):
            return self.dan3_catholic.get((c, v), (c, v))
        if s.v1 is None:
            return s
        c1, v1 = conv(s.c1, s.v1)
        if s.v2 is None and s.c2 is None:
            return Segment(c1, v1, s.l1)
        c2, v2 = conv(s.end_chapter, s.end_verse)
        return Segment(c1, v1, s.l1, c2 if c2 != c1 else None, v2, s.l2)


def _expand(spec: str) -> list[tuple[str, int, int]]:
    book, cv = spec.split(" ")
    chapter, verses = cv.split(":")
    verses = re.sub(r"[a-z]", "", verses)  # versículos parciais: mapeia o versículo inteiro
    if "-" in verses:
        a, b = verses.split("-")
        return [(book, int(chapter), v) for v in range(int(a), int(b) + 1)]
    return [(book, int(chapter), int(verses))]


@lru_cache(maxsize=None)
def default_versification(root: str) -> Versification:
    base = Path(root) / "data" / "fontes" / "versificacao"
    return Versification(base / "eng.json", base / "org.json")


def greek_daniel_to_catholic(ref: Ref, vrs: Versification) -> Ref:
    """Daniel grego numerado como na fonte tâmil (1 = Cântico de Azarias, 2 = Susana, 3 = Bel)
    -> numeração católica (Dn 3,24-90; Dn 13; Dn 14).

    O cântico é inserido depois de Dn 3,23: versículo n -> Dn 3,23+n. O mapa "org" confirma esse
    deslocamento nos vv. 1-29 (S3Y 1,1-29 -> Dn 3,24-52) e, nos cânticos, o resultado coincide
    com a LitCal (teste em tests/test_bible_refs.py). Depois do v. 29 o mapa "org" segue outra
    ordenação (a de traduções que invertem versículos) e por isso não é usado."""
    verses: set[tuple[int, int]] = set()
    for s in ref.segments:
        c, v = s.c1, s.v1
        ev = s.end_verse
        for x in range(v, ev + 1):
            if c == 1:
                if x <= 29:
                    assert vrs.org_map[("S3Y", 1, x)][1:] == (3, 23 + x)
                verses.add((3, 23 + x))
            else:
                verses.add((11 + c, x))  # 2 -> Dn 13 (Susana), 3 -> Dn 14 (Bel e o dragão)
    return Ref.from_verses("DAN", frozenset(verses), vrs.max_verses, ref.cf)
