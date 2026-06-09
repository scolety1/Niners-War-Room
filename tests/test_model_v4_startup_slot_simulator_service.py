from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_startup_slot_simulator_service import (
    BUCKET_HEADER,
    NINERS_PICKS,
    PICK_ZONE_HEADER,
    REVIEW_HEADER,
    build_startup_slot_simulator,
    write_startup_slot_simulator_outputs,
)


def test_startup_slot_simulator_builds_review_only_sorted_board() -> None:
    result = build_startup_slot_simulator()
    disclosure_fields = {"source_path", "source_column", "lineage_class"}

    assert result.review_rows
    assert disclosure_fields <= set(REVIEW_HEADER)
    assert all(disclosure_fields <= set(row) for row in result.review_rows)
    assert all(str(row["source_path"]) for row in result.review_rows)
    assert all(str(row["source_column"]) for row in result.review_rows)
    assert all(str(row["lineage_class"]).startswith("review_v4_") for row in result.review_rows)
    scores = [float(row["model_score"]) for row in result.review_rows]
    assert scores == sorted(scores, reverse=True)
    assert {row["allowed_use"] for row in result.review_rows} == {
        "review_only_startup_slot_context_not_final_recommendation"
    }
    assert all("recommendation" in str(row["blocked_use"]) for row in result.review_rows)
    assert all("trade_market_reality_context" in row for row in result.review_rows)
    assert all("equivalence_guardrail" in row for row in result.review_rows)
    assert {row["player_or_asset"] for row in result.review_rows} >= {
        "2026 1.03",
        "2026 1.04",
    }


def test_startup_slot_pick_zones_include_all_niners_picks() -> None:
    result = build_startup_slot_simulator()
    disclosure_fields = {"source_path", "source_column", "lineage_class"}

    assert {row["pick_label"] for row in result.pick_zone_rows} == set(NINERS_PICKS)
    assert disclosure_fields <= set(PICK_ZONE_HEADER)
    assert all(disclosure_fields <= set(row) for row in result.pick_zone_rows)
    assert {row["source_column"] for row in result.pick_zone_rows} == {
        "pick_value_review_score"
    }
    assert all(row["allowed_use"].startswith("review_only") for row in result.pick_zone_rows)
    assert all("final" in str(row["blocked_use"]) for row in result.pick_zone_rows)
    early_pick = next(row for row in result.pick_zone_rows if row["pick_label"] == "2026 1.03")
    assert (
        early_pick["equivalence_guardrail"]
        == "internal_model_neighbor_only_not_one_for_one_trade_equivalent"
    )
    assert "not a claim that one pick can buy" in str(
        early_pick["trade_market_reality_context"]
    )
    assert "elite_current_asset_requires_package_premium_review" in str(
        early_pick["warning_flags"]
    )


def test_startup_slot_504_stays_manual_only_without_exact_baseline() -> None:
    result = build_startup_slot_simulator()
    pick_504 = next(row for row in result.pick_zone_rows if row["pick_label"] == "2026 5.04")

    assert pick_504["pick_value_review_score"] == ""
    assert pick_504["pick_zone_band"] == "manual_only_no_exact_model_baseline"
    assert pick_504["review_label"] == "manual_only_no_exact_model_baseline"
    assert pick_504["nearby_startup_assets"] == ""
    assert pick_504["assets_above_pick"] == ""
    assert pick_504["assets_below_pick"] == ""
    assert "manual_only_no_exact_model_baseline" in str(pick_504["warning_flags"])


def test_outcome_buckets_are_context_only_and_honest_about_samples() -> None:
    result = build_startup_slot_simulator()

    assert result.bucket_rows
    assert all(
        row["allowed_use"] == "review_only_outcome_bucket_context_not_formula_input"
        for row in result.bucket_rows
    )
    assert any(
        row["sample_size_status"] == "low_confidence_small_or_missing_sample"
        for row in result.bucket_rows
    )
    assert any("no_premium_te" in str(row["warning_flags"]) for row in result.bucket_rows)
    assert any("one_qb_qb" in str(row["warning_flags"]) for row in result.bucket_rows)


def test_startup_slot_writes_expected_files(tmp_path: Path) -> None:
    paths = write_startup_slot_simulator_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["review_rows"]) == REVIEW_HEADER
    assert _header(paths["pick_zone_rows"]) == PICK_ZONE_HEADER
    assert _header(paths["bucket_rows"]) == BUCKET_HEADER
    assert paths["component_rows"].exists()
    assert paths["receipts"].exists()
    assert paths["warnings"].exists()
    assert paths["doc"].read_text(encoding="utf-8").startswith("# Startup Slot Simulator Review")


def test_startup_slot_outputs_do_not_use_market_fields_as_value() -> None:
    result = build_startup_slot_simulator()

    private_context = " ".join(
        str(row.get("draft_capital_context", ""))
        + " "
        + str(row.get("evidence_status", ""))
        + " "
        + str(row.get("why_this_slot", ""))
        for row in result.review_rows
    ).lower()
    blocked_terms = ("fantasypros", "rotowire ranking", "projection", "mock draft")
    assert not any(term in private_context for term in blocked_terms)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
