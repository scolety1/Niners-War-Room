from __future__ import annotations

import hashlib
import json
from typing import Any


def fingerprint_rows(
    source_family: str,
    rows: list[dict[str, Any]],
    *,
    required_fields: set[str] | None = None,
    source_version: str = "",
) -> dict[str, Any]:
    columns = _columns(rows)
    required = sorted(required_fields or set())
    payload = {
        "source_family": source_family,
        "columns": columns,
        "dtypes": {column: _dtype(rows, column) for column in columns},
        "required_fields_present": {field: field in columns for field in required},
        "source_version": source_version,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["schema_fingerprint"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return payload


def schema_changed(old: dict[str, Any], new: dict[str, Any]) -> bool:
    return old.get("schema_fingerprint") != new.get("schema_fingerprint")


def fingerprint_registry_row(fingerprint: dict[str, Any]) -> dict[str, str]:
    return {
        "source_family": str(fingerprint["source_family"]),
        "schema_fingerprint": str(fingerprint["schema_fingerprint"]),
        "field_count": str(len(fingerprint["columns"])),
        "columns": "|".join(fingerprint["columns"]),
        "source_version": str(fingerprint.get("source_version", "")),
        "model_input_allowed": "no",
        "app_wiring_allowed": "no",
    }


def _columns(rows: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    columns: list[str] = []
    for row in rows:
        for key in row:
            field = str(key)
            if field not in seen:
                columns.append(field)
                seen.add(field)
    return sorted(columns)


def _dtype(rows: list[dict[str, Any]], column: str) -> str:
    values = [row.get(column) for row in rows if row.get(column) not in ("", None)]
    if not values:
        return "empty"
    if all(isinstance(value, bool) for value in values):
        return "bool"
    if all(_is_int(value) for value in values):
        return "int"
    if all(_is_float(value) for value in values):
        return "float"
    return "str"


def _is_int(value: Any) -> bool:
    try:
        return str(int(value)) == str(value)
    except (TypeError, ValueError):
        return False


def _is_float(value: Any) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True
