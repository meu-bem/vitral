"""Gera data/lecionario/*.yaml (só referências bíblicas) a partir das fontes vendorizadas.

Uso: ``python scripts/ingest_lectionary.py``. Depois de gerados, os arquivos são mantidos
à mão; regenerar sobrescreve correções, então revise o diff.

Fontes (docs/FONTES.md):
- ``lecionario-tamil``: lecionário de jayarathina (domínio público, Unlicense), completo,
  versificação inglesa -> convertida para a hebraica com os mapas da Copenhagen Alliance.
- ``litcal``: Liturgical Calendar API (Apache-2.0), parcial, numeração hebraica.

Regra de status por leitura:
- ``verificado``: as duas fontes concordam (após normalizar);
- ``fonte-unica``: só uma fonte tem a leitura;
- ``pendente``: as fontes divergem. Fica registrada a parte comum (livro e capítulo)
  em ``capitulo`` e as duas versões em ``candidatos``.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vitral.bible import Ref, default_versification, greek_daniel_to_catholic, parse_ref  # noqa: E402

SRC = ROOT / "data" / "fontes"
OUT_DIR = ROOT / "data" / "lecionario"
REPORT = ROOT / "docs" / "relatorios" / "lecionario-divergencias.md"

WD_EN = {"Monday": "segunda", "Tuesday": "terca", "Wednesday": "quarta", "Thursday": "quinta",
         "Friday": "sexta", "Saturday": "sabado", "Sunday": "domingo"}
WD_TA = {"0Sun": "domingo", "1Mon": "segunda", "2Tue": "terca", "3Wed": "quarta", "4Thu": "quinta",
         "5Fri": "sexta", "6Sat": "sabado"}
DAY_N = {1: "segunda", 2: "terca", 3: "quarta", 4: "quinta", 5: "sexta", 6: "sabado"}
MONTHS_EN = {"Dec": 12, "Jan": 1}

# Ordem dos livros em TamilLectionaryUtil.php ($tamilAbbr), conferida com os nomes por extenso.
TA_ORDER = [
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA", "1KI", "2KI", "1CH", "2CH", "EZR", "NEH",
    "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS", "JOL", "AMO", "OBA", "JON",
    "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL",
    "TOB", "JDT", "EST*", "WIS", "SIR", "BAR", "DAN*", "1MA", "2MA",
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI",
    "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV",
]
UNPARSED: list[tuple[str, str]] = []
UNCERTAIN: set[str] = set()  # referências tâmeis com versificação incerta (pela forma original)
UNCERTAIN_REFS: set[str] = set()  # as mesmas, já convertidas (formato br)
SLOTS = {"1": "primeira_leitura", "2": "salmo", "3": "segunda_leitura", "6": "evangelho"}
LITCAL_SLOTS = {"first_reading": "primeira_leitura", "responsorial_psalm": "salmo",
                "second_reading": "segunda_leitura", "gospel": "evangelho"}


# ------------------------------------------------------------------ fonte tâmil
def tamil_books() -> list[tuple[str, str]]:
    php = (SRC / "lecionario-tamil" / "TamilLectionaryUtil.php").read_text(encoding="utf-8")
    block = php[php.index("$tamilAbbr = ["):]
    block = block[: block.index("];")]
    abbrs = re.findall(r"'([^']+)'\s*=>", block)
    if len(abbrs) != len(TA_ORDER):
        raise SystemExit(f"tabela de livros tâmil mudou: {len(abbrs)} != {len(TA_ORDER)}")
    # Mais longas primeiro, para "1யோவா" não casar como "யோவா".
    return sorted(zip(abbrs, TA_ORDER), key=lambda x: -len(x[0]))


def tamil_rows() -> dict[str, dict[str, str]]:
    sql = (SRC / "lecionario-tamil" / "readings__list.sql").read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = defaultdict(dict)
    for day, typ, ref in re.findall(r"\('([^']*)',\s*([\d.]+),\s*'([^']*)'\)", sql):
        out[day][typ] = ref
    return out


class TamilParser:
    def __init__(self):
        self.books = tamil_books()
        self.vrs = default_versification(str(ROOT))

    def __call__(self, raw: str) -> Ref | None:
        raw = raw.strip()
        # Partes gregas: a fonte grafa sem o espaço da tabela ("எஸ்(கி)", "தானி(இ)").
        for abbr, code in (("எஸ்(கி)", "EST"), ("தானி(இ)", "DAN")):
            if raw.startswith(abbr):
                spec = raw[len(abbr):].lstrip(":")
                try:
                    ref = parse_ref(f"{code}|{spec}", "ta")
                    return greek_daniel_to_catholic(ref, self.vrs) if code == "DAN" else ref
                except (ValueError, KeyError):
                    UNPARSED.append(("lecionario-tamil", raw))
                    return None
        for abbr, code in self.books:
            if raw.startswith(abbr) and raw[len(abbr):][:1].isdigit():
                spec = raw[len(abbr):]
                greek = code.endswith("*")  # partes gregas de Ester/Daniel: numeração católica, sem conversão
                try:
                    ref = parse_ref(f"{code.rstrip('*')}|{spec}", "ta")
                except ValueError:
                    UNPARSED.append(("lecionario-tamil", raw))
                    return None
                if greek:
                    return ref
                org = self.vrs.to_org(ref)
                if self.vrs.uncertain(ref):
                    UNCERTAIN.add(raw)
                    UNCERTAIN_REFS.add(org.br())
                return org
        return None  # ponteiro interno (ex.: "LW06-6Sat~1") ou texto não bíblico


def tamil_key(day_id: str, cycle_suffix: str | None, saints: dict[str, str]) -> str | None:
    """Converte o id do dia tâmil na chave do Vitral (sem o sufixo de ciclo)."""
    cyc = f"{cycle_suffix}." if cycle_suffix in ("A", "B", "C") else ""
    fer = {"1": "I.", "2": "II."}.get(cycle_suffix or "", "")
    if m := re.fullmatch(r"AW0(\d)-(\d\w{3})", day_id):
        w, d = m[1], WD_TA[m[2]]
        return f"{cyc}advento-{w}.domingo" if d == "domingo" else f"{cyc}advento-{w}.{d}"
    if m := re.fullmatch(r"AW05-Dec(\d+)", day_id):
        return f"advento.12-{int(m[1]):02d}"
    if m := re.fullmatch(r"CW01-Dec(\d+)", day_id):
        return f"natal.12-{int(m[1]):02d}"
    if day_id == "CW01-HolyFamily":
        return f"{cyc}natal.sagrada-familia"
    if day_id == "CW02-0Sun":
        return "natal-2.domingo"
    if m := re.fullmatch(r"CW02-Jan(\d+)", day_id):
        return f"natal.01-{int(m[1]):02d}"
    if m := re.fullmatch(r"CW03-Day(\d)", day_id):
        return f"natal.depois-da-epifania.{DAY_N[int(m[1])]}"
    if day_id == "CW03-Epiphany":
        return "natal.epifania"
    if day_id == "CW04-Baptism":
        return f"{cyc}natal.batismo-do-senhor"
    if day_id == "LW00-3Wed":
        return "quaresma.cinzas"
    if m := re.fullmatch(r"LW00-(\d\w{3})", day_id):
        return f"quaresma-0.{WD_TA[m[1]]}"
    if m := re.fullmatch(r"LW06-(\d\w{3})(~Chrism)?", day_id):
        d = WD_TA[m[1]]
        if m[2]:
            return "triduo.missa-do-crisma"
        return {"domingo": f"{cyc}semana-santa.ramos", "quinta": "triduo.quinta-feira-santa",
                "sexta": "triduo.sexta-feira-santa", "sabado": f"{cyc}triduo.vigilia-pascal"}.get(d, f"semana-santa.{d}")
    if m := re.fullmatch(r"LW0(\d)-(\d\w{3})", day_id):
        w, d = m[1], WD_TA[m[2]]
        return f"{cyc}quaresma-{w}.{d}"
    if day_id == "EW01-0Sun":
        return "pascoa.domingo"
    if m := re.fullmatch(r"EW01-(\d\w{3})", day_id):
        return f"pascoa-1.{WD_TA[m[1]]}"
    if m := re.fullmatch(r"EW07-Ascension", day_id):
        return f"{cyc}pascoa.ascensao"
    if day_id == "EW08-Pentecost":
        return f"{cyc}pascoa.pentecostes"
    if m := re.fullmatch(r"EW0(\d)-(\d\w{3})", day_id):
        return f"{cyc}pascoa-{m[1]}.{WD_TA[m[2]]}"
    if day_id == "OW00-Trinity":
        return f"{cyc}tc.santissima-trindade"
    if day_id == "OW00-CorpusChristi":
        return f"{cyc}tc.corpo-e-sangue-de-cristo"
    if day_id == "OW00-SacredHeart":
        return f"{cyc}tc.sagrado-coracao-de-jesus"
    if day_id == "OW34-0Sun":
        return f"{cyc}tc.cristo-rei"
    if m := re.fullmatch(r"OW(\d\d)-0Sun", day_id):
        return f"{cyc}tc-{int(m[1])}.domingo"
    if m := re.fullmatch(r"OW(\d\d)-(\d\w{3})", day_id):
        return f"{fer}tc-{int(m[1])}.{WD_TA[m[2]]}" if fer else f"*tc-{int(m[1])}.{WD_TA[m[2]]}"
    if day_id == "OW00-MaryMotherofChurch":
        return saints.get("@mary_mother_of_the_church")
    if day_id == "OW00-ImmaculateHeart":
        return saints.get("@immaculate_heart_of_mary")
    if m := re.fullmatch(r"Nativity of the Lord (\d)", day_id):
        return {"1": "natal.natal-do-senhor.vigilia", "2": "natal.natal-do-senhor.noite",
                "3": "natal.natal-do-senhor.aurora", "4": "natal.natal-do-senhor"}[m[1]]
    if day_id == "Blessed Virgin Mary, the Mother of God":
        return "natal.santa-maria-mae-de-deus"
    if day_id in saints:
        return f"{cyc}santos.{saints[day_id]}" if cyc else f"santos.{saints[day_id]}"
    return None


# Nomes da lista de leituras tâmil que não casam pelo calendário tâmil.
TAMIL_SPECIAL = {"All Souls": "commemoration_of_all_the_faithful_departed",
                 "Saint Birgitta, religious": "bridget_of_sweden_religious",
                 "Saint Blase, bishop and martyr": "blaise_of_sebaste_bishop"}
_STOP = {"saint", "saints", "the", "of", "and", "blessed", "bishop", "priest", "virgin", "martyr", "martyrs",
         "religious", "doctor", "pope", "apostle", "apostles", "companions", "deacon", "abbot"}


def _tokens(text: str) -> set[str]:
    return {w for w in re.split(r"[^a-z]+", text.lower()) if w and w not in _STOP}


def fuzzy_saint(name: str, saints: dict[str, str]) -> str | None:
    """Casa um nome inglês da fonte tâmil com o id romcal (também em inglês) da celebração."""
    if name.startswith(("IN ", "_")) or name.endswith("Vigil") or re.match(r"[ACELO]W\d", name):
        return None
    if name in TAMIL_SPECIAL:
        return saints.get(f"@{TAMIL_SPECIAL[name]}")
    want = _tokens(name)
    best, score = None, 0.0
    for k, v in saints.items():
        if not k.startswith("@"):
            continue
        have = _tokens(k[1:].replace("_", " "))
        j = len(want & have) / len(want | have) if want | have else 0
        if j > score:
            best, score = v, j
    return best if score >= 0.5 else None


def collect_tamil(saints: dict[str, str]) -> tuple[dict[str, dict], list[str]]:
    parse = TamilParser()
    data: dict[str, dict] = defaultdict(dict)
    proper: dict[str, bool] = {}
    unmapped = []
    for raw_id, fields in tamil_rows().items():
        m = re.fullmatch(r"(.+?) (A|B|C|1|2)", raw_id)
        if raw_id == "All Souls A":  # três formulários de missa, não ciclos: usa o primeiro
            base, suffix = "All Souls", None
        elif m and re.match(r"(AW|CW|LW|EW|OW)\d\d-", raw_id):
            base, suffix = m[1], m[2]
        else:
            base, suffix = raw_id, None
        key = tamil_key(base, suffix, saints)
        if key is None and raw_id in ("All Souls", "All Souls B", "All Souls C"):
            continue
        if key is None:
            key = fuzzy_saint(base, saints)
        if key is None:
            unmapped.append(raw_id)
            continue
        targets = [key]
        if key.startswith("*tc-"):  # evangelho comum aos anos I e II
            targets = [f"I.{key[1:]}", f"II.{key[1:]}"]
        for typ, raw in sorted(fields.items(), key=lambda x: float(x[0])):
            head, _, tail = typ.partition(".")
            if head == "9":  # comuns sugeridos: a memória não tem leituras próprias
                for t in targets:
                    proper[t] = False
                continue
            ref = parse(raw)
            if ref is None:
                continue
            for t in targets:
                slot = _tamil_slot(t, head, tail)
                if slot:
                    data[t].setdefault(slot, []).append(ref)
    for t in data:
        if ".santos." in f".{t}" and t not in proper:
            proper[t] = True
    return data, unmapped, proper


def _tamil_slot(key: str, head: str, tail: str) -> str | None:
    if "vigilia-pascal" in key and head in ("1", "2"):
        n = tail[:1] or "1"
        return f"{'leitura' if head == '1' else 'salmo'}_{n}"
    if head == "0":
        return "evangelho_procissao"
    return SLOTS.get(head)


# ------------------------------------------------------------------ fonte LitCal
def litcal_key(group: str, key: str) -> list[str]:
    cyc = group[-1] if group.startswith("dominicale") else ""
    if m := re.fullmatch(r"Advent(\d)", key):
        return [f"{cyc}.advento-{m[1]}.domingo"]
    if m := re.fullmatch(r"OrdSunday(\d+)", key):
        return [f"{cyc}.tc-{m[1]}.domingo"]
    if m := re.fullmatch(r"Lent(\d)", key):
        return [f"{cyc}.quaresma-{m[1]}.domingo"]
    if m := re.fullmatch(r"Easter(\d)", key):
        return [f"{cyc}.pascoa-{m[1]}.domingo"]
    simple = {
        "HolyFamily": f"{cyc}.natal.sagrada-familia", "MaryMotherOfGod": "natal.santa-maria-mae-de-deus",
        "Christmas2": "natal-2.domingo", "Epiphany": "natal.epifania", "BaptismLord": f"{cyc}.natal.batismo-do-senhor",
        "PalmSun": f"{cyc}.semana-santa.ramos", "HolyThursChrism": "triduo.missa-do-crisma",
        "HolyThurs": "triduo.quinta-feira-santa", "GoodFri": "triduo.sexta-feira-santa",
        "EasterVigil": f"{cyc}.triduo.vigilia-pascal", "Easter": "pascoa.domingo",
        "Ascension": f"{cyc}.pascoa.ascensao", "Pentecost": f"{cyc}.pascoa.pentecostes",
        "Trinity": f"{cyc}.tc.santissima-trindade", "CorpusChristi": f"{cyc}.tc.corpo-e-sangue-de-cristo",
        "SacredHeart": f"{cyc}.tc.sagrado-coracao-de-jesus", "ChristKing": f"{cyc}.tc.cristo-rei",
        "AshWednesday": "quaresma.cinzas",
    }
    if key in simple:
        return [simple[key]]
    if m := re.fullmatch(r"AdventWeekday(\d)(\w+)", key):
        return [f"advento-{m[1]}.{WD_EN[m[2]]}"]
    if m := re.fullmatch(r"AdventWeekdayDec(\d+)", key):
        return [f"advento.12-{int(m[1]):02d}"]
    if m := re.fullmatch(r"ChristmasWeekday(Dec|Jan)(\d+)", key):
        return [f"natal.{MONTHS_EN[m[1]]:02d}-{int(m[2]):02d}"]
    if m := re.fullmatch(r"DayAfterEpiphany(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)", key):
        return [f"natal.depois-da-epifania.{WD_EN[m[1]]}"]
    if m := re.fullmatch(r"(\w+)AfterAshWednesday", key):
        return [f"quaresma-0.{WD_EN[m[1]]}"]
    if m := re.fullmatch(r"LentWeekday(\d)(\w+)", key):
        return [f"quaresma-{m[1]}.{WD_EN[m[2]]}"]
    if m := re.fullmatch(r"(Mon|Tue|Wed)HolyWeek", key):
        return [f"semana-santa.{ {'Mon': 'segunda', 'Tue': 'terca', 'Wed': 'quarta'}[m[1]] }"]
    if m := re.fullmatch(r"(Mon|Tue|Wed|Thu|Fri|Sat)OctaveEaster", key):
        return [f"pascoa-1.{ {'Mon': 'segunda', 'Tue': 'terca', 'Wed': 'quarta', 'Thu': 'quinta', 'Fri': 'sexta', 'Sat': 'sabado'}[m[1]] }"]
    if m := re.fullmatch(r"EasterWeekday(\d)(\w+)", key):
        return [f"pascoa-{m[1]}.{WD_EN[m[2]]}"]
    if m := re.fullmatch(r"OrdWeekday(\d+)(\w+)", key):
        fer = "I" if group.endswith("_I") else "II"
        return [f"{fer}.tc-{m[1]}.{WD_EN[m[2]]}"]
    return []


def collect_litcal(litcal_saints: dict[str, str]) -> dict[str, dict]:
    data: dict[str, dict] = defaultdict(dict)
    base = SRC / "litcal" / "lectionary"
    for group_dir in sorted(base.iterdir()):
        group = group_dir.name
        doc = json.loads((group_dir / "en.json").read_text())
        for key, val in doc.items():
            entries: list[tuple[str, dict]] = []
            if group == "sanctorum":
                if key not in litcal_saints:
                    continue
                target = litcal_saints[key]
                if isinstance(val, dict) and "day" in val:
                    val = val["day"]
                if isinstance(val, dict) and not any(isinstance(v, str) for v in val.values()):
                    continue  # várias missas (ex.: Finados): fica só a fonte tâmil
                entries = [(target, val)]
            elif key == "Christmas":
                entries = [("natal.natal-do-senhor", val["day"]), ("natal.natal-do-senhor.noite", val["night"]),
                           ("natal.natal-do-senhor.aurora", val["dawn"]), ("natal.natal-do-senhor.vigilia", val["vigil"])]
            else:
                entries = [(k, val) for k in litcal_key(group, key)]
            for target, fields in entries:
                if not isinstance(fields, dict):
                    continue
                for f, slot in LITCAL_SLOTS.items():
                    raw = (fields.get(f) or "").strip()
                    if not raw or ("vigilia-pascal" in target and f != "gospel"):
                        continue
                    refs = []
                    for alt in raw.split("|"):
                        try:
                            refs.append(parse_ref(alt, "en"))
                        except ValueError:
                            UNPARSED.append(("litcal", alt))
                    if refs:
                        data[target].setdefault(slot, refs)
    return data


# ------------------------------------------------------------------ cruzamento
def merge(tamil: dict, litcal: dict, proper: dict, max_verses) -> tuple[dict, list]:
    out, report = {}, []
    for key in sorted(set(tamil) | set(litcal)):
        t, lc = tamil.get(key, {}), litcal.get(key, {})
        entry: dict = {}
        for slot in sorted(set(t) | set(lc), key=_slot_order):
            tr, lr = t.get(slot), lc.get(slot)
            item: dict
            if tr and lr:
                same = tr[0].normalized(max_verses) == lr[0].normalized(max_verses)
                vt, vl = tr[0].verses(max_verses), lr[0].verses(max_verses)
                item = {"ref": tr[0].br()}
                if same:
                    item["status"] = "verificado"
                elif tr[0].book == lr[0].book and vt == vl:
                    # Mesmos versículos; só as letras de meio-versículo divergem: mostra os inteiros.
                    item = {"ref": Ref.from_verses(tr[0].book, vt, max_verses, tr[0].cf).br(),
                            "status": "verificado", "precisao": "versiculos-inteiros"}
                else:
                    # Decisão do mantenedor (2026-10-27): nas divergências vale a fonte tâmil, que
                    # segue o Ordo Lectionum Missae; a LitCal segue o lecionário adaptado dos EUA.
                    item = {"ref": tr[0].br(), "status": "fonte-unica", "divergencia": {"litcal": lr[0].br()}}
                    if lr[0].book == tr[0].book and all(g.v1 is None for g in lr[0].segments) \
                            and lr[0].chapter_level() == tr[0].chapter_level():
                        item["observacao"] = "a LitCal confirma livro e capítulo, sem versículos"
                    report.append((key, slot, tr[0].br(), lr[0].br()))
            else:
                src = tr or lr
                item = {"ref": src[0].br(), "status": "fonte-unica"}
            alts = (tr or lr)[1:]
            if alts and item.get("ref"):
                item["alternativas"] = [a.br() for a in alts]
            entry[slot] = item
        if key in proper:
            entry["leituras_proprias"] = proper[key]
        entry["fontes"] = [s for s, d in (("lecionario-tamil", t), ("litcal", lc)) if d]
        out[key] = entry
    return out, report


def _slot_order(s: str) -> tuple:
    order = ["evangelho_procissao", "primeira_leitura", "salmo", "segunda_leitura", "evangelho"]
    if s in order:
        return (0, order.index(s), 0)
    m = re.match(r"(leitura|salmo)_(\d)", s)
    return (1, int(m[2]), 0 if m[1] == "leitura" else 1) if m else (2, 0, 0)


def group_of(key: str) -> str:
    k = re.sub(r"^(A|B|C|I|II)\.", "", key)
    if k.startswith("santos."):
        return "santos"
    if re.match(r"tc-\d+\.", k) and key.startswith(("I.", "II.")):
        return "tempo-comum-semana"
    if re.match(r"tc-\d+\.domingo", k) or k.startswith("tc."):
        return "tempo-comum-domingos"
    if k.startswith(("advento", "natal")):
        return "advento-natal"
    if k.startswith(("quaresma", "semana-santa", "triduo")):
        return "quaresma-triduo"
    return "pascoa"


def main() -> int:
    santos = yaml.safe_load((ROOT / "data" / "calendario" / "santos.yaml").read_text())["celebracoes"]
    saints_by_tamil = {e["ids_externos"]["tamil"]: e["id"] for e in santos if "tamil" in e["ids_externos"]}
    for e in santos:
        saints_by_tamil[f"@{e['ids_externos']['romcal']}"] = f"santos.{e['id']}"
    # O nome na lista de leituras às vezes difere do calendário tâmil (ex.: "Saint Barnabas the Apostle").
    gc_names = set(saints_by_tamil)
    litcal_saints = {e["ids_externos"]["litcal"]: f"santos.{e['id']}" for e in santos if "litcal" in e["ids_externos"]}

    tamil, unmapped, proper = collect_tamil(saints_by_tamil)
    litcal = collect_litcal(litcal_saints)
    vrs = default_versification(str(ROOT))
    merged, report = merge(tamil, litcal, proper, vrs.max_verses)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    groups: dict[str, dict] = defaultdict(dict)
    for key, entry in merged.items():
        groups[group_of(key)][key] = entry
    header = (
        "# Referências do Lecionário (só referências; nenhum texto bíblico).\n"
        "# Gerado por scripts/ingest_lectionary.py; depois disso, mantido à mão.\n"
        "# status por leitura: verificado | fonte-unica | pendente. Fontes: docs/FONTES.md.\n"
    )
    for name, entries in groups.items():
        (OUT_DIR / f"{name}.yaml").write_text(
            header + yaml.safe_dump({"leituras": entries}, allow_unicode=True, sort_keys=True, width=110),
            encoding="utf-8")

    status = Counter(v["status"] for e in merged.values() for k, v in e.items() if isinstance(v, dict) and "status" in v)
    lines = ["# Divergências do lecionário", "",
             "Gerado por `scripts/ingest_lectionary.py`. Cada linha é uma leitura em que o lecionário",
             "tâmil (domínio público) e a LitCal (Apache-2.0) discordam depois de normalizar livro,",
             "versificação e separadores. Por decisão do mantenedor, o livro usa a versão tâmil",
             "(segue o Ordo Lectionum Missae); a da LitCal fica em `divergencia` para revisão.", "",
             f"Chaves: {len(merged)}. Leituras: " + ", ".join(f"{k} {v}" for k, v in sorted(status.items())) + ".", "",
             "| chave | leitura | lecionário tâmil | LitCal |", "|---|---|---|---|"]
    lines += [f"| `{k}` | {s} | {a} | {b} |" for k, s, a, b in report]
    if UNCERTAIN:
        lines += ["", "## Versículos deduzidos pelo vizinho no mapa de versificação", ""]
        lines += [f"- `{raw}`" for raw in sorted(UNCERTAIN)]
    if UNPARSED:
        lines += ["", "## Referências que o importador não conseguiu ler", ""]
        lines += [f"- {src}: `{raw}`" for src, raw in sorted(set(UNPARSED))]
    if unmapped:
        lines += ["", "## Dias da fonte tâmil sem correspondência no calendário do Brasil", ""]
        lines += [f"- {u}" for u in sorted(unmapped)]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(len(merged), "chaves;", dict(status), "; sem correspondência:", len(unmapped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
