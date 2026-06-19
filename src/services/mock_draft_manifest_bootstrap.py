from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.services.mock_draft_input_contract import READINESS_GREEN, READINESS_RED

DEFAULT_LOCAL_MANIFEST_PATH = Path("local_exports/mock_draft/manual_input_manifest.local.json")
REQUIRED_BOOTSTRAP_ROLES = (
    "rookie_input",
    "veteran_pool",
    "pick_order",
    "my_picks",
    "rosters_keepers",
    "team_needs",
    "nwr_private_values",
    "market_context",
)


@dataclass(frozen=True)
class ManifestBootstrapReport:
    readiness: str
    destination: str
    manifest_json: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    dry_run: bool = True
    no_files_written: bool = True
    no_simulations_run: bool = True


def build_manifest_skeleton(
    *,
    destination: str | Path = DEFAULT_LOCAL_MANIFEST_PATH,
    roles: tuple[str, ...] = REQUIRED_BOOTSTRAP_ROLES,
) -> ManifestBootstrapReport:
    path = Path(destination)
    errors = _validate_roles(roles) + _validate_destination(path)
    payload = {
        "version": 1,
        "review_only": True,
        "dry_run_template": True,
        "no_simulations_run": True,
        "inputs": {
            role: {
                "role": role,
                "path": "",
                "source_note": "",
                "manual_review_note": "",
            }
            for role in roles
        },
    }
    return ManifestBootstrapReport(
        readiness=READINESS_RED if errors else READINESS_GREEN,
        destination=str(path).replace("\\", "/"),
        manifest_json=json.dumps(payload, indent=2),
        errors=tuple(errors),
        warnings=(
            "Dry run only. Real manifest files stay local-only and uncommitted.",
        ),
    )


def is_local_only_manifest_path(path: str | Path) -> bool:
    normalized = Path(path).as_posix().lower()
    return normalized.startswith("local_exports/mock_draft/") and normalized.endswith(
        ".local.json"
    )


def _validate_roles(roles: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    missing = sorted(set(REQUIRED_BOOTSTRAP_ROLES) - set(roles))
    extra = sorted(set(roles) - set(REQUIRED_BOOTSTRAP_ROLES))
    if missing:
        errors.append(f"Missing manifest roles: {', '.join(missing)}.")
    if extra:
        errors.append(f"Unknown manifest roles: {', '.join(extra)}.")
    if "nwr_private_values" in roles and "market_context" in roles:
        return errors
    errors.append("NWR private value and market context roles must stay separate.")
    return errors


def _validate_destination(path: Path) -> list[str]:
    if is_local_only_manifest_path(path):
        return []
    return [f"Manifest destination is not an approved local-only path: {path}."]
