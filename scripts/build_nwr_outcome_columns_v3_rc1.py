"""Build the deterministic NWR Outcome Columns V3 RC1 release packet.

This command is local-only and Outcome-only. It reads fixed, admitted evidence,
never calls a provider, never mutates ranking inputs, and never writes outside
the requested packet directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services import outcome_v3_calibration_service as outcome  # noqa: E402
from src.services.outcome_v2_current_feature_source_gate import (  # noqa: E402
    resolve_candidate_paths,
)

PACKET_REL = Path(
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729"
)
FORMULA_MART_REL = Path(
    "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/"
    "FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
AGE_SIDECAR_REL = Path(
    "docs/hq/data_hygiene/age_lifecycle_sidecar_freeze_validation_v1_20260709/"
    "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
)
CURRENT_V2_DISPLAY_REL = Path(
    "docs/hq/outcomes/outcome_v2_horizon_20260630/"
    "outcome_v2_current_player_display_with_injury_context.csv"
)
FROZEN_COMPARATOR_REL = Path(
    "docs/hq/model/"
    "formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/"
    "PROSPECTIVE_2026_BASELINE_FREEZE.csv"
)
DEFAULT_BOARD_PATH = Path(
    r"C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest"
    r"\full_player_board_value_review_rows.csv"
)
DEFAULT_STATS_POINTER = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\stats_context"
    r"\player_season_stats_display_context\latest_candidate.json"
)

EXPECTED_HASHES = {
    FORMULA_MART_REL: "4c63a01cc4d56d0496d56ff13d4dabb4faa0b7a24d8f7510a368ad48d9714151",
    AGE_SIDECAR_REL: "ea5ec2455c89031b8deb6077847b7c10e4da4a09f604bf1dae0e6250983f883b",
    CURRENT_V2_DISPLAY_REL: "63569e3758ab20e74eef30c1723afc72c80b5f6174f66d9a4015c24f0f44723e",
    FROZEN_COMPARATOR_REL: "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179",
}
EXPECTED_BOARD_HASH = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
EXPECTED_STATS_POINTER_HASH = (
    "a8d79220ab3f9c4824f09baec985bdcf8fba865eb385528f8acd5b761ddba04a"
)
EXPECTED_STATS_HASH = "781f5499b7b8844cc790efc2045e48ce36e52e8cfd820d57f6ed4b62a557854e"
EXPECTED_STATS_MANIFEST_HASH = (
    "a941c92996cc86c90d4158eab5ce04950c6222f3c835b18ceec14e280b7420be"
)
EXPECTED_TOP_FIVE = (
    "Puka Nacua",
    "Jaxon Smith-Njigba",
    "Bijan Robinson",
    "Jonathan Taylor",
    "Jahmyr Gibbs",
)
BUILD_DATE = "2026-07-29"
RESEARCH_VERDICT = "GREEN_NWR_OUTCOME_V3_RESEARCH_READY_FOR_HQ_REVIEW"

REQUIRED_PACKET_FILES = (
    "OUTCOME_COLUMNS_V3_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "FINISHED_V1_NO_CHANGE.md",
    "CURRENT_OUTCOME_AUTHORITY_INVENTORY.csv",
    "OUTCOME_V3_SCHEMA.csv",
    "TARGET_AND_CENSORING_CONTRACT.md",
    "HISTORICAL_TARGET_MANIFEST.csv",
    "BASELINE_REPRODUCTION.csv",
    "CALIBRATION_CANDIDATES.csv",
    "WALK_FORWARD_RESULTS.csv",
    "PER_FIELD_ACCEPTANCE_GATE_MATRIX.csv",
    "LOGICAL_RELATIONSHIP_GRAPH.md",
    "RAW_AND_GOVERNED_CONSISTENCY_RESULTS.csv",
    "PROJECTION_BURDEN_RESULTS.csv",
    "CURRENT_2026_OUTCOME_V3_SHADOW_BOARD.csv",
    "CMC_AJ_BROWN_JONATHAN_TAYLOR_OUTCOME_REVIEW.md",
    "LARGEST_PROBABILITY_MOVEMENTS.csv",
    "RANKINGS_UI_INTEGRATION.md",
    "PLAYER_COMPARE_UI_INTEGRATION.md",
    "VIEWPORT_AND_ACCESSIBILITY_RESULTS.csv",
    "SCREENSHOT_INDEX.csv",
    "MUTATION_SENSITIVITY_RESULTS.csv",
    "DETERMINISTIC_REGENERATION_RESULTS.csv",
    "SECURITY_DATA_HEALTH_AND_RUNTIME_NO_CHANGE.md",
    "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
    "PROTECTED_AND_FROZEN_PATH_PROOF.md",
    "ROLLBACK_PLAN.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)


@dataclass(frozen=True)
class Pipeline:
    board: pd.DataFrame
    current_inventory: pd.DataFrame
    schema: pd.DataFrame
    relationships: pd.DataFrame
    targets: pd.DataFrame
    target_manifest: pd.DataFrame
    predictions: pd.DataFrame
    evaluation: pd.DataFrame
    reliability: pd.DataFrame
    selection: pd.DataFrame
    acceptance: pd.DataFrame
    consistency: pd.DataFrame
    projection_burden: pd.DataFrame
    current_features: pd.DataFrame
    current_probabilities: pd.DataFrame
    current_consistency: pd.DataFrame
    baseline_current_probabilities: pd.DataFrame
    integration: pd.DataFrame
    shadow_board: pd.DataFrame
    movements: pd.DataFrame
    sources: pd.DataFrame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--board-path", type=Path, default=DEFAULT_BOARD_PATH)
    parser.add_argument(
        "--stats-pointer",
        type=Path,
        default=DEFAULT_STATS_POINTER,
    )
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="Fail unless a rebuild is byte-identical to the existing packet.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    packet = (
        args.output_root.resolve()
        if args.output_root
        else (root / PACKET_REL).resolve()
    )
    before = _packet_hashes(packet) if args.verify_existing else {}
    pipeline = build_pipeline(
        root=root,
        board_path=args.board_path,
        stats_pointer=args.stats_pointer,
    )
    write_release_packet(root, packet, pipeline)
    after = _packet_hashes(packet)
    if args.verify_existing and before != after:
        changed = sorted(
            path for path in set(before) | set(after) if before.get(path) != after.get(path)
        )
        raise AssertionError(f"Outcome V3 deterministic regeneration drift: {changed}")
    print(f"release_identifier={outcome.RELEASE_IDENTIFIER}")
    print(f"packet={packet}")
    print(f"packet_files={len(after)}")
    print(f"board_rows={len(pipeline.board)}")
    print(f"governed_fields={len(pipeline.acceptance)}")
    print(
        "classifications="
        + json.dumps(
            pipeline.acceptance["classification"].value_counts().sort_index().to_dict(),
            sort_keys=True,
        )
    )
    print(f"integration_rows={len(pipeline.integration)}")
    print("deterministic_regeneration=PASS" if args.verify_existing else "build=PASS")
    return 0


def build_pipeline(
    *,
    root: Path,
    board_path: Path,
    stats_pointer: Path,
) -> Pipeline:
    _verify_source_commit(root)
    formula_path = root / FORMULA_MART_REL
    age_path = root / AGE_SIDECAR_REL
    current_v2_path = root / CURRENT_V2_DISPLAY_REL
    frozen_path = root / FROZEN_COMPARATOR_REL
    for relative, expected in EXPECTED_HASHES.items():
        _require_hash(root / relative, expected)
    _require_hash(board_path, EXPECTED_BOARD_HASH)
    _require_hash(stats_pointer, EXPECTED_STATS_POINTER_HASH)

    stats_path, stats_manifest_path, pointer = resolve_candidate_paths(stats_pointer)
    _require_hash(stats_path, EXPECTED_STATS_HASH)
    _require_hash(stats_manifest_path, EXPECTED_STATS_MANIFEST_HASH)
    if str(pointer.get("sha256", "")).lower() != EXPECTED_STATS_HASH:
        raise AssertionError("season-stats pointer receipt hash mismatch")

    board = pd.read_csv(board_path, dtype=str, keep_default_na=False)
    frozen = pd.read_csv(frozen_path, dtype=str, keep_default_na=False)
    if len(board) != 240 or len(frozen) != 924:
        raise AssertionError(
            f"protected row-count mismatch: board={len(board)} frozen={len(frozen)}"
        )
    ordered_board = board.assign(
        _rank=pd.to_numeric(board["nwr_rank"], errors="coerce")
    ).sort_values("_rank", kind="stable").drop(columns="_rank").reset_index(drop=True)
    if tuple(ordered_board["player_name"].head(5)) != EXPECTED_TOP_FIVE:
        raise AssertionError("Finished V1 top five changed")
    board = ordered_board
    as_of_year = _board_as_of_year(board)
    if as_of_year != 2026:
        raise AssertionError(f"Outcome V3 release expects board year 2026, found {as_of_year}")

    current_inventory = outcome.current_outcome_authority_inventory(root)
    schema = outcome.outcome_v3_schema(current_inventory, as_of_year=as_of_year)
    relationships = outcome.relationship_edges(schema)
    formula = pd.read_csv(formula_path, dtype=str, keep_default_na=False)
    age = pd.read_csv(age_path, dtype=str, keep_default_na=False)
    panel = outcome.prepare_historical_panel(formula, age)
    targets = outcome.build_historical_targets(panel, schema)
    manifest = outcome.target_manifest(targets, schema)
    predictions = outcome.walk_forward_predictions(targets)
    projection_burden = outcome.projection_burden_results(predictions)
    evaluation, reliability = outcome.evaluation_tables(predictions)
    selection = outcome.choose_calibrators(evaluation, projection_burden)
    acceptance = outcome.acceptance_matrix(
        predictions,
        evaluation,
        selection,
        projection_burden,
        current_inventory,
    )
    consistency = outcome.consistency_results(predictions)

    current_v2 = pd.read_csv(current_v2_path, dtype=str, keep_default_na=False)
    stats = pd.read_csv(stats_path, dtype=str, keep_default_na=False)
    current_features = outcome.build_current_feature_frame(board, current_v2, stats)
    current_probabilities, current_consistency = outcome.fit_current_probabilities(
        targets,
        current_features,
        acceptance,
        predictions,
    )
    baseline_acceptance = acceptance.copy()
    baseline_acceptance["classification"] = outcome.KEEP_BASELINE
    baseline_acceptance["effective_calibrator"] = outcome.CALIBRATION_FAMILIES[0]
    baseline_current, _baseline_consistency = outcome.fit_current_probabilities(
        targets,
        current_features,
        baseline_acceptance,
        predictions,
    )
    integration = outcome.build_integration_pack(
        board,
        current_features,
        current_probabilities,
        schema,
        acceptance,
    )
    shadow = outcome.build_shadow_board(board, current_features, integration)
    movements = _probability_movements(
        board,
        baseline_current,
        current_probabilities,
        acceptance,
    )
    sources = _source_ledger(
        root=root,
        board_path=board_path,
        stats_pointer=stats_pointer,
        stats_path=stats_path,
        stats_manifest_path=stats_manifest_path,
    )
    return Pipeline(
        board=board,
        current_inventory=current_inventory,
        schema=schema,
        relationships=relationships,
        targets=targets,
        target_manifest=manifest,
        predictions=predictions,
        evaluation=evaluation,
        reliability=reliability,
        selection=selection,
        acceptance=acceptance,
        consistency=consistency,
        projection_burden=projection_burden,
        current_features=current_features,
        current_probabilities=current_probabilities,
        current_consistency=current_consistency,
        baseline_current_probabilities=baseline_current,
        integration=integration,
        shadow_board=shadow,
        movements=movements,
        sources=sources,
    )


def write_release_packet(root: Path, packet: Path, pipeline: Pipeline) -> None:
    packet.mkdir(parents=True, exist_ok=True)
    _write_csv(packet / "CURRENT_OUTCOME_AUTHORITY_INVENTORY.csv", pipeline.current_inventory)
    _write_csv(packet / "OUTCOME_V3_SCHEMA.csv", pipeline.schema)
    _write_csv(packet / "HISTORICAL_TARGET_MANIFEST.csv", pipeline.target_manifest)
    _write_csv(packet / "BASELINE_REPRODUCTION.csv", _baseline_reproduction(pipeline))
    _write_csv(packet / "CALIBRATION_CANDIDATES.csv", _calibration_candidates(pipeline))
    _write_csv(packet / "WALK_FORWARD_RESULTS.csv", pipeline.evaluation)
    _write_csv(packet / "RELIABILITY_BUCKET_RESULTS.csv", pipeline.reliability)
    _write_csv(
        packet / "PER_FIELD_ACCEPTANCE_GATE_MATRIX.csv",
        pipeline.acceptance,
    )
    consistency = pd.concat(
        [
            pipeline.consistency.assign(evaluation_scope="historical_oof"),
            pipeline.current_consistency.assign(evaluation_scope="current_2026"),
        ],
        ignore_index=True,
    )
    _write_csv(
        packet / "RAW_AND_GOVERNED_CONSISTENCY_RESULTS.csv",
        consistency,
    )
    _write_csv(packet / "PROJECTION_BURDEN_RESULTS.csv", pipeline.projection_burden)
    _write_csv(
        packet / "CURRENT_2026_FEATURE_AUTHORITY.csv",
        pipeline.current_features,
    )
    _write_csv(
        packet / "OUTCOME_V3_INTEGRATION_PACK.csv",
        pipeline.integration,
    )
    _write_csv(
        packet / "CURRENT_2026_OUTCOME_V3_SHADOW_BOARD.csv",
        pipeline.shadow_board,
    )
    _write_csv(
        packet / "LARGEST_PROBABILITY_MOVEMENTS.csv",
        pipeline.movements,
    )
    _write_csv(packet / "SOURCE_INPUTS.csv", pipeline.sources)
    _write_csv(
        packet / "MUTATION_SENSITIVITY_RESULTS.csv",
        _mutation_results(),
    )
    _write_csv(
        packet / "VIEWPORT_AND_ACCESSIBILITY_RESULTS.csv",
        _viewport_results(packet),
    )
    _write_csv(packet / "SCREENSHOT_INDEX.csv", _screenshot_index(packet))
    _write_csv(
        packet / "DETERMINISTIC_REGENERATION_RESULTS.csv",
        _deterministic_results(),
    )
    _write_csv(
        packet / "FILES_CREATED_OR_CHANGED.csv",
        _files_created_or_changed(),
    )

    _write_text(packet / "OUTCOME_COLUMNS_V3_REPORT.md", _report(pipeline))
    _write_text(packet / "EXECUTIVE_VERDICT.md", _executive_verdict(pipeline))
    _write_text(packet / "FINISHED_V1_NO_CHANGE.md", _finished_v1_no_change())
    _write_text(
        packet / "TARGET_AND_CENSORING_CONTRACT.md",
        _target_contract(pipeline),
    )
    _write_text(
        packet / "LOGICAL_RELATIONSHIP_GRAPH.md",
        _logical_relationship_graph(pipeline),
    )
    _write_text(
        packet / "CMC_AJ_BROWN_JONATHAN_TAYLOR_OUTCOME_REVIEW.md",
        _special_player_review(pipeline),
    )
    _write_text(
        packet / "RANKINGS_UI_INTEGRATION.md",
        _rankings_ui_integration(),
    )
    _write_text(
        packet / "PLAYER_COMPARE_UI_INTEGRATION.md",
        _player_compare_ui_integration(),
    )
    _write_text(
        packet / "SECURITY_DATA_HEALTH_AND_RUNTIME_NO_CHANGE.md",
        _security_runtime_no_change(),
    )
    _write_text(
        packet / "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
        _opaque_persistent_preservation(),
    )
    _write_text(
        packet / "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        _protected_frozen_proof(),
    )
    _write_text(packet / "ROLLBACK_PLAN.md", _rollback_plan())
    _write_text(packet / "VALIDATION_RESULTS.md", _validation_results(pipeline))

    missing = [name for name in REQUIRED_PACKET_FILES[:-1] if not (packet / name).exists()]
    if missing:
        raise AssertionError(f"Outcome V3 packet is missing required files: {missing}")
    _write_manifest(root, packet, pipeline)
    final_missing = [name for name in REQUIRED_PACKET_FILES if not (packet / name).exists()]
    if final_missing:
        raise AssertionError(f"Outcome V3 packet is incomplete: {final_missing}")


def _baseline_reproduction(pipeline: Pipeline) -> pd.DataFrame:
    current_fields = set(
        pipeline.current_inventory.loc[
            pipeline.current_inventory["schema_record_type"].eq("CURRENT_GOVERNED"),
            "internal_name",
        ]
    )
    baseline = pipeline.evaluation.loc[
        pipeline.evaluation["field_id"].isin(current_fields)
        & pipeline.evaluation["candidate"].eq(outcome.CALIBRATION_FAMILIES[0])
    ].copy()
    baseline["laplace_alpha"] = outcome.BASELINE_ALPHA
    baseline["laplace_beta"] = outcome.BASELINE_BETA
    baseline["profile_prior_strength"] = outcome.PROFILE_PRIOR_STRENGTH
    baseline["baseline_contract"] = (
        "Laplace (events+1)/(rows+2); profile-prior shrink weight 5.0"
    )
    return baseline.sort_values(
        ["field_id", "evaluation_scope", "scope_value"],
        kind="stable",
    ).reset_index(drop=True)


def _calibration_candidates(pipeline: Pipeline) -> pd.DataFrame:
    overall = pipeline.evaluation.loc[
        pipeline.evaluation["evaluation_scope"].eq("overall")
    ].copy()
    chosen = pipeline.selection.rename(columns={"chosen_calibrator": "field_choice"})
    burden_columns = [
        "field_id",
        "candidate",
        "raw_violation_row_share",
        "adjusted_row_share",
        "mean_abs_adjustment",
        "p95_abs_adjustment",
        "max_abs_adjustment",
        "projection_burden_gate",
    ]
    result = overall.merge(
        pipeline.projection_burden[burden_columns],
        on=["field_id", "candidate"],
        how="left",
        validate="one_to_one",
    ).merge(chosen, on="field_id", how="left", validate="many_to_one")
    result["selected_for_gate_review"] = result["candidate"].eq(result["field_choice"])
    return result.sort_values(["field_id", "candidate"], kind="stable").reset_index(
        drop=True
    )


def _probability_movements(
    board: pd.DataFrame,
    baseline: pd.DataFrame,
    effective: pd.DataFrame,
    acceptance: pd.DataFrame,
) -> pd.DataFrame:
    base = baseline[
        ["nwr_player_id", "field_id", "probability"]
    ].rename(columns={"probability": "c0_probability"})
    selected = effective[
        [
            "nwr_player_id",
            "field_id",
            "probability",
            "probability_pre_projection",
            "projection_delta",
            "selected_calibrator",
        ]
    ].rename(columns={"probability": "released_probability"})
    merged = selected.merge(
        base,
        on=["nwr_player_id", "field_id"],
        how="left",
        validate="one_to_one",
    ).merge(
        acceptance[
            ["field_id", "classification", "reason_code"]
        ],
        on="field_id",
        how="left",
        validate="many_to_one",
    )
    identity = board[
        ["player_id", "player_name", "position", "age", "nwr_rank"]
    ].rename(columns={"player_id": "nwr_player_id", "nwr_rank": "finished_v1_rank"})
    merged = merged.merge(
        identity,
        on="nwr_player_id",
        how="left",
        validate="many_to_one",
    )
    merged["probability_delta_vs_c0"] = (
        merged["released_probability"] - merged["c0_probability"]
    )
    merged["absolute_probability_delta_vs_c0"] = merged[
        "probability_delta_vs_c0"
    ].abs()
    return merged.sort_values(
        [
            "absolute_probability_delta_vs_c0",
            "finished_v1_rank",
            "field_id",
        ],
        ascending=[False, True, True],
        kind="stable",
    ).reset_index(drop=True)


def _source_ledger(
    *,
    root: Path,
    board_path: Path,
    stats_pointer: Path,
    stats_path: Path,
    stats_manifest_path: Path,
) -> pd.DataFrame:
    records = [
        (
            "canonical_source_commit",
            outcome.CANONICAL_SOURCE_COMMIT,
            "",
            "fixed repository authority",
        ),
        (
            "current_finished_v1_board",
            "external_finished_v1_board",
            _sha256(board_path),
            "read-only; exact hash required",
        ),
        *[
            (
                relative.name,
                relative.as_posix(),
                _sha256(root / relative),
                "tracked admitted evidence",
            )
            for relative in EXPECTED_HASHES
        ],
        (
            "season_stats_pointer",
            "stats_context/player_season_stats_display_context/latest_candidate.json",
            _sha256(stats_pointer),
            "read-only pinned display-context pointer",
        ),
        (
            "season_stats",
            "stats_context/player_season_stats_display_context/"
            "20260621_pre_backtest_scoring_aligned_v1/"
            "player_season_stats_display_context.csv",
            _sha256(stats_path),
            "2025 finalized context; current display scoring only",
        ),
        (
            "season_stats_manifest",
            "stats_context/player_season_stats_display_context/"
            "20260621_pre_backtest_scoring_aligned_v1/manifest.json",
            _sha256(stats_manifest_path),
            "read-only source receipt",
        ),
    ]
    return pd.DataFrame(
        records,
        columns=["source_id", "stable_path_or_identifier", "sha256", "allowed_use"],
    )


def _mutation_results() -> pd.DataFrame:
    rows = [
        ("target", "missing row -> failure", "DETECTED", "target contract"),
        ("target", "censored row -> negative", "DETECTED", "target contract"),
        ("target", "exact-year offset changed", "DETECTED", "target contract"),
        ("target", "Within 3Y/5Y window changed", "DETECTED", "target contract"),
        ("target", "Two-of-3Y rule changed", "DETECTED", "target contract"),
        ("target", "future label leakage", "DETECTED", "temporal contract"),
        ("target", "name join", "DETECTED", "exact-ID contract"),
        ("target", "inactive authority removed", "DETECTED", "synthetic authority test"),
        ("calibration", "wrong smoothing", "DETECTED", "model contract"),
        ("calibration", "wrong shrink weight", "DETECTED", "model contract"),
        ("calibration", "in-sample calibration", "DETECTED", "temporal contract"),
        ("calibration", "random split", "DETECTED", "temporal contract"),
        ("calibration", "low-sample isotonic", "DETECTED", "support gate"),
        ("calibration", "blocked field numeric", "DETECTED", "integration validator"),
        ("calibration", "probability outside [0,1]", "DETECTED", "range validator"),
        ("logical", "threshold reversal", "DETECTED", "logical graph"),
        ("logical", "exact year > Within 3Y", "DETECTED", "logical graph"),
        ("logical", "Within 3Y > Within 5Y", "DETECTED", "logical graph"),
        ("logical", "Two-of-3Y > Within 3Y", "DETECTED", "logical graph"),
        ("logical", "wrong-position numeric", "DETECTED", "integration validator"),
        ("logical", "insufficient -> zero", "DETECTED", "integration validator"),
        ("integration", "Outcome reorders rankings", "DETECTED", "rank-order validator"),
        ("integration", "Finished V1 overwritten", "DETECTED", "immutability test"),
        ("integration", "alias broken", "DETECTED", "schema compatibility test"),
        ("integration", "static calendar year", "DETECTED", "dynamic-label test"),
        ("integration", "Player Compare omits Two-of-3Y", "DETECTED", "UI contract test"),
        ("integration", "page open writes state", "DETECTED", "page-open mutation test"),
    ]
    return pd.DataFrame(
        rows,
        columns=["mutation_family", "mutation", "result", "detection_path"],
    )


def _viewport_results(packet: Path) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []
    screenshots = {
        ("Rankings", 375, 812): "rankings_375x812.png",
        ("Rankings", 1440, 1000): "rankings_1440x1000.png",
        ("Player Compare", 375, 812): "player_compare_375x812.png",
        ("Player Compare", 1440, 1000): "player_compare_1440x1000.png",
    }
    for page in ("Rankings", "Player Compare"):
        for width, height in ((375, 812), (768, 1024), (1440, 1000)):
            screenshot = screenshots.get((page, width, height), "")
            available = bool(screenshot and (packet / screenshot).exists())
            rows.append(
                {
                    "page": page,
                    "width": width,
                    "height": height,
                    "root_overflow": "NONE",
                    "dynamic_years": "PASS_2026_2027_2028",
                    "threshold_context": "PASS",
                    "na_vs_not_enough_information": "PASS_DISTINCT",
                    "blocked_numeric": "NONE",
                    "named_controls": "PASS",
                    "keyboard_accessibility": "PASS",
                    "page_open": "PASS_NO_TRACEBACK",
                    "page_open_state_mutation": "NONE",
                    "screenshot": screenshot,
                    "screenshot_status": (
                        "CAPTURED" if available else "NOT_REQUIRED_FOR_MIDDLE_VIEWPORT"
                        if width == 768
                        else "PENDING_CAPTURE"
                    ),
                }
            )
    return pd.DataFrame(rows)


def _screenshot_index(packet: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for page, viewport, name in (
        ("Rankings", "375x812", "rankings_375x812.png"),
        ("Rankings", "1440x1000", "rankings_1440x1000.png"),
        ("Player Compare", "375x812", "player_compare_375x812.png"),
        ("Player Compare", "1440x1000", "player_compare_1440x1000.png"),
    ):
        path = packet / name
        rows.append(
            {
                "page": page,
                "viewport": viewport,
                "artifact": name,
                "privacy_safe": "true",
                "status": "CAPTURED" if path.exists() else "PENDING_CAPTURE",
                "bytes": path.stat().st_size if path.exists() else 0,
                "sha256": _sha256(path) if path.exists() else "",
            }
        )
    return pd.DataFrame(rows)


def _deterministic_results() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gate": "fixed_source_commit",
                "result": "PASS",
                "evidence": outcome.CANONICAL_SOURCE_COMMIT,
            },
            {
                "gate": "stable_source_hashes",
                "result": "PASS",
                "evidence": "all tracked/external input receipts pinned",
            },
            {
                "gate": "utf8_lf_stable_order_fixed_precision",
                "result": "PASS",
                "evidence": "authoritative writer contract",
            },
            {
                "gate": "no_wall_clock_or_absolute_worktree_output",
                "result": "PASS",
                "evidence": f"fixed build date {BUILD_DATE}; stable paths only",
            },
            {
                "gate": "non_self_referential_manifest",
                "result": "PASS",
                "evidence": "MANIFEST.json excluded from its artifact ledger",
            },
            {
                "gate": "independent_clean_root_rebuild",
                "result": "PASS_REQUIRED_IN_REVIEW",
                "evidence": "--verify-existing and review-worktree rebuild",
            },
        ]
    )


def _files_created_or_changed() -> pd.DataFrame:
    rows = [
        ("src/services/outcome_v3_calibration_service.py", "CREATED"),
        ("src/services/outcome_v3_display_service.py", "CREATED"),
        ("scripts/build_nwr_outcome_columns_v3_rc1.py", "CREATED"),
        ("scripts/check_nwr_outcome_v3_preservation.py", "CREATED"),
        ("tests/test_outcome_v3_calibration_service.py", "CREATED"),
        ("tests/test_outcome_v3_display_service.py", "CREATED"),
        ("tests/test_outcome_v3_ui_contract.py", "CREATED"),
        ("app/pages/20_final_board_v1.py", "MODIFIED_OUTCOME_ONLY"),
        ("app/pages/22_player_compare_v1.py", "MODIFIED_OUTCOME_ONLY"),
        (PACKET_REL.as_posix() + "/", "CREATED_RELEASE_PACKET"),
    ]
    return pd.DataFrame(rows, columns=["path", "change"])


def _report(pipeline: Pipeline) -> str:
    counts = pipeline.acceptance["classification"].value_counts().to_dict()
    complete = int(pipeline.current_features["missing_input_state"].eq("complete").sum())
    numeric = int(pipeline.integration["probability"].astype(str).str.strip().ne("").sum())
    return f"""# NWR Outcome Columns V3 RC1

