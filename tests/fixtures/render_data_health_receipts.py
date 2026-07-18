from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.services.data_refresh_orchestrator_service import DEFAULT_STATUS_ROOT  # noqa: E402
from src.services.refresh_receipt_store_service import (  # noqa: E402
    BACKUP_RECEIPT_NAME,
    write_refresh_receipt,
)


def _row(
    source_id: str,
    label: str,
    *,
    action_type: str,
    status: str,
    refreshed: bool = False,
    **values,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "source_name": f"Synthetic fixture - {label}",
        "dataset_id": "",
        "source_family": "",
        "action_type": action_type,
        "status": status,
        "refreshed": refreshed,
        **values,
    }


def _payload(run_id: str, rows: list[dict[str, object]], status: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "started_at_utc": "2026-07-13T18:00:00+00:00",
        "finished_at_utc": "2026-07-13T18:01:00+00:00",
        "loader_mode": "QUICK_REFRESH",
        "overall_status": status,
        "results": rows,
    }


def write_matrix(root: Path) -> None:
    prior_rows = [
        _row(
            "failed_with_lkg",
            "prior success retained for failed source",
            action_type="REFRESHED",
            status="GREEN",
            refreshed=True,
            freshness_status="CURRENT",
        ),
        _row(
            "stale_retained",
            "prior success retained for stale source",
            action_type="REFRESHED",
            status="GREEN",
            refreshed=True,
            freshness_status="CURRENT",
        ),
    ]
    write_refresh_receipt(_payload("20260713_180000", prior_rows, "GREEN"), status_root=root)
    rows = [
        _row(
            "current_success",
            "current success",
            action_type="REFRESHED",
            status="GREEN",
            refreshed=True,
            freshness_status="CURRENT",
        ),
        _row(
            "partial_success",
            "partial success",
            action_type="CHECK_ONLY",
            status="YELLOW",
            headline_status="PARTIAL_SUCCESS",
        ),
        _row(
            "failed_with_lkg",
            "failed latest with last-known-good",
            action_type="FAILED",
            status="RED",
            execution_status="failed",
            freshness_status="STALE",
        ),
        _row(
            "failed_without_data",
            "failed latest with no usable data",
            action_type="FAILED",
            status="RED",
            execution_status="failed",
        ),
        _row(
            "stale_retained",
            "stale retained data",
            action_type="CHECK_ONLY",
            status="YELLOW",
            freshness_status="STALE",
        ),
        _row(
            "gated_source",
            "gated source",
            action_type="BLOCKED_MANUAL",
            status="BLOCKED",
        ),
        _row(
            "unavailable_source",
            "unavailable source",
            action_type="NOT_CONFIGURED",
            status="NOT_CONFIGURED",
            execution_status="blocked_config",
        ),
        _row(
            "skipped_source",
            "skipped source",
            action_type="SKIPPED_BY_POLICY",
            status="SKIPPED",
        ),
        _row(
            "unknown_source",
            "not enough information",
            action_type="CHECK_ONLY",
            status="YELLOW",
        ),
    ]
    write_refresh_receipt(_payload("20260713_180100", rows, "RED"), status_root=root)


def write_success(root: Path) -> None:
    rows = [
        _row(
            "current_success",
            "current success",
            action_type="REFRESHED",
            status="GREEN",
            refreshed=True,
            freshness_status="CURRENT",
        )
    ]
    write_refresh_receipt(_payload("20260713_180200", rows, "GREEN"), status_root=root)


def clear_latest_and_backup(root: Path) -> None:
    (root / "latest_refresh_status.json").unlink(missing_ok=True)
    (root / "backups" / BACKUP_RECEIPT_NAME).unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("matrix", "success", "missing", "corrupt", "unsupported"))
    args = parser.parse_args()
    root = DEFAULT_STATUS_ROOT
    root.mkdir(parents=True, exist_ok=True)
    if args.mode == "matrix":
        write_matrix(root)
    elif args.mode == "success":
        clear_latest_and_backup(root)
        write_success(root)
    else:
        clear_latest_and_backup(root)
        if args.mode == "corrupt":
            (root / "latest_refresh_status.json").write_text("{synthetic-corrupt", encoding="utf-8")
        elif args.mode == "unsupported":
            (root / "latest_refresh_status.json").write_text(
                '{"schema_version":99,"synthetic_fixture":true}',
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
