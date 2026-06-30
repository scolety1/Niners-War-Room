from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_outcome_drafted_only_review_v1_20260630"
)
ENTRY_STATUS_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_entry_status_hygiene_v1_20260630"
    / "historical_rookie_entry_status_v1.csv"
)
ENTRY_STATUS_ROOT = ENTRY_STATUS_PATH.parent
LABEL_PATH = Path(
    r"C:\NWR_SHARED_DATA\rookie_outcomes\historical_labels_v1"
    r"\rookie_historical_outcome_labels_v1.csv"
)

BASE_HEAD = "a3d4b94d1e482a022c1cc17b32cbb7e8f2bf85cc"
RUN_ID = "rookie_outcome_drafted_only_review_v1_20260630"
NOT_ENOUGH = "Not enough information"
POSITIONS = {"QB", "RB", "WR", "TE"}

THRESHOLD_MAP = {
    "QB": ("top_6", "top_12"),
    "RB": ("top_6", "top_12", "top_24", "top_36"),
    "WR": ("top_6", "top_12", "top_24", "top_36"),
    "TE": ("top_6", "top_12"),
}

COVERAGE_COLUMNS = (
    "draft_year",
    "position",
    "drafted_count",
    "rookie_year_label_count",
    "2y_label_count",
    "3y_label_count",
    "5y_label_count",
    "missing_label_count",
    "incomplete_window_count",
    "notes",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

AUDIT_COLUMNS = (
    "player_name",
    "position",
    "rookie_class_year",
    "draft_year",
    "draft_round",
    "overall_pick",
    "drafted_team",
    "entry_status",
    "has_rookie_year_label",
    "has_2y_label",
    "has_3y_label",
    "has_5y_label",
    "outcome_window_status",
    "censoring_status",
    "blocker_reason",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)

    entry_rows = load_entry_rows()
    label_rows = load_label_rows()
    drafted_rows = [
        row
        for row in entry_rows
        if row["entry_status"] == "drafted" and row["position"] in POSITIONS
    ]
    if not drafted_rows:
        raise RuntimeError("BLOCKED_NEEDS_ENTRY_STATUS_ARTIFACT: no drafted rows.")

    label_index = build_label_index(label_rows)
    audit_rows = [build_audit_row(row, label_index) for row in drafted_rows]
    coverage_rows = build_coverage_rows(audit_rows)
    entry_counts = Counter(row["entry_status"] for row in entry_rows)

    write_csv(
        args.output_root / "drafted_only_outcome_player_audit.csv",
        AUDIT_COLUMNS,
        audit_rows,
    )
    write_csv(
        args.output_root / "drafted_only_outcome_coverage.csv",
        COVERAGE_COLUMNS,
        coverage_rows,
    )
    write_docs(args.output_root, entry_counts, audit_rows, coverage_rows, label_rows)

    print(
        {
            "verdict": "YELLOW_DRAFTED_ONLY_REVIEW_READY",
            "drafted_player_rows": len(audit_rows),
            "label_rows_used": count_any_label(audit_rows),
            "rookie_year_labels": count_flag(audit_rows, "has_rookie_year_label"),
            "2y_labels": count_flag(audit_rows, "has_2y_label"),
            "3y_labels": count_flag(audit_rows, "has_3y_label"),
            "5y_labels": count_flag(audit_rows, "has_5y_label"),
            "confirmed_udfa_count": entry_counts["confirmed_udfa"],
            "likely_udfa_needs_review_count": entry_counts["likely_udfa_needs_review"],
        }
    )


def load_entry_rows() -> list[dict[str, str]]:
    if not ENTRY_STATUS_PATH.exists():
        raise RuntimeError("BLOCKED_NEEDS_ENTRY_STATUS_ARTIFACT")
    rows = read_csv(ENTRY_STATUS_PATH)
    required = {
        "player_name",
        "position",
        "rookie_class_year",
        "draft_year",
        "draft_round",
        "overall_pick",
        "drafted_team",
        "entry_status",
        "review_only",
        "model_use_allowed",
        "training_allowed",
    }
    if not rows or not required.issubset(rows[0]):
        raise RuntimeError("BLOCKED_NEEDS_ENTRY_STATUS_ARTIFACT")
    if "drafted" not in {row["entry_status"] for row in rows}:
        raise RuntimeError("BLOCKED_NEEDS_ENTRY_STATUS_ARTIFACT")
    if any(row["model_use_allowed"] != "false" for row in rows):
        raise RuntimeError("Entry-status artifact contains model-use rows.")
    if any(row["training_allowed"] != "false" for row in rows):
        raise RuntimeError("Entry-status artifact contains training-use rows.")
    return rows


def load_label_rows() -> list[dict[str, str]]:
    if not LABEL_PATH.exists():
        raise RuntimeError("BLOCKED_NEEDS_OUTCOME_LABELS")
    rows = read_csv(LABEL_PATH)
    required = {
        "player_name",
        "position",
        "draft_year",
        "rookie_class_year",
        "rookie_year_position_finish",
        "year_2_position_finish",
        "first_3y_window_complete",
        "first_5y_window_complete",
        "censoring_status",
        "review_only",
        "model_use_allowed",
        "training_allowed",
    }
    if not rows or not required.issubset(rows[0]):
        raise RuntimeError("BLOCKED_NEEDS_OUTCOME_LABELS")
    if any(row["model_use_allowed"] != "false" for row in rows):
        raise RuntimeError("Outcome label artifact contains model-use rows.")
    if any(row["training_allowed"] != "false" for row in rows):
        raise RuntimeError("Outcome label artifact contains training-use rows.")
    return rows


def build_label_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        for column in ("player_stats_id", "gsis_id", "nfl_player_id"):
            value = clean(row.get(column))
            if value != NOT_ENOUGH:
                index.setdefault(value, row)
    return index


def build_audit_row(
    entry: dict[str, str],
    label_index: dict[str, dict[str, str]],
) -> dict[str, str]:
    label = find_label(entry, label_index)
    if not label:
        return {
            "player_name": clean(entry["player_name"]),
            "position": clean(entry["position"]),
            "rookie_class_year": clean(entry["rookie_class_year"]),
            "draft_year": clean(entry["draft_year"]),
            "draft_round": clean(entry["draft_round"]),
            "overall_pick": clean(entry["overall_pick"]),
            "drafted_team": clean(entry["drafted_team"]),
            "entry_status": "drafted",
            "has_rookie_year_label": "false",
            "has_2y_label": "false",
            "has_3y_label": "false",
            "has_5y_label": "false",
            "outcome_window_status": "missing_outcome_label",
            "censoring_status": NOT_ENOUGH,
            "blocker_reason": missing_label_reason(entry),
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
        }

    has_rookie = has_year_label(label, "rookie_year")
    has_2y = has_year_label(label, "year_2")
    has_3y = label.get("first_3y_window_complete") == "true" and has_window_label(
        label,
        "first_3y",
    )
    has_5y = label.get("first_5y_window_complete") == "true" and has_window_label(
        label,
        "first_5y",
    )
    return {
        "player_name": clean(entry["player_name"]),
        "position": clean(entry["position"]),
        "rookie_class_year": clean(entry["rookie_class_year"]),
        "draft_year": clean(entry["draft_year"]),
        "draft_round": clean(entry["draft_round"]),
        "overall_pick": clean(entry["overall_pick"]),
        "drafted_team": clean(entry["drafted_team"]),
        "entry_status": "drafted",
        "has_rookie_year_label": bool_text(has_rookie),
        "has_2y_label": bool_text(has_2y),
        "has_3y_label": bool_text(has_3y),
        "has_5y_label": bool_text(has_5y),
        "outcome_window_status": outcome_window_status(has_rookie, has_2y, has_3y, has_5y),
        "censoring_status": clean(label["censoring_status"]),
        "blocker_reason": blocker_reason(label, has_rookie, has_2y, has_3y, has_5y),
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


def find_label(
    entry: dict[str, str],
    label_index: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    for column in ("player_stats_id", "gsis_id", "nfl_player_id"):
        value = clean(entry.get(column))
        if value != NOT_ENOUGH and value in label_index:
            return label_index[value]
    return None


def has_year_label(label: dict[str, str], prefix: str) -> bool:
    return any(
        label.get(f"{prefix}_{threshold}_hit") in {"hit", "miss"}
        for threshold in thresholds(label)
    )


def has_window_label(label: dict[str, str], prefix: str) -> bool:
    return any(
        label.get(f"{prefix}_{threshold}_hit") in {"hit", "miss"}
        for threshold in thresholds(label)
    )


def thresholds(label: dict[str, str]) -> tuple[str, ...]:
    return THRESHOLD_MAP.get(label["position"], ())


def outcome_window_status(has_rookie: bool, has_2y: bool, has_3y: bool, has_5y: bool) -> str:
    if has_rookie and has_2y and has_3y and has_5y:
        return "complete_5y_review_only_labels"
    if has_rookie or has_2y or has_3y or has_5y:
        return "partial_or_censored_review_only_labels"
    return "missing_outcome_label"


def blocker_reason(
    label: dict[str, str],
    has_rookie: bool,
    has_2y: bool,
    has_3y: bool,
    has_5y: bool,
) -> str:
    if has_rookie and has_2y and has_3y and has_5y:
        return "NO_BLOCKER_DRAFTED_REVIEW_ONLY"
    blockers = []
    if not has_rookie:
        blockers.append("missing_rookie_year_label")
    if not has_2y:
        blockers.append("missing_2y_label")
    if not has_3y:
        blockers.append("missing_or_incomplete_3y_window")
    if not has_5y:
        blockers.append("missing_or_incomplete_5y_window")
    if label.get("censoring_status") == "right_censored":
        blockers.append("right_censored")
    return "|".join(blockers)


def missing_label_reason(entry: dict[str, str]) -> str:
    year = clean(entry["draft_year"])
    if year.isdigit() and int(year) < 2012:
        return "outside_available_outcome_label_years_2012_2024"
    return "missing_outcome_label_linkage"


def build_coverage_rows(audit_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in audit_rows:
        grouped[(row["draft_year"], row["position"])].append(row)

    output = []
    for (draft_year, position), rows in sorted(
        grouped.items(),
        key=lambda item: (int_or_large(item[0][0]), item[0][1]),
    ):
        incomplete_count = sum(
            row["outcome_window_status"] != "complete_5y_review_only_labels"
            for row in rows
        )
        missing_count = sum(row["outcome_window_status"] == "missing_outcome_label" for row in rows)
        output.append(
            {
                "draft_year": draft_year,
                "position": position,
                "drafted_count": str(len(rows)),
                "rookie_year_label_count": str(count_flag(rows, "has_rookie_year_label")),
                "2y_label_count": str(count_flag(rows, "has_2y_label")),
                "3y_label_count": str(count_flag(rows, "has_3y_label")),
                "5y_label_count": str(count_flag(rows, "has_5y_label")),
                "missing_label_count": str(missing_count),
                "incomplete_window_count": str(incomplete_count),
                "notes": coverage_notes(draft_year, rows),
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def coverage_notes(draft_year: str, rows: list[dict[str, str]]) -> str:
    if draft_year.isdigit() and int(draft_year) < 2012:
        return "No Outcome V2 label file coverage before 2012."
    if any(row["censoring_status"] == "right_censored" for row in rows):
        return "Contains right-censored windows; incomplete windows are not misses."
    if any(row["outcome_window_status"] != "complete_5y_review_only_labels" for row in rows):
        return "Contains partial/missing drafted-player review labels."
    return "Drafted-player review-only labels complete for 5Y window."


def write_docs(
    root: Path,
    entry_counts: Counter[str],
    audit_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
) -> None:
    drafted_count = len(audit_rows)
    matched_count = count_any_label(audit_rows)
    rookie_count = count_flag(audit_rows, "has_rookie_year_label")
    year2_count = count_flag(audit_rows, "has_2y_label")
    three_count = count_flag(audit_rows, "has_3y_label")
    five_count = count_flag(audit_rows, "has_5y_label")
    complete_count = count_status(audit_rows, "complete_5y_review_only_labels")
    partial_count = count_status(audit_rows, "partial_or_censored_review_only_labels")
    missing_count = count_status(audit_rows, "missing_outcome_label")

    write_doc(
        root / "artifact_manifest.md",
        [
            "# Drafted-Only Rookie Outcome Review V1",
            "",
            "## Verdict",
            "",
            "`YELLOW_DRAFTED_ONLY_REVIEW_READY`",
            "",
            "## Inputs Used",
            "",
            f"- Entry-status hygiene CSV: `{relative(ENTRY_STATUS_PATH)}`",
            "- Historical Outcome V2 label CSV: "
            "`C:/NWR_SHARED_DATA/rookie_outcomes/historical_labels_v1/"
            "rookie_historical_outcome_labels_v1.csv`",
            "",
            "## Outputs Created",
            "",
            "- `drafted_only_outcome_coverage.csv`",
            "- `drafted_only_outcome_player_audit.csv`",
            "- `outcome_window_censoring_policy.md`",
            "- `drafted_only_baseline_plan.md`",
            "- `udfa_blocker_report.md`",
            "- `gate_f_gate_g_status.md`",
            "- `merge_safety_report.md`",
            "",
            "## Source Policy",
            "",
            "The entry-status packet is YELLOW and review-only. The Outcome V2 labels are",
            "review-only exact verified first-down labels. This packet consumes them only",
            "for coverage review and does not approve model input, training, tuning, scoring,",
            "app wiring, or source-truth promotion.",
            "",
            "## Blocked Populations",
            "",
            f"- Confirmed UDFA rows: {entry_counts['confirmed_udfa']}",
            f"- Likely UDFA needs review rows: {entry_counts['likely_udfa_needs_review']}",
            f"- Wrong universe rows: {entry_counts['wrong_universe']}",
            f"- Name collision rows: {entry_counts['name_collision']}",
            "",
            "This packet approves drafted-player-only review. UDFA modeling remains blocked.",
        ],
    )
    write_doc(
        root / "outcome_window_censoring_policy.md",
        [
            "# Outcome Window Censoring Policy",
            "",
            "- Rookie-year labels cover the player's draft/rookie class season only.",
            "- 2Y labels cover rookie year plus one NFL season.",
            "- 3Y labels require the rookie season through rookie year plus two seasons.",
            "- 5Y labels require the rookie season through rookie year plus four seasons.",
            "- Incomplete or future windows are right-censored and are not failures.",
            "- Missing labels stay `Not enough information`, never `0%`.",
            "",
            "Outcome V2 label coverage used here spans 2012-2024, so drafted-player rows",
            "before 2012 are outside available label coverage in this packet. Recent classes",
            "can have incomplete 3Y/5Y windows because the seasons have not happened yet.",
            "",
            "Future NFL production after the prediction window cannot be used as an input",
            "feature because it would leak the target. Current rookies and prospects are",
            "not historical training rows; they can only receive review-only status/coverage",
            "language until a later explicit release gate approves app-facing display.",
        ],
    )
    write_doc(
        root / "drafted_only_baseline_plan.md",
        [
            "# Drafted-Only Baseline Plan",
            "",
            "This is a future plan only. No model was trained or tuned in this lane.",
            "",
            "Allowed future post-draft factual features for a drafted-only baseline:",
            "- position",
            "- draft_year / rookie_class_year",
            "- draft_round",
            "- overall_pick",
            "- drafted_team as context only unless a later policy approves modeling use",
            "",
            "Blocked leakage fields:",
            "- future NFL production",
            "- Outcome V2 labels as input features",
            "- market/ADP/DynastyProcess",
            "- projections, grades, vendor text, Gmail/news, injuries as projection inputs",
            "- CFBD production unless a later gate explicitly approves it",
            "",
            "Needed labels are rookie-year, 2Y, first-3Y, and first-5Y threshold hits by",
            "position. A future baseline should use class-year holdout splits, report Brier",
            "score, log loss, calibration buckets, and sample sizes by position/target. It",
            "must define minimum sample sizes before any tuning. These drafted-only results",
            "do not apply to UDFAs because their entry path and missingness are different.",
        ],
    )
    write_doc(
        root / "udfa_blocker_report.md",
        [
            "# UDFA Blocker Report",
            "",
            f"- Confirmed UDFA count from hygiene artifact: {entry_counts['confirmed_udfa']}",
            f"- Likely UDFA / needs-review count: {entry_counts['likely_udfa_needs_review']}",
            f"- Unknown count: {entry_counts['unknown']}",
            f"- Wrong universe count: {entry_counts['wrong_universe']}",
            f"- Name collision count: {entry_counts['name_collision']}",
            "",
            "UDFA modeling remains blocked because the hygiene artifact does not source-approve",
            "confirmed UDFA entry status. Absence from draft-pick data can be useful review",
            "evidence, but it is not enough by itself to create training truth.",
            "",
            "To unblock confirmed UDFA modeling, the project needs source-policy-approved",
            "rookie entry evidence that proves valid current/historical rookie universe",
            "membership and undrafted/free-agent entry status. Drafted-only results cannot",
            "be generalized to UDFAs because UDFAs have different opportunity, roster, and",
            "selection mechanisms. Fake round 8 is not allowed; missing draft capital is not",
            "a clean UDFA label.",
        ],
    )
    write_doc(
        root / "gate_f_gate_g_status.md",
        [
            "# Gate F / Gate G Status",
            "",
            "- Gate F may only be considered for review-only drafted-player coverage reporting.",
            "- Gate F cannot become model-ready from this lane.",
            "- Gate G remains blocked.",
            "- No app or Rankings wiring is approved.",
            "- No current-player rookie outcome columns are approved.",
            "- No model tuning, scoring, training, or release was performed.",
        ],
    )
    write_doc(
        root / "merge_safety_report.md",
        [
            "# Merge Safety Report",
            "",
            "- No app files changed.",
            "- No Rankings, Draft Room, Gate F, or Gate G behavior changed.",
            "- No model outputs changed.",
            "- No pinned snapshots changed.",
            "- No `latest_candidate` or `latest_approved` files changed.",
            "- No source-truth behavior changed.",
            "- No protected/raw/private paths are tracked by this lane.",
            "- No secrets are tracked.",
            "- Frozen Final Draft Board V1 remains outside this lane.",
        ],
    )
    write_doc(
        root / "README.md",
        [
            "# Rookie Outcome Drafted-Only Review V1",
            "",
            f"- Drafted QB/RB/WR/TE rows reviewed: {drafted_count}",
            f"- Rows with any Outcome V2 label linkage: {matched_count}",
            f"- Rookie-year label rows: {rookie_count}",
            f"- 2Y label rows: {year2_count}",
            f"- 3Y complete-window label rows: {three_count}",
            f"- 5Y complete-window label rows: {five_count}",
            f"- Complete 5Y drafted-only rows: {complete_count}",
            f"- Partial/censored rows: {partial_count}",
            f"- Missing label rows: {missing_count}",
            f"- Outcome label source rows read: {len(label_rows)}",
            "",
            "Review-only. No model/training/app/ranking approval.",
        ],
    )


def count_flag(rows: list[dict[str, str]], column: str) -> int:
    return sum(row[column] == "true" for row in rows)


def count_any_label(rows: list[dict[str, str]]) -> int:
    return sum(row["outcome_window_status"] != "missing_outcome_label" for row in rows)


def count_status(rows: list[dict[str, str]], status: str) -> int:
    return sum(row["outcome_window_status"] == status for row in rows)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def clean(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "<na>"}:
        return NOT_ENOUGH
    return text


def int_or_large(value: str) -> int:
    return int(value) if value.isdigit() else 9999


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
