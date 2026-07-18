from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.navigation import ALL_NAVIGATION_PAGES
from src.services.data_health_dashboard_service import (
    build_data_health_dashboard,
    compact_status_cards,
)
from src.services.draft_day_runtime_state_service import (
    DEFAULT_DRAFT_ID,
    empty_runtime_state,
    runtime_state_path,
)
from src.services.refresh_receipt_store_service import write_refresh_receipt


def _write_refresh_status(path: Path, payload: dict[str, object]) -> None:
    body = {
        "started_at_utc": "2026-06-24T11:59:00+00:00",
        "loader_mode": "QUICK_REFRESH",
        **payload,
    }
    body["results"] = [_closed_receipt_row(row) for row in body["results"]]
    write_refresh_receipt(
        body,
        status_root=path.parent,
        created_at_utc=str(body["finished_at_utc"]),
    )


def _closed_receipt_row(row: dict[str, object]) -> dict[str, object]:
    source_id = str(row["source_id"])
    return {
        "source_id": source_id,
        "source_name": str(row.get("source_name") or source_id),
        "dataset_id": str(row.get("dataset_id") or ""),
        "source_family": "nflverse" if source_id.startswith("nflverse_") else "",
        "action_type": row["action_type"],
        "status": row["status"],
        "refreshed": row["refreshed"],
        "execution_status": str(row.get("execution_status") or ""),
        "headline_status": str(row.get("headline_status") or ""),
        "freshness_status": str(row.get("freshness_status") or ""),
    }


def _value(report, section: str, check: str) -> str:
    frames = {
        "Board": report.board_health,
        "Market": report.market_health,
        "Refresh Data": report.refresh_health,
        "NGS": report.ngs_context,
        "Runtime": report.runtime_health,
        "Evidence": report.evidence_health,
        "Missing data": report.missing_data_health,
        "Guardrail": report.guardrails,
    }
    frame = frames[section]
    row = frame.loc[frame["check"].eq(check)].iloc[0]
    return str(row["value"])


def _status(report, section: str, check: str) -> str:
    frames = {
        "Board": report.board_health,
        "Market": report.market_health,
        "Refresh Data": report.refresh_health,
        "NGS": report.ngs_context,
        "Runtime": report.runtime_health,
        "Evidence": report.evidence_health,
        "Missing data": report.missing_data_health,
        "Guardrail": report.guardrails,
    }
    frame = frames[section]
    row = frame.loc[frame["check"].eq(check)].iloc[0]
    return str(row["status"])


def test_board_health_reports_expected_frozen_and_dynasty_counts(tmp_path: Path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)

    assert _value(report, "Board", "Frozen baseline board rows") == "66"
    assert _status(report, "Board", "Frozen baseline board rows") == "GREEN"
    assert _value(report, "Board", "Full Dynasty Rankings rows") == "240"
    assert _status(report, "Board", "Full Dynasty Rankings rows") == "GREEN"


def test_market_freshness_and_display_only_guardrail_load(tmp_path: Path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)

    assert _value(report, "Market", "DynastyProcess freshness")
    assert _status(report, "Market", "Display-only guardrail") == "GREEN"


def test_runtime_health_reports_no_state_without_creating_state(tmp_path: Path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)

    assert _value(report, "Runtime", "Live latest state found") == "no"
    assert not runtime_state_path(mode="live", draft_id=DEFAULT_DRAFT_ID, root=tmp_path).exists()