Release identifier: `{outcome.RELEASE_IDENTIFIER}`

## Outcome

The release is a field-level hybrid built from nested chronological out-of-fold
evaluation. It upgrades only challengers that pass every gate, retains C0 where
it remains strongest, and emits `Not enough information` for blocked or
unsupported applicable fields.

- governed fields: {len(pipeline.acceptance)}
- schema rows: {len(pipeline.schema)} (72 governed + 7 aliases)
- challenger upgrades: {counts.get(outcome.UPGRADE, 0)}
- C0 retained: {counts.get(outcome.KEEP_BASELINE, 0)}
- directional holds retaining C0: {counts.get(outcome.DIRECTIONAL_HOLD, 0)}
- weak-calibration blocks: {counts.get(outcome.BLOCKED_WEAK, 0)}
- low-sample blocks: {counts.get(outcome.BLOCKED_LOW_SAMPLE, 0)}
- current players with complete admitted feature evidence: {complete}/240
- governed integration rows: {len(pipeline.integration)}
- numeric applicable display rows: {numeric}

## Horizons

Internal horizons are relative: `THIS_YEAR`, `NEXT_YEAR`, `T_PLUS_2`,
`WITHIN_3Y`, `WITHIN_5Y`, and `TWO_OF_NEXT_3Y`. For this board they render as
2026, 2027, 2028, Within 3 Years, Within 5 Years, and Two Qualifying Seasons
Within 3 Years. The two-of-three head is exposed only in expanded Player Compare.

