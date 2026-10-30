"""Tradução: esquema, versificação e cobertura das referências do Lecionário."""

from pathlib import Path

import pytest
import yaml

from vitral.translation import check_coverage, check_files

ROOT = Path(__file__).resolve().parents[1]


def test_every_lectionary_ref_is_readable():
    cov = check_coverage(ROOT, translation={})
    assert cov.unreadable == []
    assert cov.needed > 10000


def test_covering_a_gap_reduces_it():
    base = check_coverage(ROOT, translation={})
    gap = next(g for g in base.gaps if not g.parts_needed)
    cov = check_coverage(ROOT, translation={gap.book: {(gap.chapter, gap.verse): {"texto": "x"}}})
    assert len(cov.gaps) == len(base.gaps) - 1


def test_half_verses_need_parts():
    base = check_coverage(ROOT, translation={})
    gap = next(g for g in base.gaps if g.parts_needed)
    whole = {gap.book: {(gap.chapter, gap.verse): {"texto": "x"}}}
    assert len(check_coverage(ROOT, translation=whole).gaps) == len(base.gaps)
    parts = {gap.book: {(gap.chapter, gap.verse): {"texto": "x", "partes": ["a"] * gap.parts_needed}}}
    assert len(check_coverage(ROOT, translation=parts).gaps) == len(base.gaps) - 1


@pytest.fixture
def sandbox(tmp_path):
    (tmp_path / "schemas").symlink_to(ROOT / "schemas")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "fontes").symlink_to(ROOT / "data" / "fontes")
    (tmp_path / "data" / "biblia").mkdir()
    return tmp_path


def _write(root, code, verses, fonte="sblgnt"):
    doc = {"livro": code, "fonte": fonte, "versiculos": verses}
    (root / "data" / "biblia" / f"{code}.yaml").write_text(yaml.safe_dump(doc, allow_unicode=True), "utf8")


def test_valid_file_passes(sandbox):
    _write(sandbox, "JHN", {"3:16": {"texto": "Porque Deus amou o mundo.", "status": "ia-sem-revisao"}})
    assert check_files(sandbox) == []


@pytest.mark.parametrize("key, verse, fragment", [
    ("3:16", {"texto": "x", "status": "oficial"}, "status"),
    ("3:99", {"texto": "x", "status": "revisado"}, "fora da versificação"),
    ("99:1", {"texto": "x", "status": "revisado"}, "fora da versificação"),
])
def test_invalid_file_is_reported(sandbox, key, verse, fragment):
    _write(sandbox, "JHN", {key: verse})
    assert any(fragment in e for e in check_files(sandbox))


def test_omitted_verse_counts_as_covered_and_is_validated(sandbox):
    doc = {"livro": "MRK", "fonte": "sblgnt", "omitidos": {"7:16": "Ausente do SBLGNT."},
           "versiculos": {"1:1": {"texto": "x", "status": "ia-sem-revisao"}}}
    (sandbox / "data" / "biblia" / "MRK.yaml").write_text(yaml.safe_dump(doc, allow_unicode=True), "utf8")
    assert check_files(sandbox) == []
    base = check_coverage(ROOT, translation={})
    with_omitted = check_coverage(ROOT, translation={"MRK": {(7, 16): {"texto": "", "status": "omitido"}}})
    assert len(with_omitted.gaps) == len(base.gaps) - 1
    doc["omitidos"] = {"7:99": "fora"}
    (sandbox / "data" / "biblia" / "MRK.yaml").write_text(yaml.safe_dump(doc, allow_unicode=True), "utf8")
    assert any("fora da versificação" in e for e in check_files(sandbox))


def test_daniel_accepts_catholic_numbering(sandbox):
    ok = {"status": "ia-sem-revisao", "texto": "x"}
    _write(sandbox, "DAN", {"3:91": ok, "3:52": ok, "13:62": ok, "14:42": ok}, fonte="oshb")
    assert check_files(sandbox) == []
    _write(sandbox, "DAN", {"3:101": ok, "13:65": ok}, fonte="oshb")
    assert len([e for e in check_files(sandbox) if "fora da versificação" in e]) == 2
