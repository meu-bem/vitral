"""Imagem do ano litúrgico: uma grade (meses × dias) colorida pela cor litúrgica.

A mesma geometria sai em SVG (texto, vetorial) e em PNG (Pillow), para o livro e o site.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path

from ..liturgy import Color, Rank, Season
from ..liturgy.temporale import MONTHS
from .model import BookYear

FONT_DIR = Path(__file__).resolve().parents[3] / "livro" / "fontes"

FILL = {
    Color.VIOLET: "#5b3a8c",
    Color.WHITE: "#f4efe3",
    Color.GREEN: "#3d7a4f",
    Color.RED: "#b0322b",
    Color.ROSE: "#d58fb2",
    Color.BLACK: "#2b2b2b",
}
INK = "#222222"
MUTED = "#6b6b6b"
SEASON_FILL = {
    Season.ADVENT: FILL[Color.VIOLET], Season.CHRISTMAS: "#c9a227", Season.ORDINARY: FILL[Color.GREEN],
    Season.LENT: FILL[Color.VIOLET], Season.TRIDUUM: FILL[Color.RED], Season.EASTER: "#c9a227",
}

CELL, GAP, LEFT, TOP = 34, 4, 150, 130
WIDTH = LEFT + 31 * (CELL + GAP) + 40


@dataclass
class Shape:
    kind: str  # rect | text | circle
    x: float
    y: float
    w: float = 0
    h: float = 0
    fill: str = ""
    stroke: str = ""
    text: str = ""
    size: int = 14
    weight: str = "normal"
    anchor: str = "start"


def _layout(book: BookYear) -> tuple[list[Shape], int]:
    shapes: list[Shape] = []
    shapes.append(Shape("text", LEFT, 48, text=f"Ano litúrgico {book.year}–{book.year + 1}", size=30, weight="bold",
                        fill=INK))
    shapes.append(Shape("text", LEFT, 84, size=17, fill=MUTED,
                        text=f"Ano {book.sunday_cycle} (domingos) · ciclo {book.weekday_cycle} (dias de semana) · "
                             f"do 1º Domingo do Advento ({book.start.day}/{book.start.month}/{book.year}) "
                             f"ao sábado antes do Advento seguinte"))
    for d in range(1, 32):
        shapes.append(Shape("text", LEFT + (d - 1) * (CELL + GAP) + CELL / 2, TOP - 10, text=str(d), size=12,
                            fill=MUTED, anchor="middle"))
    rows: list[tuple[int, int]] = []
    for bd in book.days:
        key = (bd.date.year, bd.date.month)
        if key not in rows:
            rows.append(key)
    by_date = {bd.date: bd for bd in book.days}
    for r, (y, m) in enumerate(rows):
        ry = TOP + r * (CELL + GAP)
        shapes.append(Shape("text", LEFT - 14, ry + CELL * 0.68, text=f"{MONTHS[m - 1].capitalize()} {y}",
                            size=15, fill=INK, anchor="end"))
        for dnum in range(1, 32):
            try:
                d = date(y, m, dnum)
            except ValueError:
                continue
            x = LEFT + (dnum - 1) * (CELL + GAP)
            bd = by_date.get(d)
            if bd is None:
                shapes.append(Shape("rect", x, ry, CELL, CELL, fill="#ffffff", stroke="#e4e0d8"))
                continue
            color = bd.day.color
            stroke = "#bdb4a3" if color is Color.WHITE else ""
            if d.weekday() == 6:
                stroke = INK
            shapes.append(Shape("rect", x, ry, CELL, CELL, fill=FILL[color], stroke=stroke))
            if bd.day.rank in (Rank.SOLEMNITY, Rank.FEAST) and bd.day.season is not Season.TRIDUUM:
                dot = INK if color in (Color.WHITE, Color.ROSE) else "#ffffff"
                if bd.day.rank is Rank.SOLEMNITY:
                    shapes.append(Shape("circle", x + CELL / 2, ry + CELL / 2, w=6, fill=dot))
                else:
                    shapes.append(Shape("circle", x + CELL / 2, ry + CELL / 2, w=3.5, fill=dot))
    height = TOP + len(rows) * (CELL + GAP) + 20
    # Legenda
    lx, ly = LEFT, height + 10
    legend = [(Color.VIOLET, "Roxo"), (Color.WHITE, "Branco"), (Color.RED, "Vermelho"),
              (Color.GREEN, "Verde")]
    for color, label in legend:
        shapes.append(Shape("rect", lx, ly, 22, 22, fill=FILL[color], stroke="#bdb4a3" if color is Color.WHITE else ""))
        shapes.append(Shape("text", lx + 30, ly + 17, text=label, size=15, fill=INK))
        lx += 140
    shapes.append(Shape("rect", lx, ly, 22, 22, fill="#ffffff", stroke=INK))
    shapes.append(Shape("text", lx + 30, ly + 17, text="Domingo", size=15, fill=INK))
    lx += 140
    shapes.append(Shape("circle", lx + 11, ly + 11, w=6, fill=INK))
    shapes.append(Shape("text", lx + 30, ly + 17, text="Solenidade", size=15, fill=INK))
    lx += 150
    shapes.append(Shape("circle", lx + 11, ly + 11, w=3.5, fill=INK))
    shapes.append(Shape("text", lx + 30, ly + 17, text="Festa", size=15, fill=INK))
    # Tempos
    ty = ly + 50
    tx = LEFT
    seasons: list[tuple[Season, date, date]] = []
    for bd in book.days:
        s = bd.day.season
        if seasons and seasons[-1][0] is s:
            seasons[-1] = (s, seasons[-1][1], bd.date)
        else:
            seasons.append((s, bd.date, bd.date))
    for s, a, b in seasons:
        label = f"{s.label}: {a.day}/{a.month} a {b.day}/{b.month}"
        shapes.append(Shape("rect", tx, ty, 10, 22, fill=SEASON_FILL[s]))
        shapes.append(Shape("text", tx + 16, ty + 17, text=label, size=14, fill=INK))
        tx += 8 * len(label) + 40
        if tx > WIDTH - 300:
            tx, ty = LEFT, ty + 30
    return shapes, ty + 50


def calendar_svg(book: BookYear, font_family: str = "'Source Sans 3', 'Source Sans Pro', sans-serif") -> str:
    shapes, height = _layout(book)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" '
           f'height="{height}" role="img" aria-labelledby="cal-title">',
           f'<title id="cal-title">Calendário do ano litúrgico {book.year}–{book.year + 1}</title>',
           f'<rect width="{WIDTH}" height="{height}" fill="#fffdf8"/>',
           f'<g font-family="{escape(font_family)}">']
    for s in shapes:
        if s.kind == "rect":
            stroke = f' stroke="{s.stroke}" stroke-width="1.5"' if s.stroke else ""
            out.append(f'<rect x="{s.x:g}" y="{s.y:g}" width="{s.w:g}" height="{s.h:g}" rx="3" fill="{s.fill}"{stroke}/>')
        elif s.kind == "circle":
            out.append(f'<circle cx="{s.x:g}" cy="{s.y:g}" r="{s.w:g}" fill="{s.fill}"/>')
        else:
            out.append(f'<text x="{s.x:g}" y="{s.y:g}" font-size="{s.size}" font-weight="{s.weight}" '
                       f'fill="{s.fill}" text-anchor="{s.anchor}">{escape(s.text)}</text>')
    out.append("</g></svg>")
    return "\n".join(out) + "\n"


def calendar_png(book: BookYear, scale: float = 1.5) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    shapes, height = _layout(book)
    img = Image.new("RGB", (int(WIDTH * scale), int(height * scale)), "#fffdf8")
    draw = ImageDraw.Draw(img)
    fonts: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}

    def font(size: int, weight: str):
        key = (size, weight)
        if key not in fonts:
            name = "SourceSans3-Semibold.ttf" if weight == "bold" else "SourceSans3-Regular.ttf"
            fonts[key] = ImageFont.truetype(str(FONT_DIR / name), int(size * scale))
        return fonts[key]

    k = scale
    for s in shapes:
        if s.kind == "rect":
            draw.rounded_rectangle([s.x * k, s.y * k, (s.x + s.w) * k, (s.y + s.h) * k], radius=int(3 * k),
                                   fill=s.fill, outline=s.stroke or None, width=int(1.5 * k) if s.stroke else 0)
        elif s.kind == "circle":
            draw.ellipse([(s.x - s.w) * k, (s.y - s.w) * k, (s.x + s.w) * k, (s.y + s.w) * k], fill=s.fill)
        else:
            anchor = {"start": "ls", "middle": "ms", "end": "rs"}[s.anchor]
            draw.text((s.x * k, s.y * k), s.text, fill=s.fill, font=font(s.size, s.weight), anchor=anchor)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)  # Pillow não grava data no PNG: saída reprodutível
    return buf.getvalue()
