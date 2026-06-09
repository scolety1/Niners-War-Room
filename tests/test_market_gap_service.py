from __future__ import annotations

from pathlib import Path

import pytest

from src.config.settings import get_settings
from src.services.market_gap_service import (
    MARKET_DISPLAY_ALLOWED_USE,
    MARKET_DISPLAY_BLOCKED_USE,
    _application_hint,
    build_market_gap_report,
    load_dynasty_adp_rows,
    normalize_rank_score,
)


def test_normalize_rank_score_maps_best_to_100_and_worst_to_zero() -> None:
    assert normalize_rank_score(1, 301) == pytest.approx(100.0)
    assert normalize_rank_score(301, 301) == pytest.approx(0.0)
    assert normalize_rank_score(151, 301) == pytest.approx(50.0)
    assert normalize_rank_score("", 301) is None


def test_load_dynasty_adp_rows_prefers_dynasty_sleeper_column(tmp_path: Path) -> None:
    adp_path = tmp_path / "adp.csv"
    adp_path.write_text(
        "\n".join(
            [
                ",,,,12 Team,,,Dynasty,AAV,,Health Report,",
                "Rank,Name,Team,Pos,Fantrax,Sleeper,MFL,Sleeper,MFL,Ottoneu,Status,Injury",
                "T1,Bijan Robinson,ATL,RB,-,1.60,-,2.70,,,,",
                "T1,Player Missing,ATL,RB,-,-,-,-,,,,",
            ]
        ),
        encoding="utf-8",
    )

    rows, issues = load_dynasty_adp_rows(adp_path)

    assert issues == []
    assert len(rows) == 1
    assert rows[0]["player"] == "Bijan Robinson"
    assert rows[0]["dynasty_startup_adp"] == pytest.approx(2.7)


def test_market_gap_report_adds_review_only_normalized_scores() -> None:
    report = build_market_gap_report(get_settings().active_data_pack)

    assert report.rows
    assert report.source_summary["allowed_use"] == MARKET_DISPLAY_ALLOWED_USE
    assert report.source_summary["blocked_use"] == MARKET_DISPLAY_BLOCKED_USE
    assert report.source_summary["market_display_only"] is True
    scored_rows = [
        row
        for row in report.rows
        if row["league_rank_normalized_score"] != ""
        and row["adp_normalized_score"] != ""
    ]
    assert scored_rows
    assert all(row["market_display_only"] is True for row in scored_rows)
    assert all(row["primary_review_score"] == "" for row in scored_rows)
    assert all(row["review_label"] == "" for row in scored_rows)
    assert all(row["allowed_use"] == MARKET_DISPLAY_ALLOWED_USE for row in scored_rows)
    assert all(row["blocked_use"] == MARKET_DISPLAY_BLOCKED_USE for row in scored_rows)


def test_partial_market_context_does_not_create_watch_label() -> None:
    assert (
        _application_hint(
            owner_side="opponent_roster",
            model_value=80,
            league_score=20,
            adp_score=None,
            reference_score=20,
            gap=60,
        )
        == "partial_market_context_review"
    )


def test_market_gap_application_hint_uses_neutral_display_context_labels() -> None:
    assert (
        _application_hint(
            owner_side="opponent_roster",
            model_value=80,
            league_score=20,
            adp_score=20,
            reference_score=20,
            gap=60,
        )
        == "opponent_roster_model_gap_context_review"
    )
    assert (
        _application_hint(
            owner_side="my_roster",
            model_value=30,
            league_score=90,
            adp_score=90,
            reference_score=90,
            gap=-60,
        )
        == "my_roster_market_premium_context_review"
    )


def test_market_gap_application_hint_has_no_action_like_terms() -> None:
    report = build_market_gap_report(get_settings().active_data_pack)
    banned_terms = ("trade", "buy", "sell", "target", "avoid", "pay")

    assert report.rows
    assert all(
        not any(term in str(row["application_hint"]).lower() for term in banned_terms)
        for row in report.rows
    )
