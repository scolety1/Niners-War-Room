from __future__ import annotations

from pathlib import Path

from src.services.historical_rookie_replay_service import (
    NO_FUTURE_STATS_POLICY,
    OUTCOME_CATEGORY_VALUES,
    RANKING_FEATURE_FIELDS,
    build_historical_rookie_replay_report,
)

PREDRAFT_FIXTURE = "sample_data/historical_rookie_replay/pre_draft_prospect_inputs.csv"
OUTCOME_FIXTURE = "sample_data/historical_rookie_replay/post_draft_outcomes.csv"


def test_historical_rookie_replay_displays_top_20_by_year() -> None:
    report = build_historical_rookie_replay_report(PREDRAFT_FIXTURE, OUTCOME_FIXTURE)

    assert report.years == [2022, 2023, 2024]
    assert {row["draft_year"] for row in report.summary_rows} == {2022, 2023, 2024}
    assert [row["top_prospect_rows"] for row in report.summary_rows] == [20, 20, 20]

    rows_2024 = [row for row in report.top20_rows if row["draft_year"] == 2024]
    assert len(rows_2024) == 20
    assert rows_2024[0]["model_rank"] == 1
    assert rows_2024[0]["future_nfl_stats_used"] is False


def test_metadata_declares_no_future_nfl_stats_used() -> None:
    report = build_historical_rookie_replay_report(PREDRAFT_FIXTURE, OUTCOME_FIXTURE)
    metadata = {row["metadata_key"]: row["metadata_value"] for row in report.metadata_rows}

    assert metadata["ranking_input_scope"] == NO_FUTURE_STATS_POLICY
    assert metadata["future_nfl_stats_used_in_ranking"] is False
    assert metadata["outcome_join_policy"] == "display_after_ranking_only"


def test_outcome_labels_cover_required_hit_rate_categories() -> None:
    report = build_historical_rookie_replay_report(PREDRAFT_FIXTURE, OUTCOME_FIXTURE)
    categories = {
        row["outcome_category"]
        for row in report.outcome_rows
        if row["outcome_loaded"]
    }

    assert set(OUTCOME_CATEGORY_VALUES).issubset(categories)


def test_hit_rate_reports_calculate_top_windows() -> None:
    report = build_historical_rookie_replay_report(PREDRAFT_FIXTURE, OUTCOME_FIXTURE)
    rows_2023 = {
        row["rank_window"]: row
        for row in report.hit_rate_rows
        if row["draft_year"] == 2023 and row["scope"] == "overall"
    }

    assert rows_2023["top_5"]["ranked_count"] == 5
    assert rows_2023["top_5"]["labeled_count"] == 5
    assert rows_2023["top_5"]["hit_count"] == 5
    assert rows_2023["top_5"]["hit_rate"] == 1.0
    assert rows_2023["top_20"]["ranked_count"] == 20
    assert rows_2023["top_20"]["hit_count"] == 13
    assert rows_2023["top_20"]["hit_rate"] == 0.65
    assert rows_2023["top_20"]["ranking_input"] is False


def test_hit_rate_reports_break_out_by_position() -> None:
    report = build_historical_rookie_replay_report(PREDRAFT_FIXTURE, OUTCOME_FIXTURE)
    qb_2022_top5 = next(
        row
        for row in report.position_hit_rate_rows
        if row["draft_year"] == 2022
        and row["position"] == "QB"
        and row["rank_window"] == "top_5"
    )

    assert qb_2022_top5["scope"] == "position"
    assert qb_2022_top5["ranked_count"] == 3
    assert qb_2022_top5["hit_count"] == 0
    assert qb_2022_top5["hit_rate"] == 0.0


def test_model_win_and_miss_reports_are_review_only() -> None:
    report = build_historical_rookie_replay_report(PREDRAFT_FIXTURE, OUTCOME_FIXTURE)

    assert any(row["player_name"] == "Breece Hall" for row in report.model_win_rows)
    assert any(row["review_type"] == "model_overrated_miss" for row in report.model_miss_rows)
    assert all(row["ranking_input"] is False for row in report.model_win_rows)
    assert all(row["ranking_input"] is False for row in report.model_miss_rows)


