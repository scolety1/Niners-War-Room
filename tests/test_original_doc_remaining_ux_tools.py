from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_original_doc_status_matrix_documents_fixed_safe_and_deferred_items() -> None:
    text = _read("docs/hq/app_ux/NWR_ORIGINAL_DRAFT_ISSUES_STATUS_20260627.md")

    required = [
        "Reload lost drafted state",
        "In-draft trade `1.04` for `2028 1st + 2.03`",
        "Player Compare was useful but too confusing",
        "Trade Finder / trade away pick tool",
        "Trade For tool",
        "Draft room tabs/search/side panel/cheat sheet/tier ideas",
        "FIXED_ALREADY",
        "SAFE_FIX_THIS_LANE",
        "BLOCKED_NEEDS_MODEL_OR_DATA_GATE",
        "DEFER_DRAFT_ROOM_REVIEW",
    ]
    for term in required:
        assert term in text


def test_player_compare_page_contains_simplified_summary_and_injury_transparency() -> None:
    text = _read("app/pages/22_player_compare_v1.py")

    required = [
        "How to use this comparison",
        "Decision Summary is display-only",
        "Plain-language comparison read",
        "Safer profile",
        "Upside profile",
        "League/scoring fit",
        "Timing / window",
        "Main risk",
        "What still needs review",
        "Injury / Availability Data Status",
        "Injury / Availability Context",
        "Review-only context. No medical projection or injury-risk score is made.",
        "Missing injury context is not clean health",
        "No approved injury context available does not mean clean health.",
    ]
    for term in required:
        assert term in text

    assert "Does not change rank, tier, model value, or source truth." in text


def test_trading_lab_planners_are_manual_only_and_do_not_write_runtime_events() -> None:
    text = _read("app/pages/23_trading_lab_v1.py")

    required = [
        "Trade Away Pick Planner",
        "Trade For Pick Planner",
        "Manual planning only. No trade valuation, market valuation, pick valuation, model",
        "does not find offers, appraise picks, or update",
        "manual workspace, not an offer generator",
        "Structured manual planner rows",
        "Editable manual checklist",
        "Download manual trade-away memo",
        "NFLVerse player context / display-only",
        "Display-only context | Manual review only | No valuation calculated",
    ]
    for term in required:
        assert term in text

    forbidden = [
        "record_trade_event",
        "apply_trade_events_to_pick_frame",
        "RUNTIME_STATE_KEY",
        "Record Accepted Trade",
        "Cheapest Plausible",
        "Worth Pursuing?",
        "least acceptable",
        "market-driven answer",
        "Market sanity",
        "Visible score gap",
        "Looks favorable",
        "Risky",
    ]
    for term in forbidden:
        assert term not in text


def test_player_compare_trade_planner_doc_preserves_guardrails() -> None:
    text = _read("docs/hq/app_ux/NWR_PLAYER_COMPARE_TRADE_PLANNER_UX_20260627.md")

    required = [
        "No injury risk score",
        "No medical comeback projection",
        "Does not write to live draft runtime state",
        "Does not change pick ownership",
        "Does not generate offers",
        "Does not calculate the least acceptable price",
        "DEFER_DRAFT_ROOM_REVIEW",
    ]
    for term in required:
        assert term in text
