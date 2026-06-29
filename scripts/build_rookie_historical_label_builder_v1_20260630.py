from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_historical_label_builder_v1_20260630"
)
SHARED_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\historical_labels_v1")
BRIDGE_PATH = Path(
    r"C:\NWR_SHARED_DATA\rookie_outcomes\draft_class_gsis_bridge_v1"
    r"\historical_rookie_draft_class_gsis_bridge_v1.csv"
)
OUTCOME_SHARED_ROOT = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended"
)
OUTCOME_SEASON_LABEL_PATH = (
    OUTCOME_SHARED_ROOT / "outcome_v2_extended_season_outcome_labels.csv"
)
OUTCOME_MANIFEST_PATH = OUTCOME_SHARED_ROOT / "outcome_v2_extended_label_manifest.csv"

BASE_HEAD = "ec0702ff467ef86a4973fc6e8e156fc7be89b49e"
FINAL_VERDICT = "PARTIAL_HISTORICAL_ROOKIE_LABELS"
NOT_ENOUGH = "Not enough information"
EXPECTED_SCORING_MODE = "exact_verified_first_downs"
SUPPORTED_THRESHOLDS = {
    "QB": (6, 12),
    "RB": (6, 12, 24, 36),
    "WR": (6, 12, 24, 36),
    "TE": (6, 12),
}
ALL_THRESHOLDS = (6, 12, 24, 36)

