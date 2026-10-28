"""Fase 2: esquemas, validador de dados e de conteúdo humano."""

from pathlib import Path

import pytest

from vitral.content import check_content
from vitral.schema import validate
from vitral.validate import check_data

FIX = Path(__file__).parent / "fixtures"
KEYS = {"B.advento-1.domingo", "advento-1.segunda"}


def test_repository_data_has_no_errors():
    assert check_data() == []


def test_schema_subset():
    schema = {
        "type": "object", "required": ["a"], "additionalProperties": False,
        "properties": {"a": {"enum": ["x", "y"]}, "b": {"type": "array", "items": {"type": "integer"}}},
    }
    assert validate({"a": "x", "b": [1, 2]}, schema) == []
    assert validate({"b": [1]}, schema) == ["$: campo obrigatório ausente: a"]
    assert validate({"a": "z"}, schema)[0].startswith("$.a: valor 'z' fora")
    assert validate({"a": "x", "c": 1}, schema) == ["$: campo não permitido: c"]
    assert validate({"a": "x", "b": [True]}, schema)  # bool não é inteiro


def test_valid_content_is_accepted():
    items, errors = check_content(FIX / "conteudo-valido", KEYS)
    assert errors == [] and len(items) == 1
    assert items[0].day_key == "B.advento-1.domingo"


@pytest.mark.parametrize("name, fragment", [
    ("sem-licenca.md", "campo obrigatório ausente: licenca"),
    ("licenca-proibida.md", "fora de"),
    ("nc.md", "fora de"),
    ("dominio-publico-sem-fonte.md", "domínio público exige 'fonte'"),
    ("dia-inexistente.md", "não existe no calendário"),
])
def test_invalid_content_is_rejected(name, fragment):
    _, errors = check_content(FIX / "conteudo-invalido", KEYS)
    assert any(name in e and fragment in e for e in errors), errors


def test_repository_content_folder_is_valid():
    from vitral.validate import all_day_keys
    _, errors = check_content(known_keys=all_day_keys(2024, 2027))
    assert errors == []
