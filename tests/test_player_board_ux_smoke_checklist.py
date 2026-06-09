from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/PLAYER_BOARD_UX_SMOKE_CHECKLIST_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"
PLAYER_BOARD_PAGE = ROOT / "app/pages/05_rankings.py"


def test_player_board_ux_smoke_checklist_covers_source_routing_sentinels() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv",
        "checkpoint_review_score",
        "legacy_active_pack_score",
        "review_v4_current_player",
        "Keenan Allen",
        "41.6097",
        "82.4",
        "Darius Slayton",
        "78.88",
        "fail-closed",
        "Score Source File",
        "Score Column",
        "Score Lineage",
        "Trust Cap",
        "Warnings",
    ]

    for term in required_terms:
        assert term in text


def test_player_board_ux_smoke_checklist_covers_manual_filter_and_display_only_flows() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "Position filter",
        "Owner filter",
        "Min Model Value",
        "Show audit-watch warnings only",
        "Search by player",
        "Inspect player",
        "Market Context (Read-Only)",
        "display-only",
        "Formula Components",
        "Advanced: raw formula fields",
        "Audit Watchlist",
        "TE No-Premium Review",
        "Evidence Capture Worksheet",
    ]

    for term in required_terms:
        assert term in text


def test_player_board_ux_smoke_checklist_preserves_review_only_guardrails() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "Do not tune formulas from this checklist." in text
    assert "Do not use this checklist as proof the model is ready for money decisions." in text
    assert "does not tune formulas, change generated outputs" in text
    assert "must not issue final trade, cut, keep" in text
    assert "Do not edit active rankings" in text
    assert "My Team, War Board" in text


def test_player_board_page_contains_ui_labels_referenced_by_checklist() -> None:
    page = PLAYER_BOARD_PAGE.read_text(encoding="utf-8")

    for term in [
        "Player Board",
        "Score Source File",
        "Score Column",
        "Score Lineage",
        "Market Context (Read-Only)",
        "Position",
        "Owner",
        "Min Model Value",
        "Show audit-watch warnings only",
        "Inspect player",
        "Advanced: raw formula fields",
        "Audit Watchlist",
        "TE No-Premium Review",
    ]:
        assert term in page


def test_refinement_queue_marks_r18_done_with_audit_note() -> None:
    queue = QUEUE.read_text(encoding="utf-8")

    assert "| R18 | Player Board UX smoke checklist |" in queue
    r18_line = next(line for line in queue.splitlines() if line.startswith("| R18 |"))
    assert "| Done |" in r18_line
    assert "PLAYER_BOARD_UX_SMOKE_CHECKLIST_20260605.md" in r18_line
    assert "filters, score disclosure, warnings, named-player traceability" in r18_line
