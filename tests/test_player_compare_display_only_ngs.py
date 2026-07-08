from __future__ import annotations

import csv
from pathlib import Path

from src.services.display_only_ngs_context_service import (
    NGS_GATE,
    NOT_APPLICABLE_FOR_POSITION,
    NOT_ENOUGH_INFORMATION,
    REVIEW_ONLY_WARNING,
    UNAVAILABLE_THRESHOLDED,
    player_compare_ngs_rows,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "app" / "pages" / "22_player_compare_v1.py"


def test_player_compare_page_wires_review_only_ngs_context() -> None:
    page = PAGE.read_text(encoding="utf-8")

    assert "Review-only NGS Context" in page
    assert "REVIEW_ONLY_WARNING" in page
    assert "Display-only context" in REVIEW_ONLY_WARNING
    assert "Not used in rankings" in REVIEW_ONLY_WARNING
    assert "Not a model score" in REVIEW_ONLY_WARNING
    assert "NGS public thresholds may exclude low-volume players" in REVIEW_ONLY_WARNING
    assert "player_compare_ngs_rows" in page
    assert "winner, recommendation" in page


def test_player_compare_ngs_rows_show_position_applicable_side_by_side_values(
    tmp_path: Path,
) -> None:
    context_path, feature_path = _write_ngs_test_files(tmp_path)
    rows = player_compare_ngs_rows(
        [
            {"player": "Safe QB", "position": "QB", "player_id": "qb-1"},
            {"player": "Safe Wideout", "position": "WR", "player_id": "wr-1"},
        ],
        player_context_path=context_path,
        feature_panel_path=feature_path,
    )
    by_metric = {row["Metric"]: row for row in rows}

    assert by_metric["CPOE"]["Safe QB"] == "3.2"
    assert by_metric["CPOE"]["Safe Wideout"] == NOT_APPLICABLE_FOR_POSITION
    assert by_metric["Avg separation"]["Safe QB"] == NOT_APPLICABLE_FOR_POSITION
    assert by_metric["Avg separation"]["Safe Wideout"] == "3.4"
    assert by_metric["Avg separation"]["Safe Wideout season"] == "2024"
    assert {row["Gate"] for row in rows} == {NGS_GATE}


def test_player_compare_ngs_missing_and_identity_review_rows_are_not_zero_forced(
    tmp_path: Path,
) -> None:
    context_path, feature_path = _write_ngs_test_files(tmp_path)
    rows = player_compare_ngs_rows(
        [
            {"player": "Review Back", "position": "RB", "player_id": "rb-review"},
            {"player": "Missing Back", "position": "RB", "player_id": "rb-missing"},
        ],
        player_context_path=context_path,
        feature_panel_path=feature_path,
    )
    by_metric = {row["Metric"]: row for row in rows}

    assert by_metric["RYOE per attempt"]["Review Back"] == UNAVAILABLE_THRESHOLDED
    assert by_metric["RYOE per attempt"]["Missing Back"] == UNAVAILABLE_THRESHOLDED
    assert by_metric["RYOE per attempt"]["Review Back season"] == NOT_ENOUGH_INFORMATION
    assert "0" not in {
        by_metric["RYOE per attempt"]["Review Back"],
        by_metric["RYOE per attempt"]["Missing Back"],
    }


def test_player_compare_ngs_rows_do_not_include_blocked_metric_families(tmp_path: Path) -> None:
    context_path, feature_path = _write_ngs_test_files(tmp_path)
    rows = player_compare_ngs_rows(
        [{"player": "Safe Wideout", "position": "WR", "player_id": "wr-1"}],
        player_context_path=context_path,
        feature_panel_path=feature_path,
    )
    text = "\n".join(str(row) for row in rows).lower()

    for blocked in ("pfr", "espn", "ftn", "pff", "ffopportunity", "tprr", "yprr", "rz_att"):
        assert blocked not in text
    assert "pick this player" not in text
    assert "winner:" not in text
    assert "boost:" not in text
    assert "verdict:" not in text


def _write_ngs_test_files(tmp_path: Path) -> tuple[Path, Path]:
    context_path = tmp_path / "player_context.csv"
    feature_path = tmp_path / "feature_panel.csv"
    _write_csv(
        context_path,
        [
            _context_row("qb-1", "Safe QB", "QB", "00-qb", "SAFE_NOW_DISPLAY_ONLY", "false"),
            _context_row("wr-1", "Safe Wideout", "WR", "00-wr", "SAFE_NOW_DISPLAY_ONLY", "false"),
            _context_row(
                "rb-review",
                "Review Back",
                "RB",
                "00-rb-review",
                "NEED_IDENTITY_REVIEW",
                "true",
            ),
            _context_row(
                "rb-missing",
                "Missing Back",
                "RB",
                "00-rb-missing",
                "SAFE_NOW_DISPLAY_ONLY",
                "false",
            ),
        ],
    )
    _write_csv(
        feature_path,
        [
            _feature_row(
                "00-qb",
                "2024",
                "QB",
                {
                    "ngs_passing__completion_percentage_above_expectation": "3.2",
                    "ngs_passing__expected_completion_percentage": "65.1",
                },
            ),
            _feature_row(
                "00-wr",
                "2024",
                "WR",
                {
                    "ngs_receiving__avg_separation": "3.4",
                    "ngs_receiving__avg_cushion": "6.1",
                    "ngs_receiving__avg_expected_yac": "4.5",
                },
            ),
            _feature_row(
                "00-rb-review",
                "2024",
                "RB",
                {"ngs_rushing__rush_yards_over_expected_per_att": "9.9"},
            ),
            _feature_row("00-rb-missing", "2024", "RB", {}),
        ],
    )
    return context_path, feature_path


def _context_row(
    player_id: str,
    player: str,
    position: str,
    gsis_id: str,
    identity_status: str,
    review_required: str,
) -> dict[str, str]:
    return {
        "nwr_player_id": player_id,
        "nwr_player_name": player,
        "nwr_position": position,
        "nflverse_gsis_id": gsis_id,
        "identity_join_status": identity_status,
        "review_required": review_required,
    }


def _feature_row(
    gsis_id: str,
    season: str,
    position: str,
    overrides: dict[str, str],
) -> dict[str, str]:
    row = {
        "player_id_gsis": gsis_id,
        "feature_season": season,
        "position": position,
    }
    row.update(overrides)
    return row


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
