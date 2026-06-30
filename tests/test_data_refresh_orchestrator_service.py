from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import src.services.data_refresh_orchestrator_service as orchestrator
from src.config.api_settings import ApiSettings
from src.services.data_refresh_orchestrator_service import (
    ACTION_CHECK_ONLY,
    ACTION_NOT_CONFIGURED,
    BLOCKED_MANUAL,
    CHECK_PROTECTED_ARTIFACTS,
    FAILED,
    QUICK_REFRESH,
    REFRESHED,
    CommandResult,
    RefreshSourceResult,
    build_refresh_registry,
    export_results_csv,
    refresh_results_table,
    run_check_protected_artifacts,
    run_data_loader,
    run_full_safe_refresh,
    run_manual_sources_checklist,
    run_quick_refresh,
    validate_refresh_result_schema,
)
from src.services.nflverse_refresh_health_service import CANONICAL_DATASET_IDS


def _settings(*, cfbd_api_key: str = "", sleeper_league_id: str = "123") -> ApiSettings:
    return ApiSettings(
        sleeper_league_id=sleeper_league_id,
        sleeper_api_base="https://api.sleeper.app/v1",
        cfbd_api_key=cfbd_api_key,
        cfbd_api_base="https://api.collegefootballdata.com",
        sportsdataio_api_key="",
        sportsdataio_api_base="https://api.sportsdata.io",
        rotowire_export_root=None,
        pff_export_root=None,
        live_api_enabled=False,
        api_cache_root=Path("local_exports/api_cache"),
        api_timeout_seconds=1,
        max_requests_per_minute=60,
    )


def _fake_refreshed(entry, context) -> RefreshSourceResult:
    from src.services.data_refresh_orchestrator_service import _result

    return _result(
        entry,
        context,
        started=0.0,
        action_type=REFRESHED,
        status="GREEN",
        refreshed=True,
        freshness="fixture refreshed",
        found_artifacts=("fixture",),
        explanation=f"{entry.source_id} fixture refreshed",
        artifact="fixture",
    )


def _runner(command: list[str], cwd: Path, timeout: int) -> CommandResult:
    return CommandResult(0, "ok", "")


def test_nflverse_registry_uses_25_canonical_dataset_rows() -> None:
    registry = build_refresh_registry(settings=_settings())
    dataset_entries = [
        entry for entry in registry if entry.source_kind == "public_structured_nfl_dataset"
    ]

    assert [entry.source_id for entry in dataset_entries] == [
        f"nflverse_{dataset_id}" for dataset_id in CANONICAL_DATASET_IDS
    ]
    assert len(dataset_entries) == 25
    assert "nflverse_weekly_stats" not in {entry.source_id for entry in dataset_entries}
    assert "nflverse_opportunity" not in {entry.source_id for entry in dataset_entries}
    assert all(entry.model_use_allowed is False for entry in dataset_entries)
    ff_rankings = next(
        entry for entry in dataset_entries if entry.source_id == "nflverse_ff_rankings"
    )
    assert ff_rankings.configured


def test_registry_contains_required_source_policy_fields() -> None:
    registry = build_refresh_registry(settings=_settings())
    sleeper = next(entry for entry in registry if entry.source_id == "sleeper_league_state")
    cfbd = next(entry for entry in registry if entry.source_id == "cfbd_college_football_data")

    assert sleeper.loader_category == "AUTO_QUICK"
    assert sleeper.enabled_in_quick_refresh is True
    assert sleeper.model_use_allowed is False
    assert cfbd.requires_api_key is True
    assert cfbd.required_env_vars == ("CFBD_API_KEY or NWR_CFBD_API_KEY_FILE",)


def test_quick_refresh_pulls_sleeper_and_dynastyprocess_only(tmp_path: Path) -> None:
    run = run_quick_refresh(
        status_root=tmp_path / "status",
        settings=_settings(),
        handlers={
            "sleeper_league_state": _fake_refreshed,
            "dynastyprocess_market_baseline": _fake_refreshed,
        },
        write_status=False,
    )
    refreshed = {row.source_id for row in run.results if row.action_type == REFRESHED}

    assert refreshed == {"sleeper_league_state", "dynastyprocess_market_baseline"}
    assert all(
        row.action_type != REFRESHED
        for row in run.results
        if row.source_id not in refreshed
    )


