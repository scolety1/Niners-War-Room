from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_class_gsis_bridge_v1_20260630"
)
SHARED_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\draft_class_gsis_bridge_v1")
OUTCOME_SHARED_ROOT = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended"
)
OUTCOME_ANCHOR_LABEL_PATH = (
    OUTCOME_SHARED_ROOT / "outcome_v2_extended_anchor_horizon_labels.csv"
)
OUTCOME_MANIFEST_PATH = OUTCOME_SHARED_ROOT / "outcome_v2_extended_label_manifest.csv"

DRAFT_PICKS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "draft_picks/draft_picks.csv"
)
NFLVERSE_DRAFT_DICTIONARY_URL = (
    "https://nflreadr.nflverse.com/reference/dictionary_draft_picks.html"
)
BASE_HEAD = "5dc578d9c8feaa02b49f8db9700999f651158500"
SOURCE_POLICY_VERDICT = "PARTIAL_BRIDGE_SOURCE_POLICY"
FINAL_VERDICT = "PARTIAL_DRAFT_CLASS_GSIS_BRIDGE"
NOT_ENOUGH = "Not enough information"
SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")
MIN_DRAFT_YEAR = 2012
MAX_DRAFT_YEAR = 2024
LATEST_LABEL_SEASON = 2024

BRIDGE_COLUMNS = (
    "player_name",
    "position",
    "draft_year",
    "rookie_class_year",
    "draft_round",
    "draft_pick",
    "drafted_team",
    "nfl_team_initial",
    "college_team",
    "nfl_player_id",
    "gsis_id",
    "player_stats_id",
    "pfr_player_id",
    "cfb_player_id",
    "nwr_player_id",
    "cfbd_player_id",
    "identity_source_status",
    "draft_class_source_status",
    "nfl_id_source_status",
    "outcome_label_link_status",
    "first_outcome_season_available",
    "rookie_year_label_possible",
    "year_2_label_possible",
    "first_3y_window_complete",
    "fifth_year_window_complete",
    "bridge_status",
    "blocker_reason",
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
        description="Build review-only historical rookie draft-class to GSIS bridge."
    )
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--shared-output-root", type=Path, default=SHARED_OUTPUT_ROOT)
    parser.add_argument("--draft-picks-url", default=DRAFT_PICKS_URL)
    parser.add_argument("--outcome-anchor-label-path", type=Path, default=OUTCOME_ANCHOR_LABEL_PATH)
    parser.add_argument("--outcome-manifest-path", type=Path, default=OUTCOME_MANIFEST_PATH)
    args = parser.parse_args()

    run_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    run_id = "rookie_draft_class_gsis_bridge_v1_20260630"
    draft_rows = read_csv_url(args.draft_picks_url)
    outcome_rows = read_csv_path(args.outcome_anchor_label_path)
    outcome_manifest_rows = (
        read_csv_path(args.outcome_manifest_path)
        if args.outcome_manifest_path.exists()
        else []
    )

    bridge_rows = build_bridge_rows(
        draft_rows=draft_rows,
        outcome_rows=outcome_rows,
    )
    validate_bridge_rows(bridge_rows)
    coverage_rows = build_coverage_rows(
        bridge_rows=bridge_rows,
        outcome_rows=outcome_rows,
    )
    validate_review_rows(coverage_rows)

    args.shared_output_root.mkdir(parents=True, exist_ok=True)
    shared_bridge_path = (
        args.shared_output_root / "historical_rookie_draft_class_gsis_bridge_v1.csv"
    )
    shared_manifest_path = (
        args.shared_output_root
        / "historical_rookie_draft_class_gsis_bridge_manifest_v1.csv"
    )
    shared_coverage_path = (
        args.shared_output_root
        / "historical_rookie_draft_class_gsis_bridge_coverage_summary_v1.csv"
    )
    write_csv(shared_bridge_path, BRIDGE_COLUMNS, bridge_rows)
    write_csv(shared_coverage_path, COVERAGE_COLUMNS, coverage_rows)
    manifest_rows = build_manifest_rows(
        run_id=run_id,
        run_timestamp=run_timestamp,
        bridge_rows=bridge_rows,
        coverage_rows=coverage_rows,
        shared_bridge_path=shared_bridge_path,
        shared_coverage_path=shared_coverage_path,
    )
    write_csv(shared_manifest_path, MANIFEST_COLUMNS, manifest_rows)

    args.output_root.mkdir(parents=True, exist_ok=True)
    write_csv(
        args.output_root / "rookie_draft_class_gsis_bridge_coverage_matrix_v1.csv",
        COVERAGE_COLUMNS,
        coverage_rows,
    )
    write_inventory_doc(
        args.output_root,
        bridge_rows=bridge_rows,
        outcome_rows=outcome_rows,
        outcome_manifest_rows=outcome_manifest_rows,
        shared_bridge_path=shared_bridge_path,
        shared_manifest_path=shared_manifest_path,
        shared_coverage_path=shared_coverage_path,
    )
    write_source_policy_gate_doc(args.output_root, bridge_rows)
    write_outcome_linkage_summary_doc(args.output_root, bridge_rows)
    write_final_decision_doc(args.output_root, bridge_rows)
    write_readme(args.output_root, bridge_rows, shared_bridge_path)

    print(
        {
            "source_policy": SOURCE_POLICY_VERDICT,
            "final_verdict": FINAL_VERDICT,
            "bridge_rows": len(bridge_rows),
            "linked_rows": count_status(
                bridge_rows,
                "outcome_label_link_status",
                "linked_to_outcome_labels",
            ),
            "shared_bridge": str(shared_bridge_path),
        }
    )
    return 0


