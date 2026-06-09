from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/DRAFT_ROOM_UX_SMOKE_CHECKLIST_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"
DRAFT_ROOM_PAGE = ROOT / "app/pages/06_draft_board.py"


def test_draft_room_ux_smoke_checklist_covers_sources_and_owned_picks() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv",
        "league_format_adjusted_score",
        "prospect_private_value_review_score",
        "local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv",
        "pick_value_score",
        "2026 1.03",
        "2026 1.04",
        "2026 2.04",
        "2026 2.08",
        "2026 5.04",
        "Manual-only: no exact model baseline",
        "internal_model_neighbor_only_not_one_for_one_trade_equivalent",
    ]

    for term in required_terms:
        assert term in text


def test_draft_room_ux_smoke_checklist_covers_rookie_traceability_and_receipts() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "Jeremiyah Love",
        "Makai Lemon",
        "Skyler Bell",
        "Jordyn Tyson",
        "Carnell Tate",
        "Antonio Williams",
        "Daniel Sobkowicz",
        "Eli Raridon",
        "Kadarius Calloway",
        "Receipts / Warnings",
        "Components",
        "Warnings",
        "Evidence Capture Worksheet",
    ]

    for term in required_terms:
        assert term in text


def test_draft_room_ux_smoke_checklist_preserves_state_and_formula_guardrails() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "Do not tune formulas from this checklist." in text
    assert "Do not click `Draft`, `Undo`, `Replace`, `Reset Mock`" in text
    assert "Do not mutate active rankings, My Team, War Board" in text
    assert "Do not use this checklist as proof the model is ready for money decisions." in text
    assert "must not populate rookie `Final Score`" in text
    assert "must not be presented as one-for-one trade prices" in text


def test_draft_room_page_contains_ui_labels_referenced_by_checklist() -> None:
    page = DRAFT_ROOM_PAGE.read_text(encoding="utf-8")

    for term in [
        "Draft Prep",
        "Scouting prep mode:",
        "My Pick Cards",
        "Pick-by-Pick Candidate Windows",
        "Scouting Prep Pool",
        "League History Context",
        "Advanced Audit",
        "Live Draft Room tools moved",
        "2026 1.03",
        "2026 1.04",
        "2026 2.04",
        "2026 2.08",
        "2026 5.04",
        "No Baseline",
        "Manual late-round watchlist; no exact equivalence.",
    ]:
        assert term in page


def test_refinement_queue_marks_r19_done_with_audit_note() -> None:
    queue = QUEUE.read_text(encoding="utf-8")

    assert "| R19 | Draft Room UX smoke checklist |" in queue
    r19_line = next(line for line in queue.splitlines() if line.startswith("| R19 |"))
    assert "| Done |" in r19_line
    assert "DRAFT_ROOM_UX_SMOKE_CHECKLIST_20260605.md" in r19_line
    assert "owned picks, rookie filters, source disclosure, warning groups" in r19_line