def test_full_safe_refresh_includes_nflverse_when_runner_exists(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    scripts = repo_root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "run_nflverse_refresh_v0.ps1").write_text("# runner", encoding="utf-8")
    shared_root = tmp_path / "shared"
    (shared_root / "vendor_spikes" / "nflverse" / "scratch" / "pydeps").mkdir(
        parents=True
    )

    run = run_full_safe_refresh(
        repo_root=repo_root,
        status_root=tmp_path / "status",
        shared_root=shared_root,
        settings=_settings(),
        command_runner=_runner,
        handlers={
            "sleeper_league_state": _fake_refreshed,
            "dynastyprocess_market_baseline": _fake_refreshed,
        },
        write_status=False,
    )
    nflverse = next(row for row in run.results if row.source_id == "nflverse_refresh_runner")

    assert nflverse.runner_exists is True
    assert nflverse.action_type == REFRESHED
    assert nflverse.refreshed is True
    assert nflverse.exit_code == "0"
    assert "nflverse_refresh_manifest.json" in nflverse.found_artifacts[-1]
    dataset_rows = [
        row for row in run.results if row.source_kind == "public_structured_nfl_dataset"
    ]
    assert [row.source_id for row in dataset_rows] == [
        f"nflverse_{dataset_id}" for dataset_id in CANONICAL_DATASET_IDS
    ]
    assert all(row.model_use_allowed is False for row in dataset_rows)
    assert all(row.training_allowed == "false" for row in dataset_rows)
    assert all(row.rank_logic_allowed == "false" for row in dataset_rows)
    assert any(row.status == "BLOCKED" for row in dataset_rows)


def test_nflverse_missing_runner_or_deps_returns_not_configured(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "scripts").mkdir(parents=True)

    run = run_full_safe_refresh(
        repo_root=repo_root,
        status_root=tmp_path / "status",
        shared_root=tmp_path / "shared",
        source_ids=["nflverse_refresh_runner"],
        settings=_settings(),
        command_runner=_runner,
        write_status=False,
    )
    nflverse = next(row for row in run.results if row.source_id == "nflverse_refresh_runner")

    assert nflverse.action_type == ACTION_NOT_CONFIGURED
    assert nflverse.refreshed is False
    assert "not configured" in nflverse.user_explanation
    assert "runner missing" in nflverse.user_explanation


def test_nflverse_dataset_rows_are_refresh_health_only(tmp_path: Path) -> None:
    run = run_full_safe_refresh(
        status_root=tmp_path / "status",
        shared_root=tmp_path / "shared",
        source_ids=["nflverse_player_stats_weekly", "nflverse_ff_rankings"],
        settings=_settings(),
        write_status=False,
    )
    by_source = {row.source_id: row for row in run.results}
    weekly = by_source["nflverse_player_stats_weekly"]
    rankings = by_source["nflverse_ff_rankings"]

    assert weekly.action_type == ACTION_CHECK_ONLY
    assert weekly.refreshed is False
    assert weekly.status == "YELLOW"
    assert weekly.dataset_id == "player_stats_weekly"
    assert weekly.dataset_row_count == "Not enough information"
    assert weekly.full_safe_refresh_health == "YELLOW"
    assert "zero/false/healthy/clean" in weekly.user_message
    assert rankings.action_type == ACTION_CHECK_ONLY
    assert rankings.refreshed is False
    assert rankings.status == "BLOCKED"
    assert rankings.execution_status == "blocked_policy"
    assert rankings.model_use_allowed is False


