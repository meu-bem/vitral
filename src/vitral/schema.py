"""Validador mínimo de JSON Schema (subconjunto usado em ``schemas/``), sem dependências.

Suporta: type, enum, const, pattern, required, properties, additionalProperties,
patternProperties, items, minItems, minLength, minimum, maximum, anyOf, $ref local ($defs).
Os arquivos de ``schemas/`` são JSON Schema padrão: editores também conseguem usá-los.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

__all__ = ["validate", "load_schema"]

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(data: Any, schema: dict, root: dict | None = None, path: str = "$") -> list[str]:
    """Retorna a lista de erros (vazia se válido)."""
    root = root or schema
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"$ref não suportado: {ref}")
        return validate(data, root["$defs"][ref.split("/")[-1]], root, path)
    errors: list[str] = []
    if "anyOf" in schema:
        options = [validate(data, s, root, path) for s in schema["anyOf"]]
        if all(options):
            errors.append(f"{path}: não corresponde a nenhuma das opções ({options[0][0]})")
        return errors
    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        ok = any(
            isinstance(data, _TYPES[x]) and not (x in ("integer", "number") and isinstance(data, bool))
            for x in types
        )
        if not ok:
            return [f"{path}: esperado {t}, veio {type(data).__name__}"]
    if "const" in schema and data != schema["const"]:
        errors.append(f"{path}: esperado {schema['const']!r}")
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path}: valor {data!r} fora de {schema['enum']}")
    if isinstance(data, str):
        if "pattern" in schema and not re.search(schema["pattern"], data):
            errors.append(f"{path}: {data!r} não segue o padrão {schema['pattern']}")
        if len(data) < schema.get("minLength", 0):
            errors.append(f"{path}: texto vazio ou curto demais")
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"{path}: {data} < {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"{path}: {data} > {schema['maximum']}")
    if isinstance(data, list):
        if len(data) < schema.get("minItems", 0):
            errors.append(f"{path}: precisa de pelo menos {schema['minItems']} item(ns)")
        if "items" in schema:
            for i, item in enumerate(data):
                errors += validate(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(data, dict):
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{path}: campo obrigatório ausente: {key}")
        props = schema.get("properties", {})
        patterns = schema.get("patternProperties", {})
        extra = schema.get("additionalProperties", True)
        for key, value in data.items():
            sub = f"{path}.{key}"
            if key in props:
                errors += validate(value, props[key], root, sub)
                continue
            matched = [s for p, s in patterns.items() if re.search(p, str(key))]
            for s in matched:
                errors += validate(value, s, root, sub)
            if matched:
                continue
            if extra is False:
                errors.append(f"{path}: campo não permitido: {key}")
            elif isinstance(extra, dict):
                errors += validate(value, extra, root, sub)
    return errors
