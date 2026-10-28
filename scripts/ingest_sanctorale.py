"""Gera data/calendario/santos.yaml a partir das fontes vendorizadas em data/fontes/.

Uso único (ou para regenerar do zero): ``python scripts/ingest_sanctorale.py``.
Depois de gerado, o arquivo é mantido à mão; não rode de novo sem revisar o diff.

- Base: romcal (MIT), calendário do Brasil em pt-BR (data/fontes/romcal/definitions.json).
- Conferência do calendário geral: Liturgical Calendar API (Apache-2.0) e
  lecionário tâmil de jayarathina (domínio público, Unlicense).
- Relatório: docs/relatorios/santos-divergencias.md.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "fontes"
OUT = ROOT / "data" / "calendario" / "santos.yaml"
REPORT = ROOT / "docs" / "relatorios" / "santos-divergencias.md"

GRADE_NAMES = {"s": "solenidade", "f": "festa", "m": "memoria", "mf": "memoria-facultativa", "c": "comemoracao"}
COLORS = {"WHITE": "branco", "RED": "vermelho", "GREEN": "verde", "PURPLE": "roxo", "ROSE": "rosa", "BLACK": "preto",
          "GOLD": "branco"}
MOVABLE = {"maryMotherOfTheChurch": ("pentecostes", 1), "immaculateHeartOfMary": ("sagrado-coracao", 1)}
# NUALC 60: a Anunciação impedida na Semana Santa vai para a segunda-feira depois do 2º Domingo da Páscoa.
HOLY_WEEK_RULES = {"annunciation_of_the_lord": "segunda-apos-2-domingo-da-pascoa"}
# Memória da Virgem Maria prevalece sobre a de outro santo no mesmo dia (notificação da
# Congregação para o Culto Divino, 24/3/2018, sobre Maria Mãe da Igreja; o Imaculado
# Coração é citado como caso análogo).
MARIAN_PREVAILS = {"mary_mother_of_the_church", "immaculate_heart_of_mary"}
# Regras nacionais (data/calendario/regras-brasil.yaml).
BR_TRANSFER = {"peter_and_paul_apostles", "assumption_of_the_blessed_virgin_mary", "all_saints"}
BR_STAYS_ON_ADVENT_SUNDAY = {"immaculate_conception_of_the_blessed_virgin_mary"}
# Nome em português ausente no romcal: tirado da tradução pt da LitCal.
NAME_FIXES_FROM_LITCAL = {"our_lady_of_guadalupe": "OurLadyOfGuadalupe"}

STOP = {"saint", "saints", "st", "sts", "the", "of", "and", "blessed", "bl", "de", "da", "do", "dos", "das", "e",
        "sao", "santo", "santa", "santos", "santas", "s", "ss"}


def norm_tokens(text: str) -> set[str]:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return {w for w in re.split(r"[^a-z]+", t) if w and w not in STOP}


def slug(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def romcal_grade(d: dict) -> str:
    if d["id"] == "commemoration_of_all_the_faithful_departed":
        return "c"
    return {"SOLEMNITY": "s", "FEAST": "f", "MEMORIAL": "m", "OPTIONAL_MEMORIAL": "mf"}[d["rank"]]


def precedence(d: dict, grade: str) -> int:
    p = d["precedence"]
    if d["fromCalendarId"] == "general_roman" or d["id"] in BR_TRANSFER:
        # Tabela dos Dias Litúrgicos (NUALC 59): grau + calendário geral.
        return {"s": 3, "c": 3, "f": 5 if "LORD" in p else 7, "m": 10, "mf": 12}[grade]
    return int(re.search(r"_(\d+)[A-Z]?$", p).group(1))


def litcal_events() -> list[dict]:
    events: dict[str, dict] = {}
    names: dict[str, str] = {}
    for edition in ("1970", "2002", "2008"):
        base = SRC / "litcal" / f"propriumdesanctis_{edition}"
        for e in json.loads((base / f"propriumdesanctis_{edition}.json").read_text()):
            events[e["event_key"]] = dict(e)
        names.update(json.loads((base / "i18n" / "pt.json").read_text()))
    for dec in json.loads((SRC / "litcal" / "decrees" / "decrees.json").read_text()):
        ev, meta = dec["liturgical_event"], dec["metadata"]
        if meta["action"] == "createNew" and "month" in ev:
            events[ev["event_key"]] = dict(ev)
        elif meta["action"] == "setProperty" and ev["event_key"] in events and meta["property"] in ev:
            events[ev["event_key"]][meta["property"]] = ev[meta["property"]]
    for k, e in events.items():
        e["name_pt"] = names.get(k, "")
    return list(events.values())


LITCAL_GRADE = {2: "mf", 3: "m", 4: "f", 5: "f", 6: "s", 7: "s"}
TAMIL_GRADE = {"Solemnity": "s", "Feast-Lord": "f", "Feast": "f", "Mem-Mary": "m", "Mem": "m", "OpMem": "mf"}


def tamil_events() -> list[dict]:
    sql = (SRC / "lecionario-tamil" / "generalcalendar.sql").read_text(encoding="utf-8")
    rows = re.findall(r"\((\d+), (\d+), '((?:[^'\\]|\\.)*)', '(?:[^'\\]|\\.)*', '([\w-]+)'\)", sql)
    return [{"month": int(m), "day": int(d), "name": n.replace("\\'", "'"), "grade": TAMIL_GRADE[t]}
            for m, d, n, t in rows]


def best_match(candidates, key_tokens, get_tokens, threshold=0.34):
    scored = sorted(((jaccard(key_tokens, get_tokens(c)), i) for i, c in enumerate(candidates)), reverse=True)
    if scored and scored[0][0] >= threshold:
        return candidates[scored[0][1]], scored[0][0]
    return None, 0.0


def main() -> int:
    defs = json.loads((SRC / "romcal" / "definitions.json").read_text())
    litcal = litcal_events()
    litcal_pt = {e["event_key"]: e["name_pt"] for e in litcal}
    tamil = tamil_events()

    entries, report = [], []
    for d in defs:
        if d["properCycle"] == "PROPER_OF_TIME" and d["id"] not in ("mary_mother_of_the_church", "immaculate_heart_of_mary"):
            continue
        grade = romcal_grade(d)
        name = d["name"]
        if d["id"] in NAME_FIXES_FROM_LITCAL:
            name = litcal_pt[NAME_FIXES_FROM_LITCAL[d["id"]]]
        e: dict = {"id": slug(name), "nome": name}
        dd = d["dateDef"]
        if "dateFn" in dd:
            anchor, offset = MOVABLE[dd["dateFn"]]
            e["movel"] = {"ancora": anchor, "dias": offset}
        else:
            e["data"] = f"{dd['month']:02d}-{dd['date']:02d}"
        e["grau"] = GRADE_NAMES[grade]
        e["precedencia"] = precedence(d, grade)
        e["cor"] = COLORS[d["colors"][0]] if d["colors"] else None
        cal = {"general_roman": "geral", "brazil": "brasil", "americas": "america"}.get(d["fromCalendarId"], "geral")
        if d["properCycle"] == "PROPER_OF_TIME" or d["id"] in BR_TRANSFER:
            cal = "geral"  # o romcal só muda a data de transferência no Brasil
        e["calendario"] = cal
        if d["id"] in BR_TRANSFER:
            e["transferencia"] = "domingo-seguinte"
        if d["id"] in BR_STAYS_ON_ADVENT_SUNDAY:
            e["prevalece_sobre_domingo_privilegiado"] = True
        if d["id"] in HOLY_WEEK_RULES:
            e["regra_semana_santa"] = HOLY_WEEK_RULES[d["id"]]
        ext = {"romcal": d["id"]}
        fontes = ["romcal"]
        problems: list[str] = []

        # Conferência com as duas fontes do calendário geral. Vale a maioria: romcal + uma
        # das outras duas de acordo em data e grau = verificado; a discordância da terceira
        # fica registrada (o calendário tâmil é o da Índia e tem ajustes nacionais).
        rtok = norm_tokens(d["id"].replace("_", " ")) | norm_tokens(name)
        lit_tok = lambda x: norm_tokens(x["name_pt"]) | norm_tokens(re.sub(r"([a-z])([A-Z])", r"\1 \2", x["event_key"]))
        if cal == "geral" and "data" in e:
            m, day = dd["month"], dd["date"]
            agree = 0
            lm, _ = best_match([x for x in litcal if (x["month"], x["day"]) == (m, day)], rtok, lit_tok, 0.2)
            lit_ok = lm is not None
            if lm is None:
                lm, _ = best_match(litcal, rtok, lambda x: norm_tokens(x["name_pt"]), 0.5)
                if lm:
                    problems.append(f"data diverge da LitCal ({lm['month']:02d}-{lm['day']:02d})")
            if lm:
                ext["litcal"] = lm["event_key"]
                fontes.append("litcal")
                lg = LITCAL_GRADE.get(lm["grade"])
                if lg != grade and not (grade == "c" and lm["grade"] >= 6):
                    problems.append(f"grau diverge da LitCal ({GRADE_NAMES.get(lg, lm['grade'])})")
                    lit_ok = False
                agree += lit_ok
            tm, _ = best_match([x for x in tamil if (x["month"], x["day"]) == (m, day)], rtok,
                               lambda x: norm_tokens(x["name"]), 0.2)
            tam_ok = tm is not None
            if tm is None:
                tm, _ = best_match(tamil, rtok, lambda x: norm_tokens(x["name"]), 0.5)
                if tm:
                    problems.append(f"data diverge do calendário tâmil ({tm['month']:02d}-{tm['day']:02d})")
            if tm:
                ext["tamil"] = tm["name"]
                fontes.append("lecionario-tamil")
                if tm["grade"] != grade and grade != "c":
                    problems.append(f"grau diverge do calendário tâmil ({GRADE_NAMES[tm['grade']]})")
                    tam_ok = False
                agree += tam_ok
            if agree >= 1:
                e["status"] = "verificado"
            else:
                e["status"] = "pendente" if problems else "fonte-unica"
        else:
            # Próprio do Brasil/América: o romcal cita o Diretório da Liturgia da CNBB. Liga os
            # ids externos (pelo nome) só para achar as leituras no lecionário.
            e["status"] = "fonte-unica"
            lm, _ = best_match(litcal, rtok, lit_tok, 0.5)
            if lm:
                ext["litcal"] = lm["event_key"]
            tm, _ = best_match(tamil, rtok, lambda x: norm_tokens(x["name"]), 0.5)
            if tm:
                ext["tamil"] = tm["name"]
        if d["id"] in MARIAN_PREVAILS:
            e["prevalece_sobre_memorias"] = True
            fontes.append("ccdds-2018-mater-ecclesiae")
        if e["cor"] is None:
            problems.append("sem cor na fonte")
            e["status"] = "pendente"
        e["fontes"] = fontes
        e["ids_externos"] = ext
        if problems:
            e["divergencias"] = problems
            if e["status"] == "pendente":
                report.append((e["id"], e.get("data") or "móvel", name, problems))
        entries.append(e)

    # Ids duplicados (Brasil sobrescreve o geral no romcal; aqui já vêm resolvidos).
    seen: set[str] = set()
    for e in entries:
        if e["id"] in seen:
            raise SystemExit(f"id duplicado: {e['id']}")
        seen.add(e["id"])

    entries.sort(key=lambda e: (e.get("data", "99"), e["id"]))
    header = (
        "# Próprio dos santos e memórias móveis (calendário geral + Brasil).\n"
        "# Gerado uma vez por scripts/ingest_sanctorale.py; a partir daí, mantido à mão.\n"
        "# status: verificado (romcal + outra fonte concordam) | fonte-unica | pendente.\n"
        "# Fontes: ver docs/FONTES.md.\n"
    )
    OUT.write_text(header + yaml.safe_dump({"celebracoes": entries}, allow_unicode=True, sort_keys=False, width=110),
                   encoding="utf-8")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Divergências do próprio dos santos", "",
             "Gerado por `scripts/ingest_sanctorale.py`. Entradas aqui ficam com `status: pendente`",
             "até o mantenedor conferir e corrigir `data/calendario/santos.yaml`.", "",
             "Vale a maioria: romcal e pelo menos uma das outras fontes de acordo = verificado.", "",
             f"Total de celebrações: {len(entries)}. Pendentes: {len(report)}. "
             f"Verificadas: {sum(e['status'] == 'verificado' for e in entries)}. "
             f"Fonte única: {sum(e['status'] == 'fonte-unica' for e in entries)}.", "",
             "| id | data | nome | problema |", "|---|---|---|---|"]
    lines += [f"| `{i}` | {dt} | {n} | {'; '.join(p)} |" for i, dt, n, p in report]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(entries)} celebrações; {len(report)} com divergência")
    return 0


if __name__ == "__main__":
    sys.exit(main())
