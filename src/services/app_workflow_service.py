from __future__ import annotations

from dataclasses import dataclass

from src.services.data_pack_admission_service import DataPackAdmissionReport
from src.services.data_pack_health_service import DataPackHealthReport
from src.services.final_calibration_gate_service import FinalCalibrationGateReport
from src.services.model_recalibration_service import model_recalibration_policy


@dataclass(frozen=True)
class AppWorkflowReport:
    mode: str
    headline: str
    explanation: str
    primary_next_step: str
    safe_rows: list[dict[str, object]]
    blocked_rows: list[dict[str, object]]
    next_update_rows: list[dict[str, object]]
    page_rows: list[dict[str, object]]


def build_app_workflow_report(
    health: DataPackHealthReport,
    admission: DataPackAdmissionReport,
    calibration: FinalCalibrationGateReport,
) -> AppWorkflowReport:
    if health.error_count > 0 or health.readiness == "blocked" or admission.decision == "blocked":
        return AppWorkflowReport(
            mode="Data Blocked",
            headline="Fix import data before using model pages.",
            explanation=(
                "The app cannot safely reason from the selected pack until blocking "
                "roster, pick, league-rank, or CSV-shape issues are fixed."
            ),
            primary_next_step="Open Import & Refresh validation rows and clear blocking errors.",
            safe_rows=_safe_rows(data_ok=False),
            blocked_rows=_blocked_rows(data_blocked=True, calibration=calibration),
            next_update_rows=_next_update_rows(),
            page_rows=_page_rows("data_blocked"),
        )

    recalibration = model_recalibration_policy()
    if recalibration.active and not calibration.passed:
        if calibration.pre_declaration_passed:
            return AppWorkflowReport(
                mode="Roster Declaration Review Mode",
                headline="Roster decisions can be reviewed before released veterans arrive.",
                explanation=(
                    "The pre-declaration model gates are clear for keep/drop/shop review. "
                    "The mixed offline draft board still waits on the official released "
                    "veteran list, so draft decisions remain held."
                ),
                primary_next_step=(
                    "Use My Team and War Board for roster declaration review. Import "
                    "official released veterans later to unlock draft-ready status."
                ),
                safe_rows=_safe_rows(data_ok=True, pre_declaration_ready=True),
                blocked_rows=_blocked_rows(data_blocked=False, calibration=calibration),
                next_update_rows=_next_update_rows(),
                page_rows=_page_rows("pre_declaration"),
            )
        return AppWorkflowReport(
            mode="Safe Inventory Mode",
            headline="Use facts, not rankings, until calibration passes.",
            explanation=(
                "Roster, pick, league-rank, and import facts are usable. Model "
                "rankings, trade targets, draft values, and freeze outputs are "
                "intentionally blocked because the final calibration gate has not passed."
            ),
            primary_next_step=(
                "Wait for the stats/source research, import real sources, then clear "
                "source coverage, identity, and ranking outlier blockers."
            ),
            safe_rows=_safe_rows(data_ok=True),
            blocked_rows=_blocked_rows(data_blocked=False, calibration=calibration),
            next_update_rows=_next_update_rows(),
            page_rows=_page_rows("safe_inventory"),
        )

    if calibration.passed and health.readiness == "ready" and admission.decision == "ready":
        return AppWorkflowReport(
            mode="Decision Mode",
            headline="Model calibration passed.",
            explanation=(
                "The selected pack has cleared import readiness, admission, and the "
                "final calibration gate. Use decision pages, then freeze a final board."
            ),
            primary_next_step=(
                "Use War Board first, then My Team, League Targets, Rankings, "
                "Draft Board, and Trade Lab."
            ),
            safe_rows=_safe_rows(data_ok=True, decision_ready=True),
            blocked_rows=[],
            next_update_rows=_next_update_rows(decision_ready=True),
            page_rows=_page_rows("decision"),
        )

    return AppWorkflowReport(
        mode="Review Mode",
        headline="Data loads, but something still needs review.",
        explanation=(
            "The selected pack is not blocked, but at least one readiness, admission, "
            "or calibration item needs review before money decisions."
        ),
        primary_next_step="Use the readiness and calibration tables below to clear review items.",
        safe_rows=_safe_rows(data_ok=True),
        blocked_rows=_blocked_rows(data_blocked=False, calibration=calibration),
        next_update_rows=_next_update_rows(),
        page_rows=_page_rows("review"),
    )


