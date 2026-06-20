from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "nflverse_normalize_snapshot_v0.py"
SPEC = importlib.util.spec_from_file_location("nflverse_normalize_snapshot_v0", MODULE_PATH)
assert SPEC is not None
NORMALIZER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nflverse_normalize_snapshot_v0"] = NORMALIZER
SPEC.loader.exec_module(NORMALIZER)


def test_dry_run_writes_report_and_no_candidates(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path / "snapshot")
    output_root = tmp_path / "lane_exchange"

    result = NORMALIZER.normalize_snapshot(
        snapshot_dir=snapshot,
        output_root=output_root,
        write_candidates=False,
        snapshot_label="dry_run",
    )

    counts = {package.package_name: len(package.rows) for package in result.packages}
    assert counts["stats_context/player_weekly_stats_display_context"] == 2
    assert counts["stats_context/player_usage_context"] == 2
    assert counts["stats_context/player_stats_crosscheck_report"] >= 3
    assert "stats_context/player_season_stats_display_context" not in counts
    assert result.report_path.exists()
    assert not output_root.exists()
    assert any("season_stats.csv missing" in warning for warning in result.warnings)


def test_write_candidates_creates_latest_candidate_only(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path / "snapshot", include_season_stats=True)
    output_root = tmp_path / "lane_exchange"

    result = NORMALIZER.normalize_snapshot(
        snapshot_dir=snapshot,
        output_root=output_root,
        write_candidates=True,
        snapshot_label="candidate",
    )

    package_names = {package.package_name for package in result.packages}
    assert package_names == set(NORMALIZER.PACKAGE_NAMES)
    for package_name in package_names:
        source_lane, short_name = package_name.split("/", 1)
        package_root = output_root / source_lane / short_name
        pointer_path = package_root / "latest_candidate.json"
        approved_path = package_root / "latest_approved.json"
        manifest_path = package_root / "candidate" / "manifest.json"
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        data_path = manifest_path.parent / pointer["data_file"]
        rows = _read_rows(data_path)

        assert pointer_path.exists()
        assert manifest_path.exists()
        assert not approved_path.exists()
        assert pointer["approval_status"] == "candidate"
        assert manifest["approval_status"] == "candidate"
        assert manifest["contains_private_value"] is False
        assert manifest["contains_market_data"] is False
        assert manifest["contains_adp"] is False
        assert manifest["not_latest_approved"] is True
        assert manifest["row_count"] == len(rows)
        assert pointer["row_count"] == len(rows)
        assert manifest["sha256"] == hashlib.sha256(data_path.read_bytes()).hexdigest()
        assert pointer["sha256"] == manifest["sha256"]


def test_quarantined_fields_are_excluded_from_display_packages(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path / "snapshot")

    result = NORMALIZER.normalize_snapshot(
        snapshot_dir=snapshot,
        output_root=tmp_path / "lane_exchange",
        write_candidates=False,
        snapshot_label="dry_run",
    )

    weekly = _package(result, "stats_context/player_weekly_stats_display_context")
    usage = _package(result, "stats_context/player_usage_context")
    for row in [*weekly.rows, *usage.rows]:
        serialized = ",".join(row)
        assert "fantasy_points" not in serialized
        assert "target_share" not in serialized
        assert "passing_epa" not in serialized
        assert "wopr" not in serialized
        assert "rank" not in serialized.lower()
        assert row["allowed_use"] == "display_stat_context_only"
        assert "private_value" in row["blocked_use"]

    assert "fantasy_points_ppr" in result.quarantine_summary["weekly_stats"]
    assert "target_share" in result.quarantine_summary["weekly_stats"]


def test_missing_optional_season_stats_is_yellow_not_crash(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path / "snapshot", include_season_stats=False)

    result = NORMALIZER.normalize_snapshot(
        snapshot_dir=snapshot,
        output_root=tmp_path / "lane_exchange",
        write_candidates=False,
        snapshot_label="dry_run",
    )

    assert _package(result, "stats_context/player_weekly_stats_display_context")
    assert _package(result, "stats_context/player_stats_crosscheck_report")
    assert any("season_stats.csv missing" in warning for warning in result.warnings)
    assert not any(
        package.package_name == "stats_context/player_season_stats_display_context"
        for package in result.packages
    )


def test_missing_required_sources_fails_closed(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    _write_json(snapshot / "snapshot_metadata.json", {"snapshot_label": "empty"})

    try:
        NORMALIZER.normalize_snapshot(
            snapshot_dir=snapshot,
            output_root=tmp_path / "lane_exchange",
            write_candidates=False,
        )
    except NORMALIZER.NormalizationError as exc:
        assert "neither weekly_stats.csv nor snap_counts.csv" in str(exc)
    else:
        raise AssertionError("expected missing source failure")


def _package(result: Any, package_name: str) -> Any:
    return next(package for package in result.packages if package.package_name == package_name)


def _write_snapshot(snapshot: Path, *, include_season_stats: bool = False) -> Path:
    snapshot.mkdir(parents=True)
    _write_json(
        snapshot / "snapshot_metadata.json",
        {
            "snapshot_label": "fake_nflverse_snapshot",
            "created_at": "2026-06-20T21:25:00+00:00",
            "datasets": [
                {
                    "name": "weekly_stats",
                    "status": "ok",
                    "row_count": 2,
                    "column_count": 15,
                    "warning": "weekly quarantine fields exist",
                },
                {
                    "name": "snap_counts",
                    "status": "ok",
                    "row_count": 2,
                    "column_count": 9,
                    "warning": "",
                },
            ],
        },
    )
    _write_csv(
        snapshot / "weekly_stats.csv",
        [
            {
                "player_id": "p1",
                "player_name": "Drake Maye",
                "position": "QB",
                "season": "2025",
                "week": "1",
                "team": "NE",
                "attempts": "31",
                "completions": "21",
                "passing_yards": "240",
                "passing_tds": "2",
                "passing_epa": "4.2",
                "fantasy_points_ppr": "22.1",
                "target_share": "",
                "nwr_private_value": "forbidden",
                "market_rank": "forbidden",
            },
            {
                "player_id": "p2",
                "player_name": "Jaylen Warren",
                "position": "RB",
                "season": "2025",
                "week": "1",
                "team": "PIT",
                "carries": "12",
                "rushing_yards": "70",
                "targets": "4",
                "receptions": "3",
                "receiving_yards": "28",
                "wopr": "0.1",
                "rank_score": "forbidden",
            },
        ],
    )
    _write_csv(
        snapshot / "snap_counts.csv",
        [
            {
                "player": "Drake Maye",
                "position": "QB",
                "season": "2025",
                "week": "1",
                "team": "NE",
                "offense_snaps": "60",
                "offense_pct": "0.95",
                "snap_share": "0.95",
                "sort_key": "forbidden",
            },
            {
                "player": "Jaylen Warren",
                "position": "RB",
                "season": "2025",
                "week": "1",
                "team": "PIT",
                "offense_snaps": "28",
                "offense_pct": "0.44",
                "snap_share": "0.44",
                "sort_key": "forbidden",
            },
        ],
    )
    if include_season_stats:
        _write_csv(
            snapshot / "season_stats.csv",
            [
                {
                    "player_id": "p1",
                    "player_name": "Drake Maye",
                    "position": "QB",
                    "season": "2025",
                    "team": "NE",
                    "attempts": "500",
                    "passing_yards": "3900",
                    "fantasy_points": "300",
                }
            ],
        )
    return snapshot


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    headers: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                headers.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
