from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_overnight_tune_dataset_v0 import (
    FEATURE_FAMILIES,
    OvernightTuneBuildError,
    build_overnight_tune_dataset_v0,
)
from scripts.run_overnight_tune_v0 import run_overnight_tune_v0


def test_overnight_registry_labels_families_and_isolates_vendor(tmp_path: Path) -> None:
    input_dir = _write_input_dataset(tmp_path / "input")
    result = build_overnight_tune_dataset_v0(
        input_dataset_dir=input_dir,
        output_root=tmp_path / "tune",
        vendor_archive_root=tmp_path / "vendor_archive",
        snap_audit_doc=tmp_path / "snap_doc.md",
    )

    registry = pd.read_csv(result.feature_registry_path)
    variants = pd.read_csv(result.variant_plan_path)
    blocked = pd.read_csv(result.blocked_registry_path)

    assert set(FEATURE_FAMILIES).issubset(set(registry["feature_family"]))
    vendor = variants[variants["feature_family"].eq("VENDOR_YELLOW_CHALLENGER")]
    assert not vendor.empty
    assert vendor["include_in_dry_run"].astype(str).str.lower().eq("false").all()
    assert vendor["requires_vendor_join"].astype(str).str.lower().eq("true").all()
    assert "FantasyPros RK" in set(blocked["field_or_pattern"])
    assert result.vendor_archive_status == "missing"


def test_overnight_builder_rejects_blocked_fields(tmp_path: Path) -> None:
    input_dir = _write_input_dataset(tmp_path / "input")
    baseline = pd.read_csv(input_dir / "feature_dataset_v1_baseline.csv")
    baseline["FantasyPros RK"] = 1
    baseline.to_csv(input_dir / "feature_dataset_v1_baseline.csv", index=False)

    try:
        build_overnight_tune_dataset_v0(
            input_dataset_dir=input_dir,
            output_root=tmp_path / "tune",
            vendor_archive_root=tmp_path / "vendor_archive",
            snap_audit_doc=tmp_path / "snap_doc.md",
        )
    except OvernightTuneBuildError as exc:
        assert "blocked field" in str(exc)
    else:
        raise AssertionError("expected blocked field rejection")


def test_overnight_dry_run_writes_checkpoint_and_metrics(tmp_path: Path) -> None:
    input_dir = _write_input_dataset(tmp_path / "input")
    tune_root = tmp_path / "tune"
    build_overnight_tune_dataset_v0(
        input_dataset_dir=input_dir,
        output_root=tune_root,
        vendor_archive_root=tmp_path / "vendor_archive",
        snap_audit_doc=tmp_path / "snap_doc.md",
    )

    result = run_overnight_tune_v0(
        dataset_root=tune_root,
        output_root=tune_root,
        dry_run=True,
        positions=["QB"],
        evaluation_seasons=[2021, 2022],
        max_variants=3,
        max_seasons=2,
        min_train_rows=2,
        time_budget_minutes=1,
    )

    metrics = pd.read_csv(result.metrics_by_position_path)
    winners = pd.read_csv(result.winner_report_path)

    assert result.checkpoint_path.exists()
    assert result.predictions_path.exists()
    assert not metrics.empty
    assert "top_n_hit_rate" in metrics.columns
    assert "median_yearly_top_n_improvement" in metrics.columns
    assert set(winners["position"]) == {"QB"}
    assert result.sklearn_available is False


def _write_input_dataset(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    labels = []
    positions = ["QB", "RB", "WR", "TE"]
    for target_season in range(2019, 2024):
        feature_season = target_season - 1
        for position in positions:
            for index in range(6):
                player_id = f"{position.lower()}_{index}"
                base_points = 80 + index * 12 + (target_season - 2019) * 7
                if position == "QB":
                    base_points += 120
                elif position == "RB":
                    base_points += 80
                elif position == "WR":
                    base_points += 70
                else:
                    base_points += 35
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
        column
        for column in full.columns
        if column
        in {
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
        }
    ]
    full[baseline_columns].to_csv(root / "feature_dataset_v1_baseline.csv", index=False)
    full.to_csv(root / "feature_dataset_v1_clean_expanded.csv", index=False)
    pd.DataFrame(labels).to_csv(root / "labels_v1.csv", index=False)
    return root
