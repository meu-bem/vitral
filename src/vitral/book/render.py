"""Saídas do livro: PDF (WeasyPrint), EPUB 3 (zip montado à mão) e AZW3 (Calibre, opcional).

Reprodutibilidade: mesmas entradas geram os mesmos bytes. A data registrada nos
arquivos é fixa e derivada do ano (1º Domingo do Advento), ou SOURCE_DATE_EPOCH.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .calendar_image import calendar_png, calendar_svg
from .html import calendar_page, credits_page, day_section, how_to, title_page
from .model import BookYear

LIVRO_DIR = Path(__file__).resolve().parents[3] / "livro"
FONT_FILES = sorted((LIVRO_DIR / "fontes").glob("*.ttf"))
LANG = "pt-BR"


def build_timestamp(book: BookYear) -> datetime:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc)
    s = book.start
    return datetime(s.year, s.month, s.day, tzinfo=timezone.utc)


def _head(book: BookYear, css_href: str, extra: str = "") -> str:
    ts = build_timestamp(book).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (f'<head><meta charset="utf-8"/><title>{escape(book.title)}</title>'
            f'<meta name="author" content="Projeto Vitral"/>'
            f'<meta name="description" content="{escape(book.subtitle)}"/>'
            f'<meta name="generator" content="Vitral"/>'
            f'<meta name="dcterms.created" content="{ts}"/><meta name="dcterms.modified" content="{ts}"/>'
            f'<link rel="stylesheet" href="{css_href}"/>{extra}</head>')


# ------------------------------------------------------------------ PDF
def book_html(book: BookYear) -> str:
    parts = [title_page(book), how_to(book), calendar_page(book, calendar_svg(book))]
    for label, days in book.months():
        parts.append(f'<section class="mes"><h1 class="mes-titulo">{escape(label)}</h1></section>')
        parts += [day_section(bd) for bd in days]
    parts.append(credits_page(book))
    head = _head(book, "estilo.css", '<link rel="stylesheet" href="estilo-pdf.css"/>')
    return (f'<!DOCTYPE html><html lang="{LANG}" class="pdf">{head}<body>'
            + "\n".join(parts) + "</body></html>")


def write_pdf(book: BookYear, target: Path) -> Path:
    from weasyprint import HTML

    # O fontTools grava a data de criação dos subconjuntos de fonte; com SOURCE_DATE_EPOCH ela fica fixa.
    os.environ.setdefault("SOURCE_DATE_EPOCH", str(int(build_timestamp(book).timestamp())))
    html = HTML(string=book_html(book), base_url=str(LIVRO_DIR) + "/")
    ident = hashlib.sha256(f"vitral-{book.year}".encode()).digest()[:16]
    html.write_pdf(target, pdf_identifier=ident, pdf_variant=None)
    return target


# ------------------------------------------------------------------ EPUB 3
def _xhtml(book: BookYear, title: str, body: str) -> str:
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
            f'xml:lang="{LANG}" lang="{LANG}">'
            f'<head><meta charset="utf-8"/><title>{escape(title)}</title>'
            '<link rel="stylesheet" type="text/css" href="estilo.css"/></head>'
            f'<body class="epub">{body}</body></html>\n')


def _cover_png(book: BookYear) -> bytes:
    """Capa simples: título sobre uma faixa com as cores do ano (sem ilustração de terceiros)."""
    import io

    from PIL import Image, ImageDraw, ImageFont

    from .calendar_image import FILL

    w, h = 1600, 2400
    img = Image.new("RGB", (w, h), "#fffdf8")
    draw = ImageDraw.Draw(img)
    cols, size = 14, w // 14
    for i, bd in enumerate(book.days[: cols * 7]):
        x, y = (i % cols) * size, h - (7 - i // cols) * size
        draw.rectangle([x + 3, y + 3, x + size - 3, y + size - 3], fill=FILL[bd.day.color])
    serif = ImageFont.truetype(str(LIVRO_DIR / "fontes" / "EBGaramond-Regular.ttf"), 230)
    sans = ImageFont.truetype(str(LIVRO_DIR / "fontes" / "SourceSans3-Regular.ttf"), 70)
    draw.text((w / 2, 620), "Vitral", fill="#1d1d1d", font=serif, anchor="ms")
    draw.text((w / 2, 780), "LEITURAS PARA LECTIO DIVINA", fill="#555555", font=sans, anchor="ms")
    draw.text((w / 2, 1000), f"Ano litúrgico {book.year}–{book.year + 1}", fill="#1d1d1d", font=sans, anchor="ms")
    draw.text((w / 2, 1100), f"Ano {book.sunday_cycle} · ciclo {book.weekday_cycle}", fill="#555555", font=sans,
              anchor="ms")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def epub_files(book: BookYear) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    chapters: list[tuple[str, str, str]] = []  # (arquivo, título, propriedades)

    def add(name: str, title: str, body: str, props: str = ""):
        files[f"OEBPS/{name}"] = _xhtml(book, title, body).encode()
        chapters.append((name, title, props))

    add("rosto.xhtml", "Rosto", title_page(book))
    add("como-usar.xhtml", "Como usar este livro", how_to(book))
    add("calendario.xhtml", "Calendário do ano",
        calendar_page(book, '<img src="calendario.png" alt="Grade do ano litúrgico com a cor de cada dia"/>'))
    for i, (label, days) in enumerate(book.months(), start=1):
        body = f'<h1 class="mes-titulo">{escape(label)}</h1>' + "\n".join(day_section(bd) for bd in days)
        add(f"mes-{i:02d}.xhtml", label, body, "svg")
    add("creditos.xhtml", "Créditos e licenças", credits_page(book))

    files["OEBPS/estilo.css"] = (LIVRO_DIR / "estilo.css").read_bytes()
    for f in FONT_FILES:
        files[f"OEBPS/fontes/{f.name}"] = f.read_bytes()
    files["OEBPS/calendario.png"] = calendar_png(book)
    files["OEBPS/capa.png"] = _cover_png(book)

    nav = "".join(f'<li><a href="{n}">{escape(t)}</a></li>' for n, t, _ in chapters)
    files["OEBPS/nav.xhtml"] = _xhtml(book, "Sumário",
                                      f'<nav epub:type="toc" id="toc"><h1>Sumário</h1><ol>{nav}</ol></nav>').encode()

    uid = f"urn:uuid:{_uuid_for(book)}"
    modified = build_timestamp(book).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="css" href="estilo.css" media-type="text/css"/>',
                '<item id="cal" href="calendario.png" media-type="image/png"/>',
                '<item id="capa" href="capa.png" media-type="image/png" properties="cover-image"/>']
    for i, f in enumerate(FONT_FILES):
        manifest.append(f'<item id="font{i}" href="fontes/{f.name}" media-type="font/ttf"/>')
    spine = []
    for i, (n, _, props) in enumerate(chapters):
        p = f' properties="{props}"' if props else ""
        manifest.append(f'<item id="c{i}" href="{n}" media-type="application/xhtml+xml"{p}/>')
        spine.append(f'<itemref idref="c{i}"/>')
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="{LANG}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">{uid}</dc:identifier>
<dc:title>{escape(book.title)}</dc:title>
<dc:language>{LANG}</dc:language>
<dc:creator>Projeto Vitral</dc:creator>
<dc:description>{escape(book.subtitle)}</dc:description>
<dc:rights>Conteúdo original: CC BY-SA 4.0. Textos de colaboradores: licença indicada em cada texto.</dc:rights>
<meta property="dcterms:modified">{modified}</meta>
<meta name="cover" content="capa"/>
</metadata>
<manifest>
{chr(10).join(manifest)}
</manifest>
<spine>
{chr(10).join(spine)}
</spine>
</package>
"""
    files["OEBPS/content.opf"] = opf.encode()
    files["META-INF/container.xml"] = (
        b'<?xml version="1.0" encoding="utf-8"?>\n<container version="1.0" '
        b'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
        b'<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
        b"</rootfiles></container>\n")
    return files


def _uuid_for(book: BookYear) -> str:
    import uuid

    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://vitral/livro/{book.year}"))


def write_epub(book: BookYear, target: Path) -> Path:
    files = epub_files(book)
    fixed = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(target, "w") as z:
        info = zipfile.ZipInfo("mimetype", fixed)
        info.compress_type = zipfile.ZIP_STORED
        z.writestr(info, b"application/epub+zip")
        for name in sorted(files):
            info = zipfile.ZipInfo(name, fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[name])
    return target


# ------------------------------------------------------------------ AZW3 (opcional)
def write_azw3(epub: Path, target: Path) -> Path | None:
    """Converte com o Calibre, se houver. Falha não interrompe o build."""
    tool = shutil.which("ebook-convert")
    if not tool:
        print("aviso: ebook-convert (Calibre) não encontrado; AZW3 não gerado")
        return None
    env = dict(os.environ, CALIBRE_NO_NATIVE_FILEDIALOGS="1", QT_QPA_PLATFORM="offscreen")
    try:
        subprocess.run([tool, str(epub), str(target), "--no-inline-toc"], check=True, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=900)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"aviso: falha ao gerar AZW3 ({exc}); o build continua")
        return None
    return target