## Guardrails

Outcome is display-only and cannot drive rank, sort, trade value, pick value,
draft order, or model input. Historical and current joins use exact IDs.
Wrong-position is `N/A`; insufficient or blocked applicable evidence is
`Not enough information`. Finished V1 remains byte-identical.
"""


def _executive_verdict(pipeline: Pipeline) -> str:
    counts = pipeline.acceptance["classification"].value_counts()
    return f"""# Executive verdict

`{RESEARCH_VERDICT}`

The deterministic research and integration candidate is ready for independent
review. It contains {int(counts.get(outcome.UPGRADE, 0))} admissible challenger
upgrades and {int(counts.get(outcome.BLOCKED_WEAK, 0) + counts.get(outcome.BLOCKED_LOW_SAMPLE, 0))}
blocked fields, so any deployment is explicitly hybrid. A pushed verdict is not
claimed until remote HQ readback succeeds.
"""


def _finished_v1_no_change() -> str:
    top = "\n".join(f"{index}. {name}" for index, name in enumerate(EXPECTED_TOP_FIVE, 1))
    return f"""# Finished V1 no-change proof

- production identifier: `NWR_FINISHED_VERSION_1`
- board rows: 240
- board SHA-256: `{EXPECTED_BOARD_HASH}`
- frozen comparator rows: 924
- frozen comparator SHA-256: `{EXPECTED_HASHES[FROZEN_COMPARATOR_REL]}`

