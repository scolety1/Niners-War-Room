from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "nflverse_scheduled_pull_v0.py"
SPEC = importlib.util.spec_from_file_location("nflverse_scheduled_pull_v0", MODULE_PATH)
assert SPEC is not None
PULLER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nflverse_scheduled_pull_v0"] = PULLER
SPEC.loader.exec_module(PULLER)


def test_nflverse_pull_writes_snapshot_manifest_and_report(tmp_path: Path) -> None:
    result = PULLER.run_nflverse_pull(
        seasons=[2024, 2025],
        output_root=tmp_path,
        dataset_names=["weekly_stats", "season_stats"],
        snapshot_label="20260620_210000",
        loader_module=FakeNflreadpy(),
    )

    assert result.snapshot_dir == tmp_path / "20260620_210000"
    assert result.report_path.exists()
    assert result.metadata_path.exists()
    assert (result.snapshot_dir / "weekly_stats.csv").exists()
    assert (result.snapshot_dir / "season_stats.csv").exists()

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["creates_lane_exchange_packages"] is False
    assert metadata["updates_latest_candidate"] is False
    assert metadata["updates_latest_approved"] is False
    assert metadata["field_policy"]["no_private_value"] is True
    assert metadata["package_version"] == "0.1.5-test"

    datasets = {row["name"]: row for row in metadata["datasets"]}
    assert datasets["weekly_stats"]["status"] == "ok"
    assert datasets["weekly_stats"]["row_count"] == 3
    assert datasets["weekly_stats"]["column_count"] == 9
    assert "fantasy_points_ppr" in datasets["weekly_stats"]["quarantined_fields"]
    assert "target_share" in datasets["weekly_stats"]["quarantined_fields"]
    assert datasets["weekly_stats"]["matched_sample_players"] == [
        "Drake Maye",
        "Jaylen Warren",
        "Brian Thomas Jr",
        "Brian Thomas",
    ]
    assert {
        "query": "Brian Thomas",
        "matched_name": "Brian Thomas Jr",
        "match_type": "alias",
        "matched_on": "Brian Thomas Jr",
        "source_field": "player_name",
    } in datasets["weekly_stats"]["identity_matches"]
    assert datasets["weekly_stats"]["field_roles"]["player_name"] == ["player_name"]
    assert datasets["weekly_stats"]["field_roles"]["player_id"] == ["player_id"]
    assert datasets["weekly_stats"]["field_roles"]["team"] == ["team"]

    weekly_body = (result.snapshot_dir / "weekly_stats.csv").read_bytes()
    assert datasets["weekly_stats"]["sha256"] == hashlib.sha256(weekly_body).hexdigest()
    report = result.report_path.read_text(encoding="utf-8")
    assert "Stats are display/stat context only" in report
    assert "latest_approved" in report
    assert "Brian Thomas` matched source `Brian Thomas Jr`" in report
    assert str(result.snapshot_dir).startswith(str(tmp_path))


def test_skip_live_creates_report_without_raw_dataset_files(tmp_path: Path) -> None:
    result = PULLER.run_nflverse_pull(
        seasons=[2025],
        output_root=tmp_path,
        dataset_names=["weekly_stats"],
        snapshot_label="skip_live",
        skip_live=True,
    )

    assert result.metadata_path.exists()
    assert result.report_path.exists()
    assert not (result.snapshot_dir / "weekly_stats.csv").exists()

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dataset = metadata["datasets"][0]
    assert dataset["status"] == "skipped"
    assert dataset["warning"] == "YELLOW: skip_live requested"
    assert metadata["skip_live"] is True


