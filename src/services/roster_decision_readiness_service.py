from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.command_board_service import build_team_command_board
from src.services.identity_audit_service import build_identity_audit
from src.services.legacy_label_quarantine_service import quarantine_legacy_label
from src.services.model_outlier_service import (
    build_model_outlier_report,
    is_review_required_bucket,
)
from src.services.model_recalibration_service import model_v4_rebuild_freeze_active
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    build_player_feature_receipts,
)
from src.services.player_lifecycle_service import is_young_nfl_bridge_lifecycle
from src.services.source_coverage_audit_service import build_source_coverage_audit

STATS_FIRST_OUTPUT_FILE = "stats_first_veteran_model_preview_outputs.csv"
OUTLIER_ACCEPTANCE_FILE = "model_outlier_acceptances.csv"
BRIDGE_RECEIPT_FEATURES = {
    "draft_capital_prior_score",
    "young_nfl_bridge_decay_weight",
    "young_nfl_bridge_nfl_evidence_weight",
    "young_nfl_bridge_prior",
}


@dataclass(frozen=True)
class RosterReadinessCheck:
    gate: str
    requirement: str
    status: str
    severity: str
    detail: str
    next_action: str


@dataclass(frozen=True)
class RosterDecisionReadinessReport:
    status: str
    badge: str
    passed: bool
    blocked_count: int
    review_count: int
    ready_count: int
    checks: tuple[RosterReadinessCheck, ...]
    my_team_id: str
    my_team_name: str


