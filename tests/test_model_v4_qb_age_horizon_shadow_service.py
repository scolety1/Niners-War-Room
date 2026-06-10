from __future__ import annotations

from pathlib import Path

from src.services.model_v4_qb_age_horizon_shadow_service import (
    build_qb_age_horizon_shadow,
    write_qb_age_horizon_shadow_exports,
)


def test_old_pocket_qb_shadow_cap_keeps_promoted_stafford_guarded() -> None:
    result = build_qb_age_horizon_shadow()
    stafford = _watch_row(result, "Matthew Stafford")

    assert stafford["baseline_rank"] == "91"
    assert stafford["shadow_rank"] == stafford["baseline_rank"]
    assert float(stafford["shadow_score"]) == 23.5
    assert float(stafford["score_delta"]) == 0.0
    assert "old_pocket_qb_already_below_horizon_cap" in stafford["reason_codes"]
    assert stafford["role_archetype"] == "qb_pocket_leaning"


def test_shadow_cap_does_not_crush_elite_or_younger_qbs() -> None:
    result = build_qb_age_horizon_shadow()

    for player in ("Josh Allen", "Jalen Hurts", "Lamar Jackson", "Patrick Mahomes"):
        row = _watch_row(result, player)
        assert float(row["score_delta"]) == 0.0
        assert "old_pocket_qb_horizon_cap_applied" not in row["reason_codes"]

    for player in ("Dak Prescott", "Jared Goff", "Baker Mayfield"):
        row = _watch_row(result, player)
        assert float(row["score_delta"]) == 0.0


def test_rodgers_is_already_below_old_pocket_cap_when_present() -> None:
    result = build_qb_age_horizon_shadow()
    rodgers = _watch_row(result, "Aaron Rodgers")

    assert float(rodgers["score_delta"]) == 0.0
    assert "old_pocket_qb_already_below_horizon_cap" in rodgers["reason_codes"]


def test_shadow_exports_and_guardrails(tmp_path: Path) -> None:
    result = build_qb_age_horizon_shadow()
    paths = write_qb_age_horizon_shadow_exports(output_root=tmp_path, result=result)

    assert paths.rankings.exists()
    assert paths.watch_rows.exists()
    assert paths.gate_report.exists()
    assert all(row["status"] == "pass" for row in result.gate_rows)

    gates = {row["gate"]: row for row in result.gate_rows}
    assert gates["banned_scoring_input_count"]["observed_value"] == 0
    assert gates["non_qb_score_changes"]["observed_value"] == 0
    assert gates["elite_rushing_qbs_not_crushed"]["observed_value"] == 0


def _watch_row(result, player: str) -> dict[str, object]:
    return next(row for row in result.watch_rows if row["player"] == player)
