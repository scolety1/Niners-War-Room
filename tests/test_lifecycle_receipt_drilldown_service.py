from __future__ import annotations

from src.services.lifecycle_receipt_drilldown_service import (
    build_lifecycle_receipt_drilldown,
)
from src.services.player_feature_receipts_service import PlayerFeatureReceiptsReport


def test_lifecycle_receipt_drilldown_groups_sections_and_reconciles_totals() -> None:
    report = PlayerFeatureReceiptsReport(
        rows=[
            _receipt_row(
                "Luther Burden",
                "WR",
                "NFL Production",
                "private_lve_value",
                "weighted_recent_lve_ppg_score",
                12.0,
            ),
            _receipt_row(
                "Luther Burden",
                "WR",
                "Role/Usage",
                "private_lve_value",
                "role_security",
                11.0,
            ),
            _receipt_row(
                "Luther Burden",
                "WR",
                "Young-Player Bridge Prior",
                "private_lve_value",
                "young_nfl_bridge_prior",
                14.0,
                raw_value=82,
                weight=35,
            ),
            _receipt_row(
                "Luther Burden",
                "WR",
                "Market/Liquidity",
                "trade_value",
                "market_liquidity",
                0.0,
            ),
        ],
        component_summary_rows=[
            {
                "player": "Luther Burden",
                "position": "WR",
                "component": "private_lve_value",
                "component_score": 37.0,
                "contribution_sum": 37.0,
                "reconciliation_status": "matched",
            },
            {
                "player": "Luther Burden",
                "position": "WR",
                "component": "trade_value",
                "component_score": 0.0,
                "contribution_sum": 0.0,
                "reconciliation_status": "matched",
            },
        ],
        players=["Luther Burden"],
        components=["private_lve_value", "trade_value"],
        issues=[],
        source_root="test",
    )

    drilldown = build_lifecycle_receipt_drilldown(report, "Luther Burden")

    assert drilldown.issues == []
    assert drilldown.lifecycle_label == "Young NFL Bridge"
    assert "young NFL bridge asset" in drilldown.lifecycle_explanation
    assert sum(float(row["section_contribution"]) for row in drilldown.section_rows) == 37.0
    private_reconciliation = [
        row
        for row in drilldown.component_reconciliation_rows
        if row["component"] == "private_lve_value"
    ][0]
    assert private_reconciliation["section_total_sum"] == 37.0
    assert private_reconciliation["receipt_contribution_sum"] == 37.0
    assert private_reconciliation["status"] == "matched"
    assert drilldown.bridge_rows == [
        {
            "bridge_item": "Final bridge contribution",
            "feature": "young_nfl_bridge_prior",
            "raw_value": 82,
            "normalized_score": 82,
            "feature_weight": 35,
            "contribution": 14.0,
            "source": "test_features.csv",
            "warning": "",
        }
    ]


def test_lifecycle_receipt_drilldown_marks_established_veteran_draft_capital_not_scored() -> None:
    report = PlayerFeatureReceiptsReport(
        rows=[
            _receipt_row(
                "Lamar Jackson",
                "QB",
                "NFL Production",
                "private_lve_value",
                "weighted_recent_lve_ppg_score",
                28.0,
                lifecycle_label="Established Veteran",
                lifecycle_explanation=(
                    "This player is being treated as established veteran; current NFL "
                    "stats explain the score."
                ),
            )
        ],
        component_summary_rows=[
            {
                "player": "Lamar Jackson",
                "position": "QB",
                "component": "private_lve_value",
                "component_score": 28.0,
                "contribution_sum": 28.0,
                "reconciliation_status": "matched",
            }
        ],
        players=["Lamar Jackson"],
        components=["private_lve_value"],
        issues=[],
        source_root="test",
    )

    drilldown = build_lifecycle_receipt_drilldown(report, "Lamar Jackson")

    assert drilldown.lifecycle_label == "Established Veteran"
    assert "Draft capital not scored for established veterans." in (
        drilldown.lifecycle_explanation
    )
    assert drilldown.bridge_rows == []
    assert drilldown.component_reconciliation_rows[0]["status"] == "matched"


def _receipt_row(
    player: str,
    position: str,
    section: str,
    component: str,
    feature_name: str,
    contribution: float,
    *,
    raw_value: object = 70,
    normalized_score: object = 82,
    weight: object = 20,
    lifecycle_label: str = "Young NFL Bridge",
    lifecycle_explanation: str = (
        "This player is being treated as a young NFL bridge asset because he is "
        "classified as a year-one NFL player."
    ),
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "asset_lifecycle_label": lifecycle_label,
        "receipt_section_label": section,
        "lifecycle_explanation": lifecycle_explanation,
        "component": component,
        "formula_feature_name": feature_name,
        "raw_feature_value": raw_value,
        "normalized_score": normalized_score,
        "feature_weight": weight,
        "contribution": contribution,
        "source_file": "test_features.csv",
        "warning_reason": "",
        "imputed_flag": False,
    }
