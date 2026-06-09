from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.navigation import VISIBLE_NAVIGATION_PAGES, app_page_path
from src.services.draft_service import build_draft_room
from src.services.draft_ux_service import DRAFT_TOTAL_PICKS, build_draft_ux_contract
from src.services.historical_rookie_replay_service import (
    NO_FUTURE_STATS_POLICY,
    build_historical_rookie_replay_report,
)
from src.services.identity_audit_service import build_identity_audit
from src.services.lve_stats_first_calibration_service import (
    build_stats_first_calibration_report,
    stats_first_calibration_readiness_rows,
)
from src.services.lve_stats_first_preview_service import DEFAULT_STATS_FIRST_PREVIEW_ROOT
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

DEFAULT_HISTORICAL_ROOKIE_PREDRAFT_PATH = Path(
    "sample_data/historical_rookie_replay/pre_draft_prospect_inputs.csv"
)
DEFAULT_HISTORICAL_ROOKIE_OUTCOME_PATH = Path(
    "sample_data/historical_rookie_replay/post_draft_outcomes.csv"
)
DECISION_GATE_LABELS: dict[str, str] = {
    "model_v4_rebuild_freeze": "Model v4 Rebuild Freeze",
    "real_draft_pool_loaded": "Draft Pool Loaded",
    "source_coverage_thresholds": "Source Coverage Clear",
    "identity_audit_pass": "Identity Audit Pass",
    "lifecycle_model_separation": "Lifecycle/Model Separation Pass",
    "sanity_fixture_pass": "Named Sanity Fixtures Pass",
    "ranking_outlier_review": "Outlier Review Accepted/Resolved",
    "rookie_replay_no_leakage_pass": "Rookie Replay No-Leakage Pass",
    "final_ui_smoke_pass": "Core App Pages Load",
    "draft_ux_smoke_pass": "Draft UX Smoke Pass",
}

DECISION_GATE_REQUIREMENTS: dict[str, str] = {
    "model_v4_rebuild_freeze": (
        "Legacy scoring, action labels, and readiness gates stay audit-only until "
        "the v4 model spec, fixtures, and scoring lane are rebuilt."
    ),
    "real_draft_pool_loaded": (
        "Rookies, free agents, manual draftables, and eventually released veterans "
        "must be separated from protected roster players."
    ),
    "source_coverage_thresholds": (
        "The model needs enough production, role/usage, age/bio, and identity data "
        "to avoid fake confidence."
    ),
    "identity_audit_pass": (
        "Sleeper players must map cleanly to the stats/player identity used by the model."
    ),
    "lifecycle_model_separation": (
        "Incoming rookies, young NFL bridge assets, and established veterans must use "
        "the correct scoring lane."
    ),
    "sanity_fixture_pass": (
        "Named football sanity checks must pass before surprising rankings can be trusted."
    ),
    "ranking_outlier_review": (
        "High-risk weird rankings must be fixed or explicitly accepted with an audit trail."
    ),
    "rookie_replay_no_leakage_pass": (
        "Historical rookie replay must prove it ranks prospects without future NFL stats."
    ),
    "final_ui_smoke_pass": "The decision pages must exist and be loadable.",
    "draft_ux_smoke_pass": (
        "Rankings and Draft Board must support the live/mock draft workflow."
    ),
}


@dataclass(frozen=True)
class CalibrationGateCheck:
    gate: str
    status: str
    severity: str
    detail: str
    next_action: str


@dataclass(frozen=True)
class FinalCalibrationGateReport:
    status: str
    badge: str
    decision_badge: str
    passed: bool
    blocked_count: int
    review_count: int
    ready_count: int
    checks: tuple[CalibrationGateCheck, ...]
    pre_declaration_passed: bool = False
    pre_declaration_badge: str = "Review Only"
    draft_passed: bool = False
    draft_badge: str = "Review Only"


