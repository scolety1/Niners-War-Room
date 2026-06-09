from __future__ import annotations

import csv
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK
from src.services.player_board_score_service import build_player_board_score_rows


ROOT = Path(__file__).resolve().parents[1]
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
ROOKIE_ROWS = (
    ROOT
    / "local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
)
PICK_INVENTORY_ROWS = (
    ROOT
    / "local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv"
)
PICK_DECISION_ROWS = (
    ROOT
    / "local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv"
)
DECISION_BOARD_ROWS = (
    ROOT
    / "local_exports/model_v4/june15_decision_board/latest/"
    "june15_decision_board_review_rows.csv"
)
DECISION_BOARD_RECEIPTS = (
    ROOT
    / "local_exports/model_v4/june15_decision_board/latest/"
    "june15_decision_board_receipts.csv"
)
DECISION_BOARD_COMPONENTS = (
    ROOT
    / "local_exports/model_v4/june15_decision_board/latest/"
    "june15_decision_board_component_rows.csv"
)
NOTES = ROOT / "docs/model_v4/NON_FORMULA_SANITY_FIXTURE_TEST_NOTES_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def test_current_player_elite_anchors_stay_above_obvious_depth_rows_with_guardrails() -> None:
    rows = _read_rows(CURRENT_ROWS)
    by_player = {row["player_name"]: row for row in rows}
    elite_names = {
        "Puka Nacua",
        "Jaxon Smith-Njigba",
        "Christian McCaffrey",
        "Jonathan Taylor",
        "Bijan Robinson",
        "Jahmyr Gibbs",
    }
    depth_names = {"Kaleb Johnson", "Luke McCaffrey", "Darrell Henderson"}

    elite_scores = [_float(by_player[name]["checkpoint_review_score"]) for name in elite_names]
    depth_scores = [_float(by_player[name]["checkpoint_review_score"]) for name in depth_names]

    assert min(elite_scores) > max(depth_scores)
    for name in elite_names | depth_names:
        row = by_player[name]
        assert row["allowed_use"] == "review_only_current_value_checkpoint"
        assert row["blocked_use"] == "do_not_use_as_final_ranking_or_roster_recommendation"
        assert row["warning_flags"]


def test_legacy_sentinals_remain_comparison_only_and_fail_closed() -> None:
    rows = build_player_board_score_rows(Path(DEFAULT_DATA_PACK))
    by_player = {row["player"]: row for row in rows}
    keenan = by_player["Keenan Allen"]
    darius = by_player["Darius Slayton"]

    assert keenan["source_column"] == "checkpoint_review_score"
    assert keenan["lineage_class"] == "review_v4_current_player"
    assert keenan["private_score"] != keenan["legacy_active_pack_score"]
    assert str(keenan["legacy_active_pack_score"]) == "82.4"
    assert darius["private_score"] in {"", None}
    assert str(darius["legacy_active_pack_score"]) == "78.88"
    assert darius["manual_decision_required"] is True


def test_rookie_watchlist_rows_remain_blocked_from_final_pick_use() -> None:
    rows = _read_rows(ROOKIE_ROWS)
    by_player = {row["prospect_name"]: row for row in rows}
    sobkowicz = by_player["Daniel Sobkowicz"]

    assert sobkowicz["evidence_status"] == "watchlist_data_incomplete"
    assert sobkowicz["draft_board_band"] == "watchlist_or_data_incomplete_context_review"
    assert sobkowicz["allowed_use"] == "review_only_rookie_board_context_not_final_pick"
    assert sobkowicz["blocked_use"] == "do_not_use_as_final_rookie_draft_recommendation"
    assert "missing_prospect_or_college_evidence" in sobkowicz["warning_flags"]
    assert "market_context_excluded_from_private_value" in sobkowicz["warning_flags"]


