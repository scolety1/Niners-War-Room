from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.model_v4_player_identity_crosswalk_service import (  # noqa: E402
    normalize_identity_name,
)

APPROVAL_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "cfbd_rookie_identity_approval_v1_20260629"
)
DRAFT_CAPITAL_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_capital_review_v1_20260629"
)
HISTORICAL_LABEL_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_historical_labels_v1_20260629"
)
ROOKIE_OVERLAY_PATH = (
    REPO_ROOT
    / "docs"
    / "draft_day_exports"
    / "final_board_v1_20260622"
    / "app_props"
    / "rookie_hq"
    / "rookie_overlay_context.csv"
)

NOT_ENOUGH = "Not enough information"
GATE_B_VERDICT = "PARTIAL_DRAFT_CAPITAL_REVIEW_ARTIFACT"
GATE_C_VERDICT = "BLOCKED_NEEDS_HISTORICAL_LABELS"

DRAFT_CAPITAL_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "cfbd_identity_approval_status",
    "human_decision",
    "draft_year",
    "draft_round",
    "overall_pick",
    "drafted_team",
    "udfa_status",
    "nfl_entry_status",
    "rookie_class_year",
    "age_at_draft",
    "source_file",
    "source_status",
    "source_provenance",
    "data_quality_status",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "blocker_reason",
)

