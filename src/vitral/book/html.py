"""HTML (XHTML válido) compartilhado pelo PDF e pelo EPUB.

O texto aqui é de interface (títulos, rótulos e explicações de uso), mais duas fontes de texto corrido:
as leituras, traduzidas por IA a partir do original (data/biblia/, sem revisão humana, avisado na abertura),
e os comentários de conteudo/ (humanos e licenciados). Nenhum texto espiritual é gerado.
"""

from __future__ import annotations

from html import escape

import segno
from markdown_it import MarkdownIt

from ..content import LICENSE_LABELS
from ..liturgy.model import Color
from ..reading_text import reading_verses
from .calendar_image import FILL
from .model import BookDay, BookYear

_md = MarkdownIt("commonmark", {"html": False, "xhtmlOut": True, "linkify": False})

SOURCES = [
    ("Liturgical Calendar API", "Apache-2.0", "https://github.com/Liturgical-Calendar/LiturgicalCalendarAPI",
     "conferência de datas e referências"),
    ("romcal", "MIT", "https://github.com/romcal/romcal", "nomes, datas e graus das celebrações"),
    ("Tamil Catholic Lectionary (jayarathina)", "domínio público (Unlicense)",
     "https://github.com/jayarathina/Tamil-Catholic-Lectionary", "referências do lecionário"),
    ("Copenhagen Alliance — versification mappings", "CC BY-SA 4.0",
     "https://github.com/Copenhagen-Alliance/versification-specification", "conversão de versículos"),
    ("CNBB, Comissão Episcopal Pastoral para a Liturgia — Celebrar em Família: Nossa Senhora da "
     "Conceição Aparecida", "direitos reservados; só as referências bíblicas são citadas",
     "https://www.cnbb.org.br/wp-content/uploads/2021/10/56-Celebrar-e-Familia-NSraAparecida.pdf",
     "referências das leituras da solenidade de Nossa Senhora Aparecida"),
]
TRANSLATION_BASES = [
    ("SBL Greek New Testament (SBLGNT), © Society of Biblical Literature e Logos Bible Software", "CC BY 4.0",
     "https://sblgnt.com/", "texto-base do Novo Testamento; o grego não é publicado e a tradução é nova"),
    ("Open Scriptures Hebrew Bible (OSHB), Códice de Leningrado", "texto em domínio público; lemas e morfologia CC BY 4.0",
     "https://github.com/openscriptures/morphhb", "texto-base do Antigo Testamento"),
    ("Vulgata Clementina (eBible.org)", "domínio público", "https://ebible.org/latVUC/",
     "texto-base dos livros deuterocanônicos"),
    ("Novum Testamentum Graece (Nestle, 1904)", "domínio público",
     "https://github.com/biblicalhumanities/Nestle1904", "somente Rm 16,25-27"),
]
NORMS = [
    "Normas Universais sobre o Ano Litúrgico e o Calendário (Paulo VI, Mysterii Paschalis, 1969)",
    "Decreto De celebratione Baptismatis Domini (Sagrada Congregação para os Sacramentos e o Culto Divino, 1977)",
    "Notificação sobre a memória da Bem-Aventurada Virgem Maria, Mãe da Igreja (Congregação para o Culto "
    "Divino e a Disciplina dos Sacramentos, 2018)",
    "Responsum ad dubia de calendario liturgico pro anno 2022 (Congregação para o Culto Divino e a Disciplina "
    "dos Sacramentos, 2020)",
]
WEEKDAY_ABBR = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
FONTS = [("EB Garamond", "SIL Open Font License 1.1"), ("Source Sans 3", "SIL Open Font License 1.1")]


def e(text: object) -> str:
    return escape(str(text), quote=True)


def qr_svg(url: str) -> str:
    """QR code em SVG embutido (sem dimensões fixas; o CSS define o tamanho)."""
    qr = segno.make(url, error="m")
    svg = qr.svg_inline(scale=1, border=2, dark="#111111", omitsize=True)
    if "xmlns=" not in svg:  # XHTML (EPUB) exige o namespace no SVG embutido
        svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    return svg.replace("<svg ", '<svg aria-hidden="true" ', 1)


def color_chip(color: Color) -> str:
    return f'<span class="chip chip-{color.name.lower()}" style="background:{FILL[color]}"></span>'


def reading_text(label: str, ref: str | None) -> str:
    """Texto de uma leitura: versículos numerados, em ordem. Vazio se não há referência ou tradução."""
    verses = reading_verses(ref) if ref else []
    if not verses:
        return ""
    chapter = verses[0].chapter
    body = []
    for v in verses:
        num = v.label if v.chapter == chapter else f"{v.chapter},{v.label}"
        body.append(f'<sup class="v">{e(num)}</sup>{e(v.text)}')
    return (f'<div class="leitura-texto"><h3>{e(label)} · {e(ref)}</h3>'
            f'<p>{" ".join(body)}</p></div>')