def workflow_summary_row(report: AppWorkflowReport) -> dict[str, object]:
    return {
        "mode": report.mode,
        "headline": report.headline,
        "primary_next_step": report.primary_next_step,
    }


def _safe_rows(
    *,
    data_ok: bool,
    decision_ready: bool = False,
    pre_declaration_ready: bool = False,
) -> list[dict[str, object]]:
    rows = [
        {
            "area": "Rosters",
            "status": "usable" if data_ok else "blocked",
            "meaning": "Who is on each roster.",
            "use": (
                "Keep/drop/shop review."
                if pre_declaration_ready
                else "Inventory only."
                if not decision_ready
                else "Roster context."
            ),
        },
        {
            "area": "Picks",
            "status": "usable" if data_ok else "blocked",
            "meaning": "Current pick ownership.",
            "use": "Inventory only." if not decision_ready else "Draft planning.",
        },
        {
            "area": "Roster's League-Rank Top Five",
            "status": "usable" if data_ok else "blocked",
            "meaning": (
                "The five highest league-ranked players on each roster. This is "
                "not league ranks 1-5 overall."
            ),
            "use": (
                "Forced-release review."
                if pre_declaration_ready
                else "Rule check only."
                if not decision_ready
                else "Forced-release strategy."
            ),
        },
        {
            "area": "Import Validation",
            "status": "usable" if data_ok else "blocked",
            "meaning": "CSV shape, coverage, and pack health.",
            "use": "Fix blockers before model work.",
        },
    ]
    if decision_ready or pre_declaration_ready:
        rows.extend(
            [
                {
                    "area": "Stats Value",
                    "status": "usable",
                    "meaning": "Private LVE football/stat value.",
                    "use": (
                        "Roster-declaration review score."
                        if pre_declaration_ready
                        else "Primary model score."
                    ),
                },
                {
                    "area": "Market Edge",
                    "status": "usable",
                    "meaning": "Stats value minus market/liquidity value.",
                    "use": (
                        "Shop/trade review."
                        if pre_declaration_ready
                        else "Trade opportunity finder."
                    ),
                },
            ]
        )
    return rows


