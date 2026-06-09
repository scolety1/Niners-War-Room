from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import src.services.roster_decision_readiness_service as service
from src.services.roster_decision_readiness_service import (
    build_roster_decision_readiness,
    roster_decision_gate_rows,
    roster_decision_summary_row,
)


def test_roster_readiness_can_pass_before_released_veterans_are_loaded(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(service, "model_v4_rebuild_freeze_active", lambda: False)
    _write_csv(
        tmp_path / "stats_first_veteran_model_preview_outputs.csv",
        [
            {"player_id": "young_wr", "player_name": "Young WR"},
            {"player_id": "veteran_rb", "player_name": "Veteran RB"},
        ],
    )
    monkeypatch.setattr(
        service,
        "validate_data_pack",
        lambda _: _validated_pack(),
    )
    monkeypatch.setattr(
        service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            missing_critical_rows=[],
            player_rows=[
                {"player_id": "young_wr", "player": "Young WR", "coverage_status": "ready"},
                {
                    "player_id": "veteran_rb",
                    "player": "Veteran RB",
                    "coverage_status": "ready",
                },
            ],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_identity_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            blocked_rows=[],
            rows=[
                {"player_id": "young_wr", "player": "Young WR", "audit_status": "ready"},
                {"player_id": "veteran_rb", "player": "Veteran RB", "audit_status": "ready"},
            ],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                _receipt("young_wr", "Young WR", "young_nfl_bridge", "draft_capital_prior_score"),
                _receipt(
                    "young_wr",
                    "Young WR",
                    "young_nfl_bridge",
                    "young_nfl_bridge_decay_weight",
                ),
                _receipt(
                    "young_wr",
                    "Young WR",
                    "young_nfl_bridge",
                    "young_nfl_bridge_nfl_evidence_weight",
                ),
                _receipt("young_wr", "Young WR", "young_nfl_bridge", "young_nfl_bridge_prior"),
                _receipt(
                    "veteran_rb",
                    "Veteran RB",
                    "established_veteran",
                    "weighted_recent_lve_ppg_score",
                ),
            ],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_model_outlier_report",
        lambda *_args, **_kwargs: SimpleNamespace(issues=[], rows=[]),
    )
    monkeypatch.setattr(
        service,
        "build_team_command_board",
        lambda *_args, **_kwargs: SimpleNamespace(
            roster_rows=[
                {"player": "Young WR", "team_section": "Core Holds", "confidence": 88.0},
                {"player": "Veteran RB", "team_section": "Bubble Players", "confidence": 80.0},
            ]
        ),
    )

    report = build_roster_decision_readiness(
        "pack_without_released_veterans",
        veteran_model_dir=tmp_path,
    )

    assert report.passed is True
    assert report.badge == "Roster Decisions Ready"
    summary = roster_decision_summary_row(report)
    assert summary["roster_decision_ready"] is True
    assert "released veterans do not block" in summary["draft_day_note"]
    gates = {row["requirement"]: row for row in roster_decision_gate_rows(report)}
    assert gates["Current rosters loaded"]["status"] == "ready"
    assert gates["League ranks loaded"]["status"] == "ready"


