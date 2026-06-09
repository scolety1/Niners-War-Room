from __future__ import annotations

from src.services.young_nfl_bridge_service import (
    bridge_weight_for_bucket,
    decayed_bridge_weight,
    draft_capital_prior_score,
    experience_bucket,
    nfl_evidence_weight,
    young_nfl_bridge_prior_from_row,
)


def test_experience_bucket_decays_from_rookie_to_established() -> None:
    assert experience_bucket(season=2026, draft_year=2026) == "true_rookie"
    assert experience_bucket(season=2026, draft_year=2025) == "year_one_nfl_player"
    assert experience_bucket(season=2026, draft_year=2024) == "year_two_nfl_player"
    assert experience_bucket(season=2026, draft_year=2023) == "year_three_nfl_player"
    assert experience_bucket(season=2026, draft_year=2022) == "established_veteran"


def test_bridge_weight_fades_as_nfl_evidence_takes_over() -> None:
    assert bridge_weight_for_bucket("true_rookie") > bridge_weight_for_bucket(
        "year_one_nfl_player"
    )
    assert bridge_weight_for_bucket("year_one_nfl_player") > bridge_weight_for_bucket(
        "year_two_nfl_player"
    )
    assert bridge_weight_for_bucket("year_two_nfl_player") > bridge_weight_for_bucket(
        "year_three_nfl_player"
    )
    assert bridge_weight_for_bucket("established_veteran") == 0.0


def test_bridge_prior_outputs_year_specific_decay_weights() -> None:
    year_one = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "year_one",
            "player_name": "Year One",
            "position": "WR",
            "draft_year": "2025",
            "draft_round": "1",
            "draft_ovr": "20",
        }
    )
    year_two = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "year_two",
            "player_name": "Year Two",
            "position": "WR",
            "draft_year": "2024",
            "draft_round": "1",
            "draft_ovr": "20",
        }
    )
    year_three = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "year_three",
            "player_name": "Year Three",
            "position": "WR",
            "draft_year": "2023",
            "draft_round": "1",
            "draft_ovr": "20",
        }
    )
    established = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "established",
            "player_name": "Established",
            "position": "WR",
            "draft_year": "2022",
            "draft_round": "1",
            "draft_ovr": "20",
        }
    )

    assert year_one.experience_bucket == "year_one_nfl_player"
    assert year_two.experience_bucket == "year_two_nfl_player"
    assert year_three.experience_bucket == "year_three_nfl_player"
    assert established.experience_bucket == "established_veteran"
    assert year_one.bridge_weight > year_two.bridge_weight > year_three.bridge_weight
    assert established.bridge_weight == 0.0


def test_draft_capital_prior_scores_second_round_above_third_round() -> None:
    luther_prior = draft_capital_prior_score(
        position="WR",
        draft_round=2,
        draft_overall=39,
    )
    kaleb_prior = draft_capital_prior_score(
        position="RB",
        draft_round=3,
        draft_overall=83,
    )

    assert luther_prior > kaleb_prior
    assert 80 <= luther_prior <= 85
    assert 70 <= kaleb_prior <= 75


def test_young_bridge_prior_uses_draft_capital_without_fake_production() -> None:
    prior = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "12519",
            "player_name": "Luther Burden",
            "position": "WR",
            "draft_year": "2025",
            "draft_round": "2",
            "draft_ovr": "39",
        }
    )

    assert prior.experience_bucket == "year_one_nfl_player"
    assert prior.bridge_weight == 0.35
    assert prior.rookie_prior_score == 82.0
    assert prior.source == "draft_capital_prior"