def test_pick_ladder_keeps_scored_order_and_manual_only_missing_baseline() -> None:
    rows = _read_rows(PICK_INVENTORY_ROWS)
    by_pick = {row["pick_label"]: row for row in rows}

    assert _float(by_pick["2026 1.03"]["pick_value_review_score"]) > _float(
        by_pick["2026 1.04"]["pick_value_review_score"]
    )
    assert _float(by_pick["2026 1.04"]["pick_value_review_score"]) > _float(
        by_pick["2026 2.04"]["pick_value_review_score"]
    )
    assert _float(by_pick["2026 2.04"]["pick_value_review_score"]) > _float(
        by_pick["2026 2.08"]["pick_value_review_score"]
    )

    five_four = by_pick["2026 5.04"]
    assert five_four["pick_value_review_score"] == ""
    assert five_four["tier_label"] == "manual_only_no_exact_model_baseline"
    assert five_four["baseline_match_status"] == "missing_pick_value_baseline"
    assert "manual_only_no_exact_model_baseline" in five_four["warning_flags"]
    assert five_four["blocked_use"] == "do_not_use_as_pick_trade_recommendation_or_offer"


def test_pick_decision_lab_context_rows_keep_equivalence_guardrails() -> None:
    rows = _read_rows(PICK_DECISION_ROWS)
    by_pick = {row["pick_label"]: row for row in rows}

    for pick in ("2026 1.03", "2026 1.04"):
        row = by_pick[pick]
        assert row["equivalence_guardrail"] == (
            "internal_model_neighbor_only_not_one_for_one_trade_equivalent"
        )
        assert "opportunity-cost context" in row["trade_market_reality_context"]
        assert row["blocked_use"] == "do_not_use_as_final_pick_trade_cut_keep_or_draft_recommendation"

    five_four = by_pick["2026 5.04"]
    assert five_four["pick_value_score"] == ""
    assert five_four["review_label"] == "manual_only_no_exact_model_baseline"
    assert five_four["equivalence_guardrail"] == "no_exact_equivalence_without_pick_baseline"
    assert "no exact trade-market equivalence" in five_four["trade_market_reality_context"]


def test_decision_board_rows_remain_review_only_and_traceable() -> None:
    board_rows = _read_rows(DECISION_BOARD_ROWS)
    receipt_rows = _read_rows(DECISION_BOARD_RECEIPTS)
    component_rows = _read_rows(DECISION_BOARD_COMPONENTS)
    by_entity = {row["entity_label"]: row for row in board_rows}
    receipt_keys = {row["decision_key"] for row in receipt_rows}
    component_counts: dict[str, int] = {}
    for row in component_rows:
        component_counts[row["decision_key"]] = component_counts.get(row["decision_key"], 0) + 1

    assert {row["allowed_use"] for row in board_rows} == {
        "review_only_june15_decision_context_not_final_action"
    }
    assert {row["blocked_use"] for row in board_rows} == {
        "do_not_use_as_final_cut_keep_trade_or_draft_recommendation"
    }
    assert {row["decision_area"] for row in board_rows} == {
        "pick_trade_defer_context",
        "roster_pressure_trade_context",
        "rookie_pick_window_context",
    }
    for row in board_rows:
        assert row["decision_key"] in receipt_keys
        assert component_counts[row["decision_key"]] == 3

    five_four = by_entity["2026 5.04"]
    assert five_four["source_review_score"] == ""
    assert five_four["primary_review_band"] == "pick_baseline_missing_review"
    assert "manual_only_no_exact_model_baseline" in five_four["warning_flags"]


def test_r22_notes_and_queue_document_non_formula_scope() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    queue = QUEUE.read_text(encoding="utf-8")

    assert "Automated In R22" in notes
    assert "Intentionally Not Automated Yet" in notes
    assert "Exact elite tier score cutoffs." in notes
    assert "Whether Trey McBride should or should not be the highest current-player score" in notes
    assert "Do not tune formulas from these tests." in notes

    r22_line = next(line for line in queue.splitlines() if line.startswith("| R22 |"))
    assert "| Done |" in r22_line
    assert "test_non_formula_sanity_fixtures.py" in r22_line
    assert "source/risk guardrails" in r22_line


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _float(value: object) -> float:
    return float(str(value).strip())
