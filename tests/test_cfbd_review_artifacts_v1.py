from __future__ import annotations

from pathlib import Path

from scripts.build_cfbd_review_artifacts_v1 import (
    COVERAGE_COLUMNS,
    IDENTITY_COLUMNS,
    MANIFEST_COLUMNS,
    PRODUCTION_COLUMNS,
    PullResult,
    build_coverage_rows,
    build_identity_rows,
    build_manifest_rows,
    build_production_rows,
)


def test_cfbd_identity_review_rows_enforce_review_only_flags() -> None:
    rows = build_identity_rows(
        "run-1",
        [
            {
                "_nwr_season": 2025,
                "id": 123,
                "firstName": "Test",
                "lastName": "Player",
                "team": "Alabama",
                "position": "WR",
                "height": "6-1",
                "weight": 205,
                "homeCity": "Mobile",
                "homeState": "AL",
                "homeCountry": "USA",
            }
        ],
    )

    assert tuple(rows[0]) == IDENTITY_COLUMNS
    assert rows[0]["model_use_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"
    assert rows[0]["identity_review_required"] == "true"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["candidate_nwr_player_id"] == ""
    assert rows[0]["candidate_sleeper_id"] == ""
    assert rows[0]["match_status"] == "unmatched_review_required"


def test_cfbd_production_review_rows_enforce_review_only_flags() -> None:
    rows = build_production_rows(
        "run-1",
        [
            {
                "season": 2025,
                "playerId": "abc",
                "player": "Test Player",
                "team": "Alabama",
                "position": "RB",
                "category": "rushing",
                "statType": "YDS",
                "stat": "1000",
            },
            {
                "season": 2025,
                "playerId": "abc",
                "player": "Test Player",
                "team": "Alabama",
                "position": "RB",
                "category": "rushing",
                "statType": "G",
                "stat": "12",
            },
        ],
    )

    assert tuple(rows[0]) == PRODUCTION_COLUMNS
    assert rows[0]["games"] == "12"
    assert rows[0]["stat_1_name"] == "YDS"
    assert rows[0]["identity_review_required"] == "true"
    assert rows[0]["model_use_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"
    assert rows[0]["review_only"] == "true"


def test_cfbd_manifest_and_coverage_keep_raw_cache_outside_git(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "docs" / "cfbd"
    raw_path = Path(r"C:\NWR_SHARED_DATA\public_sources\cfbd\run-1\teams.json")
    pulls = [
        PullResult(
            dataset_name="cfbd_teams_fbs",
            season=2025,
            endpoint_or_source="/teams/fbs?year=2025",
            raw_cache_location=raw_path,
            rows=[{"id": 1, "school": "Alabama"}],
            refreshed=True,
            notes="fixture",
        )
    ]

    manifest = build_manifest_rows(
        run_id="run-1",
        run_timestamp="2026-06-24T00:00:00Z",
        pulls=pulls,
        artifact_dir=artifact_dir,
    )
    coverage = build_coverage_rows(run_id="run-1", pulls=pulls, artifact_dir=artifact_dir)

    assert tuple(manifest[0]) == MANIFEST_COLUMNS
    assert tuple(coverage[0]) == COVERAGE_COLUMNS
    assert manifest[0]["raw_cache_location"].startswith(
        r"C:\NWR_SHARED_DATA\public_sources\cfbd"
    )
    assert str(artifact_dir) in manifest[0]["tracked_artifact"]
    assert manifest[0]["model_use_allowed"] == "false"
    assert coverage[0]["training_allowed"] == "false"
    assert coverage[0]["identity_review_required"] == "true"
    assert coverage[0]["review_only"] == "true"
