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
    url = youtube_search("salmo responsorial Sl 22(23) 4º Domingo da Páscoa ano A")
    parsed = urlparse(url)
    assert parsed.netloc == "www.youtube.com" and parsed.path == "/results"
    assert parse_qs(parsed.query)["search_query"] == ["salmo responsorial Sl 22(23) 4º Domingo da Páscoa ano A"]


def test_searches_use_only_reference_and_day_name(book):
    for bd in book.days:
        for s in (bd.psalm_search, bd.gospel_search):
            if s is None:
                continue
            assert bd.day.name in s.query
            reading = bd.readings.get("salmo" if s.label.startswith("Salmo") else "evangelho")
            assert reading.display in s.query
            rest = s.query.replace(reading.display, "").replace(bd.day.name, "")
            assert set(rest.split()) <= {"salmo", "responsorial", "evangelho", "ano", "A", "B", "C"}


def test_every_day_has_one_page_and_printed_url_for_each_qr(book):
    assert len(book.days) == 364
    html = day_section(book.days[0])
    assert html.count("<svg") == 2
    assert html.count("https://www.youtube.com/results?search_query=") == 4  # link + texto, 2 buscas


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


def test_no_reading_text_only_references(book):
    """O livro não traz texto bíblico: cada leitura é uma referência curta."""
    for bd in book.days:
        for r in bd.reading_list():
            if r.display:
                assert len(r.display) < 80
