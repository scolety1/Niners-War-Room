from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.final_calibration_gate_service import (
    CalibrationGateCheck,
    FinalCalibrationGateReport,
    build_final_calibration_gate,
)
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    build_player_feature_receipts,
)
from src.services.roster_decision_readiness_service import (
    RosterDecisionReadinessReport,
    RosterReadinessCheck,
    build_roster_decision_readiness,
)


@dataclass(frozen=True)
class PreDecisionChecklistItem:
    item: str
    status: str
    severity: str
    decision_scope: str
    page: str
    section: str
    detail: str
    next_action: str


@dataclass(frozen=True)
class PreDecisionChecklistReport:
    status: str
    roster_decision_badge: str
    draft_badge: str
    final_money_badge: str
    roster_decisions_ready: bool
    draft_ready: bool
    final_money_ready: bool
    blocked_count: int
    review_count: int
    ready_count: int
    items: tuple[PreDecisionChecklistItem, ...]


CHECKLIST_LABELS: dict[str, str] = {
    "current_rosters_loaded": "Roster data",
    "league_ranks_loaded": "League ranks",
    "lifecycle_model_separation": "Lifecycle audit",
    "source_coverage_thresholds": "Source coverage",
    "identity_audit_pass": "Identity audit",
    "young_bridge_receipts_visible": "Young bridge receipts",
    "sanity_fixture_pass": "Named sanity fixtures",
    "ranking_outlier_review": "Outlier review",
    "my_team_receipt_review": "My team receipt review",
}

CHECKLIST_PAGE_SECTIONS: dict[str, tuple[str, str]] = {
    "current_rosters_loaded": ("Import & Refresh", "Pack Health"),
    "league_ranks_loaded": ("Import & Refresh", "League Rank Merge"),
    "lifecycle_model_separation": ("Model Lab", "Lifecycle"),
    "source_coverage_thresholds": ("Model Lab", "Coverage"),
    "identity_audit_pass": ("Model Lab", "Lifecycle / Identity"),
    "young_bridge_receipts_visible": ("Model Lab", "Young Players"),
    "sanity_fixture_pass": ("Model Lab", "Gate"),
    "ranking_outlier_review": ("Model Lab", "Outliers"),
    "my_team_receipt_review": ("My Team", "Why? receipts"),
}