def read_csv_url(url: str) -> list[dict[str, str]]:
    with urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def read_csv_path(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_bridge_rows(
    *,
    draft_rows: list[dict[str, str]],
    outcome_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    outcome_seasons_by_player = outcome_seasons(outcome_rows)
    duplicate_keys = duplicate_identity_keys(draft_rows)
    rows: list[dict[str, str]] = []
    for draft in draft_rows:
        draft_year = to_int(clean(draft.get("season")))
        position = clean(draft.get("position"))
        if draft_year is None or not MIN_DRAFT_YEAR <= draft_year <= MAX_DRAFT_YEAR:
            continue
        if position not in SUPPORTED_POSITIONS:
            continue

        player_name = clean(draft.get("pfr_player_name")) or NOT_ENOUGH
        gsis_id = clean(draft.get("gsis_id")) or NOT_ENOUGH
        seasons = outcome_seasons_by_player.get(gsis_id, set())
        duplicate_key = identity_key(player_name, position, str(draft_year))
        is_ambiguous = duplicate_key in duplicate_keys
        first_outcome_season = min(seasons) if seasons else None
        outcome_link_status = outcome_label_link_status(
            gsis_id=gsis_id,
            seasons=seasons,
            is_ambiguous=is_ambiguous,
        )
        first_3y_complete = draft_year + 2 <= LATEST_LABEL_SEASON
        first_5y_complete = draft_year + 4 <= LATEST_LABEL_SEASON
        bridge_status = bridge_status_for(
            gsis_id=gsis_id,
            is_ambiguous=is_ambiguous,
            linked=outcome_link_status == "linked_to_outcome_labels",
            fifth_year_window_complete=first_5y_complete,
        )
        rows.append(
            {
                "player_name": player_name,
                "position": position,
                "draft_year": str(draft_year),
                "rookie_class_year": str(draft_year),
                "draft_round": clean(draft.get("round")) or NOT_ENOUGH,
                "draft_pick": clean(draft.get("pick")) or NOT_ENOUGH,
                "drafted_team": clean(draft.get("team")) or NOT_ENOUGH,
                "nfl_team_initial": clean(draft.get("team")) or NOT_ENOUGH,
                "college_team": clean(draft.get("college")) or NOT_ENOUGH,
                "nfl_player_id": gsis_id,
                "gsis_id": gsis_id,
                "player_stats_id": gsis_id,
                "pfr_player_id": clean(draft.get("pfr_player_id")) or NOT_ENOUGH,
                "cfb_player_id": clean(draft.get("cfb_player_id")) or NOT_ENOUGH,
                "nwr_player_id": NOT_ENOUGH,
                "cfbd_player_id": NOT_ENOUGH,
                "identity_source_status": identity_source_status(gsis_id, is_ambiguous),
                "draft_class_source_status": (
                    "nflverse_draft_picks_public_structured_review_only"
                ),
                "nfl_id_source_status": nfl_id_source_status(gsis_id),
                "outcome_label_link_status": outcome_link_status,
                "first_outcome_season_available": (
                    str(first_outcome_season) if first_outcome_season else NOT_ENOUGH
                ),
                "rookie_year_label_possible": bool_text(draft_year in seasons),
                "year_2_label_possible": bool_text(draft_year + 1 in seasons),
                "first_3y_window_complete": bool_text(first_3y_complete),
                "fifth_year_window_complete": bool_text(first_5y_complete),
                "bridge_status": bridge_status,
                "blocker_reason": blocker_reason(
                    gsis_id=gsis_id,
                    is_ambiguous=is_ambiguous,
                    linked=outcome_link_status == "linked_to_outcome_labels",
                    fifth_year_window_complete=first_5y_complete,
                ),
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return rows


def outcome_seasons(outcome_rows: list[dict[str, str]]) -> dict[str, set[int]]:
    seasons_by_player: dict[str, set[int]] = defaultdict(set)
    for row in outcome_rows:
        player_id = clean(row.get("player_id"))
        season = to_int(row.get("anchor_season") or row.get("season"))
        if player_id and season is not None:
            seasons_by_player[player_id].add(season)
    return seasons_by_player


def duplicate_identity_keys(draft_rows: list[dict[str, str]]) -> set[str]:
    keys: Counter[str] = Counter()
    for row in draft_rows:
        year = clean(row.get("season"))
        position = clean(row.get("position"))
        if position in SUPPORTED_POSITIONS:
            keys[identity_key(clean(row.get("pfr_player_name")), position, year)] += 1
    return {key for key, count in keys.items() if key and count > 1}


def identity_key(player_name: str, position: str, draft_year: str) -> str:
    normalized = "".join(char for char in player_name.lower() if char.isalnum())
    return "|".join((normalized, position.upper(), draft_year))


def outcome_label_link_status(
    *,
    gsis_id: str,
    seasons: set[int],
    is_ambiguous: bool,
) -> str:
    if is_ambiguous:
        return "blocked_ambiguous_identity"
    if gsis_id == NOT_ENOUGH:
        return "blocked_missing_gsis_id"
    if seasons:
        return "linked_to_outcome_labels"
    return "blocked_no_outcome_label_rows"


def identity_source_status(gsis_id: str, is_ambiguous: bool) -> str:
    if is_ambiguous:
        return "ambiguous_duplicate_name_position_year_review_required"
    if gsis_id == NOT_ENOUGH:
        return "draft_pick_identity_missing_gsis_id_review_required"
    return "nflverse_draft_pick_identity_review_only"


def nfl_id_source_status(gsis_id: str) -> str:
    if gsis_id == NOT_ENOUGH:
        return "missing_gsis_id_review_required"
    if not gsis_id.startswith("00-"):
        return "legacy_or_nonstandard_gsis_id_review_required"
    return "gsis_id_available_review_only"


def bridge_status_for(
    *,
    gsis_id: str,
    is_ambiguous: bool,
    linked: bool,
    fifth_year_window_complete: bool,
) -> str:
    if is_ambiguous:
        return "blocked_ambiguous_identity"
    if gsis_id == NOT_ENOUGH:
        return "blocked_missing_gsis_id"
    if not linked:
        return "blocked_no_outcome_label_link"
    if fifth_year_window_complete:
        return "linked_review_only_complete_5y"
    return "linked_review_only_right_censored_5y"


def blocker_reason(
    *,
    gsis_id: str,
    is_ambiguous: bool,
    linked: bool,
    fifth_year_window_complete: bool,
) -> str:
    if is_ambiguous:
        return "Ambiguous duplicate draft identity requires human review."
    if gsis_id == NOT_ENOUGH:
        return "Draft pick row is missing GSIS/player_stats ID."
    if not linked:
        return "No Outcome V2 target label row found for this GSIS/player_stats ID."
    if not fifth_year_window_complete:
        return "Linked review-only bridge; 5Y window is right-censored by 2024 labels."
    return "Linked review-only bridge; still not model/training/source-truth approved."


def build_coverage_rows(
    *,
    bridge_rows: list[dict[str, str]],
    outcome_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    linked = rows_with_value(bridge_rows, "outcome_label_link_status", "linked_to_outcome_labels")
    with_gsis = [row for row in bridge_rows if row["gsis_id"] != NOT_ENOUGH]
    position_counts = Counter(row["position"] for row in bridge_rows)
    year_counts = Counter(row["draft_year"] for row in bridge_rows)
    linked_position_counts = Counter(row["position"] for row in linked)
    linked_year_counts = Counter(row["draft_year"] for row in linked)
    latest_label = max(to_int(row.get("anchor_season")) or 0 for row in outcome_rows)
    return [
        coverage(
            "source_policy_gate",
            SOURCE_POLICY_VERDICT,
            "Public factual source is usable with limits.",
        ),
        coverage(
            "final_bridge_verdict",
            FINAL_VERDICT,
            "Partial bridge, not model/training approved.",
        ),
        coverage(
            "historical_rookie_draft_rows",
            len(bridge_rows),
            "Drafted QB/RB/WR/TE rows, 2012-2024.",
        ),
        coverage(
            "rows_with_draft_year",
            len(bridge_rows),
            "Draft source carries season/draft year.",
        ),
        coverage(
            "rows_with_gsis_or_player_stats_id",
            len(with_gsis),
            "GSIS/player_stats IDs from draft_picks.",
        ),
        coverage(
            "rows_missing_gsis_or_player_stats_id",
            len(bridge_rows) - len(with_gsis),
            "Blocked rows.",
        ),
        coverage(
            "rows_linked_to_outcome_labels",
            len(linked),
            "Joined to Outcome V2 by GSIS/player_stats ID.",
        ),
        coverage(
            "rows_not_linked_to_outcome_labels",
            len(bridge_rows) - len(linked),
            "Missing GSIS or no target-label row.",
        ),
        coverage(
            "rookie_year_label_possible_rows",
            count_true(bridge_rows, "rookie_year_label_possible"),
            "Outcome label row exists in rookie class year.",
        ),
        coverage(
            "year_2_label_possible_rows",
            count_true(bridge_rows, "year_2_label_possible"),
            "Outcome label row exists in rookie class year plus one.",
        ),
        coverage(
            "first_3y_calendar_complete_rows",
            count_true(bridge_rows, "first_3y_window_complete"),
            "Latest target label season allows a 3Y window.",
        ),
        coverage(
            "first_5y_calendar_complete_rows",
            count_true(bridge_rows, "fifth_year_window_complete"),
            "Latest target label season allows a 5Y window.",
        ),
        coverage(
            "linked_first_3y_calendar_complete_rows",
            sum(
                row["outcome_label_link_status"] == "linked_to_outcome_labels"
                and row["first_3y_window_complete"] == "true"
                for row in bridge_rows
            ),
            "Linked rows with calendar-complete 3Y windows.",
        ),
        coverage(
            "linked_first_5y_calendar_complete_rows",
            sum(
                row["outcome_label_link_status"] == "linked_to_outcome_labels"
                and row["fifth_year_window_complete"] == "true"
                for row in bridge_rows
            ),
            "Linked rows with calendar-complete 5Y windows.",
        ),
        coverage(
            "position_coverage",
            format_counts(position_counts),
            "All bridge rows by position.",
        ),
        coverage(
            "linked_position_coverage",
            format_counts(linked_position_counts),
            "Outcome-linked rows by position.",
        ),
        coverage(
            "draft_year_coverage",
            format_counts(year_counts),
            "All bridge rows by draft year.",
        ),
        coverage(
            "linked_draft_year_coverage",
            format_counts(linked_year_counts),
            "Outcome-linked rows by draft year.",
        ),
        coverage("latest_outcome_label_season", latest_label, "Outcome V2 target label ceiling."),
        coverage("rookie_probabilities_created", 0, "No probabilities created in this lane."),
        coverage("rankings_wiring_created", 0, "No Rankings/app wiring created in this lane."),
    ]


def build_manifest_rows(
    *,
    run_id: str,
    run_timestamp: str,
    bridge_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    shared_bridge_path: Path,
    shared_coverage_path: Path,
) -> list[dict[str, str]]:
    return [
        manifest_row(
            run_id,
            run_timestamp,
            "historical_rookie_draft_class_gsis_bridge_v1.csv",
            DRAFT_PICKS_URL,
            len(bridge_rows),
            shared_bridge_path,
            "Generated review-only bridge under shared data; not tracked.",
        ),
        manifest_row(
            run_id,
            run_timestamp,
            "historical_rookie_draft_class_gsis_bridge_coverage_summary_v1.csv",
            "derived_from_bridge_and_outcome_v2_labels",
            len(coverage_rows),
            shared_coverage_path,
            "Generated review-only coverage summary under shared data; not tracked.",
        ),
    ]


def validate_bridge_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("Bridge rows are required.")
    for row in rows:
        missing = [column for column in BRIDGE_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"Bridge row missing columns: {missing}")
        if row["review_only"] != "true":
            raise ValueError("Bridge rows must keep review_only=true.")
        if row["model_use_allowed"] != "false":
            raise ValueError("Bridge rows must keep model_use_allowed=false.")
        if row["training_allowed"] != "false":
            raise ValueError("Bridge rows must keep training_allowed=false.")
        row_text = ",".join(row.values())
        if "0%" in row_text:
            raise ValueError("Missing bridge data must not be represented as 0%.")


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
    outcome_rows: list[dict[str, str]],
    outcome_manifest_rows: list[dict[str, str]],
    shared_bridge_path: Path,
    shared_manifest_path: Path,
    shared_coverage_path: Path,
) -> None:
    lines = [
        "# Draft-Class / GSIS Bridge Inventory - 2026-06-30",
        "",
        "## Current Master",
        "",
        f"- Base HEAD: `{BASE_HEAD}`",
        "- Branch: `work/historical-rookie-draft-class-gsis-bridge-v1-20260630`",
        "",
        "## Prior Rookie Gates",
        "",
        "- Gate A: `GREEN_REVIEW_ONLY_IDENTITY_APPROVAL`",
        "- Gate B: `PARTIAL_DRAFT_CAPITAL_REVIEW_ARTIFACT`",
        "- Gate C: `BLOCKED_NEEDS_DRAFT_CLASS_BRIDGE`",
        "",
        "## Sources Inventoried",
        "",
        "- Gate A CFBD identity approval artifact: current/future review-only identity context.",
        "- Gate B draft capital artifact: partial current 2026 review-only draft context.",
        "- CFBD identity/link registries: review-only, not source truth.",
        (
            "- NWR player ID maps: useful for current players, not sufficient "
            "for historical GSIS bridge."
        ),
        "- Sleeper/NWR IDs: not enough for historical player_stats labels by themselves.",
        (
            "- `nflreadpy` dependency approval: loaders are approved, but not "
            "installed in this runtime."
        ),
        "- nflverse draft-picks release CSV: public structured draft class plus GSIS/PFR IDs.",
        "- Outcome V2 target labels under shared data: review-only factual NFL outcome labels.",
        "- Old prototype/model files: reference only, not source-approved for labels.",
        "",
        "## Sources Excluded",
        "",
        "- Market, ADP, DynastyProcess, projections, vendor/RotoWire, Gmail, and scraping.",
        "- CFBD as NFL outcome truth.",
        "- App display gaps as negative labels.",
        "",
        "## Generated Shared Outputs",
        "",
        f"- Bridge CSV: `{shared_bridge_path}`",
        f"- Manifest CSV: `{shared_manifest_path}`",
        f"- Coverage CSV: `{shared_coverage_path}`",
        "- Shared outputs are outside git and must remain untracked.",
        "",
        "## Inventory Counts",
        "",
        f"- Bridge rows built: {len(bridge_rows)}",
        f"- Outcome V2 rows inspected: {len(outcome_rows)}",
        f"- Outcome V2 manifest rows inspected: {len(outcome_manifest_rows)}",
    ]
    (root / "00_BRIDGE_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_source_policy_gate_doc(root: Path, bridge_rows: list[dict[str, str]]) -> None:
    with_gsis = count_not_value(bridge_rows, "gsis_id", NOT_ENOUGH)
    linked = count_status(bridge_rows, "outcome_label_link_status", "linked_to_outcome_labels")
    lines = [
        "# Bridge Source-Policy Gate - 2026-06-30",
        "",
        "## Verdict",
        "",
        f"`{SOURCE_POLICY_VERDICT}`",
        "",
        "The bridge may use public structured nflverse draft-picks data for",
        "review-only historical drafted-player bridge rows. This is partial because",
        "it covers drafted players only, has a small number of missing GSIS IDs,",
        "and does not approve any model/training/source-truth use.",
        "",
        "## Approved Review-Only Source Candidate",
        "",
        f"- Source: `{DRAFT_PICKS_URL}`",
        f"- Dictionary: `{NFLVERSE_DRAFT_DICTIONARY_URL}`",
        "- Fields used: season, round, pick, team, gsis_id, pfr_player_id,",
        "  cfb_player_id, pfr_player_name, position, college.",
        "",
        "## Counts",
        "",
        f"- Drafted QB/RB/WR/TE rows: {len(bridge_rows)}",
        f"- Rows with GSIS/player_stats ID: {with_gsis}",
        f"- Rows linked to Outcome V2 labels: {linked}",
        "",
        "## Guardrails",
        "",
        "- `review_only=true`",
        "- `model_use_allowed=false`",
        "- `training_allowed=false`",
        "- No rookie probabilities.",
        "- No Rankings/app wiring.",
        "- Missing data remains `Not enough information`, never `0%`.",
    ]
    (root / "01_BRIDGE_SOURCE_POLICY_GATE.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_outcome_linkage_summary_doc(root: Path, bridge_rows: list[dict[str, str]]) -> None:
    total = len(bridge_rows)
    with_gsis = count_not_value(bridge_rows, "gsis_id", NOT_ENOUGH)
    linked = rows_with_value(bridge_rows, "outcome_label_link_status", "linked_to_outcome_labels")
    position_counts = Counter(row["position"] for row in bridge_rows)
    linked_position_counts = Counter(row["position"] for row in linked)
    class_counts = Counter(row["draft_year"] for row in bridge_rows)
    linked_class_counts = Counter(row["draft_year"] for row in linked)
    lines = [
        "# Outcome Label Linkage Summary - 2026-06-30",
        "",
        "## Summary",
        "",
        f"- Total historical rookie class rows: {total}",
        f"- Rows with draft year: {total}",
        f"- Rows with NFL/player_stats ID: {with_gsis}",
        f"- Rows linked to outcome labels: {len(linked)}",
        (
            "- Rows with complete rookie-year label possibility: "
            f"{count_true(bridge_rows, 'rookie_year_label_possible')}"
        ),
        (
            "- Rows with complete year-2 label possibility: "
            f"{count_true(bridge_rows, 'year_2_label_possible')}"
        ),
        (
            "- Rows with complete first-3-year calendar window: "
            f"{count_true(bridge_rows, 'first_3y_window_complete')}"
        ),
        (
            "- Rows with complete first-5-year calendar window: "
            f"{count_true(bridge_rows, 'fifth_year_window_complete')}"
        ),
        "",
        "## Position Coverage",
        "",
        f"- All bridge rows: {format_counts(position_counts)}",
        f"- Linked rows: {format_counts(linked_position_counts)}",
        "",
        "## Class Coverage",
        "",
        f"- All bridge rows: {format_counts(class_counts)}",
        f"- Linked rows: {format_counts(linked_class_counts)}",
        "",
        "## Exact Blockers",
        "",
        "- Undrafted/free-agent rookies are not covered by draft-picks rows.",
        "- Rows without GSIS/player_stats ID remain blocked.",
        "- Rows without Outcome V2 target-label rows remain blocked.",
        "- 2021-2024 classes are right-censored for 5Y windows by the 2024 target ceiling.",
        "- This bridge is still review-only and not source truth for model/training.",
    ]
    (root / "02_OUTCOME_LABEL_LINKAGE_SUMMARY.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_final_decision_doc(root: Path, bridge_rows: list[dict[str, str]]) -> None:
    linked = count_status(bridge_rows, "outcome_label_link_status", "linked_to_outcome_labels")
    missing_gsis = count_status(bridge_rows, "gsis_id", NOT_ENOUGH)
    lines = [
        "# Draft-Class / GSIS Bridge Final Decision - 2026-06-30",
        "",
        "## Verdict",
        "",
        f"`{FINAL_VERDICT}`",
        "",
        "A review-only historical drafted-rookie bridge now exists under shared data.",
        "It connects draft year/round/pick/team to GSIS/player_stats IDs and Outcome",
        "V2 target-label availability for drafted QB/RB/WR/TE rows from 2012-2024.",
        "",
        "## Counts",
        "",
        f"- Bridge rows built: {len(bridge_rows)}",
        f"- Rows linked to Outcome V2 labels: {linked}",
        f"- Rows missing GSIS/player_stats ID: {missing_gsis}",
        "- Historical rookie probability rows built: 0",
        "- Rankings/app wiring rows built: 0",
        "",
        "## Gate C Retry",
        "",
        "Gate C can be retried for a partial drafted-player historical label build.",
        "It must keep UDFA and unlinked rows blocked, preserve right-censoring, and",
        "keep all rows review-only unless a later gate explicitly approves more.",
        "",
        "## Remaining Blockers",
        "",
        "- No UDFA/free-agent rookie-entry bridge.",
        "- No current 2026 CFBD-to-GSIS bridge.",
        "- Some drafted rows lack outcome-label linkage.",
        "- No model/training/source-truth promotion.",
    ]
    (root / "03_BRIDGE_FINAL_DECISION.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_readme(root: Path, bridge_rows: list[dict[str, str]], shared_bridge_path: Path) -> None:
    linked = count_status(bridge_rows, "outcome_label_link_status", "linked_to_outcome_labels")
    lines = [
        "# Historical Rookie Draft-Class + GSIS Bridge V1",
        "",
        f"Final verdict: `{FINAL_VERDICT}`",
        "",
        "This package is review-only. It does not create rookie probabilities, model",
        "scores, Rankings columns, source-truth rows, or training truth.",
        "",
        "## Artifacts",
        "",
        "- `00_BRIDGE_INVENTORY.md`",
        "- `01_BRIDGE_SOURCE_POLICY_GATE.md`",
        "- `rookie_draft_class_gsis_bridge_coverage_matrix_v1.csv`",
        "- `02_OUTCOME_LABEL_LINKAGE_SUMMARY.md`",
        "- `03_BRIDGE_FINAL_DECISION.md`",
        "",
        "## Generated Shared Data",
        "",
        f"- `{shared_bridge_path}`",
        "- Full generated bridge rows live outside git under `C:\\NWR_SHARED_DATA`.",
        "",
        "## Counts",
        "",
        f"- Bridge rows: {len(bridge_rows)}",
        f"- Outcome-linked rows: {linked}",
        "- Model-use rows: 0",
        "- Training-use rows: 0",
    ]
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def coverage(metric: str, value: object, notes: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": str(value),
        "notes": notes,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


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


def rows_with_value(rows: list[dict[str, str]], field: str, value: str) -> list[dict[str, str]]:
    return [row for row in rows if row[field] == value]


def count_status(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(row[field] == value for row in rows)


def count_not_value(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(row[field] != value for row in rows)


def count_true(rows: list[dict[str, str]], field: str) -> int:
    return sum(row[field] == "true" for row in rows)


def format_counts(counts: Counter[str]) -> str:
    return "; ".join(f"{key}:{value}" for key, value in sorted(counts.items()))


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def to_int(value: object) -> int | None:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def clean(value: object) -> str:
    return str(value or "").strip()


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