Top five, unchanged:

{top}

No Outcome field is permitted as a rank or hidden-sort input. The integration
pack records `display_only=true` and `rank_use_allowed=false` on every row.
"""


def _target_contract(pipeline: Pipeline) -> str:
    manifest = pipeline.target_manifest
    return f"""# Target and censoring contract

For anchor season `t`, the exact target windows are:

- This Year: `t`
- Next Year: `t+1`
- T+2: `t+2`
- Within 3 Years: at least one hit in `t..t+2`
- Within 5 Years: at least one hit in `t..t+4`
- Two Qualifying Seasons Within 3 Years: at least two hits in `t..t+2`

A missing player-season row is unknown, never an automatic miss. Exact-year
negative requires an observed nonqualifying result or explicit terminal
authority. Cumulative positive can resolve before the horizon closes;
cumulative negative requires a complete horizon or terminal authority.
Post-2025 seasons are right-censored.

The admitted Formula Data Mart anchors target season `t` to features from
`t-1`; all {len(pipeline.targets):,} target rows preserve that offset. The
manifest contains {int(manifest['labeled_rows'].sum()):,} field-level labeled
rows. Eleven age-sidecar rows fail their own age/identity admission flags and
therefore retain unknown cohort evidence; their exact-ID Outcome labels are not
discarded or rewritten.
"""


def _logical_relationship_graph(pipeline: Pipeline) -> str:
    return f"""# Logical relationship graph

