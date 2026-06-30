from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from src.config.constants import APP_NAME
from src.services.draft_day_app_v1_service import (
    FULL_DYNASTY_VIEW,
    RANKINGS_IDENTITY_COLUMN_CONFIG,
    RANKINGS_TABLE_COLUMN_CONFIG,
    display_unified_player_board_frame,
    enrich_statistic_analysis_display_context,
    enrich_unified_player_board_with_market_baseline,
    market_baseline_age_coverage,
    sort_rankings_frame_by_column,
)
from src.services.market_baseline_registry import PAGE_USAGE

PAGE = Path("app/pages/20_final_board_v1.py")
SCORE_FEASIBILITY = Path(
    "docs/hq/rankings/statistic_analysis_v0_20260630/statistic_analysis_design.md"
)


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


def _page_function(name: str):
    tree = ast.parse(_page_text())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            module = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(module)
            namespace: dict[str, object] = {"pd": pd}
            exec(compile(module, str(PAGE), "exec"), namespace)
            return namespace[name]
    raise AssertionError(f"{name} not found")


def test_rankings_full_view_position_filter_defaults_to_fantasy_positions() -> None:
    text = _page_text()

    assert _constant_tuple("BASE_POSITION_FILTERS") == ("QB", "RB", "WR", "TE")
    assert "default_positions = position_values" in text
    assert 'position != "K"' not in text


def test_rankings_full_view_sort_options_do_not_foreground_draft_board_rank() -> None:
    text = _page_text()

    assert 'if view_mode == FULL_DYNASTY_VIEW:' in text
    assert 'return ["Dynasty Rank", "NWR Dynasty Score", "Position Rank", "Age", "Player"]' in text
    assert 'sort_default = _default_sort_label(view_mode)' in text
    assert 'index=sort_options.index(sort_default)' in text
    assert '_default_ascending_for_sort(sort_by)' in text
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
    assert RANKINGS_TABLE_COLUMN_CONFIG["NWR Dynasty Score"]["label"] == "NWR Score"
    assert "missing scores are blank and sort last" in RANKINGS_TABLE_COLUMN_CONFIG[
        "NWR Dynasty Score"
    ]["help"]


def test_rankings_full_view_source_filter_keeps_frozen_board_optional() -> None:
    text = _page_text()

    assert 'options = ["All", "Rookies / prospects", "Veterans", "Full Dynasty source"]' in text
    assert "if view_mode != FULL_DYNASTY_VIEW:" in text
    assert 'options.append("Frozen Baseline only")' in text


def test_market_baseline_is_visible_by_preset_and_display_only() -> None:
    text = _page_text()

    assert '"Market Context"' in text
    assert "_show_market_for_preset" in text
    assert "VIEW_PRESET_DYNASTY_REVIEW" in text
    assert "VIEW_PRESET_MARKET_CONTEXT" in text
    assert "Full dynasty board with DynastyProcess market sanity columns visible" in text
    assert "external market context only" in text
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

    assert "DP Value" in market_display.columns
    assert "Market Flag" in market_display.columns
    assert list(market_display.columns).index("NWR Dynasty Score") < list(
        market_display.columns
    ).index("DP Value")


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
    assert usage.default_visible is False
    assert usage.sort_allowed is False
    assert usage.model_input_allowed is False
    assert "dp_market_rank_1qb" in usage.fields_allowed
    assert "dp_value_1qb" in usage.fields_allowed


def test_rankings_presets_and_advanced_filters_clean_top_controls() -> None:
    text = _page_text()

    for preset in (
        "Dynasty Review",
        "Market Context",
        "Outcome Context",
        "Data Review",
        "Statistic Analysis",
        "Draft Rankings",
    ):
        assert preset in text
    assert "Player Compare Prep" not in text
    assert "Roster Triage" not in text
    assert "Market Analyzer" not in text
    assert "Outcome Lens" not in text
    assert "Compact Draft View" not in text
    assert '"Advanced filters"' in text
    assert '"Value band / review band"' in text
    assert '"Review needed"' in text
    assert '"Market match"' in text
    assert 'st.radio("View"' not in text
    assert '"Tier / band"' not in text
    assert '"Manual review"' not in text
    assert '"Show Market Baseline columns"' not in text


def test_compact_draft_view_stays_full_dynasty_sorted_by_dynasty_rank() -> None:
    text = _page_text()

    assert "Fast-scan full dynasty board" in text
    assert "Dynasty Rank remains the default sort" in text
    assert "if preset == VIEW_PRESET_DRAFT_RANKINGS:" not in text


def test_rankings_default_preset_is_dynasty_review_clean_board() -> None:
    text = _page_text()

    assert 'VIEW_PRESET_DYNASTY_REVIEW = "Dynasty Review"' in text
    assert (
        'st.session_state.get("dynasty_rankings_view_preset", VIEW_PRESET_DYNASTY_REVIEW)'
        in text
    )
    assert "preset = VIEW_PRESET_DYNASTY_REVIEW" in text
    assert "injury-review detail columns stay hidden by default" in text
    assert "VIEW_PRESET_DYNASTY_REVIEW," in text


def test_rankings_browser_title_uses_niners_war_room_not_drop_deadline() -> None:
    assert APP_NAME == "Niners War Room"


