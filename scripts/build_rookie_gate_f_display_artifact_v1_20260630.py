from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_f_display_artifact_v1_20260630"
)
SHARED_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\display_artifact_v1")
HISTORICAL_LABEL_PATH = Path(
    r"C:\NWR_SHARED_DATA\rookie_outcomes\historical_labels_v1"
    r"\rookie_historical_outcome_labels_v1.csv"
)
MODEL_RD_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\model_rd_v1")
GATE_A_RELATIVE_PATH = (
    Path("docs")
    / "hq"
    / "rookie_outcomes"
    / "cfbd_rookie_identity_approval_v1_20260629"
    / "cfbd_rookie_identity_human_approval_v1.csv"
)
GATE_B_RELATIVE_PATH = (
    Path("docs")
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_capital_review_v1_20260629"
    / "rookie_draft_capital_review_artifact_v1.csv"
)
GATE_D_POLICY_RELATIVE_PATH = (
    Path("docs")
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_d_feature_policy_v1_20260630"
    / "rookie_feature_policy_matrix_v1.csv"
)
GATE_E_SUMMARY_RELATIVE_PATH = (
    Path("docs")
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_e_model_rd_v1_20260630"
    / "rookie_model_rd_validation_summary_v1.csv"
)

BASE_HEAD = "c957ec31a2f358545a32d3ba506299fc02e6ef07"
RUN_ID = "rookie_gate_f_display_artifact_v1_20260630"
FINAL_VERDICT = "PARTIAL_REVIEW_ONLY_DISPLAY_ARTIFACT"
NOT_ENOUGH = "Not enough information"
ALLOWED_FEATURES = (
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "draft_year",
    "rookie_class_year",
    "position",
)
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

COVERAGE_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "identity_status",
    "draft_capital_status",
    "feature_coverage_status",
    "model_rd_status",
    "validation_status",
    "display_status",
    "display_field_count",
    "not_enough_information_field_count",
    "blocker_reason",
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

MANIFEST_COLUMNS = (
    "run_id",
    "run_timestamp",
    "artifact",
    "source",
    "rows",
    "output_path",
    "review_only",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "rankings_wiring_allowed",
    "notes",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-a-path", type=Path, default=REPO_ROOT / GATE_A_RELATIVE_PATH)
    parser.add_argument("--gate-b-path", type=Path, default=REPO_ROOT / GATE_B_RELATIVE_PATH)
    parser.add_argument(
        "--gate-d-policy-path",
        type=Path,
        default=REPO_ROOT / GATE_D_POLICY_RELATIVE_PATH,
    )
    parser.add_argument(
        "--gate-e-summary-path",
        type=Path,
        default=REPO_ROOT / GATE_E_SUMMARY_RELATIVE_PATH,
    )
    parser.add_argument("--historical-label-path", type=Path, default=HISTORICAL_LABEL_PATH)
    parser.add_argument(
        "--gate-e-metrics-path",
        type=Path,
        default=MODEL_RD_ROOT / "rookie_model_rd_validation_metrics_v1.csv",
    )
    parser.add_argument("--shared-output-root", type=Path, default=SHARED_OUTPUT_ROOT)
    parser.add_argument("--doc-root", type=Path, default=DOC_ROOT)
    args = parser.parse_args(argv)

    gate_a_rows = read_csv(args.gate_a_path)
    gate_b_rows = read_csv(args.gate_b_path)
    gate_d_rows = read_csv(args.gate_d_policy_path)
    gate_e_summary_rows = read_csv(args.gate_e_summary_path)
    label_rows = read_csv(args.historical_label_path)
    gate_e_metric_rows = read_csv(args.gate_e_metrics_path)

    validate_inputs(gate_b_rows, gate_d_rows, gate_e_summary_rows, gate_e_metric_rows)
    display_rows = build_display_rows(
        gate_b_rows,
        label_rows,
        gate_e_summary_rows,
        gate_e_metric_rows,
    )
    coverage_rows = build_coverage_rows(display_rows)
    summary_rows = build_summary_rows(gate_a_rows, gate_b_rows, display_rows, gate_e_metric_rows)

    args.shared_output_root.mkdir(parents=True, exist_ok=True)
    args.doc_root.mkdir(parents=True, exist_ok=True)
    display_path = args.shared_output_root / "rookie_outcome_review_only_display_artifact_v1.csv"
    manifest_path = args.shared_output_root / "rookie_outcome_review_only_display_manifest_v1.csv"
    summary_path = (
        args.shared_output_root / "rookie_outcome_review_only_display_coverage_summary_v1.csv"
    )
    tracked_coverage_path = args.doc_root / "rookie_display_artifact_coverage_matrix_v1.csv"

    write_csv(display_path, display_rows, DISPLAY_COLUMNS)
    write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)
    write_csv(tracked_coverage_path, coverage_rows, COVERAGE_COLUMNS)
    manifest_rows = build_manifest_rows(
        display_rows,
        summary_rows,
        display_path,
        summary_path,
        manifest_path,
    )
    write_csv(manifest_path, manifest_rows, MANIFEST_COLUMNS)

    write_docs(args.doc_root, gate_a_rows, gate_b_rows, display_rows, gate_e_metric_rows)
    print(
        {
            "verdict": FINAL_VERDICT,
            "current_rookie_rows": len(display_rows),
            "rows_with_display_fields": count_rows_with_display_fields(display_rows),
            "not_enough_information_rows": count_not_enough_rows(display_rows),
            "shared_output": str(args.shared_output_root),
        }
    )


