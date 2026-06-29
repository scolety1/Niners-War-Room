from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_historical_labels_v1_20260630"
)
APPROVAL_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "cfbd_rookie_identity_approval_v1_20260629"
    / "cfbd_rookie_identity_human_approval_v1.csv"
)
DRAFT_CAPITAL_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_capital_review_v1_20260629"
    / "rookie_draft_capital_review_artifact_v1.csv"
)
OUTCOME_SHARED_ROOT = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended"
)
OUTCOME_BRANCH = "origin/work/outcome-v2-5y-data-coverage-20260630"
OUTCOME_BRANCH_HEAD = "e9cef8d2456164c93151d5e841de46010efd9d8e"
BASE_HEAD = "291d219a705897bece621ac41bfd779bb3cd1791"
NOT_ENOUGH = "Not enough information"
GATE_C_DECISION = "BLOCKED_NEEDS_DRAFT_CLASS_BRIDGE"
TARGET_SOURCE_GATE = "GREEN_REVIEW_ONLY_NFL_OUTCOME_TARGET_SOURCE"

THRESHOLD_MAP = {
    "QB": (6, 12),
    "RB": (6, 12, 24, 36),
    "WR": (6, 12, 24, 36),
    "TE": (6, 12),
}

BRIDGE_COLUMNS = (
    "cfbd_player_id",
    "nfl_player_id",
    "nwr_player_id",
    "player_name",
    "position",
    "college_team",
    "draft_year",
    "rookie_class_year",
    "draft_capital_status",
    "identity_approval_status",
    "cfbd_bridge_status",
    "nfl_outcome_label_link_status",
    "ambiguity_flag",
    "blocker_reason",
    "review_only",
    "approved_by_human",
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Gate C rookie historical label source-policy artifacts."
    )
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--approval-path", type=Path, default=APPROVAL_PATH)
    parser.add_argument("--draft-capital-path", type=Path, default=DRAFT_CAPITAL_PATH)
    parser.add_argument("--outcome-shared-root", type=Path, default=OUTCOME_SHARED_ROOT)
    args = parser.parse_args()

    approval_rows = _read_rows(args.approval_path)
    draft_rows = _read_rows(args.draft_capital_path)
    approved_rows = [
        row for row in approval_rows if _clean(row.get("approved_by_human")) == "true"
    ]
    draft_by_player_id = {_clean(row.get("player_id")): row for row in draft_rows}
    outcome_status = inspect_outcome_v2_shared_outputs(args.outcome_shared_root)
    bridge_rows = build_bridge_rows(
        approved_rows=approved_rows,
        draft_by_player_id=draft_by_player_id,
        outcome_player_ids=outcome_status["anchor_player_ids"],
    )
    validate_bridge_rows(bridge_rows)
    coverage_rows = build_coverage_rows(
        bridge_rows=bridge_rows,
        outcome_status=outcome_status,
    )
    validate_review_rows(coverage_rows)

    args.output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(
        args.output_root / "rookie_cfbd_to_nfl_bridge_matrix_v1.csv",
        BRIDGE_COLUMNS,
        bridge_rows,
    )
    _write_csv(
        args.output_root / "rookie_historical_label_coverage_matrix_v1.csv",
        COVERAGE_COLUMNS,
        coverage_rows,
    )
    _write_inventory(args.output_root, bridge_rows, outcome_status)
    _write_bridge_audit(args.output_root, bridge_rows)
    _write_target_source_gate(args.output_root, outcome_status)
    _write_label_spec(args.output_root)
    _write_gate_c_decision(args.output_root, bridge_rows, outcome_status)
    _write_readme(args.output_root, bridge_rows, outcome_status)

    print(
        {
            "gate_c": GATE_C_DECISION,
            "bridge_rows": len(bridge_rows),
            "linked_to_outcome_labels": sum(
                row["nfl_outcome_label_link_status"] == "linked_to_review_only_outcome_labels"
                for row in bridge_rows
            ),
            "outcome_target_source_gate": TARGET_SOURCE_GATE,
        }
    )
    return 0