def day_section(bd: BookDay, anchor: bool = True) -> str:
    d = bd.day
    h = [f'<section class="dia" id="d{bd.date.isoformat()}">' if anchor else '<section class="dia">']
    h.append(f'<p class="data">{e(bd.date_label)}</p>')
    h.append(f'<h2 class="nome">{e(d.name)}</h2>')
    meta = [e(bd.season_label), e(bd.cycle_label)]
    if bd.rank_label:
        meta.insert(0, e(bd.rank_label))
    colors = [d.color] + [c for c in d.alt_colors if c is not d.color]
    chip = "".join(color_chip(c) for c in colors)
    color_txt = " ou ".join(c.label.lower() for c in colors)
    h.append(f'<p class="meta">{chip} Cor: {e(color_txt)} · {" · ".join(meta)}</p>')
    for note in bd.notes:
        h.append(f'<p class="nota">{e(note)}</p>')

    h.append('<table class="leituras"><tbody>')
    for r in bd.reading_list():
        if r.ref:
            ref = e(r.ref)
            if r.alternatives:
                ref += f' <span class="alt">(ou {e("; ".join(r.alternatives))})</span>'
        elif r.chapter:
            ref = f'{e(r.chapter)} <span class="alt">(versículos a conferir)</span>'
        else:
            ref = '<span class="alt">referência a conferir</span>'
        h.append(f'<tr><th scope="row">{e(r.label)}</th><td>{ref}</td></tr>')
    if not bd.reading_list():
        h.append('<tr><td colspan="2" class="alt">Referências ainda não disponíveis para este dia. '
                 'Consulte os links oficiais.</td></tr>')
    h.append("</tbody></table>")

    for r in bd.reading_list():
        h.append(reading_text(r.label, r.ref))

    searches = [s for s in (bd.psalm_search, bd.gospel_search) if s]
    if searches:
        h.append('<div class="buscas">')
        for s in searches:
            h.append('<div class="busca">')
            h.append(f'<div class="qr">{qr_svg(s.url)}</div>')
            h.append(f'<p class="busca-rotulo">Busca no YouTube: {e(s.label.lower())}</p>')
            h.append(f'<p class="url"><a href="{e(s.url)}">{e(s.url)}</a></p>')
            h.append("</div>")
        h.append("</div>")

    for item in bd.content:
        h.append('<div class="comentario">')
        if item.title:
            h.append(f"<h3>{e(item.title)}</h3>")
        h.append(_md.render(item.body))
        credit = f"{e(item.author)} · {e(LICENSE_LABELS[item.license])}"
        if item.source:
            src = item.source
            credit += f" · {e(src['obra'])}, {e(src['edicao'])}"
            if src.get("tradutor"):
                credit += f", trad. {e(src['tradutor'])}"
            credit += f", {e(src['ano'])}"
        h.append(f'<p class="credito">{credit}</p></div>')

    h.append('<div class="anotacoes"><p class="anotacoes-rotulo">Anotações</p></div>')
    h.append("</section>")
    return "\n".join(h)


def toc_page(book: BookYear, href) -> str:
    """Sumário com todos os dias, por mês. ``href(bd)`` dá o destino do link de cada dia.

    No PDF, o CSS acrescenta o número da página (``target-counter``); no EPUB o link basta."""
    out = ['<section class="texto toc" id="sumario"><h1>Sumário</h1>',
           '<p class="toc-dica">Procure o mês e o dia que deseja; cada dia começa em uma página nova.</p>']
    for label, days in book.months():
        out.append(f'<h2>{e(label)}</h2><ul>')
        for bd in days:
            d = bd.date
            out.append(f'<li><a href="{e(href(bd))}"><span class="toc-data">{WEEKDAY_ABBR[d.weekday()]} {d.day:02d}</span>'
                       f'<span class="toc-nome">{e(bd.day.name)}</span></a></li>')
        out.append("</ul>")
    out.append("</section>")
    return "\n".join(out)


def links_list(book: BookYear) -> str:
    rows = []
    labels = {"liturgia-diaria": "Leituras do dia", "comentario": "Comentário", "biblia": "Bíblia",
              "calendario": "Calendário"}
    for link in book.links:
        rows.append(f'<li><strong>{e(labels.get(link["tipo"], link["tipo"]))}:</strong> {e(link["titulo"])} — '
                    f'<a href="{e(link["url"])}">{e(link["url"])}</a></li>')
    return '<ul class="links">' + "\n".join(rows) + "</ul>"


def title_page(book: BookYear) -> str:
    return f"""<section class="rosto">
<h1>Vitral</h1>
<p class="subtitulo">Leituras para lectio divina</p>
<p class="ano">Ano litúrgico {book.year}–{book.year + 1}</p>
<p class="ciclo">Ano {e(book.sunday_cycle)} · ciclo ferial {e(book.weekday_cycle)} · calendário do Brasil</p>
</section>"""


