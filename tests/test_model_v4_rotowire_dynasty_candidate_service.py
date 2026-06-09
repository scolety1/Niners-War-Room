from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_rotowire_dynasty_candidate_service import (
    CANDIDATE_HEADER,
    POSITION_WEIGHTS,
    build_rotowire_dynasty_candidate_layer,
    write_rotowire_dynasty_candidate_outputs,
)


def test_position_weights_sum_to_one() -> None:
    for weights in POSITION_WEIGHTS.values():
        assert round(sum(weights.values()), 6) == 1.0


def test_dynasty_candidate_layer_excludes_projection_market_and_league_rank_value() -> None:
    result = build_rotowire_dynasty_candidate_layer()
    assert result.summary["projection_rows_used_for_core_value"] == 0
    assert result.summary["market_value_used_for_private_value"] is False
    assert result.summary["league_rank_used_for_private_value"] is False

    bijan = next(row for row in result.candidate_rows if row["player_name"] == "Bijan Robinson")
    assert bijan["allowed_use"] == "review_only"
    assert bijan["projections_used_for_core_value"] is False
    assert bijan["market_used_for_private_value"] is False
    assert bijan["league_rank_used_for_private_value"] is False


def test_missing_incoming_rookie_is_capped_and_review_only() -> None:
    result = build_rotowire_dynasty_candidate_layer()
    rows = {row["player_name"]: row for row in result.candidate_rows}

    assert rows["Jeremiyah Love"]["confidence_label"] == "weak_review"
    assert float(rows["Jeremiyah Love"]["dynasty_candidate_value"]) <= 40.0
    assert rows["Jeremiyah Love"]["confidence_cap_applied"] is True


def test_missing_components_do_not_become_zero_evidence() -> None:
    result = build_rotowire_dynasty_candidate_layer()
    missing = [
        row
        for row in result.component_rows
        if row["player_name"] == "Jeremiyah Love" and row["component"] == "route_target_role"
    ][0]

    assert missing["source_status"] == "missing"
    assert missing["normalized_score"] == ""
    assert missing["contribution"] == ""


def test_confidence_is_receipt_only_not_private_value_boost() -> None:
    result = build_rotowire_dynasty_candidate_layer()
    confidence = [
        row
        for row in result.component_rows
        if row["player_name"] == "Bijan Robinson" and row["component"] == "evidence_confidence"
    ][0]

    assert confidence["allowed_use"] == "confidence_only"
    assert float(confidence["component_weight"]) == 0.0
    assert float(confidence["contribution"]) == 0.0


def test_qb_format_suppression_keeps_elite_rbs_above_elite_qbs_in_candidate_review() -> None:
    result = build_rotowire_dynasty_candidate_layer()
    rows = {row["player_name"]: row for row in result.candidate_rows}

    assert float(rows["Bijan Robinson"]["dynasty_candidate_value"]) > float(
        rows["Josh Allen"]["dynasty_candidate_value"]
    )
    assert float(rows["De'Von Achane"]["dynasty_candidate_value"]) > float(
        rows["Lamar Jackson"]["dynasty_candidate_value"]
    )


def test_rb_age_cap_prevents_old_production_from_beating_young_elite_rb() -> None:
    result = build_rotowire_dynasty_candidate_layer()
    rows = {row["player_name"]: row for row in result.candidate_rows}

    assert rows["Derrick Henry"]["age_value_cap_applied"] is True
    assert "age_value_cap_applied" in str(rows["Derrick Henry"]["review_warnings"])
    assert float(rows["De'Von Achane"]["dynasty_candidate_value"]) > float(
        rows["Derrick Henry"]["dynasty_candidate_value"]
    )


def test_dynasty_candidate_receipts_show_vorp_is_review_only_first_down_estimated() -> None:
    result = build_rotowire_dynasty_candidate_layer()
    receipts = [
        row
        for row in result.receipt_rows
        if row["player_name"] == "Bijan Robinson" and row["component"] == "replacement_vorp"
    ]

    assert receipts
    assert receipts[0]["allowed_use"] == "review_only"
    assert receipts[0]["source_status"] == "review_only_first_down_estimated_from_history"
    assert "estimated_first_down_points" in str(receipts[0]["raw_fields_json"])
    assert "first-down-adjusted" in str(receipts[0]["receipt_note"])


def test_dynasty_candidate_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_dynasty_candidate_layer()
    paths = write_rotowire_dynasty_candidate_outputs(tmp_path, result)

    assert paths["candidates"].exists()
    with paths["candidates"].open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == CANDIDATE_HEADER
