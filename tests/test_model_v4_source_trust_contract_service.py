from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_source_trust_contract_service import (
    CLASSIFICATION_CONTEXT_ONLY,
    CLASSIFICATION_MARKET_CONTEXT_ONLY,
    CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
    CLASSIFICATION_REJECTED,
    CLASSIFICATION_SCORING_EVIDENCE,
    CLASSIFICATION_SOURCE_LIMITED,
    SOURCE_TRUST_CONTRACT_HEADER,
    build_source_trust_contract_rows,
    no_leakage_violations,
    row_for_field,
    write_source_trust_contract_outputs,
)


def test_source_trust_contract_covers_new_data_families() -> None:
    rows = build_source_trust_contract_rows()
    families = {str(row["source_family"]) for row in rows}

    required = {
        "rotowire_nfl_passing",
        "rotowire_nfl_rushing",
        "rotowire_nfl_receiving",
        "manual_first_down_exports",
        "manual_return_exports",
        "rotowire_snap_counts",
        "rotowire_receiver_alignment",
        "rotowire_te_route_data",
        "rotowire_target_leaders",
        "rotowire_raw_stat_projections",
        "fantasypros_adp",
        "rookie_adp_market",
        "kaggle_mock_drafts_big_boards",
        "nfl_draft_results",
        "cfbd_college_production",
        "cfbd_market_share",
        "rotowire_cfb_stats_targets",
        "third_party_combine_pro_day",
        "player_identity_crosswalk",
        "league_rank_rule_context",
        "trade_market_liquidity",
    }
    assert required <= families


def test_no_leakage_contract_has_no_private_value_violations() -> None:
    assert no_leakage_violations() == ()


def test_market_rankings_mocks_and_adp_are_market_context_only() -> None:
    rows = build_source_trust_contract_rows()
    market_rows = [
        row
        for row in rows
        if row["source_family"]
        in {
            "fantasypros_adp",
            "rookie_adp_market",
            "rotowire_rankings_and_cheatsheets",
            "rotowire_rookie_rankings",
            "kaggle_mock_drafts_big_boards",
            "trade_market_liquidity",
        }
    ]

    assert market_rows
    assert all(row["classification"] == CLASSIFICATION_MARKET_CONTEXT_ONLY for row in market_rows)
    assert all(row["private_football_value_allowed"] is False for row in market_rows)
    assert all(row["market_liquidity_allowed"] is True for row in market_rows)


def test_projections_cannot_drive_private_football_value() -> None:
    raw_projection = row_for_field(
        "rotowire_raw_stat_projections",
        "projected passing/rushing/receiving raw stats",
    )
    supplied_points = row_for_field(
        "external_projection_points",
        "fantasy points|ranked projection total",
    )

    assert raw_projection["classification"] == CLASSIFICATION_CONTEXT_ONLY
    assert raw_projection["private_football_value_allowed"] is False
    assert "cannot directly drive private football value" in raw_projection["leakage_rule"]
    assert supplied_points["classification"] == CLASSIFICATION_REJECTED
    assert supplied_points["private_football_value_allowed"] is False


def test_league_rank_market_and_missing_data_rules_are_explicit() -> None:
    league_rank = row_for_field(
        "league_rank_rule_context",
        "league rank|Roster's League-Rank Top Five",
    )
    source_gap = row_for_field(
        "source_coverage_and_warnings",
        "missing evidence|unavailable sections|source warnings",
    )

    assert league_rank["private_football_value_allowed"] is False
    assert "League rank cannot drive Dynasty Asset Value" in league_rank["leakage_rule"]
    assert source_gap["private_football_value_allowed"] is False
    assert "cannot become zero" in source_gap["missing_data_rule"]
    assert "cannot become zero" in league_rank["missing_data_rule"]


def test_sourced_stats_and_prospect_facts_have_private_value_lanes() -> None:
    first_downs = row_for_field(
        "manual_first_down_exports",
        "Rush 1st|Rush 1st%|Receiving 1st|Receiving 1st%",
    )
    draft_capital = row_for_field(
        "nfl_draft_results",
        "draft year|round|overall pick|NFL team",
    )
    third_party = row_for_field(
        "third_party_combine_pro_day",
        "combine/pro-day measurements and IDs",
    )

    assert first_downs["classification"] == CLASSIFICATION_SCORING_EVIDENCE
    assert first_downs["private_football_value_allowed"] is True
    assert first_downs["direct_scoring_allowed"] is True
    assert first_downs["admitted_only_if_join_status_matched"] is True
    assert draft_capital["classification"] == CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE
    assert draft_capital["private_football_value_allowed"] is True
    assert third_party["classification"] == CLASSIFICATION_SOURCE_LIMITED
    assert third_party["private_football_value_allowed"] is False


def test_return_data_is_scoring_only_not_talent_or_role_signal() -> None:
    returns = row_for_field(
        "manual_return_exports",
        "kick_return_yards|punt_return_yards|return_td",
    )

    assert returns["direct_scoring_allowed"] is True
    assert returns["talent_signal_allowed"] is False
    assert returns["role_signal_allowed"] is False
    assert returns["admitted_only_if_join_status_matched"] is True


def test_source_trust_contract_writes_doc_and_csv(tmp_path: Path) -> None:
    paths = write_source_trust_contract_outputs(
        csv_path=tmp_path / "contract.csv",
        doc_path=tmp_path / "contract.md",
    )

    assert _header(paths["csv"]) == SOURCE_TRUST_CONTRACT_HEADER
    assert paths["doc"].exists()
    assert "ADP, rankings, cheat sheets" in paths["doc"].read_text(encoding="utf-8")


def test_contract_classification_vocabulary_is_exact() -> None:
    allowed = {
        "scoring_evidence",
        "derived_evidence",
        "prospect_prior_evidence",
        "context_only",
        "market_context_only",
        "source_limited",
        "rejected",
    }

    assert {str(row["classification"]) for row in build_source_trust_contract_rows()} <= allowed


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
