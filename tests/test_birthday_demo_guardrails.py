from __future__ import annotations

from pathlib import Path

from app.components.demo_source_labels import demo_source_label
from app.navigation import HIDDEN_ADVANCED_PAGES, VISIBLE_NAVIGATION_PAGES
from src.services.full_player_board_value_service import (
    FULL_BOARD_SCORE_COLUMN,
    _full_board_row,
)
from src.services.player_detail_card_service import build_player_detail_card_payload

UI_FRAMEWORK = Path("app/components/ui_framework.py")
DRAFT_PREP_PAGE = Path("app/pages/06_draft_board.py")
LIVE_DRAFT_ROOM_PAGE = Path("app/pages/07_live_draft_room.py")


def test_demo_source_label_masks_local_paths() -> None:
    assert demo_source_label(
        r"C:\Dev\niners-war-room\local_exports\model_v4\current_value\latest"
        r"\full_player_board_value_review_rows.csv"
    ) == "Full-board NWR Dynasty Rankings export"
    assert demo_source_label(
        r"C:\Dev\niners-war-room\local_exports\model_v4\current_value\latest"
        r"\unknown_receipts.csv"
    ) == "Source file: unknown_receipts.csv"
    assert demo_source_label(
        r"C:\Dev\niners-war-room\local_exports\data_packs"
        r"\lve_sleeper_20260505_pdf_ranks\model_outputs.csv"
    ) == "Active data pack: 2026 pre-draft review pack"


def test_player_detail_receipts_use_demo_safe_source_labels() -> None:
    payload = build_player_detail_card_payload(
        {
            "player": "Keenan Allen",
            "position": "WR",
            "private_score": "17.2422",
            "nwr_rank": "124",
            "source_path": (
                r"C:\Dev\niners-war-room\local_exports\model_v4\current_value\latest"
                r"\full_player_board_value_review_rows.csv"
            ),
            "source_column": "nwr_dynasty_score",
            "upstream_source_path": (
                r"C:\Dev\niners-war-room\local_exports\model_v4\current_value\latest"
                r"\current_player_value_full_board_review_rows.csv"
            ),
            "upstream_source_column": "checkpoint_review_score",
            "lineage_class": "review_v4_current_player",
            "allowed_use": "review_only_full_player_board_rankings",
            "blocked_use": "comparison_only_context_blocked_from_recommendations",
        },
        context="rankings",
    )
    receipts = {receipt.label: receipt.value for receipt in payload.receipts}

    assert payload.source_path == "Full-board NWR Dynasty Rankings export"
    assert receipts["Source path"] == "Full-board NWR Dynasty Rankings export"
    assert receipts["Upstream source path"] == "Model v4 full-board current value export"
    assert not any("C:\\Dev" in receipt.value for receipt in payload.receipts)


def test_draft_prep_and_live_draft_cards_wrap_long_status_values() -> None:
    draft_text = DRAFT_PREP_PAGE.read_text(encoding="utf-8")
    live_text = LIVE_DRAFT_ROOM_PAGE.read_text(encoding="utf-8")

    assert "source-card-grid" in draft_text
    assert "source-card-value" in draft_text
    assert '("My Picks", "1.03, 1.04, 2.04, 2.08, 5.04")' in draft_text
    assert "source-card-grid" in live_text
    assert '("My Picks", ", ".join(OWNED_PICK_LABELS))' in live_text
    assert '("Legal Pool", "Pending")' in live_text


def test_live_draft_room_advanced_details_hide_raw_session_paths() -> None:
    text = LIVE_DRAFT_ROOM_PAGE.read_text(encoding="utf-8")

    assert "Session key hidden for demo" in text
    assert "demo_source_label(SCOUTING_PREP_POOL_ROWS)" in text
    assert '"value": session_key' not in text
    assert '"value": str(SCOUTING_PREP_POOL_ROWS)' not in text
    assert "Never writes to active data packs." in text
    assert "Read-only input for session state." in text


def test_streamlit_status_widget_is_hidden_best_effort_for_demo() -> None:
    text = UI_FRAMEWORK.read_text(encoding="utf-8")

    assert "[data-testid=\"stStatusWidget\"]" in text
    assert "#MainMenu" in text
    assert "footer" in text


def test_rankings_has_visible_route_and_hidden_root_alias() -> None:
    visible_rankings = next(
        page for page in VISIBLE_NAVIGATION_PAGES if page.title == "Dynasty Rankings"
    )
    hidden_defaults = [page for page in HIDDEN_ADVANCED_PAGES if page.default]

    assert visible_rankings.url_path == "rankings"
    assert visible_rankings.default is False
    assert [(page.title, page.url_path) for page in hidden_defaults] == [
        ("Dynasty Rankings Home", "home")
    ]


def test_team_and_roster_tags_are_display_only_for_private_score() -> None:
    active_row = {
        "player_id": "test-001",
        "player_name": "Neutral Tag Player",
        "position": "WR",
        "nfl_team": "SF",
        "snapshot_date": "2026-06-09",
        "private_score": "99.9",
    }
    current_row = {
        "canonical_player_key": "nfl:neutraltagplayer:WR",
        "player_name": "Neutral Tag Player",
        "normalized_player_name": "neutraltagplayer",
        "position": "WR",
        "nfl_team": "SF",
        "checkpoint_review_score": "42.5",
        "confidence_cap": "1.0",
        "checkpoint_version": "model_v4_test",
        "warning_flags": "",
    }
    current_lookup = {("neutraltagplayer", "WR"): [current_row]}

    mine = _full_board_row(
        output_path=Path("local_exports/model_v4/current_value/latest/full.csv"),
        active_row=active_row,
        roster_row={
            "team_name": "Niners",
            "roster_status": "Rostered",
            "team_id": "1",
            "nfl_team": "SF",
        },
        official_row={"league_rank": "1", "rank_source_name": "display only", "nfl_team": "SF"},
        dim_row={"nfl_team": "SF"},
        rotowire_row={"nfl_team": "SF"},
        current_lookup=current_lookup,
        rookie_lookup={},
        market_row={"dynasty_startup_adp": "1.0"},
        current_value_path=Path("local_exports/model_v4/current_value/latest/current.csv"),
    )
    other = _full_board_row(
        output_path=Path("local_exports/model_v4/current_value/latest/full.csv"),
        active_row=active_row,
        roster_row={
            "team_name": "Other Team",
            "roster_status": "Rostered",
            "team_id": "2",
            "nfl_team": "SF",
        },
        official_row={"league_rank": "1", "rank_source_name": "display only", "nfl_team": "SF"},
        dim_row={"nfl_team": "SF"},
        rotowire_row={"nfl_team": "SF"},
        current_lookup=current_lookup,
        rookie_lookup={},
        market_row={"dynasty_startup_adp": "1.0"},
        current_value_path=Path("local_exports/model_v4/current_value/latest/current.csv"),
    )

    assert mine[FULL_BOARD_SCORE_COLUMN] == other[FULL_BOARD_SCORE_COLUMN] == "42.5"
    assert mine["source_column"] == other["source_column"] == FULL_BOARD_SCORE_COLUMN
    assert mine["lineage_class"] == other["lineage_class"] == "review_v4_current_player"
    assert mine["pool_status"] == "MY TEAM"
    assert other["pool_status"] == "OTHER TEAM"
    assert mine["is_my_team"] == "1"
    assert other["is_my_team"] == "0"
