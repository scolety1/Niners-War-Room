from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from src.services.model_v4_sprint14d_pick_trade_defer_service import (
    DEFER_SCENARIO_HEADER,
    FUTURE_PICK_CONTEXT_HEADER,
    PICK_INVENTORY_HEADER,
    build_pick_trade_defer_outputs,
    write_pick_trade_defer_outputs,
)


def test_14d_builds_review_only_pick_trade_defer_surfaces() -> None:
    result = build_pick_trade_defer_outputs()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["niners_pick_rows"] == 5
    assert result.summary["defer_scenario_rows"] == 4
    assert result.summary["future_pick_context_rows"] == 20
    assert result.summary["pick_trade_recommendations_created"] is False
    assert result.summary["trade_packages_created"] is False
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False


def test_14d_pick_inventory_matches_niners_picks_and_flags_missing_baseline() -> None:
    result = build_pick_trade_defer_outputs()
    by_label = {row["pick_label"]: row for row in result.pick_inventory_rows}

    assert set(by_label) == {"2026 1.03", "2026 1.04", "2026 2.04", "2026 2.08", "2026 5.04"}
    assert by_label["2026 1.03"]["baseline_match_status"] == "matched_pick_value_baseline"
    assert by_label["2026 5.04"]["baseline_match_status"] == "missing_pick_value_baseline"
    assert by_label["2026 5.04"]["tier_label"] == "manual_only_no_exact_model_baseline"
    assert "pick_value_baseline_missing" in by_label["2026 5.04"]["warning_flags"]
    assert "manual_only_no_exact_model_baseline" in by_label["2026 5.04"]["warning_flags"]
    assert {row["blocked_use"] for row in result.pick_inventory_rows} == {
        "do_not_use_as_pick_trade_recommendation_or_offer"
    }


def test_14d_defer_scenarios_are_context_not_trade_recommendations() -> None:
    result = build_pick_trade_defer_outputs()
    by_current = {row["current_pick_label"]: row for row in result.defer_scenario_rows}

    assert by_current["2026 1.03"]["future_pick_label"] == "2027 1.03"
    assert by_current["2026 1.03"]["value_delta_review"] == 6.4
    assert by_current["2026 1.03"]["defer_review_band"] == (
        "future_first_defer_premium_context_review"
    )
    assert "2026 5.04" not in by_current
    assert {row["allowed_use"] for row in result.defer_scenario_rows} == {
        "review_only_pick_defer_context_not_recommendation"
    }
    assert {row["blocked_use"] for row in result.defer_scenario_rows} == {
        "do_not_use_as_pick_trade_recommendation_or_offer"
    }


def test_14d_future_pick_context_is_not_target_recommendation() -> None:
    result = build_pick_trade_defer_outputs()

    assert {row["season"] for row in result.future_pick_context_rows} == {"2027"}
    assert {row["round"] for row in result.future_pick_context_rows} == {"1", "2"}
    assert {row["allowed_use"] for row in result.future_pick_context_rows} == {
        "review_only_future_pick_context_not_trade_target_recommendation"
    }
    assert {row["blocked_use"] for row in result.future_pick_context_rows} == {
        "do_not_use_as_pick_trade_recommendation_or_offer"
    }


def test_14d_components_warnings_docs_and_packet(tmp_path: Path) -> None:
    result = build_pick_trade_defer_outputs()
    paths = write_pick_trade_defer_outputs(
        output_root=tmp_path / "pick_trade_defer",
        packet_root=tmp_path / "packets",
        result=result,
    )

    assert _header(paths.pick_inventory_rows) == PICK_INVENTORY_HEADER
    assert _header(paths.defer_scenario_rows) == DEFER_SCENARIO_HEADER
    assert _header(paths.future_pick_context_rows) == FUTURE_PICK_CONTEXT_HEADER
    assert len(result.component_rows) == (5 * 3) + (4 * 3) + 20
    warning_codes = {row["warning_code"] for row in result.warning_rows}
    assert "no_pick_trade_recommendations_or_packages_created" in warning_codes
    assert "pick_value_baseline_missing" in warning_codes
    assert "does not create pick-trade" in paths.doc.read_text(encoding="utf-8")
    assert paths.audit_packet.exists()
    with zipfile.ZipFile(paths.audit_packet) as archive:
        assert "docs/model_v4/SPRINT_14D_EXTERNAL_AUDIT_PROMPT.md" in archive.namelist()


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