def test_roster_readiness_is_review_only_during_model_v4_freeze(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _stub_ready_roster_readiness(monkeypatch, tmp_path)

    report = build_roster_decision_readiness(
        "pack_during_model_v4_freeze",
        veteran_model_dir=tmp_path,
    )

    assert report.passed is False
    assert report.badge == "Roster Decisions Review Only"
    freeze_gate = next(check for check in report.checks if check.gate == "model_v4_rebuild_freeze")
    assert freeze_gate.status == "review"
    assert "Legacy roster action buckets" in freeze_gate.detail


def test_roster_readiness_blocks_without_stats_first_outputs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(service, "validate_data_pack", lambda _: _validated_pack())
    monkeypatch.setattr(
        service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            missing_critical_rows=[],
            player_rows=[],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_identity_audit",
        lambda *_args, **_kwargs: SimpleNamespace(issues=[], blocked_rows=[], rows=[]),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(issues=[], rows=[]),
    )
    monkeypatch.setattr(
        service,
        "build_model_outlier_report",
        lambda *_args, **_kwargs: SimpleNamespace(issues=[], rows=[]),
    )
    monkeypatch.setattr(
        service,
        "build_team_command_board",
        lambda *_args, **_kwargs: SimpleNamespace(roster_rows=[]),
    )

    report = build_roster_decision_readiness("pack", veteran_model_dir=tmp_path)

    assert report.passed is False
    assert report.badge == "Roster Decisions Need Data"
    output_gate = next(
        check for check in report.checks if check.gate == "stats_first_veteran_outputs_present"
    )
    assert output_gate.status == "blocked"


def test_roster_readiness_reviews_low_confidence_active_rows(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_csv(
        tmp_path / "stats_first_veteran_model_preview_outputs.csv",
        [{"player_id": "young_wr", "player_name": "Young WR"}],
    )
    monkeypatch.setattr(service, "validate_data_pack", lambda _: _validated_pack())
    monkeypatch.setattr(
        service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            missing_critical_rows=[],
            player_rows=[
                {"player_id": "young_wr", "player": "Young WR", "coverage_status": "ready"},
            ],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_identity_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            blocked_rows=[],
            rows=[{"player_id": "young_wr", "player": "Young WR", "audit_status": "ready"}],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                _receipt("young_wr", "Young WR", "young_nfl_bridge", "draft_capital_prior_score"),
                _receipt(
                    "young_wr",
                    "Young WR",
                    "young_nfl_bridge",
                    "young_nfl_bridge_decay_weight",
                ),
                _receipt(
                    "young_wr",
                    "Young WR",
                    "young_nfl_bridge",
                    "young_nfl_bridge_nfl_evidence_weight",
                ),
                _receipt("young_wr", "Young WR", "young_nfl_bridge", "young_nfl_bridge_prior"),
            ],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_model_outlier_report",
        lambda *_args, **_kwargs: SimpleNamespace(issues=[], rows=[]),
    )
    monkeypatch.setattr(
        service,
        "build_team_command_board",
        lambda *_args, **_kwargs: SimpleNamespace(
            roster_rows=[
                {"player": "Young WR", "team_section": "Needs Data Review", "confidence": 66.5}
            ]
        ),
    )

    report = build_roster_decision_readiness("pack", veteran_model_dir=tmp_path)

    assert report.passed is False
    assert report.badge == "Roster Decisions Review Only"
    quality_gate = next(
        check for check in report.checks if check.gate == "active_roster_output_quality_review"
    )
    assert quality_gate.status == "review"


def _stub_ready_roster_readiness(monkeypatch, tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "stats_first_veteran_model_preview_outputs.csv",
        [
            {"player_id": "young_wr", "player_name": "Young WR"},
            {"player_id": "veteran_rb", "player_name": "Veteran RB"},
        ],
    )
    monkeypatch.setattr(service, "validate_data_pack", lambda _: _validated_pack())
    monkeypatch.setattr(
        service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            missing_critical_rows=[],
            player_rows=[
                {"player_id": "young_wr", "player": "Young WR", "coverage_status": "ready"},
                {
                    "player_id": "veteran_rb",
                    "player": "Veteran RB",
                    "coverage_status": "ready",
                },
            ],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_identity_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            blocked_rows=[],
            rows=[
                {"player_id": "young_wr", "player": "Young WR", "audit_status": "ready"},
                {"player_id": "veteran_rb", "player": "Veteran RB", "audit_status": "ready"},
            ],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                _receipt("young_wr", "Young WR", "young_nfl_bridge", "draft_capital_prior_score"),
                _receipt(
                    "young_wr",
                    "Young WR",
                    "young_nfl_bridge",
                    "young_nfl_bridge_decay_weight",
                ),
                _receipt(
                    "young_wr",
                    "Young WR",
                    "young_nfl_bridge",
                    "young_nfl_bridge_nfl_evidence_weight",
                ),
                _receipt("young_wr", "Young WR", "young_nfl_bridge", "young_nfl_bridge_prior"),
                _receipt(
                    "veteran_rb",
                    "Veteran RB",
                    "established_veteran",
                    "weighted_recent_lve_ppg_score",
                ),
            ],
        ),
    )
    monkeypatch.setattr(
        service,
        "build_model_outlier_report",
        lambda *_args, **_kwargs: SimpleNamespace(issues=[], rows=[]),
    )
    monkeypatch.setattr(
        service,
        "build_team_command_board",
        lambda *_args, **_kwargs: SimpleNamespace(
            roster_rows=[
                {"player": "Young WR", "team_section": "Core Holds", "confidence": 88.0},
                {"player": "Veteran RB", "team_section": "Bubble Players", "confidence": 80.0},
            ]
        ),
    )


def _validated_pack() -> SimpleNamespace:
    return SimpleNamespace(
        has_errors=False,
        rows_by_table={
            "rosters": [
                _roster_row("young_wr", "Young WR", "WR", 10),
                _roster_row("veteran_rb", "Veteran RB", "RB", 20),
                _roster_row("ranked_qb", "Ranked QB", "QB", 30),
                _roster_row("ranked_te", "Ranked TE", "TE", 40),
                _roster_row("ranked_wr", "Ranked WR", "WR", 50),
            ],
            "official_rankings": [],
        },
    )


def _roster_row(player_id: str, player: str, position: str, rank: int) -> dict[str, object]:
    return {
        "team_id": "niners",
        "team_name": "Niners",
        "player_id": player_id,
        "player_name": player,
        "position": position,
        "league_rank": rank,
    }


def _receipt(
    player_id: str,
    player: str,
    lifecycle: str,
    feature_name: str,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player": player,
        "position": "WR",
        "asset_lifecycle": lifecycle,
        "formula_feature_name": feature_name,
        "feature_weight": 1,
        "contribution": 1,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
