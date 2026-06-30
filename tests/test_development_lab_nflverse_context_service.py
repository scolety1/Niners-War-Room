from __future__ import annotations

from src.services.development_lab_nflverse_context_service import (
    DevelopmentLabNflverseContext,
    dataset_readiness_rows,
    development_lab_context_status_rows,
    draft_capital_context_rows,
    identity_review_status_rows,
    load_development_lab_nflverse_context,
    manual_nwr_player_ids,
    player_context_artifact_status_rows,
    roster_status_context_rows,
    schedule_context_display_rows,
    schedule_unavailable_rows,
)
from src.services.nflverse_player_context_display_service import SAFE_NOW_DISPLAY_ONLY


def test_player_context_artifact_status_matches_hq_expected_counts() -> None:
    context = load_development_lab_nflverse_context()
    rows = player_context_artifact_status_rows(context)
    status_by_check = {row["Check"]: row["Status"] for row in rows}

    assert len(context.artifact_rows) == 294
    assert len(context.safe_rows) == 281
    assert len(context.needs_identity_review_rows) == 13
    assert status_by_check["Identity proposals"] == "43"
    assert status_by_check["Identity rows needing human review"] == "4"
    assert status_by_check["Identity rows kept for future review"] == "7"
    assert status_by_check["next game / opponent / bye"] == "240/281 display rows"
    assert status_by_check["ff_rankings"] == "blocked_policy"


def test_dataset_readiness_uses_tracked_refresh_health_docs() -> None:
    rows = dataset_readiness_rows()
    by_dataset = {row["Dataset"]: row for row in rows}

    assert by_dataset["players"]["Policy"] == "identity_only"
    assert "Not enough information" in by_dataset["rosters"]["Missing rule"]
    assert by_dataset["ff_rankings"]["Policy"] == "blocked_policy"
    assert {row["Model input"] for row in rows} == {"false"}
    assert {row["Rank logic"] for row in rows} == {"false"}


def test_roster_status_context_filters_by_safe_identity_and_player_id() -> None:
    rows = roster_status_context_rows(player_ids=("9493",))

    assert len(rows) == 1
    assert rows[0]["NWR Player ID"] == "9493"
    assert rows[0]["Player"] == "Puka Nacua"
    assert rows[0]["Identity Status"] == SAFE_NOW_DISPLAY_ONLY
    assert rows[0]["Display Policy"] == "display-only/manual context"
    assert rows[0]["Source Label"]
    assert rows[0]["Freshness Label"]
    assert rows[0]["Coverage Label"]
    assert "next_game_context" not in rows[0]


def test_unmapped_player_id_renders_not_enough_information() -> None:
    rows = roster_status_context_rows(player_ids=("not-real",))

    assert rows == [
        {
            "NWR Player ID": "not-real",
            "Player": "Not enough information",
            "Identity Status": "Not enough information",
            "Source Label": "Not enough information",
            "Freshness Label": "Not enough information",
            "Coverage Label": "Not enough information",
        }
    ]


def test_schema_manifest_blocks_unapproved_fields_even_for_safe_rows() -> None:
    context = DevelopmentLabNflverseContext(
        artifact_rows=(
            {
                "nwr_player_id": "1",
                "nwr_player_name": "Player One",
                "identity_join_status": SAFE_NOW_DISPLAY_ONLY,
                "review_required": "false",
                "display_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "source_truth_allowed": "false",
                "rank_logic_allowed": "false",
                "hidden_sort_allowed": "false",
                "trade_value_allowed": "false",
                "pick_value_allowed": "false",
                "roster_status": "ACT",
                "per_field_dataset_source": "rosters",
                "per_field_freshness_source_status": "fresh",
                "data_coverage_status": "ready",
            },
        ),
        schema_rows=(
            _schema_row("nwr_player_id"),
            _schema_row("nwr_player_name"),
            _schema_row("roster_status", field_status="NEED_SCHEMA_REVIEW"),
            _schema_row("per_field_dataset_source"),
            _schema_row("per_field_freshness_source_status"),
            _schema_row("data_coverage_status"),
        ),
        identity_review_rows=(),
        dataset_registry_rows=(),
        dataset_coverage_rows=(),
    )

    rows = roster_status_context_rows(player_ids=("1",), context=context)

    assert rows[0]["Roster Status"] == "Not enough information"
    assert rows[0]["Source Label"] == "rosters"


def test_need_identity_review_rows_show_status_only() -> None:
    rows = identity_review_status_rows(limit=5)

    assert rows
    assert set(rows[0]) == {
        "NWR Player ID",
        "Player",
        "NWR Position",
        "NWR Team",
        "Identity Status",
        "Review Note",
    }
    assert {row["Identity Status"] for row in rows} == {"Needs identity review"}
    assert "Roster Status" not in rows[0]
    assert "NFLVerse Team" not in rows[0]


def test_draft_capital_rows_are_factual_display_only_when_present() -> None:
    rows = draft_capital_context_rows(limit=10)

    assert rows
    assert all(row["Identity Status"] == SAFE_NOW_DISPLAY_ONLY for row in rows)
    assert all(row["NFL Draft Year"] != "Not enough information" for row in rows)
    assert all(row["Display Policy"] == "display-only/manual context" for row in rows)


def test_schedule_and_context_status_keep_unavailable_fields_explicit() -> None:
    schedule = schedule_unavailable_rows()
    statuses = development_lab_context_status_rows()

    assert {row["Status"] for row in schedule} == {"Not enough information"}
    assert any(row["Status"] == "SCHEDULE_CONTEXT_DISPLAY_READY" for row in statuses)
    assert any(row["Status"] == "Needs identity review" for row in statuses)


def test_schedule_context_display_rows_show_only_safe_schedule_facts() -> None:
    rows = schedule_context_display_rows(player_ids=("9493",))

    assert len(rows) == 1
    row = rows[0]
    assert row["NWR Player ID"] == "9493"
    assert row["Player"] == "Puka Nacua"
    assert row["Next Game Context"] == (
        "season=2026; week=1; date=2026-09-10; game_id=2026_01_SF_LA"
    )
    assert row["Opponent Context"] == "opponent=SF; home_away=home"
    assert row["Bye Context"] == "week=11"
    assert row["Game Date"] == "2026-09-10"
    assert row["Game Week"] == "1"
    assert row["Home/Away"] == "home"
    assert row["Season"] == "2026"
    assert row["Team"] == "LA"
    assert row["Status"] == SAFE_NOW_DISPLAY_ONLY


def test_schedule_context_unknown_player_id_stays_not_enough_information() -> None:
    rows = schedule_context_display_rows(player_ids=("not-real",))

    assert rows[0]["NWR Player ID"] == "not-real"
    assert rows[0]["Next Game Context"] == "Not enough information"
    assert rows[0]["Opponent Context"] == "Not enough information"
    assert rows[0]["Bye Context"] == "Not enough information"
    assert rows[0]["Status"] == "Not enough information"


def test_manual_nwr_player_ids_are_manual_only_inputs() -> None:
    rows = [
        {"nwr_player_id": "9493"},
        {"nwr_player_id": "Not enough information"},
        {"nwr_player_id": ""},
    ]

    assert manual_nwr_player_ids(rows) == ("9493",)


def _schema_row(column_name: str, *, field_status: str = SAFE_NOW_DISPLAY_ONLY) -> dict[str, str]:
    return {
        "column_name": column_name,
        "field_status": field_status,
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "rank_logic_allowed": "false",
        "hidden_sort_allowed": "false",
        "trade_value_allowed": "false",
        "pick_value_allowed": "false",
    }