def test_missing_nflreadpy_fails_safely(tmp_path: Path) -> None:
    with patch.object(PULLER.importlib, "import_module", side_effect=ModuleNotFoundError):
        try:
            PULLER.run_nflverse_pull(
                seasons=[2025],
                output_root=tmp_path,
                dataset_names=["weekly_stats"],
                snapshot_label="missing",
            )
        except PULLER.MissingNflreadpyError as exc:
            assert "Install it only in an approved local-only scratch/runtime" in str(exc)
        else:
            raise AssertionError("expected MissingNflreadpyError")

    assert not (tmp_path / "missing").exists()


def test_unsupported_dataset_is_rejected(tmp_path: Path) -> None:
    try:
        PULLER.run_nflverse_pull(
            seasons=[2025],
            output_root=tmp_path,
            dataset_names=["made_up_dataset"],
            snapshot_label="bad",
            loader_module=FakeNflreadpy(),
        )
    except PULLER.NflversePullError as exc:
        assert "unsupported dataset" in str(exc)
    else:
        raise AssertionError("expected unsupported dataset failure")


def test_loader_warning_is_reported_for_missing_optional_function(tmp_path: Path) -> None:
    result = PULLER.run_nflverse_pull(
        seasons=[2025],
        output_root=tmp_path,
        dataset_names=["opportunity"],
        snapshot_label="missing_loader",
        loader_module=FakeNflreadpy(),
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dataset = metadata["datasets"][0]
    assert dataset["status"] == "skipped"
    assert "YELLOW: no supported nflreadpy function" in dataset["warning"]


def test_expanded_dataset_loaders_are_supported_and_soft_quarantined(tmp_path: Path) -> None:
    result = PULLER.run_nflverse_pull(
        seasons=[2025],
        output_root=tmp_path,
        dataset_names=["rosters", "weekly_rosters", "participation", "opportunity"],
        snapshot_label="expanded",
        loader_module=ExpandedFakeNflreadpy(),
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    datasets = {row["name"]: row for row in metadata["datasets"]}

    assert datasets["rosters"]["status"] == "ok"
    assert datasets["rosters"]["function_name"] == "load_rosters"
    assert "years_exp" not in datasets["rosters"]["quarantined_fields"]
    assert "headshot_url" in datasets["rosters"]["quarantined_fields"]
    assert datasets["weekly_rosters"]["function_name"] == "load_rosters_weekly"
    assert datasets["participation"]["function_name"] == "load_participation"
    assert datasets["opportunity"]["function_name"] == "load_ff_opportunity"
    assert "pass_completions_exp" in datasets["opportunity"]["quarantined_fields"]
    assert "total_fantasy_points" in datasets["opportunity"]["quarantined_fields"]
    assert datasets["opportunity"]["warning"].startswith("YELLOW:")

    for file_name in (
        "rosters.csv",
        "weekly_rosters.csv",
        "participation.csv",
        "opportunity.csv",
    ):
        assert (result.snapshot_dir / file_name).exists()


def test_snap_counts_player_field_identity_matching(tmp_path: Path) -> None:
    result = PULLER.run_nflverse_pull(
        seasons=[2024, 2025],
        output_root=tmp_path,
        dataset_names=["snap_counts"],
        snapshot_label="snap_identity",
        loader_module=FakeNflreadpy(),
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dataset = metadata["datasets"][0]
    assert dataset["status"] == "ok"
    assert dataset["matched_sample_players"] == ["Brian Thomas Jr", "Brian Thomas", "Alec Pierce"]
    assert {
        "query": "Brian Thomas",
        "matched_name": "Brian Thomas Jr",
        "match_type": "alias",
        "matched_on": "Brian Thomas Jr",
        "source_field": "player",
    } in dataset["identity_matches"]
    assert dataset["field_roles"]["player_name"] == ["player"]
    assert dataset["field_roles"]["position"] == ["position"]
    assert dataset["field_roles"]["team"] == ["team"]


class FakeFrame:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.columns = list(rows[0]) if rows else []

    def to_dicts(self) -> list[dict[str, Any]]:
        return self._rows


class FakeNflreadpy:
    __version__ = "0.1.5-test"

    def import_weekly_data(self, seasons: list[int]) -> FakeFrame:
        assert seasons == [2024, 2025]
        return FakeFrame(
            [
                {
                    "season": 2024,
                    "week": 1,
                    "player_id": "p1",
                    "player_name": "Drake Maye",
                    "team": "NE",
                    "passing_yards": 120,
                    "targets": 0,
                    "fantasy_points_ppr": 10.2,
                    "target_share": 0,
                },
                {
                    "season": 2025,
                    "week": 1,
                    "player_id": "p2",
                    "player_name": "Jaylen Warren",
                    "team": "PIT",
                    "passing_yards": 0,
                    "targets": 4,
                    "fantasy_points_ppr": 11.0,
                    "target_share": 0.12,
                },
                {
                    "season": 2025,
                    "week": 1,
                    "player_id": "p3",
                    "player_name": "Brian Thomas Jr",
                    "team": "JAX",
                    "passing_yards": 0,
                    "targets": 8,
                    "fantasy_points_ppr": 16.4,
                    "target_share": 0.26,
                },
            ]
        )

    def import_seasonal_data(self, seasons: list[int]) -> FakeFrame:
        assert seasons == [2024, 2025]
        return FakeFrame(
            [
                {
                    "season": 2024,
                    "player_id": "p1",
                    "player_name": "Drake Maye",
                    "team": "NE",
                    "attempts": 338,
                    "carries": 54,
                    "receptions": 0,
                }
            ]
        )

    def import_snap_counts(self, seasons: list[int]) -> FakeFrame:
        assert seasons == [2024, 2025]
        return FakeFrame(
            [
                {
                    "season": 2025,
                    "week": 1,
                    "player": "Brian Thomas Jr",
                    "position": "WR",
                    "team": "JAX",
                    "offense_snaps": 55,
                    "offense_pct": 0.82,
                },
                {
                    "season": 2025,
                    "week": 1,
                    "player": "Alec Pierce",
                    "position": "WR",
                    "team": "IND",
                    "offense_snaps": 48,
                    "offense_pct": 0.74,
                },
            ]
        )


class ExpandedFakeNflreadpy:
    __version__ = "0.1.5-test"

    def load_rosters(self, seasons: list[int]) -> FakeFrame:
        assert seasons == [2025]
        return FakeFrame(
            [
                {
                    "season": 2025,
                    "team": "NE",
                    "position": "QB",
                    "full_name": "Drake Maye",
                    "gsis_id": "00-0039999",
                    "years_exp": 1,
                    "headshot_url": "https://example.invalid/maye.png",
                }
            ]
        )

    def load_rosters_weekly(self, seasons: list[int]) -> FakeFrame:
        assert seasons == [2025]
        return FakeFrame(
            [
                {
                    "season": 2025,
                    "week": 1,
                    "team": "PIT",
                    "position": "RB",
                    "full_name": "Jaylen Warren",
                    "status": "ACT",
                    "years_exp": 4,
                }
            ]
        )

    def load_participation(self, seasons: list[int]) -> FakeFrame:
        assert seasons == [2025]
        return FakeFrame(
            [
                {
                    "nflverse_game_id": "2025_01_NE_PIT",
                    "play_id": 42,
                    "possession_team": "NE",
                    "route": "go",
                    "offense_players": "00-0039999",
                }
            ]
        )

    def load_ff_opportunity(self, seasons: list[int]) -> FakeFrame:
        assert seasons == [2025]
        return FakeFrame(
            [
                {
                    "season": 2025,
                    "week": 1,
                    "posteam": "JAX",
                    "player_id": "p3",
                    "full_name": "Brian Thomas Jr",
                    "position": "WR",
                    "rec_attempt": 9,
                    "rec_air_yards": 110,
                    "receptions": 6,
                    "pass_completions_exp": 2.1,
                    "total_fantasy_points": 18.4,
                }
            ]
        )