def test_full_safe_refresh_reports_cfbd_not_configured_without_key(tmp_path: Path) -> None:
    run = run_full_safe_refresh(
        status_root=tmp_path / "status",
        settings=_settings(cfbd_api_key=""),
        handlers={
            "sleeper_league_state": _fake_refreshed,
            "dynastyprocess_market_baseline": _fake_refreshed,
        },
        command_runner=_runner,
        write_status=False,
    )
    cfbd = next(row for row in run.results if row.source_id == "cfbd_college_football_data")

    assert cfbd.action_type == ACTION_NOT_CONFIGURED
    assert cfbd.configured is False
    assert (
        cfbd.user_explanation
        == "CFBD_API_KEY/NWR_CFBD_API_KEY_FILE is not set; CFBD refresh is unavailable."
    )


def test_cfbd_is_eligible_only_when_configured() -> None:
    no_key = next(
        entry
        for entry in build_refresh_registry(settings=_settings(cfbd_api_key=""))
        if entry.source_id == "cfbd_college_football_data"
    )
    with_key = next(
        entry
        for entry in build_refresh_registry(settings=_settings(cfbd_api_key="secret"))
        if entry.source_id == "cfbd_college_football_data"
    )

    assert no_key.loader_category == "NOT_CONFIGURED"
    assert no_key.safe_to_pull is False
    assert with_key.loader_category == "AUTO_SLOW"
    assert with_key.safe_to_pull is True


def test_cfbd_with_mocked_api_key_runs_review_status_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class MockResponse:
        def __enter__(self) -> MockResponse:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'[{"school":"NWR Test State","conference":"Test"}]'

    def fake_urlopen(request, timeout: int) -> MockResponse:
        return MockResponse()

    monkeypatch.setattr(orchestrator.urllib.request, "urlopen", fake_urlopen)
    shared_root = tmp_path / "shared"
    run = run_full_safe_refresh(
        status_root=tmp_path / "status",
        shared_root=shared_root,
        source_ids=["cfbd_college_football_data"],
        settings=_settings(cfbd_api_key="mock-key"),
        write_status=False,
    )
    cfbd = next(row for row in run.results if row.source_id == "cfbd_college_football_data")
    manifest = Path(cfbd.artifact_updated)
    review_status = manifest.parent / "cfbd_review_status.csv"

    assert cfbd.action_type == REFRESHED
    assert cfbd.refreshed is True
    assert str(shared_root / "public_sources" / "cfbd") in cfbd.raw_cache_location
    assert review_status.exists()
    assert cfbd.tracked_artifacts_written == ""
    assert "reviewed/matched before model use" in cfbd.model_use_warning
    assert "No college identities became model input" in cfbd.user_explanation


