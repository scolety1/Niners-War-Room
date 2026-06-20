from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from src.services.mock_draft_input_contract import (
    READINESS_GREEN,
    READINESS_RED,
    READINESS_YELLOW,
)
from src.services.mock_draft_lane_exchange_validator import (
    MANUAL_REVIEW_USE,
    OPTIONAL_PACKAGES,
    PRIVATE_VALUE_FORBIDDEN,
    READ_ONLY_USE,
    REQUIRED_PACKAGES,
    validate_lane_exchange_readiness,
)


def test_all_required_packages_validate_green_with_optional_market_missing(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    for package_name in REQUIRED_PACKAGES:
        _write_package(hub, package_name)

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    assert report.readiness == READINESS_GREEN
    assert _package(report, "market_behavior/display_only_market_context").readiness == (
        READINESS_YELLOW
    )
    assert report.no_simulations_run is True
    assert report.no_files_written is True


def test_required_package_missing_latest_approved_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    for package_name in REQUIRED_PACKAGES[1:]:
        _write_package(hub, package_name)

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    assert report.readiness == READINESS_RED
    missing = _package(report, "rookie_hq/frozen_rookie_mock_input")
    assert missing.readiness == READINESS_RED
    assert "latest_approved.json not found" in missing.errors[0]


def test_latest_candidate_is_not_accepted_for_required_package(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    package_root = hub / "rookie_hq" / "frozen_rookie_mock_input"
    package_root.mkdir(parents=True)
    (package_root / "latest_candidate.json").write_text("{}", encoding="utf-8")
    for package_name in REQUIRED_PACKAGES[1:]:
        _write_package(hub, package_name)

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    candidate_only = _package(report, "rookie_hq/frozen_rookie_mock_input")
    assert report.readiness == READINESS_RED
    assert "latest_candidate exists but is not accepted" in candidate_only.errors[0]


def test_unapproved_manifest_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    _write_all_required(hub)
    _write_package(
        hub,
        "league_state/pick_order",
        manifest_overrides={"approval_status": "candidate"},
    )

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    pick_order = _package(report, "league_state/pick_order")
    assert report.readiness == READINESS_RED
    assert "approval_status must be approved" in " ".join(pick_order.errors)


def test_hash_mismatch_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    _write_all_required(hub)
    _write_package(
        hub,
        "drop_decision/dropped_veterans",
        manifest_overrides={"sha256": "0" * 64},
    )

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    dropped = _package(report, "drop_decision/dropped_veterans")
    assert report.readiness == READINESS_RED
    assert "sha256" in " ".join(dropped.errors)


def test_row_count_mismatch_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    _write_all_required(hub)
    _write_package(
        hub,
        "league_state/nwr_picks",
        manifest_overrides={"row_count": 99},
    )

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    nwr_picks = _package(report, "league_state/nwr_picks")
    assert report.readiness == READINESS_RED
    assert "row_count mismatch" in " ".join(nwr_picks.errors)


def test_non_market_package_with_adp_fails_private_market_contamination(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    _write_all_required(hub)
    _write_package(
        hub,
        "model_value/veteran_private_values",
        manifest_overrides={"contains_adp": True},
    )

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    private_values = _package(report, "model_value/veteran_private_values")
    assert report.readiness == READINESS_RED
    assert "market/ADP" in " ".join(private_values.errors)


def test_optional_market_package_must_be_display_only(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    _write_all_required(hub)
    _write_package(
        hub,
        "market_behavior/display_only_market_context",
        manifest_overrides={
            "contains_private_value": True,
            "forbidden_use": [],
        },
    )

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    market = _package(report, "market_behavior/display_only_market_context")
    assert report.readiness == READINESS_RED
    assert "private value" in " ".join(market.errors)


def test_registry_missing_mock_draft_package_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(
        tmp_path,
        consumer_packages=REQUIRED_PACKAGES[:-1],
    )
    _write_all_required(hub)

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    assert report.readiness == READINESS_RED
    assert "Registry missing Mock Draft consumer package" in " ".join(report.errors)


def test_malformed_latest_approved_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hub, registry = _exchange_fixture(tmp_path)
    _write_all_required(hub)
    package_root = hub / "league_state" / "pick_order"
    (package_root / "latest_approved.json").write_text("{bad json", encoding="utf-8")

    report = validate_lane_exchange_readiness(hub_root=hub, registry_path=registry)

    pick_order = _package(report, "league_state/pick_order")
    assert report.readiness == READINESS_RED
    assert "malformed" in " ".join(pick_order.errors)


def _exchange_fixture(
    tmp_path: Path,
    *,
    consumer_packages: tuple[str, ...] = (*REQUIRED_PACKAGES, *OPTIONAL_PACKAGES),
) -> tuple[Path, Path]:
    hub = tmp_path / "lane_exchange"
    registry = tmp_path / "lane_exchange_registry" / "lane_exchange_v0_registry.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "contract_version": "lane_exchange_v0",
                "hub_root": str(hub),
                "local_only": True,
                "lane_ownership": [
                    {
                        "source_lane": "mock_draft",
                        "consumer_packages": list(consumer_packages),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return hub, registry


def _write_all_required(hub: Path) -> None:
    for package_name in REQUIRED_PACKAGES:
        _write_package(hub, package_name)


def _write_package(
    hub: Path,
    package_name: str,
    *,
    manifest_overrides: dict[str, object] | None = None,
) -> None:
    package_root = hub / Path(*package_name.split("/"))
    snapshot_dir = package_root / "20260620_approved"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    data_file = snapshot_dir / "data.csv"
    rows = [
        {"asset_id": f"{package_name}:asset_a", "player": "Fixture A"},
        {"asset_id": f"{package_name}:asset_b", "player": "Fixture B"},
    ]
    with data_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("asset_id", "player"))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "source_lane": package_name.split("/")[0],
        "source_repo": "fixture-only",
        "source_branch": "fixture",
        "source_head": "fixturehead",
        "package_name": package_name,
        "schema_version": "fixture_schema_v1",
        "data_file": "data.csv",
        "row_count": len(rows),
        "sha256": _sha256(data_file),
        "created_at": "2026-06-20T00:00:00-06:00",
        "approval_status": "approved",
        "approved_for": [READ_ONLY_USE],
        "allowed_use": [READ_ONLY_USE, MANUAL_REVIEW_USE],
        "forbidden_use": [PRIVATE_VALUE_FORBIDDEN],
        "contains_private_value": package_name
        in {
            "rookie_hq/frozen_rookie_mock_input",
            "model_value/veteran_private_values",
        },
        "contains_market_data": False,
        "contains_adp": False,
        "notes": "Fixture-only exchange package.",
    }
    if package_name == "market_behavior/display_only_market_context":
        manifest.update(
            {
                "allowed_use": [
                    READ_ONLY_USE,
                    "display_only_market_context",
                    "opponent_behavior",
                    "availability",
                    "pick_timing",
                ],
                "forbidden_use": [PRIVATE_VALUE_FORBIDDEN, "nwr_private_value"],
                "contains_private_value": False,
                "contains_market_data": True,
                "contains_adp": True,
            }
        )
    if manifest_overrides:
        manifest.update(manifest_overrides)
    (snapshot_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package_root / "latest_approved.json").write_text(
        json.dumps({"manifest_path": "20260620_approved/manifest.json"}),
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _package(report: object, package_name: str) -> object:
    return next(row for row in report.package_reports if row.package_name == package_name)