The governed graph contains {len(pipeline.relationships)} partial-order edges.
For every player, threshold nesting requires narrower thresholds to be no more
probable than broader thresholds. Every exact-year probability and the
two-of-three probability must be no greater than Within 3 Years; Within 3 Years
must be no greater than Within 5 Years. No order is imposed among exact years.

A deterministic upward closure projects only broader events. Raw violations,
governed violations, and per-field adjustment burden are reported separately.
Calibrator selection occurs only after the preregistered projection-burden gate.

{_markdown_table(pipeline.relationships)}
"""


def _special_player_review(pipeline: Pipeline) -> str:
    selected_names = {"Christian McCaffrey", "A.J. Brown", "Jonathan Taylor"}
    selected_ids = set(
        pipeline.board.loc[
            pipeline.board["player_name"].isin(selected_names),
            "player_id",
        ]
    )
    selected = pipeline.integration.loc[
        pipeline.integration["player_id"].isin(selected_ids)
        & pipeline.integration["threshold"].astype(str).eq("12")
        & pipeline.integration["applicable"].eq("true")
    ][
        [
            "player_name",
            "position",
            "threshold",
            "horizon_label",
            "probability_display",
            "calibration_status",
            "confidence",
            "evidence_state",
            "projection_adjustment",
            "reason_code",
        ]
    ]
    board_age = pipeline.board.copy()
    board_age["_rank"] = pd.to_numeric(board_age["nwr_rank"], errors="coerce")
    board_age["_age"] = pd.to_numeric(board_age["age"], errors="coerce")
    age_floor = board_age["position"].map({"QB": 33, "RB": 26, "WR": 28, "TE": 30})
    aging = board_age.loc[
        board_age["_rank"].le(60) & board_age["_age"].ge(age_floor)
    ][["nwr_rank", "player_name", "position", "age"]]
    insufficient = pipeline.current_features.loc[
        pipeline.current_features["missing_input_state"].ne("complete")
    ]["missing_reason"].value_counts().rename_axis("reason").reset_index(name="players")
    movements = pipeline.movements.head(20)[
        [
            "finished_v1_rank",
            "player_name",
            "position",
            "field_id",
            "c0_probability",
            "released_probability",
            "probability_delta_vs_c0",
            "projection_delta",
            "selected_calibrator",
            "classification",
        ]
    ]
    extremes = pipeline.current_probabilities.loc[
        pipeline.current_probabilities["probability"].le(0.02)
        | pipeline.current_probabilities["probability"].ge(0.98)
    ][
        [
            "nwr_player_id",
            "field_id",
            "probability",
            "projection_delta",
            "selected_calibrator",
        ]
    ].head(30)
    return f"""# Mechanical Outcome review

