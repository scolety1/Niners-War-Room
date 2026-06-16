from __future__ import annotations

from src.services.nwr_outcome_scoring_service import (
    add_position_ranks,
    aggregate_season_scores,
    app_tier_labels,
    companion_labels,
    compute_weekly_replacement_lines,
    duplicate_player_week_keys,
    finish_flags,
    forbidden_input_violations,
    future_window_label,
    load_scoring_rules,
    score_player_week,
)


def test_weekly_score_equals_component_point_sum() -> None:
    scored = score_player_week(
        {
            "pass_yds": 300,
            "pass_td": 2,
            "pass_int": 1,
            "rush_yds": 40,
            "rush_td": 1,
            "rush_first_downs": 5,
            "receptions": 6,
            "rec_yds": 80,
            "rec_td": 1,
            "rec_first_downs": 4,
            "fumbles_lost": 1,
            "return_yds": 30,
        }
    )

    assert scored["pts_passing"] == 15.0
    assert scored["pts_rushing"] == 10.0
    assert scored["pts_receiving"] == 13.6
    assert scored["pts_turnovers"] == -1.0
    assert scored["pts_misc"] == 1.0
    assert scored["week_score_total"] == 38.6


def test_scoring_rules_load_from_versioned_config() -> None:
    rules = load_scoring_rules()

    assert rules.scoring_version_id == "nwr_1qb_nonppr_fd_v1"
    assert rules.pass_td_pt == 3.0
    assert rules.rec_pt == 0.0
    assert rules.rush_1d_pt == 0.4
    assert rules.qualified_games_min == 8


def test_season_total_equals_sum_and_qualified_ppg_min_games() -> None:
    rows = [
        {
            "season": 2025,
            "player_id": "wr_1",
            "player_name": "Proof Receiver",
            "position": "WR",
            "week_score_total": 10,
            "include_in_scoring": "true",
            "ppg_game_eligible": "true",
        }
        for _ in range(8)
    ]

    output = aggregate_season_scores(rows)

    assert len(output) == 1
    assert output[0]["season_total_score"] == 80
    assert output[0]["qualified_ppg"] == 10
    assert output[0]["ppg_game_count"] == 8


def test_duplicate_player_week_keys_are_detected() -> None:
    rows = [
        {"season": 2025, "week": 1, "player_id": "wr_1", "position": "WR"},
        {"season": 2025, "week": 1, "player_id": "wr_1", "position": "WR"},
    ]

    assert duplicate_player_week_keys(rows) == ("nwr_1qb_nonppr_fd_v1|2025|1|wr_1",)


def test_position_ranks_are_monotonic_by_score() -> None:
    rows = [
        {"season": 2025, "player_id": "wr_1", "position": "WR", "season_total_score": 10},
        {"season": 2025, "player_id": "wr_2", "position": "WR", "season_total_score": 30},
        {"season": 2025, "player_id": "wr_3", "position": "WR", "season_total_score": 20},
    ]

    ranked = add_position_ranks(
        rows,
        value_column="season_total_score",
        rank_column="season_total_rank_pos",
    )
    by_player = {row["player_id"]: row["season_total_rank_pos"] for row in ranked}

    assert by_player == {"wr_1": 3, "wr_2": 1, "wr_3": 2}


def test_k_rows_are_ignored_for_model_outcome_scoring() -> None:
    output = aggregate_season_scores(
        [
            {
                "season": 2025,
                "player_id": "k_1",
                "player_name": "Kicker",
                "position": "K",
                "week_score_total": 15,
            }
        ]
    )

    assert output == []


def test_finish_flags_and_app_tiers_are_coherent() -> None:
    flags = finish_flags("WR", total_rank=8, qualified_ppg_rank=13)
    tiers = app_tier_labels("WR", total_rank=8, qualified_ppg_rank=13)

    assert flags["total_top_12"] is True
    assert flags["qppg_top_12"] is False
    assert tiers["is_difference_maker"] is True
    assert tiers["is_starter"] is True
    assert tiers["is_useful"] is True


def test_bust_replacement_injury_and_ambiguous_labels_are_mutually_safe() -> None:
    replacement = companion_labels(opportunity_evidence=True, useful=False, replacement_level=True)
    injury = companion_labels(opportunity_evidence=True, useful=False, injury_lost=True)
    ambiguous = companion_labels(opportunity_evidence=True, useful=False, ambiguous=True)

    assert replacement["is_replacement_level"] is True
    assert replacement["is_bust"] is False
    assert injury["is_injury_lost"] is True
    assert injury["is_bust"] is False
    assert ambiguous["is_ambiguous"] is True
    assert ambiguous["is_bust"] is False


def test_future_window_labels_are_null_when_right_censored() -> None:
    assert (
        future_window_label(
            anchor_season=2024,
            latest_observed_season=2026,
            window_years=3,
            observed_value=False,
        )
        is None
    )
    assert (
        future_window_label(
            anchor_season=2023,
            latest_observed_season=2026,
            window_years=3,
            observed_value=False,
        )
        is False
    )


def test_forbidden_public_market_fields_are_not_allowed_as_inputs() -> None:
    violations = forbidden_input_violations(
        (
            "private_pre_draft_feature",
            "market_rank",
            "legacy_private_score",
            "rotowire_values",
            "prior_fantasy_draft_history",
        )
    )

    assert "market_rank" in violations
    assert "private_score" in violations
    assert "rotowire_value" in violations
    assert "prior_fantasy_draft_history" in violations


def test_replacement_line_uses_score_thresholds_for_ties() -> None:
    rows = []
    for index in range(11):
        rows.append(
            {
                "season": 2025,
                "week": 1,
                "player_id": f"qb_{index}",
                "position": "QB",
                "week_score_total": 20 if index < 9 else 18,
            }
        )
    for position, count in (("RB", 30), ("WR", 40), ("TE", 20)):
        for index in range(count):
            rows.append(
                {
                    "season": 2025,
                    "week": 1,
                    "player_id": f"{position.lower()}_{index}",
                    "position": position,
                    "week_score_total": 10 - (index / 100),
                }
            )

    lines = compute_weekly_replacement_lines(rows)
    qb_line = next(row for row in lines if row["position"] == "QB")

    assert qb_line["required_line_score"] == 18
    assert qb_line["cutoff_tie_count"] == 2
    assert qb_line["data_quality_code"] == "computed_threshold_line"
    assert sum(row["flex_selected_count_position"] for row in lines) == 20
