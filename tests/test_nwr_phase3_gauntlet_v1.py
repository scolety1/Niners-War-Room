from __future__ import annotations

import json
from pathlib import Path

from scripts.run_nwr_phase3_gauntlet_v1 import (
    FAMILIES,
    PACKET_RELATIVE,
    TARGETS,
    _target_frame,
    generated_outputs,
    load_inputs,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def test_governed_inputs_have_exact_universe_and_keys() -> None:
    frame = load_inputs(ROOT)
    assert len(frame) == 5518
    assert not frame[["player_id", "season", "position"]].duplicated().any()
    assert set(frame["position"]) == {"QB", "RB", "WR", "TE"}


def test_feature_registry_is_exact_and_bounded() -> None:
    assert set(FAMILIES) == {
        "PRODUCTION_PERSISTENCE_2Y",
        "ROLE_OPPORTUNITY_VOLUME",
        "ROLE_TRAJECTORY_DELTA",
        "RB_HIGH_LEVERAGE_RUSHING",
        "QB_RUSHING_OPPORTUNITY",
    }
    assert len(FAMILIES) == 5


def test_target_components_remain_separate_and_horizon_closed() -> None:
    frame = load_inputs(ROOT)
    assert TARGETS == {
        "WIN_NOW_POINTS_T0": (0, 2025),
        "TWO_YEAR_POINTS_T1": (1, 2024),
        "THREE_YEAR_POINTS_T2": (2, 2023),
    }
    for horizon, maximum_anchor in TARGETS.values():
        target = _target_frame(frame, horizon, maximum_anchor)
        assert int(target["season"].max()) == maximum_anchor
        assert (target["outcome_season"] == target["season"] + horizon).all()


def test_missingness_is_not_zero_filled() -> None:
    frame = load_inputs(ROOT)
    assert frame["age_bucket"].isna().sum() >= 8
    assert frame.loc[frame["age_bucket"].isna(), "lifecycle_bucket"].isna().all()


def test_generated_evidence_is_deterministic() -> None:
    first = generated_outputs(ROOT)
    second = generated_outputs(ROOT)
    assert first == second
    assert set(first) == {
        "GAUNTLET_RESULTS.csv",
        "GUARDRAIL_RESULTS.csv",
        "FAMILY_DECISIONS.csv",
        "GAUNTLET_SUMMARY.json",
    }


def test_truthful_null_result_and_no_production_mutation() -> None:
    summary = json.loads(generated_outputs(ROOT)["GAUNTLET_SUMMARY.json"])
    assert summary["overall_verdict"] == "NULL_NO_FAMILY_PASSED"
    assert summary["families_passed"] == []
    assert summary["production_changes"] == 0
    assert summary["provider_calls"] == 0


def test_packet_and_manifest_validate() -> None:
    result = validate(ROOT)
    assert result["valid"] is True
    assert result["families_tested"] == 5
    assert (ROOT / PACKET_RELATIVE / "MANIFEST.json").is_file()
