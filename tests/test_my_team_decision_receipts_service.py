from __future__ import annotations

from pathlib import Path

from src.services.command_board_service import build_team_command_board
from src.services.my_team_decision_receipts_service import build_my_team_decision_receipts
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    PlayerFeatureReceiptsReport,
    build_player_feature_receipts,
)


def test_my_team_decision_receipts_keep_top_five_rule_and_model_recommendation_separate() -> None:
    team_rows = [
        {
            "player": "Luther Burden",
            "pos": "WR",
            "asset_lifecycle_label": "Year-One NFL Bridge",
            "top_five_rule": "Required Top-Five Release Slot",
            "model_recommendation": "shop/release",
            "release_pain": 17.25,
            "decision_explanation": "Weakest top-five keep priority versus easier cuts.",
            "market_edge": 4.5,
            "confidence": 76.0,
        }
    ]
    receipt_report = PlayerFeatureReceiptsReport(
        rows=[
            _receipt("Luther Burden", "WR", "private_lve_value", "role_security", 12.0),
            _receipt(
                "Luther Burden",
                "WR",
                "private_lve_value",
                "draft_capital_prior_score",
                0.0,
                section="Young-Player Bridge Prior",
                normalized=81.0,
            ),
            _receipt(
                "Luther Burden",
                "WR",
                "private_lve_value",
                "young_nfl_bridge_prior",
                9.0,
                section="Young-Player Bridge Prior",
            ),
            _receipt(
                "Luther Burden",
                "WR",
                "private_lve_value",
                "lve_structural_formula_adjustment",
                -4.0,
            ),
        ],
        component_summary_rows=[],
        players=["Luther Burden"],
        components=["private_lve_value"],
        issues=[],
        source_root="test",
    )

    receipts = build_my_team_decision_receipts(team_rows, receipt_report)

    assert receipts[0]["top_five_rule"] == "Required Top-Five Release Slot"
    assert receipts[0]["model_recommendation"] == "shop/release"
    assert "limited NFL evidence" in receipts[0]["lifecycle_explanation"]
    assert "Required Top-Five Release Slot" in receipts[0]["release_pain_explanation"]
    assert "Model recommendation: shop/release" in receipts[0]["release_pain_explanation"]
    assert "role security: 12.00" in receipts[0]["stats_value_drivers"]
    assert "role security: 12.00" in receipts[0]["model_value_drivers"]
    assert "role security: 12.00" in receipts[0]["top_positive_drivers"]
    assert "LVE structural adjustment: -4.00" in receipts[0]["top_negative_drivers"]
    assert "draft/prospect prior 81.0" in receipts[0]["bridge_prior"]
    assert "bridge contribution 9.00" in receipts[0]["bridge_prior"]
    assert receipts[0]["market_edge"] == "Model vs market 4.50."
    assert receipts[0]["confidence_label"] == "review"
    assert "Review confidence" in receipts[0]["confidence_explanation"]
    assert "Score 76.0" in receipts[0]["confidence_explanation"]


def test_my_team_decision_receipts_explain_non_top_five_player_without_release_pain() -> None:
    team_rows = [
        {
            "player": "Bench WR",
            "pos": "WR",
            "asset_lifecycle_label": "Established Veteran",
            "top_five_rule": "Not in Roster's League-Rank Top Five",
            "model_recommendation": "shop",
            "top_five_rule_note": "League-rank rule does not apply to this player.",
            "market_value_status": "neutral_market_placeholder",
            "confidence": 62.0,
        }
    ]
    receipt_report = PlayerFeatureReceiptsReport(
        rows=[
            _receipt(
                "Bench WR",
                "WR",
                "private_lve_value",
                "weighted_recent_lve_ppg_score",
                8.5,
            )
        ],
        component_summary_rows=[],
        players=["Bench WR"],
        components=["private_lve_value"],
        issues=[],
        source_root="test",
    )

    receipts = build_my_team_decision_receipts(team_rows, receipt_report)

    assert receipts[0]["top_five_rule"] == "Not in Roster's League-Rank Top Five"
    assert receipts[0]["model_recommendation"] == "shop"
    assert "Top-Five Rule Status: Not in Roster's League-Rank Top Five" in (
        receipts[0]["release_pain_explanation"]
    )
    assert "No young-player bridge prior scored." == receipts[0]["bridge_prior"]
    assert receipts[0]["market_edge"] == (
        "Trade market unavailable; no Model vs Market edge is trusted."
    )
    assert receipts[0]["confidence_label"] == "weak"
    assert "Weak confidence" in receipts[0]["confidence_explanation"]


def test_my_team_decision_receipts_match_receipt_rows_with_suffix_difference() -> None:
    team_rows = [
        {
            "player": "Brian Thomas",
            "pos": "WR",
            "asset_lifecycle_label": "Young NFL Bridge",
            "top_five_rule": "Roster Top-Five Protected Slot",
            "model_recommendation": "keep",
            "confidence": 84.0,
        }
    ]
    receipt_report = PlayerFeatureReceiptsReport(
        rows=[
            _receipt(
                "Brian Thomas Jr.",
                "WR",
                "private_lve_value",
                "role_security",
                11.5,
            )
        ],
        component_summary_rows=[],
        players=["Brian Thomas Jr."],
        components=["private_lve_value"],
        issues=[],
        source_root="test",
    )

    receipts = build_my_team_decision_receipts(team_rows, receipt_report)

    assert "role security: 11.50" in receipts[0]["stats_value_drivers"]


def test_my_team_decision_receipts_cover_every_active_niners_player() -> None:
    pack = Path("local_exports/data_packs/lve_sleeper_20260505_pdf_ranks")
    board = build_team_command_board(pack)
    receipt_report = build_player_feature_receipts(
        pack,
        veteran_model_dir=DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    )

    receipts = build_my_team_decision_receipts(board.roster_rows, receipt_report)

    assert len(receipts) == len(board.roster_rows) == 24
    assert {receipt["player"] for receipt in receipts} == {
        row["player"] for row in board.roster_rows
    }
    for receipt in receipts:
        assert receipt["lifecycle_explanation"]
        assert receipt["top_positive_drivers"]
        assert receipt["top_negative_drivers"]
        assert receipt["confidence_explanation"]
        assert receipt["confidence_label"] in {
            "strong",
            "usable",
            "review",
            "weak",
            "blocked",
        }
        assert receipt["source_warnings"]


def _receipt(
    player: str,
    position: str,
    component: str,
    feature: str,
    contribution: float,
    *,
    section: str = "NFL Production",
    normalized: float = 70.0,
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "component": component,
        "formula_feature_name": feature,
        "receipt_section_label": section,
        "raw_feature_value": normalized,
        "normalized_score": normalized,
        "feature_weight": 20,
        "contribution": contribution,
        "warning_reason": "",
        "warning_status": "",
    }
