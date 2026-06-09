from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.lve_role_usage_service import (
    ROLE_USAGE_FEATURE_HEADER,
    derive_lve_role_usage_feature_rows,
    write_lve_role_usage_feature_rows,
)
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

TEMPLATE_ROOT = Path("templates/real_data_inputs/nflverse_stats_upgrade")


def test_wr_role_security_uses_route_target_and_snap_context(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root, "p_wr", "Receiver One", "WR", targets="10")
    _write_snap_rows(source_root, "p_wr", "Receiver One", "WR", offense_pct="88")
    _write_participation_rows(
        source_root,
        "p_wr",
        "Receiver One",
        "WR",
        route_participation_proxy="82",
        targets_per_dropback_snap_proxy="0.22",
    )
    _write_depth_rows(source_root, "p_wr", "Receiver One", "WR", pos_rank="1")

    result = derive_lve_role_usage_feature_rows(source_root)
    row = result.rows[0]

    assert result.status == "ready"
    assert row["position"] == "WR"
    assert row["role_security"] > 80
    assert row["route_role_score"] == 82
    assert row["scoring_effect"] == "derived role/usage features only; no model mutation"


def test_wr_target_earning_uses_target_share_wopr_and_air_yards(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(
        source_root,
        "p_wr",
        "Receiver One",
        "WR",
        targets="7",
        target_share="0.31",
        air_yards_share="0.43",
        wopr="0.80",
    )
    _write_snap_rows(source_root, "p_wr", "Receiver One", "WR", offense_pct="84")
    _write_participation_rows(
        source_root,
        "p_wr",
        "Receiver One",
        "WR",
        route_participation_proxy="80",
        targets_per_dropback_snap_proxy="0.18",
    )
    _write_depth_rows(source_root, "p_wr", "Receiver One", "WR", pos_rank="1")

    row = derive_lve_role_usage_feature_rows(source_root).rows[0]

    assert row["target_earning_stability_score"] > 90
    assert row["target_earning_source_detail"] == (
        "targets_per_game=7.0;target_share=0.31;air_yards_share=0.43;wopr=0.8"
    )
    assert row["role_security"] > 80


def test_te_route_gate_caps_blocking_profile(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root, "p_te", "Tight End One", "TE", targets="1")
    _write_snap_rows(source_root, "p_te", "Tight End One", "TE", offense_pct="90")
    _write_participation_rows(
        source_root,
        "p_te",
        "Tight End One",
        "TE",
        route_participation_proxy="25",
        targets_per_dropback_snap_proxy="0.03",
    )
    _write_depth_rows(source_root, "p_te", "Tight End One", "TE", pos_rank="1")

    row = derive_lve_role_usage_feature_rows(source_root).rows[0]

    assert row["role_security"] <= 40
    assert "te_route_role_gate" in row["warnings"]


def test_rb_workload_earning_blends_rushes_targets_and_snaps(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(
        source_root,
        "p_rb",
        "Runner One",
        "RB",
        rushing_attempts="18",
        targets="4",
    )
    _write_snap_rows(source_root, "p_rb", "Runner One", "RB", offense_pct="68")
    _write_participation_rows(
        source_root,
        "p_rb",
        "Runner One",
        "RB",
        route_participation_proxy="45",
        targets_per_dropback_snap_proxy="0.10",
    )
    _write_depth_rows(source_root, "p_rb", "Runner One", "RB", pos_rank="1")

    row = derive_lve_role_usage_feature_rows(source_root).rows[0]

    assert row["workload_earning_score"] > 85
    assert row["role_security"] > 70


def test_role_usage_merges_same_identity_when_source_names_differ(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_snap_rows(source_root, "p_wr", "Receiver One", "WR", offense_pct="72")
    _write_rows(
        source_root / "nflverse_depth_chart_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_depth_chart_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "0",
                "team": "SF",
                "gsis_id": "p_wr",
                "player_name": "Receiver One III",
                "position": "WR",
                "pos_rank": "2",
                "depth_chart_role_score": "70",
                "schema_version": "test",
            }
        ],
    )

    rows = derive_lve_role_usage_feature_rows(source_root).rows
    row = rows[0]

    assert len(rows) == 1
    assert row["player_name"] == "Receiver One"
    assert row["snap_share_score"] == 72.0
    assert row["depth_chart_role_score"] == 70.0
    assert "missing_depth_chart" not in row["warnings"]


def test_role_usage_blocks_when_raw_contract_invalid(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    (source_root / "nflverse_snap_counts_weekly.csv").write_text("bad,header\n", encoding="utf-8")

    result = derive_lve_role_usage_feature_rows(source_root)

    assert result.status == "blocked"
    assert result.rows == ()


def test_role_usage_write_uses_contract_header(tmp_path: Path) -> None:
    output_path = tmp_path / "role" / "lve_role_usage_features.csv"

    write_lve_role_usage_feature_rows(output_path, ())

    with output_path.open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == ROLE_USAGE_FEATURE_HEADER


def _copy_templates(tmp_path: Path) -> Path:
    target = tmp_path / "nflverse_stats_upgrade"
    shutil.copytree(TEMPLATE_ROOT, target)
    return target


def _write_player_stats(
    source_root: Path,
    player_id: str,
    player_name: str,
    position: str,
    *,
    rushing_attempts: str = "",
    targets: str = "",
    target_share: str = "",
    air_yards_share: str = "",
    wopr: str = "",
) -> None:
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "player_id": player_id,
                "player_name": player_name,
                "position": position,
                "team": "SF",
                "rushing_attempts": rushing_attempts,
                "targets": targets,
                "target_share": target_share,
                "air_yards_share": air_yards_share,
                "wopr": wopr,
            }
        ],
    )


def _write_snap_rows(
    source_root: Path,
    player_id: str,
    player_name: str,
    position: str,
    *,
    offense_pct: str,
) -> None:
    _write_rows(
        source_root / "nflverse_snap_counts_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_snap_counts_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "game_id": "2025_01_SF_ARI",
                "gsis_id": player_id,
                "player_name": player_name,
                "position": position,
                "team": "SF",
                "offense_snaps": "60",
                "offense_pct": offense_pct,
            }
        ],
    )


def _write_participation_rows(
    source_root: Path,
    player_id: str,
    player_name: str,
    position: str,
    *,
    route_participation_proxy: str,
    targets_per_dropback_snap_proxy: str,
) -> None:
    _write_rows(
        source_root / "nflverse_participation_player_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_participation_player_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "team": "SF",
                "gsis_id": player_id,
                "player_name": player_name,
                "position": position,
                "offensive_plays_on_field": "60",
                "team_offensive_plays": "65",
                "dropbacks_on_field": "35",
                "team_dropbacks": "40",
                "route_participation_proxy": route_participation_proxy,
                "targets": "8",
                "targets_per_dropback_snap_proxy": targets_per_dropback_snap_proxy,
                "confidence": "90",
            }
        ],
    )


def _write_depth_rows(
    source_root: Path,
    player_id: str,
    player_name: str,
    position: str,
    *,
    pos_rank: str,
) -> None:
    _write_rows(
        source_root / "nflverse_depth_chart_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_depth_chart_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "team": "SF",
                "gsis_id": player_id,
                "player_name": player_name,
                "position": position,
                "pos_rank": pos_rank,
                "depth_chart_role_score": "100",
                "schema_version": "test",
            }
        ],
    )


def _write_rows(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
