from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.model_v4_player_identity_crosswalk_service import (  # noqa: E402
    normalize_identity_name,
)

NFLVERSE_PYDEPS = Path(r"C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps")
if str(NFLVERSE_PYDEPS) not in sys.path:
    sys.path.insert(0, str(NFLVERSE_PYDEPS))

DOC_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_source_expansion_coverage_runner_v1_20260630"
)
SHARED_DRAFT_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\draft_capital_repair_v1")
SHARED_COMBINE_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\combine_measurements_v1")
SHARED_DISPLAY_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\display_artifact_v2")

GATE_A_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "cfbd_rookie_identity_approval_v1_20260629"
    / "cfbd_rookie_identity_human_approval_v1.csv"
)
GATE_B_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_capital_review_v1_20260629"
    / "rookie_draft_capital_review_artifact_v1.csv"
)
GATE_D_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_d_feature_policy_v1_20260630"
    / "rookie_feature_policy_matrix_v1.csv"
)
GATE_E_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_e_model_rd_v1_20260630"
    / "rookie_model_rd_validation_summary_v1.csv"
)
GATE_E_METRICS_PATH = (
    Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\model_rd_v1")
    / "rookie_model_rd_validation_metrics_v1.csv"
)
GATE_F_COVERAGE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_f_display_artifact_v1_20260630"
    / "rookie_display_artifact_coverage_matrix_v1.csv"
)
HISTORICAL_LABEL_PATH = (
    Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\historical_labels_v1")
    / "rookie_historical_outcome_labels_v1.csv"
)
SOURCE_REGISTRY_PATH = REPO_ROOT / "config" / "source_registry.csv"

BASE_HEAD = "8744fa0351c5aa64591ec2398c3c7fed1684ef2b"
NOT_ENOUGH = "Not enough information"
RUN_ID = "rookie_source_expansion_coverage_runner_v1_20260630"

TARGETS = tuple(
    f"{horizon}_top_{threshold}_hit"
    for horizon in ("rookie_year", "year_2", "first_3y", "first_5y")
    for threshold in (12, 24, 36)
)
POSITION_SUPPORTED_THRESHOLDS = {
    "QB": {12},
    "RB": {12, 24, 36},
    "WR": {12, 24, 36},
    "TE": {12},
}

SOURCE_POLICY_COLUMNS = (
    "source_name",
    "source_url_or_identifier",
    "source_type",
    "candidate_fields",
    "license_status",
    "provenance_status",
    "automation_allowed",
    "factual_fields_allowed",
    "analyst_grade_fields_allowed",
    "allowed_for_review_only_model_rd",
    "allowed_for_display_context",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "source_policy_verdict",
    "blocker_reason",
    "required_next_gate",
    "notes",
)

DRAFT_REPAIR_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "draft_year",
    "draft_round",
    "draft_pick",
    "overall_pick",
    "drafted_team",
    "draft_capital_bucket",
    "draft_capital_value",
    "draft_capital_value_method",
    "draft_capital_source",
    "draft_capital_provenance",
    "draft_capital_status",
    "is_udfa",
    "udfa_status_source",
    "data_quality_status",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

COMBINE_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "rookie_class_year",
    "height",
    "weight",
    "bmi",
    "forty_time",
    "speed_score",
    "vertical",
    "broad",
    "three_cone",
    "shuttle",
    "bench",
    "arm_length",
    "hand_size",
    "measurement_source",
    "combine_vs_pro_day_flag",
    "measurement_status",
    "data_quality_status",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

FEATURE_POLICY_COLUMNS = (
    "feature_family",
    "feature_name",
    "source",
    "availability_status",
    "approval_status",
    "allowed_for_review_only_model_rd",
    "allowed_for_display_context",
    "model_use_allowed",
    "training_allowed",
    "review_only",
    "leakage_risk",
    "missingness_risk",
    "blocker_reason",
    "required_next_gate",
    "notes",
)

DISPLAY_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "identity_status",
    "draft_capital_status",
    "feature_coverage_status",
    "model_rd_status",
    "validation_status",
    "display_status",
    "data_quality_status",
    "source_provenance_status",
    "rookie_year_top_12_review_display_rate",
    "rookie_year_top_24_review_display_rate",
    "rookie_year_top_36_review_display_rate",
    "year_2_top_12_review_display_rate",
    "year_2_top_24_review_display_rate",
    "year_2_top_36_review_display_rate",
    "first_3y_top_12_review_display_rate",
    "first_3y_top_24_review_display_rate",
    "first_3y_top_36_review_display_rate",
    "first_5y_top_12_review_display_rate",
    "first_5y_top_24_review_display_rate",
    "first_5y_top_36_review_display_rate",
    "display_field_count",
    "not_enough_information_field_count",
    "rate_method_summary",
    "review_only",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "rankings_wiring_allowed",
    "notes",
)

