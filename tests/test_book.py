"""Fase 4: modelo do livro, buscas, QR, HTML/XHTML, EPUB e reprodutibilidade."""

import io
import zipfile
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

import pytest

from vitral.book.calendar_image import calendar_png, calendar_svg
from vitral.book.html import day_section, qr_svg
from vitral.book.model import build_book_year, youtube_search
from vitral.book.render import epub_files, write_epub


@pytest.fixture(scope="module")
def book():
    return build_book_year(2026)


def test_youtube_search_is_a_stable_search_url():
    url = youtube_search("Salmo 22(23)")
    parsed = urlparse(url)
    assert parsed.netloc == "www.youtube.com" and parsed.path == "/results"
    assert parse_qs(parsed.query)["search_query"] == ["Salmo 22(23)"]


def test_searches_use_only_book_and_reference(book):
    """Nada de dia litúrgico, tempo ou cor: livro por extenso e referência; no salmo, só o número."""
    import re

    n = 0
    for bd in book.days:
        for r in bd.reading_list():
            s = bd.search_for(r)
            if not r.ref:
                assert s is None
                continue
            n += 1
            assert re.fullmatch(r"(?:[1-3] )?[A-Za-zÀ-ú ]+ \d+[^ ]*", s.query), s.query
            assert bd.day.name not in s.query and len(s.url) < 120
            if r.slot.startswith("salmo"):
                assert re.fullmatch(r"Salmo \d+[AB]?\(\d+[AB]?\)|Salmo \d+", s.query), s.query
    assert n > 1000


def test_search_query_examples():
    from vitral.formulas import search_query

    assert search_query("Lc 14,25-33", "evangelho") == "Lucas 14,25-33"
    assert search_query("Sl 89(90),3-4.5-6.12-13.14.17", "salmo") == "Salmo 89(90)"
    assert search_query("1Cor 15,20-26", "primeira_leitura") == "1 Coríntios 15,20-26"
    assert search_query("At 2,1-11", "segunda_leitura") == "Atos dos Apóstolos 2,1-11"
    assert search_query("Xx 1,1", "evangelho") is None


def test_every_reading_has_its_own_qr_after_the_text(book):
    """Um bloco de busca (título, QR e endereço) logo depois de cada leitura e de cada salmo."""
    html = day_section(book.days[0])
    n_readings = sum(1 for r in book.days[0].reading_list() if r.ref)
    chunks = html.split('<div class="leitura-texto')[1:]
    assert len(chunks) == n_readings == html.count('class="busca"') == html.count("<svg")
    assert all(chunk.count('class="busca"') == 1 for chunk in chunks)  # a busca vem logo depois do texto
    assert html.count("https://www.youtube.com/results?search_query=") == 2 * n_readings


def test_qr_svg_is_namespaced():
    svg = qr_svg("https://example.org")
    ElementTree.fromstring(svg)
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg


def test_calendar_images(book):
    ElementTree.fromstring(calendar_svg(book))
    png = calendar_png(book)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert calendar_png(book) == png


def test_epub_xhtml_is_well_formed(book):
    files = epub_files(book)
    for name, data in files.items():
        if name.endswith((".xhtml", ".opf", ".xml")):
            ElementTree.fromstring(data)
    assert "OEBPS/nav.xhtml" in files and "OEBPS/capa.png" in files


def test_epub_container_and_reproducibility(book, tmp_path):
    a, b = tmp_path / "a.epub", tmp_path / "b.epub"
    write_epub(book, a)
    write_epub(book, b)
    assert a.read_bytes() == b.read_bytes()
    with zipfile.ZipFile(io.BytesIO(a.read_bytes())) as z:
        first = z.infolist()[0]
        assert first.filename == "mimetype" and first.compress_type == zipfile.ZIP_STORED
        assert z.read("mimetype") == b"application/epub+zip"


def test_reading_reference_stays_short(book):
    """No modelo, cada leitura continua sendo uma referência curta; o texto vem de reading_text."""
    for bd in book.days:
        for r in bd.reading_list():
            if r.display:
                assert len(r.display) < 80


def test_every_reading_of_the_year_has_text(book):
    """Com a tradução completa, toda leitura com referência traz ao menos um versículo."""
    from vitral.reading_text import reading_verses

    for bd in book.days:
        for r in bd.reading_list():
            if r.ref:
                assert reading_verses(r.ref), f"{bd.date}: {r.ref} sem texto"


def test_reading_text_picks_only_cited_parts():
    from vitral.reading_text import reading_verses

    labels = [v.label for v in reading_verses("Sl 80(81),6c-8a.8bc-9.10-11ab.14.17")]
    assert labels[0] == "6c" and "8a" in labels and "8bc" in labels and labels[-1] == "17"
    assert [v.label for v in reading_verses("Est 4,17k-m.17r-t")] == ["17klm", "17rst"]
    assert reading_verses("Xx 1,1") == []


def test_day_html_shows_reading_text(book):
    from vitral.book.html import day_section

    html = day_section(book.days[0])
    assert 'class="leitura-texto' in html and '<sup class="v">' in html


def test_epub_qr_codes_are_png_files_listed_in_the_manifest(book):
    """O Kindle encolhe o SVG embutido; no EPUB/AZW3 o QR vai em PNG, com um arquivo por endereço."""
    import re
    import struct

    files = epub_files(book)
    pngs = sorted(n for n in files if n.startswith("OEBPS/qr/"))
    assert len(pngs) > 500
    opf = files["OEBPS/content.opf"].decode()
    for name in pngs[:50] + pngs[-50:]:
        data = files[name]
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", data[16:24])
        assert width == height >= 400  # módulos de 10 px: legível mesmo reduzido a 45% da largura
        assert name[len("OEBPS/"):] in opf
    month = files["OEBPS/mes-01.xhtml"].decode()
    assert "<svg" not in month
    used = set(re.findall(r'<img src="(qr/[0-9a-f]+\.png)"', month))
    assert used and all(f"OEBPS/{u}" in files for u in used)