def build_pre_decision_checklist(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
    team_id: str = "niners",
) -> PreDecisionChecklistReport:
    source_root = (
        Path(veteran_model_dir) if veteran_model_dir else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    calibration = build_final_calibration_gate(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    roster = build_roster_decision_readiness(
        data_pack_path,
        veteran_model_dir=source_root,
        team_id=team_id,
    )
    items = tuple(
        _checklist_items(
            data_pack_path,
            source_root,
            team_id,
            calibration,
            roster,
        )
    )
    blocked = sum(1 for item in items if item.status == "blocked")
    review = sum(1 for item in items if item.status == "review")
    ready = sum(1 for item in items if item.status == "ready")
    status = "blocked" if blocked else "review" if review else "ready"
    return PreDecisionChecklistReport(
        status=status,
        roster_decision_badge=roster.badge,
        draft_badge=calibration.draft_badge,
        final_money_badge=calibration.decision_badge,
        roster_decisions_ready=roster.passed,
        draft_ready=calibration.draft_passed,
        final_money_ready=calibration.passed,
        blocked_count=blocked,
        review_count=review,
        ready_count=ready,
        items=items,
    )


def pre_decision_checklist_summary_row(
    report: PreDecisionChecklistReport,
) -> dict[str, object]:
    return {
        "Roster Decisions Ready": report.roster_decision_badge,
        "Draft Ready": report.draft_badge,
        "Final Money Decisions Ready": report.final_money_badge,
        "blocked": report.blocked_count,
        "review": report.review_count,
        "ready": report.ready_count,
    }


def pre_decision_checklist_rows(
    report: PreDecisionChecklistReport,
) -> list[dict[str, object]]:
    return [
        {
            "check": item.item,
            "status": item.status,
            "severity": item.severity,
            "scope": item.decision_scope,
            "go_to": f"{item.page} > {item.section}",
            "detail": item.detail,
            "next_action": item.next_action,
        }
        for item in report.items
    ]


def _checklist_items(
    data_pack_path: str | Path,
    source_root: Path,
    team_id: str,
    calibration: FinalCalibrationGateReport,
    roster: RosterDecisionReadinessReport,
) -> list[PreDecisionChecklistItem]:
    roster_checks = {check.gate: check for check in roster.checks}
    calibration_checks = {check.gate: check for check in calibration.checks}
    items: list[PreDecisionChecklistItem] = []
    items.extend(
        _from_roster_check(
            roster_checks[gate],
            scope="Roster",
        )
        for gate in ("current_rosters_loaded", "league_ranks_loaded")
        if gate in roster_checks
    )
    for gate in (
        "lifecycle_model_separation",
        "source_coverage_thresholds",
        "identity_audit_pass",
        "sanity_fixture_pass",
        "ranking_outlier_review",
    ):
        if gate in calibration_checks:
            items.append(_from_calibration_check(calibration_checks[gate]))
    if "young_bridge_receipts_visible" in roster_checks:
        items.append(
            _from_roster_check(
                roster_checks["young_bridge_receipts_visible"],
                scope="Roster",
            )
        )
    items.append(_my_team_receipt_check(data_pack_path, source_root, team_id))
    return items


def _from_roster_check(
    check: RosterReadinessCheck,
    *,
    scope: str,
) -> PreDecisionChecklistItem:
    page, section = _page_section(check.gate)
    return PreDecisionChecklistItem(
        item=CHECKLIST_LABELS.get(check.gate, check.requirement),
        status=check.status,
        severity=check.severity,
        decision_scope=scope,
        page=page,
        section=section,
        detail=check.detail,
        next_action=check.next_action,
    )


def _from_calibration_check(check: CalibrationGateCheck) -> PreDecisionChecklistItem:
    page, section = _page_section(check.gate)
    return PreDecisionChecklistItem(
        item=CHECKLIST_LABELS.get(check.gate, check.gate.replace("_", " ").title()),
        status=check.status,
        severity=check.severity,
        decision_scope="Roster + Draft",
        page=page,
        section=section,
        detail=check.detail,
        next_action=check.next_action,
    )


def _my_team_receipt_check(
    data_pack_path: str | Path,
    source_root: Path,
    team_id: str,
) -> PreDecisionChecklistItem:
    page, section = _page_section("my_team_receipt_review")
    validated = validate_data_pack(data_pack_path)
    roster_rows = _my_roster_rows(
        validated.rows_by_table.get("rosters", []),
        team_id,
    )
    if validated.has_errors:
        return PreDecisionChecklistItem(
            "My team receipt review",
            "blocked",
            "error",
            "Roster",
            page,
            section,
            "The selected data pack has validation errors.",
            "Fix Import & Refresh validation before reviewing My Team receipts.",
        )
    if not roster_rows:
        return PreDecisionChecklistItem(
            "My team receipt review",
            "blocked",
            "error",
            "Roster",
            page,
            section,
            "No selected-team roster rows are available for receipt review.",
            "Refresh rosters and confirm the selected team id.",
        )
    receipt_report = build_player_feature_receipts(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    if receipt_report.issues:
        return PreDecisionChecklistItem(
            "My team receipt review",
            "blocked",
            "error",
            "Roster",
            page,
            section,
            "Player receipts could not be built: " + "; ".join(receipt_report.issues),
            "Fix receipt source files before trusting My Team decisions.",
        )
    receipt_keys = _receipt_player_keys(receipt_report.rows)
    missing_rows = [
        row
        for row in roster_rows
        if _player_match_keys(row).isdisjoint(receipt_keys)
    ]
    missing = [
        str(row.get("player") or row.get("player_name") or row.get("player_id") or "")
        for row in missing_rows
    ]
    if missing:
        return PreDecisionChecklistItem(
            "My team receipt review",
            "review",
            "warning",
            "Roster",
            page,
            section,
            f"{len(missing)} selected-roster players do not have visible receipt rows.",
            "Open My Team and Model Lab Receipts; regenerate receipts for missing players.",
        )
    return PreDecisionChecklistItem(
        "My team receipt review",
        "ready",
        "info",
        "Roster",
        page,
        section,
        f"{len(roster_rows)} selected-roster players have visible receipt rows.",
        "Review the Why? expanders for forced-release and bubble-player conflicts.",
    )


def _page_section(gate: str) -> tuple[str, str]:
    return CHECKLIST_PAGE_SECTIONS.get(gate, ("Model Lab", "Gate"))


def _my_roster_rows(
    roster_rows: list[dict[str, object]],
    team_id: str,
) -> list[dict[str, object]]:
    requested = _key(team_id)
    matches = [row for row in roster_rows if _key(row.get("team_id")) == requested]
    if matches:
        return matches
    return [row for row in roster_rows if _key(row.get("team_name")) == requested]


def _receipt_player_keys(rows: list[dict[str, object]]) -> set[str]:
    keys: set[str] = set()
    for row in rows:
        keys.update(_player_match_keys(row))
    return keys


def _player_match_keys(row: dict[str, object]) -> set[str]:
    keys: set[str] = set()
    player_id = str(row.get("player_id") or "")
    player = str(row.get("player") or row.get("player_name") or "")
    position = str(row.get("position") or row.get("pos") or "")
    if player_id:
        keys.add(f"id:{player_id}")
    if player and position:
        keys.add(f"name:{_player_name_key(player)}::{_key(position)}")
    return keys


def _key(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _player_name_key(value: object) -> str:
    suffix_tokens = {"jr", "sr", "ii", "iii", "iv", "v"}
    normalized = (
        str(value or "")
        .replace(".", " ")
        .replace("'", "")
        .replace("-", " ")
    )
    tokens = [
        "".join(character.lower() for character in token if character.isalnum())
        for token in normalized.split()
    ]
    tokens = [token for token in tokens if token]
    while tokens and tokens[-1] in suffix_tokens:
        tokens.pop()
    return "".join(tokens)