def test_decayed_bridge_weight_falls_when_nfl_evidence_is_clear() -> None:
    missing_evidence = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "young_missing",
            "player_name": "Young Missing",
            "position": "WR",
            "draft_year": "2025",
            "draft_round": "2",
            "draft_ovr": "39",
            "weighted_recent_lve_ppg_score": "50",
            "expected_lve_points_score": "50",
            "lve_projection_value": "50",
            "role_security": "50",
            "confidence": "84",
            "warnings": (
                "missing_lve_scoring_history|missing_projection_features|"
                "missing_participation_proxy"
            ),
        }
    )
    clear_evidence = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "young_clear",
            "player_name": "Young Clear",
            "position": "WR",
            "draft_year": "2025",
            "draft_round": "2",
            "draft_ovr": "39",
            "weighted_recent_lve_ppg_score": "78",
            "expected_lve_points_score": "80",
            "lve_projection_value": "79",
            "role_security": "82",
            "confidence": "86",
            "warnings": "",
        }
    )

    assert missing_evidence.nfl_evidence_weight < 0.05
    assert missing_evidence.bridge_weight > 0.34
    assert clear_evidence.nfl_evidence_weight > 0.95
    assert clear_evidence.bridge_weight < missing_evidence.bridge_weight


def test_generated_bridge_weight_is_recomputed_from_nfl_evidence() -> None:
    prior = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "young_clear_generated",
            "player_name": "Young Clear Generated",
            "position": "WR",
            "draft_year": "2024",
            "draft_round": "1",
            "draft_ovr": "23",
            "young_nfl_bridge_weight": "0.20",
            "weighted_recent_lve_ppg_score": "86",
            "expected_lve_points_score": "87",
            "lve_projection_value": "86",
            "role_security": "84",
            "confidence": "88",
            "warnings": "",
        }
    )

    assert prior.experience_bucket == "year_two_nfl_player"
    assert prior.nfl_evidence_weight > 0.95
    assert prior.bridge_weight < 0.12


def test_manual_bridge_weight_override_is_explicit_only() -> None:
    prior = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "young_manual",
            "player_name": "Young Manual",
            "position": "WR",
            "draft_year": "2024",
            "draft_round": "1",
            "draft_ovr": "23",
            "young_nfl_bridge_weight": "0.20",
            "young_nfl_bridge_weight_source": "manual_override",
            "weighted_recent_lve_ppg_score": "86",
            "expected_lve_points_score": "87",
            "lve_projection_value": "86",
            "role_security": "84",
            "confidence": "88",
            "warnings": "",
        }
    )

    assert prior.nfl_evidence_weight > 0.95
    assert prior.bridge_weight == 0.20


def test_established_veteran_ignores_leaked_generated_bridge_weight() -> None:
    prior = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "established_with_leak",
            "player_name": "Established With Leak",
            "position": "WR",
            "draft_year": "2022",
            "draft_round": "1",
            "draft_ovr": "18",
            "young_nfl_bridge_weight": "0.35",
            "weighted_recent_lve_ppg_score": "86",
            "expected_lve_points_score": "87",
            "lve_projection_value": "86",
            "role_security": "84",
            "confidence": "88",
            "warnings": "",
        }
    )

    assert prior.experience_bucket == "established_veteran"
    assert prior.bridge_weight == 0.0


def test_incoming_rookie_uses_full_rookie_context_weight() -> None:
    prior = young_nfl_bridge_prior_from_row(
        {
            "season": "2026",
            "player_id": "incoming_rb",
            "player_name": "Incoming RB",
            "position": "RB",
            "draft_year": "2026",
            "draft_round": "1",
            "draft_ovr": "12",
            "weighted_recent_lve_ppg_score": "90",
            "role_security": "90",
            "confidence": "90",
        }
    )

    assert prior.experience_bucket == "true_rookie"
    assert prior.bridge_weight == 1.0
    assert decayed_bridge_weight(bucket="true_rookie", nfl_evidence_weight=1.0) == 1.0


def test_nfl_evidence_weight_respects_missing_source_warnings() -> None:
    row = {
        "weighted_recent_lve_ppg_score": "90",
        "expected_lve_points_score": "90",
        "lve_projection_value": "90",
        "role_security": "90",
        "confidence": "90",
        "warnings": "missing_lve_scoring_history|missing_projection_features",
    }

    assert nfl_evidence_weight(row) < 0.50