def test_predraft_feature_receipts_do_not_include_outcome_fields() -> None:
    report = build_historical_rookie_replay_report(PREDRAFT_FIXTURE, OUTCOME_FIXTURE)

    forbidden_fragments = ("outcome", "rookie_year", "year2", "year3", "best_lve")
    assert report.feature_rows
    for row in report.feature_rows:
        assert row["future_nfl_stats_used"] is False
        assert all(fragment not in row["feature_name"] for fragment in forbidden_fragments)
        assert "hit_label" not in row
        assert "best_lve_ppg" not in row


def test_ranking_feature_contract_excludes_post_draft_outcome_fields() -> None:
    forbidden_fragments = ("outcome", "rookie_year", "year2", "year3", "best_lve", "top24")

    for feature_name in RANKING_FEATURE_FIELDS:
        assert all(fragment not in feature_name for fragment in forbidden_fragments)


def test_outcome_file_changes_do_not_change_prospect_ranking(tmp_path: Path) -> None:
    predraft_path = tmp_path / "pre_draft_prospect_inputs.csv"
    first_outcome_path = tmp_path / "outcomes_a.csv"
    second_outcome_path = tmp_path / "outcomes_b.csv"
    predraft_path.write_text(
        "\n".join(
            [
                "draft_year,prospect_id,player_name,position,school,as_of_date,source,"
                "draft_capital_score,age_trajectory_score,production_score,efficiency_score,"
                "target_earning_score,rushing_profile_score,receiving_role_score,"
                "athleticism_score,lve_position_fit_score,confidence_score,source_notes",
                "2020,player_a,Player A,WR,Alpha,2020-04-25,test,90,85,90,88,"
                "92,50,50,80,92,90,Fixture row.",
                "2020,player_b,Player B,WR,Beta,2020-04-25,test,70,75,74,72,"
                "70,50,50,78,84,90,Fixture row.",
            ]
        ),
        encoding="utf-8",
    )
    first_outcome_path.write_text(
        "\n".join(
            [
                "draft_year,prospect_id,nfl_team,nfl_draft_pick,rookie_year_lve_ppg,"
                "year2_lve_ppg,year3_lve_ppg,best_lve_ppg,top24_seasons,hit_label,outcome_notes",
                "2020,player_a,AAA,1,1,1,1,1,0,miss,Outcome should not demote Player A.",
                "2020,player_b,BBB,2,30,30,30,30,3,smash,Outcome should not promote Player B.",
            ]
        ),
        encoding="utf-8",
    )
    second_outcome_path.write_text(
        "\n".join(
            [
                "draft_year,prospect_id,nfl_team,nfl_draft_pick,rookie_year_lve_ppg,"
                "year2_lve_ppg,year3_lve_ppg,best_lve_ppg,top24_seasons,hit_label,outcome_notes",
                "2020,player_a,AAA,1,30,30,30,30,3,smash,Outcome should not matter.",
                "2020,player_b,BBB,2,1,1,1,1,0,miss,Outcome should not matter.",
            ]
        ),
        encoding="utf-8",
    )

    first_report = build_historical_rookie_replay_report(predraft_path, first_outcome_path)
    second_report = build_historical_rookie_replay_report(predraft_path, second_outcome_path)

    first_order = [row["player_name"] for row in first_report.top20_rows]
    second_order = [row["player_name"] for row in second_report.top20_rows]
    assert first_order == ["Player A", "Player B"]
    assert second_order == first_order
    assert first_report.top20_rows[0]["outcome_category"] == "bust"
    assert second_report.top20_rows[0]["outcome_category"] == "fantasy_difference_maker"
    assert first_report.top20_rows[0]["best_lve_ppg_after_draft"] == 1.0
    assert second_report.top20_rows[0]["best_lve_ppg_after_draft"] == 30.0
    assert all(row["ranking_input"] is False for row in first_report.hit_rate_rows)
