"""Tradução das passagens (data/biblia/): leitura, validação e cobertura do Lecionário.

Cada livro é um arquivo ``data/biblia/<CÓDIGO>.yaml`` com chave ``"capítulo:versículo"`` na
versificação hebraica ("org"), a mesma das referências do Lecionário (``bible.py``). Um versículo
citado com letra (``2ac``, ``4,17k-m``) precisa de ``partes``: a lista das partes na ordem a, b, c...
Versículo que o texto-base não traz mas o Lecionário cita fica em ``omitidos`` (com o motivo): conta
como coberto e não tem texto.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .bible import BOOKS, Ref, default_versification, parse_ref
from .data_loader import DATA_DIR, ROOT, load_yaml
from .schema import load_schema, validate

__all__ = ["Gap", "Coverage", "load_translation", "lectionary_refs", "check_coverage", "check_files", "progress"]

TRANSLATION_DIR = DATA_DIR / "biblia"
_CODES = {b.code for b in BOOKS}


@dataclass
class Gap:
    book: str
    chapter: int
    verse: int
    parts_needed: int = 0  # >0: o versículo precisa de ao menos tantas partes (letras)

    def __str__(self) -> str:
        extra = f" (precisa de {self.parts_needed} partes)" if self.parts_needed else ""
        return f"{self.book} {self.chapter}:{self.verse}{extra}"


@dataclass
class Coverage:
    needed: int = 0
    gaps: list[Gap] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)

    @property
    def covered(self) -> int:
        return self.needed - len(self.gaps)


def load_translation(directory: Path = TRANSLATION_DIR) -> dict[str, dict[tuple[int, int], dict]]:
    out: dict[str, dict[tuple[int, int], dict]] = {}
    if not directory.exists():
        return out
    for path in sorted(directory.glob("*.yaml")):
        doc = load_yaml(path)
        verses = {}
        for key, verse in doc["versiculos"].items():
            c, v = key.split(":")
            verses[(int(c), int(v))] = verse
        for key, reason in doc.get("omitidos", {}).items():  # ausentes do texto-base, por decisão
            c, v = key.split(":")
            verses[(int(c), int(v))] = {"texto": "", "status": "omitido", "observacao": reason}
        out[doc["livro"]] = verses
    return out


def lectionary_refs(root: Path = ROOT) -> list[str]:
    refs: list[str] = []
    for path in sorted((root / "data" / "lecionario").glob("*.yaml")):
        doc = load_yaml(path)
        for reading in doc["leituras"].values():
            refs += [r["ref"] for r in reading.values() if isinstance(r, dict) and "ref" in r]
    return refs


def _parts_needed(ref: Ref) -> dict[tuple[int, int], int]:
    """Versículo -> maior letra citada (a=1, b=2...). Ignora versículos sem letra."""
    need: dict[tuple[int, int], int] = {}
    for s in ref.segments:
        for (c, v, letters) in ((s.c1, s.v1, s.l1), (s.end_chapter, s.end_verse, s.l2)):
            if v is not None and letters:
                need[(c, v)] = max(need.get((c, v), 0), max(ord(ch) - 96 for ch in letters))
    return need


def check_coverage(root: Path = ROOT, translation: dict | None = None) -> Coverage:
    """Confere se cada referência do Lecionário tem tradução, versículo a versículo."""
    translation = load_translation(root / "data" / "biblia") if translation is None else translation
    vrs = default_versification(str(root))
    required: dict[str, dict[tuple[int, int], int]] = {}
    result = Coverage()
    for text in sorted(set(lectionary_refs(root))):
        try:
            ref = parse_ref(text, "br")
        except ValueError:
            result.unreadable.append(text)
            continue
        need = _parts_needed(ref)
        for cv in ref.verses(vrs.max_verses):
            required.setdefault(ref.book, {})
            required[ref.book][cv] = max(required[ref.book].get(cv, 0), need.get(cv, 0))
        for cv, n in need.items():  # letras em versículo que a expansão não alcançou
            required.setdefault(ref.book, {})
            required[ref.book][cv] = max(required[ref.book].get(cv, 0), n)
    for book in sorted(required):
        have = translation.get(book, {})
        for (c, v), parts in sorted(required[book].items()):
            result.needed += 1
            verse = have.get((c, v))
            if verse is None or (parts and len(verse.get("partes", [])) < parts):
                result.gaps.append(Gap(book, c, v, parts))
    return result


def check_files(root: Path = ROOT) -> list[str]:
    """Erros de esquema e de versículos fora da versificação. Lista vazia = válido."""
    errors: list[str] = []
    directory = root / "data" / "biblia"
    if not directory.exists():
        return errors
    schema = load_schema(root / "schemas" / "traducao.schema.json")
    max_verses = default_versification(str(root)).max_verses
    for path in sorted(directory.glob("*.yaml")):
        doc = load_yaml(path)
        errors += [f"{path.name}: {e}" for e in validate(doc, schema)]
        if errors and errors[-1].startswith(path.name):
            continue
        if doc["livro"] != path.stem or doc["livro"] not in _CODES:
            errors.append(f"{path.name}: código de livro inválido ou diferente do nome do arquivo")
            continue
        limits = max_verses.get(doc["livro"], [])
        for key in [*doc["versiculos"], *doc.get("omitidos", {})]:
            c, v = map(int, key.split(":"))
            if c < 1 or c > len(limits) or v < 1 or v > limits[c - 1]:
                errors.append(f"{path.name}: {key} fora da versificação")
    return errors


def progress(root: Path = ROOT, translation: dict | None = None) -> list[tuple[str, int, int]]:
    """Por livro com algo traduzido: (código, versículos traduzidos, versículos do livro)."""
    translation = load_translation(root / "data" / "biblia") if translation is None else translation
    max_verses = default_versification(str(root)).max_verses
    return [(code, len(verses), sum(int(n) for n in max_verses.get(code, [])))
            for code, verses in sorted(translation.items())]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida a tradução e mostra a cobertura do Lecionário.")
    parser.add_argument("--progresso", action="store_true", help="mostra o avanço por livro")
    parser.add_argument("--exigir-completo", action="store_true", help="falha se faltar algum versículo")
    args = parser.parse_args(argv)
    if args.progresso:
        for code, done, total in progress():
            print(f"{code}: {done}/{total}")
    errors = check_files()
    for e in errors:
        print("ERRO:", e)
    cov = check_coverage()
    print(f"Versículos do Lecionário: {cov.needed}; traduzidos: {cov.covered}; faltando: {len(cov.gaps)}")
    if cov.unreadable:
        print(f"Referências ilegíveis: {len(cov.unreadable)}")
        for text in cov.unreadable[:10]:
            print("  ", text)
    if errors or (args.exigir_completo and (cov.gaps or cov.unreadable)):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
