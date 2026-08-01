#!/usr/bin/env python3
"""Run and validate the bounded Phase 3 review-only feature gauntlet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PACKET_RELATIVE = Path("docs/hq/master/nwr_open_role_availability_lifecycle_gauntlet_v1_20260801")
MART_RELATIVE = Path(
    "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/"
    "FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
LIFECYCLE_RELATIVE = Path(
    "docs/hq/data_hygiene/age_lifecycle_sidecar_freeze_validation_v1_20260709/"
    "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
)
SCORING_RELATIVE = Path("config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json")
EXPECTED_HASHES = {
    MART_RELATIVE: "705ce26c9b3649405efe42af135204e98bcad91ae718b43d55b5415fcef6159f",
    LIFECYCLE_RELATIVE: "623de1acd6fc1d885cf4b645be62d4bd4f9032b33de723e6547a3c8070c4573a",
    SCORING_RELATIVE: "59e7a65f61fd95cd83e82ba0fb631e4977faf120d7692f3aa3ebc690000af3a7",
}
REPLACEMENT_RANKS = {"QB": 12, "RB": 30, "WR": 40, "TE": 12}
TARGETS = {
    "WIN_NOW_POINTS_T0": (0, 2025),
    "TWO_YEAR_POINTS_T1": (1, 2024),
    "THREE_YEAR_POINTS_T2": (2, 2023),
}
FAMILIES = {
    "PRODUCTION_PERSISTENCE_2Y": {
        "positions": ("QB", "RB", "WR", "TE"),
        "column": "prior_2yr_weighted_nwr_points",
    },
    "ROLE_OPPORTUNITY_VOLUME": {
        "positions": ("RB", "WR", "TE"),
        "column": "prior_opportunities",
    },
    "ROLE_TRAJECTORY_DELTA": {
        "positions": ("QB", "RB", "WR", "TE"),
        "column": "role_trajectory_delta",
    },
    "RB_HIGH_LEVERAGE_RUSHING": {
        "positions": ("RB",),
        "column": "prior_rushing_first_downs",
    },
    "QB_RUSHING_OPPORTUNITY": {
        "positions": ("QB",),
        "column": "qb_rushing_opportunity",
    },
}
MIN_ANCHOR_SEASON = 2018
BOOTSTRAP_REPS = 2000


def canonical_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def csv_bytes(rows: list[dict[str, Any]], fieldnames: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _number(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")


def load_inputs(repo_root: Path) -> pd.DataFrame:
    for relative, expected in EXPECTED_HASHES.items():
        actual = sha256_bytes(canonical_bytes(repo_root / relative))
        if actual != expected:
            raise AssertionError(f"governed source hash changed: {relative}")

    columns = [
        "player_id",
        "season",
        "feature_season",
        "position",
        "label_next_nwr_points",
        "label_next_position_finish",
        "pyf_prior_nwr_points",
        "pyf_prior_rank_position_feature_season",
        "prior_2yr_weighted_nwr_points",
        "prior_games",
        "prior_opportunities",
        "prior_rushing_yards",
        "prior_rushing_first_downs",
        "low_games_flag",
        "leakage_check_result",
        "asof_check_result",
        "formula_test_allowed_scope",
    ]
    mart = pd.read_csv(repo_root / MART_RELATIVE, usecols=columns, dtype=str)
    numeric = [column for column in columns if column.startswith(("label_", "pyf_", "prior_"))]
    _number(mart, numeric + ["season", "feature_season"])
    if len(mart) != 5518 or mart[["player_id", "season", "position"]].duplicated().any():
        raise AssertionError("Formula Data Mart row count or exact key changed")
    if set(mart["position"]) != set(REPLACEMENT_RANKS):
        raise AssertionError("unexpected position universe")
    if not mart["leakage_check_result"].eq("PASS_FEATURE_N_TARGET_N_PLUS_1_SEPARATED").all():
        raise AssertionError("mart leakage gate failed")
    if not mart["asof_check_result"].eq("PASS_NO_TARGET_SEASON_CONTEXT_IN_FEATURE_COLUMNS").all():
        raise AssertionError("mart as-of gate failed")
    if not mart["formula_test_allowed_scope"].eq("review_only_component_signal_tests_only").all():
        raise AssertionError("mart scope gate failed")

    lifecycle_columns = [
        "player_id",
        "season",
        "position",
        "age_bucket",
        "lifecycle_bucket",
        "decision_date_safe",
        "leakage_flag",
        "identity_flag",
        "missingness_flag",
    ]
    lifecycle = pd.read_csv(repo_root / LIFECYCLE_RELATIVE, usecols=lifecycle_columns, dtype=str)
    lifecycle["season"] = pd.to_numeric(lifecycle["season"], errors="raise")
    if len(lifecycle) != 5518 or lifecycle[["player_id", "season", "position"]].duplicated().any():
        raise AssertionError("lifecycle row count or exact key changed")
    allowed_decision_states = {
        "PASS_STABLE_IDENTITY_METADATA_ASOF_DERIVED_FOR_TARGET_SEASON_START",
        "PARTIAL_MISSING_DOB_NOT_DECISION_DATE_SIGNAL",
    }
    if not set(lifecycle["decision_date_safe"]).issubset(allowed_decision_states):
        raise AssertionError("unexpected lifecycle decision-date state")
    lifecycle_admitted = (
        lifecycle["decision_date_safe"].eq(
            "PASS_STABLE_IDENTITY_METADATA_ASOF_DERIVED_FOR_TARGET_SEASON_START"
        )
        & lifecycle["leakage_flag"].eq(
            "PASS_STABLE_DOB_AND_DRAFT_YEAR_DERIVED_ASOF_SEPT_01_NO_OUTCOME_FIELDS"
        )
        & lifecycle["identity_flag"].eq("PASS_GSIS_ID_JOIN")
    )
    lifecycle.loc[~lifecycle_admitted, ["age_bucket", "lifecycle_bucket"]] = pd.NA
    frame = mart.merge(
        lifecycle,
        on=["player_id", "season", "position"],
        how="left",
        validate="one_to_one",
    )
    frame["role_trajectory_delta"] = (
        frame["pyf_prior_nwr_points"] - frame["prior_2yr_weighted_nwr_points"]
    )
    frame["qb_rushing_opportunity"] = (
        0.1 * frame["prior_rushing_yards"] + 0.4 * frame["prior_rushing_first_downs"]
    )
    frame["low_games"] = frame["low_games_flag"].str.lower().eq("true")
    frame["productive_veteran"] = frame["lifecycle_bucket"].isin(
        ["veteran_7_to_9", "late_career_10_plus"]
    ) & (
        frame["pyf_prior_rank_position_feature_season"] <= frame["position"].map(REPLACEMENT_RANKS)
    )
    return frame


def _spearman(left: pd.Series, right: pd.Series) -> float:
    if len(left) < 3 or left.nunique() < 2 or right.nunique() < 2:
        return float("nan")
    return float(left.rank(method="average").corr(right.rank(method="average")))


def _bootstrap(deltas: list[float], seed_text: str) -> tuple[float, float]:
    if len(deltas) < 5:
        return float("nan"), 1.0
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:16], 16)
    rng = np.random.default_rng(seed)
    values = np.asarray(deltas, dtype=float)
    samples = rng.choice(values, size=(BOOTSTRAP_REPS, len(values)), replace=True).mean(axis=1)
    lower = float(np.quantile(samples, 0.025))
    p_value = float((1 + np.count_nonzero(samples <= 0)) / (BOOTSTRAP_REPS + 1))
    return lower, p_value


def _target_frame(frame: pd.DataFrame, horizon: int, max_anchor: int) -> pd.DataFrame:
    outcome = frame[
        ["player_id", "season", "label_next_nwr_points", "label_next_position_finish"]
    ].rename(
        columns={
            "season": "outcome_season",
            "label_next_nwr_points": "target_points",
            "label_next_position_finish": "target_finish",
        }
    )
    anchored = frame.copy()
    anchored["outcome_season"] = anchored["season"] + horizon
    merged = anchored.merge(outcome, on=["player_id", "outcome_season"], how="left")
    return merged[(merged["season"] >= MIN_ANCHOR_SEASON) & (merged["season"] <= max_anchor)]


def _guardrail_demotion(frame: pd.DataFrame, signal: str, mask: pd.Series) -> tuple[int, float]:
    rows = frame.loc[mask & frame[signal].notna() & frame["pyf_prior_nwr_points"].notna()].copy()
    if rows.empty:
        return 0, float("nan")
    groups = ["position", "season"]
    rows["baseline_pct"] = rows.groupby(groups)["pyf_prior_nwr_points"].rank(
        ascending=False, method="average", pct=True
    )
    rows["candidate_pct"] = rows.groupby(groups)[signal].rank(
        ascending=False, method="average", pct=True
    )
    positive_demotion = (rows["candidate_pct"] - rows["baseline_pct"]).clip(lower=0)
    return len(rows), float(positive_demotion.mean())


def evaluate(
    repo_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    frame = load_inputs(repo_root)
    detail: list[dict[str, Any]] = []
    guardrails: list[dict[str, Any]] = []
    family_p: dict[str, float] = {}
    family_prepass: dict[str, bool] = {}

    for family_id, spec in FAMILIES.items():
        signal = str(spec["column"])
        family_cells: list[dict[str, Any]] = []
        family_frame = frame[frame["position"].isin(spec["positions"])].copy()
        veteran_rows, veteran_demotion = _guardrail_demotion(
            family_frame, signal, family_frame["productive_veteran"]
        )
        low_rows, low_demotion = _guardrail_demotion(
            family_frame, signal, family_frame["low_games"]
        )
        for guardrail_id, rows, demotion in (
            ("PRODUCTIVE_VETERAN", veteran_rows, veteran_demotion),
            ("LOW_GAMES", low_rows, low_demotion),
        ):
            guardrails.append(
                {
                    "family_id": family_id,
                    "guardrail_id": guardrail_id,
                    "rows": rows,
                    "mean_positive_percentile_demotion": ""
                    if np.isnan(demotion)
                    else f"{demotion:.6f}",
                    "threshold": "<=0.100000",
                    "status": "PASS" if rows >= 20 and demotion <= 0.10 else "FAIL",
                }
            )

        for target_id, (horizon, max_anchor) in TARGETS.items():
            target_frame = _target_frame(family_frame, horizon, max_anchor)
            for position in spec["positions"]:
                position_frame = target_frame[target_frame["position"].eq(position)].copy()
                universe = position_frame.dropna(
                    subset=["target_points", "target_finish", "pyf_prior_nwr_points"]
                )
                compared = universe.dropna(subset=[signal]).copy()
                coverage = len(compared) / len(universe) if len(universe) else 0.0
                fold_rows: list[dict[str, float]] = []
                replacement_rank = REPLACEMENT_RANKS[position]
                for season, season_rows in compared.groupby("season", sort=True):
                    baseline_corr = _spearman(
                        season_rows["pyf_prior_nwr_points"], season_rows["target_points"]
                    )
                    candidate_corr = _spearman(season_rows[signal], season_rows["target_points"])
                    baseline_rank = season_rows["pyf_prior_nwr_points"].rank(
                        ascending=False, method="min"
                    )
                    candidate_rank = season_rows[signal].rank(ascending=False, method="min")
                    actual_hit = season_rows["target_finish"] <= replacement_rank
                    baseline_selected = baseline_rank <= replacement_rank
                    candidate_selected = candidate_rank <= replacement_rank
                    baseline_precision = (
                        float(actual_hit[baseline_selected].mean())
                        if baseline_selected.any()
                        else 0.0
                    )
                    candidate_precision = (
                        float(actual_hit[candidate_selected].mean())
                        if candidate_selected.any()
                        else 0.0
                    )
                    if not np.isnan(baseline_corr) and not np.isnan(candidate_corr):
                        fold_rows.append(
                            {
                                "season": float(season),
                                "delta": candidate_corr - baseline_corr,
                                "precision_delta": candidate_precision - baseline_precision,
                            }
                        )
                deltas = [row["delta"] for row in fold_rows]
                precision_deltas = [row["precision_delta"] for row in fold_rows]
                lower, p_value = _bootstrap(deltas, f"{family_id}|{target_id}|{position}")
                positives = int((compared["target_finish"] <= replacement_rank).sum())
                negatives = len(compared) - positives
                support = (
                    len(compared) >= 100
                    and positives >= 20
                    and negatives >= 20
                    and len(fold_rows) >= 5
                )
                median_delta = float(np.median(deltas)) if deltas else float("nan")
                win_rate = float(np.mean(np.asarray(deltas) > 0)) if deltas else 0.0
                worst_delta = min(deltas) if deltas else float("nan")
                precision_delta = (
                    float(np.mean(precision_deltas)) if precision_deltas else float("nan")
                )
                cell_pass = (
                    support
                    and coverage >= 0.80
                    and median_delta >= 0.01
                    and lower > 0
                    and win_rate >= 0.60
                    and worst_delta >= -0.10
                    and precision_delta >= 0
                )
                result = {
                    "family_id": family_id,
                    "target_component": target_id,
                    "position": position,
                    "rows": len(compared),
                    "eligible_rows": len(universe),
                    "coverage": f"{coverage:.6f}",
                    "positives": positives,
                    "negatives": negatives,
                    "test_seasons": len(fold_rows),
                    "median_fold_spearman_delta": ""
                    if np.isnan(median_delta)
                    else f"{median_delta:.6f}",
                    "bootstrap_95_lower_mean_delta": "" if np.isnan(lower) else f"{lower:.6f}",
                    "bootstrap_one_sided_p": f"{p_value:.6f}",
                    "season_win_rate": f"{win_rate:.6f}",
                    "worst_fold_delta": "" if np.isnan(worst_delta) else f"{worst_delta:.6f}",
                    "replacement_precision_delta": ""
                    if np.isnan(precision_delta)
                    else f"{precision_delta:.6f}",
                    "status": "PASS"
                    if cell_pass
                    else ("INSUFFICIENT_SUPPORT" if not support else "FAIL"),
                }
                detail.append(result)
                family_cells.append(result)
        guardrail_pass = all(
            row["status"] == "PASS" for row in guardrails if row["family_id"] == family_id
        )
        family_prepass[family_id] = guardrail_pass and all(
            row["status"] == "PASS" for row in family_cells
        )
        family_p[family_id] = max(float(row["bootstrap_one_sided_p"]) for row in family_cells)

    ordered = sorted(family_p, key=family_p.get)
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, family_id in enumerate(ordered):
        running = max(running, (total - index) * family_p[family_id])
        adjusted[family_id] = min(1.0, running)

    decisions: list[dict[str, Any]] = []
    for family_id in FAMILIES:
        final_pass = family_prepass[family_id] and adjusted[family_id] <= 0.05
        failed_cells = sum(
            row["status"] != "PASS" for row in detail if row["family_id"] == family_id
        )
        decisions.append(
            {
                "family_id": family_id,
                "applicable_cells": sum(row["family_id"] == family_id for row in detail),
                "failed_cells": failed_cells,
                "family_bootstrap_p": f"{family_p[family_id]:.6f}",
                "holm_adjusted_p": f"{adjusted[family_id]:.6f}",
                "all_cell_and_guardrail_gates": "PASS" if family_prepass[family_id] else "FAIL",
                "decision": "PASS_REVIEW_ONLY" if final_pass else "NULL_NOT_PROMOTED",
            }
        )
    passing = [row["family_id"] for row in decisions if row["decision"] == "PASS_REVIEW_ONLY"]
    summary = {
        "bootstrap_repetitions": BOOTSTRAP_REPS,
        "families_passed": passing,
        "families_tested": len(FAMILIES),
        "formula_data_mart_rows": len(frame),
        "overall_verdict": "PASSING_REVIEW_ONLY_FAMILIES" if passing else "NULL_NO_FAMILY_PASSED",
        "production_changes": 0,
        "provider_calls": 0,
        "schema_version": "NWR_PHASE_3_GAUNTLET_SUMMARY_V1",
        "target_components_tested": len(TARGETS),
    }
    return detail, guardrails, decisions, summary


DETAIL_FIELDS = [
    "family_id",
    "target_component",
    "position",
    "rows",
    "eligible_rows",
    "coverage",
    "positives",
    "negatives",
    "test_seasons",
    "median_fold_spearman_delta",
    "bootstrap_95_lower_mean_delta",
    "bootstrap_one_sided_p",
    "season_win_rate",
    "worst_fold_delta",
    "replacement_precision_delta",
    "status",
]
GUARDRAIL_FIELDS = [
    "family_id",
    "guardrail_id",
    "rows",
    "mean_positive_percentile_demotion",
    "threshold",
    "status",
]
DECISION_FIELDS = [
    "family_id",
    "applicable_cells",
    "failed_cells",
    "family_bootstrap_p",
    "holm_adjusted_p",
    "all_cell_and_guardrail_gates",
    "decision",
]


def generated_outputs(repo_root: Path) -> dict[str, bytes]:
    detail, guardrails, decisions, summary = evaluate(repo_root)
    return {
        "GAUNTLET_RESULTS.csv": csv_bytes(detail, DETAIL_FIELDS),
        "GUARDRAIL_RESULTS.csv": csv_bytes(guardrails, GUARDRAIL_FIELDS),
        "FAMILY_DECISIONS.csv": csv_bytes(decisions, DECISION_FIELDS),
        "GAUNTLET_SUMMARY.json": json_bytes(summary),
    }


def write_manifest(packet: Path) -> None:
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(packet.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "MANIFEST.json":
            body = canonical_bytes(path)
            files[path.name] = {"bytes": len(body), "sha256": sha256_bytes(body)}
    manifest = {
        "files": files,
        "hash_representation": "UTF8_LF_CANONICAL_BYTES",
        "manifest_excludes_self": True,
        "packet": PACKET_RELATIVE.as_posix(),
        "required_file_count": len(files) + 1,
        "schema_version": "NWR_PHASE_3_GAUNTLET_MANIFEST_V1",
    }
    (packet / "MANIFEST.json").write_bytes(json_bytes(manifest))


def write_generated(repo_root: Path) -> dict[str, Any]:
    packet = repo_root / PACKET_RELATIVE
    outputs = generated_outputs(repo_root)
    for name, body in outputs.items():
        (packet / name).write_bytes(body)
    write_manifest(packet)
    return json.loads(outputs["GAUNTLET_SUMMARY.json"])


def validate(repo_root: Path) -> dict[str, Any]:
    packet = repo_root / PACKET_RELATIVE
    outputs = generated_outputs(repo_root)
    for name, expected in outputs.items():
        if canonical_bytes(packet / name) != expected:
            raise AssertionError(f"generated Phase 3 evidence changed: {name}")
    manifest = json.loads((packet / "MANIFEST.json").read_text(encoding="utf-8"))
    if manifest["required_file_count"] != len(manifest["files"]) + 1:
        raise AssertionError("manifest count mismatch")
    for name, receipt in manifest["files"].items():
        body = canonical_bytes(packet / name)
        if receipt != {"bytes": len(body), "sha256": sha256_bytes(body)}:
            raise AssertionError(f"manifest mismatch: {name}")
    summary = json.loads(outputs["GAUNTLET_SUMMARY.json"])
    summary["valid"] = True
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-generated", action="store_true")
    args = parser.parse_args()
    result = write_generated(args.repo_root) if args.write_generated else validate(args.repo_root)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