def build_final_calibration_gate(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
    identity_source_root: str | Path | None = None,
    stats_first_preview_root: str | Path = DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    historical_rookie_predraft_path: str | Path = DEFAULT_HISTORICAL_ROOKIE_PREDRAFT_PATH,
    historical_rookie_outcome_path: str | Path = DEFAULT_HISTORICAL_ROOKIE_OUTCOME_PATH,
    app_dir: str | Path | None = None,
) -> FinalCalibrationGateReport:
    source_root = (
        Path(veteran_model_dir)
        if veteran_model_dir
        else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    checks = (
        _model_v4_rebuild_freeze_gate(),
        _real_draft_pool_gate(data_pack_path),
        _source_coverage_gate(data_pack_path, source_root),
        _identity_audit_gate(
            data_pack_path,
            Path(identity_source_root) if identity_source_root else source_root,
        ),
        _lifecycle_model_separation_gate(data_pack_path, source_root),
        _sanity_fixture_gate(stats_first_preview_root),
        _ranking_outlier_gate(data_pack_path, source_root),
        _rookie_replay_no_leakage_gate(
            historical_rookie_predraft_path,
            historical_rookie_outcome_path,
        ),
        _final_ui_smoke_gate(app_dir),
        _draft_ux_smoke_gate(data_pack_path),
    )
    blocked = sum(1 for check in checks if check.status == "blocked")
    review = sum(1 for check in checks if check.status == "review")
    ready = sum(1 for check in checks if check.status == "ready")
    status = "blocked" if blocked else "review" if review else "ready"
    pre_declaration_passed = _pre_declaration_passed(checks)
    draft_passed = status == "ready"
    return FinalCalibrationGateReport(
        status=status,
        badge=_badge(status),
        decision_badge=_decision_badge(status, checks),
        passed=draft_passed,
        blocked_count=blocked,
        review_count=review,
        ready_count=ready,
        checks=checks,
        pre_declaration_passed=pre_declaration_passed,
        pre_declaration_badge=_pre_declaration_badge(pre_declaration_passed, checks),
        draft_passed=draft_passed,
        draft_badge=_draft_badge(draft_passed, checks),
    )


def final_calibration_gate_summary_row(
    report: FinalCalibrationGateReport,
) -> dict[str, object]:
    return {
        "summary_badge": report.decision_badge,
        "calibration_status": report.status,
        "calibration_badge": report.badge,
        "final_decision_badge": report.decision_badge,
        "model_calibration_passed": report.passed,
        "pre_declaration_decision_badge": report.pre_declaration_badge,
        "pre_declaration_decision_ready": report.pre_declaration_passed,
        "draft_decision_badge": report.draft_badge,
        "draft_decision_ready": report.draft_passed,
        "blocked": report.blocked_count,
        "review": report.review_count,
        "ready": report.ready_count,
        "decision_ready_gate": "pass" if report.passed else "hold",
        "next_action": _overall_next_action(report.status),
    }


def final_calibration_gate_rows(
    report: FinalCalibrationGateReport,
) -> list[dict[str, object]]:
    return [
        {
            "gate": check.gate,
            "requirement": _gate_label(check.gate),
            "status": check.status,
            "severity": check.severity,
            "blocker": _gate_blocker(check),
            "why_it_matters": _gate_why_it_matters(check.gate),
            "detail": check.detail,
            "next_action": check.next_action,
        }
        for check in report.checks
    ]


def _gate_label(gate: str) -> str:
    return DECISION_GATE_LABELS.get(gate, gate.replace("_", " ").title())


def _gate_why_it_matters(gate: str) -> str:
    return DECISION_GATE_REQUIREMENTS.get(
        gate,
        "This gate protects against using rankings before their assumptions are auditable.",
    )


def _gate_blocker(check: CalibrationGateCheck) -> str:
    if check.status == "ready":
        return "No blocker."
    if check.status == "review":
        return f"Needs review: {_gate_label(check.gate)}."
    return f"Blocked: {_gate_label(check.gate)}."


def _model_v4_rebuild_freeze_gate() -> CalibrationGateCheck:
    if not model_v4_rebuild_freeze_active():
        return CalibrationGateCheck(
            gate="model_v4_rebuild_freeze",
            status="ready",
            severity="info",
            detail="Model v4 rebuild freeze is inactive.",
            next_action="Continue normal readiness gates.",
        )
    return CalibrationGateCheck(
        gate="model_v4_rebuild_freeze",
        status="review",
        severity="warning",
        detail=(
            "Model v4 rebuild freeze is active. Legacy rankings may be inspected, "
            "but legacy action labels and readiness badges cannot be trusted."
        ),
        next_action=(
            "Finish Model v4 Sprint 0, source contract, sanity fixtures, and the "
            "new scoring lane before restoring readiness labels."
        ),
    )


def _real_draft_pool_gate(data_pack_path: str | Path) -> CalibrationGateCheck:
    board = build_draft_room(data_pack_path)
    required_sources = [
        row for row in board.available_pool_source_rows if bool(row["required"])
    ]
    missing_released_veterans = [
        row
        for row in required_sources
        if row["source"] == "released veterans" and row["status"] != "loaded"
    ]
    missing_required = [
        row
        for row in required_sources
        if row["status"] != "loaded" and row["source"] != "released veterans"
    ]
    review_only_sources = [
        row for row in required_sources if bool(row.get("review_only"))
    ]
    blocking_warnings = [
        warning
        for warning in board.available_pool_warnings
        if "no released veterans" not in warning.lower()
    ]
    if missing_required or review_only_sources or blocking_warnings:
        details = []
        if missing_required:
            details.append(
                "missing required pool sources: "
                + ", ".join(str(row["source"]) for row in missing_required)
            )
        if review_only_sources:
            details.append(
                "review-only/demo pool sources: "
                + ", ".join(str(row["source"]) for row in review_only_sources)
            )
        if blocking_warnings:
            details.append("; ".join(blocking_warnings))
        return CalibrationGateCheck(
            gate="real_draft_pool_loaded",
            status="blocked",
            severity="error",
            detail="; ".join(details),
            next_action=(
                "Load real rookie and free-agent draftable pools before draft-board "
                "labels or final draft freeze. Official released veterans can be "
                "added later when declarations are available."
            ),
        )
    if missing_released_veterans:
        return CalibrationGateCheck(
            gate="real_draft_pool_loaded",
            status="review",
            severity="warning",
            detail=(
                "Official released veterans are not loaded yet. Roster-declaration "
                "drop/shop decisions can still be reviewed, but the mixed offline "
                "draft board is not draft-ready until declared releases are imported."
            ),
            next_action=(
                "Use My Team and War Board for pre-declaration keep/drop/shop review. "
                "After declarations, import released veterans and rerun the draft "
                "pool preview before live draft use."
            ),
        )
    return CalibrationGateCheck(
        gate="real_draft_pool_loaded",
        status="ready",
        severity="info",
        detail=(
            f"{len(board.rookie_rows)} rookies, "
            f"{len(board.released_veteran_rows)} available veterans/free agents, "
            f"and {len(board.manual_draftable_rows)} manual draftables loaded."
        ),
        next_action="Keep draftable pool files frozen before the live draft.",
    )


def _source_coverage_gate(data_pack_path: str | Path, source_root: Path) -> CalibrationGateCheck:
    report = build_source_coverage_audit(data_pack_path, veteran_model_dir=source_root)
    if report.issues:
        return CalibrationGateCheck(
            gate="source_coverage_thresholds",
            status="blocked",
            severity="error",
            detail="Source coverage could not be built: " + "; ".join(report.issues),
            next_action="Fix veteran source fixtures before trusting model rankings.",
        )
    blocked_players = [
        row for row in report.player_rows if str(row["coverage_status"]).startswith("blocked")
    ]
    blocking_missing_rows = list(report.missing_critical_rows)
    review_gap_rows = list(getattr(report, "review_gap_rows", []))
    accepted_review_gap_rows = list(getattr(report, "accepted_review_gap_rows", []))
    invalid_gap_acceptance_rows = list(getattr(report, "invalid_gap_acceptance_rows", []))
    if invalid_gap_acceptance_rows:
        return CalibrationGateCheck(
            gate="source_coverage_thresholds",
            status="blocked",
            severity="error",
            detail=(
                f"{len(invalid_gap_acceptance_rows)} source gap acceptance rows "
                "are invalid."
            ),
            next_action=(
                "Fix source_coverage_gap_acceptances.csv. Optional gap acceptance "
                "requires bucket/gap_type, reason, reviewer, timestamp, and "
                "confidence_penalty_retained=true."
            ),
        )
    if blocking_missing_rows or blocked_players:
        return CalibrationGateCheck(
            gate="source_coverage_thresholds",
            status="blocked",
            severity="error",
            detail=(
                f"{len(blocking_missing_rows)} critical source bucket gaps; "
                f"{len(review_gap_rows)} unaccepted review-only gaps; "
                f"{len(accepted_review_gap_rows)} accepted review-only gaps; "
                f"{len(blocked_players)} players blocked by coverage."
            ),
            next_action=(
                "Fill critical production, role/usage, age/bio, and identity inputs "
                "before trusting model rankings. Projection, injury, and market gaps "
                "are review/acceptance items and still lower confidence."
            ),
        )
    if review_gap_rows:
        return CalibrationGateCheck(
            gate="source_coverage_thresholds",
            status="review",
            severity="warning",
            detail=(
                f"{len(review_gap_rows)} unaccepted review-only source gaps "
                f"remain ({_bucket_gap_summary(review_gap_rows)}); "
                f"{len(accepted_review_gap_rows)} "
                "review-only gaps have been accepted."
            ),
            next_action=(
                "Review or fill these noncritical gaps, or add audited acceptance "
                "rows if the missing projection, injury, or market source is safe "
                "to live with for now."
            ),
        )
    critical_review_players = [
        row
        for row in report.player_rows
        if int(row.get("critical_review_count", 0)) > 0
    ]
    critical_review_detail = (
        f" {len(critical_review_players)} players still have imputed-but-present "
        "critical coverage and keep confidence penalties."
        if critical_review_players
        else ""
    )
    return CalibrationGateCheck(
        gate="source_coverage_thresholds",
        status="ready",
        severity="info",
        detail=(
            f"{len(report.player_rows)} players pass critical source coverage "
            f"thresholds; {len(accepted_review_gap_rows)} optional gaps have "
            "audited acceptance rows and still retain confidence penalties."
            + critical_review_detail
        ),
        next_action="Keep source snapshots frozen unless intentionally refreshed.",
    )


def _identity_audit_gate(data_pack_path: str | Path, source_root: Path) -> CalibrationGateCheck:
    report = build_identity_audit(data_pack_path, source_root=source_root)
    if report.issues:
        return CalibrationGateCheck(
            gate="identity_audit_pass",
            status="blocked",
            severity="error",
            detail="Identity audit could not run: " + "; ".join(report.issues),
            next_action="Create or repair Sleeper-to-nflverse identity bridge files.",
        )
    if report.blocked_rows:
        return CalibrationGateCheck(
            gate="identity_audit_pass",
            status="blocked",
            severity="error",
            detail=f"{len(report.blocked_rows)} high-value rankings are identity-blocked.",
            next_action="Resolve blocked identity rows before trusting stats joins.",
        )
    review_rows = [row for row in report.rows if row["audit_status"] != "ready"]
    if review_rows:
        return CalibrationGateCheck(
            gate="identity_audit_pass",
            status="review",
            severity="warning",
            detail=f"{len(review_rows)} identity rows need manual review.",
            next_action="Review ambiguous identity joins before final calibration.",
        )
    return CalibrationGateCheck(
        gate="identity_audit_pass",
        status="ready",
        severity="info",
        detail=f"{len(report.rows)} player identity joins pass.",
        next_action="Keep manual identity overrides audited.",
    )


def _lifecycle_model_separation_gate(
    data_pack_path: str | Path,
    source_root: Path,
) -> CalibrationGateCheck:
    draft_board = build_draft_room(data_pack_path)
    receipt_report = build_player_feature_receipts(data_pack_path, veteran_model_dir=source_root)
    if receipt_report.issues:
        return CalibrationGateCheck(
            gate="lifecycle_model_separation",
            status="blocked",
            severity="error",
            detail="Lifecycle receipts could not be built: " + "; ".join(receipt_report.issues),
            next_action=(
                "Fix player receipts before deciding whether players are rookies, "
                "young bridge assets, or established veterans."
            ),
        )

    rookie_rows = [
        row for row in draft_board.rookie_rows if str(row.get("asset_type") or "") == "rookie"
    ]
    rookie_lifecycle_errors = [
        row
        for row in rookie_rows
        if str(row.get("asset_lifecycle") or "") != "incoming_rookie"
    ]
    rookie_model_errors = [
        row
        for row in rookie_rows
        if "rookie" not in str(row.get("source") or "").lower()
    ]

    rows_by_player: dict[str, list[dict[str, object]]] = {}
    for row in receipt_report.rows:
        rows_by_player.setdefault(str(row.get("player") or ""), []).append(row)

    young_bridge_players = {
        player
        for player, rows in rows_by_player.items()
        if any(is_young_nfl_bridge_lifecycle(row.get("asset_lifecycle")) for row in rows)
    }
    missing_bridge_receipt_players = [
        player
        for player in sorted(young_bridge_players)
        if not _has_required_bridge_receipts(rows_by_player[player])
    ]
    established_draft_capital_rows = [
        row
        for row in receipt_report.rows
        if str(row.get("asset_lifecycle") or "") == "established_veteran"
        and str(row.get("formula_feature_name") or "")
        in {
            "draft_capital_prior_score",
            "young_nfl_bridge_decay_weight",
            "young_nfl_bridge_nfl_evidence_weight",
            "young_nfl_bridge_prior",
        }
        and (
            _safe_float(row.get("feature_weight"), 0.0) > 0
            or abs(_safe_float(row.get("contribution"), 0.0)) > 0.0001
        )
    ]
    established_missing_stats_rows = [
        player
        for player, rows in rows_by_player.items()
        if any(str(row.get("asset_lifecycle") or "") == "established_veteran" for row in rows)
        and not _has_established_veteran_stats_receipts(rows)
    ]

    blocked_details: list[str] = []
    if rookie_lifecycle_errors:
        blocked_details.append(
            f"{len(rookie_lifecycle_errors)} rookie draftable rows are not labeled incoming_rookie"
        )
    if rookie_model_errors:
        blocked_details.append(
            f"{len(rookie_model_errors)} rookie draftable rows do not point to rookie model source"
        )
    if missing_bridge_receipt_players:
        blocked_details.append(
            f"{len(missing_bridge_receipt_players)} young NFL bridge players lack bridge receipts"
        )
    if established_draft_capital_rows:
        blocked_details.append(
            f"{len(established_draft_capital_rows)} established veteran receipt rows "
            "still use draft-capital prior"
        )
    if established_missing_stats_rows:
        blocked_details.append(
            f"{len(established_missing_stats_rows)} established veterans lack stats-first receipts"
        )

    if blocked_details:
        return CalibrationGateCheck(
            gate="lifecycle_model_separation",
            status="blocked",
            severity="error",
            detail="; ".join(blocked_details),
            next_action=(
                "Keep rankings review-only. Incoming rookies must route through the "
                "rookie model, young NFL players need visible bridge prior receipts, "
                "and established veterans must stay stats-first with draft capital removed."
            ),
        )
    return CalibrationGateCheck(
        gate="lifecycle_model_separation",
        status="ready",
        severity="info",
        detail=(
            f"{len(rookie_rows)} incoming rookies use rookie draftable rows; "
            f"{len(young_bridge_players)} young NFL bridge players show bridge receipts; "
            "established veteran receipts do not use draft-capital prior."
        ),
        next_action="Keep lifecycle lanes visible on rankings, receipts, and draft boards.",
    )


def _has_required_bridge_receipts(rows: list[dict[str, object]]) -> bool:
    features = {str(row.get("formula_feature_name") or "") for row in rows}
    sections = {str(row.get("receipt_section_label") or "") for row in rows}
    explanations = " ".join(str(row.get("lifecycle_explanation") or "") for row in rows)
    has_required_features = {
        "draft_capital_prior_score",
        "young_nfl_bridge_decay_weight",
        "young_nfl_bridge_nfl_evidence_weight",
        "young_nfl_bridge_prior",
    }.issubset(features)
    has_bridge_section = "Young-Player Bridge Prior" in sections
    has_explanation = "young NFL bridge asset" in explanations
    return has_required_features and has_bridge_section and has_explanation


def _has_established_veteran_stats_receipts(rows: list[dict[str, object]]) -> bool:
    sections = {
        str(row.get("receipt_section_label") or "")
        for row in rows
        if str(row.get("asset_lifecycle") or "") == "established_veteran"
    }
    return bool({"NFL Production", "Role/Usage"}.intersection(sections))


def _sanity_fixture_gate(preview_root: str | Path) -> CalibrationGateCheck:
    report = build_stats_first_calibration_report(str(preview_root))
    readiness_rows = stats_first_calibration_readiness_rows(report)
    fixture_areas = {"stats_first_scenarios", "stats_first_sensitivity"}
    failed = [
        row
        for row in readiness_rows
        if row["area"] in fixture_areas and row["status"] != "ready"
    ]
    if failed:
        return CalibrationGateCheck(
            gate="sanity_fixture_pass",
            status="blocked",
            severity="error",
            detail=(
                f"{len(failed)} stats-first calibration areas did not pass: "
                + ", ".join(str(row["area"]) for row in failed)
            ),
            next_action="Fix failed sanity fixtures before restoring decision-ready status.",
        )
    return CalibrationGateCheck(
        gate="sanity_fixture_pass",
        status="ready",
        severity="info",
        detail=(
            f"{len(report.scenario_rows)} sanity scenarios pass; stats-first "
            "sensitivity checks are stable. Preview replay rows are handled as "
            "preview/apply review, not named sanity fixtures."
        ),
        next_action="Keep named sanity fixtures in the regression suite.",
    )


def _ranking_outlier_gate(data_pack_path: str | Path, source_root: Path) -> CalibrationGateCheck:
    report = build_model_outlier_report(data_pack_path, veteran_model_dir=source_root)
    if report.issues:
        return CalibrationGateCheck(
            gate="ranking_outlier_review",
            status="blocked",
            severity="error",
            detail="Ranking outlier review could not run: " + "; ".join(report.issues),
            next_action="Fix feature receipts before reviewing ranking outliers.",
        )
    invalid_acceptances = list(getattr(report, "invalid_acceptance_rows", []))
    review_required = [
        row
        for row in report.rows
        if is_review_required_bucket(row["bucket"])
        and row.get("acceptance_status") != "accepted"
    ]
    accepted_count = sum(
        1
        for row in report.rows
        if is_review_required_bucket(row["bucket"])
        and row.get("acceptance_status") == "accepted"
    )
    blocking = [row for row in review_required if row["severity"] == "blocking"]
    high = [row for row in review_required if row["severity"] == "high"]
    if invalid_acceptances:
        return CalibrationGateCheck(
            gate="ranking_outlier_review",
            status="blocked",
            severity="error",
            detail=(
                f"{len(invalid_acceptances)} outlier acceptance rows are invalid; "
                f"{accepted_count} valid acceptance rows loaded."
            ),
            next_action=(
                "Fix model_outlier_acceptances.csv so every accepted outlier has "
                "player_id, player_name, outlier_type, reason, reviewer, and timestamp."
            ),
        )
    if blocking or high:
        return CalibrationGateCheck(
            gate="ranking_outlier_review",
            status="blocked",
            severity="error",
            detail=(
                f"{len(blocking)} blocking and {len(high)} high-severity "
                f"review-required ranking outliers remain; {accepted_count} "
                "outliers have audited acceptance rows."
            ),
            next_action="Resolve or explicitly approve review-required outliers.",
        )
    if review_required:
        return CalibrationGateCheck(
            gate="ranking_outlier_review",
            status="review",
            severity="warning",
            detail=(
                f"{len(review_required)} lower-severity review-required outliers remain; "
                f"{accepted_count} outliers have audited acceptance rows."
            ),
            next_action=(
                "Review lower-severity outliers before draft-day freeze, or accept "
                "them with audited reasons if they are intentionally tolerated."
            ),
        )
    return CalibrationGateCheck(
        gate="ranking_outlier_review",
        status="ready",
        severity="info",
        detail=(
            "No unresolved review-required ranking outliers remain; "
            f"{accepted_count} outliers have audited acceptance rows."
        ),
        next_action="Use market-edge outliers as review prompts, not hidden rank inputs.",
    )


def _rookie_replay_no_leakage_gate(
    predraft_path: str | Path,
    outcome_path: str | Path,
) -> CalibrationGateCheck:
    predraft = Path(predraft_path)
    outcome = Path(outcome_path)
    if not predraft.exists():
        return CalibrationGateCheck(
            gate="rookie_replay_no_leakage_pass",
            status="blocked",
            severity="error",
            detail=f"Missing historical rookie predraft input file: {predraft}.",
            next_action="Add pre-NFL/as-of-draft replay inputs before calibration.",
        )
    try:
        report = build_historical_rookie_replay_report(predraft, outcome)
    except (OSError, ValueError) as exc:
        return CalibrationGateCheck(
            gate="rookie_replay_no_leakage_pass",
            status="blocked",
            severity="error",
            detail=f"Historical rookie replay could not run: {exc}",
            next_action="Fix historical replay fixture columns and values.",
        )
    if report.issues:
        return CalibrationGateCheck(
            gate="rookie_replay_no_leakage_pass",
            status="blocked",
            severity="error",
            detail="Historical rookie replay has issues: " + "; ".join(report.issues),
            next_action="Fix replay issues before calibration.",
        )
    metadata = {str(row["metadata_key"]): row["metadata_value"] for row in report.metadata_rows}
    future_used = any(bool(row["future_nfl_stats_used"]) for row in report.top20_rows)
    policy_ok = metadata.get("ranking_input_scope") == NO_FUTURE_STATS_POLICY
    if future_used or not policy_ok:
        return CalibrationGateCheck(
            gate="rookie_replay_no_leakage_pass",
            status="blocked",
            severity="error",
            detail="Historical rookie replay does not prove no-leakage ranking inputs.",
            next_action="Separate predraft ranking inputs from post-draft outcome labels.",
        )
    return CalibrationGateCheck(
        gate="rookie_replay_no_leakage_pass",
        status="ready",
        severity="info",
        detail=f"{len(report.top20_rows)} top prospect replay rows prove no future stats.",
        next_action="Keep outcome labels display-only in historical replay.",
    )


def _final_ui_smoke_gate(app_dir: str | Path | None) -> CalibrationGateCheck:
    root = Path(app_dir) if app_dir else Path(__file__).resolve().parents[2] / "app"
    missing = [
        spec.file_path
        for spec in VISIBLE_NAVIGATION_PAGES
        if not app_page_path(root, spec).exists()
    ]
    if missing:
        return CalibrationGateCheck(
            gate="final_ui_smoke_pass",
            status="blocked",
            severity="error",
            detail="Missing visible app pages: " + ", ".join(missing),
            next_action="Restore missing decision pages before calibration can pass.",
        )
    return CalibrationGateCheck(
        gate="final_ui_smoke_pass",
        status="ready",
        severity="info",
        detail=f"{len(VISIBLE_NAVIGATION_PAGES)} visible decision pages exist.",
        next_action="Run browser smoke QA before creating the final draft freeze.",
    )


def _draft_ux_smoke_gate(data_pack_path: str | Path) -> CalibrationGateCheck:
    contract = build_draft_ux_contract(data_pack_path)
    page_routes = {str(row["route"]) for row in contract.page_rows}
    if contract.issues:
        return CalibrationGateCheck(
            gate="draft_ux_smoke_pass",
            status="blocked",
            severity="error",
            detail="Draft UX contract has issues: " + "; ".join(contract.issues),
            next_action="Fix Rankings/Draft Board contract issues before final freeze.",
        )
    if page_routes != {"rankings", "draft-board"}:
        return CalibrationGateCheck(
            gate="draft_ux_smoke_pass",
            status="blocked",
            severity="error",
            detail="Draft UX pages are not the expected Rankings plus Draft Board pair.",
            next_action="Restore the simplified draft UX navigation contract.",
        )
    if len(contract.pick_grid_rows) != DRAFT_TOTAL_PICKS:
        return CalibrationGateCheck(
            gate="draft_ux_smoke_pass",
            status="blocked",
            severity="error",
            detail=(
                f"Draft pick grid has {len(contract.pick_grid_rows)} rows; "
                f"expected {DRAFT_TOTAL_PICKS}."
            ),
            next_action="Fix draft board pick-grid generation before final freeze.",
        )
    if not contract.best_option_rows or not contract.my_pick_rows:
        return CalibrationGateCheck(
            gate="draft_ux_smoke_pass",
            status="blocked",
            severity="error",
            detail="Draft UX cannot show my-pick options from the active pool.",
            next_action="Fix my-pick detection and available-pool options before final freeze.",
        )
    return CalibrationGateCheck(
        gate="draft_ux_smoke_pass",
        status="ready",
        severity="info",
        detail=(
            f"Rankings/Draft Board contract passes with {len(contract.pick_grid_rows)} "
            f"pick cells and {len(contract.best_option_rows)} best-option rows."
        ),
        next_action="Browser-smoke Rankings and Draft Board before live use.",
    )


def _badge(status: str) -> str:
    if status == "ready":
        return "Model Calibration Passed"
    if status == "blocked":
        return "Model Calibration Blocked"
    return "Model Calibration Needs Review"


def _decision_badge(
    status: str,
    checks: tuple[CalibrationGateCheck, ...],
) -> str:
    if model_v4_rebuild_freeze_active() and status == "ready":
        return "Review Only"
    if status == "ready":
        return "Decision Ready"
    blocked_gates = {check.gate for check in checks if check.status == "blocked"}
    if (
        model_v4_rebuild_freeze_active()
        and not blocked_gates
        and any(check.gate == "model_v4_rebuild_freeze" for check in checks)
    ):
        return "Review Only"
    if blocked_gates.intersection(
        {
            "real_draft_pool_loaded",
            "source_coverage_thresholds",
            "identity_audit_pass",
            "lifecycle_model_separation",
        }
    ):
        return "Needs Data"
    if any(check.status == "review" for check in checks) or blocked_gates:
        return "Calibration Needs Review"
    return "Review Only"


def _pre_declaration_passed(checks: tuple[CalibrationGateCheck, ...]) -> bool:
    roster_decision_gates = {
        "model_v4_rebuild_freeze",
        "source_coverage_thresholds",
        "identity_audit_pass",
        "lifecycle_model_separation",
        "sanity_fixture_pass",
        "ranking_outlier_review",
        "final_ui_smoke_pass",
    }
    by_gate = {check.gate: check for check in checks}
    return all(
        by_gate.get(gate) is not None and by_gate[gate].status == "ready"
        for gate in roster_decision_gates
    )


def _pre_declaration_badge(
    passed: bool,
    checks: tuple[CalibrationGateCheck, ...],
) -> str:
    if passed:
        return "Roster Decisions Ready"
    blocking_roster_gates = {
        check.gate
        for check in checks
        if check.status == "blocked"
        and check.gate
        in {
            "source_coverage_thresholds",
            "identity_audit_pass",
            "lifecycle_model_separation",
            "sanity_fixture_pass",
            "ranking_outlier_review",
            "final_ui_smoke_pass",
        }
    }
    if blocking_roster_gates:
        return "Roster Decisions Need Data"
    return "Roster Decisions Need Review"


def _draft_badge(
    passed: bool,
    checks: tuple[CalibrationGateCheck, ...],
) -> str:
    if passed:
        return "Draft Ready"
    draft_pool = next(
        (check for check in checks if check.gate == "real_draft_pool_loaded"),
        None,
    )
    if draft_pool is not None and draft_pool.status != "ready":
        if "released veterans" in draft_pool.detail.lower():
            return "Needs Released Veterans"
        return "Draft Pool Needs Data"
    if any(check.status == "blocked" for check in checks):
        return "Draft Needs Data"
    return "Draft Needs Review"


def _bucket_gap_summary(rows: list[dict[str, object]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        bucket = str(row["bucket"])
        counts[bucket] = counts.get(bucket, 0) + 1
    return ", ".join(f"{bucket}: {counts[bucket]}" for bucket in sorted(counts))


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _overall_next_action(status: str) -> str:
    if model_v4_rebuild_freeze_active():
        return "Finish the Model v4 rebuild before restoring readiness labels."
    if status == "ready":
        return "Calibration gate passed; decision-ready status may be restored."
    if status == "blocked":
        return "Fix blocked calibration gates before money decisions."
    return "Review calibration warnings before restoring decision-ready status."
