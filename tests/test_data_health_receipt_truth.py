from __future__ import annotations

from pathlib import Path

from src.services.data_health_dashboard_service import _refresh_health
from src.services.refresh_receipt_store_service import (
    load_refresh_receipt,
    write_refresh_receipt,
)


def _row(
    *,
    source_id: str = "source_a",
    action_type: str = "REFRESHED",
    status: str = "GREEN",
    refreshed: bool = True,
    **values,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "source_name": source_id,
        "dataset_id": "",
        "source_family": "",
        "action_type": action_type,
        "status": status,
        "refreshed": refreshed,
        **values,
    }


def _write(
    root: Path,
    run_id: str,
    rows: list[dict[str, object]],
    *,
    overall_status: str = "GREEN",
) -> Path:
    return write_refresh_receipt(
        {
            "run_id": run_id,
            "started_at_utc": "2026-07-13T12:00:00+00:00",
            "finished_at_utc": "2026-07-13T12:01:00+00:00",
            "loader_mode": "QUICK_REFRESH",
            "overall_status": overall_status,
            "results": rows,
        },
        status_root=root,
        created_at_utc="2026-07-13T12:02:00+00:00",
    ).latest_path


def _value(frame, check: str) -> str:
    return str(frame.loc[frame["check"].eq(check)].iloc[0]["value"])


def _status(frame, check: str) -> str:
    return str(frame.loc[frame["check"].eq(check)].iloc[0]["status"])


def test_healthy_current_receipt_is_explicitly_successful(tmp_path: Path) -> None:
    latest = _write(
        tmp_path,
        "20260713_120101",
        [_row(freshness_status="CURRENT")],
    )
    frame = _refresh_health(latest)

    assert _status(frame, "Receipt storage status") == "GREEN"
    assert _status(frame, "Last manual Refresh Data run") == "GREEN"
    assert _value(frame, "Sources refreshed") == "1"
    assert _value(frame, "Stale retained sources") == "0"


def test_success_with_stale_data_never_displays_current_or_green(tmp_path: Path) -> None:
    latest = _write(
        tmp_path,
        "20260713_120102",
        [_row(freshness_status="STALE")],
    )
    frame = _refresh_health(latest)

    assert _status(frame, "Last manual Refresh Data run") == "YELLOW"
    assert _value(frame, "Sources refreshed") == "0"
    assert _value(frame, "Stale retained sources") == "1"


def test_mixed_success_and_failure_is_partial_with_failure_visible(tmp_path: Path) -> None:
    latest = _write(
        tmp_path,
        "20260713_120103",
        [
            _row(source_id="ok", freshness_status="CURRENT"),
            _row(
                source_id="failed",
                action_type="FAILED",
                status="RED",
                refreshed=False,
                execution_status="failed",
            ),
        ],
        overall_status="RED",
    )
    frame = _refresh_health(latest)

    assert "PARTIAL_SUCCESS" in _value(frame, "Last manual Refresh Data run")
    assert _status(frame, "Last manual Refresh Data run") == "YELLOW"
    assert _status(frame, "Failed sources") == "RED"
    assert _value(frame, "Sources refreshed") == "1"


def test_failed_latest_with_valid_lkg_is_separate_from_current(tmp_path: Path) -> None:
    _write(tmp_path, "20260713_120104", [_row(freshness_status="CURRENT")])
    latest = _write(
        tmp_path,
        "20260713_120105",
        [
            _row(
                action_type="FAILED",
                status="RED",
                refreshed=False,
                execution_status="failed",
                freshness_status="STALE",
            )
        ],
        overall_status="RED",
    )
    frame = _refresh_health(latest)

    assert _status(frame, "Last manual Refresh Data run") == "RED"
    assert _value(frame, "Last-known-good retained-data links") == "1"
    assert _value(frame, "Stale retained sources") == "0"
    assert _value(frame, "Failed sources") == "1"


