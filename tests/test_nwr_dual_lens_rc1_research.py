from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_nwr_dual_lens_rc1_v1_20260729.py"
PACKET = ROOT / "docs/hq/master/nwr_dual_lens_rc1_v1_20260729"


def _load_builder():
    spec = importlib.util.spec_from_file_location("nwr_dual_lens_research", BUILDER)
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


def test_candidate_registry_is_bounded_and_has_no_v2_2_chain() -> None:
    module = _load_builder()
    definitions = module.formula_definitions()
    assert definitions["candidate_id"].tolist() == [
        "W0_FINISHED_V1_ACCEPTED_PROXY",
        "W1_NEXT_SEASON_VOR",
        "W2_CONDITIONAL_PRODUCTION_AVAILABILITY",
        "W3_SHORT_HORIZON_CALIBRATED_BLEND",
        "D0_FINISHED_V1_ACCEPTED_PROXY",
        "D1_DISCOUNTED_MULTI_HORIZON_VOR",
        "D2_FUTURE_PRODUCTION_X_RETENTION",
        "D3_CAPPED_CAREER_HORIZON_GUARDS",
    ]
    assert definitions["bounded_search"].all()
    assert not definitions.astype(str).apply(
        lambda column: column.str.contains("V2-2|V2_2", case=False).any()
    ).any()


def test_fixed_baselines_and_outcome_v3_are_byte_identical() -> None:
    module = _load_builder()
    for relative, expected in (
        (module.BOARD_REL, module.EXPECTED_HASHES[module.BOARD_REL]),
        (module.FROZEN_REL, module.EXPECTED_HASHES[module.FROZEN_REL]),
        (
            module.OUTCOME_BOARD_REL,
            module.EXPECTED_HASHES[module.OUTCOME_BOARD_REL],
        ),
        (
            module.OUTCOME_SCHEMA_REL,
            module.EXPECTED_HASHES[module.OUTCOME_SCHEMA_REL],
        ),
    ):
        assert _sha256(ROOT / relative) == expected
    assert len(pd.read_csv(ROOT / module.BOARD_REL)) == 240
    assert len(pd.read_csv(ROOT / module.FROZEN_REL)) == 924
    assert len(pd.read_csv(ROOT / module.OUTCOME_SCHEMA_REL)) == 79
    outcome_root = ROOT / module.OUTCOME_SCHEMA_REL.parent
    outcome_manifest = json.loads(
        (outcome_root / "MANIFEST.json").read_text(encoding="utf-8")
    )
    outcome_entries = {
        row["path"]: row for row in outcome_manifest["artifacts"]
    }
    for relative in (module.OUTCOME_BOARD_REL, module.OUTCOME_SCHEMA_REL):
        entry = outcome_entries[relative.name]
        assert entry["sha256"] == module.EXPECTED_HASHES[relative]
        assert entry["bytes"] == (ROOT / relative).stat().st_size
    integration = outcome_root / "OUTCOME_V3_INTEGRATION_PACK.csv"
    integration_entry = outcome_entries[integration.name]
    assert _sha256(integration) == integration_entry["sha256"]
    assert integration.stat().st_size == integration_entry["bytes"]
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert (
        "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/** text eol=lf"
        in attributes.splitlines()
    )


def test_deterministic_float_serialization_ignores_sub_precision_runtime_noise() -> None:
    module = _load_builder()
    assert module.canonical_hash({"value": 0.12345678901231}) == module.canonical_hash(
        {"value": 0.12345678901232}
    )
    assert module.stable_markdown_float(0.9987731370189845) == "0.998773137"
    assert module.stable_markdown_float(-0.0) == "0.0"


def test_shadow_board_is_detached_transparent_and_null_fenced() -> None:
    board = pd.read_csv(PACKET / "CURRENT_2026_DUAL_LENS_SHADOW_BOARD.csv")
    assert len(board) == 240
    assert board["release_identifier_dual_lens"].eq(
        "NWR_DUAL_LENS_RC1_RESEARCH_ONLY_NOT_ADMITTED"
    ).all()
    assert board["rank_scope"].eq(
        "SCORED_REVIEW_ONLY_SUBSET_NOT_240_PLAYER_PRODUCTION_RANK"
    ).all()
    assert board["win_now_score"].notna().sum() == 227
    assert board["dynasty_value_score"].notna().sum() == 227
    unsupported = board.loc[~board["source_ready"]]
    assert len(unsupported) == 13
    assert unsupported["win_now_score"].isna().all()
    assert unsupported["dynasty_value_score"].isna().all()
    assert unsupported["balanced_team_window_score"].isna().all()
    assert board["is_rookie"].sum() == 0
    assert {
        "w1_score",
        "w2_score",
        "w3_score",
        "w3_weight_w1",
        "w3_weight_w2",
        "d_h1_pred",
        "d_h2_pred",
        "d_h3_pred",
        "retention_h2_predicted",
        "retention_h3_predicted",
        "contending_win_now_weight",
        "contending_dynasty_weight",
        "balanced_win_now_weight",
        "balanced_dynasty_weight",
        "rebuilding_win_now_weight",
        "rebuilding_dynasty_weight",
        "outcome_v3_next_year_context",
        "reason_codes",
        "confidence",
        "missing_reason",
    }.issubset(board.columns)
    assert board.loc[board["source_ready"], "multiyear_feature_status"].str.startswith(
        "DERIVED_REVIEW_ONLY"
    ).all()


