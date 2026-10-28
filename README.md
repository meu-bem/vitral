# Vitral

O Vitral gera, a cada ano litúrgico, um livro para lectio divina com as **referências** das
leituras da Missa de cada dia, segundo o calendário litúrgico do Brasil. Ele sai em PDF (A5),
EPUB (para Kindle) e AZW3, e é publicado num site estático.

Cada dia traz:

- a data, o dia litúrgico, o tempo e a cor;
- as referências da 1ª leitura, do salmo, da 2ª leitura e do evangelho;
- QR codes, com a URL escrita ao lado, para uma busca no YouTube pelo salmo e pelo evangelho;
- links para sites oficiais;
- espaço para um comentário humano licenciado, quando houver.

O livro **não reproduz texto bíblico nem comentário de terceiros** e não contém texto gerado
por IA. Veja [docs/LICENCIAMENTO.md](docs/LICENCIAMENTO.md).

- Site: PREENCHER (endereço do GitHub Pages ou domínio próprio)
- Livros: aba *Releases* do repositório (uma release por ano, tag `livro-AAAA`)

## Rodar localmente

Requisitos: Python 3.11+ com [uv](https://docs.astral.sh/uv/) (ou pip), as bibliotecas do
sistema do WeasyPrint (Pango; no Ubuntu, `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0`),
Node 20.9+ para o site e, opcionalmente, o Calibre (`ebook-convert`) para gerar o AZW3.

```sh
make venv                         # cria .venv com as dependências fixadas por hash
make test                         # testes (calendário 2024-2060, dados, livro)
make validar                      # erros de dados/conteúdo e lacunas do ano atual
make validar ANO=2027 ANOS=3      # lacunas de vários anos
make calendario ANO=2026          # cada dia com as chaves do Lecionário e as leituras
make livro ANO=2026               # gera dist/2026/: PDF, EPUB, AZW3, calendário, manifest.json
make publicar-simulado            # regra de publicação e catalog.json, sem tocar no GitHub
make site                         # site estático em site/out
```

`ANO` é o ano civil do 1º Domingo do Advento: `ANO=2026` gera o ano litúrgico de 29/11/2026
a 27/11/2027 (ano B, ciclo ferial I).

## Como o build funciona

```
data/  (versionado)                     src/vitral/
├─ calendario/regras-brasil.yaml   ┐    ├─ liturgy/   calendário em Python puro: Páscoa, tempos,
├─ calendario/santos.yaml          ├──▶ │             precedência, transferências (NUALC)
├─ calendario/excecoes.yaml        ┘    ├─ lectionary.py  leituras de cada dia
├─ lecionario/*.yaml  (referências) ──▶ ├─ book/      HTML comum → PDF (WeasyPrint) e EPUB 3
├─ links.yaml                           ├─ build.py   um ano → dist/<ano>/
└─ fontes/  (cópias das fontes)         └─ validate.py  esquemas + lacunas
conteudo/*.md  (textos humanos)  ─────▶ entram no dia correspondente, se válidos
```

1. **Calendário.** `vitral.liturgy` calcula o ano litúrgico sem dependências: Páscoa pelo
   algoritmo de Meeus/Jones/Butcher, tempos, ciclos A/B/C e I/II, Tabela de Precedência e
   transferências, com as opções do Brasil em `data/calendario/regras-brasil.yaml`.
2. **Dados.** O próprio dos santos e as referências do Lecionário estão em `data/`, cada item
   com `status` (`verificado`, `fonte-unica` ou `pendente`) e a fonte. Origem e licenças:
   [docs/FONTES.md](docs/FONTES.md).
3. **Lacunas não quebram o build.** Leitura pendente aparece só com livro e capítulo. Dia sem
   leitura aparece só com os links. `make validar` lista tudo o que falta.
4. **Saídas reprodutíveis.** As mesmas entradas geram os mesmos bytes, porque a data dos
   arquivos é fixa (o 1º Domingo do Advento, ou `SOURCE_DATE_EPOCH`) e o zip do EPUB é
   ordenado.
5. **Publicação.** `.github/workflows/publicar.yml` roda todo dia e:
   - gera os anos que faltam ou que mudaram;
   - pré-gera os próximos 10 anos (variável `VITRAL_ANOS_A_FRENTE`) como pré-releases;
   - promove o ano Y a release normal quando faltam 30 dias para o Advento de Y;
   - monta o `catalog.json` e publica o site.

   O site só lê o `catalog.json`: se ele quebrar, os livros continuam nas Releases.

## Estrutura

| pasta | conteúdo |
|---|---|
| `src/vitral/` | código (calendário, dados, livro, validação) |
| `data/` | dados versionados; `data/fontes/` guarda cópias das fontes licenciadas |
| `schemas/` | JSON Schema dos arquivos de dados e do front matter de `conteudo/` |
| `conteudo/` | textos humanos licenciados (vazio de propósito; ver o README da pasta) |
| `livro/` | CSS e fontes (SIL OFL) do livro |
| `scripts/` | importadores únicos das fontes, cruzamento, publicação, verificação de links |
| `site/` | site Next.js estático |
| `docs/` | fontes, licenciamento, sucessão e relatórios de divergência |
| `tests/` | testes (pytest) |

## Documentos

- [CONTRIBUINDO.md](CONTRIBUINDO.md): como contribuir com dados, textos e código
- [docs/FONTES.md](docs/FONTES.md): procedência de cada dado
- [docs/LICENCIAMENTO.md](docs/LICENCIAMENTO.md): o que entra e o que não entra, e por quê
- [docs/SUCESSAO.md](docs/SUCESSAO.md): roteiro para outra pessoa assumir o projeto
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## Licenças

Código: [MIT](LICENSE). Conteúdo original e dados derivados: [CC BY-SA 4.0](LICENSE-CONTEUDO).
Fontes tipográficas: SIL Open Font License 1.1 (ver `livro/fontes/`). Textos de colaboradores:
a licença indicada em cada arquivo.