def _blocked_rows(
    *,
    data_blocked: bool,
    calibration: FinalCalibrationGateReport,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if data_blocked:
        rows.append(
            {
                "area": "All model pages",
                "why_blocked": "Import data has blocking errors.",
                "what_to_do": "Fix Import & Refresh validation errors.",
            }
        )
        return rows
    if not calibration.passed:
        if calibration.pre_declaration_passed:
            rows.extend(
                [
                    {
                        "area": "Final War Board rankings",
                        "why_blocked": calibration.draft_badge,
                        "what_to_do": (
                            "Use War Board/My Team for roster declaration review only; "
                            "load rookies, free agents, and released veterans before "
                            "final draft decisions."
                        ),
                    },
                    {
                        "area": "League Targets and Trade Lab",
                        "why_blocked": "Opponent acquisition decisions need the real draft pool.",
                        "what_to_do": (
                            "Use market-edge/pressure rows as review prompts until the "
                            "available rookie/free-agent/released-veteran pool is loaded."
                        ),
                    },
                    {
                        "area": "Rankings and Draft Board",
                        "why_blocked": calibration.draft_badge,
                        "what_to_do": (
                            "Load real rookies and available free agents now; add official "
                            "released veterans after declaration."
                        ),
                    },
                    {
                        "area": "Final Draft Freeze",
                        "why_blocked": "Freeze is only final after draft/final gates pass.",
                        "what_to_do": (
                            "Create only review snapshots until the draft pool is complete."
                        ),
                    },
                ]
            )
            return rows
        rows.extend(
            [
                {
                    "area": "War Board rankings",
                    "why_blocked": calibration.badge,
                    "what_to_do": "Clear final calibration gate blockers first.",
                },
                {
                    "area": "My Team keep/drop/shop calls",
                    "why_blocked": "Model recommendations are not trusted yet.",
                    "what_to_do": (
                        "Use only roster and Roster's League-Rank Top Five rule "
                        "inventory."
                    ),
                },
                {
                    "area": "League Targets and Trade Lab",
                    "why_blocked": "Target/trade edge needs trusted stats and identity joins.",
                    "what_to_do": "Import and validate source statistics.",
                },
                {
                    "area": "Rankings and Draft Board",
                    "why_blocked": "Rookie/veteran values are not calibrated yet.",
                    "what_to_do": "Wait for model rebuild and sanity fixtures.",
                },
                {
                    "area": "Final Draft Freeze",
                    "why_blocked": "Freeze is only final after calibration passes.",
                    "what_to_do": "Create only review snapshots until the gate passes.",
                },
            ]
        )
    return rows


def _next_update_rows(*, decision_ready: bool = False) -> list[dict[str, object]]:
    rows = [
        {
            "bucket": "Data Truth",
            "goal": "Import real stats, usage, injuries, projections, IDs, and rookies.",
            "success_signal": "Source coverage and identity gates pass.",
        },
        {
            "bucket": "Model Truth",
            "goal": "Rebuild formulas around statistics and named sanity fixtures.",
            "success_signal": "Outlier and sanity gates pass without hand-waving.",
        },
        {
            "bucket": "Product Truth",
            "goal": "Make pages answer one question each with plain labels.",
            "success_signal": "You know where to click under draft pressure.",
        },
        {
            "bucket": "Decision Truth",
            "goal": "Separate facts, model calls, market edge, and watchlist items.",
            "success_signal": "No page shows untrusted recommendations as action items.",
        },
        {
            "bucket": "Historical Trust",
            "goal": "Backtest college prospects with pre-NFL inputs only.",
            "success_signal": "Hit-rate reports show whether the rookie model actually works.",
        },
    ]
    if decision_ready:
        rows.append(
            {
                "bucket": "Draft Freeze",
                "goal": "Lock a final local board after late-news review.",
                "success_signal": "Final board certificate says money-decision ready.",
            }
        )
    return rows


def _page_rows(mode: str) -> list[dict[str, object]]:
    blocked = mode != "decision"
    pre_declaration = mode == "pre_declaration"
    return [
        {
            "page": "Import & Refresh",
            "use_for": "Refresh data and understand current mode.",
            "current_behavior": "Main command center.",
        },
        {
            "page": "War Board",
            "use_for": "Overall decisions after calibration.",
            "current_behavior": (
                "Roster declaration review only."
                if pre_declaration
                else "Hidden rankings; inventory only."
                if blocked
                else "Primary decision board."
            ),
        },
        {
            "page": "My Team",
            "use_for": "Your roster, forced-release rule, and personal decisions.",
            "current_behavior": (
                "Keep/drop/shop review."
                if pre_declaration
                else "Roster and Roster's League-Rank Top Five inventory only."
                if blocked
                else "Roster action board."
            ),
        },
        {
            "page": "League Targets",
            "use_for": "Opponent release and acquisition opportunities.",
            "current_behavior": (
                "Pressure review only."
                if pre_declaration
                else "Pressure inventory only."
                if blocked
                else "Target finder."
            ),
        },
        {
            "page": "Trade Lab",
            "use_for": "Market edge and package ideas.",
            "current_behavior": (
                "Trade review prompts only."
                if pre_declaration
                else "Trade inputs only."
                if blocked
                else "Trade edge workspace."
            ),
        },
        {
            "page": "Rankings",
            "use_for": "Draftable player list.",
            "current_behavior": "Pool status only." if blocked else "Available-player rankings.",
        },
        {
            "page": "Draft Board",
            "use_for": "Live/mock draft pick tracker.",
            "current_behavior": "Pick grid contract only." if blocked else "Live draft board.",
        },
        {
            "page": "Model Lab",
            "use_for": "Audit why the model is or is not trusted.",
            "current_behavior": "Calibration blockers and receipts.",
        },
        {
            "page": "Freeze",
            "use_for": "Lock final board or review snapshot.",
            "current_behavior": "Review snapshots only." if blocked else "Final freeze enabled.",
        },
    ]
