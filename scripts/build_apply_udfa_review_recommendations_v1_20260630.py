from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_current_rookie_universe_udfa_policy_v1_20260630 import (  # noqa: E402
    DISPLAY_COLUMNS as V4_DISPLAY_COLUMNS,
)

INVENTORY_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "apply_udfa_review_recommendations_v1_20260630"
)
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "udfa_review_application_v1_20260630"
)
PACKET_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "current_rookie_udfa_unknown_review_packet_v1_20260630"
)
UNIVERSE_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "current_rookie_universe_udfa_policy_v1_20260630"
)
SHARED_DISPLAY_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\display_artifact_v5")

RECOMMENDATION_PATH = (
    PACKET_ROOT / "current_rookie_udfa_unknown_review_recommendations_v1.csv"
)
EVIDENCE_PATH = PACKET_ROOT / "current_rookie_udfa_unknown_evidence_packet_v1.csv"
PREVIEW_PATH = PACKET_ROOT / "rookie_display_artifact_v5_preview_coverage_matrix.csv"
V4_DISPLAY_PATH = UNIVERSE_ROOT / "rookie_display_artifact_v4_coverage_matrix.csv"
UNIVERSE_PATH = UNIVERSE_ROOT / "current_rookie_universe_matrix_v1.csv"

BASE_HEAD = "2fbc252016eefab3149fa1e119f7bbe098c5ec3d"
RUN_ID = "apply_udfa_review_recommendations_v1_20260630"
NOT_ENOUGH = "Not enough information"
APPROVAL_SOURCE = "user_chat_20260630"
APPROVAL_NOTES = (
    "User accepted evidence-packet recommendations for UDFA status review-only. "
    "This is not model, training, source-truth, ranking, or projection approval."
)

APPLICATION_COLUMNS = (
    "run_id",
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "current_status_before",
    "recommended_human_decision",
    "evidence_strength",
    "nflverse_draft_pick_search_result",
    "human_decision",
    "approved_by_human",
    "approval_scope",
    "udfa_status",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "rankings_wiring_allowed",
    "approval_source",
    "approval_notes",
)