def inspect_outcome_v2_shared_outputs(root: Path) -> dict[str, object]:
    manifest_path = root / "outcome_v2_extended_label_manifest.csv"
    coverage_path = root / "outcome_v2_extended_5y_coverage_summary.csv"
    anchor_path = root / "outcome_v2_extended_anchor_horizon_labels.csv"
    season_path = root / "outcome_v2_extended_season_outcome_labels.csv"

    manifest_rows = _read_rows(manifest_path) if manifest_path.exists() else []
    coverage_rows = _read_rows(coverage_path) if coverage_path.exists() else []
    anchor_rows = _read_rows(anchor_path) if anchor_path.exists() else []
    season_rows = _read_rows(season_path) if season_path.exists() else []
    anchor_player_ids = {_clean(row.get("player_id")) for row in anchor_rows}
    positions = Counter(_clean(row.get("position")) for row in anchor_rows)
    complete_5y = sum(_clean(row.get("within_5y_window_complete")) == "True" for row in anchor_rows)
    seasons = {
        _clean(row.get("anchor_season") or row.get("season"))
        for row in anchor_rows + season_rows
        if _clean(row.get("anchor_season") or row.get("season"))
    }

    return {
        "root": str(root),
        "manifest_rows": manifest_rows,
        "coverage_rows": coverage_rows,
        "anchor_rows_count": len(anchor_rows),
        "season_rows_count": len(season_rows),
        "anchor_player_ids": anchor_player_ids,
        "positions": positions,
        "complete_5y_rows": complete_5y,
        "season_min": min(seasons) if seasons else NOT_ENOUGH,
        "season_max": max(seasons) if seasons else NOT_ENOUGH,
        "scoring_mode": _manifest_value(manifest_rows, "scoring_mode"),
        "review_only": _manifest_value(manifest_rows, "review_only"),
        "model_input_allowed": _manifest_value(manifest_rows, "model_input_allowed"),
        "training_allowed": _manifest_value(manifest_rows, "training_allowed"),
        "app_wiring_allowed": _manifest_value(manifest_rows, "app_wiring_allowed"),
        "outputs_present": all(
            path.exists() for path in (manifest_path, coverage_path, anchor_path, season_path)
        ),
    }


