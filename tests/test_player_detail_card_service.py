from __future__ import annotations

import pytest

from src.services.player_detail_card_service import (
    DISPLAY_ONLY_NOTE,
    DRAFT_PREP_CONTEXT,
    LEGACY_COMPARISON_ONLY_NOTE,
    build_player_detail_card_payload,
)


def test_rankings_payload_maps_common_and_rankings_fields() -> None:
    payload = build_player_detail_card_payload(_rankings_row(), context="rankings")

    assert payload.player == "Keenan Allen"
    assert payload.position == "WR"
    assert payload.age == "34.1"
    assert payload.team == "FA"
    assert payload.nwr_score == "33.16"
    assert payload.nwr_rank == "188"
    assert payload.trust_status == "Capped Score"
    assert payload.market_rank_display_only == "199.4"
    assert payload.league_rank_display_only == "140"
    assert payload.market_gap_display_only == "+11"
    assert payload.league_gap_display_only == "-48"
    assert payload.display_only_note == DISPLAY_ONLY_NOTE


def test_rankings_payload_keeps_legacy_score_comparison_only() -> None:
    payload = build_player_detail_card_payload(_rankings_row(), context="rankings")

    assert payload.legacy_comparison_score == "82.40"
    assert payload.legacy_note == LEGACY_COMPARISON_ONLY_NOTE
    assert "comparison-only" in payload.legacy_note
    assert "cannot drive NWR score" in payload.legacy_note


def test_rankings_payload_sentinel_darius_legacy_score_is_not_primary() -> None:
    row = _rankings_row(
        player="Darius Slayton",
        private_score="23.6148",
        legacy_active_pack_score="78.88",
    )
    payload = build_player_detail_card_payload(row, context="rankings")

    assert payload.nwr_score == "23.61"
    assert payload.legacy_comparison_score == "78.88"
    assert payload.nwr_score != payload.legacy_comparison_score


def test_payload_handles_missing_optional_fields_without_crashing() -> None:
    payload = build_player_detail_card_payload({"player": "No Score Player"}, context="rankings")

    assert payload.player == "No Score Player"
    assert payload.nwr_score == "-"
    assert payload.trust_status == "No Private Score"
    assert "No private NWR Dynasty Score is available." in payload.data_needed
    assert "Source path is missing." in payload.data_needed
    assert "Source column is missing." in payload.data_needed


def test_raw_receipts_are_available_for_advanced_display() -> None:
    payload = build_player_detail_card_payload(_rankings_row(), context="rankings")
    receipts = {receipt.label: receipt.value for receipt in payload.receipts}

    assert receipts["Source path"] == "local_exports/model_v4/current_value/latest/full.csv"
    assert receipts["Source column"] == "nwr_dynasty_score"
    assert receipts["Lineage"] == "review_v4_current_player"
    assert receipts["Allowed use"] == "review_only_full_player_board_rankings"
    assert "do_not_use_as_final" in receipts["Blocked use"]
    assert "partial_first_down_confidence_cap" in receipts["Raw warnings"]


def test_unsupported_context_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unsupported player detail card context"):
        build_player_detail_card_payload(_rankings_row(), context="live_draft_room")


def test_draft_prep_payload_maps_context_only_fields() -> None:
    payload = build_player_detail_card_payload(_draft_prep_row(), context=DRAFT_PREP_CONTEXT)

    assert payload.context == "draft_prep"
    assert payload.player == "Jeremiyah Love"
    assert payload.position == "RB"
    assert payload.team == "ARI"
    assert payload.nwr_score == "75.31"
    assert payload.source_type == "Rookie"
    assert payload.roster_status == "Rookie Draftable"
    assert "Legal Pool Pending" in payload.why_text
    assert "display-only/context-only" in payload.display_only_note
    assert _metric_value(payload.draft_prep_context_metrics, "Pick Window") == "2026 1.03"
    assert _metric_value(payload.draft_prep_context_metrics, "Fit Band") == "In Range"
    assert _metric_value(payload.draft_prep_context_metrics, "Draftable Status") == (
        "Rookie Draftable"
    )


def test_draft_prep_payload_keeps_history_context_display_only() -> None:
    payload = build_player_detail_card_payload(
        _draft_prep_row(user_context_tags="Must Review At Cost; User Drafted Context"),
        context=DRAFT_PREP_CONTEXT,
    )

    assert _metric_value(payload.user_context_metrics, "User / History Context") == (
        "Must Review At Cost; User Drafted Context"
    )
    assert _metric_note(payload.user_context_metrics, "Must Review At Cost") == (
        "context-only, not a final instruction"
    )


def test_draft_prep_payload_missing_fields_do_not_invent_draftable_status() -> None:
    payload = build_player_detail_card_payload(
        {"player": "Manual Watchlist Player"},
        context=DRAFT_PREP_CONTEXT,
    )

    assert payload.player == "Manual Watchlist Player"
    assert payload.roster_status == "-"
    assert payload.nwr_score == "-"
    assert payload.draft_prep_context_metrics == ()


def _rankings_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "player": "Keenan Allen",
        "position": "WR",
        "age": "34.1",
        "nfl_team": "FA",
        "pool_status": "AVAILABLE",
        "private_score": "33.1581",
        "nwr_rank": "188",
        "nwr_trust_status": "Capped Score",
        "market_rank": "199.4",
        "league_rank": "140",
        "legacy_active_pack_score": "82.4",
        "source_path": "local_exports/model_v4/current_value/latest/full.csv",
        "source_column": "nwr_dynasty_score",
        "upstream_source_path": "local_exports/model_v4/current_value/latest/current.csv",
        "upstream_source_column": "checkpoint_review_score",
        "lineage_class": "review_v4_current_player",
        "model_version": "model_v4",
        "score_as_of_date": "2026-06-09",
        "confidence_cap": "0.8",
        "confidence_status": "capped_review_required",
        "allowed_use": "review_only_full_player_board_rankings",
        "blocked_use": "do_not_use_as_final_ranking_or_roster_recommendation",
        "warning_reasons": "partial_first_down_confidence_cap|source_limited_evidence_cap",
    }
    row.update(overrides)
    return row


def _draft_prep_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "player": "Jeremiyah Love",
        "position": "RB",
        "nfl_team": "ARI",
        "college_team": "Notre Dame",
        "age": "21.1",
        "source_type": "rookie",
        "draftable_status": "rookie_draftable",
        "legal_draftable": "false",
        "nwr_rookie_score": "75.31",
        "pick_window": "2026 1.03",
        "fit_band": "In Range",
        "prospect_talent_context": "early_first_round_context",
        "landing_spot_context": "post_draft_landing_spot_loaded",
        "draft_capital_context": "round_2",
        "role_path_context": "needs_role_review",
        "trust_status": "Scouting Only",
        "warning_flags": "source_limited_evidence_cap",
        "data_needed": "Need scouting confirmation.",
        "allowed_use": "scouting_prep_context_only",
        "blocked_use": "do_not_use_as_private_value_or_final_draft_recommendation",
        "source_path": "local_exports/model_v4/draft_prep/latest/scouting.csv",
        "source_column": "nwr_rookie_score",
        "lineage_class": "review_v4_dynasty_asset",
    }
    row.update(overrides)
    return row


def _metric_value(metrics: tuple[object, ...], label: str) -> str:
    return next(metric.value for metric in metrics if metric.label == label)


def _metric_note(metrics: tuple[object, ...], label: str) -> str:
    return next(metric.note for metric in metrics if metric.label == label)