def test_team_window_blends_normalized_scores_with_visible_weights() -> None:
    board = pd.read_csv(PACKET / "CURRENT_2026_DUAL_LENS_SHADOW_BOARD.csv")
    valid = board.dropna(
        subset=["win_now_normalized_score", "dynasty_normalized_score"]
    )
    for prefix, win_weight in (
        ("contending", 0.75),
        ("balanced", 0.50),
        ("rebuilding", 0.25),
    ):
        dynasty_weight = 1.0 - win_weight
        expected = (
            win_weight * valid["win_now_normalized_score"]
            + dynasty_weight * valid["dynasty_normalized_score"]
        )
        assert valid[f"{prefix}_win_now_weight"].eq(win_weight).all()
        assert valid[f"{prefix}_dynasty_weight"].eq(dynasty_weight).all()
        assert (
            valid[f"{prefix}_team_window_score"].sub(expected).abs().max() < 1e-7
        )
    contract = (PACKET / "TEAM_WINDOW_CONTRACT.md").read_text(encoding="utf-8")
    assert "Raw ranks are never blended" in contract
    assert "universally optimal" in contract


def test_true_rookie_and_injury_return_claims_fail_closed() -> None:
    cohorts = pd.read_csv(PACKET / "ROOKIE_VETERAN_EVALUATION.csv")
    true_rookie = cohorts.loc[cohorts["cohort"].eq("TRUE_ROOKIE")]
    assert len(true_rookie) == 2
    assert true_rookie["eligible_rows"].eq(0).all()
    assert true_rookie["status"].eq("UNSUPPORTED_ZERO_ROWS").all()
    injury = cohorts.loc[cohorts["cohort"].eq("INJURY_RETURN")]
    assert injury["status"].eq("SOURCE_BLOCKED_NO_INJURY_RETURN_AUTHORITY").all()
    authority = pd.read_csv(PACKET / "ROOKIE_EVIDENCE_AUTHORITY.csv")
    statuses = dict(
        zip(authority["feature"], authority["classification"], strict=True)
    )
    assert statuses["true-rookie evaluation label"] == "insufficient"
    assert statuses["injury-return cohort authority"] == "source-blocked"
    assert statuses["NFL draft capital"] == "review-only"


def test_both_formula_lanes_fail_closed_and_no_ui_is_installed() -> None:
    win = pd.read_csv(PACKET / "WIN_NOW_ACCEPTANCE_GATE_MATRIX.csv")
    dynasty = pd.read_csv(PACKET / "DYNASTY_ACCEPTANCE_GATE_MATRIX.csv")
    assert not win["status"].eq("PASS").all()
    assert not dynasty["status"].eq("PASS").all()
    assert win.loc[win["gate_id"].eq("W-G11"), "status"].item() == "FAIL"
    assert dynasty.loc[dynasty["gate_id"].eq("D-G12"), "status"].item() == "FAIL"
    audit = pd.read_csv(PACKET / "CORE_APP_REFRESH_AUDIT.csv")
    assert audit["recommended_action"].str.contains(
        "NO_CHANGE|DESIGN_READY|DOCUMENT_RESEARCH"
    ).all()
    viewport = pd.read_csv(PACKET / "VIEWPORT_AND_ACCESSIBILITY_RESULTS.csv")
    assert viewport["dual_lens_integration_present"].eq(False).all()  # noqa: E712
    assert viewport["status"].eq(
        "NOT_APPLICABLE_PRODUCTION_UI_NOT_INTEGRATED"
    ).all()


def test_mutations_are_detected_and_outcome_is_not_a_formula_input() -> None:
    results = pd.read_csv(PACKET / "MUTATION_SENSITIVITY_RESULTS.csv")
    assert len(results) == 19
    assert results["observed"].eq("DETECTED").all()
    assert results["result"].eq("PASS").all()
    module = _load_builder()
    assert not any("OUTCOME" in feature.upper() for feature in module.COMMON_FEATURES)
    assert "player_name" not in module.COMMON_FEATURES
    assert "current_adp" not in module.COMMON_FEATURES


def test_manifest_is_non_self_referential_and_complete() -> None:
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["self_referential"] is False
    assert manifest["production_integration"] is False
    assert manifest["win_now_admitted"] is False
    assert manifest["dynasty_admitted"] is False
    listed = {row["path"]: row for row in manifest["files"]}
    assert "MANIFEST.json" not in listed
    module = _load_builder()
    for filename in module.REQUIRED_OUTPUTS:
        assert (PACKET / filename).is_file()
    for filename, row in listed.items():
        path = PACKET / filename
        assert path.stat().st_size == row["bytes"]
        assert _sha256(path) == row["sha256"]


def test_builder_has_local_research_only_write_contract() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    assert "requests" not in source
    assert "http://" not in source
    assert "https://" not in source
    assert "_manual_recovery_dropzone" not in source
    assert "shutil.rmtree(output)" in source
    assert "inside-repository output must be the governed dual-lens packet path" in source
    assert "production_integration" in source
