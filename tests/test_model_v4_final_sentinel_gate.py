from __future__ import annotations

from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.config.settings import get_settings
from src.services.full_board_current_value_export_service import (
    DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS,
)
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.market_gap_service import build_market_gap_report
from src.services.model_v4_rookie_pick_decision_lab_service import (
    build_rookie_pick_decision_lab,
)
from src.services.model_v4_roster_opportunity_cost_service import (
    build_roster_opportunity_cost,
)
from src.services.model_v4_sprint14c_trade_review_service import (
    build_trade_review_outputs,
)
from src.services.model_v4_startup_slot_simulator_service import (
    build_startup_slot_simulator,
)
from src.services.player_board_score_service import build_player_board_score_rows

ACTIVE_PACK = Path(DEFAULT_DATA_PACK)
CURRENT_VALUE_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)

pytestmark = pytest.mark.skipif(
    not ACTIVE_PACK.exists() or not CURRENT_VALUE_ROWS.exists(),
    reason="local Model v4 exports are required for final sentinel regression tests",
)


def test_final_gate_keeps_legacy_keenan_and_darius_scores_out_of_primary_value() -> None:
    rows = build_player_board_score_rows(ACTIVE_PACK)
    by_player = {str(row["player"]): row for row in rows}

    keenan = by_player["Keenan Allen"]
    darius = by_player["Darius Slayton"]

    if DEFAULT_FULL_PLAYER_BOARD_ROWS.exists():
        assert keenan["source_column"] == "nwr_dynasty_score"
        assert keenan["source_path"] == str(DEFAULT_FULL_PLAYER_BOARD_ROWS)
    else:
        assert keenan["source_column"] == "checkpoint_review_score"
    assert keenan["lineage_class"] == "review_v4_current_player"
    if DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS.exists():
        assert float(keenan["private_score"]) == pytest.approx(33.1581)
    else:
        assert float(keenan["private_score"]) == pytest.approx(41.6097)
    assert float(keenan["legacy_active_pack_score"]) == pytest.approx(82.4)
    assert float(keenan["private_score"]) != pytest.approx(82.4)

    assert float(darius["legacy_active_pack_score"]) == pytest.approx(78.88)
    if DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS.exists():
        assert float(darius["private_score"]) == pytest.approx(23.6148)
        assert darius["lineage_class"] == "review_v4_current_player"
        assert float(darius["private_score"]) != pytest.approx(78.88)
    else:
        assert darius["private_score"] in {"", None}
        assert darius["primary_review_score"] in {"", None}
        assert darius["manual_decision_required"] is True


def test_final_gate_market_context_stays_display_only_and_action_neutral() -> None:
    report = build_market_gap_report(get_settings().active_data_pack)
    banned_terms = ("trade_for", "buy", "sell", "target", "avoid", "pay")

    assert report.rows
    assert report.source_summary["market_display_only"] is True
    assert all(row["market_display_only"] is True for row in report.rows)
    assert all(row["primary_review_score"] == "" for row in report.rows)
    assert all(row["review_label"] == "" for row in report.rows)
    assert all(
        not any(term in str(row["application_hint"]).lower() for term in banned_terms)
        for row in report.rows
    )


def test_final_gate_copy_and_banners_keep_review_language_neutral() -> None:
    trade_page = Path("app/pages/04_trade_central.py").read_text(encoding="utf-8")
    banner_component = Path("app/components/trust_status.py").read_text(encoding="utf-8")
    draft_page = Path("app/pages/06_draft_board.py").read_text(encoding="utf-8")

    assert "External Asset Reviews" in trade_page
    for banned_copy in ("Buy Targets", "Sell Candidates", "Trade-For Candidate"):
        assert banned_copy not in trade_page
    assert "REVIEW_ONLY_SURFACE_BANNER" in banner_component
    assert "does not make automatic trade, cut, keep" in banner_component
    assert "Score Source File" in draft_page
    assert "Score Lineage" in draft_page


def test_final_gate_pick_labels_and_comparisons_remain_gated() -> None:
    result = build_rookie_pick_decision_lab()
    allowed_labels = {
        "use_pick_review",
        "hold_pick_value_context",
        "manual_decision_required",
    }
    blocked_labels = {
        "review_defer_context",
        "review_value_gap",
        "review_candidate_cluster",
        "review_rookie_vs_veteran",
        "review_rookie_vs_drop_player",
        "manual_only_no_exact_model_baseline",
    }

    assert {row["review_label"] for row in result.rows} <= allowed_labels
    assert not ({row["review_label"] for row in result.rows} & blocked_labels)
    assert all(row["comparator_key"] for row in result.compare_rows)
    assert all(
        row["comparator_source_status"] == "concrete_comparator_loaded"
        for row in result.compare_rows
    )


def test_final_gate_cross_asset_exports_disclose_source_lineage() -> None:
    startup = build_startup_slot_simulator()
    roster = build_roster_opportunity_cost()
    pick_lab = build_rookie_pick_decision_lab()
    external = build_trade_review_outputs()
    disclosure_fields = {"source_path", "source_column", "lineage_class"}

    assert startup.review_rows
    assert all(disclosure_fields <= set(row) for row in startup.review_rows)
    assert all(disclosure_fields <= set(row) for row in startup.pick_zone_rows)
    assert roster.rows
    assert all(disclosure_fields <= set(row) for row in roster.rows)
    assert pick_lab.rows
    assert all(disclosure_fields <= set(row) for row in pick_lab.rows)
    assert all(disclosure_fields <= set(row) for row in pick_lab.compare_rows)
    assert external.trade_away_rows
    assert all(disclosure_fields <= set(row) for row in external.trade_away_rows)
    assert external.external_asset_rows
    assert all(disclosure_fields <= set(row) for row in external.external_asset_rows)
