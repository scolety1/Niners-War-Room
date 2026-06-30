from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.draft_day_trade_lab_service import (
    NOT_ENOUGH_INFORMATION,
    add_trade_item,
    build_trade_item_lookup,
    empty_trade_state,
    package_summary_rows,
    pick_context_options,
    player_options,
    review_trade_package,
    trade_item_rows,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "app" / "pages" / "23_trading_lab_v1.py"
SERVICE_PATH = ROOT / "src" / "services" / "draft_day_trade_lab_service.py"
DOC_ROOT = ROOT / "docs" / "hq" / "trading_lab" / "manual_planner_safe_upgrade_20260630"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _board() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Alpha RB",
                "position": "RB",
                "nfl_team": "SF",
                "final_tier": "Tier 1",
                "final_board_score_visible": "99.0",
                "risk_notes": "",
            },
            {
                "final_board_rank": 30,
                "player": "Bravo WR",
                "position": "WR",
                "nfl_team": "DAL",
                "final_tier": "Tier 4",
                "final_board_score_visible": "55.0",
                "risk_notes": "Needs manual role review",
            },
        ]
    )


def _trade_context() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Alpha RB",
                "position": "RB",
                "nfl_team": "SF",
                "tier_movement_note": "top tier",
                "position_scarcity_note": "scarcity note",
                "pick_window_note": "",
                "risk_manual_review_notes": "",
            },
            {
                "final_board_rank": 30,
                "player": "Bravo WR",
                "position": "WR",
                "nfl_team": "DAL",
                "tier_movement_note": "depth tier",
                "position_scarcity_note": "",
                "pick_window_note": "",
                "risk_manual_review_notes": "Needs manual role review",
            },
        ]
    )


def _pick_context() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Alpha RB",
                "position": "RB",
                "nfl_team": "SF",
                "rookie_tier_display_only": "Tier 1",
                "pick_window_note": "1.05 window",
                "caveat": "display-only pick context",
            }
        ]
    )


def test_page_exposes_manual_planning_workspace_without_market_panel() -> None:
    text = _read(PAGE_PATH)

    required = [
        "Manual trade planning workspace",
        "Manual planning only. No trade valuation, market valuation, pick valuation, model",
        "Trade Away Pick Planner",
        "Trade For Pick Planner",
        "Structured manual planner rows",
        "Editable manual checklist",
        "Download manual trade-away memo",
        "Download manual trade-for memo",
        "Missing evidence / gated context",
        "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN",
        "Not enough information",
    ]
    for term in required:
        assert term in text

    forbidden = [
        "summarize_trade_package_market",
        "display_market_package_rows",
        "display_market_totals",
        "Market Baseline / Display-Only sanity check",
        "Market sanity",
        "Visible score gap",
        "score_gap_display",
        "Looks favorable",
        "least I can pay",
        "Minimum offer",
    ]
    for term in forbidden:
        assert term not in text


def test_service_review_is_context_completeness_not_verdict_or_pricing() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    state = add_trade_item(
        empty_trade_state(),
        "give",
        player_options(lookup)["#30 - Bravo WR (WR, DAL)"],
    )
    state = add_trade_item(state, "get", player_options(lookup)["#1 - Alpha RB (RB, SF)"])

    review = review_trade_package(state, lookup)
    summary = package_summary_rows(state, lookup)
    rows = trade_item_rows(state, lookup)

    assert review.status == "Context ready for manual review"
    assert review.missing_context_display == "Manual review required"
    assert "No package value" in review.explanation
    assert "visible_score_sum" not in summary.columns
    assert "visible_score_for_context" not in rows.columns


def test_pick_only_package_stays_not_enough_information_without_pick_pricing() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    pick = next(iter(pick_context_options(lookup).values()))
    state = add_trade_item(empty_trade_state(), "give", pick)
    state = add_trade_item(state, "get", pick)

    review = review_trade_package(state, lookup)

    assert review.status == "Pick-only context present"
    assert review.missing_context_display == "More evidence needed"
    assert "no numeric pick context is inferred" in review.explanation.lower()


def test_service_does_not_import_market_or_mutate_source_truth() -> None:
    text = _read(SERVICE_PATH)

    forbidden = [
        "market_baseline_service",
        "get_pick_market_value",
        "join_market_to_players",
        "load_market_freshness",
        "dp_value",
        "final_board_rank =",
        "sort_values",
    ]
    for term in forbidden:
        assert term not in text


def test_docs_required_for_safe_upgrade_exist() -> None:
    expected = [
        "current_state_audit.md",
        "research_intake_matrix.csv",
        "language_guardrail_audit.md",
        "implementation_summary.md",
        "test_report.md",
        "safe_upgrade_manifest.md",
    ]
    for filename in expected:
        assert (DOC_ROOT / filename).exists(), filename


def test_no_recommendation_adjacent_strings_in_active_page_or_service() -> None:
    combined = f"{_read(PAGE_PATH)}\n{_read(SERVICE_PATH)}".lower()
    allowed_negative_assertions = [
        "trade valuation",
        "market valuation",
        "pick valuation",
        "trade calculator",
    ]
    forbidden = [
        "looks favorable",
        "risky",
        "fair value",
        "value gap",
        "winner",
        "win this trade",
        "lose this trade",
        "least you can pay",
        "least i can pay",
        "minimum offer",
        "overpay",
        "underpay",
        "pick value",
        "market says",
        "adp value",
        "dynastyprocess value",
        "ktc value",
        "trade score",
        "score gap",
        "visible score gap",
    ]
    for term in forbidden:
        assert term not in combined
    for term in allowed_negative_assertions:
        assert term in combined


def test_missing_context_uses_explicit_not_enough_information() -> None:
    assert NOT_ENOUGH_INFORMATION == "Not enough information"
    page = _read(PAGE_PATH)
    for unsafe_default in (
        "missing data is healthy",
        "missing data is clean",
        "missing data is zero",
    ):
        assert unsafe_default not in page.lower()
