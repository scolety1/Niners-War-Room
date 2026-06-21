from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.build_overnight_tune_dataset_v1 import (
    OvernightTuneV1BuildError,
    build_overnight_tune_dataset_v1,
)
from scripts.run_overnight_tune_v1 import run_overnight_tune_v1


def test_v1_builder_requires_actual_vendor_join(tmp_path: Path) -> None:
    input_dir = _write_input_dataset(tmp_path / "input")
    vendor_root = tmp_path / "vendor_archive"
    (vendor_root / "02_canonical").mkdir(parents=True)

    try:
        build_overnight_tune_dataset_v1(
            input_dataset_dir=input_dir,
            output_root=tmp_path / "tune",
            vendor_archive_root=vendor_root,
        )
    except OvernightTuneV1BuildError as exc:
        assert "no vendor feature rows parsed" in str(exc)
    else:
        raise AssertionError("expected V1 to stop before a no-vendor full run")


def test_v1_builder_writes_expanded_grid_and_vendor_reports(tmp_path: Path) -> None:
    input_dir = _write_input_dataset(tmp_path / "input")
    vendor_root = _write_vendor_archive(tmp_path / "vendor_archive")
    tune_root = tmp_path / "tune"

    result = build_overnight_tune_dataset_v1(
        input_dataset_dir=input_dir,
        output_root=tune_root,
        vendor_archive_root=vendor_root,
    )

    grid = pd.read_csv(result.grid_manifest_path)
    coverage = pd.read_csv(tune_root / "VENDOR_FEATURE_JOIN_COVERAGE.csv")
    blocked = pd.read_csv(tune_root / "VENDOR_FEATURE_BLOCKED_FIELDS.csv")
    manifest = json.loads((tune_root / "tune_input_manifest_v1.json").read_text())

    assert result.vendor_ready is True
    assert result.planned_fit_count >= 500
    assert grid.groupby("position").size().min() >= 100
    assert grid["feature_family"].eq("VENDOR_YELLOW_CHALLENGER").any()
    assert coverage["joined_rows"].sum() > 0
    assert "RK" in set(blocked["source_field"])
    assert manifest["vendor_ready"] is True
    assert (tune_root / "V0_SMALL_GRID_DIAGNOSIS.md").exists()


def test_v1_runner_executes_capped_expanded_grid(tmp_path: Path) -> None:
    input_dir = _write_input_dataset(tmp_path / "input")
    vendor_root = _write_vendor_archive(tmp_path / "vendor_archive")
    tune_root = tmp_path / "tune"
    build_overnight_tune_dataset_v1(
        input_dataset_dir=input_dir,
        output_root=tune_root,
        vendor_archive_root=vendor_root,
    )

    result = run_overnight_tune_v1(
        dataset_root=tune_root,
        output_root=tune_root,
        positions=["QB"],
        time_budget_minutes=1,
        resume=False,
        full_run=True,
        confirm_full_run=True,
        require_expanded_grid=True,
        require_vendor_challengers=True,
        max_fits=5,
    )

    position = pd.read_csv(result.position_results_path)
    manifest = pd.read_csv(result.run_manifest_path)
    grid = pd.read_csv(tune_root / "V1_EXPANDED_PRE_RUN_GRID_MANIFEST.csv")

    assert len(grid) >= 500
    assert result.planned_fits == 5
    assert result.completed_fits == 3
    assert set(position["position"]) == {"QB"}
    assert "top_n_hit_rate" in position.columns
    assert "median_yearly_top_n_improvement" in position.columns
    assert "SAFE_RESEARCH_CANDIDATE" in set(position["candidate_label"]) or (
        "BASELINE_REFERENCE" in set(position["candidate_label"])
    )
    assert "PASS" in set(manifest["value"])