V5_DISPLAY_COLUMNS = (
    *V4_DISPLAY_COLUMNS,
    "human_decision",
    "approved_by_human",
    "approval_scope",
    "udfa_status",
    "source_truth_allowed",
    "approval_source",
    "approval_notes",
    "outcome_display_field_count",
    "status_display_available",
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

RATE_COLUMNS = tuple(
    column for column in V4_DISPLAY_COLUMNS if column.endswith("_review_display_rate")
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-root", type=Path, default=INVENTORY_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--shared-display-root", type=Path, default=SHARED_DISPLAY_ROOT)
    args = parser.parse_args(argv)

    args.inventory_root.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.shared_display_root.mkdir(parents=True, exist_ok=True)

    recommendation_rows = read_csv(RECOMMENDATION_PATH)
    evidence_rows = read_csv(EVIDENCE_PATH)
    preview_rows = read_csv(PREVIEW_PATH)
    v4_display_rows = read_csv(V4_DISPLAY_PATH)
    universe_rows = read_csv(UNIVERSE_PATH)

    validate_inputs(recommendation_rows, evidence_rows, preview_rows, universe_rows)

    evidence_index = row_index(evidence_rows)
    application_rows = build_application_rows(recommendation_rows, evidence_index)
    application_index = row_index(application_rows)
    v5_display_rows = build_v5_display_rows(v4_display_rows, application_index)
    summary_rows = build_summary_rows(v5_display_rows, application_rows)

    write_csv(
        args.output_root / "udfa_review_application_v1.csv",
        APPLICATION_COLUMNS,
        application_rows,
    )
    write_csv(
        args.output_root / "rookie_display_artifact_v5_coverage_matrix.csv",
        V5_DISPLAY_COLUMNS,
        v5_display_rows,
    )
    write_csv(
        args.shared_display_root / "rookie_outcome_review_only_display_artifact_v5.csv",
        V5_DISPLAY_COLUMNS,
        v5_display_rows,
    )
    write_csv(
        args.shared_display_root
        / "rookie_outcome_review_only_display_coverage_summary_v5.csv",
        SUMMARY_COLUMNS,
        summary_rows,
    )
    write_csv(
        args.shared_display_root / "rookie_outcome_review_only_display_manifest_v5.csv",
        SUMMARY_COLUMNS,
        shared_manifest_rows(len(v5_display_rows)),
    )
    write_docs(args.inventory_root, args.output_root, application_rows, v5_display_rows)
    print(
        {
            "final_verdict": "GREEN_REVIEW_ONLY_UDFA_APPLICATION_V1",
            "application_rows": len(application_rows),
            "confirmed_udfa_review_only": count_application(
                application_rows,
                "CONFIRM_UDFA_REVIEW_ONLY",
            ),
            "keep_unknown": count_application(application_rows, "KEEP_UNKNOWN"),
            "v5_rows": len(v5_display_rows),
            "v5_outcome_rate_rows": count_outcome_rows(v5_display_rows),
            "v5_udfa_status_rows": count_udfa_status_rows(v5_display_rows),
            "gate_g": "BLOCKED_NEEDS_RANKINGS_WIRING_APPROVAL",
        }
    )


def validate_inputs(
    recommendation_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    preview_rows: list[dict[str, str]],
    universe_rows: list[dict[str, str]],
) -> None:
    required_paths = [
        RECOMMENDATION_PATH,
        EVIDENCE_PATH,
        PREVIEW_PATH,
        V4_DISPLAY_PATH,
        UNIVERSE_PATH,
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        raise RuntimeError(f"Missing required packet/source files: {missing}")

    recommendation_counts = Counter(
        row["recommended_human_decision"] for row in recommendation_rows
    )
    if recommendation_counts["CONFIRM_UDFA_REVIEW_ONLY"] != 28:
        raise RuntimeError("Expected exactly 28 CONFIRM_UDFA_REVIEW_ONLY rows.")
    if recommendation_counts["KEEP_UNKNOWN"] != 10:
        raise RuntimeError("Expected exactly 10 KEEP_UNKNOWN rows.")
    if any(row["model_use_allowed"] != "false" for row in recommendation_rows):
        raise RuntimeError("Recommendation packet contains model-use rows.")
    if any(row["training_allowed"] != "false" for row in recommendation_rows):
        raise RuntimeError("Recommendation packet contains training-use rows.")

    evidence_keys = set(row_index(evidence_rows))
    universe_keys = set(row_index(universe_rows))
    for row in recommendation_rows:
        key = make_key(row)
        if key not in evidence_keys:
            raise RuntimeError(f"Recommendation row missing evidence match: {key}")
        if key not in universe_keys:
            raise RuntimeError(f"Recommendation row missing universe match: {key}")

    preview_counts = Counter(
        row["preview_display_status_if_accepted"] for row in preview_rows
    )
    expected_preview = {
        "review_only_outcome_rates_available": 117,
        "udfa_status_review_only_preview": 28,
        NOT_ENOUGH: 10,
        "wrong_universe_blocked": 2,
    }
    for status, count in expected_preview.items():
        if preview_counts[status] != count:
            raise RuntimeError(f"Unexpected preview count for {status}: {count}")


def build_application_rows(
    recommendation_rows: list[dict[str, str]],
    evidence_index: dict[tuple[str, str, str, str], dict[str, str]],
) -> list[dict[str, str]]:
    output = []
    for row in recommendation_rows:
        evidence = evidence_index[make_key(row)]
        decision = row["recommended_human_decision"]
        is_confirm = decision == "CONFIRM_UDFA_REVIEW_ONLY"
        output.append(
            {
                "run_id": RUN_ID,
                "player_id": clean(row["player_id"]),
                "player_name": clean(row["player_name"]),
                "position": clean(row["position"]),
                "team": clean(row["team"]),
                "rookie_class_year": clean(row["rookie_class_year"]),
                "current_status_before": clean(evidence["current_status_before"]),
                "recommended_human_decision": decision,
                "evidence_strength": clean(row["evidence_strength"]),
                "nflverse_draft_pick_search_result": clean(
                    evidence["nflverse_draft_pick_search_result"]
                ),
                "human_decision": decision,
                "approved_by_human": "true" if is_confirm else "false",
                "approval_scope": "udfa_status_review_only" if is_confirm else "none",
                "udfa_status": "confirmed_udfa_review_only" if is_confirm else "unknown",
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "source_truth_allowed": "false",
                "rankings_wiring_allowed": "false",
                "approval_source": APPROVAL_SOURCE if is_confirm else "not_applicable",
                "approval_notes": APPROVAL_NOTES if is_confirm else "Kept unknown.",
            }
        )
    return output


def build_v5_display_rows(
    v4_rows: list[dict[str, str]],
    application_index: dict[tuple[str, str, str, str], dict[str, str]],
) -> list[dict[str, str]]:
    output = []
    for row in v4_rows:
        next_row = {column: clean(row.get(column)) for column in V4_DISPLAY_COLUMNS}
        application = application_index.get(make_key(row))
        human_decision = "not_applicable"
        approved = "false"
        approval_scope = "not_applicable"
        udfa_status = udfa_status_for_non_application(next_row)
        approval_source = "not_applicable"
        approval_notes = "No UDFA review application for this row."

        if application:
            human_decision = application["human_decision"]
            approved = application["approved_by_human"]
            approval_scope = application["approval_scope"]
            udfa_status = application["udfa_status"]
            approval_source = application["approval_source"]
            approval_notes = application["approval_notes"]

            if human_decision == "CONFIRM_UDFA_REVIEW_ONLY":
                apply_confirmed_udfa_status(next_row)
            elif human_decision == "KEEP_UNKNOWN":
                apply_keep_unknown_status(next_row)
        elif next_row["wrong_universe_flag"] == "true":
            next_row["display_status"] = "wrong_universe_blocked"
            next_row["notes"] = "Wrong-universe/name-collision row remains blocked."

        status_display_available = (
            "true"
            if int(next_row["display_field_count"]) > 0
            or udfa_status == "confirmed_udfa_review_only"
            else "false"
        )

        output.append(
            {
                **next_row,
                "human_decision": human_decision,
                "approved_by_human": approved,
                "approval_scope": approval_scope,
                "udfa_status": udfa_status,
                "source_truth_allowed": "false",
                "approval_source": approval_source,
                "approval_notes": approval_notes,
                "outcome_display_field_count": next_row["display_field_count"],
                "status_display_available": status_display_available,
            }
        )
    return output


def apply_confirmed_udfa_status(row: dict[str, str]) -> None:
    row["udffa_or_undrafted_status"] = "confirmed_udfa_review_only"
    row["current_rookie_universe_status"] = "current_rookie_confirmed_udfa_review_only"
    row["udfa_display_status"] = "confirmed_udfa_review_only_status"
    row["draft_capital_bucket"] = "udfa_review_only"
    row["display_status"] = "confirmed_udfa_review_only_status_available"
    row["data_quality_status"] = "PARTIAL_REVIEW_ONLY_UDFA_STATUS_ONLY"
    row["source_provenance_status"] = (
        "User accepted review-packet UDFA recommendation; no 2025/2026 "
        "nflverse draft-pick match; review-only status, not source truth."
    )
    row["repair_action"] = "applied_user_accepted_udfa_review_recommendation"
    row["repair_confidence"] = "HIGH_REVIEW_ONLY_STATUS"
    row["display_field_count"] = "0"
    row["not_enough_information_field_count"] = str(len(RATE_COLUMNS))
    row["rate_method_summary"] = NOT_ENOUGH
    row["notes"] = (
        "Confirmed review-only UDFA status; no outcome probabilities; no app wiring."
    )
    for column in RATE_COLUMNS:
        row[column] = NOT_ENOUGH


def apply_keep_unknown_status(row: dict[str, str]) -> None:
    row["udffa_or_undrafted_status"] = "unknown"
    row["udfa_display_status"] = "unknown_keep_not_enough_information"
    row["display_status"] = NOT_ENOUGH
    row["data_quality_status"] = "BLOCKED_NEEDS_MORE_UDFA_EVIDENCE"
    row["source_provenance_status"] = "User accepted keeping row unknown."
    row["display_field_count"] = "0"
    row["not_enough_information_field_count"] = str(len(RATE_COLUMNS))
    row["rate_method_summary"] = NOT_ENOUGH
    row["notes"] = "Unknown row remains Not enough information."
    for column in RATE_COLUMNS:
        row[column] = NOT_ENOUGH


def udfa_status_for_non_application(row: dict[str, str]) -> str:
    if row["udffa_or_undrafted_status"] == "not_udfa_drafted":
        return "not_udfa_drafted"
    if row["wrong_universe_flag"] == "true":
        return "wrong_universe_blocked"
    return clean(row["udffa_or_undrafted_status"])


def build_summary_rows(
    display_rows: list[dict[str, str]],
    application_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    application_counts = Counter(row["human_decision"] for row in application_rows)
    display_counts = Counter(row["display_status"] for row in display_rows)
    metrics = [
        ("total_current_rookie_rows", len(display_rows), "Gate F V5 current rookie rows."),
        (
            "existing_review_only_outcome_rate_rows",
            count_outcome_rows(display_rows),
            "Drafted rows with review-only outcome rates preserved.",
        ),
        (
            "confirmed_udfa_review_only_status_rows",
            count_udfa_status_rows(display_rows),
            "Accepted UDFA status-only rows; no probabilities.",
        ),
        ("keep_unknown_rows", application_counts["KEEP_UNKNOWN"], "Kept unknown."),
        (
            "not_enough_information_rows",
            display_counts[NOT_ENOUGH],
            "Rows still lacking safe display evidence.",
        ),
        (
            "wrong_universe_blocked_rows",
            display_counts["wrong_universe_blocked"],
            "Name-collision/wrong-universe rows remain blocked.",
        ),
        ("rows_approved_for_model_use", 0, "No model use allowed."),
        ("rankings_wiring_allowed_rows", 0, "No Rankings wiring in this lane."),
    ]
    return [summary_row(metric, value, notes) for metric, value, notes in metrics]


def shared_manifest_rows(row_count: int) -> list[dict[str, str]]:
    run_timestamp = datetime.now(UTC).isoformat()
    return [
        summary_row("run_id", RUN_ID, "Review-only Gate F V5 display artifact."),
        summary_row("run_timestamp", run_timestamp, "UTC."),
        summary_row("row_count", row_count, "Generated shared-data rows."),
        summary_row(
            "source",
            "tracked_udfa_review_application_v1",
            "Generated from tracked review-only application artifacts.",
        ),
    ]


def summary_row(metric: str, value: object, notes: str) -> dict[str, str]:
    return {
        "metric": str(metric),
        "value": str(value),
        "notes": notes,
        "review_only": "true",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "rankings_wiring_allowed": "false",
    }


def write_docs(
    inventory_root: Path,
    output_root: Path,
    application_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
) -> None:
    confirm_count = count_application(application_rows, "CONFIRM_UDFA_REVIEW_ONLY")
    unknown_count = count_application(application_rows, "KEEP_UNKNOWN")
    outcome_rows = count_outcome_rows(display_rows)
    udfa_status_rows = count_udfa_status_rows(display_rows)
    wrong_rows = count_display_status(display_rows, "wrong_universe_blocked")
    nei_rows = count_display_status(display_rows, NOT_ENOUGH)
    write_doc(
        inventory_root / "00_APPLICATION_INVENTORY.md",
        [
            "# Apply UDFA Review Recommendations V1 - Inventory",
            "",
            f"- Actual base HEAD: `{BASE_HEAD}`",
            f"- Recommendation packet path: `{relative(RECOMMENDATION_PATH)}`",
            f"- Evidence packet path: `{relative(EVIDENCE_PATH)}`",
            f"- Gate F V5 preview path: `{relative(PREVIEW_PATH)}`",
            f"- Current Gate F V4 source: `{relative(V4_DISPLAY_PATH)}`",
            f"- Current rookie universe source: `{relative(UNIVERSE_PATH)}`",
            f"- Expected `CONFIRM_UDFA_REVIEW_ONLY` rows: {confirm_count}",
            f"- Expected `KEEP_UNKNOWN` rows: {unknown_count}",
            "- Expected `wrong_universe_blocked` rows: 2",
            "",
            "Stop conditions passed: packet exists, 28/10 counts match, all packet",
            "model/training flags are false, and rows match the current rookie universe.",
        ],
    )
    write_doc(
        output_root / "UDFA_REVIEW_APPLICATION_V1_SUMMARY.md",
        [
            "# UDFA Review Application V1 Summary",
            "",
            f"- Accepted rows: {confirm_count}",
            f"- Unknown rows: {unknown_count}",
            f"- Wrong-universe rows: {wrong_rows}",
            "- No model/training/source-truth promotion.",
            "- No rookie probabilities created.",
            "- No Rankings or app wiring created.",
            "",
            "The accepted rows are approved only for `udfa_status_review_only`.",
            "They remain blocked for model use, training use, source truth, and ranking",
            "integration.",
        ],
    )
    write_doc(
        output_root / "GATE_G_RELEASE_AUDIT_AFTER_UDFA_APPLICATION_V1.md",
        [
            "# Gate G Release Audit After UDFA Application V1",
            "",
            "## Verdict",
            "",
            "`BLOCKED_NEEDS_RANKINGS_WIRING_APPROVAL`",
            "",
            f"- Total current rookie rows: {len(display_rows)}",
            f"- Existing review-only outcome-rate rows: {outcome_rows}",
            f"- Confirmed UDFA review-only status rows: {udfa_status_rows}",
            f"- `Not enough information` rows: {nei_rows}",
            f"- Wrong-universe blocked rows: {wrong_rows}",
            "- Validation status is preserved from Gate E/Gate F for drafted rows.",
            "- UDFA rows are status-only and do not receive fake probabilities.",
            "- Rankings wiring was not touched.",
            "",
            "Gate G should not run next without explicit Rankings wiring approval and",
            "UI review for the review-only Outcome Lens.",
        ],
    )
    write_doc(
        output_root / "README.md",
        [
            "# UDFA Review Application V1",
            "",
            "Applies the user-accepted UDFA recommendations as review-only status",
            "decisions and rebuilds the official Gate F V5 display artifact. This is",
            "not model input, not training truth, not source truth, and not app-wired.",
        ],
    )


def count_application(rows: list[dict[str, str]], decision: str) -> int:
    return sum(row["human_decision"] == decision for row in rows)


def count_outcome_rows(rows: list[dict[str, str]]) -> int:
    return sum(int(row["outcome_display_field_count"]) > 0 for row in rows)


def count_udfa_status_rows(rows: list[dict[str, str]]) -> int:
    return sum(row["udfa_status"] == "confirmed_udfa_review_only" for row in rows)


def count_display_status(rows: list[dict[str, str]], status: str) -> int:
    return sum(row["display_status"] == status for row in rows)


def make_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        clean(row["player_id"]),
        clean(row["player_name"]),
        clean(row["position"]),
        clean(row["team"]),
    )


def row_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    return {make_key(row): row for row in rows}


def clean(value: object) -> str:
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "<na>"} or not text:
        return NOT_ENOUGH
    return text


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


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


if __name__ == "__main__":
    main()