def test_failed_latest_without_prior_valid_data_fails_closed(tmp_path: Path) -> None:
    latest = _write(
        tmp_path,
        "20260713_120106",
        [
            _row(
                action_type="FAILED",
                status="RED",
                refreshed=False,
                execution_status="failed",
                freshness_status="STALE",
            )
        ],
        overall_status="RED",
    )
    frame = _refresh_health(latest)

    assert _status(frame, "Failed sources") == "RED"
    assert _value(frame, "Last-known-good retained-data links") == "0"
    assert _status(frame, "Last-known-good retained-data links") == "YELLOW"


def test_skipped_unavailable_and_gated_are_mechanically_distinct(tmp_path: Path) -> None:
    latest = _write(
        tmp_path,
        "20260713_120107",
        [
            _row(
                source_id="skipped",
                action_type="SKIPPED_BY_POLICY",
                status="SKIPPED",
                refreshed=False,
            ),
            _row(
                source_id="unavailable",
                action_type="NOT_CONFIGURED",
                status="NOT_CONFIGURED",
                refreshed=False,
            ),
            _row(
                source_id="gated",
                action_type="BLOCKED_MANUAL",
                status="BLOCKED",
                refreshed=False,
            ),
        ],
        overall_status="YELLOW",
    )
    frame = _refresh_health(latest)

    assert _value(frame, "Sources skipped") == "1"
    assert _value(frame, "Sources unavailable") == "1"
    assert _value(frame, "Sources gated") == "1"
    assert _value(frame, "Failed sources") == "0"


def test_explicit_partial_and_not_enough_information_remain_distinct(tmp_path: Path) -> None:
    latest = _write(
        tmp_path,
        "20260713_120108",
        [
            _row(
                source_id="partial",
                action_type="CHECK_ONLY",
                status="YELLOW",
                refreshed=False,
                headline_status="PARTIAL_SUCCESS",
            ),
            _row(
                source_id="unknown",
                action_type="CHECK_ONLY",
                status="YELLOW",
                refreshed=False,
            ),
        ],
        overall_status="YELLOW",
    )
    frame = _refresh_health(latest)

    assert _value(frame, "Partial-success sources") == "1"
    assert _value(frame, "Not-enough-information sources") == "1"


def test_identity_and_source_exceptions_are_preserved_and_fail_closed(
    tmp_path: Path,
) -> None:
    latest = _write(
        tmp_path,
        "20260713_120109",
        [
            _row(
                source_id="identity_review",
                action_type="CHECK_ONLY",
                status="YELLOW",
                refreshed=False,
                identity_exception="UNRESOLVED_IDENTITY",
            ),
            _row(
                source_id="source_review",
                action_type="CHECK_ONLY",
                status="YELLOW",
                refreshed=False,
                source_exception="SOURCE_CONTRACT_EXCEPTION",
            ),
        ],
        overall_status="YELLOW",
    )

    loaded = load_refresh_receipt(status_path=latest)
    frame = _refresh_health(latest)

    assert loaded.latest_receipt["results"][0]["identity_exception"] == (
        "UNRESOLVED_IDENTITY"
    )
    assert loaded.latest_receipt["results"][1]["source_exception"] == (
        "SOURCE_CONTRACT_EXCEPTION"
    )
    assert _value(frame, "Sources refreshed") == "0"
    assert _value(frame, "Not-enough-information sources") == "2"


def test_missing_corrupt_and_unsupported_receipts_never_upgrade_to_healthy(
    tmp_path: Path,
) -> None:
    latest = tmp_path / "latest_refresh_status.json"
    missing = _refresh_health(latest)
    assert _status(missing, "Receipt storage status") == "YELLOW"
    assert _value(missing, "Last manual Refresh Data run") == "Not enough information"

    latest.write_text("{bad", encoding="utf-8")
    corrupt = _refresh_health(latest)
    assert _status(corrupt, "Receipt storage status") == "RED"
    assert _value(corrupt, "Last manual Refresh Data run") == "Not enough information"

    latest.write_text('{"schema_version":99}', encoding="utf-8")
    unsupported = _refresh_health(latest)
    assert _status(unsupported, "Receipt storage status") == "RED"
    assert _value(unsupported, "Last manual Refresh Data run") == (
        "Not enough information"
    )
