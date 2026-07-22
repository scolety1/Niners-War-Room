from __future__ import annotations

from pathlib import Path


def inject_direct_file_write(root: Path) -> None:
    (root / "direct-page-open-write.txt").write_text(
        "durable page-open mutation",
        encoding="utf-8",
    )


def inject_receipt_write(root: Path) -> None:
    import src.services.refresh_receipt_store_service as receipt_store

    receipt_store.write_refresh_receipt(
        _receipt_payload(),
        status_root=root / "receipts",
        created_at_utc="2026-07-22T12:00:02+00:00",
    )


def inject_runtime_state_write(root: Path) -> None:
    import src.services.draft_day_runtime_state_service as runtime_state

    state = runtime_state.empty_runtime_state(
        mode="live",
        draft_id="start_here_mutation",
        source_checkpoint="isolated test mutation",
    )
    runtime_state.save_runtime_state(
        state,
        event_type="isolated_page_open_mutation",
        root=root / "draft-runtime",
        create_backup=False,
    )


def inject_refresh_dispatch(_root: Path) -> None:
    import src.services.data_refresh_orchestrator_service as refresh

    refresh.run_quick_refresh()


def inject_rename_and_delete(root: Path) -> None:
    source = root / "rename-source.txt"
    target = root / "rename-target.txt"
    source.write_text("rename mutation", encoding="utf-8")
    source.rename(target)
    target.unlink()


def inject_wrapped_write(root: Path) -> None:
    _write_through_wrapper(root / "wrapped-page-open-write.bin")


def _write_through_wrapper(path: Path) -> None:
    path.write_bytes(b"wrapped durable page-open mutation")


def _receipt_payload() -> dict[str, object]:
    return {
        "run_id": "20260722_120001",
        "started_at_utc": "2026-07-22T12:00:00+00:00",
        "finished_at_utc": "2026-07-22T12:00:01+00:00",
        "loader_mode": "QUICK_REFRESH",
        "overall_status": "GREEN",
        "results": [
            {
                "source_id": "start_here_mutation_fixture",
                "source_name": "Start Here mutation fixture",
                "dataset_id": "",
                "source_family": "",
                "action_type": "REFRESHED",
                "status": "GREEN",
                "refreshed": True,
                "execution_status": "success",
                "headline_status": "current",
                "freshness_status": "CURRENT",
            }
        ],
    }
