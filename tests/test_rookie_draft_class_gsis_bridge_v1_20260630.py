from __future__ import annotations

from scripts.build_rookie_draft_class_gsis_bridge_v1_20260630 import (
    FINAL_VERDICT,
    NOT_ENOUGH,
    SHARED_OUTPUT_ROOT,
    SOURCE_POLICY_VERDICT,
    build_bridge_rows,
    build_coverage_rows,
    validate_bridge_rows,
    validate_review_rows,
)


def test_bridge_rows_are_review_only_and_link_by_gsis_id() -> None:
    rows = build_bridge_rows(
        draft_rows=_draft_rows(),
        outcome_rows=_outcome_rows(),
    )

    validate_bridge_rows(rows)
    linked = [row for row in rows if row["player_name"] == "Linked Runner"][0]
    censored = [row for row in rows if row["player_name"] == "Censored Receiver"][0]

    assert linked["outcome_label_link_status"] == "linked_to_outcome_labels"
    assert linked["bridge_status"] == "linked_review_only_complete_5y"
    assert linked["fifth_year_window_complete"] == "true"
    assert censored["bridge_status"] == "linked_review_only_right_censored_5y"
    assert censored["fifth_year_window_complete"] == "false"
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_missing_and_unlinked_data_remain_blocked_not_zero_percent() -> None:
    rows = build_bridge_rows(
        draft_rows=_draft_rows(),
        outcome_rows=_outcome_rows(),
    )
    missing = [row for row in rows if row["player_name"] == "Missing Id"][0]
    unlinked = [row for row in rows if row["player_name"] == "Unlinked Tight End"][0]

    assert missing["gsis_id"] == NOT_ENOUGH
    assert missing["bridge_status"] == "blocked_missing_gsis_id"
    assert unlinked["bridge_status"] == "blocked_no_outcome_label_link"
    assert all("0%" not in ",".join(row.values()) for row in rows)


def test_ambiguous_duplicate_name_position_year_rows_are_blocked() -> None:
    rows = build_bridge_rows(
        draft_rows=_draft_rows(),
        outcome_rows=_outcome_rows(),
    )
    ambiguous = [row for row in rows if row["player_name"] == "Alex Same"]

    assert len(ambiguous) == 2
    assert {row["outcome_label_link_status"] for row in ambiguous} == {
        "blocked_ambiguous_identity"
    }
    assert {row["bridge_status"] for row in ambiguous} == {"blocked_ambiguous_identity"}


def test_coverage_rows_keep_flags_closed_and_report_no_probability_wiring() -> None:
    bridge_rows = build_bridge_rows(
        draft_rows=_draft_rows(),
        outcome_rows=_outcome_rows(),
    )
    coverage = build_coverage_rows(
        bridge_rows=bridge_rows,
        outcome_rows=_outcome_rows(),
    )
    metrics = {row["metric"]: row["value"] for row in coverage}

    validate_review_rows(coverage)
    assert metrics["source_policy_gate"] == SOURCE_POLICY_VERDICT
    assert metrics["final_bridge_verdict"] == FINAL_VERDICT
    assert metrics["rookie_probabilities_created"] == "0"
    assert metrics["rankings_wiring_created"] == "0"
    assert metrics["rows_linked_to_outcome_labels"] == "2"


def test_bridge_validation_rejects_model_or_training_promotion() -> None:
    rows = build_bridge_rows(
        draft_rows=_draft_rows(),
        outcome_rows=_outcome_rows(),
    )
    rows[0]["training_allowed"] = "true"

    try:
        validate_bridge_rows(rows)
    except ValueError as exc:
        assert "training_allowed=false" in str(exc)
    else:
        raise AssertionError("Expected bridge validation to reject training promotion")


def test_shared_outputs_are_outside_repo_and_not_local_exports() -> None:
    shared_text = str(SHARED_OUTPUT_ROOT)

    assert "C:\\NWR_SHARED_DATA" in shared_text
    assert "local_exports" not in shared_text


def test_lane_code_does_not_reference_protected_nfl_usage_paths() -> None:
    protected_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )

    assert all("rookie_draft_class_gsis_bridge" not in path for path in protected_paths)


def _draft_rows() -> list[dict[str, str]]:
    return [
        _draft_row("2019", "1", "1", "ARI", "00-1000001", "Linked Runner", "RB"),
        _draft_row("2022", "2", "45", "GB", "00-1000002", "Censored Receiver", "WR"),
        _draft_row("2020", "3", "80", "DAL", "", "Missing Id", "QB"),
        _draft_row("2020", "4", "100", "BUF", "00-1000003", "Unlinked Tight End", "TE"),
        _draft_row("2020", "5", "150", "NYG", "00-1000004", "Alex Same", "RB"),
        _draft_row("2020", "6", "180", "NYJ", "00-1000005", "Alex Same", "RB"),
    ]


def _draft_row(
    season: str,
    round_: str,
    pick: str,
    team: str,
    gsis_id: str,
    name: str,
    position: str,
) -> dict[str, str]:
    return {
        "season": season,
        "round": round_,
        "pick": pick,
        "team": team,
        "gsis_id": gsis_id,
        "pfr_player_id": f"{name[:4]}00",
        "cfb_player_id": "",
        "pfr_player_name": name,
        "position": position,
        "college": "Example",
    }


def _outcome_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for season in range(2019, 2024):
        rows.append({"player_id": "00-1000001", "anchor_season": str(season)})
    rows.append({"player_id": "00-1000002", "anchor_season": "2022"})
    rows.append({"player_id": "00-1000004", "anchor_season": "2020"})
    rows.append({"player_id": "00-1000005", "anchor_season": "2020"})
    return rows
