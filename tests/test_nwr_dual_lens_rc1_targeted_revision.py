from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BUILDER = (
    ROOT
    / "scripts/build_nwr_dual_lens_rc1_targeted_revision_v1_20260729.py"
)
ORIGINAL = ROOT / "docs/hq/master/nwr_dual_lens_rc1_v1_20260729"
PACKET = (
    ROOT
    / "docs/hq/master/nwr_dual_lens_rc1_targeted_revision_v1_20260729"
)


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "nwr_dual_lens_targeted_revision", BUILDER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_all_real_path_mutations_fail_closed() -> None:
    results = pd.read_csv(PACKET / "MUTATION_RESULTS_BEFORE_AFTER.csv")
    assert results["mutation_id"].tolist() == [f"M{index:02d}" for index in range(1, 21)]
    assert results["result"].eq("PASS").all()
    assert results["observed"].eq("DETECTED").all()
    assert results["actual_failure"].ne("NO_FAILURE").all()
    assert results["actual_failure"].str.startswith("UNEXPECTED_").sum() == 0
    assert results["production_function_or_path_exercised"].str.len().gt(10).all()
    assert results["evidence_artifact"].str.contains(
        "test_all_real_path_mutations_fail_closed", regex=False
    ).all()


def test_availability_semantics_are_separate_and_valid() -> None:
    results = pd.read_csv(PACKET / "AVAILABILITY_CALIBRATION_RESULTS.csv")
    continuous = results.loc[
        results["target"].eq("EXPECTED_GAMES_FRACTION")
    ]
    binary = results.loc[results["target"].eq("P_GAMES_PLAYED_GE_8")]
    assert not continuous.empty and not binary.empty
    assert continuous["metric_family"].eq("CONTINUOUS_EXPECTATION").all()
    assert continuous[["brier", "log_loss", "ece"]].isna().all().all()
    assert continuous[["mae", "rmse", "mean_residual"]].notna().all().all()
    assert binary["metric_family"].eq("BINARY_PROBABILITY").all()
    assert binary[["mae", "rmse", "mean_residual"]].isna().all().all()
    assert binary[["brier", "log_loss", "ece"]].notna().all().all()
    overall = binary.loc[binary["scope_type"].eq("OVERALL")].iloc[0]
    assert overall["rows"] >= 500
    assert overall["events"] >= 50
    assert pd.notna(overall["calibration_slope"])
    assert pd.notna(overall["calibration_intercept"])


def test_primary_ndcg_is_season_aware_with_pooled_diagnostic_only() -> None:
    results = pd.read_csv(PACKET / "SEASON_AWARE_NDCG_RESULTS.csv")
    overall = results.loc[results["scope_type"].eq("OVERALL")]
    assert len(overall) == 8
    assert overall["ndcg_primary_aggregate"].eq(
        "UNWEIGHTED_MEAN_OF_TARGET_SEASON_NDCG"
    ).all()
    required = {
        "ndcg",
        "ndcg_pooled_diagnostic",
        "ndcg_row_weighted_mean",
        "ndcg_median",
        "ndcg_worst_season",
        "ndcg_ci_low",
        "ndcg_ci_high",
    }
    assert required.issubset(results.columns)
    assert results.loc[
        results["scope_type"].eq("SEASON"), "ndcg"
    ].notna().all()


def test_current_cohort_inventory_is_complete_and_mechanical() -> None:
    completeness = pd.read_csv(PACKET / "COHORT_COMPLETENESS_RESULTS.csv")
    assert len(completeness) == 240
    assert completeness["nwr_player_id"].is_unique
    assert completeness["included"].all()
    assert completeness["duplicate_free"].all()
    assert completeness["cohort_correct"].all()
    assert completeness["status"].eq("PASS_COMPLETE").all()
    second_year = completeness.loc[
        completeness["expected_cohort"].eq("SECOND_YEAR")
    ]
    assert len(second_year) == 43
    assert {"LeQuint Allen", "Jaydon Blue", "Kaleb Johnson"}.issubset(
        set(second_year["player_name"])
    )
    original_review = (
        ORIGINAL / "CMC_AJ_BROWN_JONATHAN_TAYLOR_REVIEW.md"
    ).read_text(encoding="utf-8")
    for player in ("LeQuint Allen", "Jaydon Blue", "Kaleb Johnson"):
        assert player in original_review


