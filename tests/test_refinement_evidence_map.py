from pathlib import Path


EVIDENCE_MAP = Path("docs/model_v4/REFINEMENT_EVIDENCE_MAP_20260605.md")


def test_refinement_evidence_map_covers_core_sources_and_surfaces() -> None:
    text = EVIDENCE_MAP.read_text(encoding="utf-8")

    for required in (
        "current_player_value_review_rows.csv",
        "checkpoint_review_score",
        "review_v4_current_player",
        "dynasty_asset_value_review_rows.csv",
        "dynasty_asset_value_review_score",
        "review_v4_dynasty_asset",
        "rookie_draft_board_review_rows.csv",
        "rookie_pick_candidate_review_rows.csv",
        "pick_decision_rows.csv",
        "niners_pick_inventory_review_rows.csv",
        "pick_defer_scenario_review_rows.csv",
        "external_asset_context_review_rows.csv",
        "june15_decision_board_review_rows.csv",
        "startup_slot_review_rows.csv",
        "roster_opportunity_cost_rows.csv",
    ):
        assert required in text


def test_refinement_evidence_map_preserves_guardrails_and_known_gap() -> None:
    text = EVIDENCE_MAP.read_text(encoding="utf-8")

    for required in (
        "does not change formulas",
        "not a ranking judgment",
        "Do not generate outputs",
        "legacy_active_pack_score",
        "display-only context",
        "Current local generated CSV is missing",
        "trade_review/latest",
        "one-for-one trade equivalence",
    ):
        assert required in text
