from __future__ import annotations

import json
from pathlib import Path

from src.services.mock_draft_input_manifest import validate_input_manifest

FIXTURE_MANIFEST = Path("tests/fixtures/mock_draft_inputs/input_manifest_fixture.json")


def test_missing_manifest_returns_yellow() -> None:
    report = validate_input_manifest("local_exports/mock_draft/missing_manifest.local.json")

    assert report.readiness == "YELLOW"
    assert report.manifest_present is False
    assert report.no_simulations_run is True


def test_fixture_manifest_validates_green() -> None:
    report = validate_input_manifest(FIXTURE_MANIFEST)

    assert report.readiness == "GREEN"
    assert report.input_report is not None
    assert report.input_report.readiness == "GREEN"


def test_malformed_manifest_returns_red(tmp_path: Path) -> None:
    manifest = tmp_path / "bad.json"
    manifest.write_text("{not-json", encoding="utf-8")

    report = validate_input_manifest(manifest)

    assert report.readiness == "RED"


def test_adversarial_malformed_manifest_fixture_returns_red() -> None:
    manifest = Path("tests/fixtures/mock_draft_inputs/adversarial/malformed_manifest.json")

    report = validate_input_manifest(manifest)

    assert report.readiness == "RED"


def test_manifest_rejects_market_context_as_private_value(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    payload["inputs"]["nwr_private_values"]["path"] = (
        "tests/fixtures/mock_draft_inputs/market_context_fixture.csv"
    )
    manifest = tmp_path / "swapped.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    report = validate_input_manifest(manifest)

    assert report.readiness == "RED"


def test_manifest_rejects_private_value_as_market_context(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    payload["inputs"]["market_context"]["path"] = (
        "tests/fixtures/mock_draft_inputs/nwr_private_values_fixture.csv"
    )
    manifest = tmp_path / "swapped.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    report = validate_input_manifest(manifest)

    assert report.readiness == "RED"
