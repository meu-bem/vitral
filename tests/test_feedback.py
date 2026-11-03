"""Link de sugestão de correção da tradução."""

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from vitral.feedback import correction_url

ROOT = Path(__file__).resolve().parents[1]


def test_correction_url_prefills_ref():
    url = urlparse(correction_url("Sl 121(122),1-2"))
    query = parse_qs(url.query)
    assert url.path.endswith("/issues/new")
    assert query["template"] == ["correcao-traducao.yml"]
    assert query["passagem"] == ["Sl 121(122),1-2"]
    assert query["title"] == ["[Tradução] Sl 121(122),1-2"]


def test_template_has_the_prefilled_field():
    form = yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE/correcao-traducao.yml").read_text(encoding="utf8"))
    ids = {item.get("id") for item in form["body"]}
    assert "passagem" in ids