def _write_input_dataset(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    labels: list[dict[str, object]] = []
    for target_season in range(2019, 2026):
        feature_season = target_season - 1
        for position in ["QB", "RB", "WR", "TE"]:
            for index in range(10):
                player_id = f"{position.lower()}_{index}"
                base_points = _base_points(position, target_season, index)
                rows.append(
                    {
                        "player_id": player_id,
                        "feature_season": feature_season,
                        "target_season": target_season,
                        "player_name": f"{position} Player {index}",
                        "position": position,
                        "recent_team": "SF",
                        "feature_games": 12 + index,
                        "feature_nwr_points": base_points - 15,
                        "feature_nwr_ppg": (base_points - 15) / max(12 + index, 1),
                        "completions": 220 + index if position == "QB" else 0,
                        "attempts": 350 + index if position == "QB" else 0,
                        "passing_yards": 3000 + index * 50 if position == "QB" else 0,
                        "passing_tds": 20 + index if position == "QB" else 0,
                        "passing_interceptions": 8,
                        "passing_first_downs": 120 if position == "QB" else 0,
                        "passing_2pt_conversions": 0,
                        "carries": 180 + index
                        if position == "RB"
                        else 20
                        if position == "QB"
                        else 0,
                        "rushing_yards": 800 + index * 20
                        if position == "RB"
                        else 100
                        if position == "QB"
                        else 0,
                        "rushing_tds": 6 if position == "RB" else 1 if position == "QB" else 0,
                        "rushing_first_downs": 45 if position in {"QB", "RB"} else 0,
                        "rushing_2pt_conversions": 0,
                        "targets": 110 + index
                        if position in {"WR", "TE"}
                        else 40
                        if position == "RB"
                        else 0,
                        "receptions": 70 + index
                        if position in {"WR", "TE"}
                        else 28
                        if position == "RB"
                        else 0,
                        "receiving_yards": 900 + index * 30
                        if position in {"WR", "TE"}
                        else 220
                        if position == "RB"
                        else 0,
                        "receiving_tds": 7
                        if position in {"WR", "TE"}
                        else 2
                        if position == "RB"
                        else 0,
                        "receiving_first_downs": 48
                        if position in {"WR", "TE"}
                        else 12
                        if position == "RB"
                        else 0,
                        "receiving_2pt_conversions": 0,
                        "fumbles_lost": 1,
                        "offense_snaps": 650 + index * 5,
                        "offense_pct": 0.55 + index * 0.03,
                        "age_at_season_end": 25 + index,
                        "years_exp": 2 + index,
                        "draft_round": 2,
                        "draft_pick": 50 + index,
                        "draft_pick_log": 4.0,
                        "age_missing": 0,
                        "draft_capital_missing": 0,
                        "snap_pct_missing": 0,
                        "air_yards_missing": 0,
                        "is_active_any_week": 1,
                        "active_weeks": 16,
                        "depth_chart_best_rank": 1 + index,
                        "team_plays": 1000,
                        "team_pass_rate": 0.55,
                        "team_run_rate": 0.45,
                        "team_offensive_tds": 45,
                        "sacks_suffered": 30 if position == "QB" else 0,
                        "sack_yards_lost": 180 if position == "QB" else 0,
                        "sack_fumbles": 4 if position == "QB" else 0,
                        "sack_fumbles_lost": 2 if position == "QB" else 0,
                        "qb_carries": 20 if position == "QB" else 0,
                        "qb_rushing_yards": 100 if position == "QB" else 0,
                        "qb_rushing_tds": 1 if position == "QB" else 0,
                        "qb_scrambles": 12 if position == "QB" else 0,
                        "rushes_inside_20": 25 if position == "RB" else 0,
                        "rushes_inside_10": 12 if position == "RB" else 0,
                        "rushes_inside_5": 6 if position == "RB" else 0,
                        "goal_to_go_rushes": 5 if position == "RB" else 0,
                        "red_zone_tds": 4 if position == "RB" else 0,
                        "red_zone_first_downs": 12 if position == "RB" else 0,
                        "receiving_air_yards": 1100 if position in {"WR", "TE"} else 0,
                        "receiving_yards_after_catch": 300 if position in {"WR", "TE"} else 0,
                        "rushing_first_downs_per_carry": 0.25,
                        "receiving_first_downs_per_target": 0.40,
                        "receiving_first_downs_per_reception": 0.62,
                        "rushing_yards_per_carry": 4.5,
                        "receiving_yards_per_target": 8.5,
                        "receiving_yards_per_reception": 12.0,
                        "yards_per_target": 8.5,
                        "air_yards_per_target": 10.0,
                        "yac_per_reception": 4.0,
                    }
                )
                labels.append(
                    {
                        "player_id": player_id,
                        "target_season": target_season,
                        "target_player_name": f"{position} Player {index}",
                        "target_position": position,
                        "target_team": "SF",
                        "target_games": 14 + index,
                        "next_nwr_points": base_points + index * 2,
                        "next_nwr_ppg": (base_points + index * 2) / max(14 + index, 1),
                    }
                )
    full = pd.DataFrame(rows)
    baseline_columns = [
        "player_id",
        "feature_season",
        "target_season",
        "player_name",
        "position",
        "recent_team",
        "feature_games",
        "feature_nwr_points",
        "feature_nwr_ppg",
        "completions",
        "attempts",
        "passing_yards",
        "passing_tds",
        "passing_interceptions",
        "passing_first_downs",
        "passing_2pt_conversions",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "rushing_first_downs",
        "rushing_2pt_conversions",
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
        "receiving_first_downs",
        "receiving_2pt_conversions",
        "fumbles_lost",
        "offense_snaps",
        "offense_pct",
    ]
    full[baseline_columns].to_csv(root / "feature_dataset_v1_baseline.csv", index=False)
    full.to_csv(root / "feature_dataset_v1_clean_expanded.csv", index=False)
    pd.DataFrame(labels).to_csv(root / "labels_v1.csv", index=False)
    return root


def _write_vendor_archive(root: Path) -> Path:
    canonical = root / "02_canonical"
    for year in range(2021, 2025):
        _write_rotowire_receiving_advanced(canonical, year)
        _write_rotowire_receiving_redzone(canonical, year)
        _write_rotowire_rushing_advanced(canonical, year)
        _write_rotowire_rushing_redzone(canonical, year)
    _write_fantasypros_wr(canonical, 2021)
    return root


def _write_rotowire_receiving_advanced(canonical: Path, year: int) -> None:
    path = (
        canonical / "rotowire" / str(year) / "receiving" / f"rotowire_{year}_receiving_advanced.csv"
    )
    _write_two_header_csv(
        path,
        ["PlayerID", "Name", "Team", "Pos", "G", "Rts", "TPRR%", "YPRR", "AY.1", "TAR.1", "YAC%"],
        [
            ["1", "WR Player 0", "SF", "WR", "17", "520", "24.2", "2.4", "34.0", "26.0", "38.0"],
            ["2", "TE Player 0", "SF", "TE", "17", "410", "20.0", "1.9", "18.0", "19.0", "42.0"],
        ],
    )


def _write_rotowire_receiving_redzone(canonical: Path, year: int) -> None:
    path = (
        canonical / "rotowire" / str(year) / "receiving" / f"rotowire_{year}_receiving_redzone.csv"
    )
    _write_two_header_csv(
        path,
        ["PlayerID", "Name", "Team", "Pos", "G", "In20", "In10", "In5", "%Tm"],
        [["1", "WR Player 0", "SF", "WR", "17", "18", "9", "3", "24.0"]],
    )


def _write_rotowire_rushing_advanced(canonical: Path, year: int) -> None:
    path = canonical / "rotowire" / str(year) / "rushing" / f"rotowire_{year}_rushing_advanced.csv"
    _write_two_header_csv(
        path,
        [
            "PlayerID",
            "Name",
            "Team",
            "Pos",
            "G",
            "BT",
            "BT%",
            "YDS.1",
            "AVG",
            "%",
            "Stuffed",
            "In%",
        ],
        [["3", "RB Player 0", "SF", "RB", "17", "22", "9.2", "640", "3.2", "62.0", "18", "54.0"]],
    )


def _write_rotowire_rushing_redzone(canonical: Path, year: int) -> None:
    path = canonical / "rotowire" / str(year) / "rushing" / f"rotowire_{year}_rushing_redzone.csv"
    _write_two_header_csv(
        path,
        [
            "PlayerID",
            "Name",
            "Team",
            "Pos",
            "G",
            "In20",
            "In10",
            "In5",
            "%Tm",
            "In20.1",
            "In10.1",
            "In5.1",
        ],
        [["3", "RB Player 0", "SF", "RB", "17", "42", "22", "11", "38.0", "7", "5", "3"]],
    )


def _write_fantasypros_wr(canonical: Path, year: int) -> None:
    path = canonical / "fantasypros" / str(year) / "WR" / f"fantasypros_{year}_WR_advanced.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "Player": "WR Player 0 SF",
                "RK": 1,
                "YBC": 700,
                "AIR": 1100,
                "YAC": 340,
                "BRKTKL": 5,
                "% TM": 26,
                "DROP": 4,
                "RZ TGT": 18,
            }
        ]
    ).to_csv(path, index=False)


def _write_two_header_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = ",".join(f"unused_{index}" for index in range(len(header)))
    text += "\n" + ",".join(header)
    for row in rows:
        text += "\n" + ",".join(row)
    path.write_text(text + "\n", encoding="utf-8")


def _base_points(position: str, target_season: int, index: int) -> int:
    output = 80 + index * 12 + (target_season - 2019) * 7
    if position == "QB":
        return output + 120
    if position == "RB":
        return output + 80
    if position == "WR":
        return output + 70
    return output + 35
