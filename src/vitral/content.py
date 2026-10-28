"""Conteúdo humano licenciado em ``conteudo/`` (Markdown com front matter YAML).

Cada arquivo serve a um dia do Lecionário, independente do ano (ex.: ``B.advento-1.domingo``).
Só entram licenças da lista abaixo; domínio público exige a procedência em ``fonte``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .data_loader import ROOT
from .schema import load_schema, validate

__all__ = ["ContentItem", "load_content", "check_content", "ALLOWED_LICENSES"]

CONTENT_DIR = ROOT / "conteudo"
SCHEMA = ROOT / "schemas" / "conteudo.schema.json"
ALLOWED_LICENSES = ("CC0", "CC-BY-4.0", "CC-BY-SA-4.0", "dominio-publico")
LICENSE_LABELS = {
    "CC0": "CC0 1.0 (domínio público)",
    "CC-BY-4.0": "CC BY 4.0",
    "CC-BY-SA-4.0": "CC BY-SA 4.0",
    "dominio-publico": "Domínio público",
}


@dataclass
class ContentItem:
    path: Path
    author: str
    license: str
    day_key: str
    body: str
    title: str | None = None
    source: dict | None = None


def _split(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("falta o front matter (o arquivo deve começar com '---')")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("front matter sem '---' de fechamento")
    meta = yaml.safe_load(text[4:end]) or {}
    if not isinstance(meta, dict):
        raise ValueError("front matter não é um mapa YAML")
    return meta, text[end + 4:].lstrip("\n")


def check_content(directory: Path | None = None, known_keys: set[str] | None = None) -> tuple[list[ContentItem], list[str]]:
    """Lê e valida todo o conteúdo. Retorna (itens válidos, erros)."""
    directory = directory or CONTENT_DIR
    schema = load_schema(SCHEMA)
    items, errors = [], []
    for path in sorted(directory.rglob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        rel = path.relative_to(directory)
        try:
            meta, body = _split(path.read_text(encoding="utf-8"))
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(f"{rel}: {exc}")
            continue
        errs = [e.replace("$", str(rel), 1) for e in validate(meta, schema)]
        if meta.get("licenca") == "dominio-publico" and "fonte" not in meta:
            errs.append(f"{rel}: domínio público exige 'fonte' (obra, edição, tradutor, ano)")
        if known_keys is not None and meta.get("dia") and meta["dia"] not in known_keys:
            errs.append(f"{rel}: dia '{meta['dia']}' não existe no calendário")
        if not body.strip():
            errs.append(f"{rel}: texto vazio")
        if errs:
            errors += errs
            continue
        items.append(ContentItem(path, meta["autor"], meta["licenca"], meta["dia"], body,
                                 meta.get("titulo"), meta.get("fonte")))
    return items, errors


def load_content(known_keys: set[str] | None = None) -> dict[str, list[ContentItem]]:
    """Conteúdo válido indexado pela chave do dia (o inválido fica de fora)."""
    items, _ = check_content(known_keys=known_keys)
    out: dict[str, list[ContentItem]] = {}
    for item in items:
        out.setdefault(item.day_key, []).append(item)
    return out