def validate_inputs(
    gate_b_rows: list[dict[str, str]],
    gate_d_rows: list[dict[str, str]],
    gate_e_summary_rows: list[dict[str, str]],
    gate_e_metric_rows: list[dict[str, str]],
) -> None:
    if not gate_b_rows:
        raise ValueError("Gate B draft-capital artifact is required.")
    gate_d_allowed = {
        row["feature_name"]
        for row in gate_d_rows
        if row.get("allowed_for_review_only_model_rd") == "true"
    }
    if gate_d_allowed != set(ALLOWED_FEATURES):
        raise ValueError(f"Gate D allowed features changed: {sorted(gate_d_allowed)}")
    summary = {row["metric"]: row["value"] for row in gate_e_summary_rows}
    if summary.get("gate_e_verdict") != "PARTIAL_REVIEW_ONLY_ROOKIE_MODEL_RD":
        raise ValueError("Gate E must be partial review-only model R&D.")
    if summary.get("current_player_predictions_created") != "0":
        raise ValueError("Gate E current-player predictions must remain zero.")
    if summary.get("rankings_wiring_created") != "0":
        raise ValueError("Gate E Rankings wiring must remain zero.")
    if len(gate_e_metric_rows) != len(TARGETS):
        raise ValueError("Gate E metrics must cover the expected 12 display targets.")
    if any(row.get("validation_status") != "pass_review_only" for row in gate_e_metric_rows):
        raise ValueError("Every Gate E target must pass review-only validation.")