def build_bridge_rows(
    *,
    approved_rows: list[dict[str, str]],
    draft_by_player_id: dict[str, dict[str, str]],
    outcome_player_ids: set[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for approval in approved_rows:
        nwr_player_id = _clean(approval.get("player_id"))
        draft = draft_by_player_id.get(nwr_player_id, {})
        nfl_player_id = nwr_player_id if nwr_player_id.startswith("00-") else NOT_ENOUGH
        draft_year = _clean(draft.get("draft_year")) or NOT_ENOUGH
        rookie_class_year = _clean(draft.get("rookie_class_year")) or NOT_ENOUGH
        link_status = _label_link_status(nfl_player_id, draft_year, outcome_player_ids)
        blocker = _bridge_blocker_reason(nfl_player_id, draft_year, rookie_class_year, link_status)
        rows.append(
            {
                "cfbd_player_id": _clean(approval.get("cfbd_candidate_id")),
                "nfl_player_id": nfl_player_id,
                "nwr_player_id": nwr_player_id,
                "player_name": _clean(approval.get("player_name")),
                "position": _clean(approval.get("position")),
                "college_team": _clean(approval.get("college_team")),
                "draft_year": draft_year,
                "rookie_class_year": rookie_class_year,
                "draft_capital_status": _clean(draft.get("data_quality_status")) or NOT_ENOUGH,
                "identity_approval_status": _clean(approval.get("gate_a_status")),
                "cfbd_bridge_status": "cfbd_to_nwr_identity_review_only_approved",
                "nfl_outcome_label_link_status": link_status,
                "ambiguity_flag": _clean(approval.get("ambiguity_flags")) or "none",
                "blocker_reason": blocker,
                "review_only": "true",
                "approved_by_human": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return rows


def label_hit(position: str, position_finish: object, threshold: int) -> str:
    if threshold not in THRESHOLD_MAP.get(_clean(position).upper(), ()):
        return "not_applicable"
    finish = _to_int(position_finish)
    if finish is None:
        return NOT_ENOUGH
    return "hit" if finish <= threshold else "miss"


def horizon_hit(labels: list[str], *, window_complete: bool) -> str:
    if not window_complete:
        return NOT_ENOUGH
    applicable = [label for label in labels if label != "not_applicable"]
    if not applicable:
        return "not_applicable"
    if "hit" in applicable:
        return "hit"
    if any(label == NOT_ENOUGH for label in applicable):
        return NOT_ENOUGH
    return "miss"


def window_complete(
    rookie_class_year: int,
    horizon_years: int,
    *,
    latest_label_season: int,
) -> bool:
    return rookie_class_year + horizon_years - 1 <= latest_label_season


def censoring_status(
    rookie_class_year: int,
    horizon_years: int,
    *,
    latest_label_season: int,
) -> str:
    return (
        "complete"
        if window_complete(
            rookie_class_year,
            horizon_years,
            latest_label_season=latest_label_season,
        )
        else "right_censored"
    )


def validate_bridge_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != 157:
        raise ValueError(f"Expected 157 Gate-A approved bridge rows; found {len(rows)}.")
    for row in rows:
        missing = [column for column in BRIDGE_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"Bridge row missing columns: {missing}")
        if row["review_only"] != "true":
            raise ValueError("Bridge rows must be review_only=true.")
        if row["model_use_allowed"] != "false":
            raise ValueError("Bridge rows must keep model_use_allowed=false.")
        if row["training_allowed"] != "false":
            raise ValueError("Bridge rows must keep training_allowed=false.")
        if row["approved_by_human"] != "true":
            raise ValueError("Bridge rows must preserve identity-review human approval.")


def validate_review_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row.get("review_only") != "true":
            raise ValueError("Rows must keep review_only=true.")
        if row.get("model_use_allowed") != "false":
            raise ValueError("Rows must keep model_use_allowed=false.")
        if row.get("training_allowed") != "false":
            raise ValueError("Rows must keep training_allowed=false.")


def build_coverage_rows(
    *,
    bridge_rows: list[dict[str, str]],
    outcome_status: dict[str, object],
) -> list[dict[str, str]]:
    linked = sum(
        row["nfl_outcome_label_link_status"] == "linked_to_review_only_outcome_labels"
        for row in bridge_rows
    )
    draft_year_rows = sum(row["draft_year"] != NOT_ENOUGH for row in bridge_rows)
    positions = outcome_status["positions"]
    if isinstance(positions, Counter):
        position_notes = "; ".join(f"{key}:{value}" for key, value in sorted(positions.items()))
    else:
        position_notes = NOT_ENOUGH
    rows = [
        _coverage("gate_a_approved_identity_rows", len(bridge_rows), "Identity-review-only rows."),
        _coverage(
            "bridge_rows_linked_to_outcome_labels",
            linked,
            "No GSIS/NFL outcome ID bridge exists.",
        ),
        _coverage(
            "bridge_rows_with_draft_year",
            draft_year_rows,
            "Current 2026 draft context only.",
        ),
        _coverage(
            "outcome_v2_anchor_rows",
            outcome_status["anchor_rows_count"],
            "Shared-data target rows.",
        ),
        _coverage(
            "outcome_v2_season_rows",
            outcome_status["season_rows_count"],
            "Shared-data season rows.",
        ),
        _coverage(
            "outcome_v2_complete_5y_rows",
            outcome_status["complete_5y_rows"],
            "Complete 5Y rows.",
        ),
        _coverage(
            "outcome_v2_position_rows",
            position_notes,
            "Rows by position in shared target source.",
        ),
        _coverage(
            "scoring_mode",
            outcome_status["scoring_mode"],
            "Exact first-down status from manifest.",
        ),
        _coverage("historical_rookie_label_rows_built", 0, "Blocked before label artifact build."),
        _coverage("gate_c_decision", GATE_C_DECISION, "Gate D cannot run next."),
    ]
    return rows


def _write_inventory(
    root: Path,
    bridge_rows: list[dict[str, str]],
    outcome_status: dict[str, object],
) -> None:
    lines = [
        "# Gate C Inventory - 2026-06-30",
        "",
        "## Current Master",
        "",
        f"- Expected/current base: `{BASE_HEAD}`",
        "- Worktree branch: `work/historical-rookie-label-source-policy-v1-20260630`",
        "",
        "## Current Rookie Gate Artifacts",
        "",
        f"- Gate A approval artifact: `{_relative(APPROVAL_PATH)}`",
        "- Gate A approved identity rows: 157",
        "- Gate A deferred rows: 56",
        f"- Gate B draft-capital artifact: `{_relative(DRAFT_CAPITAL_PATH)}`",
        "- Gate B review-only round/pick/team rows: 54",
        "- Gate B rows still missing draft capital: 103",
        "- Prior Gate C blocker: `docs/hq/rookie_outcomes/rookie_historical_labels_v1_20260629/`",
        "",
        "## CFBD / Identity Inputs",
        "",
        "- CFBD review artifacts are review-only and remain `model_use_allowed=false`.",
        "- CFBD identity matching V1 remains review-only.",
        "- Gate-A approval is identity-review-only, not model/training/source-truth approval.",
        "- Current approved CFBD rows do not contain a GSIS/NFL outcome `player_id` bridge.",
        "",
        "## Outcome V2 5Y Branch",
        "",
        f"- Branch inspected: `{OUTCOME_BRANCH}`",
        f"- Branch HEAD: `{OUTCOME_BRANCH_HEAD}`",
        "- Branch was not merged or cherry-picked in this lane.",
        "- Diff is not directly merge-safe here because it predates latest rookie Gate B work.",
        "",
        "## Shared Outcome V2 Outputs",
        "",
        f"- Shared output root inspected: `{outcome_status['root']}`",
        f"- Outputs present: `{outcome_status['outputs_present']}`",
        f"- Anchor/horizon rows: {outcome_status['anchor_rows_count']}",
        f"- Season rows: {outcome_status['season_rows_count']}",
        f"- Complete 5Y rows: {outcome_status['complete_5y_rows']}",
        f"- Seasons: {outcome_status['season_min']}-{outcome_status['season_max']}",
        f"- Scoring mode: `{outcome_status['scoring_mode']}`",
        f"- Review-only: `{outcome_status['review_only']}`",
        "",
        "## Source Policy Docs Found",
        "",
        "- `docs/hq/data_sources/nfl_usage/NWR_NFL_USAGE_SOURCE_CONTRACT_V0_20260624.md`",
        (
            "- `docs/hq/data_sources/nfl_usage/target_backtest/"
            "NWR_NFL_USAGE_HISTORICAL_EXPANSION_STRATEGY_20260624.md`"
        ),
        "- `docs/hq/data_sources/nfl_usage/NWR_NFLREADPY_DEPENDENCY_APPROVAL_20260624.md`",
        "- `docs/hq/data_sources/cfbd_review_artifacts_20260624/README.md`",
        "- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/README.md`",
        "",
        "## Inventory Conclusion",
        "",
        "The NFL outcome target source is available for review-only target truth,",
        "but current CFBD-approved rookie identities cannot be converted into",
        "historical rookie labels because the draft-class/GSIS bridge is missing.",
        f"Bridge rows audited: {len(bridge_rows)}.",
    ]
    (root / "00_GATE_C_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_bridge_audit(root: Path, bridge_rows: list[dict[str, str]]) -> None:
    link_counts = Counter(row["nfl_outcome_label_link_status"] for row in bridge_rows)
    draft_counts = Counter(row["draft_capital_status"] for row in bridge_rows)
    lines = [
        "# CFBD Rookie Bridge Audit - 2026-06-30",
        "",
        "## Result",
        "",
        "`BLOCKED_NEEDS_DRAFT_CLASS_BRIDGE`",
        "",
        "Gate-A CFBD identities are approved only for identity review. They bridge",
        "to NWR/Sleeper-style player IDs, but not to the GSIS/NFL player IDs used by",
        "the Outcome V2 historical target labels.",
        "",
        "## Counts",
        "",
        f"- Approved identity rows audited: {len(bridge_rows)}",
        *[f"- Outcome link `{key}`: {value}" for key, value in sorted(link_counts.items())],
        *[f"- Draft capital `{key}`: {value}" for key, value in sorted(draft_counts.items())],
        "",
        "## Limitations",
        "",
        "- CFBD college team/timeline is review-only context, not outcome truth.",
        "- Draft year is present for only the partial Gate B rows.",
        "- Current 2026 rookie rows are outside the 2012-2024 historical outcome window.",
        "- Historical rookie classes need a separate identity/draft-class bridge.",
    ]
    (root / "01_CFBD_ROOKIE_BRIDGE_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_target_source_gate(root: Path, outcome_status: dict[str, object]) -> None:
    lines = [
        "# Historical NFL Outcome Target Source Gate - 2026-06-30",
        "",
        "## Gate Result",
        "",
        f"`{TARGET_SOURCE_GATE}`",
        "",
        "The NFL outcome target source can be used as review-only target truth for",
        "future historical rookie labels. It cannot by itself identify rookie",
        "classes or approve modeling/training use.",
        "",
        "## Source Candidate",
        "",
        "- Source family: `nflreadpy.load_player_stats(summary_level=reg)`",
        "- Shared generated artifacts: Outcome V2 extended historical labels",
        f"- Shared root: `{outcome_status['root']}`",
        f"- Season rows: {outcome_status['season_rows_count']}",
        f"- Anchor rows: {outcome_status['anchor_rows_count']}",
        f"- Complete 5Y rows: {outcome_status['complete_5y_rows']}",
        f"- Scoring mode: `{outcome_status['scoring_mode']}`",
        "",
        "## Source Policy",
        "",
        "- Uses factual public NFL player-season outcomes.",
        "- Does not use market, ADP, DynastyProcess, projections, vendor/Gmail, or CFBD.",
        "- Rows remain review-only and not model/training/app wiring approved.",
        "",
        "## Guardrails",
        "",
        "- `model_use_allowed=false` for this rookie lane.",
        "- `training_allowed=false` for this rookie lane.",
        "- CFBD is not used as NFL outcome truth.",
    ]
    (root / "02_HISTORICAL_NFL_OUTCOME_TARGET_SOURCE_GATE.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_label_spec(root: Path) -> None:
    lines = [
        "# Rookie Historical Label Spec V1 - 2026-06-30",
        "",
        "## Threshold Map",
        "",
        "- QB: T6, T12",
        "- RB: T6, T12, T24, T36",
        "- WR: T6, T12, T24, T36",
        "- TE: T6, T12",
        "",
        "## Horizon Labels",
        "",
        "- `rookie_year_top_6/12/24/36`",
        "- `year_2_top_6/12/24/36`",
        "- `first_3y_top_6/12/24/36`",
        "- `first_5y_top_6/12/24/36`",
        "",
        "## Definitions",
        "",
        "- Rookie year is NFL season equal to approved rookie class/draft year.",
        "- Year 2 is rookie class year plus one.",
        (
            "- First 3 years hits if the player reaches the threshold at least once "
            "from rookie year through year 3."
        ),
        (
            "- First 5 years hits if the player reaches the threshold at least once "
            "from rookie year through year 5."
        ),
        "",
        "## Censoring",
        "",
        "- Recent classes without full windows are `right_censored`.",
        "- Incomplete future windows must not be counted as misses.",
        f"- Missing labels must be `{NOT_ENOUGH}`, never `0%`.",
        "",
        "## Scoring",
        "",
        "- Prefer `exact_verified_first_downs` from factual NFL player-season data.",
        "- If exact scoring is unavailable, keep approximation modes separate.",
        "- Do not silently zero-fill missing scoring components unless source policy approves it.",
        "",
        "## Status",
        "",
        "This spec is ready for a future build, but no label artifact was generated",
        "because the draft-class/identity bridge is blocked.",
    ]
    (root / "03_ROOKIE_HISTORICAL_LABEL_SPEC.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_gate_c_decision(
    root: Path,
    bridge_rows: list[dict[str, str]],
    outcome_status: dict[str, object],
) -> None:
    linked = sum(
        row["nfl_outcome_label_link_status"] == "linked_to_review_only_outcome_labels"
        for row in bridge_rows
    )
    draft_year_rows = sum(row["draft_year"] != NOT_ENOUGH for row in bridge_rows)
    lines = [
        "# Gate C Historical Label Decision - 2026-06-30",
        "",
        "## Verdict",
        "",
        f"`{GATE_C_DECISION}`",
        "",
        "The NFL outcome target source is review-only green, and the label spec is",
        "defined. A historical rookie label artifact was not built because the lane",
        "does not have an approved historical rookie draft-class and GSIS outcome ID",
        "bridge.",
        "",
        "## Row Counts",
        "",
        f"- Bridge rows audited: {len(bridge_rows)}",
        f"- Rows linked to Outcome V2 labels: {linked}",
        f"- Rows with draft/rookie class year: {draft_year_rows}",
        "- Historical rookie label rows built: 0",
        "",
        "## Source-Policy Status",
        "",
        f"- Target source gate: `{TARGET_SOURCE_GATE}`",
        f"- Scoring mode available: `{outcome_status['scoring_mode']}`",
        (
            "- Exact vs approximate scoring: exact verified first downs available "
            "for Outcome V2 target source."
        ),
        "",
        "## Coverage",
        "",
        f"- Outcome target seasons: {outcome_status['season_min']}-{outcome_status['season_max']}",
        f"- Outcome target rows: {outcome_status['anchor_rows_count']}",
        f"- Complete 5Y rows: {outcome_status['complete_5y_rows']}",
        (
            "- Class/year coverage for rookie labels: blocked; no approved historical "
            "draft-class bridge."
        ),
        "- Position coverage for target source: QB/RB/WR/TE available in Outcome V2 labels.",
        "",
        "## Draft Capital / CFBD Limitations",
        "",
        "- Gate B draft capital is partial and current 2026 review-only context.",
        "- CFBD identities remain review-only and are not model/training inputs.",
        "- CFBD does not supply NFL outcome truth.",
        "",
        "## Gate D",
        "",
        "Gate D cannot run next. Required next blocker to clear: build an approved",
        "historical rookie draft-class and NFL outcome ID bridge.",
    ]
    (root / "04_GATE_C_HISTORICAL_LABEL_DECISION.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_readme(
    root: Path,
    bridge_rows: list[dict[str, str]],
    outcome_status: dict[str, object],
) -> None:
    lines = [
        "# Rookie Historical Labels V1 - 2026-06-30",
        "",
        f"Final Gate C verdict: `{GATE_C_DECISION}`",
        "",
        "## Created",
        "",
        "- `00_GATE_C_INVENTORY.md`",
        "- `01_CFBD_ROOKIE_BRIDGE_AUDIT.md`",
        "- `rookie_cfbd_to_nfl_bridge_matrix_v1.csv`",
        "- `02_HISTORICAL_NFL_OUTCOME_TARGET_SOURCE_GATE.md`",
        "- `03_ROOKIE_HISTORICAL_LABEL_SPEC.md`",
        "- `rookie_historical_label_coverage_matrix_v1.csv`",
        "- `04_GATE_C_HISTORICAL_LABEL_DECISION.md`",
        "",
        "## Summary",
        "",
        f"- Bridge rows audited: {len(bridge_rows)}",
        f"- Outcome target rows available externally: {outcome_status['anchor_rows_count']}",
        "- Historical rookie label artifact rows built: 0",
        "- Gate D status: blocked, not run.",
        "",
        "## Guardrails",
        "",
        "- No rookie probabilities.",
        "- No current-player outcome columns.",
        "- No Rankings wiring.",
        "- No model/training/source-truth promotion.",
    ]
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _label_link_status(nfl_player_id: str, draft_year: str, outcome_player_ids: set[str]) -> str:
    if nfl_player_id != NOT_ENOUGH and nfl_player_id in outcome_player_ids:
        return "linked_to_review_only_outcome_labels"
    if draft_year == "2026":
        return "not_linked_current_2026_outside_2012_2024_outcome_window"
    if draft_year == NOT_ENOUGH:
        return "not_linked_missing_draft_class_and_nfl_id"
    return "not_linked_missing_nfl_outcome_id"


def _bridge_blocker_reason(
    nfl_player_id: str,
    draft_year: str,
    rookie_class_year: str,
    link_status: str,
) -> str:
    if link_status == "linked_to_review_only_outcome_labels":
        return "Linked to review-only target labels; still not model/training approved."
    blockers: list[str] = []
    if nfl_player_id == NOT_ENOUGH:
        blockers.append("missing GSIS/NFL outcome player_id bridge")
    if draft_year == NOT_ENOUGH or rookie_class_year == NOT_ENOUGH:
        blockers.append("missing approved draft/rookie class year")
    if draft_year == "2026":
        blockers.append("current/future class outside 2012-2024 target-label window")
    return "; ".join(blockers) if blockers else "historical rookie bridge blocked"


def _coverage(metric: str, value: object, notes: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": str(value),
        "notes": notes,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


def _manifest_value(rows: list[dict[str, str]], field: str) -> str:
    values = {_clean(row.get(field)) for row in rows if _clean(row.get(field))}
    if not values:
        return NOT_ENOUGH
    return "|".join(sorted(values))


def _to_int(value: object) -> int | None:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _clean(value: object) -> str:
    return str(value or "").strip()


if __name__ == "__main__":
    raise SystemExit(main())