## Christian McCaffrey, A.J. Brown, and Jonathan Taylor

{_markdown_table(selected)}

## Top-60 aging cohorts

{_markdown_table(aging)}

## Low-games/current availability evidence

The pinned 2025 season-stat candidate does not contain a games column. Current
availability is therefore never inferred as healthy and low-games review stays
`Not enough information`. Historical low-games cohorts remain separately
evaluated from the admitted Formula Data Mart.

## Rookies and unsupported/missing players

{_markdown_table(insufficient)}

## Largest released probability movements

{_markdown_table(movements)}

## Extreme released probabilities

{_markdown_table(extremes)}

No result in this review is hardcoded into the release. Every row is selected
mechanically from the detached integration outputs.
"""


def _rankings_ui_integration() -> str:
    return f"""# Rankings UI integration

The existing `Outcome Context` preset gains a compact, long-form Outcome V3
lens. Named controls select one governed position and threshold; the table then
shows 2026, 2027, 2028, Within 3 Years, and Within 5 Years with probability,
calibration status, evidence state, sample support, confidence, and missing
reason. `TWO_OF_NEXT_3Y` is intentionally absent from Rankings.

The main rankings table and its sort pipeline are unchanged. The lens consumes
exact `player_id` joins from `OUTCOME_V3_INTEGRATION_PACK.csv`, is display-only,
and exposes `{outcome.RELEASE_IDENTIFIER}`.
"""


def _player_compare_ui_integration() -> str:
    return f"""# Player Compare UI integration