def test_cfbd_review_status_schema_rejects_model_use(tmp_path: Path) -> None:
    path = tmp_path / "cfbd_review_status.csv"
    path.write_text(
        "\n".join(
            [
                "source_id,run_id,row_count,raw_cache_location,identity_gate_status,"
                "model_use_allowed,model_use_warning",
                "cfbd,run,1,C:/NWR_SHARED_DATA/public_sources/cfbd,REVIEW_REQUIRED,"
                "true,warning",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        orchestrator._validate_cfbd_review_status(path)


def test_manual_blocked_sources_are_never_pulled(tmp_path: Path) -> None:
    run = run_manual_sources_checklist(
        status_root=tmp_path / "status",
        settings=_settings(),
        write_status=False,
    )

    assert {row.action_type for row in run.results if row.loader_category == "MANUAL_BLOCKED"} == {
        BLOCKED_MANUAL
    }
    assert all(row.refreshed is False for row in run.results)


def test_frozen_latest_and_pinned_artifacts_are_never_mutated(tmp_path: Path) -> None:
    run = run_check_protected_artifacts(
        status_root=tmp_path / "status",
        settings=_settings(),
        write_status=False,
    )
    protected = {
        row.source_id: row
        for row in run.results
        if row.source_id
        in {"frozen_baseline_board", "latest_candidate_latest_approved", "pinned_manifest_hash"}
    }

    assert set(protected) == {
        "frozen_baseline_board",
        "latest_candidate_latest_approved",
        "pinned_manifest_hash",
    }
    assert all(row.action_type == ACTION_CHECK_ONLY for row in protected.values())
    assert all(row.refreshed is False for row in protected.values())


def test_check_only_sources_do_not_mutate_artifacts(tmp_path: Path) -> None:
    artifact = tmp_path / "protected.csv"
    artifact.write_text("a\n1\n", encoding="utf-8")
    before = artifact.read_text(encoding="utf-8")

    run = run_data_loader(
        loader_mode=CHECK_PROTECTED_ARTIFACTS,
        status_root=tmp_path / "status",
        source_ids=["frozen_baseline_board"],
        settings=_settings(),
        handlers={},
        write_status=False,
    )

    assert all(row.refreshed is False for row in run.results)
    assert artifact.read_text(encoding="utf-8") == before


def test_results_export_includes_required_columns(tmp_path: Path) -> None:
    run = run_quick_refresh(
        status_root=tmp_path / "status",
        settings=_settings(),
        handlers={
            "sleeper_league_state": _fake_refreshed,
            "dynastyprocess_market_baseline": _fake_refreshed,
        },
        write_status=False,
    )
    rows = refresh_results_table(run)
    csv_text = export_results_csv(run)

    validate_refresh_result_schema(rows)
    for column in (
        "action_type",
        "loader_mode",
        "user_explanation",
        "model_use_warning",
        "start_time",
        "end_time",
        "exit_code",
        "runner_path",
        "tracked_artifacts_written",
    ):
        assert column in rows[0]
        assert column in csv_text.splitlines()[0]


def test_no_source_writes_model_rank_or_candidate_outputs() -> None:
    registry = build_refresh_registry(settings=_settings(cfbd_api_key="secret"))

    for entry in registry:
        joined = " ".join(
            [
                entry.source_id,
                entry.raw_cache_location,
                " ".join(entry.expected_artifacts),
                entry.command_or_function,
            ]
        ).lower()
        if entry.source_id == "latest_candidate_latest_approved":
            assert entry.loader_category == "CHECK_ONLY"
            continue
        assert "latest_candidate" not in joined
        assert "latest_approved" not in joined
        assert "final_board_rank" not in joined
        assert entry.writes_tracked_artifact is False


def test_no_raw_shared_cache_files_are_tracked() -> None:
    tracked = [
        line.strip().replace("\\", "/").lower()
        for line in subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    ]

    forbidden_fragments = (
        "nwr_shared_data",
        "public_sources/cfbd",
        "scheduled_ingest/nflverse",
        "raw_nflverse",
        "raw_cfbd",
        "raw_gmail",
        "raw_vendor",
    )
    assert not [
        path for path in tracked if any(fragment in path for fragment in forbidden_fragments)
    ]


def test_status_file_payload_is_json_serializable(tmp_path: Path) -> None:
    run = run_quick_refresh(
        status_root=tmp_path / "status",
        settings=_settings(),
        handlers={
            "sleeper_league_state": _fake_refreshed,
            "dynastyprocess_market_baseline": _fake_refreshed,
        },
    )
    payload = json.loads(Path(run.status_path).read_text(encoding="utf-8"))

    assert payload["loader_mode"] == QUICK_REFRESH
    assert payload["run_id"] == run.run_id
    assert "action_type" in payload["results"][0]


def test_failed_source_does_not_crash_whole_refresh(tmp_path: Path) -> None:
    def failing_handler(entry, context) -> RefreshSourceResult:
        raise RuntimeError("planned failure")

    run = run_data_loader(
        loader_mode=QUICK_REFRESH,
        status_root=tmp_path / "status",
        source_ids=["dynastyprocess_market_baseline", "frozen_baseline_board"],
        handlers={"dynastyprocess_market_baseline": failing_handler},
        settings=_settings(),
        write_status=False,
    )
    by_source = {result.source_id: result for result in run.results}

    assert by_source["dynastyprocess_market_baseline"].action_type == FAILED
    assert by_source["frozen_baseline_board"].action_type == ACTION_CHECK_ONLY
    assert run.overall_status == "RED"


def test_refresh_result_schema_rejects_missing_columns() -> None:
    with pytest.raises(ValueError):
        validate_refresh_result_schema([{"source_id": "missing"}])
