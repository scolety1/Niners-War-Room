from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from src.services.draft_day_app_v1_service import (
    FULL_DYNASTY_VIEW,
    RANKINGS_IDENTITY_COLUMN_CONFIG,
    display_unified_player_board_frame,
    enrich_unified_player_board_with_market_baseline,
    market_baseline_age_coverage,
)
from src.services.market_baseline_registry import PAGE_USAGE

PAGE = Path("app/pages/20_final_board_v1.py")


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


def _constant_tuple(name: str) -> tuple[str, ...]:
    tree = ast.parse(_page_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = ast.literal_eval(node.value)
                    return tuple(value)
    raise AssertionError(f"{name} not found")


def test_rankings_full_view_position_filter_defaults_to_fantasy_positions() -> None:
    text = _page_text()

    assert _constant_tuple("BASE_POSITION_FILTERS") == ("QB", "RB", "WR", "TE")
    assert "default_positions = position_values" in text
    assert 'position != "K"' not in text


def test_rankings_full_view_sort_options_do_not_foreground_draft_board_rank() -> None:
    text = _page_text()

    assert 'if view_mode == FULL_DYNASTY_VIEW:' in text
    assert 'return ["Dynasty Rank", "Position Rank", "Age", "Player"]' in text
    assert 'sort_default = _default_sort_label(view_mode)' in text
    assert 'index=sort_options.index(sort_default)' in text
    assert '"Candidate Rank (Review-Only)"' in text
    assert 'if sort_by == "Position Rank" and view_mode != FULL_DYNASTY_VIEW:' in text


def test_rankings_identity_columns_are_pinned_and_sized() -> None:
    text = _page_text()
    rank_config = RANKINGS_IDENTITY_COLUMN_CONFIG["Dynasty Rank"]
    player_config = RANKINGS_IDENTITY_COLUMN_CONFIG["Player"]

    assert "_rankings_identity_column_config()" in text
    assert "column_config=_rankings_identity_column_config()" in text
    assert rank_config["pinned"] is True
    assert player_config["pinned"] is True
    assert 60 <= int(rank_config["width"]) <= 80
    assert 180 <= int(player_config["width"]) <= 220
    assert rank_config["label"] == "Rank"
    assert rank_config["help"] == "Dynasty Rank"
    assert player_config["label"] == "Player"


def test_rankings_full_view_source_filter_keeps_frozen_board_optional() -> None:
    text = _page_text()

    assert 'options = ["All", "Rookies / prospects", "Veterans", "Full Dynasty source"]' in text
    assert "if view_mode != FULL_DYNASTY_VIEW:" in text
    assert 'options.append("Frozen Baseline only")' in text


def test_market_baseline_is_visible_by_preset_and_display_only() -> None:
    text = _page_text()

    assert '"Market Analyzer"' in text
    assert "_show_market_for_preset" in text
    assert "VIEW_PRESET_CLEAN_BOARD" in text
    assert "Market Baseline columns are display-only DynastyProcess context" in text
    assert "market_sanity_filter" in text
    assert "market_match_filter" in text
    assert "display_unified_player_board_frame(" in text
    assert "show_market_baseline=show_market_baseline" in text


def test_tier_board_cheat_sheet_is_embedded_as_display_view() -> None:
    text = _page_text()

    assert '"Tier Board / Cheat Sheet"' in text
    assert "_render_tier_board_cheat_sheet(filtered_board, view_mode)" in text
    assert "Existing rank/tier view only; no hidden market sort." in text
    assert "Cheat Sheets remain available by direct URL" in text


def test_market_baseline_filters_have_required_labels() -> None:
    assert _constant_tuple("MARKET_SANITY_FILTERS") == (
        "All",
        "NWR much higher",
        "NWR much lower",
        "Aligned",
        "No market match",
    )
    assert _constant_tuple("MARKET_MATCH_FILTERS") == (
        "All",
        "Has market match",
        "No market match",
    )


def test_market_columns_can_display_without_sort_or_model_use() -> None:
    frame = pd.DataFrame(
        [
            {
                "nwr_rank": "1",
                "player_name": "Puka Nacua",
                "position": "WR",
                "nfl_team": "LAR",
                "age": "25.0",
                "nwr_position_rank": "WR1",
                "candidate_value_band": "Elite",
                "nwr_dynasty_score": "99",
                "trust_status": "GREEN",
                "confidence_band": "HIGH",
                "dp_value_1qb": "10000",
                "dp_market_rank_1qb": "2",
                "dp_ecr_pos": "1",
                "dp_age": "25.0",
                "market_gap": "-1",
                "market_sanity_label": "Aligned",
                "age_source_display": "NWR approved source",
                "market_baseline_label": "Market Baseline / Display-Only",
            }
        ]
    )

    market_display = display_unified_player_board_frame(
        frame,
        view_mode=FULL_DYNASTY_VIEW,
        show_market_baseline=True,
    )

    assert "DP 1QB Value (Market Baseline / Display-Only)" in market_display.columns
    assert "Market Sanity Flag (Market Baseline / Display-Only)" in market_display.columns
    assert list(market_display.columns).index("NWR Dynasty Score") < list(
        market_display.columns
    ).index("DP 1QB Value (Market Baseline / Display-Only)")


def test_market_baseline_age_fallback_is_display_labeled() -> None:
    frame = pd.DataFrame(
        [
            {
                "player_name": "Brock Purdy",
                "position": "QB",
                "age": "",
                "nwr_rank": "20",
            }
        ]
    )

    enriched = enrich_unified_player_board_with_market_baseline(frame)
    coverage = market_baseline_age_coverage(frame)

    assert "age_source_display" in enriched.columns
    assert coverage["after"] >= coverage["before"]
    if enriched.loc[0, "age"] != "Not enough information":
        assert enriched.loc[0, "age_source_display"] in {
            "NWR approved source",
            "Market Baseline / Display-Only fallback",
        }


def test_market_baseline_unmatched_players_remain_visible() -> None:
    frame = pd.DataFrame(
        [
            {
                "player_name": "Not A Real NWR Player",
                "position": "WR",
                "nwr_rank": "999",
                "age": "",
            }
        ]
    )

    enriched = enrich_unified_player_board_with_market_baseline(frame)

    assert len(enriched) == 1
    assert enriched.loc[0, "player_name"] == "Not A Real NWR Player"
    assert enriched.loc[0, "market_sanity_label"] == "No market match"


def test_market_baseline_registry_allows_rankings_display_only_usage_only() -> None:
    usage = PAGE_USAGE["dynasty_rankings"]

    assert usage.enabled is True
    assert usage.default_visible is True
    assert usage.sort_allowed is False
    assert usage.model_input_allowed is False
    assert "dp_market_rank_1qb" in usage.fields_allowed
    assert "dp_value_1qb" in usage.fields_allowed


def test_rankings_presets_and_advanced_filters_clean_top_controls() -> None:
    text = _page_text()

    for preset in (
        "Clean Board",
        "Market Analyzer",
        "Outcome Lens",
        "Data Review",
        "Compact Draft View",
    ):
        assert preset in text
    assert '"Advanced filters"' in text
    assert '"Value band / review band"' in text
    assert '"Review needed"' in text
    assert '"Market match"' in text
    assert 'st.radio("View"' not in text
    assert '"Tier / band"' not in text
    assert '"Manual review"' not in text
    assert '"Show Market Baseline columns"' not in text


def test_rankings_column_labels_are_human_readable_and_review_fields_late() -> None:
    display = display_unified_player_board_frame(
        pd.DataFrame(
            [
                {
                    "nwr_rank": "1",
                    "player_name": "Puka Nacua",
                    "position": "WR",
                    "nfl_team": "LAR",
                    "age": "25.0",
                    "nwr_dynasty_score": "99",
                    "trust_status": "GREEN",
                    "confidence_band": "HIGH",
                    "candidate_key_caveat": "None",
                    "candidate_value_band": "Anchor",
                }
            ]
        ),
        view_mode=FULL_DYNASTY_VIEW,
        show_market_baseline=False,
    )
    columns = list(display.columns)

    assert columns[:6] == [
        "Dynasty Rank",
        "Player",
        "Pos",
        "NFL Team",
        "Age",
        "NWR Dynasty Score",
    ]
    assert "Data Trust" in columns
    assert "Main Caveat" in columns
    assert "Key Caveat / Review Flag" not in columns
    assert "Candidate Band" not in columns
    assert columns.index("Data Trust") > columns.index("NWR Dynasty Score")


def test_outcome_lens_documents_v2_display_only_and_blocked_fields() -> None:
    text = _page_text()
    audit = Path("docs/hq/app_ux/NWR_DYNASTY_RANKINGS_OUTCOME_COLUMN_AUDIT_20260627.md").read_text(
        encoding="utf-8"
    )

    assert "Outcome V2 is display-only" in text
    assert "This Year = 2026 NFL season" in text
    assert "sack_fumbles_lost missing" in text
    assert "games field missing" in text
    assert "Outcome V1 / Legacy and blocked V2 fields" in text
    assert "BLOCKED_OUTCOME_V2_FIELDS" in text
    assert "T12 this year" in audit
    assert "Blocked until an approved artifact exists" in audit
    assert "Older legacy page text referenced horizon-style placeholder labels" in audit
