from __future__ import annotations

import json
from pathlib import Path

from scripts.mock_draft_preflight_input_gates import (
    build_and_write_preflight_input_gates,
    build_preflight_input_gates,
)

ROSTER_FIXTURE = Path(
    "tests/fixtures/mock_draft/roster_coverage_validator/"
    "post_drop_rosters_10_teams_valid.csv"
)
TEAM_MANAGERS_FIXTURE = Path(
    "tests/fixtures/mock_draft/roster_coverage_validator/"
    "team_managers_10_teams_valid.csv"
)
DRAFT_ORDER_FIXTURE = Path(
    "tests/fixtures/mock_draft/pick_order_validator/draft_order_valid_2026.csv"
)
REVIEW_DRAFT_ORDER_FIXTURE = Path(
    "tests/fixtures/mock_draft/pick_order_validator/draft_order_review_flags.csv"
)


def test_missing_required_staged_inputs_are_blockers_not_simulation() -> None:
    result = build_preflight_input_gates(staging_root=Path("missing/staging"))

    assert result.review_only is True
    assert result.full_simulation_ready is False
    assert result.manifest["simulation_run"] is False
    assert len(result.blocking_reasons) == 3
    assert result.manifest["real_market_data_imported"] is False


def test_fake_complete_staging_set_can_pass_preflight(tmp_path) -> None:
    staging_root = tmp_path / "staging"
    staging_root.mkdir()
    _copy_text(ROSTER_FIXTURE, staging_root / "post_drop_rosters.csv")
    _copy_text(TEAM_MANAGERS_FIXTURE, staging_root / "team_managers.csv")
    _copy_text(DRAFT_ORDER_FIXTURE, staging_root / "post_drop_draft_order.csv")

    result = build_preflight_input_gates(staging_root=staging_root)

    assert result.full_simulation_ready is True
    assert result.blocking_reasons == ()
    assert result.manifest["yellow_gate_rows"] == 3
    assert all(
        "optional_input_missing" in str(row["review_flag"])
        for row in result.gate_rows
        if row["status"] == "YELLOW"
    )


def test_placeholder_pick_blocks_full_simulation(tmp_path) -> None:
    staging_root = tmp_path / "staging"
    staging_root.mkdir()
    _copy_text(ROSTER_FIXTURE, staging_root / "post_drop_rosters.csv")
    _copy_text(TEAM_MANAGERS_FIXTURE, staging_root / "team_managers.csv")
    _copy_text(REVIEW_DRAFT_ORDER_FIXTURE, staging_root / "post_drop_draft_order.csv")

    result = build_preflight_input_gates(staging_root=staging_root)

    assert result.full_simulation_ready is False
    assert "post_drop_draft_order:not_green" in result.blocking_reasons
    assert any(
        row["review_flag"] == "future_placeholder_pick_review_required"
        for row in result.gate_rows
    )


def test_preflight_writer_creates_local_manifest_and_gate_rows(tmp_path) -> None:
    staging_root = tmp_path / "staging"
    output_root = tmp_path / "local_exports/mock_draft/preflight_input_gates_20260617"
    result = build_and_write_preflight_input_gates(
        staging_root=staging_root,
        output_root=output_root,
    )

    manifest_path = result.artifact_paths["manifest"]
    gate_rows_path = result.artifact_paths["gate_rows"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["full_simulation_ready"] is False
    assert manifest["simulation_run"] is False
    assert manifest["market_policy"] == (
        "ADP/market remains behavior-only and cannot become NWR value."
    )
    assert gate_rows_path.exists()
    assert "local_exports" in str(output_root).replace("\\", "/")


def _copy_text(source: Path, destination: Path) -> None:
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