MISSINGNESS_COLUMNS = (
    "field_name",
    "total_rows",
    "available_rows",
    "missing_rows",
    "coverage_pct",
    "notes",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

SOURCE_AUDIT_COLUMNS = (
    "source_name",
    "source_path",
    "scope",
    "availability_status",
    "approved_identity_rows_covered",
    "draft_year_available",
    "draft_round_available",
    "overall_pick_available",
    "drafted_team_available",
    "udfa_status_available",
    "age_at_draft_available",
    "historical_classes_available",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "gate_b_use_status",
    "blocker_reason",
    "safe_next_step",
)

LABEL_COVERAGE_COLUMNS = (
    "dataset_name",
    "source_path",
    "scope",
    "availability_status",
    "approved_for_label_build",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "blocker_reason",
    "safe_next_step",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build rookie draft capital review artifact and retry Gates C-G."
    )
    parser.add_argument("--approval-root", type=Path, default=APPROVAL_ROOT)
    parser.add_argument("--draft-capital-root", type=Path, default=DRAFT_CAPITAL_ROOT)
    parser.add_argument("--historical-label-root", type=Path, default=HISTORICAL_LABEL_ROOT)
    parser.add_argument("--rookie-overlay-path", type=Path, default=ROOKIE_OVERLAY_PATH)
    args = parser.parse_args()

    approval_rows = _read_rows(
        args.approval_root / "cfbd_rookie_identity_human_approval_v1.csv"
    )
    approved_rows = [row for row in approval_rows if _clean(row.get("approved_by_human")) == "true"]
    overlay_rows = _read_rows(args.rookie_overlay_path)
    draft_rows = build_draft_capital_review_rows(
        approval_rows=approved_rows,
        overlay_rows=overlay_rows,
        source_file=_relative(args.rookie_overlay_path),
    )
    validate_draft_capital_rows(draft_rows)

    source_audit_rows = build_gate_b_source_audit_rows(
        draft_rows=draft_rows,
        overlay_rows=overlay_rows,
    )
    missingness_rows = build_missingness_rows(draft_rows)
    label_coverage_rows = build_gate_c_label_coverage_rows(draft_rows)
    validate_review_flag_rows(source_audit_rows)
    validate_review_flag_rows(missingness_rows)
    validate_review_flag_rows(label_coverage_rows)

    args.draft_capital_root.mkdir(parents=True, exist_ok=True)
    args.historical_label_root.mkdir(parents=True, exist_ok=True)

    _write_csv(
        args.draft_capital_root / "rookie_draft_capital_review_artifact_v1.csv",
        DRAFT_CAPITAL_COLUMNS,
        draft_rows,
    )
    _write_csv(
        args.draft_capital_root / "rookie_draft_capital_missingness_matrix_v1.csv",
        MISSINGNESS_COLUMNS,
        missingness_rows,
    )
    _write_csv(
        args.draft_capital_root / "rookie_draft_capital_source_audit_v1.csv",
        SOURCE_AUDIT_COLUMNS,
        source_audit_rows,
    )
    _write_gate_b_summary(args.draft_capital_root, draft_rows, source_audit_rows)
    _write_gate_b_provenance(args.draft_capital_root, draft_rows, overlay_rows)
    _write_gate_b_readme(args.draft_capital_root, draft_rows)
    _write_superseded_gate_b_blocker(args.draft_capital_root, draft_rows)

    _write_csv(
        args.historical_label_root / "rookie_historical_label_coverage_matrix_v1.csv",
        LABEL_COVERAGE_COLUMNS,
        label_coverage_rows,
    )
    _write_gate_c_availability(args.historical_label_root, draft_rows, label_coverage_rows)
    _write_gate_c_blocker(args.historical_label_root, draft_rows, label_coverage_rows)
    _write_gate_c_readme(args.historical_label_root, draft_rows)

    print(
        {
            "gate_b": GATE_B_VERDICT,
            "approved_identity_rows": len(draft_rows),
            "draft_capital_rows_with_round_pick": _available_count(draft_rows, "overall_pick"),
            "gate_c": GATE_C_VERDICT,
        }
    )
    return 0


def build_draft_capital_review_rows(
    *,
    approval_rows: list[dict[str, str]],
    overlay_rows: list[dict[str, str]],
    source_file: str,
) -> list[dict[str, str]]:
    overlay_by_name_position = {
        (
            normalize_identity_name(_clean(row.get("player"))),
            _clean(row.get("position")).upper(),
        ): row
        for row in overlay_rows
        if _clean(row.get("player"))
    }

    output: list[dict[str, str]] = []
    for approval in approval_rows:
        key = (
            normalize_identity_name(_clean(approval.get("player_name"))),
            _clean(approval.get("position")).upper(),
        )
        overlay = overlay_by_name_position.get(key, {})
        capital_text = _clean(overlay.get("nfl_draft_capital_display_only"))
        parsed = parse_draft_capital_text(capital_text)
        has_capital = bool(parsed)
        output.append(
            {
                "player_id": _clean(approval.get("player_id")),
                "player_name": _clean(approval.get("player_name")),
                "position": _clean(approval.get("position")),
                "cfbd_identity_approval_status": _clean(approval.get("gate_a_status")),
                "human_decision": _clean(approval.get("human_decision")),
                "draft_year": "2026" if has_capital else NOT_ENOUGH,
                "draft_round": parsed.get("draft_round", NOT_ENOUGH),
                "overall_pick": parsed.get("overall_pick", NOT_ENOUGH),
                "drafted_team": _clean(overlay.get("nfl_team")) if has_capital else NOT_ENOUGH,
                "udfa_status": "false" if has_capital else NOT_ENOUGH,
                "nfl_entry_status": "drafted_review_only" if has_capital else NOT_ENOUGH,
                "rookie_class_year": "2026" if has_capital else NOT_ENOUGH,
                "age_at_draft": NOT_ENOUGH,
                "source_file": source_file if has_capital else NOT_ENOUGH,
                "source_status": (
                    "tracked_display_review_artifact_not_source_truth"
                    if has_capital
                    else "missing_tracked_draft_capital_for_identity"
                ),
                "source_provenance": (
                    "Derived from tracked Rookie HQ overlay display-only draft capital field; "
                    "raw source not committed; not source truth."
                    if has_capital
                    else "No tracked draft-capital row matched this approved identity."
                ),
                "data_quality_status": (
                    "PARTIAL_REVIEW_ONLY_DRAFT_CAPITAL_AVAILABLE"
                    if has_capital
                    else "MISSING_DRAFT_CAPITAL_REVIEW_REQUIRED"
                ),
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "blocker_reason": (
                    "review-only draft capital available; not model/training/source-truth"
                    if has_capital
                    else "No tracked review-only draft year/round/pick/team found."
                ),
            }
        )
    return output


def parse_draft_capital_text(value: str) -> dict[str, str]:
    text = _clean(value).lower()
    if not text or "unavailable" in text:
        return {}
    round_match = re.search(r"round\s*=\s*(\d+)", text)
    pick_match = re.search(r"pick\s*=\s*(\d+)", text)
    if not round_match or not pick_match:
        return {}
    return {
        "draft_round": round_match.group(1),
        "overall_pick": pick_match.group(1),
    }


def validate_draft_capital_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != 157:
        raise ValueError(f"Expected 157 approved identity rows; found {len(rows)}.")
    for row in rows:
        missing = [column for column in DRAFT_CAPITAL_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"Draft capital artifact missing columns: {missing}")
        if row["review_only"] != "true":
            raise ValueError("Draft capital rows must keep review_only=true.")
        if row["model_use_allowed"] != "false":
            raise ValueError("Draft capital rows must keep model_use_allowed=false.")
        if row["training_allowed"] != "false":
            raise ValueError("Draft capital rows must keep training_allowed=false.")
        if "0%" in ",".join(row.values()):
            raise ValueError("Missing draft capital must not be represented as 0%.")


def build_missingness_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    fields = (
        "draft_year",
        "draft_round",
        "overall_pick",
        "drafted_team",
        "udfa_status",
        "nfl_entry_status",
        "rookie_class_year",
        "age_at_draft",
    )
    total = len(rows)
    output: list[dict[str, str]] = []
    for field in fields:
        available = _available_count(rows, field)
        output.append(
            {
                "field_name": field,
                "total_rows": str(total),
                "available_rows": str(available),
                "missing_rows": str(total - available),
                "coverage_pct": f"{(available / total * 100):.1f}" if total else "0.0",
                "notes": _missingness_note(field, available, total),
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def build_gate_b_source_audit_rows(
    *,
    draft_rows: list[dict[str, str]],
    overlay_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    covered = _available_count(draft_rows, "overall_pick")
    total = len(draft_rows)
    return [
        {
            "source_name": "Rookie HQ overlay display draft capital",
            "source_path": _relative(ROOKIE_OVERLAY_PATH),
            "scope": "tracked display-only draft capital fields for current rookie board rows",
            "availability_status": "partial_tracked_review_display",
            "approved_identity_rows_covered": str(covered),
            "draft_year_available": "derived_2026_for_matched_rows",
            "draft_round_available": f"{covered}/{total}",
            "overall_pick_available": f"{covered}/{total}",
            "drafted_team_available": f"{covered}/{total}",
            "udfa_status_available": "not_explicit; false only when round/pick present",
            "age_at_draft_available": "false",
            "historical_classes_available": "false",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "gate_b_use_status": GATE_B_VERDICT,
            "blocker_reason": "Covers only matched display rows and is not source truth.",
            "safe_next_step": "Create official/provenance-backed draft capital artifact.",
        },
        {
            "source_name": "Rookie overlay source row count",
            "source_path": _relative(ROOKIE_OVERLAY_PATH),
            "scope": "row-count provenance for tracked display source",
            "availability_status": "tracked_review_display",
            "approved_identity_rows_covered": str(len(overlay_rows)),
            "draft_year_available": "partial",
            "draft_round_available": "partial",
            "overall_pick_available": "partial",
            "drafted_team_available": "partial",
            "udfa_status_available": "false",
            "age_at_draft_available": "false",
            "historical_classes_available": "false",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "gate_b_use_status": "source_context_only",
            "blocker_reason": "Display source does not cover all approved identities.",
            "safe_next_step": "Backfill missing identities from approved factual draft source.",
        },
        {
            "source_name": "Documented 2026 draft-capital snapshot",
            "source_path": "docs/model_v4/ROOKIE_DRAFT_CAPITAL_2026_SNAPSHOT.md",
            "scope": "documented local-only 2026 draft-capital snapshot",
            "availability_status": "documented_but_processed_source_unavailable_here",
            "approved_identity_rows_covered": "0",
            "draft_year_available": "documented",
            "draft_round_available": "documented",
            "overall_pick_available": "documented",
            "drafted_team_available": "not_documented_in_summary",
            "udfa_status_available": "false",
            "age_at_draft_available": "false",
            "historical_classes_available": "false",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "gate_b_use_status": "not_used_processed_source_unavailable",
            "blocker_reason": (
                "The processed local file is not present; raw source was not committed."
            ),
            "safe_next_step": (
                "Rebuild a provenance-backed review artifact from available source files."
            ),
        },
        {
            "source_name": "Historical rookie draft capital",
            "source_path": NOT_ENOUGH,
            "scope": "historical rookie classes needed for labels/modeling",
            "availability_status": "missing",
            "approved_identity_rows_covered": "0",
            "draft_year_available": "false",
            "draft_round_available": "false",
            "overall_pick_available": "false",
            "drafted_team_available": "false",
            "udfa_status_available": "false",
            "age_at_draft_available": "false",
            "historical_classes_available": "false",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "gate_b_use_status": "blocked_missing_historical_draft_capital",
            "blocker_reason": "No approved historical class draft-capital source exists.",
            "safe_next_step": (
                "Build historical draft-capital review artifact with source provenance."
            ),
        },
    ]


def build_gate_c_label_coverage_rows(
    draft_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    covered = _available_count(draft_rows, "overall_pick")
    total = len(draft_rows)
    return [
        {
            "dataset_name": "Gate B current rookie draft-capital review artifact",
            "source_path": (
                "docs/hq/rookie_outcomes/rookie_draft_capital_review_v1_20260629/"
                "rookie_draft_capital_review_artifact_v1.csv"
            ),
            "scope": "current approved identity rows only",
            "availability_status": f"partial_current_only_{covered}_of_{total}",
            "approved_for_label_build": "false",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "blocker_reason": "Current 2026 review rows do not create historical labels.",
            "safe_next_step": "Create historical rookie identity and draft-capital bridge.",
        },
        {
            "dataset_name": "Historical rookie outcome labels",
            "source_path": NOT_ENOUGH,
            "scope": "rookie-year, year-2, first-3Y, first-5Y labels",
            "availability_status": "missing",
            "approved_for_label_build": "false",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "blocker_reason": "No approved historical fantasy scoring/finish label source exists.",
            "safe_next_step": "Build labels from approved factual NFL historical data only.",
        },
        {
            "dataset_name": "Prototype/vendor-derived rookie labels",
            "source_path": "src/services/model_v4_rookie_outcome_label_service.py",
            "scope": "old prototype service",
            "availability_status": "blocked_policy",
            "approved_for_label_build": "false",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "blocker_reason": "Prototype depends on unapproved local/vendor-derived context.",
            "safe_next_step": "Replace with approved public/local factual label build.",
        },
    ]


def validate_review_flag_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row.get("review_only") != "true":
            raise ValueError("All gate rows must keep review_only=true.")
        if row.get("model_use_allowed") != "false":
            raise ValueError("All gate rows must keep model_use_allowed=false.")
        if row.get("training_allowed") != "false":
            raise ValueError("All gate rows must keep training_allowed=false.")


def _write_gate_b_summary(
    root: Path,
    draft_rows: list[dict[str, str]],
    source_audit_rows: list[dict[str, str]],
) -> None:
    covered = _available_count(draft_rows, "overall_pick")
    missing = len(draft_rows) - covered
    by_status = Counter(row["data_quality_status"] for row in draft_rows)
    lines = [
        "# Rookie Draft Capital Review Artifact V1 Summary - 2026-06-29",
        "",
        "## Gate B Result",
        "",
        f"`{GATE_B_VERDICT}`",
        "",
        "A tracked review-only draft-capital artifact was created from tracked",
        "display/review artifacts. Coverage is partial, so it is not source truth",
        "and not usable for model/training gates.",
        "",
        "## Coverage",
        "",
        f"- Approved Gate-A identity rows: {len(draft_rows)}",
        f"- Rows with tracked round/pick/team: {covered}",
        f"- Rows still missing draft capital: {missing}",
        "- Rows approved for model use: 0",
        "- Rows approved for training use: 0",
        "",
        "## Data Quality Status",
        "",
        *[f"- {key}: {value}" for key, value in sorted(by_status.items())],
        "",
        "## Sources Audited",
        "",
        *[
            f"- {row['source_name']}: {row['gate_b_use_status']}"
            for row in source_audit_rows
        ],
        "",
        "## Stop/Continue Decision",
        "",
        "Gate B is partial, so Gate C was retried as an audit only. Gate C blocks",
        "because historical rookie labels are not available from approved sources.",
    ]
    (root / "ROOKIE_DRAFT_CAPITAL_REVIEW_ARTIFACT_V1_SUMMARY.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_gate_b_provenance(
    root: Path,
    draft_rows: list[dict[str, str]],
    overlay_rows: list[dict[str, str]],
) -> None:
    lines = [
        "# Rookie Draft Capital Provenance V1 - 2026-06-29",
        "",
        "## Source Chain",
        "",
        "- Input identity approval: tracked CFBD rookie identity approval V1.",
        "- Draft-capital source used: tracked Rookie HQ overlay display artifact.",
        "- Raw/source-cache files were not committed.",
        "- The artifact is review-only and not source truth.",
        "",
        "## Row Counts",
        "",
        f"- Approved identity rows inspected: {len(draft_rows)}",
        f"- Tracked overlay source rows inspected: {len(overlay_rows)}",
        f"- Rows with parsed round/pick/team: {_available_count(draft_rows, 'overall_pick')}",
        "",
        "## Parsing Rules",
        "",
        "- Parsed `round=<number>; pick=<number>` text from the display-only field.",
        "- Assigned `draft_year=2026` only where round/pick was parsed.",
        "- Assigned drafted team only from the same tracked display row.",
        "- Left missing values as `Not enough information`.",
        "",
        "## Review-Only Warning",
        "",
        "These rows do not authorize model input, training truth, Rankings columns,",
        "Dynasty Rank changes, tier changes, trade values, pick values, or source-truth",
        "promotion.",
    ]
    (root / "ROOKIE_DRAFT_CAPITAL_PROVENANCE_V1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_gate_b_readme(root: Path, draft_rows: list[dict[str, str]]) -> None:
    covered = _available_count(draft_rows, "overall_pick")
    lines = [
        "# Rookie Draft Capital Review V1",
        "",
        f"Gate B result: `{GATE_B_VERDICT}`",
        "",
        "This folder now contains a partial tracked, review-only draft-capital",
        "artifact for Gate-A-approved CFBD rookie identities.",
        "",
        "## Files",
        "",
        "- `rookie_draft_capital_review_artifact_v1.csv`",
        "- `ROOKIE_DRAFT_CAPITAL_REVIEW_ARTIFACT_V1_SUMMARY.md`",
        "- `ROOKIE_DRAFT_CAPITAL_PROVENANCE_V1.md`",
        "- `rookie_draft_capital_missingness_matrix_v1.csv`",
        "- `rookie_draft_capital_source_audit_v1.csv`",
        "",
        "## Counts",
        "",
        f"- Total approved identity rows: {len(draft_rows)}",
        f"- Rows with review-only draft capital: {covered}",
        f"- Rows missing draft capital: {len(draft_rows) - covered}",
        "",
        "## Guardrails",
        "",
        "- All rows remain `review_only=true`.",
        "- All rows remain `model_use_allowed=false`.",
        "- All rows remain `training_allowed=false`.",
        "- Missing data remains `Not enough information`, never `0%`.",
    ]
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_superseded_gate_b_blocker(root: Path, draft_rows: list[dict[str, str]]) -> None:
    covered = _available_count(draft_rows, "overall_pick")
    lines = [
        "# Gate B Draft Capital Blocker - Superseded 2026-06-29",
        "",
        "This file is retained as a historical checkpoint. The current Gate B result",
        f"is `{GATE_B_VERDICT}` because a partial tracked review-only artifact now",
        "exists.",
        "",
        "## Current Coverage",
        "",
        f"- Approved identity rows: {len(draft_rows)}",
        f"- Rows with round/pick/team: {covered}",
        f"- Rows still missing draft capital: {len(draft_rows) - covered}",
        "",
        "## Remaining Blocker",
        "",
        "Gate C remains blocked because approved historical rookie outcome labels are",
        "not available.",
    ]
    (root / "00_GATE_B_DRAFT_CAPITAL_BLOCKER.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_gate_c_availability(
    root: Path,
    draft_rows: list[dict[str, str]],
    label_coverage_rows: list[dict[str, str]],
) -> None:
    lines = [
        "# Rookie Historical Label Availability V1 - 2026-06-29",
        "",
        "## Gate C Result",
        "",
        f"`{GATE_C_VERDICT}`",
        "",
        "The partial Gate B artifact covers current 2026 review rows only. It does",
        "not supply historical rookie outcome labels, position finishes, fantasy",
        "scoring, or censoring-ready training labels.",
        "",
        "## Current Draft-Capital Coverage",
        "",
        f"- Approved identity rows: {len(draft_rows)}",
        f"- Rows with review-only draft capital: {_available_count(draft_rows, 'overall_pick')}",
        "",
        "## Sources Audited",
        "",
        *[
            f"- {row['dataset_name']}: {row['availability_status']}"
            for row in label_coverage_rows
        ],
    ]
    (root / "ROOKIE_HISTORICAL_LABEL_AVAILABILITY_V1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_gate_c_blocker(
    root: Path,
    draft_rows: list[dict[str, str]],
    label_coverage_rows: list[dict[str, str]],
) -> None:
    lines = [
        "# Gate C Historical Rookie Label Blocker - 2026-06-29",
        "",
        "## Gate Result",
        "",
        f"`{GATE_C_VERDICT}`",
        "",
        "Gate C cannot build rookie-year, year-2, first-3Y, or first-5Y outcome",
        "labels because approved historical label sources are missing.",
        "",
        "## Evidence",
        "",
        f"- Gate B approved identity rows inspected: {len(draft_rows)}",
        f"- Gate B rows with current draft capital: {_available_count(draft_rows, 'overall_pick')}",
        "- Historical fantasy scoring/position-finish labels: missing.",
        "- First-down scoring exactness: not established for historical labels.",
        "- Old prototype/vendor-derived labels remain blocked by policy.",
        "",
        "## Source Audit",
        "",
        *[
            f"- {row['dataset_name']}: {row['blocker_reason']}"
            for row in label_coverage_rows
        ],
        "",
        "## Stop Decision",
        "",
        "The lane stops at Gate C. Gates D-G were not run, no model/probability",
        "artifact was built, and Rankings was not touched.",
    ]
    (root / "00_GATE_C_HISTORICAL_LABEL_BLOCKER.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_gate_c_readme(root: Path, draft_rows: list[dict[str, str]]) -> None:
    lines = [
        "# Rookie Historical Labels V1",
        "",
        f"Gate C result: `{GATE_C_VERDICT}`",
        "",
        "This folder documents the historical-label retry after the partial Gate B",
        "draft-capital artifact. No labels were built.",
        "",
        "## Files",
        "",
        "- `00_GATE_C_HISTORICAL_LABEL_BLOCKER.md`",
        "- `ROOKIE_HISTORICAL_LABEL_AVAILABILITY_V1.md`",
        "- `rookie_historical_label_coverage_matrix_v1.csv`",
        "",
        "## Guardrails",
        "",
        "- No rookie probabilities were created.",
        "- No rookie outcome columns were created.",
        "- No Rankings integration was attempted.",
        f"- Current draft-capital coverage is {_available_count(draft_rows, 'overall_pick')}/"
        f"{len(draft_rows)} rows and remains review-only.",
    ]
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _missingness_note(field: str, available: int, total: int) -> str:
    if field == "age_at_draft":
        return "No approved age-at-draft source in Gate B artifact."
    if available == total:
        return "Available for every row with tracked draft capital."
    if available == 0:
        return "Missing for all rows."
    return "Partial coverage; missing rows remain Not enough information."


def _available_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(_clean(row.get(field)) not in {"", NOT_ENOUGH} for row in rows)


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