def how_to(book: BookYear) -> str:
    return f"""<section class="texto" id="como-usar">
<h1>Como usar este livro</h1>
<p>Cada dia do ano litúrgico tem uma página com a data, o nome do dia, o tempo, a cor litúrgica e as
<strong>referências</strong> das leituras da Missa, seguidas do texto de cada leitura.</p>
<h2>Sobre o texto das leituras</h2>
<p>O texto das leituras é uma <strong>tradução feita por inteligência artificial</strong>, sem revisão humana,
sob responsabilidade e edição do mantenedor do projeto. Parte dos originais: o grego do Novo Testamento
(SBL Greek New Testament), o hebraico e o aramaico do Antigo Testamento (Open Scriptures Hebrew Bible) e, nos
livros deuterocanônicos, o latim da Vulgata Clementina. Não é a tradução usada na liturgia, e onde o
original difere da Nova Vulgata (base do Lecionário) o texto segue o original. Para a proclamação litúrgica,
use a Bíblia ou o lecionário aprovado; os sites oficiais abaixo trazem as leituras do dia.</p>
<p>Os QR codes abrem uma <strong>busca no YouTube</strong> pelo salmo responsorial e pelo evangelho do dia.
A busca usa só a referência e o nome do dia; os resultados são de terceiros e mudam com o tempo.
O endereço de cada busca também vem escrito.</p>
<p>As referências seguem a numeração das Bíblias católicas usadas no Brasil. Quando há forma
breve ou leitura alternativa, ela vem entre parênteses.</p>
<p>As memórias aparecem como nota. Quando uma memória obrigatória tem leituras próprias, elas
substituem as do dia, como manda o Lecionário.</p>
<h2>Leituras e comentários oficiais</h2>
{links_list(book)}
</section>"""


def calendar_page(book: BookYear, calendar_img: str) -> str:
    rows = []
    for bd in book.highlights():
        d = bd.date
        rank = bd.rank_label or "Domingo"
        rows.append(f'<tr><td>{d.day:02d}/{d.month:02d}/{d.year}</td><td>{color_chip(bd.day.color)}</td>'
                    f'<td>{e(bd.day.name)}</td><td>{e(rank)}</td></tr>')
    return f"""<section class="texto" id="calendario">
<h1>Calendário do ano</h1>
<figure class="calendario">{calendar_img}
<figcaption>Cada quadrado é um dia, na cor litúrgica. Domingos têm contorno escuro;
solenidades e festas, um ponto.</figcaption></figure>
</section>
<section class="texto" id="tabela">
<h1>Domingos, solenidades e festas</h1>
<table class="tabela"><thead><tr><th>Data</th><th>Cor</th><th>Celebração</th><th>Grau</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody></table>
</section>"""


def credits_page(book: BookYear) -> str:
    sources = "\n".join(f"<li>{e(n)} ({e(lic)}): {e(use)}. <a href=\"{e(u)}\">{e(u)}</a></li>"
                        for n, lic, u, use in SOURCES)
    fonts = "\n".join(f"<li>{e(n)} — {e(lic)}</li>" for n, lic in FONTS)
    bases = "\n".join(f"<li>{e(n)} ({e(lic)}): {e(use)}. <a href=\"{e(u)}\">{e(u)}</a></li>"
                      for n, lic, u, use in TRANSLATION_BASES)
    norms = "\n".join(f"<li>{e(n)}</li>" for n in NORMS)
    people = sorted({(c.author, c.license) for c in book.contributors()})
    authors = ("<ul>" + "\n".join(f"<li>{e(a)} — {e(LICENSE_LABELS[lic])}</li>" for a, lic in people) + "</ul>"
               if people else "<p>Nenhum texto de colaboradores neste ano.</p>")
    return f"""<section class="texto" id="creditos">
<h1>Créditos e licenças</h1>
<p>Este livro traz <strong>referências bíblicas</strong>, o <strong>texto das leituras</strong> em tradução
própria por inteligência artificial, sem revisão humana, e <strong>links</strong>. Não reproduz o texto das
leituras, dos salmos nem de comentários de terceiros em traduções com direitos.</p>
<h2>Textos-base da tradução</h2>
<ul>{bases}</ul>
<h2>Dados</h2>
<ul>{sources}</ul>
<h2>Normas do calendário</h2>
<ul>{norms}</ul>
<p>Com as determinações da CNBB para o Brasil. A procedência de cada dado está em
<code>docs/FONTES.md</code> no repositório do projeto.</p>
<h2>Textos de colaboradores</h2>
{authors}
<h2>Fontes tipográficas</h2>
<ul>{fonts}</ul>
<h2>Licenças do projeto</h2>
<p>Código: MIT. Conteúdo original e dados derivados: Creative Commons Atribuição-CompartilhaIgual 4.0
(CC BY-SA 4.0). Textos de colaboradores: a licença indicada em cada texto.</p>
</section>"""
