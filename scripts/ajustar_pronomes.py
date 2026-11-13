"""Modernizar pronomes em data/biblia/: mesóclise vira próclise e as contrações (vo-lo, lho...) se desfazem.

Uso: python scripts/ajustar_pronomes.py            # mostra o antes e o depois
     python scripts/ajustar_pronomes.py --gravar   # grava em data/biblia/

Mesóclise ("dar-te-ei", "guardá-la-á", "tornar-se-á") passa a próclise ("te darei", "a guardará", "se tornará").
Formas de 1ª e 2ª pessoa que abririam a frase ganham o sujeito ("Dar-te-ei" -> "Eu te darei"); as de 3ª pessoa
e o condicional que abririam a frase ficam em mesóclise, que ali é a forma correta. As contrações são
desfeitas à mão na tabela ``CONTRACOES`` (cada uma depende do sentido). Rodar de novo não muda nada.
"""

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

MESOCLISE = re.compile(
    r"(?<![\w-])([^\W\d_]+)-(lo|la|los|las|se|me|te|nos|vos|lhe|lhes)-(á|ás|ão|ei|emos|eis|ia|iam|íeis|íamos)(?![\w-])",
    re.IGNORECASE)
SUJEITO = {"ei": "Eu", "ás": "Tu", "emos": "Nós", "eis": "Vós"}
# Abre frase: depois de . ! ? ou de aspas de abertura. Depois de ; ou : a frase continua (próclise normal).
INICIO_DE_FRASE = re.compile(r"(?:^|[.!?][”’)\"']*\s+)[“‘(\"']*$|[“‘]$")
RESTAURA = {"á": "ar", "ê": "er", "i": "ir"}  # "guardá-la" = guardar+a; "enchê-lo" = encher+o; "reuni-las" = reunir+as


def _verbo(raiz: str, final: str) -> str:
    base = raiz[:-1] + RESTAURA[raiz[-1]] if raiz[-1] in RESTAURA else raiz
    return base + final


def desfazer_mesoclise(text: str, antes: str = "") -> str:
    """Converte as mesóclises de ``text``. ``antes`` é o texto que vem antes (partes anteriores do versículo)."""
    def troca(m: re.Match) -> str:
        raiz, pron, final = m.groups()
        contexto = antes + text[:m.start()]
        if contexto.strip():
            inicio = bool(INICIO_DE_FRASE.search(contexto))
        else:  # começo do versículo: só abre frase se começa com maiúscula (minúscula = continuação)
            inicio = text[:1].isupper()
        sujeito = SUJEITO.get(final.lower())
        if inicio and not sujeito:
            return m.group(0)  # 3ª pessoa ou condicional abrindo a frase: fica em mesóclise
        pron = {"lo": "o", "la": "a", "los": "os", "las": "as"}.get(pron.lower(), pron.lower())
        verbo = _verbo(raiz.lower(), final.lower())
        if inicio:
            return f"{sujeito} {pron} {verbo}"
        return f"{pron} {verbo}"
    return MESOCLISE.sub(troca, text)


# (livro, "cap:vers") -> [(antes, depois)]. Cada troca desfaz a contração pelo sentido (lho = lhe + o).
CONTRACOES = {
    ("1CO", "11:2"): [("como vo-las transmiti", "como eu as transmiti a vós")],
    ("1CO", "15:2"): [("tal como vo-lo anunciei", "tal como eu o anunciei a vós")],
    ("2SA", "16:11"): [("pois o Senhor lho disse", "pois o Senhor lhe disse isso")],
    ("ACT", "13:41"): [("se alguém vo-la contar", "se alguém a contar a vós")],
    ("JHN", "10:25"): [("Eu vo-lo disse, e não credes", "Eu vos disse, e não credes")],
    ("JHN", "11:22"): [("Deus to concederá", "Deus te concederá")],
    ("JHN", "13:19"): [("Desde agora vo-lo digo", "Desde agora vos digo isto")],
    ("JHN", "14:29"): [("E agora vo-lo disse", "E agora vos disse isto")],
    ("JHN", "15:16"): [("ele vo-lo conceda", "ele vos conceda")],
    ("JHN", "16:4"): [("que eu vo-lo disse", "que eu vos disse isso")],
    ("JHN", "16:7"): [("se eu for, vo-lo enviarei", "se eu for, eu o enviarei a vós")],
    ("JHN", "16:14"): [("e vo-lo anunciará", "e o anunciará a vós")],
    ("JHN", "16:15"): [("e vo-lo anunciará", "e o anunciará a vós")],
    ("JHN", "16:23"): [("ele vo-lo dará em meu nome", "ele o dará a vós em meu nome")],
    ("JHN", "19:4"): [("Eis que vo-lo trago fora", "Eis que o trago para fora, a vós")],
    ("JHN", "21:13"): [("toma o pão e lho dá", "toma o pão e o dá a eles")],
    ("JON", "1:10"): [("porque ele lho dissera", "porque ele lhes dissera isso")],
    ("LUK", "1:2"): [("conforme no-los transmitiram", "conforme os transmitiram a nós")],
    ("LUK", "11:13"): [("aos que lho pedem", "aos que o pedem a ele")],
    ("LUK", "18:40"): [("mandou que lho trouxessem", "mandou que o trouxessem a ele")],
    ("MAT", "6:8"): [("antes que lho peçais", "antes que o peçais a ele")],
    ("MAT", "7:11"): [("aos que lho pedem", "aos que o pedem a ele")],
    ("MAT", "16:17"): [("que to revelaram", "que te revelaram isso")],
    ("MAT", "26:15"): [("eu vo-lo entregarei", "eu o entregarei a vós")],
    ("MRK", "14:10"): [("para lho entregar", "para entregá-lo a eles")],
    ("PSA", "50:12"): [("não to diria", "não te diria isso")],
    ("ROM", "1:19"): [("Deus lho manifestou", "Deus o manifestou a eles")],
    ("TOB", "7:14"): [("de que ta entregarei", "de que a entregarei a ti")],
}


def _trocas(entry: dict, pairs: list[tuple[str, str]]) -> bool:
    """Aplica as trocas ao texto e às partes. Falso se alguma não encontrou o trecho (e a contração já foi desfeita)."""
    applied = True
    for old, new in pairs:
        if old in entry["texto"]:
            entry["texto"] = entry["texto"].replace(old, new)
        else:
            applied = applied and new in entry["texto"]
        if "partes" in entry:
            entry["partes"] = [p.replace(old, new) for p in entry["partes"]]
    return applied


def processar(doc: dict, mostrar: bool) -> int:
    n = 0
    for key, entry in doc["versiculos"].items():
        old = entry["texto"]
        if not _trocas(entry, CONTRACOES.get((doc["livro"], key), [])):
            print(f"ATENÇÃO: troca de contração não aplicada em {doc['livro']} {key}")
        entry["texto"] = desfazer_mesoclise(entry["texto"])
        if "partes" in entry:
            done = ""
            novas = []
            for p in entry["partes"]:
                novas.append(desfazer_mesoclise(p, done))
                done += p + " "
            entry["partes"] = novas
        if entry["texto"] != old:
            n += 1
            if mostrar:
                print(f"{doc['livro']} {key}\n   - {old}\n   + {entry['texto']}")
    return n


def main(write: bool) -> None:
    total = 0
    for path in sorted((ROOT / "data" / "biblia").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf8"))
        n = processar(doc, mostrar=not write)
        if n and write:
            path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf8")
        total += n
    print(f"{total} versículos {'alterados' if write else 'a alterar'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    main(ap.parse_args().gravar)
