from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.services.data_refresh_orchestrator_service import (
    CommandResult,
    RefreshSourceResult,
    build_refresh_registry,
    refresh_results_table,
    run_data_refresh,
    validate_refresh_result_schema,
)


def test_orchestrator_registry_loads_required_sources() -> None:
    registry = build_refresh_registry()
    source_ids = {entry.source_id for entry in registry}

    assert "dynastyprocess_market_baseline" in source_ids
    assert "sleeper_league_state" in source_ids
    assert "nflverse_public_data" in source_ids
    assert "collegefootballdata" in source_ids
    assert "rotowire_vendor_exports" in source_ids
    assert "gmail_league_history" in source_ids


def test_not_configured_sources_are_skipped_safely(tmp_path: Path) -> None:
    run = run_data_refresh(
        repo_root=tmp_path,
        status_root=tmp_path / "status",
        source_ids=["collegefootballdata"],
        write_status=False,
    )
    by_source = {result.source_id: result for result in run.results}

    assert by_source["collegefootballdata"].status == "NOT_CONFIGURED"
    assert by_source["collegefootballdata"].refreshed is False


def test_blocked_vendor_sources_do_not_run(tmp_path: Path) -> None:
    run = run_data_refresh(
        status_root=tmp_path / "status",
        source_ids=["rotowire_vendor_exports"],
        write_status=False,
    )
    result = next(row for row in run.results if row.source_id == "rotowire_vendor_exports")

    assert result.status == "BLOCKED"
    assert result.refreshed is False
    assert result.command_or_function == ""


def test_dynastyprocess_refresh_path_is_registered_if_script_exists() -> None:
    entry = next(
        row
        for row in build_refresh_registry()
        if row.source_id == "dynastyprocess_market_baseline"
    )

    assert entry.configured is True
    assert entry.safe_to_run is True
    assert entry.command_or_function.endswith("refresh_dynastyprocess_market_baseline_v1.py")


def test_failed_source_does_not_crash_whole_refresh(tmp_path: Path) -> None:
    def failing_handler(entry, context) -> RefreshSourceResult:
        raise RuntimeError("planned failure")

    run = run_data_refresh(
        status_root=tmp_path / "status",
        source_ids=["dynastyprocess_market_baseline", "data_health_inputs"],
        handlers={"dynastyprocess_market_baseline": failing_handler},
        write_status=False,
    )
    by_source = {result.source_id: result for result in run.results}

    assert by_source["dynastyprocess_market_baseline"].status == "RED"
    assert by_source["data_health_inputs"].status == "GREEN"
    assert run.overall_status == "RED"


def test_refresh_result_schema_validates(tmp_path: Path) -> None:
    run = run_data_refresh(
        status_root=tmp_path / "status",
        source_ids=["data_health_inputs"],
        write_status=False,
    )
    rows = refresh_results_table(run)

    validate_refresh_result_schema(rows)
    with pytest.raises(ValueError):
        validate_refresh_result_schema([{"source_id": "missing"}])


def test_refresh_status_writes_to_ignored_local_exports_only(tmp_path: Path) -> None:
    run = run_data_refresh(
        status_root=tmp_path / "local_exports" / "refresh_data",
        source_ids=["data_health_inputs"],
    )
    status_path = Path(run.status_path)

    assert "local_exports" in status_path.parts
    assert status_path.exists()
    tracked = subprocess.check_output(["git", "ls-files"], text=True)
    assert "local_exports/refresh_data" not in tracked.replace("\\", "/")
    assert "NWR_SHARED_DATA" not in tracked


def test_button_does_not_mutate_rank_model_or_source_truth_names() -> None:
    service_text = Path("src/services/data_refresh_orchestrator_service.py").read_text(
        encoding="utf-8"
    )

    for blocked_name in (
        "final_board_rank",
        "dynasty_rank_override",
        "latest_candidate",
        "latest_approved",
        "pinned_manifest",
    ):
        assert blocked_name not in service_text


def test_command_runner_failure_is_reported_without_exception(tmp_path: Path) -> None:
    def runner(command: list[str], cwd: Path, timeout: int) -> CommandResult:
        return CommandResult(2, "", "boom")

    run = run_data_refresh(
        status_root=tmp_path / "status",
        source_ids=["dynastyprocess_market_baseline"],
        command_runner=runner,
        write_status=False,
    )
    result = next(
        row for row in run.results if row.source_id == "dynastyprocess_market_baseline"
    )

    assert result.status == "RED"
    assert result.refreshed is False


def test_status_file_payload_is_json_serializable(tmp_path: Path) -> None:
    run = run_data_refresh(
        status_root=tmp_path / "status",
        source_ids=["data_health_inputs"],
    )
    payload = json.loads(Path(run.status_path).read_text(encoding="utf-8"))
    rows = {row["source_id"]: row for row in payload["results"]}

    assert payload["run_id"] == run.run_id
    assert rows["data_health_inputs"]["source_id"] == "data_health_inputs"
