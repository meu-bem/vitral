"""Envia os livros publicados ao Internet Archive (opcional, desligado por padrão).

Liga-se com a variável de repositório ARQUIVAR_INTERNET_ARCHIVE=true, os segredos
IA_ACCESS_KEY / IA_SECRET_KEY (https://archive.org/account/s3.php) e a variável
IA_PREFIXO (prefixo único dos itens, ex.: "vitral-livro"). Idempotente: item que já
existe no Internet Archive não é reenviado. Ver docs/SUCESSAO.md.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


def item_exists(identifier: str) -> bool:
    with urllib.request.urlopen(f"https://archive.org/metadata/{identifier}", timeout=60) as r:
        return bool(json.load(r).get("files"))


def upload(identifier: str, path: Path, meta: dict[str, str], first: bool) -> None:
    headers = {
        "authorization": f"LOW {os.environ['IA_ACCESS_KEY']}:{os.environ['IA_SECRET_KEY']}",
        "x-archive-queue-derive": "0",
    }
    if first:
        headers["x-archive-auto-make-bucket"] = "1"
        headers.update({f"x-archive-meta-{k}": v for k, v in meta.items()})
    req = urllib.request.Request(f"https://s3.us.archive.org/{identifier}/{path.name}",
                                 data=path.read_bytes(), method="PUT", headers=headers)
    with urllib.request.urlopen(req, timeout=600) as r:
        print(f"  {path.name}: HTTP {r.status}")


def main() -> int:
    prefix = os.environ.get("IA_PREFIXO")
    if not prefix or not os.environ.get("IA_ACCESS_KEY"):
        print("IA_PREFIXO ou segredos ausentes: nada a fazer")
        return 0
    releases = json.loads(subprocess.run(
        ["gh", "release", "list", "--json", "tagName,isPrerelease", "--limit", "100"],
        check=True, capture_output=True, text=True).stdout)
    for rel in releases:
        if rel["isPrerelease"] or not rel["tagName"].startswith("livro-"):
            continue
        year = rel["tagName"].split("-", 1)[1]
        identifier = f"{prefix}-{year}"
        if item_exists(identifier):
            print(f"{identifier}: já arquivado")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["gh", "release", "download", rel["tagName"], "-D", tmp], check=True)
            meta = {"title": f"Vitral {year}", "mediatype": "texts", "language": "por",
                    "licenseurl": "https://creativecommons.org/licenses/by-sa/4.0/"}
            print(identifier)
            for i, f in enumerate(sorted(Path(tmp).iterdir())):
                upload(identifier, f, meta, first=i == 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