def test_runtime_health_reports_sample_state_counts(tmp_path: Path) -> None:
    state = empty_runtime_state(mode="live", draft_id=DEFAULT_DRAFT_ID)
    state["workflow_state"] = {
        "assignments": [
            {
                "player": "Sample Player",
                "player_id": "sample",
                "position": "WR",
                "pick_label": "1.01",
            }
        ]
    }
    state["trade_events"] = [{"trade_id": "trade-1", "team_a": "NWR", "team_b": "Other"}]
    path = runtime_state_path(mode="live", draft_id=DEFAULT_DRAFT_ID, root=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")

    report = build_data_health_dashboard(runtime_root=tmp_path)

    assert _value(report, "Runtime", "Live latest state found") == "yes"
    assert _value(report, "Runtime", "Live drafted count") == "1"
    assert _value(report, "Runtime", "Live trade event count") == "1"


def test_historical_evidence_buckets_and_proxy_warning_load(tmp_path: Path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)

    assert _value(report, "Evidence", "ACTUAL_DROP truth count") == "22"
    assert _value(report, "Evidence", "PROXY sensitivity count") == "480"
    assert _status(report, "Evidence", "Proxy rows training truth") == "GREEN"
    assert _value(report, "Evidence", "Proxy rows training truth") == "no"


def test_missing_data_health_loads_backlog_and_source_status(tmp_path: Path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)

    assert _status(report, "Missing data", "High-priority missing data items") == "YELLOW"
    assert _value(report, "Missing data", "Actual 2026 draft log imported") == "no"
    assert _value(report, "Missing data", "Trade history imported") == "no"


def test_guardrails_report_no_shared_or_runtime_files_tracked(tmp_path: Path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)

    assert _status(report, "Guardrail", "No raw shared data tracked") == "GREEN"
    assert _status(report, "Guardrail", "No runtime JSON tracked") == "GREEN"
    assert _status(report, "Guardrail", "No model/rank mutation") == "GREEN"


def test_dashboard_status_cards_are_compact(tmp_path: Path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)
    cards = compact_status_cards(report)

    assert {card["label"] for card in cards} >= {
        "Overall",
        "Frozen baseline",
        "Full dynasty",
        "Market baseline",
        "Refresh Data",
        "Runtime state",
        "NGS context",
        "Model evidence",
    }


def test_data_health_dashboard_reports_display_only_ngs_context(tmp_path: Path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)

    assert _value(report, "NGS", "NGS display gate") == "REVIEW_ONLY_NGS_CONTEXT"
    assert _status(report, "NGS", "NGS display gate") == "GREEN"
    assert _value(report, "NGS", "ngs_passing safe display coverage") == "94"
    assert _value(report, "NGS", "ngs_rushing safe display coverage") == "143"
    assert _value(report, "NGS", "ngs_receiving safe display coverage") == "325"
    assert _value(report, "NGS", "Blocked advanced metric families") == "13"


def test_data_health_consumes_refresh_status_file(tmp_path: Path) -> None:
    refresh_status = tmp_path / "latest_refresh_status.json"
    _write_refresh_status(
        refresh_status,
        {
                "run_id": "20260624_120000",
                "finished_at_utc": "2026-06-24T12:00:00+00:00",
                "overall_status": "YELLOW",
                "results": [
                    {
                        "source_id": "dynastyprocess_market_baseline",
                        "source_name": "DynastyProcess market baseline",
                        "action_type": "REFRESHED",
                        "status": "GREEN",
                        "refreshed": True,
                        "freshness_status": "CURRENT",
                        "user_message": "ok",
                    },
                    {
                        "source_id": "rotowire_vendor_exports",
                        "action_type": "BLOCKED_MANUAL",
                        "status": "BLOCKED",
                        "refreshed": False,
                    },
                ],
        },
    )

    report = build_data_health_dashboard(
        runtime_root=tmp_path / "runtime",
        refresh_status_path=refresh_status,
    )

    assert _value(report, "Refresh Data", "Sources refreshed") == "1"
    assert _value(report, "Refresh Data", "Blocked/not configured sources") == "1"
    assert _value(report, "Refresh Data", "DynastyProcess latest refresh outcome") == (
        "REFRESH_SUCCESS"
    )


def test_data_health_summarizes_nflverse_dataset_rows(tmp_path: Path) -> None:
    refresh_status = tmp_path / "latest_refresh_status.json"
    _write_refresh_status(
        refresh_status,
        {
                "run_id": "20260630_120000",
                "finished_at_utc": "2026-06-30T12:00:00+00:00",
                "overall_status": "YELLOW",
                "results": [
                    {
                        "source_id": "nflverse_player_stats_weekly",
                        "source_kind": "public_structured_nfl_dataset",
                        "dataset_id": "player_stats_weekly",
                        "action_type": "CHECK_ONLY",
                        "status": "GREEN",
                        "configured": True,
                        "refreshed": False,
                    },
                    {
                        "source_id": "nflverse_ff_rankings",
                        "source_kind": "public_structured_nfl_dataset",
                        "dataset_id": "ff_rankings",
                        "action_type": "BLOCKED_MANUAL",
                        "status": "BLOCKED",
                        "configured": False,
                        "refreshed": False,
                    },
                ],
        },
    )

    report = build_data_health_dashboard(
        runtime_root=tmp_path / "runtime",
        refresh_status_path=refresh_status,
    )

    assert _value(report, "Refresh Data", "NFLVerse dataset health rows") == "2"
    assert _value(report, "Refresh Data", "NFLVerse blocked policy datasets") == "1"
    assert _value(report, "Refresh Data", "NFLVerse NOT_CONFIGURED datasets") == "0"
    assert _status(report, "Refresh Data", "NFLVerse review/stale/unknown datasets") == (
        "YELLOW"
    )


def test_settings_data_health_route_and_legacy_alias_exist() -> None:
    route_map = {page.url_path: page.file_path for page in ALL_NAVIGATION_PAGES}

    assert route_map["settings-data-health"] == "pages/28_settings_data_health_v1.py"
    assert route_map["settings"] == "pages/30_settings_data_health_alias.py"


def test_git_has_no_tracked_shared_data_or_runtime_json() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], text=True)

    assert "NWR_SHARED_DATA" not in tracked
    assert "draft_runtime_state" not in tracked
    assert "_draft_log.json" not in tracked
