from __future__ import annotations

from types import SimpleNamespace

import src.services.lifecycle_audit_service as service

BRIDGE_EXPLANATION = "This player is being treated as a young NFL bridge asset because..."


def test_lifecycle_audit_flags_suspicious_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "build_draft_room",
        lambda *_args, **_kwargs: SimpleNamespace(
            combined_rows=[
                {
                    "player": "Missing Lifecycle Rookie",
                    "position": "WR",
                    "team": "Rookie Pool",
                    "asset_type": "rookie",
                }
            ]
        ),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                _receipt_row(
                    "Incoming Rookie Error",
                    "WR",
                    "incoming_rookie",
                    "Incoming Rookie",
                    "weighted_recent_lve_ppg_score",
                    "NFL Production",
                ),
                _receipt_row(
                    "Young Missing Bridge",
                    "WR",
                    "young_nfl_bridge",
                    "Young NFL Bridge",
                    "weighted_recent_lve_ppg_score",
                    "NFL Production",
                ),
                _receipt_row(
                    "Old Draft Capital",
                    "RB",
                    "established_veteran",
                    "Established Veteran",
                    "draft_capital_prior_score",
                    "Young-Player Bridge Prior",
                    weight=8,
                    contribution=6,
                ),
            ],
        ),
    )

    report = service.build_lifecycle_audit("pack")

    warning_types = {row["warning_type"] for row in report.suspicious_rows}
    assert warning_types == {
        "incoming_rookie_on_veteran_board",
        "young_nfl_player_missing_bridge_prior",
        "established_veteran_with_draft_capital_prior",
        "draftable_player_missing_asset_lifecycle",
    }
    assert report.has_blockers is True


def test_lifecycle_audit_counts_and_passes_clean_lanes(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "build_draft_room",
        lambda *_args, **_kwargs: SimpleNamespace(
            combined_rows=[
                {
                    "player": "Clean Rookie",
                    "position": "WR",
                    "team": "Rookie Pool",
                    "asset_type": "rookie",
                    "asset_lifecycle": "incoming_rookie",
                    "asset_lifecycle_label": "Incoming Rookie",
                },
                {
                    "player": "Available Veteran",
                    "position": "RB",
                    "team": "Available",
                    "asset_type": "free_agent",
                    "asset_lifecycle": "free_agent",
                    "asset_lifecycle_label": "Free Agent",
                },
            ]
        ),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                *_bridge_receipts("Young Clean Bridge"),
                _receipt_row(
                    "Established Clean Veteran",
                    "WR",
                    "established_veteran",
                    "Established Veteran",
                    "weighted_recent_lve_ppg_score",
                    "NFL Production",
                    weight=20,
                    contribution=12,
                ),
            ],
        ),
    )

    report = service.build_lifecycle_audit("pack")

    assert report.suspicious_rows == []
    count_lookup = {
        row["asset_lifecycle_label"]: row["players"] for row in report.count_rows
    }
    assert count_lookup["Incoming Rookie"] == 1
    assert count_lookup["Young NFL Bridge"] == 1
    assert count_lookup["Established Veteran"] == 1
    assert count_lookup["Free Agent"] == 1


def _bridge_receipts(player: str) -> list[dict[str, object]]:
    return [
        _receipt_row(
            player,
            "WR",
            "young_nfl_bridge",
            "Young NFL Bridge",
            feature,
            "Young-Player Bridge Prior",
            explanation=BRIDGE_EXPLANATION,
        )
        for feature in service.BRIDGE_RECEIPT_FEATURES
    ]


def _receipt_row(
    player: str,
    position: str,
    lifecycle: str,
    lifecycle_label: str,
    feature: str,
    section: str,
    *,
    weight: float = 0,
    contribution: float = 0,
    explanation: str = "",
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "team": "Test",
        "asset_lifecycle": lifecycle,
        "asset_lifecycle_label": lifecycle_label,
        "formula_feature_name": feature,
        "receipt_section_label": section,
        "feature_weight": weight,
        "contribution": contribution,
        "warning_reason": "",
        "warning_status": "",
        "lifecycle_explanation": explanation,
    }
