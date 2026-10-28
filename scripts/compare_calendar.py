"""Cruza o calendário do Vitral com o romcal (MIT), dia a dia, de 2024 a 2060.

Uso: ``python scripts/compare_calendar.py`` (escreve docs/relatorios/calendario-divergencias.md).
O romcal foi exportado uma vez por data/fontes/romcal/export.mjs e guardado em
tests/fixtures/romcal-brasil-2024-2061.json.gz. Nada é baixado aqui.
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vitral.data_loader import load_national_rules, load_sanctorale, load_yaml  # noqa: E402
from vitral.liturgy import LiturgicalDay, build_liturgical_year  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "romcal-brasil-2024-2061.json.gz"
REPORT = ROOT / "docs" / "relatorios" / "calendario-divergencias.md"
WD = {"segunda": "monday", "terca": "tuesday", "quarta": "wednesday", "quinta": "thursday",
      "sexta": "friday", "sabado": "saturday", "domingo": "sunday"}
FIXED = {
    "natal-do-senhor": "nativity_of_the_lord", "sagrada-familia": "holy_family_of_jesus_mary_and_joseph",
    "santa-maria-mae-de-deus": "mary_mother_of_god", "epifania": "epiphany_of_the_lord",
    "batismo-do-senhor": "baptism_of_the_lord", "quarta-feira-de-cinzas": "ash_wednesday",
    "domingo-de-ramos": "palm_sunday_of_the_passion_of_the_lord", "quinta-feira-santa": "holy_thursday",
    "sexta-feira-santa": "friday_of_the_passion_of_the_lord", "sabado-santo": "holy_saturday",
    "pascoa": "easter_sunday", "pascoa-2-domingo": "divine_mercy_sunday", "ascensao": "ascension_of_the_lord",
    "pentecostes": "pentecost_sunday", "santissima-trindade": "most_holy_trinity",
    "corpo-e-sangue-de-cristo": "most_holy_body_and_blood_of_christ",
    "sagrado-coracao-de-jesus": "most_sacred_heart_of_jesus",
    "cristo-rei": "our_lord_jesus_christ_king_of_the_universe",
}


def temporale_to_romcal(cid: str, d: date) -> str:
    if cid in FIXED:
        return FIXED[cid]
    if m := re.fullmatch(r"advento-(\d)-([a-z]+)", cid):
        return f"advent_{m[1]}_{WD[m[2]]}"
    if cid.startswith("advento-"):
        return f"advent_december_{d.day}"
    if m := re.fullmatch(r"natal-depois-epifania-([a-z]+)", cid):
        return f"{WD[m[1]]}_after_epiphany"
    if cid.startswith("natal-") and d.month == 12:
        return f"christmas_octave_day_{d.day - 24}"
    if cid.startswith("natal-"):
        return f"christmas_time_january_{d.day}"
    if m := re.fullmatch(r"tc-(\d+)-(\w+)", cid):
        if m[1] == "3" and m[2] == "domingo":
            return "sunday_of_the_word_of_god"  # 3º domingo do Tempo Comum no romcal
        return f"ordinary_time_{m[1]}_{WD[m[2]]}"
    if m := re.fullmatch(r"quaresma-0-(\w+)", cid):
        return f"{WD[m[1]]}_after_ash_wednesday"
    if m := re.fullmatch(r"quaresma-(\d+)-(\w+)", cid):
        return f"lent_{m[1]}_{WD[m[2]]}"
    if m := re.fullmatch(r"semana-santa-(\w+)", cid):
        return f"holy_{WD[m[1]]}"
    if m := re.fullmatch(r"pascoa-1-(\w+)", cid):
        return f"easter_{WD[m[1]]}"
    if m := re.fullmatch(r"pascoa-(\d+)-(\w+)", cid):
        return f"easter_time_{m[1]}_{WD[m[2]]}"
    raise ValueError(cid)


def main_id(day: LiturgicalDay, to_romcal: dict[str, str]) -> str:
    c = day.celebration
    if not c.is_temporale:
        return to_romcal.get(c.id, c.id)
    if day.observed_memorial:
        return to_romcal.get(day.observed_memorial.id, day.observed_memorial.id)
    return temporale_to_romcal(c.id, day.date)


# Explicações conferidas para cada tipo de divergência (fontes em docs/FONTES.md).
EXPLANATIONS = {
    "imaculada": "Imaculada Conceição permanece no domingo do Advento no Brasil (diretorio-omb-2025, nota 3); o romcal a transfere.",
    "todos-os-santos": "Todos os Santos fica no sábado 1/11 quando Finados cai no domingo (cnbb-finados-2025); o romcal a leva ao domingo.",
    "pedro-paulo": "São Pedro e São Paulo vão para o domingo SEGUINTE (diretorio-cnbb-2022; 30/6/2024 em folheto diocesano); o romcal usa o 1º domingo de julho.",
    "precedencia": "Solenidade/festa vence memória (NUALC 59); o romcal lista a memória primeiro.",
    "anunciacao-2057": "Anunciação em domingo da Quaresma vai para a segunda-feira (NUALC 5); o romcal a omite em 2057.",
    "joao-batista": "Natividade de São João Batista impedida vai para o dia livre anterior (resposta da Congregação para o Culto Divino, 11/5/2020, aplicando a NUALC 60); o romcal a põe depois.",
    "memoria-mariana": "Memória da Virgem Maria prevalece sobre a de outro santo (notificação da Congregação para o Culto Divino, 24/3/2018); o romcal mantém a do santo.",
    "pendente": "Dia (ou celebração do romcal) marcado como pendente no Vitral: regra ainda sem fonte.",
}
SOLEMN_OR_FEAST = ("nativity_", "thomas_apostle", "annunciation_", "joseph_spouse", "peter_and_paul", "all_saints")


def explain(d: str, ours: str, theirs: str, status: str, pending_ids: set[str]) -> str | None:
    if "immaculate_conception_of_the_blessed_virgin_mary" in (ours, theirs) and (ours.startswith("advent_2") or theirs.startswith("advent_2")):
        return "imaculada"
    if {ours, theirs} & {"all_saints", "commemoration_of_all_the_faithful_departed"} and d[5:7] in ("10", "11"):
        return "todos-os-santos"
    if "peter_and_paul_apostles" in (ours, theirs) and d[5:7] in ("06", "07"):
        return "pedro-paulo"
    if "nativity_of_john_the_baptist" in (ours, theirs) and d[5:7] == "06":
        return "joao-batista"
    if ours in ("mary_mother_of_the_church", "immaculate_heart_of_mary") and status != "pendente":
        return "memoria-mariana"
    if status == "pendente" or theirs in pending_ids:
        return "pendente"
    if ours.startswith(SOLEMN_OR_FEAST) and theirs in ("immaculate_heart_of_mary", "mary_mother_of_the_church"):
        return "precedencia"
    if d == "2057-03-26" and ours == "annunciation_of_the_lord":
        return "anunciacao-2057"
    return None


def compare(first_year: int = 2024, last_year: int = 2060) -> list[tuple[str, str, str, str, str | None]]:
    rules, sanct = load_national_rules(), load_sanctorale()
    santos = load_yaml(ROOT / "data" / "calendario" / "santos.yaml")["celebracoes"]
    to_romcal = {e["id"]: e["ids_externos"]["romcal"] for e in santos}
    defs = json.loads((ROOT / "data" / "fontes" / "romcal" / "definitions.json").read_text())
    optional = {d["id"] for d in defs if d["precedence"] == "OPTIONAL_MEMORIAL_12"}
    with gzip.open(FIXTURE, "rt", encoding="utf-8") as fh:
        romcal = json.load(fh)
    diffs = []
    for y in range(first_year, last_year + 1):
        days = build_liturgical_year(y, rules, sanct)
        pending_ids = {to_romcal.get(x.celebration.id, x.celebration.id) for x in days if x.pending}
        for day in days:
            ours = main_id(day, to_romcal)
            theirs = next((i for i in romcal[day.date.isoformat()] if i not in optional), None) or "-"
            if ours != theirs:
                d = day.date.isoformat()
                diffs.append((d, ours, theirs, day.status, explain(d, ours, theirs, day.status, pending_ids)))
    return diffs


def main() -> int:
    diffs = compare()
    kinds = Counter(e or "SEM EXPLICAÇÃO" for *_, e in diffs)
    lines = [
        "# Divergências do calendário: Vitral × romcal", "",
        "Gerado por `scripts/compare_calendar.py`. Compara, para cada dia de 2024 a 2060, a",
        "celebração principal (a que define o dia ou a memória obrigatória) do Vitral com a do",
        "romcal (calendário do Brasil). Divergência não é erro automático: veja a explicação de",
        "cada grupo em `docs/FONTES.md`.", "",
        f"Dias comparados: 13510. Divergentes: {len(diffs)}.", "",
        "## Por explicação", "", "| explicação | dias |", "|---|---|",
    ]
    lines += [f"| {EXPLANATIONS.get(k, k)} | {n} |" for k, n in kinds.most_common()]
    lines += ["", "## Dias", "", "| data | Vitral | romcal | status no Vitral | explicação |", "|---|---|---|---|---|"]
    lines += [f"| {d} | `{o}` | `{t}` | {s} | {e or '**sem explicação**'} |" for d, o, t, s, e in diffs]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(diffs)} dias divergentes")
    for k, n in kinds.most_common():
        print(n, k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
