"""Leituras de cada dia: junta as chaves do calendário com data/lecionario/*.yaml.

Regras:
- as chaves do dia vão da mais específica para a mais genérica; cada leitura vem da
  primeira chave que a tiver (ex.: ``A.advento-1.segunda`` só troca a 1ª leitura);
- memória obrigatória celebrada no dia usa as leituras próprias quando os dados
  marcam ``leituras_proprias: true``; senão, valem as leituras do dia de semana;
- leitura ``pendente`` não mostra a referência completa, só ``capitulo`` (se houver).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .data_loader import DATA_DIR, load_yaml
from .liturgy import LiturgicalDay

__all__ = ["Reading", "DayReadings", "Lectionary", "SLOT_LABELS"]

SLOT_LABELS = {
    "evangelho_procissao": "Evangelho da procissão",
    "primeira_leitura": "1ª leitura",
    "salmo": "Salmo responsorial",
    "segunda_leitura": "2ª leitura",
    "evangelho": "Evangelho",
}
_MAIN_ORDER = list(SLOT_LABELS)


def slot_label(slot: str) -> str:
    if slot in SLOT_LABELS:
        return SLOT_LABELS[slot]
    m = re.fullmatch(r"(leitura|salmo)_(\d)", slot)
    if m:
        return f"{m[2]}ª leitura" if m[1] == "leitura" else f"Salmo após a {m[2]}ª leitura"
    return slot


def _slot_key(slot: str) -> tuple:
    if slot in _MAIN_ORDER:
        return (1, _MAIN_ORDER.index(slot), 0) if slot != "evangelho" else (3, 0, 0)
    m = re.fullmatch(r"(leitura|salmo)_(\d)", slot)
    return (2, int(m[2]), 0 if m[1] == "leitura" else 1) if m else (4, 0, 0)


@dataclass
class Reading:
    slot: str
    ref: str | None  # referência completa, só quando não pendente
    chapter: str | None  # livro e capítulo, quando a referência completa está pendente
    status: str
    alternatives: list[str] = field(default_factory=list)
    key: str = ""  # chave do Lecionário de onde veio

    @property
    def label(self) -> str:
        return slot_label(self.slot)

    @property
    def display(self) -> str | None:
        return self.ref or self.chapter


@dataclass
class DayReadings:
    readings: list[Reading]
    keys_used: list[str]
    sources: list[str]
    proper_memorial: str | None = None  # id da memória cujas leituras próprias foram usadas

    def get(self, slot: str) -> Reading | None:
        return next((r for r in self.readings if r.slot == slot), None)

    @property
    def pending(self) -> list[str]:
        out = [f"{r.label}: referência divergente entre as fontes" for r in self.readings if r.status == "pendente"]
        if not self.readings:
            out.append("sem leituras nos dados do Lecionário")
        return out


class Lectionary:
    def __init__(self, entries: dict[str, dict]):
        self.entries = entries

    @classmethod
    def load(cls, directory: Path | None = None) -> "Lectionary":
        entries: dict[str, dict] = {}
        for path in sorted((directory or DATA_DIR / "lecionario").glob("*.yaml")):
            doc = load_yaml(path) or {}
            for key, entry in (doc.get("leituras") or {}).items():
                if key in entries:
                    raise ValueError(f"chave repetida no Lecionário: {key} ({path.name})")
                entries[key] = entry
        return cls(entries)

    def keys_for(self, day: LiturgicalDay) -> tuple[list[str], str | None]:
        memorial = day.observed_memorial
        if memorial is not None:
            mkeys = [f"{day.sunday_cycle}.santos.{memorial.id}", f"santos.{memorial.id}"]
            if any(self.entries.get(k, {}).get("leituras_proprias") for k in mkeys):
                return mkeys + list(day.lectionary_keys), memorial.id
        return list(day.lectionary_keys), None

    def for_day(self, day: LiturgicalDay) -> DayReadings:
        keys, proper = self.keys_for(day)
        found: dict[str, Reading] = {}
        used: list[str] = []
        sources: list[str] = []
        for key in keys:
            entry = self.entries.get(key)
            if not entry:
                continue
            used.append(key)
            for src in entry.get("fontes", []):
                if src not in sources:
                    sources.append(src)
            for slot, item in entry.items():
                if not isinstance(item, dict) or slot in found or "status" not in item:
                    continue
                pending = item["status"] == "pendente"
                found[slot] = Reading(
                    slot=slot,
                    ref=None if pending else item.get("ref"),
                    chapter=item.get("capitulo") if pending else None,
                    status=item["status"],
                    alternatives=list(item.get("alternativas", [])) if not pending else [],
                    key=key,
                )
            if proper:
                # Leituras próprias da memória substituem o dia inteiro; as do dia só completam faltas.
                proper = None
        readings = sorted(found.values(), key=lambda r: _slot_key(r.slot))
        return DayReadings(readings, used, sources, proper_memorial=self.keys_for(day)[1])
