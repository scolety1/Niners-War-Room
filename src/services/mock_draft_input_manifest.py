from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.services.mock_draft_input_contract import (
    INPUT_SCHEMAS,
    READINESS_GREEN,
    READINESS_RED,
    READINESS_YELLOW,
    InputContractReport,
    validate_input_contract,
)


@dataclass(frozen=True)
class ManifestReport:
    readiness: str
    manifest_present: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    input_report: InputContractReport | None = None
    no_simulations_run: bool = True


def validate_input_manifest(
    manifest_path: str | Path,
    *,
    repo_root: str | Path = ".",
) -> ManifestReport:
    path = Path(manifest_path)
    root = Path(repo_root)
    full_path = path if path.is_absolute() else root / path
    if not full_path.exists():
        return ManifestReport(
            readiness=READINESS_YELLOW,
            manifest_present=False,
            errors=(),
            warnings=(f"Manifest not found: {path}",),
        )
    try:
        payload = json.loads(full_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ManifestReport(
            readiness=READINESS_RED,
            manifest_present=True,
            errors=(f"Manifest is malformed: {exc}",),
            warnings=(),
        )
    inputs = payload.get("inputs")
    if not isinstance(inputs, dict):
        return ManifestReport(
            readiness=READINESS_RED,
            manifest_present=True,
            errors=("Manifest missing inputs object.",),
            warnings=(),
        )
    errors: list[str] = []
    paths_by_key: dict[str, Path | None] = {}
    for key in INPUT_SCHEMAS:
        entry = inputs.get(key)
        if not isinstance(entry, dict):
            errors.append(f"Manifest missing role: {key}.")
            paths_by_key[key] = None
            continue
        if entry.get("role") != key:
            errors.append(f"Manifest role mismatch for {key}.")
        paths_by_key[key] = Path(str(entry.get("path") or ""))
    if errors:
        return ManifestReport(
            readiness=READINESS_RED,
            manifest_present=True,
            errors=tuple(errors),
            warnings=(),
        )
    input_report = validate_input_contract(paths_by_key, mode="fixture", repo_root=root)
    return ManifestReport(
        readiness=READINESS_RED if input_report.readiness == READINESS_RED else READINESS_GREEN,
        manifest_present=True,
        errors=(),
        warnings=(),
        input_report=input_report,
    )
