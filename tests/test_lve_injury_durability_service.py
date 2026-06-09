from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.lve_injury_durability_service import (
    INJURY_DURABILITY_HEADER,
    derive_lve_injury_durability_rows,
    write_lve_injury_durability_rows,
)
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

TEMPLATE_ROOT = Path("templates/real_data_inputs/nflverse_stats_upgrade")


def test_healthy_player_gets_high_durability_with_no_report_rows(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root, "p_wr", "Receiver One", "WR", targets="8")
    _write_snap_rows(source_root, "p_wr", "Receiver One", "WR", offense_snaps="60")

    row = derive_lve_injury_durability_rows(source_root).rows[0]

    assert row["injury_durability_score"] == 100
    assert row["confidence"] == 90
    assert "no_injury_report_rows" in row["warnings"]


def test_current_out_rb_lower_body_injury_is_severe(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root, "p_rb", "Runner One", "RB")
    _write_snap_rows(source_root, "p_rb", "Runner One", "RB", offense_snaps="0")
    _write_injury_rows(
        source_root,
        [
            _injury_row(
                "p_rb",
                "Runner One",
                "RB",
                week="1",
                report_status="Out",
                practice_status="Did Not Participate",
                body_part="lower_body_knee",
            )
        ],
    )

    row = derive_lve_injury_durability_rows(source_root).rows[0]

    assert row["current_status_score"] == 58
    assert row["injury_durability_score"] < 35
    assert "current_injury_uncertainty" in row["risk_flags"]
    assert "rb_wr_lower_body_risk" in row["risk_flags"]


def test_recurrent_wr_soft_tissue_flags_same_area_risk(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root, "p_wr", "Receiver One", "WR", targets="6")
    _write_snap_rows(source_root, "p_wr", "Receiver One", "WR", offense_snaps="55")
    _write_injury_rows(
        source_root,
        [
            _injury_row(
                "p_wr",
                "Receiver One",
                "WR",
                week="1",
                report_status="Questionable",
                practice_status="Limited",
                body_part="lower_body_soft_tissue",
            ),
            _injury_row(
                "p_wr",
                "Receiver One",
                "WR",
                week="2",
                report_status="Questionable",
                practice_status="Limited",
                body_part="lower_body_soft_tissue",
            ),
            _injury_row(
                "p_wr",
                "Receiver One",
                "WR",
                week="3",
                report_status="Questionable",
                practice_status="Limited",
                body_part="lower_body_soft_tissue",
            ),
        ],
    )

    row = derive_lve_injury_durability_rows(source_root).rows[0]

    assert row["same_area_recurrence_count"] == 2
    assert "same_area_recurrence" in row["risk_flags"]
    assert row["lower_body_risk_score"] < 80


def test_qb_lower_body_penalty_is_lighter_than_rb(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_player_stats(source_root, "p_qb", "QB One", "QB", passing_yards="250")
    _write_snap_rows(source_root, "p_qb", "QB One", "QB", offense_snaps="60")
    _write_injury_rows(
        source_root,
        [
            _injury_row(
                "p_qb",
                "QB One",
                "QB",
                week="1",
                report_status="Questionable",
                practice_status="Limited",
                body_part="lower_body_ankle",
            )
        ],
    )

    row = derive_lve_injury_durability_rows(source_root).rows[0]

    assert row["injury_durability_score"] > 65
    assert "qb_rushing_ceiling_risk" not in row["risk_flags"]


def test_injury_durability_write_uses_contract_header(tmp_path: Path) -> None:
    output_path = tmp_path / "injury" / "lve_injury_durability_features.csv"

    write_lve_injury_durability_rows(output_path, ())

    with output_path.open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == INJURY_DURABILITY_HEADER


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
    targets: str = "",
    passing_yards: str = "",
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
                "targets": targets,
                "passing_yards": passing_yards,
            }
        ],
    )


def _write_snap_rows(
    source_root: Path,
    player_id: str,
    player_name: str,
    position: str,
    *,
    offense_snaps: str,
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
                "offense_snaps": offense_snaps,
                "offense_pct": "75",
            }
        ],
    )


def _injury_row(
    player_id: str,
    player_name: str,
    position: str,
    *,
    week: str,
    report_status: str,
    practice_status: str,
    body_part: str,
) -> dict[str, str]:
    return {
        "season": "2025",
        "week": week,
        "team": "SF",
        "gsis_id": player_id,
        "player_name": player_name,
        "position": position,
        "report_primary_injury": body_part,
        "report_status": report_status,
        "practice_primary_injury": body_part,
        "practice_status": practice_status,
        "normalized_body_part": body_part,
        "source_confidence": "90",
    }


def _write_injury_rows(source_root: Path, rows: list[dict[str, str]]) -> None:
    _write_rows(
        source_root / "nflverse_injuries_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_injuries_weekly.csv"],
        rows,
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
