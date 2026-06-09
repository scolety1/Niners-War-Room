from __future__ import annotations

from pathlib import Path

import pytest

from src.services.qb_te_shadow_v2_candidate_service import (
    OUTPUT_ROOT,
    PRODUCTION_PROPOSAL,
    TE_DIAGNOSIS_REPORT,
    V1_ROOT,
    VARIANT_IDS,
    build_qb_te_shadow_v2_experiment,
    write_qb_te_shadow_v2_experiment,
)

pytestmark = pytest.mark.skipif(
    not V1_ROOT.exists(),
    reason="v1 shadow experiment output is required",
)


def test_v2_shadow_preserves_active_baseline_and_guardrails() -> None:
    result = build_qb_te_shadow_v2_experiment()

    assert result.active_hash_before == result.active_hash_after
    assert result.summary["active_output_changed"] is False
    assert result.summary["baseline_scored_rows"] == 232
    assert result.summary["baseline_k_rows"] == 8
    assert result.summary["sentinels_safe"] is True
    assert result.summary["contamination_safe"] is True
    assert result.summary["decision_board_blocked"] is True


def test_v2_variants_and_te_receipts_are_complete() -> None:
    result = build_qb_te_shadow_v2_experiment()

    assert {variant.variant_id for variant in result.variants} == set(VARIANT_IDS)
    for variant in result.variants:
        assert len(variant.ranking_rows) == 240
        assert variant.movement_vs_baseline
        assert variant.movement_vs_v1
        assert variant.position_rows
        assert variant.my_team_rows
        assert variant.suspicious_rows
        assert variant.te_receipt_rows
        assert all(row["position"] == "TE" for row in variant.te_receipt_rows)


def test_v2_outputs_do_not_use_blocked_sources_or_recommendations() -> None:
    result = build_qb_te_shadow_v2_experiment()
    text = "\n".join(
        [
            result.manifest,
            result.te_diagnosis,
            result.plan_report,
            result.results_report,
            result.production_proposal,
            result.no_promotion_note,
        ]
    ).lower()
    forbidden_recommendations = (
        "recommend trading",
        "recommend cutting",
        "recommend drafting",
        "recommend buying",
        "recommend selling",
        "should start",
        "should sit",
    )

    assert "not use market rank" in text
    assert "rotowire rankings/projections" in text
    assert "legacy active-pack scores" in text
    assert not any(phrase in text for phrase in forbidden_recommendations)


def test_v2_rb_wr_scores_remain_unchanged() -> None:
    result = build_qb_te_shadow_v2_experiment()

    for variant in result.variants:
        rb_wr_rows = [
            row for row in variant.ranking_rows if row["position"] in {"RB", "WR"}
        ]
        assert rb_wr_rows
        assert {
            float(row["score_delta_vs_baseline"])
            for row in rb_wr_rows
            if row["score_delta_vs_baseline"] != ""
        } == {0.0}


def test_v2_write_creates_experiment_folder_and_reports(tmp_path: Path) -> None:
    result = build_qb_te_shadow_v2_experiment()
    paths = write_qb_te_shadow_v2_experiment(
        result=result,
        output_root=tmp_path / OUTPUT_ROOT.name,
    )

    assert paths.manifest.exists()
    assert "shadow-only" in paths.manifest.read_text(encoding="utf-8")
    assert TE_DIAGNOSIS_REPORT.exists()
    assert paths.results_report.exists()
    for files in paths.variant_files.values():
        assert files["te_receipts"].exists()
        assert tmp_path in files["rankings"].parents
    assert paths.production_proposal is None or PRODUCTION_PROPOSAL.exists()
    assert paths.production_proposal is not None or paths.no_promotion_note is not None
