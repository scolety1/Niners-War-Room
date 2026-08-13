"""JSON-safe public contract helpers for the local desktop boundary."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "1.0.0"

_KEY_PARTS = re.compile(r"[^A-Za-z0-9]+")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
_WINDOWS_PATH_FRAGMENT = re.compile(r"(?:^|\s)[A-Za-z]:[\\/]")
_PATH_KEY_SUFFIXES = {"directory", "dir", "path", "root"}


def camel_case_key(value: object) -> str:
    """Convert service/data-frame keys to the desktop contract's camelCase."""

    text = str(value)
    if not any(separator in text for separator in ("_", "-", " ", "/")):
        return text[:1].lower() + text[1:]
    parts = [part for part in _KEY_PARTS.split(text) if part]
    if not parts:
        return "value"
    return parts[0].lower() + "".join(part[:1].upper() + part[1:].lower() for part in parts[1:])


def public_json_value(value: Any) -> Any:
    """Return a finite, path-free, JSON-serializable value with camelCase keys."""

    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Enum):
        return public_json_value(value.value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return None
    if isinstance(value, str):
        return _safe_public_string(value)
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if _is_path_key(key):
                continue
            output[camel_case_key(key)] = public_json_value(item)
        return output
    if isinstance(value, (list, tuple)):
        return [public_json_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [public_json_value(item) for item in sorted(value, key=str)]
    if hasattr(value, "item"):
        try:
            return public_json_value(value.item())
        except (TypeError, ValueError):
            pass
    if hasattr(value, "to_dict"):
        try:
            return public_json_value(value.to_dict("records"))
        except (TypeError, ValueError):
            try:
                return public_json_value(value.to_dict())
            except (TypeError, ValueError):
                pass
    return _safe_public_string(str(value))


def contract_envelope(
    mode: str,
    *,
    data: Any = None,
    warnings: tuple[str, ...] | list[str] = (),
    errors: tuple[dict[str, str], ...] | list[dict[str, str]] = (),
) -> dict[str, Any]:
    """Build the only top-level response shape exposed by the desktop API."""

    return {
        "contractVersion": CONTRACT_VERSION,
        "mode": mode,
        "data": public_json_value(data),
        "warnings": public_json_value(list(warnings)),
        "errors": public_json_value(list(errors)),
    }


def error_contract(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": _safe_public_string(message)}


def _is_path_key(value: object) -> bool:
    separated = _CAMEL_BOUNDARY.sub("_", str(value))
    tokens = [part.lower() for part in _KEY_PARTS.split(separated) if part]
    return bool(tokens and tokens[-1] in _PATH_KEY_SUFFIXES)


def _safe_public_string(value: str) -> str:
    text = value.replace("\x00", "").strip()
    if (
        _WINDOWS_ABSOLUTE_PATH.match(text)
        or _WINDOWS_PATH_FRAGMENT.search(text)
        or text.startswith(("/", "\\\\"))
    ):
        return "Unavailable"
    return text