def build_roster_decision_readiness(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
    team_id: str = "niners",
) -> RosterDecisionReadinessReport:
    source_root = (
        Path(veteran_model_dir) if veteran_model_dir else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    validated = validate_data_pack(data_pack_path)
    roster_rows = validated.rows_by_table.get("rosters", [])
    my_roster_rows = _my_roster_rows(roster_rows, team_id)
    my_team_name = str(my_roster_rows[0].get("team_name") or team_id) if my_roster_rows else team_id
    roster_keys = _player_keys(my_roster_rows)
    checks = (
        _model_v4_rebuild_freeze_check(),
        _current_rosters_check(validated.has_errors, my_roster_rows),
        _league_ranks_check(validated.rows_by_table, my_roster_rows),
        _stats_first_outputs_check(source_root),
        _active_roster_output_quality_check(data_pack_path, team_id),
        _lifecycle_separation_check(data_pack_path, source_root),
        _critical_source_coverage_check(data_pack_path, source_root, roster_keys),
        _identity_audit_check(data_pack_path, source_root, roster_keys),
        _young_bridge_receipts_check(data_pack_path, source_root, roster_keys),
        _my_roster_outlier_check(data_pack_path, source_root, roster_keys),
    )
    blocked = sum(1 for check in checks if check.status == "blocked")
    review = sum(1 for check in checks if check.status == "review")
    ready = sum(1 for check in checks if check.status == "ready")
    status = "blocked" if blocked else "review" if review else "ready"
    return RosterDecisionReadinessReport(
        status=status,
        badge=_badge(status),
        passed=status == "ready",
        blocked_count=blocked,
        review_count=review,
        ready_count=ready,
        checks=checks,
        my_team_id=team_id,
        my_team_name=my_team_name,
    )


def roster_decision_summary_row(
    report: RosterDecisionReadinessReport,
) -> dict[str, object]:
    return {
        "roster_decision_badge": report.badge,
        "roster_decision_ready": report.passed,
        "status": report.status,
        "team": report.my_team_name,
        "blocked": report.blocked_count,
        "review": report.review_count,
        "ready": report.ready_count,
        "draft_day_note": (
            "Independent from final draft readiness; released veterans do not block this gate."
        ),
    }


def roster_decision_gate_rows(
    report: RosterDecisionReadinessReport,
) -> list[dict[str, object]]:
    return [
        {
            "requirement": check.requirement,
            "status": check.status,
            "severity": check.severity,
            "detail": check.detail,
            "next_action": check.next_action,
        }
        for check in report.checks
    ]


def _current_rosters_check(
    has_validation_errors: bool,
    my_roster_rows: list[dict[str, object]],
) -> RosterReadinessCheck:
    if has_validation_errors:
        return _check(
            "current_rosters_loaded",
            "Current rosters loaded",
            "blocked",
            "error",
            "The selected data pack has validation errors.",
            "Fix Import & Refresh validation errors before roster decisions.",
        )
    if not my_roster_rows:
        return _check(
            "current_rosters_loaded",
            "Current rosters loaded",
            "blocked",
            "error",
            "No roster rows were found for the selected team.",
            "Refresh Sleeper/import data and confirm the selected team id.",
        )
    return _check(
        "current_rosters_loaded",
        "Current rosters loaded",
        "ready",
        "info",
        f"{len(my_roster_rows)} roster rows loaded for the selected team.",
        "Keep roster snapshot frozen before declaration review.",
    )


def _model_v4_rebuild_freeze_check() -> RosterReadinessCheck:
    if not model_v4_rebuild_freeze_active():
        return _check(
            "model_v4_rebuild_freeze",
            "Model v4 rebuild freeze",
            "ready",
            "info",
            "Model v4 rebuild freeze is inactive.",
            "Continue normal roster-decision gates.",
        )
    return _check(
        "model_v4_rebuild_freeze",
        "Model v4 rebuild freeze",
        "review",
        "warning",
        (
            "Model v4 rebuild freeze is active. Legacy roster action buckets may "
            "be inspected, but they cannot be treated as trusted decisions."
        ),
        "Finish the v4 scoring lane, thresholds, receipts, and sanity fixtures.",
    )


def _league_ranks_check(
    rows_by_table: dict[str, list[dict[str, object]]],
    my_roster_rows: list[dict[str, object]],
) -> RosterReadinessCheck:
    ranked_roster_ids = {
        str(row.get("player_id") or "")
        for row in my_roster_rows
        if _rank_value(row) is not None
    }
    official_rows = rows_by_table.get("official_rankings", [])
    official_ranked_ids = {
        str(row.get("player_id") or "")
        for row in official_rows
        if _rank_value(row) is not None and not _boolish(row.get("is_rank_placeholder"))
    }
    my_ranked_ids = ranked_roster_ids.union(
        {
            str(row.get("player_id") or "")
            for row in my_roster_rows
            if str(row.get("player_id") or "") in official_ranked_ids
        }
    )
    if len(my_ranked_ids) < 5:
        return _check(
            "league_ranks_loaded",
            "League ranks loaded",
            "blocked",
            "error",
            f"Only {len(my_ranked_ids)} ranked players found for the selected roster.",
            "Merge the league-rank PDF/CSV before forced-release decisions.",
        )
    return _check(
        "league_ranks_loaded",
        "League ranks loaded",
        "ready",
        "info",
        f"{len(my_ranked_ids)} selected-roster players have league-rank coverage.",
        (
            "Use league rank only for the Roster's League-Rank Top Five rule, "
            "not player quality."
        ),
    )


def _stats_first_outputs_check(source_root: Path) -> RosterReadinessCheck:
    output_path = source_root / STATS_FIRST_OUTPUT_FILE
    rows = _read_optional_csv(output_path)
    if not rows:
        return _check(
            "stats_first_veteran_outputs_present",
            "Stats-first veteran outputs present",
            "blocked",
            "error",
            f"No stats-first model output rows found at {output_path}.",
            "Generate stats-first preview outputs before roster recommendations.",
        )
    return _check(
        "stats_first_veteran_outputs_present",
        "Stats-first veteran outputs present",
        "ready",
        "info",
        f"{len(rows)} stats-first veteran output rows are available.",
        "Keep outputs review-only until roster readiness passes.",
    )


def _active_roster_output_quality_check(
    data_pack_path: str | Path,
    team_id: str,
) -> RosterReadinessCheck:
    try:
        board = build_team_command_board(data_pack_path, team_id=team_id)
    except Exception as exc:  # pragma: no cover - defensive gate detail
        return _check(
            "active_roster_output_quality_review",
            "Active roster model output quality reviewed",
            "blocked",
            "error",
            f"Could not build active roster decision rows: {exc}",
            "Fix My Team board generation before calling roster decisions ready.",
        )
    review_rows = [
        row
        for row in board.roster_rows
        if str(row.get("team_section") or "") == "Needs Data Review"
        or _float(row.get("confidence"), 100.0) < 78.0
    ]
    if review_rows:
        names = ", ".join(str(row.get("player") or "") for row in review_rows[:5])
        suffix = "..." if len(review_rows) > 5 else ""
        return _check(
            "active_roster_output_quality_review",
            "Active roster model output quality reviewed",
            "review",
            "warning",
            (
                f"{len(review_rows)} selected-roster rows still need model/source "
                f"review: {names}{suffix}"
            ),
            (
                "Audit these rows before treating Core/Bubble/Shop labels as "
                "actionable roster calls."
            ),
        )
    return _check(
        "active_roster_output_quality_review",
        "Active roster model output quality reviewed",
        "ready",
        "info",
        "No selected-roster rows are in Needs Data Review or below usable confidence.",
        "Keep close-call receipts visible while reviewing drops/trades.",
    )


def _lifecycle_separation_check(
    data_pack_path: str | Path,
    source_root: Path,
) -> RosterReadinessCheck:
    receipt_report = build_player_feature_receipts(data_pack_path, veteran_model_dir=source_root)
    if receipt_report.issues:
        return _check(
            "lifecycle_model_separation_pass",
            "Lifecycle/model separation pass",
            "blocked",
            "error",
            "Lifecycle receipts could not be built: " + "; ".join(receipt_report.issues),
            "Fix receipts before trusting rookie/young/veteran separation.",
        )
    established_prior_rows = [
        row
        for row in receipt_report.rows
        if str(row.get("asset_lifecycle") or "") == "established_veteran"
        and str(row.get("formula_feature_name") or "") in BRIDGE_RECEIPT_FEATURES
        and (
            _float(row.get("feature_weight")) > 0.0
            or abs(_float(row.get("contribution"))) > 0.0001
        )
    ]
    if established_prior_rows:
        return _check(
            "lifecycle_model_separation_pass",
            "Lifecycle/model separation pass",
            "blocked",
            "error",
            f"{len(established_prior_rows)} established-veteran rows still score bridge prior.",
            "Remove draft-capital prior from established veteran receipts.",
        )
    return _check(
        "lifecycle_model_separation_pass",
        "Lifecycle/model separation pass",
        "ready",
        "info",
        "Established veterans do not score draft-capital prior in receipts.",
        "Keep lifecycle labels visible on My Team and War Board.",
    )


def _critical_source_coverage_check(
    data_pack_path: str | Path,
    source_root: Path,
    roster_keys: set[str],
) -> RosterReadinessCheck:
    report = build_source_coverage_audit(data_pack_path, veteran_model_dir=source_root)
    if report.issues:
        return _check(
            "source_coverage_critical_buckets_pass",
            "Critical source coverage passes",
            "blocked",
            "error",
            "Source coverage could not run: " + "; ".join(report.issues),
            "Repair source coverage files before roster decisions.",
        )
    missing = [row for row in report.missing_critical_rows if _row_matches(row, roster_keys)]
    blocked_players = [
        row
        for row in report.player_rows
        if _row_matches(row, roster_keys)
        and str(row.get("coverage_status") or "").startswith("blocked")
    ]
    if missing or blocked_players:
        return _check(
            "source_coverage_critical_buckets_pass",
            "Critical source coverage passes",
            "blocked",
            "error",
            (
                f"{len(missing)} selected-roster critical bucket gaps; "
                f"{len(blocked_players)} selected-roster players blocked by coverage."
            ),
            "Fill production, role/usage, age/bio, and identity coverage for my roster.",
        )
    return _check(
        "source_coverage_critical_buckets_pass",
        "Critical source coverage passes",
        "ready",
        "info",
        "No selected-roster critical source bucket gaps are blocking roster decisions.",
        "Optional projection, injury, and market gaps can remain review warnings.",
    )


def _identity_audit_check(
    data_pack_path: str | Path,
    source_root: Path,
    roster_keys: set[str],
) -> RosterReadinessCheck:
    report = build_identity_audit(data_pack_path, source_root=source_root)
    if report.issues:
        return _check(
            "identity_audit_pass",
            "Identity audit passes",
            "blocked",
            "error",
            "Identity audit could not run: " + "; ".join(report.issues),
            "Repair Sleeper-to-nflverse identity bridge files.",
        )
    blocked = [row for row in report.blocked_rows if _row_matches(row, roster_keys)]
    review = [
        row
        for row in report.rows
        if _row_matches(row, roster_keys) and row.get("audit_status") != "ready"
    ]
    if blocked:
        return _check(
            "identity_audit_pass",
            "Identity audit passes",
            "blocked",
            "error",
            f"{len(blocked)} selected-roster players are identity-blocked.",
            "Resolve identity joins before trusting stats-first roster decisions.",
        )
    if review:
        return _check(
            "identity_audit_pass",
            "Identity audit passes",
            "review",
            "warning",
            f"{len(review)} selected-roster identity rows need review.",
            "Review ambiguous identity joins before calling roster decisions ready.",
        )
    return _check(
        "identity_audit_pass",
        "Identity audit passes",
        "ready",
        "info",
        "Selected-roster identity joins pass.",
        "Keep manual identity overrides audited.",
    )


def _young_bridge_receipts_check(
    data_pack_path: str | Path,
    source_root: Path,
    roster_keys: set[str],
) -> RosterReadinessCheck:
    receipt_report = build_player_feature_receipts(data_pack_path, veteran_model_dir=source_root)
    roster_rows = [row for row in receipt_report.rows if _row_matches(row, roster_keys)]
    young_players: dict[str, list[dict[str, object]]] = {}
    for row in roster_rows:
        if is_young_nfl_bridge_lifecycle(row.get("asset_lifecycle")):
            young_players.setdefault(str(row.get("player") or ""), []).append(row)
    missing = [
        player
        for player, rows in young_players.items()
        if not BRIDGE_RECEIPT_FEATURES.issubset(
            {str(row.get("formula_feature_name") or "") for row in rows}
        )
    ]
    if missing:
        return _check(
            "young_bridge_receipts_visible",
            "Young bridge receipts visible",
            "blocked",
            "error",
            f"{len(missing)} selected-roster young bridge players lack full bridge receipts.",
            "Regenerate receipts with draft prior, decay, NFL evidence, and contribution rows.",
        )
    return _check(
        "young_bridge_receipts_visible",
        "Young bridge receipts visible",
        "ready",
        "info",
        f"{len(young_players)} selected-roster young bridge players show bridge receipts.",
        "Review bridge receipt rows for young players before declaration.",
    )


def _my_roster_outlier_check(
    data_pack_path: str | Path,
    source_root: Path,
    roster_keys: set[str],
) -> RosterReadinessCheck:
    report = build_model_outlier_report(data_pack_path, veteran_model_dir=source_root)
    if report.issues:
        return _check(
            "my_roster_outlier_review_resolved",
            "My-roster outlier review resolved/accepted",
            "blocked",
            "error",
            "Outlier report could not run: " + "; ".join(report.issues),
            "Fix receipt/outlier inputs before roster decisions.",
        )
    accepted = _accepted_outlier_keys(source_root / OUTLIER_ACCEPTANCE_FILE)
    review_required = [
        row
        for row in report.rows
        if _row_matches(row, roster_keys)
        and is_review_required_bucket(row.get("bucket"))
        and _outlier_key(row) not in accepted
    ]
    blocked = [
        row for row in review_required if str(row.get("severity") or "") in {"blocking", "high"}
    ]
    if blocked:
        return _check(
            "my_roster_outlier_review_resolved",
            "My-roster outlier review resolved/accepted",
            "blocked",
            "error",
            f"{len(blocked)} selected-roster high/blocking outliers need review.",
            "Resolve or explicitly accept my-roster ranking outliers.",
        )
    if review_required:
        return _check(
            "my_roster_outlier_review_resolved",
            "My-roster outlier review resolved/accepted",
            "review",
            "warning",
            f"{len(review_required)} selected-roster lower-severity outliers need review.",
            "Review or accept lower-severity my-roster outliers.",
        )
    return _check(
        "my_roster_outlier_review_resolved",
        "My-roster outlier review resolved/accepted",
        "ready",
        "info",
        "No unresolved selected-roster review-required outliers remain.",
        "Use outlier receipts as audit prompts, not hidden formula changes.",
    )


def _check(
    gate: str,
    requirement: str,
    status: str,
    severity: str,
    detail: str,
    next_action: str,
) -> RosterReadinessCheck:
    return RosterReadinessCheck(gate, requirement, status, severity, detail, next_action)


def _badge(status: str) -> str:
    if model_v4_rebuild_freeze_active():
        if status == "blocked":
            return "Roster Decisions Need Data"
        return quarantine_legacy_label("Roster Decisions Ready")
    if status == "ready":
        return "Roster Decisions Ready"
    if status == "blocked":
        return "Roster Decisions Need Data"
    return "Roster Decisions Need Review"


def _my_roster_rows(
    roster_rows: list[dict[str, object]],
    team_id: str,
) -> list[dict[str, object]]:
    requested = _key(team_id)
    matches = [row for row in roster_rows if _key(row.get("team_id")) == requested]
    if matches:
        return matches
    return [row for row in roster_rows if _key(row.get("team_name")) == requested]


def _player_keys(rows: list[dict[str, object]]) -> set[str]:
    keys: set[str] = set()
    for row in rows:
        player_id = str(row.get("player_id") or "")
        player = str(row.get("player") or row.get("player_name") or "")
        position = str(row.get("position") or row.get("pos") or "")
        if player_id:
            keys.add(f"id:{player_id}")
        if player and position:
            keys.add(f"name:{_key(player)}::{position}")
    return keys


def _row_matches(row: dict[str, object], roster_keys: set[str]) -> bool:
    player_id = str(row.get("player_id") or "")
    player = str(row.get("player") or row.get("player_name") or "")
    position = str(row.get("position") or row.get("pos") or "")
    return (player_id and f"id:{player_id}" in roster_keys) or (
        player and position and f"name:{_key(player)}::{position}" in roster_keys
    )


def _rank_value(row: dict[str, object]) -> int | None:
    for field in ("league_rank", "official_rank"):
        value = row.get(field)
        try:
            if value not in (None, ""):
                return int(float(str(value)))
        except (TypeError, ValueError):
            continue
    return None


def _accepted_outlier_keys(path: Path) -> set[tuple[str, str, str, str]]:
    rows = _read_optional_csv(path)
    return {
        (
            row.get("player_id", ""),
            row.get("outlier_type", ""),
            row.get("component", ""),
            row.get("source_feature", ""),
        )
        for row in rows
        if str(row.get("review_status") or "").lower() == "accepted"
    }


def _outlier_key(row: dict[str, object]) -> tuple[str, str, str, str]:
    return (
        str(row.get("player_id") or ""),
        str(row.get("outlier_type") or ""),
        str(row.get("component") or ""),
        str(row.get("source_feature") or ""),
    )


def _read_optional_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _key(value: object) -> str:
    return "".join(character.lower() for character in str(value or "") if character.isalnum())


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _boolish(value: object) -> bool:
    return str(value or "").lower() in {"1", "true", "yes", "y"}