def build_display_rows(
    gate_b_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
    gate_e_summary_rows: list[dict[str, str]],
    gate_e_metric_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    summary = {row["metric"]: row["value"] for row in gate_e_summary_rows}
    model_rd_status = summary["gate_e_verdict"]
    metric_status = {row["target_name"]: row["validation_status"] for row in gate_e_metric_rows}
    rate_tables = {target: build_rate_table(label_rows, target) for target in TARGETS}
    output: list[dict[str, str]] = []
    for source_row in gate_b_rows:
        display_row = base_display_row(source_row, model_rd_status)
        methods: Counter[str] = Counter()
        field_count = 0
        nei_count = 0
        for target in TARGETS:
            column = target_to_display_column(target)
            if not has_complete_allowed_features(display_row):
                display_row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            if not target_is_supported_for_position(target, display_row["position"]):
                display_row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            if metric_status.get(target) != "pass_review_only":
                display_row[column] = NOT_ENOUGH
                nei_count += 1
                continue
            rate, method = display_rate_for_row(display_row, rate_tables[target])
            display_row[column] = rate
            methods[method] += 1
            field_count += 1

        display_row["display_field_count"] = str(field_count)
        display_row["not_enough_information_field_count"] = str(nei_count)
        display_row["rate_method_summary"] = format_counts(methods) if methods else NOT_ENOUGH
        if field_count:
            display_row["feature_coverage_status"] = "complete_allowed_features"
            display_row["validation_status"] = "all_supported_targets_pass_review_only"
            display_row["display_status"] = "review_only_display_fields_available"
            display_row["data_quality_status"] = "PARTIAL_REVIEW_ONLY_DISPLAY_AVAILABLE"
            display_row["notes"] = (
                "Historical empirical review display rates only; not production, "
                "not source truth, not Rankings-wired."
            )
        else:
            display_row["validation_status"] = NOT_ENOUGH
            display_row["display_status"] = NOT_ENOUGH
            display_row["notes"] = (
                "Missing allowed features; display values remain Not enough information."
            )
        output.append(display_row)
    return output


def base_display_row(source_row: dict[str, str], model_rd_status: str) -> dict[str, str]:
    draft_pick = clean_value(source_row.get("overall_pick"))
    display_row = {
        "player_id": clean_value(source_row.get("player_id")),
        "player_name": clean_value(source_row.get("player_name")),
        "position": clean_value(source_row.get("position")),
        "team": clean_value(source_row.get("drafted_team")),
        "rookie_class_year": clean_value(source_row.get("rookie_class_year")),
        "draft_year": clean_value(source_row.get("draft_year")),
        "draft_round": clean_value(source_row.get("draft_round")),
        "draft_pick": draft_pick,
        "draft_capital_bucket": draft_capital_bucket(
            {
                "draft_round": clean_value(source_row.get("draft_round")),
                "draft_pick": draft_pick,
            }
        ),
        "identity_status": clean_value(source_row.get("cfbd_identity_approval_status")),
        "draft_capital_status": clean_value(source_row.get("data_quality_status")),
        "feature_coverage_status": NOT_ENOUGH,
        "model_rd_status": model_rd_status,
        "validation_status": NOT_ENOUGH,
        "display_status": NOT_ENOUGH,
        "data_quality_status": clean_value(source_row.get("data_quality_status")),
        "review_only": "true",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "rankings_wiring_allowed": "false",
        "notes": NOT_ENOUGH,
    }
    for target in TARGETS:
        display_row[target_to_display_column(target)] = NOT_ENOUGH
    return display_row


def build_rate_table(rows: list[dict[str, str]], target: str) -> dict[str, object]:
    eligible = eligible_rows(rows, target)
    if not eligible:
        return {"global_rate": None, "by_position_bucket": {}, "by_position": {}}
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
    if global_rate is None:
        return NOT_ENOUGH, "not_enough_information"
    by_position_bucket = rate_table["by_position_bucket"]
    by_position = rate_table["by_position"]
    position = row["position"]
    bucket = row["draft_capital_bucket"]
    grouped = by_position_bucket[(position, bucket)]
    if len(grouped) >= 5:
        return format_rate(smoothed_rate(grouped, global_rate)), "position_draft_capital_bucket"
    position_group = by_position[position]
    if len(position_group) >= 10:
        return format_rate(smoothed_rate(position_group, global_rate)), "position"
    return format_rate(global_rate), "global"


def eligible_rows(rows: list[dict[str, str]], target: str) -> list[dict[str, str]]:
    output = []
    for row in rows:
        if target.startswith("first_3y") and row.get("first_3y_window_complete") != "true":
            continue
        if target.startswith("first_5y") and row.get("first_5y_window_complete") != "true":
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


def has_complete_allowed_features(row: dict[str, str]) -> bool:
    for feature in ("position", "draft_year", "rookie_class_year", "draft_round", "draft_pick"):
        if clean_value(row.get(feature)) == NOT_ENOUGH:
            return False
    return clean_value(row.get("draft_capital_bucket")) != "not_enough_information"


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
    return "not_enough_information"


def smoothed_rate(values: list[int], global_rate: float, alpha: int = 5) -> float:
    return (sum(values) + global_rate * alpha) / (len(values) + alpha)


def build_coverage_rows(display_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in display_rows:
        blocker = NOT_ENOUGH
        if row["display_status"] == NOT_ENOUGH:
            blocker = "Missing allowed draft-capital features for Gate F display artifact."
        output.append(
            {
                column: row.get(column, blocker if column == "blocker_reason" else NOT_ENOUGH)
                for column in COVERAGE_COLUMNS
            }
        )
    return output


def build_summary_rows(
    gate_a_rows: list[dict[str, str]],
    gate_b_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
    gate_e_metric_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows_with_display = count_rows_with_display_fields(display_rows)
    not_enough_rows = count_not_enough_rows(display_rows)
    tracked_draft_capital_rows = count_rows_with_tracked_draft_capital(gate_b_rows)
    metrics = {
        "gate_f_verdict": (
            FINAL_VERDICT,
            "Partial because valid Gate D feature coverage is 50 of 157 rows.",
        ),
        "gate_a_identity_rows": (str(len(gate_a_rows)), "Gate A human-review artifact rows."),
        "current_rookie_rows": (
            str(len(gate_b_rows)),
            "Approved Gate-A identities carried into Gate B.",
        ),
        "rows_with_tracked_draft_capital": (
            str(tracked_draft_capital_rows),
            "Rows with tracked review-only round/pick/team before Gate D bucket validation.",
        ),
        "rows_with_outcome_display_fields": (
            str(rows_with_display),
            "Rows with complete allowed features and at least one review display rate.",
        ),
        "not_enough_information_rows": (
            str(not_enough_rows),
            "Rows kept as Not enough information because allowed features are incomplete.",
        ),
        "gate_e_targets_validated": (
            str(len(gate_e_metric_rows)),
            "Gate E review-only validation targets.",
        ),
        "gate_e_targets_passed_review_only": (
            str(sum(row["validation_status"] == "pass_review_only" for row in gate_e_metric_rows)),
            "Targets passing review-only validation.",
        ),
        "rankings_wiring_created": ("0", "No Rankings or app wiring in Gate F."),
        "app_facing_columns_created": ("0", "Generated shared-data review artifact only."),
        "rows_approved_for_model_use": ("0", "All rows keep model_use_allowed=false."),
        "rows_approved_for_training_use": ("0", "All rows keep training_allowed=false."),
        "gate_g_can_run_next": ("false", "Gate G remains blocked because Gate F is partial."),
    }
    return [
        summary_row(metric, value, notes)
        for metric, (value, notes) in metrics.items()
    ]


def build_manifest_rows(
    display_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
    display_path: Path,
    summary_path: Path,
    manifest_path: Path,
) -> list[dict[str, str]]:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    return [
        manifest_row(
            timestamp,
            "rookie_outcome_review_only_display_artifact_v1.csv",
            f"{GATE_B_RELATIVE_PATH.as_posix()} + Gate E review-only empirical baseline",
            len(display_rows),
            display_path,
            "Review-only current rookie display artifact; not app wired.",
        ),
        manifest_row(
            timestamp,
            "rookie_outcome_review_only_display_coverage_summary_v1.csv",
            "derived_from_display_artifact",
            len(summary_rows),
            summary_path,
            "Review-only coverage summary.",
        ),
        manifest_row(
            timestamp,
            "rookie_outcome_review_only_display_manifest_v1.csv",
            "derived_from_display_artifact",
            3,
            manifest_path,
            "Shared-data manifest.",
        ),
    ]


def manifest_row(
    timestamp: str,
    artifact: str,
    source: str,
    rows: int,
    output_path: Path,
    notes: str,
) -> dict[str, str]:
    return {
        "run_id": RUN_ID,
        "run_timestamp": timestamp,
        "artifact": artifact,
        "source": source,
        "rows": str(rows),
        "output_path": str(output_path),
        "review_only": "true",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "rankings_wiring_allowed": "false",
        "notes": notes,
    }


def write_docs(
    doc_root: Path,
    gate_a_rows: list[dict[str, str]],
    gate_b_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
    gate_e_metric_rows: list[dict[str, str]],
) -> None:
    rows_with_display = count_rows_with_display_fields(display_rows)
    not_enough_rows = count_not_enough_rows(display_rows)
    tracked_draft_capital_rows = count_rows_with_tracked_draft_capital(gate_b_rows)
    position_counts = Counter(row["position"] for row in display_rows)
    covered_position_counts = Counter(
        row["position"] for row in display_rows if int(row["display_field_count"])
    )
    write_text(
        doc_root / "00_DISPLAY_ARTIFACT_INVENTORY.md",
        [
            "# Gate F Display Artifact Inventory - 2026-06-30",
            "",
            f"- Actual base HEAD: `{BASE_HEAD}`",
            f"- Gate E docs: `{GATE_E_SUMMARY_RELATIVE_PATH.as_posix()}`",
            "- Gate E shared outputs: `C:\\NWR_SHARED_DATA\\rookie_outcomes\\model_rd_v1\\`",
            f"- Gate E validation targets: {len(gate_e_metric_rows)} all `pass_review_only`",
            f"- Gate A identity review rows: {len(gate_a_rows)}",
            f"- Current rookie candidate source: `{GATE_B_RELATIVE_PATH.as_posix()}`",
            f"- Current rookie rows considered: {len(gate_b_rows)}",
            f"- Rows with tracked review-only draft capital: {tracked_draft_capital_rows}",
            f"- Rows with complete Gate D allowed features: {rows_with_display}",
            f"- Rows left as `Not enough information`: {not_enough_rows}",
            f"- Position coverage: {format_counts(position_counts)}",
            f"- Position coverage with display fields: {format_counts(covered_position_counts)}",
            "",
            "A partial review-only display artifact can be built. It is not source truth,",
            "not production, and not Rankings-wired. Gate G remains blocked because",
            "coverage is partial. Four tracked draft-capital rows use round 8 and do",
            "not map to the Gate D draft-capital bucket policy.",
        ],
    )
    write_text(
        doc_root / "01_DISPLAY_ARTIFACT_SPEC.md",
        [
            "# Gate F Display Artifact Spec - 2026-06-30",
            "",
            "## Rules",
            "",
            "- review-only and display-only",
            "- not Rankings-wired in this lane",
            "- no hidden sort logic",
            "- missing data is `Not enough information`, never `0%`",
            "- only Gate D allowed features are used",
            "- Gate E review-only validation must exist before rates are displayed",
            (
                "- market, ADP, DynastyProcess, vendor, Gmail, projections, and CFBD "
                "production are not used"
            ),
            "",
            "## Status Fields",
            "",
            "- identity_status",
            "- draft_capital_status",
            "- feature_coverage_status",
            "- model_rd_status",
            "- validation_status",
            "- display_status",
            "- data_quality_status",
            "- review_only=true",
            "- display_only=true",
            "- model_use_allowed=false",
            "- training_allowed=false",
            "- rankings_wiring_allowed=false",
        ],
    )
    write_text(
        doc_root / "02_GATE_F_DISPLAY_ARTIFACT_DECISION.md",
        [
            "# Gate F Display Artifact Decision - 2026-06-30",
            "",
            "## Verdict",
            "",
            f"`{FINAL_VERDICT}`",
            "",
            f"Rows considered: {len(display_rows)}.",
            f"Rows with tracked review-only draft capital: {tracked_draft_capital_rows}.",
            f"Rows with review-only display fields: {rows_with_display}.",
            f"Rows left as `Not enough information`: {not_enough_rows}.",
            "",
            "The artifact is partial because valid Gate D feature coverage exists for",
            "50 of 157 approved review identities. Four rows have tracked round-8",
            "display draft capital but no allowed Gate D draft-capital bucket.",
            "No current rows are approved for model use or training use.",
            "",
            "## Gate G",
            "",
            "Gate G should not run yet. This lane is partial and does not authorize",
            "Rankings integration, app-facing rookie columns, or production model use.",
        ],
    )
    write_text(
        doc_root / "README.md",
        [
            "# Rookie Gate F Review-Only Display Artifact V1",
            "",
            "This folder tracks the Gate F display-artifact feasibility summary.",
            "Generated display CSVs live outside git under",
            "`C:\\NWR_SHARED_DATA\\rookie_outcomes\\display_artifact_v1\\`.",
            "",
            "The artifact is review-only, display-only, not source truth, not training",
            "truth, and not wired to Rankings. Missing rows remain `Not enough information`.",
        ],
    )


def count_rows_with_display_fields(rows: list[dict[str, str]]) -> int:
    return sum(int(row["display_field_count"]) > 0 for row in rows)


def count_not_enough_rows(rows: list[dict[str, str]]) -> int:
    return sum(row["display_status"] == NOT_ENOUGH for row in rows)


def count_rows_with_tracked_draft_capital(rows: list[dict[str, str]]) -> int:
    return sum(
        clean_value(row.get("draft_round")) != NOT_ENOUGH
        and clean_value(row.get("overall_pick")) != NOT_ENOUGH
        and clean_value(row.get("drafted_team")) != NOT_ENOUGH
        for row in rows
    )


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: tuple[str, ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def clean_value(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return NOT_ENOUGH
    return text


def to_int(value: object) -> int | None:
    text = str(value or "").strip()
    if not text or text == NOT_ENOUGH:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def format_rate(value: float) -> str:
    return f"{value:.6f}"


def format_counts(counter: Counter[str]) -> str:
    if not counter:
        return NOT_ENOUGH
    return "; ".join(f"{key}:{counter[key]}" for key in sorted(counter))


if __name__ == "__main__":
    main()
