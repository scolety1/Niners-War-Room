from __future__ import annotations

import csv
from pathlib import Path

from src.services.player_compare_decision_service import (
    NEEDS_IDENTITY_REVIEW,
    NO_RECOMMENDATION_CALCULATED,
    NOT_ENOUGH_INFORMATION,
    SAFE_NOW_DISPLAY_ONLY,
    build_player_compare_nflverse_context,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "app" / "pages" / "22_player_compare_v1.py"


def test_safe_identity_rows_render_display_only_context(tmp_path: Path) -> None:
    artifact_path, schema_path = _write_context_files(tmp_path)

    context = build_player_compare_nflverse_context(
        [
            {"player": "Safe Wideout", "position": "WR", "player_id": "safe-1"},
            {"player": "Review Back", "position": "RB", "player_id": "review-1"},
        ],
        artifact_path=artifact_path,
        schema_path=schema_path,
    )

    safe_identity = context.identity_rows[0]
    review_identity = context.identity_rows[1]
    assert safe_identity["Context status"] == "Display-only context"
    assert safe_identity["NFLVerse/GSIS ID"] == "00-0000001"
    assert safe_identity["Sleeper ID"] == "safe-1"
    assert safe_identity["No recommendation"] == NO_RECOMMENDATION_CALCULATED
    assert review_identity["Context status"] == NEEDS_IDENTITY_REVIEW
    assert review_identity["NFLVerse/GSIS ID"] == NOT_ENOUGH_INFORMATION
    assert review_identity["Sleeper ID"] == NOT_ENOUGH_INFORMATION
    assert review_identity["Identity caveat"] == "Manual review only"


def test_identity_review_rows_do_not_expose_detailed_context(tmp_path: Path) -> None:
    artifact_path, schema_path = _write_context_files(tmp_path)

    context = build_player_compare_nflverse_context(
        [{"player": "Review Back", "position": "RB", "player_id": "review-1"}],
        artifact_path=artifact_path,
        schema_path=schema_path,
    )

    combined = " ".join(
        value
        for table in (
            context.recent_activity_rows,
            context.usage_role_rows,
            context.availability_rows,
            context.roster_window_rows,
        )
        for row in table
        for value in row.values()
    )
    assert "ACT" not in combined
    assert "RB1" not in combined
    assert "Full Participation" not in combined
    assert "active=True" not in combined
    assert NEEDS_IDENTITY_REVIEW in combined


def test_missing_values_stay_not_enough_information(tmp_path: Path) -> None:
    artifact_path, schema_path = _write_context_files(tmp_path, include_missing_safe_row=True)

    context = build_player_compare_nflverse_context(
        [{"player": "Missing Wideout", "position": "WR", "player_id": "missing-1"}],
        artifact_path=artifact_path,
        schema_path=schema_path,
    )

    usage = context.usage_role_rows[0]
    availability = context.availability_rows[0]
    activity = context.recent_activity_rows[0]
    combined = " ".join(
        value.lower()
        for row in (usage, availability, activity)
        for value in row.values()
    )
    assert usage["Depth chart role"] == NOT_ENOUGH_INFORMATION
    assert availability["Injury report status"] == NOT_ENOUGH_INFORMATION
    assert activity["Snap sample size"] == NOT_ENOUGH_INFORMATION
    assert "not zero" in combined
    assert "not zero snaps" not in combined
    assert "not no-role" in combined
    assert "not healthy" in combined
    assert "not confirmed udfa" in combined
    assert "is healthy" not in combined
    assert "is confirmed udfa" not in combined


def test_tracked_artifact_counts_and_schedule_are_current_contract() -> None:
    context = build_player_compare_nflverse_context([])

    assert context.artifact_available
    assert context.artifact_rows == 294
    assert context.safe_display_rows == 240
    assert context.identity_review_rows == 54
    assert context.schedule_available_rows == 0
    assert any(row["Item"] == "Next game / opponent / bye context" for row in context.deferred_rows)


def test_player_compare_page_uses_tracked_artifact_only() -> None:
    page = PAGE.read_text(encoding="utf-8")

    assert "build_player_compare_nflverse_context" in page
    assert "NFLVerse Player Context" in page
    assert "Dataset Freshness / Coverage Badges" in page
    assert "C:\\NWR_SHARED_DATA" not in page
    assert "NWR_SHARED_DATA" not in page
    assert "current_pick_value" not in page
    assert "comeback projection is calculated" in page
    lowered = page.lower()
    for forbidden in (
        "opportunity score",
        "role score",
        "breakout score",
        "better role",
        "pick this player",
    ):
        assert forbidden not in lowered


def _write_context_files(
    tmp_path: Path,
    *,
    include_missing_safe_row: bool = False,
) -> tuple[Path, Path]:
    artifact_path = tmp_path / "artifact.csv"
    schema_path = tmp_path / "schema.csv"
    artifact_rows = [_safe_row(), _review_row()]
    if include_missing_safe_row:
        artifact_rows.append(_missing_safe_row())
    _write_csv(artifact_path, artifact_rows)
    _write_csv(schema_path, _schema_rows())
    return artifact_path, schema_path


def _safe_row() -> dict[str, str]:
    row = _base_artifact_row("safe-1", "Safe Wideout", "WR", SAFE_NOW_DISPLAY_ONLY, "false")
    row.update(
        {
            "nflverse_gsis_id": "00-0000001",
            "nflverse_sleeper_id": "safe-1",
            "nflverse_player_name": "Safe Wideout",
            "nflverse_team": "SF",
            "nflverse_position": "WR",
            "identity_caveat": "exact_nwr_player_id_to_rosters_sleeper_id",
            "roster_birth_date_derived_age": "25",
            "age_source": "rosters.birth_date",
            "roster_status": "ACT",
            "weekly_roster_status": "ACT",
            "injury_report_status": "Questionable",
            "injury_report_date_week": "season=2025; week=9",
            "practice_status": "Limited Participation in Practice",
            "depth_chart_position": "WR",
            "depth_chart_rank": "1",
            "depth_chart_role": "formation=Offense; depth_team=1; pos_group=WR",
            "snap_count_recency": "season=2025; week=9",
            "latest_snap_season": "2025",
            "latest_snap_week": "9",
            "snap_sample_size": "4",
            "last_active_season": "2025",
            "last_active_week": "9",
            "contract_context": "active=True; team=49ers; year_signed=2025; years=2",
        }
    )
    return row


def _review_row() -> dict[str, str]:
    row = _base_artifact_row("review-1", "Review Back", "RB", "NEED_IDENTITY_REVIEW", "true")
    row.update(
        {
            "nflverse_gsis_id": "00-review",
            "nflverse_sleeper_id": "review-1",
            "roster_status": "ACT",
            "weekly_roster_status": "ACT",
            "injury_report_status": "Full Participation in Practice",
            "depth_chart_role": "RB1",
            "contract_context": "active=True; team=49ers; year_signed=2025; years=2",
        }
    )
    return row


def _missing_safe_row() -> dict[str, str]:
    row = _base_artifact_row("missing-1", "Missing Wideout", "WR", SAFE_NOW_DISPLAY_ONLY, "false")
    row.update(
        {
            "nflverse_gsis_id": "00-0000002",
            "nflverse_sleeper_id": "missing-1",
            "nflverse_player_name": "Missing Wideout",
            "depth_chart_role": "NEED_DATASET_REFRESH",
            "injury_report_status": NOT_ENOUGH_INFORMATION,
            "snap_sample_size": NOT_ENOUGH_INFORMATION,
            "draft_round": NOT_ENOUGH_INFORMATION,
        }
    )
    return row


def _base_artifact_row(
    player_id: str,
    name: str,
    position: str,
    identity_status: str,
    review_required: str,
) -> dict[str, str]:
    return {
        field: NOT_ENOUGH_INFORMATION
        for field in (
            "nwr_player_id",
            "nwr_player_name",
            "nwr_position",
            "nflverse_gsis_id",
            "nflverse_sleeper_id",
            "nflverse_player_name",
            "nflverse_team",
            "nflverse_position",
            "identity_join_status",
            "identity_caveat",
            "roster_birth_date_derived_age",
            "age_source",
            "roster_status",
            "weekly_roster_status",
            "injury_report_status",
            "injury_report_date_week",
            "practice_status",
            "next_game_context",
            "opponent_context",
            "bye_context",
            "depth_chart_position",
            "depth_chart_rank",
            "depth_chart_role",
            "snap_count_recency",
            "latest_snap_season",
            "latest_snap_week",
            "snap_sample_size",
            "last_active_season",
            "last_active_week",
            "draft_round",
            "contract_context",
            "per_field_dataset_source",
            "per_field_freshness_source_status",
            "display_only",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
            "rank_logic_allowed",
            "hidden_sort_allowed",
            "trade_value_allowed",
            "pick_value_allowed",
            "review_required",
        )
    } | {
        "nwr_player_id": player_id,
        "nwr_player_name": name,
        "nwr_position": position,
        "identity_join_status": identity_status,
        "per_field_dataset_source": "identity=rosters; snap=snap_counts; injury=injuries",
        "per_field_freshness_source_status": "rosters:YELLOW/fresh/identity_only",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "rank_logic_allowed": "false",
        "hidden_sort_allowed": "false",
        "trade_value_allowed": "false",
        "pick_value_allowed": "false",
        "review_required": review_required,
    }


def _schema_rows() -> list[dict[str, str]]:
    fields = set(_safe_row()) | set(_review_row())
    return [
        {
            "column_name": field,
            "description": field,
            "source_dataset": _source_dataset(field),
            "field_status": SAFE_NOW_DISPLAY_ONLY,
            "missing_value_policy": (
                "Missing data remains Not enough information. Missing draft is not UDFA."
            ),
            "display_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "source_truth_allowed": "false",
            "rank_logic_allowed": "false",
            "hidden_sort_allowed": "false",
            "trade_value_allowed": "false",
            "pick_value_allowed": "false",
        }
        for field in sorted(fields)
    ]


def _source_dataset(field: str) -> str:
    if field.startswith("injury") or field == "practice_status":
        return "injuries"
    if field.startswith("depth"):
        return "depth_charts"
    if "snap" in field:
        return "snap_counts"
    if field.startswith("last_active"):
        return "player_stats_weekly"
    if field.startswith("draft"):
        return "draft_picks"
    return "rosters"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
