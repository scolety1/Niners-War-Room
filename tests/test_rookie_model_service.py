from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.services.rookie_model_service import (
    GENERATED_TABLES,
    SOURCE_TABLES,
    generated_audit_rows,
    generated_model_output_rows,
    load_feature_registry,
    run_rookie_model_from_dir,
    validate_registry,
)

SAMPLE_DIR = Path("sample_data/rookie_model_v1")


def test_source_tables_exist_and_generated_tables_are_not_committed() -> None:
    for filename in SOURCE_TABLES:
        assert (SAMPLE_DIR / filename).exists()
    for filename in GENERATED_TABLES:
        assert not (SAMPLE_DIR / filename).exists()


def test_registry_validation_rejects_display_only_live_weight(tmp_path) -> None:
    registry_path = tmp_path / "rookie_feature_registry.csv"
    registry_path.write_text(
        "\n".join(
            [
                (
                    "feature_id,position,feature_name,parent_component,default_weight,"
                    "min_weight,max_weight,evidence_strength,is_core,is_display_only,"
                    "post_draft_only,manual_entry_allowed,requires_source_type"
                ),
                "wr_bad,WR,bad_feature,display_only,1,0,5,low,false,true,false,true,manual",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Display-only feature has live weight"):
        validate_registry(load_feature_registry(registry_path))


def test_registry_validation_rejects_core_feature_outside_main_component(tmp_path) -> None:
    registry_path = tmp_path / "rookie_feature_registry.csv"
    registry_path.write_text(
        "\n".join(
            [
                (
                    "feature_id,position,feature_name,parent_component,default_weight,"
                    "min_weight,max_weight,evidence_strength,is_core,is_display_only,"
                    "post_draft_only,manual_entry_allowed,requires_source_type"
                ),
                "wr_bad,WR,target_earning,league_fit_score,5,0,10,high,true,false,false,true,manual",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Core feature outside main component"):
        validate_registry(load_feature_registry(registry_path))


def test_sample_rookie_model_run_has_expected_golden_outputs() -> None:
    run = run_rookie_model_from_dir(SAMPLE_DIR)
    scores = {score.player_id: score for score in run.scores}

    assert len(scores) == 10
    assert scores["rookie_wr_elite"].final_decision_score == pytest.approx(93.69)
    assert scores["rookie_wr_elite"].recommended_range_label == "1.01-1.03"
    assert scores["rookie_rb_three_down"].final_decision_score == pytest.approx(90.13)
    assert scores["rookie_qb_elite"].gate_applied == "qb_elite_exempt"
    assert scores["rookie_qb_elite"].recommended_range_label == "1.04-1.06"
    assert scores["rookie_qb_pocket"].gate_applied == "qb_structural_penalty"
    assert scores["rookie_qb_pocket"].final_decision_score == pytest.approx(59.03)
    assert scores["rookie_te_elite"].gate_applied == "te_elite_exempt"
    assert scores["rookie_te_elite"].do_not_draft_before_pick == 11
    assert scores["rookie_te_day3"].gate_applied == "te_day3_penalty"
    assert scores["rookie_te_day3"].final_decision_score == pytest.approx(34.08)
    assert "veteran_opportunity_drag" in scores["rookie_wr_vet_drag"].risk_flags
    assert "no_ppr_satellite" in scores["rookie_rb_satellite"].risk_flags


def test_generated_output_rows_include_numeric_pick_bounds_and_flags() -> None:
    run = run_rookie_model_from_dir(SAMPLE_DIR)
    rows = generated_model_output_rows(run.scores)
    first = rows[0]

    assert first["board_rank"] == 1
    assert first["recommended_pick_min"] == 1
    assert first["recommended_pick_max"] == 3
    assert first["recommended_range_label"] == "1.01-1.03"
    assert "alpha_target_earner" in str(first["upside_flags"])


def test_audit_rows_reconcile_main_component_contributions() -> None:
    run = run_rookie_model_from_dir(SAMPLE_DIR)
    rows = generated_audit_rows(run)
    rows_by_player = {}
    for row in rows:
        rows_by_player.setdefault(row["player_id"], []).append(row)

    for score in run.scores:
        contribution_total = sum(
            row["component_contribution"] for row in rows_by_player[score.player_id]
        )
        assert contribution_total == pytest.approx(score.main_prospect_score, abs=0.01)


def test_generated_output_can_be_written_but_sample_pack_does_not_store_it(tmp_path) -> None:
    from src.services.rookie_model_service import write_generated_model_outputs

    run = run_rookie_model_from_dir(SAMPLE_DIR)
    output_path = tmp_path / "rookie_model_outputs.csv"
    write_generated_model_outputs(output_path, run.scores)

    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 10
    assert rows[0]["model_version"] == "rookie_lve_v1_0_0"
