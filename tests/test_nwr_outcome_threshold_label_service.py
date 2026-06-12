from __future__ import annotations

from src.services.nwr_outcome_threshold_label_service import (
    current_2026_prediction_feature_coverage_rows,
    direct_threshold_label_schema_rows,
    direct_threshold_labels_for_row,
    direct_threshold_support_rows,
    threshold_label_legality_audit_rows,
)


def test_direct_threshold_labels_are_position_specific() -> None:
    labels = direct_threshold_labels_for_row(
        {
            "position": "WR",
            "season_total_rank_pos": "8",
            "qualified_ppg_rank_pos": "13",
        }
    )

    assert labels["same_year_wr_t6"] is False
    assert labels["same_year_wr_t12"] is True
    assert labels["same_year_wr_t24"] is True
    assert labels["same_year_qb_t6"] is None
    assert labels["same_year_te_t3"] is None


def test_non_applicable_thresholds_are_null_not_false() -> None:
    labels = direct_threshold_labels_for_row(
        {
            "position": "QB",
            "season_total_rank_pos": "7",
            "qualified_ppg_rank_pos": "",
        }
    )

    assert labels["same_year_qb_t6"] is False
    assert labels["same_year_qb_t12"] is True
    assert labels["same_year_rb_t6"] is None
    assert labels["same_year_wr_t48"] is None


def test_label_legality_audit_blocks_public_fantasy_total_dependence() -> None:
    schema_text = " ".join(
        "|".join(row.values()) for row in direct_threshold_label_schema_rows()
    ).lower()
    audit = {row["audit"]: row for row in threshold_label_legality_audit_rows()}

    assert "fantasy_points" not in schema_text
    assert "public_fantasy_totals" in audit
    assert audit["public_fantasy_totals"]["status"] == "pass"
    assert "reconstructed_nwr_scoring_components" in schema_text


def test_support_rows_flag_sparse_position_targets() -> None:
    rows = [
        {"season": "2024", "position": "TE", "season_total_rank_pos": "1"},
        {"season": "2024", "position": "TE", "season_total_rank_pos": "2"},
        {"season": "2024", "position": "TE", "season_total_rank_pos": "30"},
    ]

    support = direct_threshold_support_rows(rows)
    t3 = next(row for row in support if row["target"] == "same_year_te_t3")

    assert t3["eligible_rows"] == 3
    assert t3["events"] == 2
    assert t3["non_events"] == 1
    assert t3["sparse_flag"] == "yes"


def test_2026_feature_coverage_blocks_forbidden_fields_and_old_names() -> None:
    rows = current_2026_prediction_feature_coverage_rows(
        [
            {
                "player": "Market Player",
                "position": "WR",
                "player_id": "p1",
                "market_rank": "10",
            },
            {
                "player": "Old Schema Player",
                "position": "RB",
                "player_id": "p2",
                "prior_nwr_ppg": "12.0",
            },
        ]
    )

    assert rows[0]["coverage_status"] == "blocked_forbidden_feature"
    assert "market_rank" in rows[0]["forbidden_feature_hits"]
    assert rows[1]["coverage_status"] == "blocked_old_ambiguous_feature_schema"
    assert "prior_nwr_ppg" in rows[1]["old_ambiguous_feature_hits"]


def test_rookies_without_legal_features_are_blocked_for_separate_head() -> None:
    row = current_2026_prediction_feature_coverage_rows(
        [{"player": "Rookie Back", "position": "RB", "is_rookie": "1"}]
    )[0]

    assert row["coverage_status"] == "blocked_rookie_requires_separate_head"
    assert row["legal_2026_prediction_features"] == "no"


def test_renamed_2026_feature_schema_can_pass_internal_coverage() -> None:
    row = {
        "player": "Legal Vet",
        "position": "WR",
        "player_id": "p3",
        "age_at_snapshot": "25.4",
        "experience_at_snapshot": "4",
        "prior_season_nwr_ppg": "11.2",
        "prior_season_nwr_finish_rank": "20",
        "prior_completed_season_games": "17",
        "prior_completed_season_games_played": "16",
        "prior_completed_season_games_active": "16",
        "prior_completed_season_rushing_first_downs": "0",
        "prior_completed_season_receiving_first_downs": "48",
        "prior_completed_season_receptions": "76",
        "prior_completed_season_rushing_yards": "0",
        "prior_completed_season_receiving_yards": "910",
        "prior_completed_season_passing_yards": "0",
    }

    coverage = current_2026_prediction_feature_coverage_rows([row])[0]

    assert coverage["coverage_status"] == "ready_internal_feature_row"
    assert coverage["legal_2026_prediction_features"] == "yes"
    assert coverage["missing_required_features"] == ""
