"""Synthetic-only tests for deterministic ESPN/Flaim snapshot ingestion."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest

from scripts.refresh_espn_flaim_snapshot import main as importer_main
from src.application.desktop_facade import DesktopBackendFacade
from src.services.espn_flaim_snapshot_import_service import (
    EspnSnapshotImportError,
    SnapshotImportExpectations,
    activate_snapshot,
    load_snapshot_input,
    prepare_snapshot_import,
    transform_flaim_raw_capture,
)
from src.services.espn_flaim_snapshot_service import (
    espn_flaim_snapshot_path,
    load_espn_flaim_snapshot,
)
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]
LEAGUE_NAME = "Synthetic Test ESPN League"
LEAGUE_ID = "SYNTHETIC-ESPN-4242"
TEAM_ID = "synthetic-owner-team-7"
TEAM_NAME = "Synthetic Test Owner Team"


def _espn_profile(tmp_path: Path) -> tuple[Path, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="10_TEAM_1QB_STANDARD", league_name=LEAGUE_NAME
    )
    profile_id = created.data["profile"]["profileId"]
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="espn"))
    return store, profile_id


def _raw_capture(profile_id: str, *, player_name: str = "Synthetic Starter") -> dict[str, Any]:
    return {
        "capture_schema": "nwr_espn_flaim_raw_capture_v1",
        "profile_id": profile_id,
        "retrieved_at_utc": "2026-09-22T06:30:00Z",
        "get_league_info": {
            "league_id": LEAGUE_ID,
            "league_name": LEAGUE_NAME,
            "season": 2026,
            "team_count": 10,
            "owner_team_id": TEAM_ID,
            "owner_team_name": TEAM_NAME,
            "scoring_settings": [
                {"name": "passingYards", "value": 0.04, "nwr_setting": "pass_yard"},
                {"name": "providerOnlyModifier", "value": 1.5, "nwr_setting": None},
            ],
            "provider_as_of_utc": None,
        },
        "get_roster": {
            "team_id": TEAM_ID,
            "team_name": TEAM_NAME,
            "players": [
                {
                    "player_id": "synthetic-player-1",
                    "player_name": player_name,
                    "position": "rb",
                    "pro_team": "syn",
                    "slot": "STARTER",
                },
                {
                    "player_id": "synthetic-player-2",
                    "player_name": "Synthetic Reserve",
                    "position": "wr",
                    "pro_team": "syn",
                    "slot": "RESERVE",
                },
            ],
        },
        "get_free_agents": {
            "coverage": "BOUNDED",
            "bound_description": "Synthetic fixture: first 100 rows, not a complete pool",
            "players": [
                {
                    "player_id": "synthetic-free-agent-1",
                    "player_name": "Synthetic Free Agent",
                    "position": "te",
                    "pro_team": "syn",
                }
            ],
        },
    }


def _expectations() -> SnapshotImportExpectations:
    return SnapshotImportExpectations(
        provider_league_id=LEAGUE_ID,
        owner_team_id=TEAM_ID,
        owner_team_name=TEAM_NAME,
    )


def _write_json(path: Path, document: object) -> None:
    path.write_text(json.dumps(document), encoding="utf-8")


def test_raw_capture_transforms_validates_and_activates_end_to_end(tmp_path: Path) -> None:
    store, profile_id = _espn_profile(tmp_path)
    source = tmp_path / "synthetic_flaim_capture.json"
    _write_json(source, _raw_capture(profile_id))

    profile, snapshot, source_hash = prepare_snapshot_import(
        redraft_root=store,
        profile_id=profile_id,
        input_path=source,
        input_kind="raw",
        expectations=_expectations(),
    )
    assert profile.profile_id == profile_id
    assert snapshot.scoring_completeness == "PARTIAL"
    assert snapshot.available_player_pool_coverage == "BOUNDED"
    assert snapshot.roster[0].player_name == "Synthetic Starter"

    result = activate_snapshot(
        redraft_root=store,
        snapshot=snapshot,
        input_path=source,
        source_sha256=source_hash,
        imported_at_utc="2026-09-22T07:00:00Z",
    )
    loaded = load_espn_flaim_snapshot(store, profile_id)
    assert loaded is not None
    assert loaded.profile_id == profile_id
    assert loaded.imported_at_utc == "2026-09-22T07:00:00Z"
    assert loaded.source_capture_sha256 == source_hash
    assert loaded.source_capture_name == source.name
    assert result.backup_path is None
    assert result.target_path == espn_flaim_snapshot_path(store, profile_id)
    assert not tuple(result.target_path.parent.glob("*.tmp"))


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda raw: raw["get_roster"].pop("players"), "get_roster.players must be a JSON list"),
        (
            lambda raw: raw["get_free_agents"].update({"coverage": "COMPLETE"}),
            "coverage=COMPLETE is forbidden",
        ),
        (
            lambda raw: raw["get_roster"].update({"team_id": "wrong-team"}),
            "team_id does not match",
        ),
    ],
)
def test_malformed_or_dishonest_raw_capture_is_rejected_clearly(
    tmp_path: Path, mutate: Any, message: str
) -> None:
    _store, profile_id = _espn_profile(tmp_path)
    raw = _raw_capture(profile_id)
    mutate(raw)
    with pytest.raises(EspnSnapshotImportError, match=message):
        transform_flaim_raw_capture(raw)


def test_atomic_target_replace_failure_preserves_previous_good_snapshot(
    tmp_path: Path,
) -> None:
    store, profile_id = _espn_profile(tmp_path)
    first_source = tmp_path / "first.json"
    _write_json(first_source, _raw_capture(profile_id, player_name="Previous Good Player"))
    first = load_snapshot_input(first_source, input_kind="raw")
    activate_snapshot(
        redraft_root=store,
        snapshot=first,
        input_path=first_source,
        source_sha256="1" * 64,
        imported_at_utc="2026-09-22T07:00:00Z",
    )
    target = espn_flaim_snapshot_path(store, profile_id)
    previous_bytes = target.read_bytes()

    second_source = tmp_path / "second.json"
    _write_json(second_source, _raw_capture(profile_id, player_name="Replacement Player"))
    second = load_snapshot_input(second_source, input_kind="raw")

    def _fail_only_target(
        source: str | os.PathLike[str], destination: str | os.PathLike[str]
    ) -> None:
        if Path(destination) == target:
            raise OSError("synthetic failure before atomic target replacement")
        os.replace(source, destination)

    with pytest.raises(EspnSnapshotImportError, match="Atomic write failed"):
        activate_snapshot(
            redraft_root=store,
            snapshot=second,
            input_path=second_source,
            source_sha256="2" * 64,
            imported_at_utc="2026-09-22T08:00:00Z",
            replace_func=_fail_only_target,
        )
    assert target.read_bytes() == previous_bytes
    assert not tuple(target.parent.glob("*.tmp"))


def test_replacement_never_silently_overwrites_and_preserves_exact_backup(tmp_path: Path) -> None:
    store, profile_id = _espn_profile(tmp_path)
    first_source = tmp_path / "first.json"
    _write_json(first_source, _raw_capture(profile_id, player_name="Previous Good Player"))
    first = load_snapshot_input(first_source, input_kind="raw")
    activate_snapshot(
        redraft_root=store,
        snapshot=first,
        input_path=first_source,
        source_sha256="1" * 64,
        imported_at_utc="2026-09-22T07:00:00Z",
    )
    target = espn_flaim_snapshot_path(store, profile_id)
    previous_bytes = target.read_bytes()

    second_source = tmp_path / "second.json"
    _write_json(second_source, _raw_capture(profile_id, player_name="Replacement Player"))
    second = load_snapshot_input(second_source, input_kind="raw")
    result = activate_snapshot(
        redraft_root=store,
        snapshot=second,
        input_path=second_source,
        source_sha256="2" * 64,
        imported_at_utc="2026-09-22T08:00:00Z",
    )
    assert result.backup_path is not None
    assert result.backup_path.read_bytes() == previous_bytes
    assert target.read_bytes() != previous_bytes
    assert load_espn_flaim_snapshot(store, profile_id).roster[0].player_name == "Replacement Player"  # type: ignore[union-attr]


def test_emergency_manual_snapshot_defaults_to_preview_then_activates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store, profile_id = _espn_profile(tmp_path)
    snapshot = transform_flaim_raw_capture(_raw_capture(profile_id))
    manual = tmp_path / "synthetic_manual_snapshot.json"
    _write_json(manual, asdict(snapshot))
    args = [
        "--profile-id",
        profile_id,
        "--input",
        str(manual),
        "--input-kind",
        "snapshot",
        "--expected-provider-league-id",
        LEAGUE_ID,
        "--expected-owner-team-id",
        TEAM_ID,
        "--expected-owner-team-name",
        TEAM_NAME,
        "--redraft-root",
        str(store),
    ]
    assert importer_main(args) == 0
    preview_output = capsys.readouterr().out
    assert "PREVIEW ONLY" in preview_output
    assert not espn_flaim_snapshot_path(store, profile_id).exists()

    assert importer_main([*args, "--activate"]) == 0
    activation_output = capsys.readouterr().out
    assert "ACTIVATED:" in activation_output
    assert espn_flaim_snapshot_path(store, profile_id).exists()


def test_identity_mismatch_rejects_before_any_write(tmp_path: Path) -> None:
    store, profile_id = _espn_profile(tmp_path)
    source = tmp_path / "wrong_identity.json"
    raw = _raw_capture(profile_id)
    raw["get_league_info"]["league_name"] = "Different Synthetic League"
    _write_json(source, raw)
    with pytest.raises(EspnSnapshotImportError, match="Identity validation failed"):
        prepare_snapshot_import(
            redraft_root=store,
            profile_id=profile_id,
            input_path=source,
            input_kind="raw",
            expectations=_expectations(),
        )
    assert not espn_flaim_snapshot_path(store, profile_id).exists()


def test_manual_snapshot_cannot_claim_complete_scoring_without_every_mapping(
    tmp_path: Path,
) -> None:
    _store, profile_id = _espn_profile(tmp_path)
    snapshot = transform_flaim_raw_capture(_raw_capture(profile_id))
    dishonest = asdict(snapshot)
    dishonest["scoring_completeness"] = "COMPLETE"
    manual = tmp_path / "dishonest_complete_snapshot.json"
    _write_json(manual, dishonest)

    with pytest.raises(EspnSnapshotImportError, match="Use PARTIAL or UNKNOWN"):
        load_snapshot_input(manual, input_kind="snapshot")
