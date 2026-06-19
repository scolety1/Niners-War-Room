from __future__ import annotations

import json
from pathlib import Path

from src.services.mock_draft_manifest_bootstrap import (
    REQUIRED_BOOTSTRAP_ROLES,
    build_manifest_skeleton,
    is_local_only_manifest_path,
)


def test_skeleton_includes_all_required_roles() -> None:
    report = build_manifest_skeleton()
    payload = json.loads(report.manifest_json)

    assert report.readiness == "GREEN"
    assert tuple(payload["inputs"]) == REQUIRED_BOOTSTRAP_ROLES
    assert payload["review_only"] is True


def test_default_behavior_writes_no_files(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())

    report = build_manifest_skeleton(destination=tmp_path / "manifest.local.json")

    assert report.no_files_written is True
    assert set(tmp_path.iterdir()) == before


def test_local_exports_mock_draft_destination_is_local_only() -> None:
    assert is_local_only_manifest_path(
        "local_exports/mock_draft/manual_input_manifest.local.json"
    )


def test_destination_outside_local_only_area_is_rejected() -> None:
    report = build_manifest_skeleton(destination="docs/hq/manifest.json")

    assert report.readiness == "RED"
    assert report.errors


def test_market_and_private_roles_stay_separate() -> None:
    report = build_manifest_skeleton()
    payload = json.loads(report.manifest_json)

    assert payload["inputs"]["market_context"]["role"] == "market_context"
    assert payload["inputs"]["nwr_private_values"]["role"] == "nwr_private_values"
