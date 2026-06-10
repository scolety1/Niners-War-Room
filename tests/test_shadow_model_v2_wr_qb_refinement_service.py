from __future__ import annotations

from pathlib import Path

from src.services.shadow_model_v2_wr_qb_refinement_service import (
    EXPERIMENT_IDS,
    WATCH_PLAYERS,
    build_shadow_model_v2_wr_qb_refinement,
    write_shadow_model_v2_wr_qb_refinement_outputs,
)


def test_v2_refinement_builds_shadow_only_experiments() -> None:
    result = build_shadow_model_v2_wr_qb_refinement()

    assert {row["experiment_id"] for row in result.summary_rows} == set(EXPERIMENT_IDS)
    assert len(result.current_rows) == 240 * len(EXPERIMENT_IDS)
    assert len(result.historical_rows) == 395 * len(EXPERIMENT_IDS)
    assert result.baseline_hash_before == result.baseline_hash_after
    assert all(row["production_scores_changed"] is False for row in result.summary_rows)


def test_v2_refinement_uses_no_banned_score_inputs() -> None:
    result = build_shadow_model_v2_wr_qb_refinement()
    blocked_fragments = (
        "market_rank",
        "league_rank",
        "adp",
        "legacy_active_pack_score",
        "private_score",
        "projection",
        "rotowire_rank",
        "prior_draft",
        "pool_status",
        "is_my_team",
        "roster_status",
    )

    for row in (*result.current_rows, *result.historical_rows):
        assert row["shadow_only_policy"] == "shadow_only_no_active_rankings_overwrite"
        assert row["contamination_check"] == "no_blocked_inputs_used"
        inputs = str(row["formula_inputs_used"])
        evidence = str(row["evidence_fields_used"])
        assert not any(fragment in inputs for fragment in blocked_fragments)
        assert not any(fragment in evidence for fragment in blocked_fragments)


def test_v2_wr_lane_tightens_v1_false_positives() -> None:
    result = build_shadow_model_v2_wr_qb_refinement()

    ceedee = _row(result.current_rows, "wr_proof_lane_v2", "CeeDee Lamb")
    jefferson = _row(result.current_rows, "wr_proof_lane_v2", "Justin Jefferson")
    jameson = _row(result.current_rows, "wr_proof_lane_v2", "Jameson Williams")
    diggs = _row(result.current_rows, "wr_proof_lane_v2", "Stefon Diggs")
    davante = _row(result.current_rows, "wr_proof_lane_v2", "Davante Adams")

    assert ceedee["movement_classification"] == "intended_improvement"
    assert jefferson["movement_classification"] == "intended_improvement"
    assert "wr_thin_or_single_year_spike_cap" in jameson["reason_codes"]
    assert "aging_wr_horizon_blocks_full_proof_lane" in diggs["reason_codes"]
    assert "aging_wr_horizon_blocks_full_proof_lane" in davante["reason_codes"]
    assert float(jameson["score_delta"]) == 0.0
    assert float(diggs["score_delta"]) == 0.0
    assert float(davante["score_delta"]) == 0.0


def test_v2_qb_lane_reduces_generic_floor_false_positives() -> None:
    result = build_shadow_model_v2_wr_qb_refinement()

    mahomes = _row(result.current_rows, "qb_floor_horizon_v2", "Patrick Mahomes")
    hurts = _row(result.current_rows, "qb_floor_horizon_v2", "Jalen Hurts")
    goff = _row(result.current_rows, "qb_floor_horizon_v2", "Jared Goff")
    baker = _row(result.current_rows, "qb_floor_horizon_v2", "Baker Mayfield")
    dart = _row(result.current_rows, "qb_floor_horizon_v2", "Jaxson Dart")
    v1_goff = _row(result.current_rows, "qb_v1_reference", "Jared Goff")

    assert mahomes["movement_classification"] == "intended_improvement"
    assert hurts["movement_classification"] == "intended_improvement"
    assert "undercompressed_elite_profile_review_band" in mahomes["reason_codes"]
    assert float(goff["score_delta"]) == 0.0
    assert float(baker["score_delta"]) == 0.0
    assert float(dart["score_delta"]) == 0.0
    assert v1_goff["movement_classification"] == "false_positive"
    assert "pocket_or_solid_qb_not_given_elite_floor" in goff["false_positive_warning"]


def test_v2_watch_rows_include_required_players_and_combined_is_limited() -> None:
    result = build_shadow_model_v2_wr_qb_refinement()
    combined = [row for row in result.current_rows if row["experiment_id"] == "wr_qb_combined_v2"]
    watch_by_experiment = {
        experiment_id: {
            row["player"] for row in result.watch_rows if row["experiment_id"] == experiment_id
        }
        for experiment_id in EXPERIMENT_IDS
    }

    for experiment_id, players in watch_by_experiment.items():
        assert set(WATCH_PLAYERS).issubset(players), experiment_id
    assert all(
        row["score_delta"] in {"", 0.0}
        for row in combined
        if row["position"] not in {"QB", "WR"}
    )


def test_v2_write_outputs_does_not_mutate_active_rankings(tmp_path: Path) -> None:
    active_path = Path(
        "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
    )
    before = active_path.read_bytes()

    result = build_shadow_model_v2_wr_qb_refinement()
    paths = write_shadow_model_v2_wr_qb_refinement_outputs(tmp_path, result)

    assert paths["current_rows"].exists()
    assert paths["metrics"].exists()
    assert paths["refinement_doc"].exists()
    assert active_path.read_bytes() == before


def _row(rows: tuple[dict[str, object], ...], experiment_id: str, player: str) -> dict[str, object]:
    return next(
        row
        for row in rows
        if row["experiment_id"] == experiment_id and row["player"] == player
    )
