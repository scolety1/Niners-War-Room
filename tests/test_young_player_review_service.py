from __future__ import annotations

import csv
from pathlib import Path

from src.services.young_player_review_service import build_young_player_review


def test_young_player_review_flags_every_review_type(tmp_path: Path) -> None:
    _write_rows(
        tmp_path / "stats_first_normalized_features.csv",
        [
            _normalized_row(
                "strong_prior",
                "Strong Prior",
                draft_year="2025",
                draft_round="2",
                draft_overall="40",
                warnings="missing_lve_scoring_history|missing_projection_features|missing_role_usage",
                confidence="30",
            ),
            _normalized_row(
                "weak_prior",
                "Weak Prior",
                draft_year="2024",
                draft_round="6",
                draft_overall="210",
                private_stat_value="72",
                confidence="95",
            ),
            _normalized_row(
                "missing_capital",
                "Missing Capital",
                draft_year="",
                draft_round="",
                draft_overall="",
                young_prior="",
                confidence="80",
            ),
            _normalized_row(
                "missing_evidence",
                "Missing Evidence",
                draft_year="2025",
                draft_round="3",
                draft_overall="90",
                warnings="missing_lve_scoring_history|missing_projection_features|missing_role_usage",
                confidence="20",
            ),
            _normalized_row(
                "bridge_dominant",
                "Bridge Dominant",
                draft_year="2025",
                draft_round="1",
                draft_overall="20",
                confidence="80",
            ),
        ],
    )
    _write_rows(
        tmp_path / "stats_first_veteran_model_preview_outputs.csv",
        [
            _output_row("strong_prior", "Strong Prior", 61, 30),
            _output_row("weak_prior", "Weak Prior", 72, 95),
            _output_row("missing_capital", "Missing Capital", 55, 80),
            _output_row("missing_evidence", "Missing Evidence", 54, 20),
            _output_row("bridge_dominant", "Bridge Dominant", 78, 80),
        ],
    )
    _write_rows(
        tmp_path / "stats_first_feature_contributions.csv",
        [
            _contribution_row("strong_prior", "Strong Prior", "young_nfl_bridge_prior", 18),
            _contribution_row("weak_prior", "Weak Prior", "weighted_recent_lve_ppg_score", 30),
            _contribution_row(
                "missing_capital",
                "Missing Capital",
                "weighted_recent_lve_ppg_score",
                20,
            ),
            _contribution_row("missing_evidence", "Missing Evidence", "young_nfl_bridge_prior", 10),
            _contribution_row("bridge_dominant", "Bridge Dominant", "young_nfl_bridge_prior", 32),
            _contribution_row(
                "bridge_dominant",
                "Bridge Dominant",
                "weighted_recent_lve_ppg_score",
                40,
            ),
        ],
    )

    report = build_young_player_review(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=tmp_path,
    )

    flags_by_player = {
        str(row["player"]): set(str(row["flags"]).split("|")) for row in report.rows
    }
    assert "strong_prior_but_weak_nfl_evidence" in flags_by_player["Strong Prior"]
    assert "weak_prior_but_strong_nfl_evidence" in flags_by_player["Weak Prior"]
    assert "missing_draft_capital" in flags_by_player["Missing Capital"]
    assert "missing_nfl_evidence" in flags_by_player["Missing Evidence"]
    assert "bridge_contribution_too_dominant" in flags_by_player["Bridge Dominant"]
    assert {
        "strong_prior_but_weak_nfl_evidence",
        "weak_prior_but_strong_nfl_evidence",
        "missing_draft_capital",
        "missing_nfl_evidence",
        "bridge_contribution_too_dominant",
    }.issubset({str(row["flag_type"]) for row in report.flag_rows})
    assert any(row["metric"] == "flagged_players" for row in report.summary_rows)


def test_young_player_review_only_includes_year_one_two_three_players(tmp_path: Path) -> None:
    _write_rows(
        tmp_path / "stats_first_normalized_features.csv",
        [
            _normalized_row(
                "young",
                "Young Player",
                experience_bucket="year_two_nfl_player",
                draft_year="2024",
                draft_round="2",
                draft_overall="45",
            ),
            _normalized_row(
                "old",
                "Old Player",
                experience_bucket="established_veteran",
                draft_year="2020",
                draft_round="1",
                draft_overall="12",
            ),
        ],
    )
    _write_rows(
        tmp_path / "stats_first_veteran_model_preview_outputs.csv",
        [
            _output_row("young", "Young Player", 70, 88),
            _output_row("old", "Old Player", 90, 92),
        ],
    )
    _write_rows(
        tmp_path / "stats_first_feature_contributions.csv",
        [
            _contribution_row("young", "Young Player", "young_nfl_bridge_prior", 8),
            _contribution_row("old", "Old Player", "weighted_recent_lve_ppg_score", 40),
        ],
    )

    report = build_young_player_review(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=tmp_path,
    )

    assert [row["player"] for row in report.rows] == ["Young Player"]


def _normalized_row(
    player_id: str,
    player_name: str,
    *,
    position: str = "WR",
    team: str = "CHI",
    experience_bucket: str = "year_one_nfl_player",
    draft_year: str = "2025",
    draft_round: str = "2",
    draft_overall: str = "50",
    young_prior: str = "",
    private_stat_value: str = "60",
    confidence: str = "80",
    warnings: str = "",
) -> dict[str, str]:
    return {
        "season": "2026",
        "player_id": player_id,
        "player_name": player_name,
        "position": position,
        "team": team,
        "weighted_recent_lve_ppg_score": "" if "missing_lve_scoring_history" in warnings else "72",
        "expected_lve_points_score": "" if "missing_projection_features" in warnings else "70",
        "lve_projection_value": "" if "missing_projection_features" in warnings else "69",
        "role_security": "" if "missing_role_usage" in warnings else "68",
        "first_down_td_fit": "65",
        "age_curve": "85",
        "injury_durability": "75",
        "private_stat_value": private_stat_value,
        "market_liquidity": "50",
        "confidence": confidence,
        "warnings": warnings,
        "draft_year": draft_year,
        "draft_round": draft_round,
        "draft_overall": draft_overall,
        "experience_bucket": experience_bucket,
        "young_nfl_bridge_prior_score": young_prior,
        "young_nfl_bridge_source": "draft_capital_prior" if draft_year or draft_round else "",
        "young_nfl_bridge_weight": "",
    }


def _output_row(
    player_id: str,
    player_name: str,
    private_value: float,
    confidence: float,
) -> dict[str, str]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": "WR",
        "team": "CHI",
        "private_lve_value": str(private_value),
        "confidence_score": str(confidence),
        "warning_status": "review_only",
        "warning_reasons": "",
        "experience_bucket": "year_one_nfl_player",
        "young_nfl_bridge_prior_score": "",
        "young_nfl_bridge_weight": "",
        "young_nfl_bridge_source": "",
    }


def _contribution_row(
    player_id: str,
    player_name: str,
    feature_name: str,
    contribution: float,
) -> dict[str, str]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": "WR",
        "component": "private_lve_value",
        "feature_name": feature_name,
        "normalized_score": "80",
        "feature_weight": "20",
        "component_contribution": str(contribution),
        "model_version": "test",
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
