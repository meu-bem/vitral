"""Verifica os links de data/links.yaml. Saída 1 se algum estiver quebrado.

Usado pelo workflow mensal, que abre uma issue com o relatório. Não altera nada.
"""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (compatible; VitralLinkCheck/1.0; +https://github.com)"


def check(url: str, tries: int = 3) -> tuple[bool, str]:
    last = ""
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status < 400, f"HTTP {resp.status}"
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code in (404, 410):
                break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = f"erro de rede: {exc}"
        time.sleep(5 * (attempt + 1))
    return False, last


def main() -> int:
    links = yaml.safe_load((ROOT / "data" / "links.yaml").read_text(encoding="utf-8"))["links"]
    broken = []
    for link in links:
        ok, info = check(link["url"])
        print(f"{'ok  ' if ok else 'FALHA'} {link['id']}: {link['url']} ({info})")
        if not ok:
            broken.append((link, info))
    report = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if report:
        lines = ["Links de `data/links.yaml` que falharam na verificação automática:", ""]
        lines += [f"- **{l['titulo']}** (`{l['id']}`): {l['url']} — {info}" for l, info in broken]
        lines += ["", "Confira à mão (pode ser instabilidade passageira) e, se o endereço mudou,",
                  "atualize `data/links.yaml` com o novo link e a data de verificação."]
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