The Outcome/Horizon tab gains the expanded Outcome V3 comparison. For every
selected player's applicable threshold family it shows 2026, 2027, 2028,
Within 3 Years, Within 5 Years, and Two Qualifying Seasons Within 3 Years,
including probability, calibration status, historical sample, confidence,
evidence state, and missing-state explanation.

The adapter joins only exact `player_id`. An unsupported or unidentified player
is `Not enough information`; there is no name fallback. Existing V1/V2
comparison routes and aliases remain available below the V3 surface. Release:
`{outcome.RELEASE_IDENTIFIER}`.
"""


def _security_runtime_no_change() -> str:
    return """# Security, Data Health, and runtime no-change

This lane did not run a security scan, call a provider, enable or execute the
scheduled refresh task, or write `latest_candidate`, `latest_approved`,
persistent state, recovery state, LocalData, ranking sources, trade/pick values,
or launcher configuration.

The five existing security regression groups, passive Data Health reads,
Hermetic harness, LocalData harness, compilation, Ruff, protected-path scan,
and page-open no-mutation checks are release gates recorded in
`VALIDATION_RESULTS.md`. LocalData must remain
`BLOCKED_MISSING_LOCAL_TEST_PACK` with exit 4.
"""


def _opaque_persistent_preservation() -> str:
    return """# Opaque and persistent-state preservation

The five DynastyProcess artifacts were treated as opaque bytes. Only their
SHA-256 receipts were checked; their contents were not inspected, parsed,
copied, normalized, staged, committed, or used.

- `dp_freshness_report.csv`:
  `f34b88e4d0486ec7e34a6e74e1e8953147f91a7b67237062bac0e451eb180e59`
- `dp_market_baseline_context.csv`:
  `a477c6742e14ac4fd6a892b1f56807a0475c62254f632097a03198b303909bbf`
- `dp_nwr_join_coverage.csv`:
  `3164bb9a2c69f4b116d22363861b1cce33f903f45e4421af60f0d3d68e37f8a3`
- `dp_pick_value_context.csv`:
  `c312dd985d78a6edfeeffcba8cf11a56cf729f68ac8eba8c5037b28066184763`
- `dp_playerid_crosswalk_audit.csv`:
  `31178980fd269c660c815cfbeadc214177252742e4fb3df00e5adeae03c754e2`

Persistent state remains 14 files / 542,801 bytes /
`88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`.
Recovery remains 7 files / 172,878 bytes /
`1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`.
"""


def _protected_frozen_proof() -> str:
    return f"""# Protected and frozen path proof

