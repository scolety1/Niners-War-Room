from __future__ import annotations

import csv
from pathlib import Path

from src.services.shadow_model_tournament_service import (
    CURRENT_ROW_HEADER,
    EXPERIMENT_IDS,
    HISTORICAL_ROW_HEADER,
    WATCH_PLAYERS,
    build_shadow_model_tournament,
    write_shadow_model_tournament_outputs,
)


def test_shadow_tournament_builds_required_individual_experiments() -> None:
    result = build_shadow_model_tournament()

    assert {row["experiment_id"] for row in result.summary_rows} == set(EXPERIMENT_IDS)
    assert "combined_edge_v1" not in {row["experiment_id"] for row in result.summary_rows}
    assert len(result.historical_rows) == 395 * len(EXPERIMENT_IDS)
    assert len(result.current_rows) == 240 * len(EXPERIMENT_IDS)
    assert result.baseline_hash_before == result.baseline_hash_after


def test_shadow_tournament_outputs_are_shadow_only_and_uncontaminated() -> None:
    result = build_shadow_model_tournament()
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

    for row in (*result.historical_rows, *result.current_rows):
        assert row["shadow_only_policy"] == "shadow_only_no_active_rankings_overwrite"
        assert row["contamination_check"] == "no_blocked_inputs_used"
        inputs = str(row["formula_inputs_used"])
        assert not any(fragment in inputs for fragment in blocked_fragments)


def test_shadow_tournament_watch_rows_include_required_players() -> None:
    result = build_shadow_model_tournament()
    watch_by_experiment = {
        experiment_id: {
            row["player"] for row in result.watch_rows if row["experiment_id"] == experiment_id
        }
        for experiment_id in EXPERIMENT_IDS
    }

    for experiment_id, players in watch_by_experiment.items():
        assert set(WATCH_PLAYERS).issubset(players), experiment_id


def test_shadow_tournament_reports_current_board_movement_without_production_change() -> None:
    result = build_shadow_model_tournament()
    wr_rows = [
        row
        for row in result.watch_rows
        if row["experiment_id"] == "established_wr_proof_lane"
        and row["player"] in {"CeeDee Lamb", "Justin Jefferson", "Jaylen Waddle"}
    ]
    qb_rows = [
        row
        for row in result.watch_rows
        if row["experiment_id"] == "elite_qb_floor_horizon"
        and row["player"] in {"Patrick Mahomes", "Lamar Jackson"}
    ]

    assert all(int(row["rank_delta"]) < 0 for row in wr_rows)
    assert all(int(row["rank_delta"]) < 0 for row in qb_rows)
    assert all(row["production_scores_changed"] is False for row in result.summary_rows)


def test_write_shadow_tournament_outputs_does_not_mutate_active_rankings(tmp_path: Path) -> None:
    active_path = Path(
        "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
    )
    before = active_path.read_bytes()

    result = build_shadow_model_tournament()
    paths = write_shadow_model_tournament_outputs(output_root=tmp_path, result=result)

    assert _header(paths["historical_rows"]) == HISTORICAL_ROW_HEADER
    assert _header(paths["current_rows"]) == CURRENT_ROW_HEADER
    assert active_path.read_bytes() == before


def test_shadow_tournament_docs_forbid_promotion_and_final_recommendations() -> None:
    result = build_shadow_model_tournament()

    for text in result.docs.values():
        lowered = text.lower()
        assert "shadow" in lowered
        assert "no production" in lowered or "production scores are unchanged" in lowered
        assert "draft this player" not in lowered
        assert "target " not in lowered
        assert "trade for" not in lowered
        assert "sell " not in lowered
        assert "cut " not in lowered


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
