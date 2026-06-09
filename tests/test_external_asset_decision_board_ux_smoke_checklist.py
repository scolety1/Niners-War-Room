from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "docs/model_v4/EXTERNAL_ASSET_DECISION_BOARD_UX_SMOKE_CHECKLIST_20260605.md"
)
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"
TRADE_PAGE = ROOT / "app/pages/04_trade_central.py"
WAR_BOARD_PAGE = ROOT / "app/pages/03_war_board.py"


def test_external_asset_decision_board_checklist_covers_sources_and_guardrails() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv",
        "dynasty_asset_value_review_score",
        "review_v4_dynasty_asset",
        "local_exports/model_v4/decision_pressure/latest/cut_keep_pressure_review_rows.csv",
        "pressure_score",
        "local_exports/model_v4/june15_decision_board/latest/june15_decision_board_review_rows.csv",
        "review_only_june15_decision_context_not_final_action",
        "do_not_use_as_final_cut_keep_trade_or_draft_recommendation",
        "final_recommendations_created",
        "readiness_unlocked",
    ]

    for term in required_terms:
        assert term in text


def test_external_asset_decision_board_checklist_covers_named_trace_rows() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "Trey McBride",
        "Puka Nacua",
        "Jaxon Smith-Njigba",
        "Christian McCaffrey",
        "Josh Allen",
        "2026 1.03",
        "2026 5.04",
        "Kaleb Johnson",
        "Luke McCaffrey",
        "Jeremiyah Love",
        "Makai Lemon",
        "Ja'Kobi Lane",
        "manual-only",
        "no exact model baseline",
    ]

    for term in required_terms:
        assert term in text


def test_external_asset_decision_board_checklist_preserves_review_only_scope() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "Do not tune formulas from this checklist." in text
    assert "Do not tune formulas from this checklist." in text
    assert "generated outputs" in text
    assert "Do not use this checklist as proof the model is ready for money decisions." in text
    assert "Market context must be described as liquidity/comparison/display context only." in text
    assert "must not convert them into final instructions" in text
    assert "Do not mutate active rankings, My Team, War Board" in text


def test_app_pages_contain_ui_labels_referenced_by_checklist() -> None:
    trade_page = TRADE_PAGE.read_text(encoding="utf-8")
    war_page = WAR_BOARD_PAGE.read_text(encoding="utf-8")

    for term in [
        "External Asset Reviews",
        "Inspect trade-context player",
        "Roster Context",
        "External Asset Context",
        "Market Context",
        "Context Drill-Down",
        "Market Gap Signal",
        "How to read Market Gap",
        "Advanced: pick path audit",
    ]:
        assert term in trade_page

    for term in [
        "War Board",
        "Decision Snapshot",
        "Top Ranked",
        "Action Queue",
        "Model vs Market",
        "Ranking Surface",
        "Why Ranked Here",
        "Advanced: full receipt rows",
        "Advanced: score source audit",
    ]:
        assert term in war_page


def test_refinement_queue_marks_r20_done_with_audit_note() -> None:
    queue = QUEUE.read_text(encoding="utf-8")

    assert "| R20 | External Asset/Decision Board UX smoke checklist |" in queue
    r20_line = next(line for line in queue.splitlines() if line.startswith("| R20 |"))
    assert "| Done |" in r20_line
    assert "EXTERNAL_ASSET_DECISION_BOARD_UX_SMOKE_CHECKLIST_20260605.md" in r20_line
    assert "External Asset Reviews, War Board Decision Snapshot" in r20_line