def test_rookie_evidence_stays_fail_closed_after_complete_cohorts() -> None:
    results = pd.read_csv(PACKET / "ROOKIE_SECOND_YEAR_REVALIDATION.csv")
    rookies = results.loc[results["cohort"].eq("TRUE_ROOKIE")]
    assert not rookies.empty
    assert rookies["rookie_evidence_disposition"].eq(
        "ROOKIE_EVIDENCE_INSUFFICIENT"
    ).all()
    assert results["dedicated_rookie_model_justified"].eq(
        "NO_SOURCE_AUTHORITY_TRUE_ROOKIE_ROWS_ZERO"
    ).all()
    historical = rookies.loc[
        rookies["record_type"].eq("HISTORICAL_OOF_METRIC")
    ]
    assert historical["eligible_rows"].eq(0).all()


def test_corrected_board_and_team_window_remain_research_only() -> None:
    board = pd.read_csv(PACKET / "CORRECTED_DUAL_LENS_SHADOW_BOARD.csv")
    assert len(board) == 240
    assert board["release_identifier_dual_lens"].eq(
        "NWR_DUAL_LENS_RC1_TARGETED_REVISION_RESEARCH_ONLY_NOT_ADMITTED"
    ).all()
    assert {
        "expected_games_fraction",
        "expected_games_played",
        "availability_8plus_probability",
    }.issubset(board.columns)
    unsupported = board.loc[~board["source_ready"]]
    assert unsupported["win_now_score"].isna().all()
    assert unsupported["dynasty_value_score"].isna().all()
    valid = board.dropna(
        subset=["win_now_normalized_score", "dynasty_normalized_score"]
    )
    expected = (
        0.75 * valid["win_now_normalized_score"]
        + 0.25 * valid["dynasty_normalized_score"]
    )
    assert (
        valid["contending_team_window_score"].sub(expected).abs().max() < 1e-7
    )


def test_formulas_fail_closed_and_no_production_integration_exists() -> None:
    win = pd.read_csv(PACKET / "WIN_NOW_GATE_REVALIDATION.csv")
    dynasty = pd.read_csv(PACKET / "DYNASTY_GATE_REVALIDATION.csv")
    assert not win["status"].eq("PASS").all()
    assert not dynasty["status"].eq("PASS").all()
    verdict = (PACKET / "EXECUTIVE_VERDICT.md").read_text(encoding="utf-8")
    assert "WIN_NOW_FORMULA_NOT_ADMITTED" in verdict
    assert "DYNASTY_FORMULA_NOT_ADMITTED" in verdict
    assert "production/UI integration is `NONE`" in verdict


def test_inventory_is_mechanical_complete_and_includes_gitattributes() -> None:
    inventory = pd.read_csv(PACKET / "FILES_CREATED_OR_CHANGED.csv")
    paths = set(inventory["path"])
    assert ".gitattributes" in paths
    assert (
        "scripts/build_nwr_dual_lens_rc1_targeted_revision_v1_20260729.py"
        in paths
    )
    assert (
        "tests/test_nwr_dual_lens_rc1_targeted_revision.py"
        in paths
    )
    assert inventory["mechanical_source"].str.contains(
        "git diff --name-status", regex=False
    ).all()
    original = pd.read_csv(ORIGINAL / "FILES_CREATED_OR_CHANGED.csv")
    assert set(original["path"]) == paths


def test_targeted_manifest_is_complete_non_self_referential_and_exact() -> None:
    module = _load_builder()
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["self_referential"] is False
    assert manifest["production_integration"] is False
    assert manifest["primary_ndcg_aggregate"] == (
        "UNWEIGHTED_MEAN_OF_TARGET_SEASON_NDCG"
    )
    listed = {row["path"]: row for row in manifest["files"]}
    assert "MANIFEST.json" not in listed
    for filename in module.TARGETED_REQUIRED_OUTPUTS:
        assert (PACKET / filename).is_file()
    for filename, row in listed.items():
        path = PACKET / filename
        assert path.stat().st_size == row["bytes"]
        assert _sha256(path) == row["sha256"]


def test_production_baselines_are_unchanged() -> None:
    module = _load_builder()
    for relative, expected in (
        (module.base.BOARD_REL, module.base.EXPECTED_HASHES[module.base.BOARD_REL]),
        (
            module.base.FROZEN_REL,
            module.base.EXPECTED_HASHES[module.base.FROZEN_REL],
        ),
        (
            module.base.OUTCOME_BOARD_REL,
            module.base.EXPECTED_HASHES[module.base.OUTCOME_BOARD_REL],
        ),
        (
            module.base.OUTCOME_SCHEMA_REL,
            module.base.EXPECTED_HASHES[module.base.OUTCOME_SCHEMA_REL],
        ),
    ):
        assert _sha256(ROOT / relative) == expected
