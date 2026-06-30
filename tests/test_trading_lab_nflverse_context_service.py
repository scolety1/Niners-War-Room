from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.trading_lab_nflverse_context_service import (
    NEED_IDENTITY_REVIEW,
    NOT_ENOUGH_INFORMATION,
    SAFE_NOW_DISPLAY_ONLY,
    display_nflverse_context_rows,
    load_trading_lab_nflverse_context_index,
    nflverse_context_detail_rows,
    nflverse_context_summary_rows,
    nflverse_manual_row_context_rows,
    nflverse_missing_evidence_rows,
    resolve_nflverse_context_for_item,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "app" / "pages" / "23_trading_lab_v1.py"
SERVICE_PATH = ROOT / "src" / "services" / "trading_lab_nflverse_context_service.py"


def _index():
    return load_trading_lab_nflverse_context_index()


def _safe_item() -> dict[str, object]:
    return {
        "side": "NWR gets",
        "asset_type": "Player",
        "label": "#31 - Zay Flowers (WR, BAL)",
        "nwr_player_id": "",
        "player": "Zay Flowers",
        "position": "WR",
        "nfl_team": "BAL",
        "final_board_rank": "31",
    }


def _safe_item_by_id() -> dict[str, object]:
    item = dict(_safe_item())
    item["nwr_player_id"] = "9997"
    return item


def _review_item() -> dict[str, object]:
    return {
        "side": "NWR gets",
        "asset_type": "Player",
        "label": "#1 - Jeremiyah Love (RB, ARI)",
        "nwr_player_id": "",
        "player": "Jeremiyah Love",
        "position": "RB",
        "nfl_team": "ARI",
        "final_board_rank": "1",
    }


def _pick_item() -> dict[str, object]:
    return {
        "side": "NWR gives",
        "asset_type": "Pick context",
        "label": "1.05 window - Example pick",
        "nwr_player_id": NOT_ENOUGH_INFORMATION,
    }


def test_context_artifact_counts_and_schema_safe_fields() -> None:
    index = _index()

    assert index.artifact_row_count == 294
    assert index.safe_row_count == 240
    assert index.identity_review_row_count == 54
    assert "nwr_player_id" in index.schema_safe_fields
    assert "injury_report_status" in index.schema_safe_fields
    assert "depth_chart_position" in index.schema_safe_fields
    assert "draft_pick" in index.schema_safe_fields
    assert "contract_context" in index.schema_safe_fields


def test_safe_player_context_details_render_only_for_safe_identity_rows() -> None:
    index = _index()
    frame = pd.DataFrame([_safe_item()])

    result = resolve_nflverse_context_for_item(_safe_item_by_id(), index)
    visible_result = resolve_nflverse_context_for_item(_safe_item(), index)
    details = display_nflverse_context_rows(nflverse_context_detail_rows(frame, index))
    combined = details.to_string()

    assert result.status == SAFE_NOW_DISPLAY_ONLY
    assert visible_result.join_basis == "artifact_visible_row_resolved_to_nwr_player_id"
    assert "Display-only context" in combined
    assert "Manual review only" in combined
    assert "No valuation calculated" in combined
    assert "No automatic recommendation" in combined
    assert "Availability Context" in combined
    assert "Role Context" in combined
    assert "Draft Context" in combined
    assert "Source / As Of" in details.columns
    assert "Freshness" in details.columns


def test_identity_review_rows_hide_player_context_details() -> None:
    index = _index()
    frame = pd.DataFrame([_review_item()])

    summary = display_nflverse_context_rows(nflverse_context_summary_rows(frame, index))
    details = display_nflverse_context_rows(nflverse_context_detail_rows(frame, index))
    combined = details.to_string()

    assert NEED_IDENTITY_REVIEW in summary.to_string()
    assert "Identity review required; player context details hidden" in combined
    assert "Roster status" not in combined
    assert "Depth chart position" not in combined
    assert "NFL draft pick" not in combined
    assert "Contract context" not in combined


def test_missing_values_and_deferred_context_do_not_become_positive_defaults() -> None:
    index = _index()
    frame = pd.DataFrame([_safe_item()])

    details = display_nflverse_context_rows(nflverse_context_detail_rows(frame, index))
    missing = display_nflverse_context_rows(nflverse_missing_evidence_rows(frame, index))
    details_text = details.to_string()
    missing_text = missing.to_string()

    assert NOT_ENOUGH_INFORMATION in details_text
    assert "Schedule / next game / opponent / bye" in missing_text
    assert "gated pending Trading Lab-specific display review" in missing_text
    assert "Missing is not zero" in missing_text
    for forbidden in ("healthy", "no-role", "no-usage", "confirmed UDFA"):
        assert forbidden.lower() not in details_text.lower()
    assert "zero" not in details_text.lower()


def test_pick_assets_remain_raw_labels_without_player_context_or_pick_valuation() -> None:
    index = _index()
    result = resolve_nflverse_context_for_item(_pick_item(), index)
    frame = pd.DataFrame([_pick_item()])

    summary = display_nflverse_context_rows(nflverse_context_summary_rows(frame, index))
    details = display_nflverse_context_rows(nflverse_context_detail_rows(frame, index))

    assert result.status == "Pick asset raw label only"
    assert "Pick/context assets do not receive NFLVerse player context" in summary.to_string()
    assert details.empty
    assert "pick value" not in summary.to_string().lower()


def test_manual_rows_use_approved_nwr_player_id_only_for_context_details() -> None:
    index = _index()
    rows = [
        {
            "scenario_name": "Manual row",
            "anchor_pick_or_asset": "Zay Flowers",
            "nwr_player_id": "9997",
        }
    ]

    context_rows = display_nflverse_context_rows(
        nflverse_manual_row_context_rows(rows, index)
    )

    assert not context_rows.empty
    assert "Zay Flowers" in context_rows.to_string()
    assert "No valuation calculated" in context_rows.to_string()


def test_active_page_and_context_service_keep_guardrails() -> None:
    combined = "\n".join(
        (
            PAGE_PATH.read_text(encoding="utf-8"),
            SERVICE_PATH.read_text(encoding="utf-8"),
        )
    )
    lower = combined.lower()

    assert r"C:\NWR_SHARED_DATA" not in PAGE_PATH.read_text(encoding="utf-8")
    assert "ff_rankings" not in lower
    for forbidden in (
        "looks favorable",
        "market sanity",
        "score_gap_display",
        "summarize_trade_package_market",
        "display_market_totals",
        "injury_risk_score",
        "medical_projection",
        "side_total_value",
        "package_delta",
        "dynastyprocess value",
        "ktc value",
    ):
        assert forbidden not in lower
