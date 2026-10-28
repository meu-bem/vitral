"""Leitura dos dados versionados em ``data/``.

Fica fora de ``vitral.liturgy`` para que o calendário continue sem
dependências: só este módulo usa PyYAML.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .liturgy import Celebration, Color, NationalRules, Precedence, Rank, SanctoraleEntry

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_national_rules(path: Path | None = None) -> NationalRules:
    """Converte ``data/calendario/regras-brasil.yaml`` em ``NationalRules``."""
    doc = load_yaml(path or DATA_DIR / "calendario" / "regras-brasil.yaml")
    rules = doc["regras"]
    pending = tuple(
        (rule_id, f"regra '{rule_id}' pendente: {r.get('observacao') or r['descricao']}".strip())
        for rule_id, r in rules.items()
        if r.get("status") != "verificado"
    )
    return NationalRules(
        epiphany_on_sunday=bool(rules["epifania_no_domingo"]["valor"]),
        ascension_on_sunday=bool(rules["ascensao_no_domingo"]["valor"]),
        corpus_christi_on_sunday=bool(rules["corpus_christi_no_domingo"]["valor"]),
        pending_rules=pending,
    )


_RANKS = {
    "solenidade": Rank.SOLEMNITY,
    "festa": Rank.FEAST,
    "comemoracao": Rank.COMMEMORATION,
    "memoria": Rank.MEMORIAL,
    "memoria-facultativa": Rank.OPTIONAL_MEMORIAL,
}
# Âncoras de datas móveis nos dados -> atributos de YearAnchors.
_ANCHORS = {"pentecostes": "pentecost", "sagrado-coracao": "sacred_heart", "pascoa": "easter"}


def load_sanctorale(path: Path | None = None) -> list[SanctoraleEntry]:
    """Converte ``data/calendario/santos.yaml`` em ``SanctoraleEntry``."""
    doc = load_yaml(path or DATA_DIR / "calendario" / "santos.yaml")
    out = []
    for e in doc["celebracoes"]:
        cel = Celebration(
            id=e["id"],
            name=e["nome"],
            rank=_RANKS[e["grau"]],
            precedence=Precedence(e["precedencia"]),
            color=Color(e["cor"]),
            beats_privileged_sunday=bool(e.get("prevalece_sobre_domingo_privilegiado")),
            prevails_over_memorials=bool(e.get("prevalece_sobre_memorias")),
            transfer=e.get("transferencia"),
            status=e["status"],
            sources=list(e.get("fontes", [])),
        )
        month_day = movable = None
        if "data" in e:
            month, day = str(e["data"]).split("-")
            month_day = (int(month), int(day))
        else:
            movable = (_ANCHORS[e["movel"]["ancora"]], int(e["movel"]["dias"]))
        out.append(SanctoraleEntry(cel, month_day=month_day, movable=movable,
                                   holy_week_rule=e.get("regra_semana_santa")))
    return out


def load_overrides(path: Path | None = None) -> dict[tuple[str, date], date]:
    """Exceções datadas de ``data/calendario/excecoes.yaml``."""
    path = path or DATA_DIR / "calendario" / "excecoes.yaml"
    if not path.exists():
        return {}
    doc = load_yaml(path) or {}
    return {
        (e["celebracao"], date.fromisoformat(e["data_propria"])): date.fromisoformat(e["nova_data"])
        for e in doc.get("excecoes") or []
    }


def build_year(year: int):
    """Ano litúrgico completo com os dados do repositório (regras, santos, exceções)."""
    from .liturgy import build_liturgical_year

    return build_liturgical_year(year, load_national_rules(), load_sanctorale(), load_overrides())
