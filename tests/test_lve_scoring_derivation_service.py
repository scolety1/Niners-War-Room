from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.lve_scoring_derivation_service import (
    LVE_WEEKLY_SCORING_HEADER,
    derive_lve_weekly_scoring_rows,
    lve_weekly_scoring_summary_rows,
    write_lve_weekly_scoring_rows,
)
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

TEMPLATE_ROOT = Path("templates/real_data_inputs/nflverse_stats_upgrade")


def test_lve_scoring_constants_match_model_v4_rules_lock() -> None:
    rules_lock = Path("docs/model_v4/LEAGUE_RULES_LOCK.md").read_text(encoding="utf-8")

    assert "| Passing yards | 1 per 30 yards |" in rules_lock
    assert "| Passing TD | 3 |" in rules_lock
    assert "| Interception | -1 |" in rules_lock
    assert "| Rushing yards | 1 per 10 yards |" in rules_lock
    assert "| Rushing TD | 4 |" in rules_lock
    assert "| Receiving yards | 1 per 10 yards |" in rules_lock
    assert "| Receiving TD | 4 |" in rules_lock
    assert "| Return yards | 1 per 30 yards |" in rules_lock
    assert "| Return TD | 4 |" in rules_lock
    assert "| Reception | 0 |" in rules_lock
    assert "| Fumble lost | -1 |" in rules_lock
    assert "| Rush or receiving first down | 0.4 |" in rules_lock

    assert LVE_SCORING == {
        "passing_yard": 1.0 / 30.0,
        "passing_td": 3.0,
        "interception": -1.0,
        "rushing_yard": 0.10,
        "rushing_td": 4.0,
        "receiving_yard": 0.10,
        "receiving_td": 4.0,
        "return_yard": 1.0 / 30.0,
        "return_td": 4.0,
        "reception": 0.0,
        "rushing_receiving_first_down": 0.40,
        "fumble_lost": -1.0,
    }


def test_lve_weekly_scoring_uses_lve_rules_not_ppr(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "player_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "team": "SF",
                "targets": "10",
                "receptions": "8",
                "receiving_yards": "100",
                "receiving_tds": "1",
                "receiving_first_downs": "6",
                "fumbles_lost": "1",
            }
        ],
    )

    result = derive_lve_weekly_scoring_rows(source_root)

    assert result.status == "ready"
    row = result.rows[0]
    assert row["receiving_points"] == 14.0
    assert row["first_down_points"] == 2.4
    assert row["turnover_points"] == -1.0
    assert row["lve_points"] == 15.4
    assert row["touches"] == 8.0
    assert row["scoring_effect"] == "derived weekly scoring only; no model mutation"


def test_lve_weekly_scoring_handles_qb_turnovers_and_rushing_first_downs(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "player_id": "p_qb",
                "player_name": "QB One",
                "position": "QB",
                "team": "BAL",
                "passing_yards": "250",
                "passing_tds": "2",
                "interceptions": "1",
                "rushing_attempts": "8",
                "rushing_yards": "50",
                "rushing_tds": "1",
                "rushing_first_downs": "4",
            }
        ],
    )

    row = derive_lve_weekly_scoring_rows(source_root).rows[0]

    assert row["passing_points"] == 14.33
    assert row["rushing_points"] == 9.0
    assert row["first_down_points"] == 1.6
    assert row["turnover_points"] == -1.0
    assert row["lve_points"] == 23.93


def test_lve_weekly_scoring_includes_return_scoring_support(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "player_id": "p_wr",
                "player_name": "Returner One",
                "position": "WR",
                "team": "TEN",
                "kick_return_yards": "60",
                "kick_return_tds": "1",
                "punt_return_yards": "30",
                "punt_return_tds": "0",
            }
        ],
    )

    row = derive_lve_weekly_scoring_rows(source_root).rows[0]

    assert row["return_yards"] == 90.0
    assert row["return_tds"] == 1.0
    assert row["return_points"] == 7.0
    assert row["lve_points"] == 7.0
    assert row["scoring_effect"] == "derived weekly scoring only; no model mutation"


def test_lve_weekly_scoring_blocks_when_raw_contract_invalid(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    (source_root / "nflverse_player_stats_weekly.csv").write_text(
        "bad,header\n",
        encoding="utf-8",
    )

    result = derive_lve_weekly_scoring_rows(source_root)

    assert result.status == "blocked"
    assert result.rows == ()
    assert any("CSV header" in issue for issue in result.issues)


def test_lve_weekly_scoring_summary_and_write(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "player_id": "p_rb",
                "player_name": "Runner One",
                "position": "RB",
                "team": "DET",
                "rushing_yards": "80",
                "rushing_tds": "1",
                "rushing_first_downs": "5",
            }
        ],
    )
    rows = derive_lve_weekly_scoring_rows(source_root).rows
    output_path = tmp_path / "derived" / "lve_player_weekly_scoring.csv"

    write_lve_weekly_scoring_rows(output_path, rows)
    summary = lve_weekly_scoring_summary_rows(rows)

    assert output_path.exists()
    with output_path.open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == LVE_WEEKLY_SCORING_HEADER
    assert summary[0]["position"] == "RB"
    assert summary[0]["total_lve_points"] == 14.0


def _copy_templates(tmp_path: Path) -> Path:
    target = tmp_path / "nflverse_stats_upgrade"
    shutil.copytree(TEMPLATE_ROOT, target)
    return target


def _write_rows(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