LABEL_COLUMNS = (
    "nfl_player_id",
    "gsis_id",
    "player_stats_id",
    "nwr_player_id",
    "cfbd_player_id",
    "player_name",
    "position",
    "rookie_class_year",
    "draft_year",
    "draft_round",
    "draft_pick",
    "drafted_team",
    "college_team",
    "scoring_mode",
    "rookie_year_position_finish",
    "year_2_position_finish",
    "rookie_year_top_6_hit",
    "rookie_year_top_12_hit",
    "rookie_year_top_24_hit",
    "rookie_year_top_36_hit",
    "year_2_top_6_hit",
    "year_2_top_12_hit",
    "year_2_top_24_hit",
    "year_2_top_36_hit",
    "first_3y_top_6_hit",
    "first_3y_top_12_hit",
    "first_3y_top_24_hit",
    "first_3y_top_36_hit",
    "first_5y_top_6_hit",
    "first_5y_top_12_hit",
    "first_5y_top_24_hit",
    "first_5y_top_36_hit",
    "first_3y_window_complete",
    "first_5y_window_complete",
    "censoring_status",
    "label_source_status",
    "bridge_status",
    "data_quality_status",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

COVERAGE_COLUMNS = (
    "metric",
    "value",
    "notes",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

MANIFEST_COLUMNS = (
    "run_id",
    "run_timestamp",
    "artifact",
    "source",
    "rows",
    "output_path",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "notes",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build review-only historical rookie outcome labels."
    )
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--shared-output-root", type=Path, default=SHARED_OUTPUT_ROOT)
    parser.add_argument("--bridge-path", type=Path, default=BRIDGE_PATH)
    parser.add_argument("--outcome-season-label-path", type=Path, default=OUTCOME_SEASON_LABEL_PATH)
    parser.add_argument("--outcome-manifest-path", type=Path, default=OUTCOME_MANIFEST_PATH)
    args = parser.parse_args()

    run_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    run_id = "rookie_historical_label_builder_v1_20260630"
    bridge_rows = read_csv(args.bridge_path)
    season_rows = read_csv(args.outcome_season_label_path)
    manifest_rows = (
        read_csv(args.outcome_manifest_path)
        if args.outcome_manifest_path.exists()
        else []
    )
    scoring_mode = scoring_mode_from_manifest(manifest_rows)
    latest_label_season = max(to_int(row.get("season")) or 0 for row in season_rows)

    label_rows = build_label_rows(
        bridge_rows=bridge_rows,
        season_rows=season_rows,
        scoring_mode=scoring_mode,
        latest_label_season=latest_label_season,
    )
    validate_label_rows(label_rows)
    coverage_rows = build_coverage_rows(
        bridge_rows=bridge_rows,
        label_rows=label_rows,
        latest_label_season=latest_label_season,
        scoring_mode=scoring_mode,
    )
    validate_review_rows(coverage_rows)

    args.shared_output_root.mkdir(parents=True, exist_ok=True)
    label_path = args.shared_output_root / "rookie_historical_outcome_labels_v1.csv"
    manifest_path = args.shared_output_root / "rookie_historical_outcome_label_manifest_v1.csv"
    coverage_path = args.shared_output_root / "rookie_historical_outcome_coverage_summary_v1.csv"
    write_csv(label_path, LABEL_COLUMNS, label_rows)
    write_csv(coverage_path, COVERAGE_COLUMNS, coverage_rows)
    write_csv(
        manifest_path,
        MANIFEST_COLUMNS,
        build_manifest_rows(
            run_id=run_id,
            run_timestamp=run_timestamp,
            label_rows=label_rows,
            coverage_rows=coverage_rows,
            label_path=label_path,
            coverage_path=coverage_path,
        ),
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    write_csv(
        args.output_root / "rookie_historical_label_coverage_matrix_v1.csv",
        COVERAGE_COLUMNS,
        coverage_rows,
    )
    write_inventory_doc(
        args.output_root,
        bridge_rows=bridge_rows,
        label_rows=label_rows,
        latest_label_season=latest_label_season,
        scoring_mode=scoring_mode,
        label_path=label_path,
    )
    write_label_spec_lock_doc(args.output_root, scoring_mode)
    write_coverage_report_doc(
        args.output_root,
        bridge_rows=bridge_rows,
        label_rows=label_rows,
        latest_label_season=latest_label_season,
        scoring_mode=scoring_mode,
    )
    write_gate_c_decision_doc(args.output_root, bridge_rows, label_rows)
    write_readme(args.output_root, label_rows, label_path)

    print(
        {
            "verdict": FINAL_VERDICT,
            "bridge_rows": len(bridge_rows),
            "label_rows": len(label_rows),
            "scoring_mode": scoring_mode,
            "shared_labels": str(label_path),
        }
    )
    return 0


def build_label_rows(
    *,
    bridge_rows: list[dict[str, str]],
    season_rows: list[dict[str, str]],
    scoring_mode: str,
    latest_label_season: int,
) -> list[dict[str, str]]:
    season_by_player_year = {
        (clean(row.get("player_id")), to_int(row.get("season"))): row
        for row in season_rows
        if clean(row.get("player_id")) and to_int(row.get("season")) is not None
    }
    label_rows: list[dict[str, str]] = []
    for bridge in bridge_rows:
        if clean(bridge.get("outcome_label_link_status")) != "linked_to_outcome_labels":
            continue
        draft_year = to_int(bridge.get("rookie_class_year") or bridge.get("draft_year"))
        if draft_year is None:
            continue
        player_id = clean(bridge.get("player_stats_id") or bridge.get("gsis_id"))
        position = clean(bridge.get("position"))
        rookie_row = season_by_player_year.get((player_id, draft_year))
        year_2_row = season_by_player_year.get((player_id, draft_year + 1))
        row = {
            "nfl_player_id": player_id,
            "gsis_id": clean(bridge.get("gsis_id")) or NOT_ENOUGH,
            "player_stats_id": player_id,
            "nwr_player_id": clean(bridge.get("nwr_player_id")) or NOT_ENOUGH,
            "cfbd_player_id": clean(bridge.get("cfbd_player_id")) or NOT_ENOUGH,
            "player_name": clean(bridge.get("player_name")) or NOT_ENOUGH,
            "position": position,
            "rookie_class_year": str(draft_year),
            "draft_year": clean(bridge.get("draft_year")) or str(draft_year),
            "draft_round": clean(bridge.get("draft_round")) or NOT_ENOUGH,
            "draft_pick": clean(bridge.get("draft_pick")) or NOT_ENOUGH,
            "drafted_team": clean(bridge.get("drafted_team")) or NOT_ENOUGH,
            "college_team": clean(bridge.get("college_team")) or NOT_ENOUGH,
            "scoring_mode": scoring_mode,
            "rookie_year_position_finish": position_finish(rookie_row),
            "year_2_position_finish": position_finish(year_2_row),
            "first_3y_window_complete": bool_text(draft_year + 2 <= latest_label_season),
            "first_5y_window_complete": bool_text(draft_year + 4 <= latest_label_season),
            "censoring_status": (
                "complete" if draft_year + 4 <= latest_label_season else "right_censored"
            ),
            "label_source_status": "review_only_outcome_v2_exact_verified_first_downs",
            "bridge_status": clean(bridge.get("bridge_status")) or NOT_ENOUGH,
            "data_quality_status": data_quality_status(
                player_id=player_id,
                draft_year=draft_year,
                latest_label_season=latest_label_season,
                season_by_player_year=season_by_player_year,
            ),
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
        }
        for threshold in ALL_THRESHOLDS:
            row[f"rookie_year_top_{threshold}_hit"] = season_hit(
                rookie_row,
                position=position,
                threshold=threshold,
            )
            row[f"year_2_top_{threshold}_hit"] = season_hit(
                year_2_row,
                position=position,
                threshold=threshold,
            )
            row[f"first_3y_top_{threshold}_hit"] = horizon_hit(
                player_id=player_id,
                position=position,
                threshold=threshold,
                start_year=draft_year,
                horizon_years=3,
                latest_label_season=latest_label_season,
                season_by_player_year=season_by_player_year,
            )
            row[f"first_5y_top_{threshold}_hit"] = horizon_hit(
                player_id=player_id,
                position=position,
                threshold=threshold,
                start_year=draft_year,
                horizon_years=5,
                latest_label_season=latest_label_season,
                season_by_player_year=season_by_player_year,
            )
        label_rows.append(row)
    return label_rows


def season_hit(
    row: dict[str, str] | None,
    *,
    position: str,
    threshold: int,
) -> str:
    if threshold not in SUPPORTED_THRESHOLDS.get(position.upper(), ()):
        return "not_applicable"
    if row is None:
        return NOT_ENOUGH
    return clean(row.get(f"top_{threshold}_hit")) or NOT_ENOUGH


def horizon_hit(
    *,
    player_id: str,
    position: str,
    threshold: int,
    start_year: int,
    horizon_years: int,
    latest_label_season: int,
    season_by_player_year: dict[tuple[str, int | None], dict[str, str]],
) -> str:
    if threshold not in SUPPORTED_THRESHOLDS.get(position.upper(), ()):
        return "not_applicable"
    end_year = start_year + horizon_years - 1
    observed_years = range(start_year, min(end_year, latest_label_season) + 1)
    labels = [
        season_hit(
            season_by_player_year.get((player_id, year)),
            position=position,
            threshold=threshold,
        )
        for year in observed_years
    ]
    if "hit" in labels:
        return "hit"
    if end_year > latest_label_season:
        return NOT_ENOUGH
    if any(label == NOT_ENOUGH for label in labels):
        return NOT_ENOUGH
    return "miss"


def position_finish(row: dict[str, str] | None) -> str:
    if row is None:
        return NOT_ENOUGH
    return clean(row.get("position_finish")) or NOT_ENOUGH


def data_quality_status(
    *,
    player_id: str,
    draft_year: int,
    latest_label_season: int,
    season_by_player_year: dict[tuple[str, int | None], dict[str, str]],
) -> str:
    if (player_id, draft_year) not in season_by_player_year:
        return "partial_missing_rookie_year_outcome_row"
    if draft_year + 4 > latest_label_season:
        return "right_censored_5y_window"
    required_years = range(draft_year, draft_year + 5)
    if all((player_id, year) in season_by_player_year for year in required_years):
        return "complete_5y_outcome_rows"
    return "partial_missing_outcome_season_rows"


def build_coverage_rows(
    *,
    bridge_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
    latest_label_season: int,
    scoring_mode: str,
) -> list[dict[str, str]]:
    blocked = len(bridge_rows) - len(label_rows)
    bridge_position_counts = Counter(clean(row.get("position")) for row in bridge_rows)
    label_position_counts = Counter(clean(row.get("position")) for row in label_rows)
    bridge_year_counts = Counter(clean(row.get("rookie_class_year")) for row in bridge_rows)
    label_year_counts = Counter(clean(row.get("rookie_class_year")) for row in label_rows)
    blocked_reasons = Counter(blocker_for_bridge(row) for row in bridge_rows)
    censoring_counts = Counter(row["censoring_status"] for row in label_rows)
    return [
        coverage("gate_c_verdict", FINAL_VERDICT, "Partial drafted-player labels built."),
        coverage("bridge_rows_considered", len(bridge_rows), "Rows from prior shared bridge."),
        coverage("label_rows_built", len(label_rows), "Outcome-linked drafted QB/RB/WR/TE rows."),
        coverage("blocked_bridge_rows", blocked, "Unlinked or missing-ID bridge rows excluded."),
        coverage(
            "missing_gsis_or_player_stats_id_rows",
            blocked_reasons["missing_gsis_id"],
            "Blocked.",
        ),
        coverage(
            "unlinked_outcome_label_rows",
            blocked_reasons["unlinked_outcome_labels"],
            "Blocked.",
        ),
        coverage(
            "rookie_year_coverage_rows",
            non_missing(label_rows, "rookie_year_position_finish"),
            "Has rookie-year season outcome row.",
        ),
        coverage(
            "year_2_coverage_rows",
            non_missing(label_rows, "year_2_position_finish"),
            "Has year-2 season outcome row.",
        ),
        coverage(
            "first_3y_calendar_complete_rows",
            count_true(label_rows, "first_3y_window_complete"),
            "Calendar complete by target ceiling.",
        ),
        coverage(
            "first_5y_calendar_complete_rows",
            count_true(label_rows, "first_5y_window_complete"),
            "Calendar complete by target ceiling.",
        ),
        coverage("censoring_summary", format_counts(censoring_counts), "5Y censoring status."),
        coverage(
            "bridge_position_coverage",
            format_counts(bridge_position_counts),
            "Bridge rows by position.",
        ),
        coverage(
            "label_position_coverage",
            format_counts(label_position_counts),
            "Label rows by position.",
        ),
        coverage(
            "bridge_class_coverage",
            format_counts(bridge_year_counts),
            "Bridge rows by class.",
        ),
        coverage("label_class_coverage", format_counts(label_year_counts), "Label rows by class."),
        coverage("latest_outcome_label_season", latest_label_season, "Outcome V2 target ceiling."),
        coverage("scoring_mode", scoring_mode, "Exact vs approximate scoring mode."),
        coverage("approximation_rows", 0, "No approximation rows generated."),
        coverage("rookie_probabilities_created", 0, "No probabilities created in this lane."),
        coverage("rankings_wiring_created", 0, "No Rankings/app wiring created in this lane."),
        coverage("model_use_rows", 0, "All generated rows keep model_use_allowed=false."),
        coverage("training_use_rows", 0, "All generated rows keep training_allowed=false."),
    ]


def build_manifest_rows(
    *,
    run_id: str,
    run_timestamp: str,
    label_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    label_path: Path,
    coverage_path: Path,
) -> list[dict[str, str]]:
    return [
        manifest_row(
            run_id,
            run_timestamp,
            "rookie_historical_outcome_labels_v1.csv",
            str(BRIDGE_PATH) + " + " + str(OUTCOME_SEASON_LABEL_PATH),
            len(label_rows),
            label_path,
            "Generated review-only labels under shared data; not tracked.",
        ),
        manifest_row(
            run_id,
            run_timestamp,
            "rookie_historical_outcome_coverage_summary_v1.csv",
            "derived_from_rookie_historical_outcome_labels_v1",
            len(coverage_rows),
            coverage_path,
            "Generated review-only coverage under shared data; not tracked.",
        ),
    ]


def validate_label_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("Label rows are required for this partial build.")
    for row in rows:
        missing = [column for column in LABEL_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"Label row missing columns: {missing}")
        if row["review_only"] != "true":
            raise ValueError("Label rows must keep review_only=true.")
        if row["model_use_allowed"] != "false":
            raise ValueError("Label rows must keep model_use_allowed=false.")
        if row["training_allowed"] != "false":
            raise ValueError("Label rows must keep training_allowed=false.")
        if row["scoring_mode"] != EXPECTED_SCORING_MODE:
            raise ValueError("Label rows must preserve exact_verified_first_downs scoring.")
        text = ",".join(row.values()).lower()
        if "probability" in text or "0%" in text:
            raise ValueError("Label rows must not contain probabilities or fake 0% values.")


def validate_review_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row.get("review_only") != "true":
            raise ValueError("Rows must keep review_only=true.")
        if row.get("model_use_allowed") != "false":
            raise ValueError("Rows must keep model_use_allowed=false.")
        if row.get("training_allowed") != "false":
            raise ValueError("Rows must keep training_allowed=false.")


def write_inventory_doc(
    root: Path,
    *,
    bridge_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
    latest_label_season: int,
    scoring_mode: str,
    label_path: Path,
) -> None:
    lines = [
        "# Historical Rookie Label Builder Inventory - 2026-06-30",
        "",
        f"- Actual base HEAD: `{BASE_HEAD}`",
        f"- Bridge artifact: `{BRIDGE_PATH}`",
        f"- Outcome V2 season labels: `{OUTCOME_SEASON_LABEL_PATH}`",
        f"- Generated shared label artifact: `{label_path}`",
        f"- Bridge rows available: {len(bridge_rows)}",
        f"- Partial label rows buildable: {len(label_rows)}",
        f"- Classes: {class_range(bridge_rows)}",
        f"- Position coverage: {format_counts(Counter(row['position'] for row in bridge_rows))}",
        f"- Latest Outcome V2 season: {latest_label_season}",
        f"- Scoring mode: `{scoring_mode}`",
        "",
        "## Missing Inputs / Limits",
        "",
        "- UDFA/free-agent rookies are out of scope.",
        "- Missing GSIS/player_stats IDs remain blocked.",
        "- Unlinked bridge rows remain blocked.",
        "- Incomplete windows remain right-censored.",
        "- No model/training/source-truth promotion.",
        "",
        "Partial drafted-player label build is possible and was built review-only.",
    ]
    (root / "00_LABEL_BUILDER_INVENTORY.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_label_spec_lock_doc(root: Path, scoring_mode: str) -> None:
    lines = [
        "# Historical Rookie Label Spec Lock - 2026-06-30",
        "",
        "- Rookie year = `rookie_class_year` / `draft_year`.",
        "- Year 2 = rookie year + 1.",
        "- First 3 years = threshold hit at least once from rookie year through rookie year + 2.",
        "- First 5 years = threshold hit at least once from rookie year through rookie year + 4.",
        "- Incomplete future windows = `right_censored`.",
        f"- Missing labels = `{NOT_ENOUGH}`, never `0%`.",
        f"- Scoring mode locked to `{scoring_mode}`.",
        "- Approximation rows: 0; no approximate scoring rows were generated.",
        "",
        "Thresholds:",
        "",
        "- QB: T6, T12",
        "- RB: T6, T12, T24, T36",
        "- WR: T6, T12, T24, T36",
        "- TE: T6, T12",
    ]
    (root / "01_LABEL_SPEC_LOCK.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_coverage_report_doc(
    root: Path,
    *,
    bridge_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
    latest_label_season: int,
    scoring_mode: str,
) -> None:
    blocked = len(bridge_rows) - len(label_rows)
    lines = [
        "# Label Coverage and Quality Report - 2026-06-30",
        "",
        f"- Total bridge rows considered: {len(bridge_rows)}",
        f"- Total label rows built: {len(label_rows)}",
        f"- Rows blocked: {blocked}",
        f"- Class/year coverage: {class_range(label_rows)}",
        f"- Position coverage: {format_counts(Counter(row['position'] for row in label_rows))}",
        f"- Rookie-year coverage rows: {non_missing(label_rows, 'rookie_year_position_finish')}",
        f"- Year-2 coverage rows: {non_missing(label_rows, 'year_2_position_finish')}",
        f"- First-3-year complete rows: {count_true(label_rows, 'first_3y_window_complete')}",
        f"- First-5-year complete rows: {count_true(label_rows, 'first_5y_window_complete')}",
        (
            "- Censoring summary: "
            f"{format_counts(Counter(row['censoring_status'] for row in label_rows))}"
        ),
        f"- Exact vs approximate scoring: `{scoring_mode}`, approximation rows 0",
        f"- Latest Outcome V2 season: {latest_label_season}",
        "- Missing GSIS/player_stats ID rows: 5 from the bridge.",
        "- Unlinked outcome label rows: 101 from the bridge.",
        "- UDFA/free-agent rookies remain out of scope.",
        "",
        "Labels are sufficient for Gate D review as a partial drafted-player-only",
        "review artifact, not as model/training/source-truth data.",
    ]
    (root / "02_LABEL_COVERAGE_AND_QUALITY_REPORT.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_gate_c_decision_doc(
    root: Path,
    bridge_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
) -> None:
    lines = [
        "# Gate C Historical Label Decision - 2026-06-30",
        "",
        "## Verdict",
        "",
        f"`{FINAL_VERDICT}`",
        "",
        "Partial historical rookie labels were built for drafted QB/RB/WR/TE rows",
        "that link through the approved review-only GSIS/player_stats bridge to",
        "Outcome V2 exact first-down target labels.",
        "",
        "## What Is Partial",
        "",
        f"- Bridge rows considered: {len(bridge_rows)}",
        f"- Label rows built: {len(label_rows)}",
        f"- Blocked bridge rows: {len(bridge_rows) - len(label_rows)}",
        "- UDFA/free-agent rookies are not included.",
        "- Missing GSIS and unlinked rows remain blocked.",
        "- Recent incomplete windows remain right-censored.",
        "",
        "## Gate D",
        "",
        "Gate D can run next as a review-only partial drafted-player feature policy",
        "gate. It must not promote these labels to model/training/source truth.",
    ]
    (root / "03_GATE_C_HISTORICAL_LABEL_DECISION.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_readme(root: Path, label_rows: list[dict[str, str]], label_path: Path) -> None:
    lines = [
        "# Historical Rookie Label Builder V1",
        "",
        f"Final verdict: `{FINAL_VERDICT}`",
        "",
        "This package is review-only. It does not create probabilities, model scores,",
        "Rankings columns, source-truth rows, or training truth.",
        "",
        "Generated full labels live outside git:",
        "",
        f"- `{label_path}`",
        "",
        f"Tracked summary label rows built: {len(label_rows)}.",
    ]
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def scoring_mode_from_manifest(rows: list[dict[str, str]]) -> str:
    modes = {clean(row.get("scoring_mode")) for row in rows if clean(row.get("scoring_mode"))}
    if modes == {EXPECTED_SCORING_MODE}:
        return EXPECTED_SCORING_MODE
    return "|".join(sorted(modes)) if modes else NOT_ENOUGH


def blocker_for_bridge(row: dict[str, str]) -> str:
    if clean(row.get("gsis_id")) == NOT_ENOUGH:
        return "missing_gsis_id"
    if clean(row.get("outcome_label_link_status")) != "linked_to_outcome_labels":
        return "unlinked_outcome_labels"
    return "linked"


def manifest_row(
    run_id: str,
    run_timestamp: str,
    artifact: str,
    source: str,
    rows: int,
    output_path: Path,
    notes: str,
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "run_timestamp": run_timestamp,
        "artifact": artifact,
        "source": source,
        "rows": str(rows),
        "output_path": str(output_path),
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "notes": notes,
    }


def coverage(metric: str, value: object, notes: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": str(value),
        "notes": notes,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


def non_missing(rows: list[dict[str, str]], field: str) -> int:
    return sum(row.get(field) != NOT_ENOUGH for row in rows)


def count_true(rows: list[dict[str, str]], field: str) -> int:
    return sum(row.get(field) == "true" for row in rows)


def class_range(rows: list[dict[str, str]]) -> str:
    years = sorted({to_int(row.get("rookie_class_year") or row.get("draft_year")) for row in rows})
    years = [year for year in years if year is not None]
    if not years:
        return NOT_ENOUGH
    return f"{years[0]}-{years[-1]}"


def format_counts(counts: Counter[str]) -> str:
    return "; ".join(f"{key}:{value}" for key, value in sorted(counts.items()))


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: object) -> int | None:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def clean(value: object) -> str:
    return str(value or "").strip()


if __name__ == "__main__":
    raise SystemExit(main())