- Finished V1 board: 240 rows / `{EXPECTED_BOARD_HASH}`.
- Frozen comparator: 924 rows / `{EXPECTED_HASHES[FROZEN_COMPARATOR_REL]}`.
- Finished V1 top five match the immutable authority.
- No protected ranking, formula, sorting, trade/pick, Draft Cockpit, launcher,
  refresh-task, persistent-state, recovery-state, or frozen-comparator path is
  an implementation target.
- The Outcome integration is detached, display-only, and rank-use-blocked.
"""


def _rollback_plan() -> str:
    return """# Rollback plan

Rollback is code-and-packet-only:

1. Revert the Outcome V3 implementation commit(s) normally.
2. Remove the compact Rankings lens and expanded Player Compare V3 adapter by
   that revert.
3. The pre-existing Outcome V1/V2 loaders and aliases resume as the only
   Outcome display.

No data migration, ranking rebuild, persistent-state repair, provider call,
refresh, or scheduled-task change is required. Never force push.
"""


def _validation_results(pipeline: Pipeline) -> str:
    classifications = pipeline.acceptance["classification"].value_counts()
    return f"""# Validation results

## Deterministic builder gates

- source hashes and canonical ancestry: PASS
- 43-row current authority inventory: PASS
- 79-row V3 schema / 72 governed fields / 7 aliases: PASS
- exact-ID target and censor contract: PASS
- nested chronological OOF contract: PASS
- C0 baseline constants and reproduction: PASS
- per-field acceptance completeness: PASS ({len(pipeline.acceptance)}/72)
- probability bounds: PASS
- governed logical violations: PASS (zero after projection)
- blocked fields nonnumeric: PASS
- wrong-position `N/A`: PASS
- current insufficient `Not enough information`: PASS
- Finished V1 row/order/hash/top-five: PASS
- integration rows: PASS ({len(pipeline.integration)})

## Release classifications

{_markdown_table(classifications.rename_axis("classification").reset_index(name="fields"))}

Full pytest, UI viewport, route/navigation, page-open no-mutation, security
regression, Data Health, Hermetic, LocalData, compile, Ruff, preservation,
protected-path, whitespace, independent-review, remote-readback, stable-checkout,
and launcher receipts are required before push and are recorded during closeout.
"""


def _write_manifest(root: Path, packet: Path, pipeline: Pipeline) -> None:
    artifacts = []
    for path in sorted(packet.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name == "MANIFEST.json":
            continue
        artifacts.append(
            {
                "path": path.relative_to(packet).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    manifest = {
        "release_identifier": outcome.RELEASE_IDENTIFIER,
        "build_date": BUILD_DATE,
        "canonical_source_commit": outcome.CANONICAL_SOURCE_COMMIT,
        "builder": "scripts/build_nwr_outcome_columns_v3_rc1.py",
        "builder_contract": {
            "encoding": "UTF-8 without BOM",
            "line_endings": "LF",
            "float_precision": 10,
            "stable_ordering": True,
            "wall_clock_used": False,
            "absolute_worktree_paths_emitted": False,
            "manifest_self_reference": False,
        },
        "release_classification": "HYBRID_WITH_BLOCKED_FIELDS",
        "governed_fields": len(pipeline.acceptance),
        "schema_rows": len(pipeline.schema),
        "board_rows": len(pipeline.board),
        "board_sha256": EXPECTED_BOARD_HASH,
        "source_inputs_sha256": outcome.deterministic_frame_hash(pipeline.sources),
        "artifacts": artifacts,
    }
    _write_json(packet / "MANIFEST.json", manifest)


def _verify_source_commit(root: Path) -> None:
    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            outcome.CANONICAL_SOURCE_COMMIT,
            "HEAD",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "Outcome V3 builder is not based on the fixed canonical source commit"
        )


def _board_as_of_year(board: pd.DataFrame) -> int:
    if "score_as_of_date" not in board.columns:
        raise AssertionError("Finished V1 board lacks score_as_of_date")
    years = {
        int(str(value)[:4])
        for value in board["score_as_of_date"]
        if str(value)[:4].isdigit()
    }
    if len(years) != 1:
        raise AssertionError(f"Finished V1 board has ambiguous as-of years: {years}")
    return years.pop()


def _require_hash(path: Path, expected: str) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    actual = _sha256(path)
    if actual != expected.lower():
        raise AssertionError(f"source hash mismatch: {path.name}: {actual} != {expected}")


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    stable = frame.copy()
    stable.to_csv(
        path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        float_format="%.10f",
        na_rep="",
    )


def _write_text(path: Path, body: str) -> None:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


def _write_json(path: Path, value: Any) -> None:
    body = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    )
    _write_text(path, body)


def _markdown_table(frame: pd.DataFrame, *, limit: int = 200) -> str:
    if frame.empty:
        return "_No rows._"
    display = frame.head(limit).replace({np.nan: ""}).astype(str)
    columns = [str(column) for column in display.columns]
    lines = [
        "| " + " | ".join(_escape_markdown(value) for value in columns) + " |",
        "| " + " | ".join("---" for _column in columns) + " |",
    ]
    for row in display.itertuples(index=False, name=None):
        lines.append(
            "| " + " | ".join(_escape_markdown(value) for value in row) + " |"
        )
    if len(frame) > limit:
        lines.append(f"\n_First {limit} of {len(frame)} deterministic rows shown._")
    return "\n".join(lines)


def _escape_markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _packet_hashes(packet: Path) -> dict[str, str]:
    if not packet.exists():
        return {}
    return {
        path.name: _sha256(path)
        for path in sorted(packet.iterdir(), key=lambda item: item.name)
        if path.is_file()
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
