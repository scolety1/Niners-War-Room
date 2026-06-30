from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "current_rookie_universe_udfa_policy_v1_20260630"
)
SHARED_DISPLAY_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\display_artifact_v4")

V2_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_capital_coverage_repair_v2_20260630"
)
V2_REPAIR_PATH = V2_ROOT / "rookie_draft_capital_repair_v2_matrix.csv"
V2_DIAGNOSIS_PATH = V2_ROOT / "rookie_draft_capital_missingness_diagnosis_v2.csv"
V3_DISPLAY_PATH = V2_ROOT / "rookie_display_artifact_v3_coverage_matrix.csv"
SOURCE_REGISTRY_PATH = REPO_ROOT / "config" / "source_registry.csv"

BASE_HEAD = "899e2276fc69041ef36d037cfb50c4b85e679232"
RUN_ID = "current_rookie_universe_udfa_policy_v1_20260630"
NOT_ENOUGH = "Not enough information"

UNIVERSE_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "identity_status",
    "current_rookie_universe_status",
    "universe_source",
    "universe_confidence",
    "wrong_universe_flag",
    "name_collision_flag",
    "blocker_reason",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

DIAGNOSIS_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "current_status_before",
    "draft_pick_match_status",
    "nflverse_absence_status",
    "source_completeness_status",
    "possible_name_collision",
    "possible_wrong_draft_year",
    "possible_wrong_player_match",
    "udfa_status_recommendation",
    "wrong_universe_recommendation",
    "recommended_action",
    "confidence",
    "blocker_reason",
    "review_only",
    "model_use_allowed",
    "training_allowed",
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
    "overall_pick",
    "draft_capital_bucket",
    "udffa_or_undrafted_status",
    "current_rookie_universe_status",
    "udfa_display_status",
    "wrong_universe_flag",
    "name_collision_flag",
    "identity_status",
    "draft_capital_status",
    "feature_coverage_status",
    "model_rd_status",
    "validation_status",
    "display_status",
    "data_quality_status",
    "source_provenance_status",
    "repair_action",
    "repair_confidence",
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
    SHARED_DISPLAY_ROOT.mkdir(parents=True, exist_ok=True)

    repair_rows = read_csv(V2_REPAIR_PATH)
    v2_diagnosis_rows = read_csv(V2_DIAGNOSIS_PATH)
    v3_display_rows = read_csv(V3_DISPLAY_PATH)
    source_rows = read_csv(SOURCE_REGISTRY_PATH)

    universe_rows = build_universe_rows(repair_rows)
    diagnosis_rows = build_udfa_wrong_universe_diagnosis(repair_rows)
    display_rows = build_display_v4_rows(v3_display_rows, universe_rows)
    summary_rows = build_display_summary_rows(display_rows)

    write_csv(
        args.doc_root / "current_rookie_universe_matrix_v1.csv",
        UNIVERSE_COLUMNS,
        universe_rows,
    )
    write_csv(
        args.doc_root / "udfa_wrong_universe_diagnosis_v1.csv",
        DIAGNOSIS_COLUMNS,
        diagnosis_rows,
    )
    write_csv(
        args.doc_root / "rookie_display_artifact_v4_coverage_matrix.csv",
        DISPLAY_COLUMNS,
        display_rows,
    )
    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_artifact_v4.csv",
        DISPLAY_COLUMNS,
        display_rows,
    )
    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_coverage_summary_v4.csv",
        SUMMARY_COLUMNS,
        summary_rows,
    )
    write_csv(
        SHARED_DISPLAY_ROOT / "rookie_outcome_review_only_display_manifest_v4.csv",
        SUMMARY_COLUMNS,
        shared_manifest_rows("display_artifact_v4", len(display_rows)),
    )

    write_docs(
        args.doc_root,
        repair_rows,
        v2_diagnosis_rows,
        v3_display_rows,
        source_rows,
        universe_rows,
        diagnosis_rows,
        display_rows,
    )
    print(
        {
            "final_verdict": "PARTIAL_CURRENT_ROOKIE_UNIVERSE_UDFA_POLICY_V1",
            "universe_rows": len(universe_rows),
            "confirmed_udfa_rows": count_universe(universe_rows, "confirmed_udfa"),
            "likely_udfa_review_rows": count_universe(
                universe_rows,
                "current_rookie_likely_udfa_review",
            ),
            "wrong_universe_rows": count_wrong_universe(universe_rows),
            "display_v4_valid_rows": count_display_rows(display_rows),
            "display_v4_not_enough_information_rows": count_not_enough_rows(display_rows),
            "gate_g": "BLOCKED_NEEDS_UDFA_REVIEW",
        }
    )


