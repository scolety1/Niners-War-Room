from __future__ import annotations

import csv
from pathlib import Path

from src.services.nflverse_identity_service import (
    build_nflverse_identity_review_rows,
    identity_map_ready_player_ids,
    nflverse_identity_review_summary_rows,
    validate_nflverse_identity_map,
)
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

SAMPLE_PACK = Path("sample_data/2026_pre_declaration")
IDENTITY_HEADER = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_identity_map.csv"]


def test_empty_identity_template_validates_ready() -> None:
    report = validate_nflverse_identity_map(
        "templates/real_data_inputs/nflverse_stats_upgrade/nflverse_identity_map.csv"
    )

    assert report.status == "ready"
    assert report.row_count == 0
    assert report.issues == ()


def test_identity_map_validation_blocks_duplicate_external_ids(
    tmp_path: Path,
) -> None:
    identity_path = tmp_path / "nflverse_identity_map.csv"
    _write_rows(
        identity_path,
        [
            _identity_row("p_achane", "De'Von Achane", "RB", sleeper_id="123"),
            _identity_row("p_lamar", "Lamar Jackson", "QB", sleeper_id="123"),
        ],
    )

    report = validate_nflverse_identity_map(identity_path)

    assert report.status == "blocked"
    assert "Duplicate sleeper_id in identity map." in {
        issue.issue for issue in report.issues
    }


def test_identity_map_validation_warns_when_external_id_missing(
    tmp_path: Path,
) -> None:
    identity_path = tmp_path / "nflverse_identity_map.csv"
    _write_rows(
        identity_path,
        [
            _identity_row("p_luther_burden", "Luther Burden", "WR"),
        ],
    )

    report = validate_nflverse_identity_map(identity_path)

    assert report.status == "review"
    assert "Identity row has no external ID." in {
        issue.issue for issue in report.issues
    }


def test_identity_review_classifies_ready_review_blocked_and_unmatched(
    tmp_path: Path,
) -> None:
    identity_path = tmp_path / "nflverse_identity_map.csv"
    _write_rows(
        identity_path,
        [
            _identity_row(
                "p_achane",
                "De'Von Achane",
                "RB",
                sleeper_id="9221",
                gsis_id="00-0039567",
                review_status="ready",
                match_confidence="100",
            ),
            _identity_row(
                "p_lamar",
                "Lamar Jackson",
                "QB",
                pfr_id="jackla00",
                review_status="review",
                match_confidence="80",
            ),
            _identity_row(
                "p_chase_brown",
                "Chase Brown",
                "RB",
                pfr_id="browch05",
                review_status="blocked",
                match_confidence="40",
            ),
        ],
    )

    rows = build_nflverse_identity_review_rows(SAMPLE_PACK, identity_path)
    by_player = {row["player_id"]: row for row in rows}

    assert by_player["p_achane"]["match_status"] == "matched"
    assert by_player["p_achane"]["match_method"] == "player_id"
    assert by_player["p_lamar"]["match_status"] == "review"
    assert by_player["p_chase_brown"]["match_status"] == "blocked"
    assert by_player["p_luther_burden"]["match_status"] == "unmatched"

    summary = {
        row["match_status"]: row
        for row in nflverse_identity_review_summary_rows(rows)
    }
    assert summary["matched"]["rows"] == 1
    assert summary["review"]["rows"] == 1
    assert summary["blocked"]["blocking"] is True
    assert summary["unmatched"]["blocking"] is True


def test_ready_player_ids_only_returns_confirmed_matches(tmp_path: Path) -> None:
    identity_path = tmp_path / "nflverse_identity_map.csv"
    _write_rows(
        identity_path,
        [
            _identity_row(
                "p_achane",
                "De'Von Achane",
                "RB",
                sleeper_id="9221",
                review_status="ready",
            ),
            _identity_row(
                "p_lamar",
                "Lamar Jackson",
                "QB",
                pfr_id="jackla00",
                review_status="review",
            ),
        ],
    )

    assert identity_map_ready_player_ids(SAMPLE_PACK, identity_path) == {"p_achane"}


def _identity_row(
    player_id: str,
    player_name: str,
    position: str,
    *,
    sleeper_id: str = "",
    gsis_id: str = "",
    pfr_id: str = "",
    review_status: str = "ready",
    match_confidence: str = "90",
) -> dict[str, str]:
    return {
        "sleeper_id": sleeper_id,
        "gsis_id": gsis_id,
        "nfl_id": "",
        "espn_id": "",
        "fantasy_data_id": "",
        "pfr_id": pfr_id,
        "player_id": player_id,
        "player_name": player_name,
        "normalized_name": "".join(
            character.lower() for character in player_name if character.isalnum()
        ),
        "position": position,
        "team": "",
        "match_method": "manual",
        "match_confidence": match_confidence,
        "review_status": review_status,
        "notes": "test row",
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=IDENTITY_HEADER)
        writer.writeheader()
        writer.writerows(rows)
