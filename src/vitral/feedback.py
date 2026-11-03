"""Link para sugerir correção de uma passagem, já com a referência preenchida."""

from urllib.parse import urlencode

__all__ = ["REPO_URL", "correction_url"]

REPO_URL = "https://github.com/meu-bem/vitral"
_TEMPLATE = "correcao-traducao.yml"


def correction_url(ref: str) -> str:
    """URL do formulário de correção com o campo ``passagem`` e o título preenchidos."""
    query = urlencode({"template": _TEMPLATE, "title": f"[Tradução] {ref}", "passagem": ref})
    return f"{REPO_URL}/issues/new?{query}"
