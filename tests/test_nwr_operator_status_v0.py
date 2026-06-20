from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "nwr_operator_status_v0.py"
SPEC = importlib.util.spec_from_file_location("nwr_operator_status_v0", MODULE_PATH)
assert SPEC is not None
STATUS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nwr_operator_status_v0"] = STATUS
SPEC.loader.exec_module(STATUS)


def test_missing_paths_warn_without_crashing(tmp_path: Path) -> None:
    status = STATUS.collect_status(tmp_path / "missing_shared")

    assert any("Lane Exchange root missing" in warning for warning in status.warnings)
    assert status.latest_candidates == {}
    assert status.latest_approved == {}


def test_candidate_newer_than_approved_is_flagged(tmp_path: Path) -> None:
    shared = _shared_root(tmp_path)
    _write_package(
        shared,
        "league_state/pick_order",
        pointer_name="latest_approved.json",
        updated_at="2026-06-20T10:00:00+00:00",
        approved_for=["first local live-test validation"],
    )
    _write_package(
        shared,
        "league_state/pick_order",
        pointer_name="latest_candidate.json",
        updated_at="2026-06-20T11:00:00+00:00",
    )

    status = STATUS.collect_status(shared)

    assert any(
        "latest_candidate newer than latest_approved: league_state/pick_order" in warning
        for warning in status.warnings
    )
    assert any(
        "approval limited to first local live-test validation: league_state/pick_order"
        in warning
        for warning in status.warnings
    )


def test_write_report_only_when_requested(tmp_path: Path) -> None:
    shared = _shared_root(tmp_path)
    _write_package(shared, "stats_context/player_weekly_stats_display_context")

    status = STATUS.collect_status(shared)
    report_root = shared / "scheduled_ingest" / "reports" / "operator_status"
    assert not report_root.exists()

    report_path = STATUS.write_report(status, report_root)

    assert report_path.exists()
    assert "NWR Operator Status V0" in report_path.read_text(encoding="utf-8")


def test_no_latest_approved_mutation(tmp_path: Path) -> None:
    shared = _shared_root(tmp_path)
    pointer_path = _write_package(
        shared,
        "model_value/veteran_private_values",
        pointer_name="latest_approved.json",
        updated_at="2026-06-20T09:00:00+00:00",
    )
    before = pointer_path.read_text(encoding="utf-8")

    status = STATUS.collect_status(shared)
    _ = STATUS.concise_summary(status)
    after = pointer_path.read_text(encoding="utf-8")

    assert after == before


def test_required_package_and_stats_context_status_tables(tmp_path: Path) -> None:
    shared = _shared_root(tmp_path)
    _write_package(shared, "stats_context/player_usage_context")
    _write_package(
        shared,
        "rookie_hq/frozen_rookie_mock_input",
        pointer_name="latest_approved.json",
    )

    status = STATUS.collect_status(shared)
    report = STATUS._markdown_report(status)

    assert "stats_context/player_usage_context" in report
    assert "rookie_hq/frozen_rookie_mock_input" in report
    assert any(
        "stats_context package missing latest_candidate" in warning
        for warning in status.warnings
    )


def _shared_root(tmp_path: Path) -> Path:
    shared = tmp_path / "shared"
    (shared / "lane_exchange").mkdir(parents=True)
    (shared / "lane_exchange_registry").mkdir()
    _write_json(shared / "lane_exchange_registry" / "lane_exchange_v0_registry.json", {})
    (shared / "scheduled_ingest" / "sleeper" / "20260620_200109").mkdir(parents=True)
    (shared / "scheduled_ingest" / "nflverse" / "20260620_214500").mkdir(parents=True)
    (shared / "live_test_reports").mkdir()
    sleeper_report = (
        shared
        / "scheduled_ingest"
        / "sleeper"
        / "20260620_200109"
        / "sleeper_normalizer_v0_report.md"
    )
    nflverse_report = (
        shared
        / "scheduled_ingest"
        / "nflverse"
        / "20260620_214500"
        / "nflverse_normalizer_v0_report.md"
    )
    sleeper_report.write_text("sleeper report", encoding="utf-8")
    nflverse_report.write_text("nflverse report", encoding="utf-8")
    return shared


def _write_package(
    shared: Path,
    package_name: str,
    *,
    pointer_name: str = "latest_candidate.json",
    updated_at: str = "2026-06-20T12:00:00+00:00",
    approved_for: list[str] | None = None,
) -> Path:
    lane, short = package_name.split("/", 1)
    package_root = shared / "lane_exchange" / lane / short
    snapshot = package_root / pointer_name.removesuffix(".json")
    snapshot.mkdir(parents=True)
    manifest_path = snapshot / "manifest.json"
    manifest = {
        "package_name": package_name,
        "approval_status": "candidate" if pointer_name == "latest_candidate.json" else "approved",
        "approved_for": approved_for or ["review_only"],
        "allowed_use": ["first local live-test validation"] if approved_for else ["review_only"],
        "forbidden_use": ["private_value", "latest_approved"],
        "data_file": "data.csv",
        "row_count": 3,
        "sha256": "abc123",
        "created_at": updated_at,
        "notes": "test package",
    }
    pointer = {
        "package_name": package_name,
        "approval_status": manifest["approval_status"],
        "manifest_path": str(manifest_path),
        "data_file": "data.csv",
        "row_count": 3,
        "sha256": "abc123",
        "updated_at": updated_at,
        "allowed_use": manifest["allowed_use"],
        "forbidden_use": manifest["forbidden_use"],
        "notes": "test pointer",
    }
    _write_json(manifest_path, manifest)
    pointer_path = package_root / pointer_name
    _write_json(pointer_path, pointer)
    return pointer_path


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