SUMMARY_COLUMNS = (
    "metric",
    "value",
    "notes",
    "review_only",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "rankings_wiring_allowed",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-root", type=Path, default=DOC_ROOT)
    args = parser.parse_args(argv)

    args.doc_root.mkdir(parents=True, exist_ok=True)
    SHARED_DRAFT_ROOT.mkdir(parents=True, exist_ok=True)
    SHARED_COMBINE_ROOT.mkdir(parents=True, exist_ok=True)
    SHARED_DISPLAY_ROOT.mkdir(parents=True, exist_ok=True)

    gate_a_rows = read_csv(GATE_A_PATH)
    gate_b_rows = read_csv(GATE_B_PATH)
    gate_d_rows = read_csv(GATE_D_PATH)
    gate_e_summary = read_csv(GATE_E_SUMMARY_PATH)
    gate_e_metrics = read_csv(GATE_E_METRICS_PATH)
    gate_f_rows = read_csv(GATE_F_COVERAGE_PATH)
    historical_labels = read_csv(HISTORICAL_LABEL_PATH)
    registry_rows = read_csv(SOURCE_REGISTRY_PATH)

    draft_picks = load_nflverse_draft_picks()
    combine_rows = load_nflverse_combine()

    source_policy_rows = build_source_policy_rows(registry_rows)
    draft_repair_rows = build_draft_repair_rows(gate_b_rows, draft_picks)
    combine_matrix_rows = build_combine_rows(gate_b_rows, combine_rows)
    feature_policy_rows = build_feature_policy_rows()
    display_rows = build_display_rows(
        draft_repair_rows,
        historical_labels,
        gate_e_summary,
        gate_e_metrics,
    )
    display_summary_rows = build_display_summary_rows(display_rows)

    write_csv(
        args.doc_root / "rookie_source_intake_policy_matrix_v1.csv",
        SOURCE_POLICY_COLUMNS,
        source_policy_rows,
    )
    write_csv(
        args.doc_root / "rookie_draft_capital_repair_coverage_matrix_v1.csv",
        DRAFT_REPAIR_COLUMNS,
        draft_repair_rows,
    )
    write_csv(
        args.doc_root / "rookie_combine_measurements_coverage_matrix_v1.csv",
        COMBINE_COLUMNS,
        combine_matrix_rows,
    )
    write_csv(
        args.doc_root / "rookie_feature_policy_refresh_matrix_v1.csv",
        FEATURE_POLICY_COLUMNS,
        feature_policy_rows,
    )
    write_csv(
        args.doc_root / "rookie_display_artifact_v2_coverage_matrix.csv",
        DISPLAY_COLUMNS,
        display_rows,
    )

    write_csv(
        SHARED_DRAFT_ROOT / "rookie_draft_capital_repair_v1.csv",
        DRAFT_REPAIR_COLUMNS,
        draft_repair_rows,
    )
    write_csv(
        SHARED_DRAFT_ROOT / "rookie_draft_capital_repair_manifest_v1.csv",
        SUMMARY_COLUMNS,
        shared_manifest_rows("draft_capital_repair_v1", len(draft_repair_rows)),
    )
    write_csv(
        SHARED_COMBINE_ROOT / "rookie_combine_measurements_v1.csv",
        COMBINE_COLUMNS,
        combine_matrix_rows,
    )
    write_csv(
        SHARED_COMBINE_ROOT / "rookie_combine_measurements_manifest_v1.csv",
        SUMMARY_COLUMNS,
        shared_manifest_rows("combine_measurements_v1", len(combine_matrix_rows)),
    )
    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_artifact_v2.csv",
        DISPLAY_COLUMNS,
        display_rows,
    )
    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_coverage_summary_v2.csv",
        SUMMARY_COLUMNS,
        display_summary_rows,
    )
    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_manifest_v2.csv",
        SUMMARY_COLUMNS,
        shared_manifest_rows("display_artifact_v2", len(display_rows)),
    )

    write_docs(
        args.doc_root,
        gate_a_rows,
        gate_b_rows,
        gate_d_rows,
        gate_e_metrics,
        gate_f_rows,
        draft_picks,
        combine_rows,
        draft_repair_rows,
        combine_matrix_rows,
        feature_policy_rows,
        display_rows,
    )

    print(
        {
            "final_verdict": "PARTIAL_SOURCE_EXPANSION_COVERAGE_REPAIR",
            "draft_repair_rows": len(draft_repair_rows),
            "draft_capital_repaired_rows": count_available_draft_rows(draft_repair_rows),
            "combine_measurement_rows": count_available_measurement_rows(combine_matrix_rows),
            "display_v2_rows": len(display_rows),
            "display_v2_valid_rows": count_display_rows(display_rows),
            "gate_g": "BLOCKED_NEEDS_DISPLAY_COVERAGE",
        }
    )