def test_rankings_advanced_filter_values_normalize_missing_and_mixed_types() -> None:
    column_values = _page_function("_column_values")
    frame = pd.DataFrame(
        {
            "candidate_value_band": [
                "Anchor",
                None,
                float("nan"),
                " Rookie ",
                1.0,
                pd.NA,
            ]
        }
    )

    assert column_values(frame, "candidate_value_band") == ["1.0", "Anchor", "Rookie"]


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
    assert "Trust" in columns
    assert "Caveat" in columns
    assert "Key Caveat / Review Flag" not in columns
    assert "Candidate Band" not in columns
    assert columns.index("Trust") > columns.index("NWR Dynasty Score")


def test_rankings_numeric_sort_uses_numeric_keys_and_missing_last() -> None:
    frame = pd.DataFrame(
        [
            {"player_name": "Rank 89", "nwr_rank": "89", "nwr_dynasty_score": "89"},
            {"player_name": "Rank 10", "nwr_rank": "10", "nwr_dynasty_score": "9.3"},
            {"player_name": "Rank Missing", "nwr_rank": "", "nwr_dynasty_score": ""},
            {"player_name": "Rank 2", "nwr_rank": "2", "nwr_dynasty_score": "88"},
            {"player_name": "Rank 88", "nwr_rank": "88", "nwr_dynasty_score": "87"},
            {"player_name": "Rank 1", "nwr_rank": "1", "nwr_dynasty_score": "9.1"},
        ]
    )

    rank_sorted = sort_rankings_frame_by_column(
        frame,
        "nwr_rank",
        ascending=True,
        view_mode=FULL_DYNASTY_VIEW,
    )
    score_sorted = sort_rankings_frame_by_column(
        frame,
        "nwr_dynasty_score",
        ascending=False,
        view_mode=FULL_DYNASTY_VIEW,
    )

    assert rank_sorted["player_name"].tolist() == [
        "Rank 1",
        "Rank 2",
        "Rank 10",
        "Rank 88",
        "Rank 89",
        "Rank Missing",
    ]
    assert score_sorted["player_name"].tolist() == [
        "Rank 89",
        "Rank 2",
        "Rank 88",
        "Rank 10",
        "Rank 1",
        "Rank Missing",
    ]


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


def test_rankings_dataset_refresh_panel_uses_central_nflverse_health_service() -> None:
    text = _page_text()

    assert '"Dataset Refresh / Outcome Status"' in text
    assert "dataset_registry_rows" in text
    assert "safe_refresh_dataset_ids" in text
    assert "full_safe_refresh_dataset_ids" in text
    assert "NFLVERSE_REFRESH_HEALTH_WAIT_STATUS" in text
    assert "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN" in text
    assert "GREEN_TRACKED_REFRESH_HEALTH_CONTRACT_PRESENT" in text
    assert "nflverse_dataset_level_refresh_health_20260630" in text
    assert "ff_rankings" in text
    assert "This panel reads only tracked repo artifacts" in text
    assert "does not read raw/cache/shared" in text
    assert "dataset health/status panel" in text
    assert "source-policy display warnings" in text
    assert "approved row-level display artifact or join gate" in text


def test_rankings_does_not_surface_nflverse_player_fields_without_refresh_gate() -> None:
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

    blocked_until_refresh = {
        "Roster Status",
        "Injury Report Status",
        "Next Game",
        "Bye Context",
        "Depth Chart Role",
        "Snap Share Recency",
        "Draft Capital",
        "Identity Bridge Health",
    }
    assert blocked_until_refresh.isdisjoint(set(display.columns))


def test_statistic_analysis_preset_is_read_only_without_invented_components() -> None:
    text = _page_text()
    doc = SCORE_FEASIBILITY.read_text(encoding="utf-8")

    assert "Statistic Analysis" in text
    assert "_render_statistic_analysis_status()" in text
    assert "component weights or per-component" in text
    assert "show_statistic_analysis=show_statistic_analysis" in text
    assert "show_market_baseline = False" in Path(
        "src/services/draft_day_app_v1_service.py"
    ).read_text(encoding="utf-8")
    assert "Status: DEFER" in doc
    assert "Future candidate status: MODEL_FEATURE_CANDIDATE" in doc
    assert "does not expose approved component-level score rows" in doc
    assert "does not calculate or display invented score breakdown math" in doc


def test_statistic_analysis_missing_components_are_not_zero_or_false() -> None:
    frame = pd.DataFrame(
        [
            {
                "nwr_rank": "1",
                "player_name": "Puka Nacua",
                "position": "WR",
                "nfl_team": "LAR",
                "age": "25.0",
                "nwr_dynasty_score": "99",
                "nwr_position_rank": "WR1",
            }
        ]
    )

    enriched = enrich_statistic_analysis_display_context(frame)
    display = display_unified_player_board_frame(
        enriched,
        view_mode=FULL_DYNASTY_VIEW,
        show_market_baseline=True,
        show_statistic_analysis=True,
    )

    assert "Contribution %" in display.columns
    assert display.loc[0, "Contribution %"] == "Not enough information"
    assert display.loc[0, "Missing Component Count"] == "Not enough information"
    assert display.loc[0, "Capped Component Count"] == "Not enough information"
    assert "Market Flag" not in display.columns
    assert "Outcome" not in display.columns
