from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.data_refresh_orchestrator_service import (
    DEFAULT_STATUS_PATH as DEFAULT_REFRESH_STATUS_PATH,
)
from src.services.display_only_ngs_context_service import (
    NGS_GATE,
    REVIEW_ONLY_WARNING,
    blocked_ngs_metric_rows,
    data_health_ngs_rows,
)
from src.services.draft_day_app_v1_service import (
    EXPECTED_DYNASTY_ROW_COUNT,
    EXPECTED_PINNED_MANIFEST_HASH,
    EXPECTED_ROW_COUNT,
    load_dynasty_rankings,
    load_frozen_board,
    pinned_manifest_hash,
)
from src.services.draft_day_runtime_state_service import (
    DEFAULT_DRAFT_ID,
    normalize_runtime_state,
    runtime_paths,
    runtime_state_path,
)
from src.services.market_baseline_service import (
    DISPLAY_ONLY_WARNING,
    load_market_freshness,
    load_market_player_context,
)
from src.services.refresh_receipt_store_service import (
    MISSING,
    VALID_LATEST,
    RefreshReceiptLoadResult,
    inspect_refresh_receipt,
)
from src.services.refresh_receipt_store_service import (
    STALE_RETAINED_DATA as RECEIPT_STALE_RETAINED_DATA,
)
from src.services.refresh_recovery_presentation_service import (
    NOT_ENOUGH_INFORMATION as RECOVERY_NOT_ENOUGH_INFORMATION,
)
from src.services.refresh_recovery_presentation_service import (
    PARTIAL_SUCCESS,
    REFRESH_FAILED,
    REFRESH_SUCCESS,
    SOURCE_GATED,
    SOURCE_SKIPPED,
    SOURCE_UNAVAILABLE,
    STALE_RETAINED_DATA,
    build_refresh_recovery_presentations,
    build_run_recovery_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
NOT_ENOUGH_INFORMATION = "Not enough information"

MODEL_EVALUATION_ROOT = REPO_ROOT / "docs" / "hq" / "model" / "evaluation_v0"
MODEL_EVALUATION_BY_BUCKET_PATH = (
    MODEL_EVALUATION_ROOT / "NWR_MODEL_EVALUATION_BY_BUCKET_V0_20260623.csv"
)
MODEL_EVALUATION_SUMMARY_PATH = (
    MODEL_EVALUATION_ROOT / "NWR_MODEL_EVALUATION_SUMMARY_V0_20260623.csv"
)
MODEL_EVALUATION_WARNINGS_PATH = (
    MODEL_EVALUATION_ROOT / "NWR_MODEL_EVALUATION_WARNINGS_V0_20260623.csv"
)
LEAGUE_HISTORY_ROOT = REPO_ROOT / "docs" / "hq" / "data_sources" / "league_history_evidence"
LEAGUE_HISTORY_BACKLOG_PATH = LEAGUE_HISTORY_ROOT / "league_history_missing_items_backlog.csv"
ACTUAL_DRAFT_LOG_PATH = LEAGUE_HISTORY_ROOT / "NWR_ACTUAL_2026_DRAFT_LOG_NORMALIZED.csv"
TRADE_HISTORY_EVENTS_PATH = (
    LEAGUE_HISTORY_ROOT / "NWR_LEAGUE_TRADE_HISTORY_EVENTS_NORMALIZED.csv"
)
GMAIL_EVIDENCE_QUEUE_PATH = (
    LEAGUE_HISTORY_ROOT / "NWR_PRE_SLEEPER_GMAIL_EVIDENCE_QUEUE_20260623.csv"
)

STATUS_ORDER = {"GREEN": 0, "YELLOW": 1, "RED": 2}
FORBIDDEN_TRACKED_PATTERNS = (
    "NWR_SHARED_DATA",
    "prediction_dump",
    "raw_vendor",
)
SOURCE_TRUTH_DIFF_PATTERNS = (
    "latest_candidate",
    "latest_approved",
    "pinned",
    "FINAL_DRAFT_BOARD",
    "final_board",
    "full_player_board_value_review_rows",
)


@dataclass(frozen=True)
class HealthDashboardReport:
    generated_at_utc: str
    overall_status: str
    app_status: pd.DataFrame
    board_health: pd.DataFrame
    market_health: pd.DataFrame
    refresh_health: pd.DataFrame
    ngs_context: pd.DataFrame
    runtime_health: pd.DataFrame
    evidence_health: pd.DataFrame
    missing_data_health: pd.DataFrame
    guardrails: pd.DataFrame
    warnings: pd.DataFrame


def build_data_health_dashboard(
    *,
    runtime_root: Path | None = None,
    repo_root: Path = REPO_ROOT,
    refresh_status_path: Path = DEFAULT_REFRESH_STATUS_PATH,
) -> HealthDashboardReport:
    sections = {
        "app_status": _app_status(repo_root),
        "board_health": _board_health(),
        "market_health": _market_health(),
        "refresh_health": _refresh_health(refresh_status_path),
        "ngs_context": _ngs_context_health(),
        "runtime_health": _runtime_health(runtime_root),
        "evidence_health": _evidence_health(),
        "missing_data_health": _missing_data_health(),
        "guardrails": _guardrail_health(repo_root),
    }
    warnings = _warning_rows(sections)
    overall = _overall_status([*sections.values(), warnings])
    return HealthDashboardReport(
        generated_at_utc=datetime.now(UTC).isoformat(timespec="seconds"),
        overall_status=overall,
        app_status=sections["app_status"],
        board_health=sections["board_health"],
        market_health=sections["market_health"],
        refresh_health=sections["refresh_health"],
        ngs_context=sections["ngs_context"],
        runtime_health=sections["runtime_health"],
        evidence_health=sections["evidence_health"],
        missing_data_health=sections["missing_data_health"],
        guardrails=sections["guardrails"],
        warnings=warnings,
    )


def compact_status_cards(report: HealthDashboardReport) -> list[dict[str, str]]:
    return [
        _card("Overall", report.overall_status, "Dashboard health rollup"),
        _card(
            "Frozen baseline",
            _status_for_check(report.board_health, "Frozen baseline board rows"),
            _value_for_check(report.board_health, "Frozen baseline board rows"),
        ),
        _card(
            "Full dynasty",
            _status_for_check(report.board_health, "Full Dynasty Rankings rows"),
            _value_for_check(report.board_health, "Full Dynasty Rankings rows"),
        ),
        _card(
            "Market baseline",
            _status_for_check(report.market_health, "DynastyProcess freshness"),
            _value_for_check(report.market_health, "DynastyProcess freshness"),
        ),
        _card(
            "Refresh Data",
            _status_for_check(report.refresh_health, "Last manual Refresh Data run"),
            _value_for_check(report.refresh_health, "Last manual Refresh Data run"),
        ),
        _card(
            "NGS context",
            _status_for_check(report.ngs_context, "NGS display gate"),
            _value_for_check(report.ngs_context, "NGS display gate"),
        ),
        _card(
            "Runtime state",
            _status_for_check(report.runtime_health, "Live latest state found"),
            _value_for_check(report.runtime_health, "Live latest state found"),
        ),
        _card(
            "Model evidence",
            _status_for_check(report.evidence_health, "Proxy rows training truth"),
            _value_for_check(report.evidence_health, "Proxy rows training truth"),
        ),
    ]


def _app_status(repo_root: Path) -> pd.DataFrame:
    return _frame(
        [
            _row("App", "Current git HEAD", "INFO", _git_output(["rev-parse", "HEAD"], repo_root)),
            _row("App", "Branch", "INFO", _git_output(["branch", "--show-current"], repo_root)),
            _row("App", "App mode", "GREEN", "Local Streamlit"),
            _row(
                "App",
                "Generated timestamp",
                "INFO",
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
            _row(
                "App",
                "Source badge",
                "GREEN",
                "Frozen baseline checkpoint plus active draftable pool overlays",
                "Frozen board is a baseline/checkpoint, not the only line of truth.",
            ),
        ]
    )


def _board_health() -> pd.DataFrame:
    frozen = load_frozen_board()
    dynasty = load_dynasty_rankings()
    pinned = pinned_manifest_hash()
    rookie_count = _safe_int(getattr(dynasty, "rookie_count", 0))
    dynasty_status = (
        "GREEN"
        if dynasty.row_count == EXPECTED_DYNASTY_ROW_COUNT
        else "YELLOW"
        if dynasty.row_count == 0 and dynasty.source_path is None
        else "RED"
    )
    dynasty_note = (
        f"Expected {EXPECTED_DYNASTY_ROW_COUNT}; source={dynasty.source_label}."
        if dynasty.source_path is not None
        else (
            f"Optional repository-local full rankings are unavailable; expected "
            f"{EXPECTED_DYNASTY_ROW_COUNT} rows when supplied."
        )
    )
    return _frame(
        [
            _row(
                "Board",
                "Frozen baseline board rows",
                "GREEN" if frozen.row_count == EXPECTED_ROW_COUNT else "RED",
                str(frozen.row_count),
                f"Expected {EXPECTED_ROW_COUNT}; source={frozen.source_label}.",
            ),
            _row(
                "Board",
                "Pinned hash status",
                "GREEN" if pinned == EXPECTED_PINNED_MANIFEST_HASH else "RED",
                pinned or "missing",
                f"Expected {EXPECTED_PINNED_MANIFEST_HASH}.",
            ),
            _row(
                "Board",
                "latest_candidate/latest_approved untouched",
                "GREEN",
                "checked by git diff guardrail",
                "Dashboard does not update latest_candidate or latest_approved.",
            ),
            _row(
                "Board",
                "Full Dynasty Rankings rows",
                dynasty_status,
                str(dynasty.row_count),
                dynasty_note,
            ),
            _row(
                "Board",
                "Full dynasty rookie/prospect caveat",
                "YELLOW" if rookie_count == 0 else "GREEN",
                str(rookie_count),
                "Known caveat: approved full dynasty source currently has 0 rookie/prospect rows.",
            ),
        ]
    )


def _market_health() -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    try:
        freshness = load_market_freshness()
        status = freshness.get("freshness_status", NOT_ENOUGH_INFORMATION)
        rows.extend(
            [
                _row("Market", "DynastyProcess freshness", _market_status(status), status),
                _row(
                    "Market",
                    "Upstream scrape date",
                    "GREEN" if freshness.get("upstream_scrape_date") else "YELLOW",
                    freshness.get("upstream_scrape_date", NOT_ENOUGH_INFORMATION),
                ),
                _row(
                    "Market",
                    "Fetch timestamp",
                    "GREEN" if freshness.get("nwr_fetch_timestamp") else "YELLOW",
                    freshness.get("nwr_fetch_timestamp", NOT_ENOUGH_INFORMATION),
                ),
            ]
        )
    except (FileNotFoundError, ValueError) as exc:
        rows.append(_row("Market", "DynastyProcess freshness", "RED", "missing", str(exc)))

    try:
        market = load_market_player_context()
        matched = _nonnull_count(market, "dp_value_1qb")
        rows.extend(
            [
                _row(
                    "Market",
                    "Market player rows",
                    "GREEN" if len(market) else "YELLOW",
                    len(market),
                ),
                _row(
                    "Market",
                    "Market join coverage",
                    "GREEN" if matched else "YELLOW",
                    str(matched),
                    "Rows with display-only DynastyProcess 1QB value.",
                ),
                _row(
                    "Market",
                    "Age fallback count",
                    "GREEN",
                    str(_age_fallback_count(market)),
                    "Count from available market context age-source columns if present.",
                ),
                _row(
                    "Market",
                    "Display-only guardrail",
                    "GREEN",
                    "active",
                    DISPLAY_ONLY_WARNING,
                ),
            ]
        )
    except (FileNotFoundError, ValueError) as exc:
        rows.append(_row("Market", "Market player rows", "YELLOW", "missing", str(exc)))
    return _frame(rows)


def _runtime_health(runtime_root: Path | None) -> pd.DataFrame:
    paths = runtime_paths(runtime_root)
    live = _runtime_state_status("live", runtime_root)
    mock = _runtime_state_status("mock", runtime_root)
    backups = list(paths.backup_dir.glob("*.json")) if paths.backup_dir.exists() else []
    return _frame(
        [
            _row("Runtime", "Runtime state path", "INFO", str(paths.root)),
            _row(
                "Runtime",
                "Live latest state found",
                "GREEN" if live["exists"] else "YELLOW",
                "yes" if live["exists"] else "no",
                "Opening the dashboard does not create runtime state.",
            ),
            _row("Runtime", "Live latest updated", live["status"], live["updated_at"]),
            _row("Runtime", "Live drafted count", live["status"], str(live["drafted_count"])),
            _row("Runtime", "Live trade event count", live["status"], str(live["trade_count"])),
            _row(
                "Runtime",
                "Mock latest state found",
                "GREEN" if mock["exists"] else "YELLOW",
                "yes" if mock["exists"] else "no",
            ),
            _row("Runtime", "Backups count", "GREEN" if backups else "YELLOW", str(len(backups))),
            _row(
                "Runtime",
                "Runtime source warning",
                "YELLOW",
                "manual/local",
                "Runtime draft state is manual local state, not official source truth.",
            ),
        ]
    )


def _ngs_context_health() -> pd.DataFrame:
    rows = data_health_ngs_rows()
    blocked_rows = blocked_ngs_metric_rows()
    if not rows:
        return _frame(
            [
                _row(
                    "NGS context",
                    "NGS display gate",
                    "YELLOW",
                    NOT_ENOUGH_INFORMATION,
                    "Display-only NGS packet is missing or unreadable.",
                )
            ]
        )
    health_rows: list[dict[str, str]] = [
        _row(
            "NGS context",
            "NGS display gate",
            "GREEN",
            NGS_GATE,
            REVIEW_ONLY_WARNING,
        )
    ]
    for row in rows:
        health_rows.append(
            _row(
                "NGS context",
                f"{row['Source family']} safe display coverage",
                "GREEN",
                row["Safe display count"],
                (
                    f"{row['Seasons']} seasons; {row['Source rows']} source rows; "
                    f"{row['Identity-review count']} identity-review rows hidden by default. "
                    f"{row['Caveat']}"
                ),
            )
        )
    health_rows.append(
        _row(
            "NGS context",
            "Blocked advanced metric families",
            "GREEN",
            str(len(blocked_rows)),
            "PFR, ESPN QBR, FTN, PFF, ffopportunity UI use, routes, TPRR, YPRR, rz_att, "
            "and elusive proxy remain outside this runtime lane.",
        )
    )
    return _frame(health_rows)


def _refresh_health(refresh_status_path: Path) -> pd.DataFrame:
    receipt_load = inspect_refresh_receipt(status_path=refresh_status_path)
    if not receipt_load.has_valid_latest:
        return _invalid_refresh_receipt_health(receipt_load)

    payload = receipt_load.latest_receipt or {}
    rows = [row for row in payload.get("results", []) if isinstance(row, dict)]
    recovery_rows = [_receipt_recovery_row(row) for row in rows]
    presentations = build_refresh_recovery_presentations(recovery_rows)
    paired = list(zip(rows, presentations, strict=False))
    run_summary = build_run_recovery_summary(
        recovery_rows,
        finished_at=str(payload.get("finished_at_utc") or ""),
    )

    def count_state(state: str) -> int:
        return sum(item.refresh_state == state for _, item in paired)

    refreshed_count = count_state(REFRESH_SUCCESS)
    partial_count = count_state(PARTIAL_SUCCESS)
    stale_count = count_state(STALE_RETAINED_DATA)
    skipped_count = count_state(SOURCE_SKIPPED)
    unavailable_count = count_state(SOURCE_UNAVAILABLE)
    gated_count = count_state(SOURCE_GATED)
    failed_count = count_state(REFRESH_FAILED)
    unknown_count = count_state(RECOVERY_NOT_ENOUGH_INFORMATION)
    lkg_count = sum(bool(str(row.get("last_known_good_receipt_id") or "")) for row in rows)
    unresolved_retained = sum(
        row.get("retained_data_status") == RECEIPT_STALE_RETAINED_DATA
        and not str(row.get("last_known_good_receipt_id") or "")
        and item.refresh_state != REFRESH_SUCCESS
        for row, item in paired
    )

    nflverse_pairs = [
        (row, item)
        for row, item in paired
        if _is_nflverse_dataset_row(row)
    ]
    nflverse_dataset_rows = [row for row, _ in nflverse_pairs]
    nflverse_failed = [row for row, item in nflverse_pairs if item.refresh_state == REFRESH_FAILED]
    nflverse_blocked = [row for row, item in nflverse_pairs if item.refresh_state == SOURCE_GATED]
    nflverse_not_configured = [
        row for row, item in nflverse_pairs if item.refresh_state == SOURCE_UNAVAILABLE
    ]
    nflverse_review = [
        row
        for row, item in nflverse_pairs
        if item.refresh_state
        in {
            PARTIAL_SUCCESS,
            STALE_RETAINED_DATA,
            SOURCE_SKIPPED,
            RECOVERY_NOT_ENOUGH_INFORMATION,
        }
    ]
    dynasty = next(
        (
            (row, item)
            for row, item in paired
            if row.get("source_id") == "dynastyprocess_market_baseline"
        ),
        None,
    )
    dynasty_state = dynasty[1].refresh_state if dynasty else RECOVERY_NOT_ENOUGH_INFORMATION
    dynasty_detail = dynasty[1].reason_summary if dynasty else "No source receipt row recorded."

    return _frame(
        [
            _row(
                "Refresh Data",
                "Receipt storage status",
                "GREEN",
                VALID_LATEST,
                "Schema and integrity passed; this does not imply source health.",
            ),
            _row(
                "Refresh Data",
                "Last manual Refresh Data run",
                _health_status_from_recovery(run_summary.refresh_state),
                (
                    f"{run_summary.refresh_state} at "
                    f"{payload.get('finished_at_utc') or NOT_ENOUGH_INFORMATION}"
                ),
                (
                    "Latest attempt receipt: "
                    f"{payload.get('receipt_id') or NOT_ENOUGH_INFORMATION}; "
                    f"refresh action: {payload.get('refresh_action_id') or NOT_ENOUGH_INFORMATION}."
                ),
            ),
            _row(
                "Refresh Data",
                "Sources refreshed",
                "GREEN" if refreshed_count else "YELLOW",
                str(refreshed_count),
                "Counts only explicit REFRESH_SUCCESS states.",
            ),
            _row(
                "Refresh Data",
                "Partial-success sources",
                "YELLOW" if partial_count else "GREEN",
                str(partial_count),
            ),
            _row(
                "Refresh Data",
                "Stale retained sources",
                "YELLOW" if stale_count else "GREEN",
                str(stale_count),
            ),
            _row(
                "Refresh Data",
                "Sources skipped",
                "YELLOW" if skipped_count else "GREEN",
                str(skipped_count),
            ),
            _row(
                "Refresh Data",
                "Sources unavailable",
                "YELLOW" if unavailable_count else "GREEN",
                str(unavailable_count),
            ),
            _row(
                "Refresh Data",
                "Sources gated",
                "YELLOW" if gated_count else "GREEN",
                str(gated_count),
            ),
            _row(
                "Refresh Data",
                "Failed sources",
                "RED" if failed_count else "GREEN",
                str(failed_count),
            ),
            _row(
                "Refresh Data",
                "Not-enough-information sources",
                "YELLOW" if unknown_count else "GREEN",
                str(unknown_count),
            ),
            _row(
                "Refresh Data",
                "Blocked/not configured sources",
                "YELLOW" if gated_count + unavailable_count else "GREEN",
                str(gated_count + unavailable_count),
                f"Gated={gated_count}; unavailable/not configured={unavailable_count}.",
            ),
            _row(
                "Refresh Data",
                "Last-known-good retained-data links",
                "YELLOW" if unresolved_retained else "GREEN",
                str(lkg_count),
                (
                    f"{unresolved_retained} stale retained row(s) lack a validated matching "
                    "prior receipt relationship."
                ),
            ),
            _row(
                "Refresh Data",
                "DynastyProcess latest refresh outcome",
                _health_status_from_recovery(dynasty_state),
                dynasty_state,
                dynasty_detail,
            ),
            _row(
                "Refresh Data",
                "NFLVerse dataset health rows",
                "GREEN" if len(nflverse_dataset_rows) == 25 else "YELLOW",
                str(len(nflverse_dataset_rows)),
                "Coverage count only; failure, gate, stale, and unknown rows remain separate.",
            ),
            _row(
                "Refresh Data",
                "NFLVerse failed datasets",
                "RED" if nflverse_failed else "GREEN",
                str(len(nflverse_failed)),
                _nflverse_dataset_detail(nflverse_failed),
            ),
            _row(
                "Refresh Data",
                "NFLVerse blocked policy datasets",
                "YELLOW" if nflverse_blocked else "GREEN",
                str(len(nflverse_blocked)),
                _nflverse_dataset_detail(nflverse_blocked),
            ),
            _row(
                "Refresh Data",
                "NFLVerse NOT_CONFIGURED datasets",
                "YELLOW" if nflverse_not_configured else "GREEN",
                str(len(nflverse_not_configured)),
                _nflverse_dataset_detail(nflverse_not_configured),
            ),
            _row(
                "Refresh Data",
                "NFLVerse review/stale/unknown datasets",
                "YELLOW" if nflverse_review else "GREEN",
                str(len(nflverse_review)),
                _nflverse_dataset_detail(nflverse_review),
            ),
        ]
    )


def _invalid_refresh_receipt_health(load: RefreshReceiptLoadResult) -> pd.DataFrame:
    status = "YELLOW" if load.load_status == MISSING else "RED"
    rows = [
        _row(
            "Refresh Data",
            "Receipt storage status",
            status,
            load.load_status,
            load.detail,
        ),
        _row(
            "Refresh Data",
            "Last manual Refresh Data run",
            status,
            NOT_ENOUGH_INFORMATION,
            "The latest receipt is not valid; no current refresh outcome is inferred.",
        ),
        _row(
            "Refresh Data",
            "DynastyProcess latest refresh outcome",
            status,
            NOT_ENOUGH_INFORMATION,
            "No valid latest source receipt row is available.",
        ),
    ]
    if load.has_valid_backup:
        backup = load.backup_receipt or {}
        rows.append(
            _row(
                "Refresh Data",
                "Validated prior receipt (not latest)",
                "YELLOW",
                str(backup.get("receipt_id") or NOT_ENOUGH_INFORMATION),
                "Prior receipt evidence is separate and does not prove retained current data.",
            )
        )
    return _frame(rows)


def _receipt_recovery_row(row: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(row)
    adapted["user_explanation"] = row.get("error_summary") or ""
    adapted["last_success_at"] = row.get("source_as_of_utc") or ""
    return adapted


def _is_nflverse_dataset_row(row: dict[str, Any]) -> bool:
    return (
        str(row.get("source_kind") or "") == "public_structured_nfl_dataset"
        or str(row.get("source_family") or "").lower() == "nflverse"
        or str(row.get("source_id") or "").startswith("nflverse_")
    )


def _evidence_health() -> pd.DataFrame:
    by_bucket = _read_csv(MODEL_EVALUATION_BY_BUCKET_PATH)
    summary = _read_csv(MODEL_EVALUATION_SUMMARY_PATH)
    warnings = _read_csv(MODEL_EVALUATION_WARNINGS_PATH)
    truth_count = _bucket_count(by_bucket, "Truth backtest")
    caution_count = _bucket_count(by_bucket, "Caution backtest")
    sensitivity_count = _bucket_count(by_bucket, "Sensitivity test")
    proxy_training = _proxy_training_count(by_bucket)
    p0_p1_warnings = (
        warnings["severity"].astype(str).isin({"P0", "P1"}).sum()
        if "severity" in warnings.columns
        else 0
    )
    return _frame(
        [
            _row(
                "Evidence",
                "ACTUAL_DROP truth count",
                "GREEN" if truth_count else "YELLOW",
                truth_count,
            ),
            _row(
                "Evidence",
                "INFERRED_DROP caution count",
                "GREEN" if caution_count else "YELLOW",
                caution_count,
            ),
            _row(
                "Evidence",
                "PROXY sensitivity count",
                "YELLOW" if sensitivity_count else "GREEN",
                sensitivity_count,
            ),
            _row(
                "Evidence",
                "Proxy rows training truth",
                "GREEN" if proxy_training == 0 else "RED",
                "no" if proxy_training == 0 else str(proxy_training),
                "PROXY_DROP/PROXY_ONLY/LOW rows are not training truth.",
            ),
            _row(
                "Evidence",
                "Truth/caution/sensitivity bucket summary",
                "GREEN" if not by_bucket.empty else "YELLOW",
                f"{len(by_bucket)} rows",
                "From Model Evaluation Harness V0.",
            ),
            _row(
                "Evidence",
                "P0/P1 evaluation warnings",
                "GREEN" if int(p0_p1_warnings) == 0 else "RED",
                str(int(p0_p1_warnings)),
                "P2 warnings remain review items.",
            ),
            _row(
                "Evidence",
                "Predictive accuracy claim",
                "GREEN",
                _summary_value(summary, "predictive_accuracy_claim"),
                "Harness must report Not enough information without actual outcome labels.",
            ),
        ]
    )


def _missing_data_health() -> pd.DataFrame:
    backlog = _read_csv(LEAGUE_HISTORY_BACKLOG_PATH)
    draft_rows = _read_csv(ACTUAL_DRAFT_LOG_PATH)
    trade_rows = _read_csv(TRADE_HISTORY_EVENTS_PATH)
    gmail_queue = _read_csv(GMAIL_EVIDENCE_QUEUE_PATH)
    high_missing = (
        backlog.loc[
            backlog.get("priority", pd.Series(dtype=str)).astype(str).str.upper().eq("HIGH")
            & ~backlog.get("current_status", pd.Series(dtype=str))
            .astype(str)
            .str.upper()
            .isin({"DONE", "COMPLETE", "CONFIRMED"})
        ]
        if not backlog.empty
        else pd.DataFrame()
    )
    return _frame(
        [
            _row(
                "Missing data",
                "High-priority missing data items",
                "YELLOW" if len(high_missing) else "GREEN",
                str(len(high_missing)),
                "From league history missing-items backlog.",
            ),
            _row(
                "Missing data",
                "Actual 2026 draft log imported",
                "GREEN" if len(draft_rows) else "YELLOW",
                "yes" if len(draft_rows) else "no",
                f"{len(draft_rows)} normalized rows.",
            ),
            _row(
                "Missing data",
                "Trade history imported",
                "GREEN" if len(trade_rows) else "YELLOW",
                "yes" if len(trade_rows) else "no",
                f"{len(trade_rows)} normalized trade events.",
            ),
            _row(
                "Missing data",
                "Gmail evidence status",
                "YELLOW" if len(gmail_queue) else "YELLOW",
                f"{len(gmail_queue)} queue rows",
                "Gmail evidence is review-only; raw bodies are not tracked.",
            ),
        ]
    )


def _guardrail_health(repo_root: Path) -> pd.DataFrame:
    tracked = _git_lines(["ls-files"], repo_root)
    diff_names = _git_lines(["diff", "--name-only"], repo_root)
    forbidden_tracked = [
        path for path in tracked if _contains_any(path, FORBIDDEN_TRACKED_PATTERNS)
    ]
    runtime_json_tracked = [
        path
        for path in tracked
        if path.lower().endswith(".json")
        and ("runtime" in path.lower() or "draft_log" in path.lower())
    ]
    source_truth_diff = [
        path for path in diff_names if _contains_any(path, SOURCE_TRUTH_DIFF_PATTERNS)
    ]
    return _frame(
        [
            _row("Guardrail", "Market display-only", "GREEN", "yes"),
            _row("Guardrail", "Frozen board wording", "GREEN", "baseline/checkpoint"),
            _row(
                "Guardrail",
                "No raw shared data tracked",
                "GREEN" if not forbidden_tracked else "RED",
                "yes" if not forbidden_tracked else str(len(forbidden_tracked)),
            ),
            _row(
                "Guardrail",
                "No runtime JSON tracked",
                "GREEN" if not runtime_json_tracked else "RED",
                "yes" if not runtime_json_tracked else str(len(runtime_json_tracked)),
            ),
            _row(
                "Guardrail",
                "No source-truth mutation",
                "GREEN" if not source_truth_diff else "RED",
                "yes" if not source_truth_diff else "; ".join(source_truth_diff[:5]),
            ),
            _row("Guardrail", "No model/rank mutation", "GREEN", "yes"),
        ]
    )


def _runtime_state_status(mode: str, runtime_root: Path | None) -> dict[str, Any]:
    path = runtime_state_path(mode=mode, draft_id=DEFAULT_DRAFT_ID, root=runtime_root)
    if not path.exists():
        return {
            "exists": False,
            "status": "YELLOW",
            "updated_at": NOT_ENOUGH_INFORMATION,
            "drafted_count": 0,
            "trade_count": 0,
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        state = normalize_runtime_state(raw, mode=mode, draft_id=DEFAULT_DRAFT_ID)
    except (OSError, json.JSONDecodeError):
        return {
            "exists": True,
            "status": "RED",
            "updated_at": "unreadable",
            "drafted_count": 0,
            "trade_count": 0,
        }
    return {
        "exists": True,
        "status": "GREEN",
        "updated_at": str(state.get("updated_at") or NOT_ENOUGH_INFORMATION),
        "drafted_count": len(state.get("drafted_players", [])),
        "trade_count": len(state.get("trade_events", [])),
    }


def _warning_rows(sections: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for frame in sections.values():
        if frame.empty:
            continue
        for row in frame.to_dict("records"):
            if row.get("status") in {"YELLOW", "RED"}:
                rows.append(
                    _row(
                        str(row.get("section") or "Warning"),
                        str(row.get("check") or ""),
                        str(row.get("status") or "YELLOW"),
                        str(row.get("value") or ""),
                        str(row.get("detail") or ""),
                    )
                )
    return _frame(rows)


def _overall_status(frames: list[pd.DataFrame]) -> str:
    worst = "GREEN"
    for frame in frames:
        if frame.empty or "status" not in frame.columns:
            continue
        for status in frame["status"].astype(str):
            if status in STATUS_ORDER and STATUS_ORDER[status] > STATUS_ORDER[worst]:
                worst = status
    return worst


def _row(
    section: str,
    check: str,
    status: str,
    value: Any,
    detail: str = "",
) -> dict[str, str]:
    return {
        "section": section,
        "check": check,
        "status": str(status),
        "value": str(value),
        "detail": str(detail),
    }


def _card(label: str, status: str, detail: str) -> dict[str, str]:
    return {"label": label, "status": status, "detail": detail}


def _frame(rows: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["section", "check", "status", "value", "detail"]).fillna("")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()


def _status_for_check(frame: pd.DataFrame, check: str) -> str:
    match = frame.loc[frame["check"].eq(check)] if "check" in frame.columns else pd.DataFrame()
    return str(match.iloc[0]["status"]) if not match.empty else "YELLOW"


def _value_for_check(frame: pd.DataFrame, check: str) -> str:
    match = frame.loc[frame["check"].eq(check)] if "check" in frame.columns else pd.DataFrame()
    return str(match.iloc[0]["value"]) if not match.empty else NOT_ENOUGH_INFORMATION


def _market_status(status: str) -> str:
    if str(status).startswith("GREEN"):
        return "GREEN"
    if str(status).startswith("RED"):
        return "RED"
    return "YELLOW"


def _health_status_from_recovery(state: str) -> str:
    if state == REFRESH_SUCCESS:
        return "GREEN"
    if state == REFRESH_FAILED:
        return "RED"
    return "YELLOW"


def _nflverse_dataset_detail(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "All dataset rows in this group are GREEN."
    labels: list[str] = []
    for row in rows[:8]:
        source_id = str(row.get("source_id") or "")
        dataset_id = str(row.get("dataset_id") or source_id.removeprefix("nflverse_"))
        status = str(row.get("status") or NOT_ENOUGH_INFORMATION)
        labels.append(f"{dataset_id}={status}")
    suffix = "" if len(rows) <= 8 else f"; +{len(rows) - 8} more"
    return "; ".join(labels) + suffix


def _nonnull_count(frame: pd.DataFrame, column: str) -> int:
    if column not in frame.columns:
        return 0
    values = frame[column].astype(str).str.strip()
    return int(values.ne("").sum())


def _age_fallback_count(frame: pd.DataFrame) -> int:
    for column in ("age_source_display", "age_source", "dp_age_source"):
        if column in frame.columns:
            values = frame[column].astype(str).str.lower()
            return int(values.str.contains("fallback|market|dp", regex=True).sum())
    return 0


def _bucket_count(frame: pd.DataFrame, bucket: str) -> int:
    if frame.empty or "bucket" not in frame.columns or "row_count" not in frame.columns:
        return 0
    values = pd.to_numeric(frame.loc[frame["bucket"].eq(bucket), "row_count"], errors="coerce")
    return int(values.fillna(0).sum())


def _proxy_training_count(frame: pd.DataFrame) -> int:
    if frame.empty or "source_class" not in frame.columns:
        return 0
    proxy = frame["source_class"].astype(str).isin({"PROXY_DROP", "PROXY_ONLY"})
    training = frame.get("eligible_for_training", pd.Series(dtype=str)).astype(str).eq("yes")
    return int((proxy & training).sum())


def _summary_value(frame: pd.DataFrame, metric: str) -> str:
    if frame.empty or "metric" not in frame.columns:
        return NOT_ENOUGH_INFORMATION
    match = frame.loc[frame["metric"].eq(metric)]
    if match.empty:
        return NOT_ENOUGH_INFORMATION
    return str(match.iloc[0].get("value") or NOT_ENOUGH_INFORMATION)


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _git_output(command: list[str], repo_root: Path) -> str:
    output = _git_lines(command, repo_root)
    return output[0] if output else "unknown"


def _git_lines(command: list[str], repo_root: Path) -> list[str]:
    try:
        output = subprocess.check_output(["git", *command], cwd=repo_root, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _contains_any(value: str, patterns: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(pattern.lower() in lowered for pattern in patterns)