def build_source_policy_rows(registry_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    registry_keys = {(row["source_name"], row["source_table"]) for row in registry_rows}
    nflverse_allowed = ("nflverse", "draft_picks") in registry_keys and (
        "nflverse",
        "combine",
    ) in registry_keys
    rows = [
        source_policy_row(
            "nflverse / nflreadpy",
            "config/source_registry.csv + nflreadpy load_draft_picks/load_combine",
            "public structured factual source",
            "draft picks; draft values if separately available; player IDs; combine",
            "admitted_in_local_source_registry",
            "nflverse draft_picks/combine rows available through existing safe runtime",
            "true",
            "true",
            "false",
            "true" if nflverse_allowed else "false",
            "true",
            "PARTIAL_SOURCE_INTAKE_POLICY",
            NOT_ENOUGH if nflverse_allowed else "Missing nflverse registry entries.",
            "Gate 2 draft capital repair and Gate 3 measurements intake.",
            "Use factual completed draft/measurement fields only; no market/rank/projection.",
        ),
        source_policy_row(
            "JackLich10/nfl-draft-data",
            "https://github.com/JackLich10/nfl-draft-data",
            "GitHub draft/prospect dataset",
            "draft context; school; height/weight; ESPN ranks/grades/profile text",
            "github_license_api_404_no_license_file_found",
            "README describes ESPN grades/ranks/profile text and draft prospect fields",
            "false",
            "false",
            "false",
            "false",
            "false",
            "BLOCKED_NEEDS_LICENSE_REVIEW",
            "No clear repository license; ESPN rank/grade/text provenance is analyst-mediated.",
            "License/provenance review before any intake.",
            "Reference only. Do not ingest in this runner.",
        ),
        source_policy_row(
            "array-carpenter/nfl-draft-data",
            "https://github.com/array-carpenter/nfl-draft-data",
            "GitHub combine/pro-day dataset",
            "combine/pro-day measurements; official combine; NFL.com/NGS grades",
            "github_license_api_404_no_license_file_found",
            "README/docs describe manually charted measurements plus grade/projection fields",
            "false",
            "false",
            "false",
            "false",
            "false",
            "BLOCKED_NEEDS_LICENSE_REVIEW",
            "No clear repository license; official grades/projections must remain separated.",
            "License/provenance review before any intake.",
            "Use nflverse combine instead for this runner.",
        ),
        source_policy_row(
            "ESPN / NFL prospect grades",
            "ESPN/NFL.com grade/rank/projection fields",
            "analyst-mediated prospect context",
            "ESPN grade; ESPN ranks; NFL.com grade; NGS grade; projection",
            "blocked_without_explicit_license",
            "analyst-mediated and potentially overlapping with draft capital",
            "false",
            "false",
            "false",
            "false",
            "false",
            "BLOCKED_GRADES_LICENSE_OR_PROVENANCE",
            "Grade/rank/projection fields are not factual measurements.",
            "Separate grade-only source policy and validation lane.",
            "No grade fields used.",
        ),
        source_policy_row(
            "FootballDB",
            "https://www.footballdb.com/",
            "website",
            "manual spot-check only",
            "blocked_for_automation",
            "scraping not allowed in this runner",
            "false",
            "false",
            "false",
            "false",
            "false",
            "RED_HOLD_FOR_AUTOMATED_COLLECTION",
            "FootballDB is blocked for automated scraping.",
            "None; manual spot-check only if user explicitly directs.",
            "No collector, scraper, or ingestion.",
        ),
    ]
    return rows


def source_policy_row(
    source_name: str,
    source_url_or_identifier: str,
    source_type: str,
    candidate_fields: str,
    license_status: str,
    provenance_status: str,
    automation_allowed: str,
    factual_fields_allowed: str,
    analyst_grade_fields_allowed: str,
    allowed_for_review_only_model_rd: str,
    allowed_for_display_context: str,
    source_policy_verdict: str,
    blocker_reason: str,
    required_next_gate: str,
    notes: str,
) -> dict[str, str]:
    return {
        "source_name": source_name,
        "source_url_or_identifier": source_url_or_identifier,
        "source_type": source_type,
        "candidate_fields": candidate_fields,
        "license_status": license_status,
        "provenance_status": provenance_status,
        "automation_allowed": automation_allowed,
        "factual_fields_allowed": factual_fields_allowed,
        "analyst_grade_fields_allowed": analyst_grade_fields_allowed,
        "allowed_for_review_only_model_rd": allowed_for_review_only_model_rd,
        "allowed_for_display_context": allowed_for_display_context,
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "source_policy_verdict": source_policy_verdict,
        "blocker_reason": blocker_reason,
        "required_next_gate": required_next_gate,
        "notes": notes,
    }


def build_draft_repair_rows(
    gate_b_rows: list[dict[str, str]],
    draft_picks: list[dict[str, str]],
) -> list[dict[str, str]]:
    draft_index = {
        (normalize_identity_name(row["pfr_player_name"]), row["position"].upper()): row
        for row in draft_picks
        if row["position"].upper() in {"QB", "RB", "WR", "TE"}
    }
    output = []
    for row in gate_b_rows:
        key = (normalize_identity_name(row["player_name"]), row["position"].upper())
        match = draft_index.get(key)
        if match:
            pick = clean(match["pick"])
            draft_round = clean(match["round"])
            team = normalize_team(clean(match["team"]))
            bucket = draft_capital_bucket({"draft_round": draft_round, "draft_pick": pick})
            status = "REPAIRED_NFLVERSE_DRAFT_CAPITAL_AVAILABLE"
            quality = "PARTIAL_DRAFT_CAPITAL_COVERAGE_REPAIR_AVAILABLE"
            provenance = (
                "nflreadpy.load_draft_picks([2026]) exact normalized-name + position match; "
                "review-only, not source truth."
            )
        else:
            pick = draft_round = team = bucket = NOT_ENOUGH
            status = "MISSING_DRAFT_CAPITAL_REVIEW_REQUIRED"
            quality = "MISSING_AFTER_NFLVERSE_DRAFT_REPAIR"
            provenance = (
                "No exact normalized-name + position match in admitted nflverse draft_picks."
            )
        output.append(
            {
                "player_id": clean(row["player_id"]),
                "player_name": clean(row["player_name"]),
                "position": clean(row["position"]),
                "team": team,
                "rookie_class_year": "2026" if match else NOT_ENOUGH,
                "draft_year": "2026" if match else NOT_ENOUGH,
                "draft_round": draft_round,
                "draft_pick": pick,
                "overall_pick": pick,
                "drafted_team": team,
                "draft_capital_bucket": bucket,
                "draft_capital_value": NOT_ENOUGH,
                "draft_capital_value_method": "blocked_no_approved_draft_value_table",
                "draft_capital_source": "nflverse_draft_picks_2026" if match else NOT_ENOUGH,
                "draft_capital_provenance": provenance,
                "draft_capital_status": status,
                "is_udfa": NOT_ENOUGH if not match else "false",
                "udfa_status_source": (
                    "nflverse_draft_picks_match" if match else "not_enough_information"
                ),
                "data_quality_status": quality,
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def build_combine_rows(
    gate_b_rows: list[dict[str, str]],
    combine_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    combine_index = {
        (normalize_identity_name(row["player_name"]), row["pos"].upper()): row
        for row in combine_rows
        if row["pos"].upper() in {"QB", "RB", "WR", "TE"}
    }
    output = []
    for row in gate_b_rows:
        key = (normalize_identity_name(row["player_name"]), row["position"].upper())
        match = combine_index.get(key)
        height = height_to_inches(clean(match.get("ht"))) if match else NOT_ENOUGH
        weight = clean_numeric(match.get("wt")) if match else NOT_ENOUGH
        forty = clean_numeric(match.get("forty")) if match else NOT_ENOUGH
        bmi = calc_bmi(height, weight)
        speed = calc_speed_score(weight, forty)
        has_measurement = match is not None and any(
            value != NOT_ENOUGH
            for value in (
                height,
                weight,
                forty,
                clean_numeric(match.get("bench")),
                clean_numeric(match.get("vertical")),
                clean_numeric(match.get("broad_jump")),
                clean_numeric(match.get("cone")),
                clean_numeric(match.get("shuttle")),
            )
        )
        output.append(
            {
                "player_id": clean(row["player_id"]),
                "player_name": clean(row["player_name"]),
                "position": clean(row["position"]),
                "rookie_class_year": "2026",
                "height": height,
                "weight": weight,
                "bmi": bmi,
                "forty_time": forty,
                "speed_score": speed,
                "vertical": clean_numeric(match.get("vertical")) if match else NOT_ENOUGH,
                "broad": clean_numeric(match.get("broad_jump")) if match else NOT_ENOUGH,
                "three_cone": clean_numeric(match.get("cone")) if match else NOT_ENOUGH,
                "shuttle": clean_numeric(match.get("shuttle")) if match else NOT_ENOUGH,
                "bench": clean_numeric(match.get("bench")) if match else NOT_ENOUGH,
                "arm_length": NOT_ENOUGH,
                "hand_size": NOT_ENOUGH,
                "measurement_source": "nflverse_combine_2026" if match else NOT_ENOUGH,
                "combine_vs_pro_day_flag": "nflverse_combine" if match else NOT_ENOUGH,
                "measurement_status": (
                    "PARTIAL_COMBINE_MEASUREMENT_AVAILABLE"
                    if has_measurement
                    else "MISSING_COMBINE_MEASUREMENT"
                ),
                "data_quality_status": (
                    "PARTIAL_COMBINE_MEASUREMENTS_REVIEW_ONLY"
                    if has_measurement
                    else "MISSING_MEASUREMENTS_REVIEW_REQUIRED"
                ),
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def build_feature_policy_rows() -> list[dict[str, str]]:
    rows = []
    for feature in (
        "draft_round",
        "draft_pick",
        "overall_pick",
        "draft_capital_bucket",
        "draft_year",
        "rookie_class_year",
        "position",
    ):
        rows.append(
            feature_row(
                "draft_capital",
                feature,
                "nflverse draft_picks / repaired review artifact",
                "available_partial",
                "allowed_review_only_model_rd",
                "true",
                "true",
                "low",
                "partial_current_rookie_coverage",
                NOT_ENOUGH,
                "Gate E refresh or Gate F rebuild.",
                "Factual completed draft/position field; review-only.",
            )
        )
    rows.extend(
        [
            feature_row(
                "draft_capital",
                "draft_capital_value",
                "Not enough information",
                "missing",
                "blocked",
                "false",
                "false",
                "low",
                "missing",
                "No approved draft-value table in this runner.",
                "Draft value source policy lane.",
                "Do not derive opaque values.",
            ),
            feature_row(
                "draft_context",
                "drafted_team",
                "nflverse draft_picks",
                "available_partial",
                "review_only_context",
                "false",
                "true",
                "medium",
                "partial_current_rookie_coverage",
                "Landing spot can leak if used as value input before separate approval.",
                "Separate landing-spot feature gate.",
                "Display context only.",
            ),
            feature_row(
                "draft_context",
                "udfa_status",
                "nflverse draft_picks absence",
                "not_enough_information",
                "blocked",
                "false",
                "false",
                "medium",
                "high",
                "Absence from draft_picks is not enough to prove UDFA for every NWR row.",
                "UDFA/free-agent source lane.",
                "Keep missing rows as Not enough information.",
            ),
        ]
    )
    for feature in (
        "height",
        "weight",
        "BMI",
        "speed_score",
        "40_time",
        "vertical_broad_agility_bench",
    ):
        rows.append(
            feature_row(
                "combine_measurements",
                feature,
                "nflverse combine",
                "available_partial",
                "review_only_context",
                "false",
                "true",
                "low",
                "partial_current_and_historical_coverage",
                "Needs separate historical validation before model R&D use.",
                "Measurement model R&D validation lane.",
                "Factual measurement display/review context only in this runner.",
            )
        )
    for feature in (
        "ESPN_NFL_grades",
        "scouting_profile_text",
        "college_production",
        "age_early_declare",
    ):
        rows.append(
            feature_row(
                "blocked_or_missing",
                feature,
                "Not enough information",
                "blocked",
                "blocked",
                "false",
                "false",
                "high" if "grade" in feature or "text" in feature else "medium",
                "high",
                "License/provenance or separate approval missing.",
                "Separate source-policy approval lane.",
                "Not used in this runner.",
            )
        )
    return rows


def feature_row(
    family: str,
    name: str,
    source: str,
    availability: str,
    approval: str,
    model_rd: str,
    display: str,
    leakage: str,
    missingness: str,
    blocker: str,
    next_gate: str,
    notes: str,
) -> dict[str, str]:
    return {
        "feature_family": family,
        "feature_name": name,
        "source": source,
        "availability_status": availability,
        "approval_status": approval,
        "allowed_for_review_only_model_rd": model_rd,
        "allowed_for_display_context": display,
        "model_use_allowed": "false",
        "training_allowed": "false",
        "review_only": "true",
        "leakage_risk": leakage,
        "missingness_risk": missingness,
        "blocker_reason": blocker,
        "required_next_gate": next_gate,
        "notes": notes,
    }


def build_display_rows(
    draft_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
    gate_e_summary: list[dict[str, str]],
    gate_e_metrics: list[dict[str, str]],
) -> list[dict[str, str]]:
    model_status = {row["metric"]: row["value"] for row in gate_e_summary}["gate_e_verdict"]
    metric_status = {row["target_name"]: row["validation_status"] for row in gate_e_metrics}
    rate_tables = {target: build_rate_table(label_rows, target) for target in TARGETS}
    output = []
    for source_row in draft_rows:
        row = base_display_row(source_row, model_status)
        methods: Counter[str] = Counter()
        display_count = 0
        nei_count = 0
        for target in TARGETS:
            column = target_to_display_column(target)
            if not has_display_features(row):
                row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            if not target_is_supported_for_position(target, row["position"]):
                row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            if metric_status.get(target) != "pass_review_only":
                row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            rate, method = display_rate_for_row(row, rate_tables[target])
            row[column] = rate
            methods[method] += 1
            display_count += 1
        row["display_field_count"] = str(display_count)
        row["not_enough_information_field_count"] = str(nei_count)
        row["rate_method_summary"] = format_counts(methods) if methods else NOT_ENOUGH
        if display_count:
            row["feature_coverage_status"] = "complete_allowed_features"
            row["validation_status"] = "all_supported_targets_pass_review_only"
            row["display_status"] = "review_only_display_fields_available"
            row["data_quality_status"] = "PARTIAL_REVIEW_ONLY_DISPLAY_V2_AVAILABLE"
            row["notes"] = "Draft-capital-repaired review-only display rates; not app-wired."
        output.append(row)
    return output


def base_display_row(source_row: dict[str, str], model_status: str) -> dict[str, str]:
    row = {
        "player_id": source_row["player_id"],
        "player_name": source_row["player_name"],
        "position": source_row["position"],
        "team": source_row["team"],
        "rookie_class_year": source_row["rookie_class_year"],
        "draft_year": source_row["draft_year"],
        "draft_round": source_row["draft_round"],
        "draft_pick": source_row["draft_pick"],
        "draft_capital_bucket": source_row["draft_capital_bucket"],
        "identity_status": "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL",
        "draft_capital_status": source_row["draft_capital_status"],
        "feature_coverage_status": NOT_ENOUGH,
        "model_rd_status": model_status,
        "validation_status": NOT_ENOUGH,
        "display_status": NOT_ENOUGH,
        "data_quality_status": source_row["data_quality_status"],
        "source_provenance_status": source_row["draft_capital_provenance"],
        "display_field_count": "0",
        "not_enough_information_field_count": str(len(TARGETS)),
        "rate_method_summary": NOT_ENOUGH,
        "review_only": "true",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "rankings_wiring_allowed": "false",
        "notes": "Missing allowed features; display values remain Not enough information.",
    }
    for target in TARGETS:
        row[target_to_display_column(target)] = NOT_ENOUGH
    return row


def build_rate_table(rows: list[dict[str, str]], target: str) -> dict[str, object]:
    eligible = eligible_rows(rows, target)
    global_rate = sum(target_value(row[target]) for row in eligible) / len(eligible)
    by_position_bucket: dict[tuple[str, str], list[int]] = defaultdict(list)
    by_position: dict[str, list[int]] = defaultdict(list)
    for row in eligible:
        actual = target_value(row[target])
        by_position_bucket[(row["position"], draft_capital_bucket(row))].append(actual)
        by_position[row["position"]].append(actual)
    return {
        "global_rate": global_rate,
        "by_position_bucket": by_position_bucket,
        "by_position": by_position,
    }


def display_rate_for_row(row: dict[str, str], rate_table: dict[str, object]) -> tuple[str, str]:
    global_rate = rate_table["global_rate"]
    by_position_bucket = rate_table["by_position_bucket"]
    by_position = rate_table["by_position"]
    grouped = by_position_bucket[(row["position"], row["draft_capital_bucket"])]
    if len(grouped) >= 5:
        return format_rate(smoothed_rate(grouped, global_rate)), "position_draft_capital_bucket"
    position_group = by_position[row["position"]]
    if len(position_group) >= 10:
        return format_rate(smoothed_rate(position_group, global_rate)), "position"
    return format_rate(global_rate), "global"


def eligible_rows(rows: list[dict[str, str]], target: str) -> list[dict[str, str]]:
    output = []
    for row in rows:
        if target.startswith("first_3y") and row["first_3y_window_complete"] != "true":
            continue
        if target.startswith("first_5y") and row["first_5y_window_complete"] != "true":
            continue
        if target_value(row.get(target)) is None:
            continue
        output.append(row)
    return output


def target_value(label: object) -> int | None:
    value = str(label or "").strip()
    if value == "hit":
        return 1
    if value == "miss":
        return 0
    return None


def target_is_supported_for_position(target: str, position: str) -> bool:
    threshold = int(target.rsplit("_top_", 1)[1].split("_", 1)[0])
    return threshold in POSITION_SUPPORTED_THRESHOLDS.get(position, set())


def target_to_display_column(target: str) -> str:
    return target.replace("_hit", "_review_display_rate")


def has_display_features(row: dict[str, str]) -> bool:
    return all(
        row[field] != NOT_ENOUGH
        for field in ("position", "draft_year", "rookie_class_year", "draft_round", "draft_pick")
    ) and row["draft_capital_bucket"] != NOT_ENOUGH


def build_display_summary_rows(display_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    values = {
        "gate_f_v2_verdict": (
            "PARTIAL_REVIEW_ONLY_DISPLAY_ARTIFACT_V2",
            "Coverage improved but remains partial.",
        ),
        "previous_valid_display_rows": ("50", "Gate F V1 valid display rows."),
        "new_valid_display_rows": (
            str(count_display_rows(display_rows)),
            "Gate F V2 valid display rows.",
        ),
        "previous_not_enough_information_rows": ("107", "Gate F V1 Not enough information rows."),
        "new_not_enough_information_rows": (
            str(sum(row["display_status"] == NOT_ENOUGH for row in display_rows)),
            "Gate F V2 Not enough information rows.",
        ),
        "rankings_wiring_allowed": ("false", "Gate G remains blocked."),
    }
    return [summary_row(metric, value, notes) for metric, (value, notes) in values.items()]


def shared_manifest_rows(name: str, rows: int) -> list[dict[str, str]]:
    return [
        summary_row("run_id", RUN_ID, name),
        summary_row("run_timestamp", datetime.now(UTC).replace(microsecond=0).isoformat(), name),
        summary_row("artifact_rows", str(rows), name),
    ]


def write_docs(
    root: Path,
    gate_a_rows: list[dict[str, str]],
    gate_b_rows: list[dict[str, str]],
    gate_d_rows: list[dict[str, str]],
    gate_e_metrics: list[dict[str, str]],
    gate_f_rows: list[dict[str, str]],
    draft_picks: list[dict[str, str]],
    combine_source_rows: list[dict[str, str]],
    draft_rows: list[dict[str, str]],
    combine_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
) -> None:
    write_doc(
        root / "00_RUNNER_INVENTORY.md",
        [
            "# Rookie Source Expansion Runner Inventory - 2026-06-30",
            "",
            f"- Actual base HEAD: `{BASE_HEAD}`",
            f"- Gate A identity rows: {len(gate_a_rows)}",
            f"- Gate B draft-capital rows: {len(gate_b_rows)}",
            f"- Gate D feature policy rows: {len(gate_d_rows)}",
            f"- Gate E validation targets: {len(gate_e_metrics)}",
            f"- Gate F V1 coverage rows: {len(gate_f_rows)}",
            f"- nflverse 2026 draft-pick rows loaded: {len(draft_picks)}",
            f"- nflverse 2026 combine rows loaded: {len(combine_source_rows)}",
            (
                "- Shared Gate E/F artifacts are available under "
                "`C:\\NWR_SHARED_DATA\\rookie_outcomes\\`."
            ),
            "",
            "Inventory is complete; no protected app/model/rank files are touched.",
        ],
    )
    write_doc(
        root / "01_SOURCE_INTAKE_POLICY_AUDIT.md",
        [
            "# Gate 1 Source Intake Policy Audit - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_SOURCE_INTAKE_POLICY`",
            "",
            "Only existing admitted nflverse/nflreadpy factual draft and combine sources are used.",
            "JackLich10 and array-carpenter repositories are blocked in this runner because",
            "the GitHub license API returned no repository license. Grade/projection/profile",
            "fields are blocked. FootballDB automated collection is blocked.",
        ],
    )
    write_doc(
        root / "02_DRAFT_CAPITAL_COVERAGE_REPAIR.md",
        [
            "# Gate 2 Draft Capital Coverage Repair - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_DRAFT_CAPITAL_COVERAGE_REPAIR`",
            "",
            "- Previous tracked draft-capital rows: 54",
            "- Previous valid Gate F display rows: 50",
            f"- Repaired nflverse draft-capital rows: {count_available_draft_rows(draft_rows)}",
            (
                "- Previous round-8 placeholders were replaced only where admitted "
                "nflverse draft picks supplied exact name + position matches."
            ),
            f"- Rows still missing: {len(draft_rows) - count_available_draft_rows(draft_rows)}",
        ],
    )
    write_doc(
        root / "03_COMBINE_MEASUREMENTS_FEATURE_INTAKE.md",
        [
            "# Gate 3 Combine Measurements Feature Intake - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_COMBINE_MEASUREMENTS_REVIEW_ONLY`",
            "",
            (
                "- Current rows with any nflverse combine measurement: "
                f"{count_available_measurement_rows(combine_rows)}"
            ),
            "- Measurements are factual review/display context only in this runner.",
            "- No grades, projections, or profile text are used.",
        ],
    )
    write_doc(
        root / "04_PROSPECT_GRADES_POLICY.md",
        [
            "# Gate 4 Prospect Grades Policy - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`BLOCKED_GRADES_LICENSE_OR_PROVENANCE`",
            "",
            "Grade/rank/projection fields are analyst-mediated and are not factual measurements.",
            "They were not ingested and are not model/display inputs in this runner.",
        ],
    )
    allowed = [
        row["feature_name"]
        for row in feature_rows
        if row["allowed_for_review_only_model_rd"] == "true"
    ]
    write_doc(
        root / "05_FEATURE_POLICY_REFRESH.md",
        [
            "# Gate 5 Feature Policy Refresh - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_FEATURE_POLICY_REFRESH`",
            "",
            f"- Review-only R&D features allowed: {', '.join(allowed)}",
            "- Combine measurements are display context only pending separate validation.",
            (
                "- Grades, profile text, CFBD production, draft value, and UDFA status "
                "remain blocked/missing."
            ),
        ],
    )
    write_doc(
        root / "06_GATE_E_REFRESH_MODEL_RD.md",
        [
            "# Gate 6 Gate E Refresh Model R&D - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_REVIEW_ONLY_MODEL_RD_REFRESH`",
            "",
            "Gate E V1 validation remains the active review-only validation source.",
            "This runner did not promote a new model or create current-player probabilities.",
            "Draft-capital coverage repair is used for the Gate F V2 display rebuild only.",
        ],
    )
    write_doc(
        root / "07_GATE_F_REBUILD_DISPLAY_ARTIFACT.md",
        [
            "# Gate 7 Gate F Rebuild Display Artifact - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_REVIEW_ONLY_DISPLAY_ARTIFACT_V2`",
            "",
            "- Previous covered rows: 157",
            "- Previous tracked draft capital: 54",
            "- Previous valid display rows: 50",
            "- Previous `Not enough information` rows: 107",
            f"- New repaired draft capital rows: {count_available_draft_rows(draft_rows)}",
            f"- New valid display rows: {count_display_rows(display_rows)}",
            (
                "- New `Not enough information` rows: "
                f"{sum(row['display_status'] == NOT_ENOUGH for row in display_rows)}"
            ),
        ],
    )
    write_doc(
        root / "08_GATE_G_RELEASE_AUDIT.md",
        [
            "# Gate 8 Gate G Release Audit - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`BLOCKED_NEEDS_DISPLAY_COVERAGE`",
            "",
            "Gate G should not run next. Gate F V2 remains partial, no user approval for",
            "Rankings wiring was granted in this runner, and all outputs remain review-only.",
        ],
    )
    write_doc(
        root / "README.md",
        [
            "# Rookie Source Expansion Coverage Runner V1",
            "",
            "This runner repairs review-only draft-capital/display coverage using admitted",
            "nflverse factual sources only. It does not scrape FootballDB, ingest blocked",
            "grade/profile sources, create production probabilities, or wire Rankings.",
        ],
    )


def load_nflverse_draft_picks() -> list[dict[str, str]]:
    import nflreadpy  # noqa: PLC0415

    data = nflreadpy.load_draft_picks([2026])
    frame = data.to_pandas() if hasattr(data, "to_pandas") else data
    return [
        {column: clean(row[column]) for column in frame.columns}
        for _, row in frame.iterrows()
    ]


def load_nflverse_combine() -> list[dict[str, str]]:
    import nflreadpy  # noqa: PLC0415

    data = nflreadpy.load_combine([2026])
    frame = data.to_pandas() if hasattr(data, "to_pandas") else data
    return [
        {column: clean(row[column]) for column in frame.columns}
        for _, row in frame.iterrows()
    ]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def write_doc(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summary_row(metric: str, value: str, notes: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": value,
        "notes": notes,
        "review_only": "true",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "rankings_wiring_allowed": "false",
    }


def count_available_draft_rows(rows: list[dict[str, str]]) -> int:
    return sum(
        row["draft_capital_status"] == "REPAIRED_NFLVERSE_DRAFT_CAPITAL_AVAILABLE"
        for row in rows
    )


def count_available_measurement_rows(rows: list[dict[str, str]]) -> int:
    return sum(row["measurement_status"] == "PARTIAL_COMBINE_MEASUREMENT_AVAILABLE" for row in rows)


def count_display_rows(rows: list[dict[str, str]]) -> int:
    return sum(int(row["display_field_count"]) > 0 for row in rows)


def clean(value: object) -> str:
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "<na>"} or not text:
        return NOT_ENOUGH
    return text


def clean_numeric(value: object) -> str:
    text = clean(value)
    if text == NOT_ENOUGH:
        return NOT_ENOUGH
    try:
        number = float(text)
    except ValueError:
        return NOT_ENOUGH
    if math.isnan(number):
        return NOT_ENOUGH
    return f"{number:.2f}".rstrip("0").rstrip(".")


def normalize_team(team: str) -> str:
    mapping = {"NOR": "NO", "SFO": "SF", "KAN": "KC", "GNB": "GB", "LVR": "LV"}
    return mapping.get(team, team)


def height_to_inches(value: str) -> str:
    if value == NOT_ENOUGH:
        return NOT_ENOUGH
    if "-" in value:
        feet, inches = value.split("-", 1)
        try:
            return str(int(feet) * 12 + int(float(inches)))
        except ValueError:
            return NOT_ENOUGH
    return clean_numeric(value)


def calc_bmi(height: str, weight: str) -> str:
    if height == NOT_ENOUGH or weight == NOT_ENOUGH:
        return NOT_ENOUGH
    return format_rate(float(weight) * 703 / (float(height) ** 2))


def calc_speed_score(weight: str, forty: str) -> str:
    if weight == NOT_ENOUGH or forty == NOT_ENOUGH:
        return NOT_ENOUGH
    return format_rate((float(weight) * 200) / (float(forty) ** 4))


def draft_capital_bucket(row: dict[str, str]) -> str:
    draft_round = to_int(row.get("draft_round"))
    draft_pick = to_int(row.get("draft_pick"))
    if draft_round == 1 and draft_pick is not None and draft_pick <= 10:
        return "round_1_top_10"
    if draft_round == 1:
        return "round_1_other"
    if draft_round == 2:
        return "round_2"
    if draft_round == 3:
        return "round_3"
    if draft_round is not None and 4 <= draft_round <= 7:
        return "round_4_7"
    return NOT_ENOUGH


def to_int(value: object) -> int | None:
    text = clean(value)
    if text == NOT_ENOUGH:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def smoothed_rate(values: list[int], global_rate: float, alpha: int = 5) -> float:
    return (sum(values) + global_rate * alpha) / (len(values) + alpha)


def format_rate(value: float) -> str:
    return f"{value:.6f}"


def format_counts(counter: Counter[str]) -> str:
    if not counter:
        return NOT_ENOUGH
    return "; ".join(f"{key}:{counter[key]}" for key in sorted(counter))


if __name__ == "__main__":
    main()
