"""Publica os livros como GitHub Releases e monta o catalog.json. Usado por .github/workflows/publicar.yml.

Regras (idempotentes; rodar duas vezes não muda nada):
- anos-alvo: o ano litúrgico atual e os próximos N (pré-geração, defesa contra o
  agendamento desativado do GitHub);
- o ano Y fica como **pré-release** até faltarem 30 dias ou menos para o Advento de Y;
  daí vira release normal ("publicado");
- um ano só é reconstruído se a impressão digital das entradas (dados, código, estilo,
  dependências) mudou desde a release existente;
- ``--ano Y`` força só aquele ano.

Requer o ``gh`` autenticado (GH_TOKEN) e o repositório em GITHUB_REPOSITORY.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vitral.build import build  # noqa: E402
from vitral.liturgy import first_sunday_of_advent  # noqa: E402
from vitral.validate import current_liturgical_year  # noqa: E402

INPUTS = ["data", "livro", "src", "conteudo", "requirements.txt"]
PUBLISH_WINDOW_DAYS = 30
FIRST_YEAR = 2026  # primeiro ano litúrgico publicado pelo projeto


def gh(*args: str, check: bool = True) -> str:
    res = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}: {res.stderr.strip()}")
    return res.stdout if res.returncode == 0 else ""


def input_fingerprint() -> str:
    h = hashlib.sha256()
    for top in INPUTS:
        p = ROOT / top
        files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file() and "__pycache__" not in x.parts)
        for f in files:
            h.update(str(f.relative_to(ROOT)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def is_published(year: int, today: date) -> bool:
    return (first_sunday_of_advent(year) - today).days <= PUBLISH_WINDOW_DAYS


def release_info(tag: str) -> dict | None:
    out = gh("release", "view", tag, "--json", "tagName,isPrerelease,assets", check=False)
    return json.loads(out) if out else None


def release_manifest(tag: str) -> dict | None:
    with tempfile.TemporaryDirectory() as tmp:
        gh("release", "download", tag, "-p", "manifest.json", "-D", tmp, check=False)
        f = Path(tmp) / "manifest.json"
        return json.loads(f.read_text()) if f.exists() else None


def notes(manifest: dict, published: bool) -> str:
    state = "Publicado." if published else (
        "Pré-gerado. Vira publicação oficial quando faltarem 30 dias para o Advento.")
    return (f"{manifest['titulo']} — ano {manifest['ciclo_dominical']}, ciclo ferial {manifest['ciclo_ferial']}.\n\n"
            f"{state}\n\nDe {manifest['inicio']} a {manifest['fim']} ({manifest['dias']} dias). "
            f"Dias com algum dado ainda pendente: {manifest['dias_com_lacuna']} "
            f"(aparecem só com o que foi verificado).\n\n"
            "Formatos: PDF (A5), EPUB (para Kindle, via Enviar para o Kindle) e AZW3 (quando gerado).")


def process_year(year: int, today: date, out_dir: Path, fingerprint: str, force: bool, dry: bool) -> dict | None:
    tag = f"livro-{year}"
    published = is_published(year, today)
    info = release_info(tag)
    old = release_manifest(tag) if info else None
    if info and old and old.get("entrada_sha256") == fingerprint and not force:
        if info["isPrerelease"] == (not published):
            print(f"{tag}: em dia")
            return old
        print(f"{tag}: só muda o estado (publicado={published})")
        if not dry:
            gh("release", "edit", tag, f"--prerelease={'false' if published else 'true'}",
               "--notes", notes(old, published))
        return old

    print(f"{tag}: gerando")
    manifest = build(year, out_dir)
    manifest["entrada_sha256"] = fingerprint
    manifest["tag"] = tag
    ydir = out_dir / str(year)
    (ydir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assets = [str(ydir / v["arquivo"]) for v in manifest["formatos"].values()]
    assets += [str(ydir / v["arquivo"]) for v in manifest["calendario"].values()]
    assets.append(str(ydir / "manifest.json"))
    if dry:
        return manifest
    flags = ["--prerelease"] if not published else []
    if info:
        gh("release", "upload", tag, *assets, "--clobber")
        gh("release", "edit", tag, f"--prerelease={'false' if published else 'true'}",
           "--notes", notes(manifest, published))
    else:
        gh("release", "create", tag, *assets, "--title", manifest["titulo"], "--notes",
           notes(manifest, published), *flags)
    return manifest


def catalog(manifests: list[dict], repo: str, today: date) -> dict:
    years = []
    for m in sorted(manifests, key=lambda m: m["ano_liturgico"]):
        tag = m.get("tag", f"livro-{m['ano_liturgico']}")
        base = f"https://github.com/{repo}/releases/download/{tag}/"
        years.append({
            "ano": m["ano_liturgico"],
            "titulo": m["titulo"],
            "publicado": is_published(m["ano_liturgico"], today),
            "inicio": m["inicio"], "fim": m["fim"],
            "ciclo_dominical": m["ciclo_dominical"], "ciclo_ferial": m["ciclo_ferial"],
            "dias_com_lacuna": m["dias_com_lacuna"],
            "release": f"https://github.com/{repo}/releases/tag/{tag}",
            "formatos": {k: {**v, "url": base + v["arquivo"]} for k, v in m["formatos"].items()},
            "calendario": {k: {**v, "url": base + v["arquivo"]} for k, v in m["calendario"].items()},
        })
    return {"versao": 1, "gerado_em": today.isoformat(), "repositorio": repo, "anos": years}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Publica os livros e o catalog.json.")
    ap.add_argument("--ano", type=int, help="só este ano litúrgico (força a geração)")
    ap.add_argument("--anos-a-frente", type=int, default=int(os.environ.get("VITRAL_ANOS_A_FRENTE", "10")))
    ap.add_argument("--saida", type=Path, default=ROOT / "dist")
    ap.add_argument("--hoje", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--simular", action="store_true", help="não fala com o GitHub")
    args = ap.parse_args(argv)
    repo = os.environ.get("GITHUB_REPOSITORY", "PREENCHER/vitral")
    fingerprint = input_fingerprint()
    current = current_liturgical_year(args.hoje)
    years = [args.ano] if args.ano else list(range(current, current + args.anos_a_frente + 1))
    manifests = []
    for y in years:
        m = process_year(y, args.hoje, args.saida, fingerprint, bool(args.ano), args.simular)
        if m:
            manifests.append(m)
    if not args.simular:  # o catálogo lista todos os anos com release, inclusive os passados
        done = {m["ano_liturgico"] for m in manifests}
        for y in range(FIRST_YEAR, current + args.anos_a_frente + 1):
            if y not in done and (m := release_manifest(f"livro-{y}")):
                manifests.append(m)
    cat = catalog(manifests, repo, args.hoje)
    args.saida.mkdir(parents=True, exist_ok=True)
    path = args.saida / "catalog.json"
    path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.simular:
        for m in manifests:
            gh("release", "upload", m.get("tag", f"livro-{m['ano_liturgico']}"), str(path), "--clobber")
    print(f"catalog.json: {len(cat['anos'])} ano(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