def build_universe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        universe_status, confidence, wrong_flag, collision_flag, blocker = classify_universe(row)
        output.append(
            {
                "player_id": clean(row["player_id"]),
                "player_name": clean(row["player_name"]),
                "position": clean(row["position"]),
                "team": clean(row["team"]),
                "rookie_class_year": clean(row["rookie_class_year"]),
                "identity_status": "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL",
                "current_rookie_universe_status": universe_status,
                "universe_source": "rookie_draft_capital_repair_v2_review_artifact",
                "universe_confidence": confidence,
                "wrong_universe_flag": wrong_flag,
                "name_collision_flag": collision_flag,
                "blocker_reason": blocker,
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def build_udfa_wrong_universe_diagnosis(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        status = clean(row["udffa_or_undrafted_status"])
        is_wrong_universe = row["draft_capital_status"] == (
            "BLOCKED_WRONG_UNIVERSE_OLDER_NFL_DRAFT_MATCH"
        )
        if status != "likely_udfa_needs_review" and not is_wrong_universe:
            continue
        if is_wrong_universe:
            output.append(wrong_universe_diagnosis_row(row))
        else:
            output.append(likely_udfa_diagnosis_row(row))
    return output


def likely_udfa_diagnosis_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "player_id": clean(row["player_id"]),
        "player_name": clean(row["player_name"]),
        "position": clean(row["position"]),
        "team": clean(row["team"]),
        "rookie_class_year": clean(row["rookie_class_year"]),
        "current_status_before": "likely_udfa_needs_review",
        "draft_pick_match_status": "no_exact_2025_2026_nflverse_draft_pick_match",
        "nflverse_absence_status": "not_found_in_complete_2025_2026_draft_picks",
        "source_completeness_status": (
            "draft_picks_complete_for_completed_drafts_but_universe_source_review_only"
        ),
        "possible_name_collision": "false",
        "possible_wrong_draft_year": "false",
        "possible_wrong_player_match": "false",
        "udfa_status_recommendation": "likely_udfa_needs_review",
        "wrong_universe_recommendation": "not_applicable",
        "recommended_action": "keep_review_needed_no_outcome_rates",
        "confidence": "MEDIUM_REVIEW_ONLY",
        "blocker_reason": (
            "Draft-pick absence plus review-only team context is not enough to "
            "confirm UDFA source truth."
        ),
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


def wrong_universe_diagnosis_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "player_id": clean(row["player_id"]),
        "player_name": clean(row["player_name"]),
        "position": clean(row["position"]),
        "team": clean(row["team"]),
        "rookie_class_year": clean(row["rookie_class_year"]),
        "current_status_before": "wrong_universe_older_nfl_draft_match",
        "draft_pick_match_status": "older_nfl_draft_match_not_current_rookie_class",
        "nflverse_absence_status": "not_current_2025_2026_draft_pick_match",
        "source_completeness_status": "nflverse_historical_draft_pick_match_found",
        "possible_name_collision": "true",
        "possible_wrong_draft_year": "true",
        "possible_wrong_player_match": "true",
        "udfa_status_recommendation": "unknown_keep_not_enough_information",
        "wrong_universe_recommendation": "wrong_universe_remove_from_rookie_artifact",
        "recommended_action": "block_from_display_and_review_universe_membership",
        "confidence": "HIGH_BLOCKER",
        "blocker_reason": clean(row["draft_capital_provenance"]),
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


def build_display_v4_rows(
    v3_display_rows: list[dict[str, str]],
    universe_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    universe_index = {
        (
            row["player_id"],
            row["player_name"],
            row["position"],
            row["team"],
        ): row
        for row in universe_rows
    }
    output = []
    for row in v3_display_rows:
        key = (row["player_id"], row["player_name"], row["position"], row["team"])
        universe = universe_index[key]
        enriched = {column: row.get(column, NOT_ENOUGH) for column in DISPLAY_COLUMNS}
        enriched["current_rookie_universe_status"] = universe[
            "current_rookie_universe_status"
        ]
        enriched["wrong_universe_flag"] = universe["wrong_universe_flag"]
        enriched["name_collision_flag"] = universe["name_collision_flag"]
        enriched["udfa_display_status"] = udfa_display_status(
            row["udffa_or_undrafted_status"],
            universe["current_rookie_universe_status"],
        )
        if universe["wrong_universe_flag"] == "true":
            block_display(enriched, "Wrong-universe/name-collision row blocked from display.")
        elif row["udffa_or_undrafted_status"] == "likely_udfa_needs_review":
            block_display(enriched, "Likely UDFA requires review; no outcome rates shown.")
        elif row["udffa_or_undrafted_status"] == "not_in_draft_picks_needs_review":
            block_display(enriched, "Unknown draft status; no outcome rates shown.")
        output.append(enriched)
    return output


def block_display(row: dict[str, str], note: str) -> None:
    for column in DISPLAY_COLUMNS:
        if column.endswith("_review_display_rate"):
            row[column] = NOT_ENOUGH
    row["display_field_count"] = "0"
    row["not_enough_information_field_count"] = "12"
    row["rate_method_summary"] = NOT_ENOUGH
    row["display_status"] = NOT_ENOUGH
    row["validation_status"] = NOT_ENOUGH
    row["feature_coverage_status"] = NOT_ENOUGH
    row["notes"] = note


def classify_universe(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    status = row["draft_capital_status"]
    udfa_status = row["udffa_or_undrafted_status"]
    if status == "REPAIRED_NFLVERSE_DRAFT_CAPITAL_AVAILABLE":
        return (
            "drafted_with_valid_draft_capital",
            "HIGH_REVIEW_ONLY",
            "false",
            "false",
            NOT_ENOUGH,
        )
    if status == "BLOCKED_WRONG_UNIVERSE_OLDER_NFL_DRAFT_MATCH":
        return (
            "wrong_universe_name_collision",
            "HIGH_BLOCKER",
            "true",
            "true",
            clean(row["draft_capital_provenance"]),
        )
    if udfa_status == "likely_udfa_needs_review":
        return (
            "current_rookie_likely_udfa_review",
            "MEDIUM_REVIEW_ONLY",
            "false",
            "false",
            "Not found in 2025/2026 nflverse draft picks; UDFA not confirmed.",
        )
    return (
        "current_rookie_unknown_needs_human_review",
        "LOW_REVIEW_ONLY",
        "false",
        "false",
        "No draft pick and no sufficient source-safe UDFA confirmation.",
    )


def udfa_display_status(udfa_status: str, universe_status: str) -> str:
    if universe_status == "wrong_universe_name_collision":
        return "wrong_universe_blocked"
    if udfa_status == "not_udfa_drafted":
        return "drafted_verified"
    if udfa_status == "confirmed_udfa":
        return "confirmed_udfa_display_status_only"
    if udfa_status == "likely_udfa_needs_review":
        return "likely_udfa_review_needed"
    if udfa_status == "not_in_draft_picks_needs_review":
        return "not_in_draft_picks_needs_review"
    return "unknown_keep_not_enough_information"


def write_docs(
    root: Path,
    repair_rows: list[dict[str, str]],
    v2_diagnosis_rows: list[dict[str, str]],
    v3_display_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    universe_rows: list[dict[str, str]],
    diagnosis_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
) -> None:
    source_keys = {
        (row["source_name"], row["source_table"]): row["default_admissibility"]
        for row in source_rows
    }
    universe_counts = Counter(row["current_rookie_universe_status"] for row in universe_rows)
    diagnosis_counts = Counter(row["udfa_status_recommendation"] for row in diagnosis_rows)
    write_doc(
        root / "00_INVENTORY.md",
        [
            "# Current Rookie Universe + UDFA Policy Inventory - 2026-06-30",
            "",
            f"- Actual base HEAD: `{BASE_HEAD}`",
            f"- Current 157 rookie universe source rows: {len(repair_rows)}",
            f"- Gate F V3 display rows: {len(v3_display_rows)}",
            f"- Draft-capital coverage repair V2 diagnosis rows: {len(v2_diagnosis_rows)}",
            (
                "- Likely UDFA / undrafted review rows: "
                f"{count_udfa(repair_rows, 'likely_udfa_needs_review')}"
            ),
            f"- Wrong-universe older draft matches: {count_wrong_repair_rows(repair_rows)}",
            f"- Remaining blocked/human-review rows: {count_not_enough_rows(v3_display_rows)}",
            (
                "- Source registry: nflverse draft_picks="
                f"{source_keys.get(('nflverse', 'draft_picks'), 'missing')}; "
                "nflverse rosters/players are not explicit draft-capital/UDFA proof here; "
                f"sleeper players={source_keys.get(('sleeper', 'players'), 'missing')}."
            ),
            (
                "- JackLich, array-carpenter, grades/profile text, FootballDB, market, "
                "vendor, and Gmail remain blocked."
            ),
            "",
            "Inventory is complete; no app/rank/model files are touched.",
        ],
    )
    write_doc(
        root / "01_CURRENT_ROOKIE_UNIVERSE_DEFINITION.md",
        [
            "# Gate 1 Current Rookie Universe Definition - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_CURRENT_ROOKIE_UNIVERSE_DEFINED`",
            "",
            "A row belongs to this review universe only if it appears in the approved",
            "rookie review artifact lineage and keeps review-only flags closed.",
            "Drafted rows require admitted nflverse draft-pick evidence. UDFA rows",
            "remain review-needed unless a source proves both current-rookie membership",
            "and undrafted status. Wrong-universe/name-collision rows are blocked.",
            "",
            (
                "- Drafted with valid draft capital: "
                f"{universe_counts['drafted_with_valid_draft_capital']}"
            ),
            f"- Likely UDFA review rows: {universe_counts['current_rookie_likely_udfa_review']}",
            (
                "- Wrong-universe/name-collision rows: "
                f"{universe_counts['wrong_universe_name_collision']}"
            ),
            (
                "- Unknown / needs human review rows: "
                f"{universe_counts['current_rookie_unknown_needs_human_review']}"
            ),
        ],
    )
    write_doc(
        root / "02_UDFA_SOURCE_POLICY_GATE.md",
        [
            "# Gate 2 UDFA Source-Policy Gate - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_UDFA_SOURCE_POLICY`",
            "",
            "Admitted nflverse draft picks can prove a player was not found in the",
            "completed 2025/2026 draft-pick set used by V2. That absence alone does",
            "not prove confirmed UDFA source truth. Existing NWR/Sleeper/CFBD review",
            "context can keep likely UDFA rows in review, but cannot promote them.",
            "",
            "- Confirmed UDFA rows allowed by this policy: 0",
            "- Likely UDFA rows remain review-needed.",
            "- Unknown rows remain `Not enough information`.",
        ],
    )
    write_doc(
        root / "03_UDFA_AND_WRONG_UNIVERSE_DIAGNOSIS.md",
        [
            "# Gate 3 UDFA And Wrong-Universe Diagnosis - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_UDFA_WRONG_UNIVERSE_DIAGNOSIS`",
            "",
            f"- Rows diagnosed: {len(diagnosis_rows)}",
            f"- Likely UDFA recommendations: {diagnosis_counts['likely_udfa_needs_review']}",
            (
                "- Wrong-universe remove recommendations: "
                f"{count_wrong_diagnosis_rows(diagnosis_rows)}"
            ),
            "- No row is promoted to confirmed UDFA.",
            "- Wrong-universe rows are blocked from display and require human cleanup.",
        ],
    )
    write_doc(
        root / "04_UDFA_BUCKET_DISPLAY_POLICY.md",
        [
            "# Gate 4 UDFA Bucket Display Policy - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_UDFA_BUCKET_DISPLAY_POLICY`",
            "",
            "- Drafted rounds 1-7 use normal draft-capital buckets.",
            "- UDFA/undrafted is separate and never fake round 8.",
            "- `confirmed_udfa` can display only if a future source-policy gate confirms it.",
            "- `likely_udfa_needs_review` is status/context only, not a model feature.",
            "- Unknown remains `Not enough information`.",
            "- Wrong-universe rows receive no rookie outcome display values.",
        ],
    )
    write_doc(
        root / "05_GATE_G_RELEASE_AUDIT_AFTER_UDFA_REPAIR.md",
        [
            "# Gate 6 Gate G Release Audit After UDFA Repair - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`BLOCKED_NEEDS_UDFA_REVIEW`",
            "",
            "- Gate F V4 remains partial.",
            "- UDFA status is mostly unconfirmed.",
            "- Rankings wiring approval was not granted.",
            "- No app code was touched.",
            "- Gate G should not run next.",
        ],
    )
    write_doc(
        root / "06_GATE_F_V4_DISPLAY_REBUILD_RESULT.md",
        [
            "# Gate 5 Gate F V4 Display Artifact Rebuild - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_DISPLAY_ARTIFACT_V4_UNIVERSE_UDFA_REPAIR`",
            "",
            "- Previous valid display rows: 117",
            "- Previous `Not enough information` rows: 40",
            "- Previous likely UDFA rows: 28",
            f"- New valid display rows: {count_display_rows(display_rows)}",
            f"- New `Not enough information` rows: {count_not_enough_rows(display_rows)}",
            f"- Confirmed UDFA rows: {count_universe(universe_rows, 'confirmed_udfa')}",
            (
                "- Likely UDFA review rows: "
                f"{count_universe(universe_rows, 'current_rookie_likely_udfa_review')}"
            ),
            f"- Wrong-universe rows cleaned/blocked: {count_wrong_universe(universe_rows)}",
            f"- Rows still blocked/human-review: {count_not_enough_rows(display_rows)}",
            (
                "- Shared V4 display outputs were written outside git under "
                "`C:\\NWR_SHARED_DATA\\rookie_outcomes\\display_artifact_v4\\`."
            ),
        ],
    )
    write_doc(
        root / "README.md",
        [
            "# Current Rookie Universe + UDFA Source Policy V1",
            "",
            "This package defines the review-only current rookie universe and UDFA",
            "policy after draft-capital repair V2. It does not confirm UDFA without",
            "source-proof, create probabilities, wire Rankings, promote source truth,",
            "or use blocked sources.",
        ],
    )


def build_display_summary_rows(display_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    values = {
        "gate_f_v4_verdict": (
            "PARTIAL_DISPLAY_ARTIFACT_V4_UNIVERSE_UDFA_REPAIR",
            "Universe/UDFA status clarified but coverage remains partial.",
        ),
        "previous_valid_display_rows": ("117", "Gate F V3 valid display rows."),
        "new_valid_display_rows": (str(count_display_rows(display_rows)), "Gate F V4."),
        "previous_not_enough_information_rows": ("40", "Gate F V3 NEI rows."),
        "new_not_enough_information_rows": (
            str(count_not_enough_rows(display_rows)),
            "Gate F V4 NEI rows.",
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


def count_display_rows(rows: list[dict[str, str]]) -> int:
    return sum(int(row["display_field_count"]) > 0 for row in rows)


def count_not_enough_rows(rows: list[dict[str, str]]) -> int:
    return sum(row["display_status"] == NOT_ENOUGH for row in rows)


def count_udfa(rows: list[dict[str, str]], status: str) -> int:
    return sum(row["udffa_or_undrafted_status"] == status for row in rows)


def count_universe(rows: list[dict[str, str]], status: str) -> int:
    return sum(row["current_rookie_universe_status"] == status for row in rows)


def count_wrong_universe(rows: list[dict[str, str]]) -> int:
    return sum(row["wrong_universe_flag"] == "true" for row in rows)


def count_wrong_repair_rows(rows: list[dict[str, str]]) -> int:
    return sum(
        row["draft_capital_status"] == "BLOCKED_WRONG_UNIVERSE_OLDER_NFL_DRAFT_MATCH"
        for row in rows
    )


def count_wrong_diagnosis_rows(rows: list[dict[str, str]]) -> int:
    return sum(
        row["wrong_universe_recommendation"]
        == "wrong_universe_remove_from_rookie_artifact"
        for row in rows
    )


def clean(value: object) -> str:
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "<na>"} or not text:
        return NOT_ENOUGH
    return text


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
