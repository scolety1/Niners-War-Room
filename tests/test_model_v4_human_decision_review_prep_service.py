from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_human_decision_review_prep_service import (
    CARD_HEADER,
    build_human_decision_review_prep,
    write_human_decision_review_prep,
)


def test_human_decision_review_prep_builds_review_only_cards() -> None:
    result = build_human_decision_review_prep()

    assert result.summary["review_status"] == "review_only_human_decision_prep"
    assert result.summary["pick_review_cards"] == 5
    assert result.summary["roster_pressure_review_cards"] == 24
    assert result.summary["trade_review_cards"] >= 20
    assert result.summary["rookie_manual_scout_queue_rows"] >= 50
    assert result.summary["veteran_risk_review_cards"] >= 10
    assert result.summary["final_recommendations_created"] is False
    assert result.summary["my_team_changed"] is False
    assert result.summary["war_board_changed"] is False
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert result.summary["app_promotion_created"] is False


def test_human_decision_review_prep_preserves_known_decision_context() -> None:
    result = build_human_decision_review_prep()
    pick_cards = {row["entity_label"]: row for row in result.pick_review_cards}
    roster_cards = {row["entity_label"]: row for row in result.roster_pressure_cards}
    scout_cards_504 = [
        row
        for row in result.rookie_manual_scout_queue
        if "pick=2026 5.04" in str(row["why_it_says_it"])
    ]

    assert "same-slot defer delta" in pick_cards["2026 1.03"]["model_says"]
    assert "no admitted exact model baseline" in pick_cards["2026 5.04"]["model_says"]
    assert "exact pick equivalence is blocked" in pick_cards["2026 5.04"]["model_says"]
    assert "manual-only watchlist context" in pick_cards["2026 5.04"]["human_needs_to_decide"]
    assert roster_cards["Kaleb Johnson"]["review_band"] == "required_pressure_zone_review"
    assert scout_cards_504
    assert all(
        "manual-only watchlist context" in row["human_needs_to_decide"]
        for row in scout_cards_504
    )


def test_human_decision_review_prep_cards_block_final_actions() -> None:
    result = build_human_decision_review_prep()
    all_cards = (
        *result.pick_review_cards,
        *result.roster_pressure_cards,
        *result.trade_review_cards,
        *result.rookie_manual_scout_queue,
        *result.veteran_risk_review_cards,
    )

    assert all_cards
    assert {row["allowed_use"] for row in all_cards} == {
        "review_only_human_decision_prep_not_final_action"
    }
    assert all(row["blocked_use"].startswith("do_not_use_as_") for row in all_cards)


def test_human_decision_review_prep_writes_outputs(tmp_path: Path) -> None:
    result = build_human_decision_review_prep()
    paths = write_human_decision_review_prep(
        output_root=tmp_path / "prep",
        doc_path=tmp_path / "HUMAN_DECISION_REVIEW_PREP_PACK.md",
        result=result,
    )

    assert _header(paths.pick_review_cards) == CARD_HEADER
    assert _header(paths.roster_pressure_cards) == CARD_HEADER
    assert _header(paths.trade_review_cards) == CARD_HEADER
    assert paths.summary.exists()
    assert paths.doc.exists()
    assert "does not create final cut" in paths.doc.read_text(encoding="utf-8")


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
