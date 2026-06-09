from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_fantasypros_advanced_intake_service import (
    FANTASYPROS_ADVANCED_CLEAN_HEADER,
    FANTASYPROS_ADVANCED_VALIDATION_HEADER,
    build_fantasypros_advanced_intake,
    normalize_numeric,
    parse_player_team,
    write_fantasypros_advanced_intake_outputs,
)


def test_fantasypros_intake_reads_only_canonical_files(tmp_path: Path) -> None:
    source = tmp_path / "canonical_wr.csv"
    extra = tmp_path / "extra_wr.csv"
    _write_csv(
        source,
        RECEIVING_HEADER,
        [
            [
                "1",
                "Jaxon Smith-Njigba   SEA",
                "17",
                "119",
                "1,793",
                "15.1",
                "1,265",
                "10.6",
                "1,831",
                "15.4",
                "528",
                "4.4",
                "174",
                "1.5",
                "3",
                "163",
                "35.8%",
                "126",
                "5",
                "17",
                "76",
                "27",
                "12",
                "8",
                "4",
                "63",
            ],
        ],
    )
    _write_csv(extra, RECEIVING_HEADER, [["1", "Should Not Read   SEA", *[""] * 24]])
    index = tmp_path / "index.csv"
    _write_index(index, source, season=2025, position="WR")

    result = build_fantasypros_advanced_intake(index)

    assert len(result.clean_rows) == 1
    row = result.clean_rows[0]
    assert row["player_name"] == "Jaxon Smith-Njigba"
    assert row["nfl_team"] == "SEA"
    assert row["receiving_yards"] == 1793
    assert row["team_target_share_pct"] == 35.8
    assert row["source_status"] == "imported_real_data"
    assert row["source_file"] == str(source)


def test_player_team_parser_preserves_suffixes() -> None:
    assert parse_player_team("Patrick Mahomes II   KC") == ("Patrick Mahomes II", "KC", "")
    assert parse_player_team("Kyle Pitts Sr.   ATL") == ("Kyle Pitts Sr.", "ATL", "")
    assert parse_player_team("Player Without Team")[2] == "team_suffix_missing"


def test_numeric_normalizer_handles_commas_percentages_blanks_and_negatives() -> None:
    assert normalize_numeric("1,585") == (1585, "")
    assert normalize_numeric("28.6%") == (28.6, "")
    assert normalize_numeric("") == ("", "")
    assert normalize_numeric("-54") == (-54, "")
    assert normalize_numeric("maybe")[1] == "non_numeric_value"


def test_rb_duplicate_yacon_is_disambiguated_with_second_field_context_only(
    tmp_path: Path,
) -> None:
    source = tmp_path / "canonical_rb.csv"
    _write_csv(
        source,
        RB_HEADER,
        [
            [
                "1",
                "Bijan Robinson   ATL",
                "17",
                "287",
                "1,478",
                "5.1",
                "812",
                "2.8",
                "666",
                "2.3",
                "22",
                "26",
                "-64",
                "93",
                "36",
                "8",
                "4",
                "2",
                "2",
                "93",
                "79",
                "103",
                "12",
                "209",
            ],
        ],
    )
    index = tmp_path / "index.csv"
    _write_index(
        index,
        source,
        season=2025,
        position="RB",
        duplicate_headers="YACON",
        validation_status="needs_header_disambiguation",
    )

    result = build_fantasypros_advanced_intake(index)

    row = result.clean_rows[0]
    assert row["rushing_yards_after_contact"] == 666
    assert row["receiving_yards_after_contact_or_yac_context"] == 209
    assert row["validation_status"] == "cleaned_with_header_disambiguation"
    assert "context-only" in str(result.summary["rb_duplicate_yacon_policy"])


def test_fantasypros_intake_write_outputs_uses_stable_headers(tmp_path: Path) -> None:
    source = tmp_path / "canonical_qb.csv"
    _write_csv(
        source,
        QB_HEADER,
        [["1", "Lamar Jackson   BAL", "17", *["1"] * 21]],
    )
    index = tmp_path / "index.csv"
    _write_index(index, source, season=2019, position="QB")
    result = build_fantasypros_advanced_intake(index)

    paths = write_fantasypros_advanced_intake_outputs(tmp_path / "out", result)

    assert _header(paths["clean"]) == FANTASYPROS_ADVANCED_CLEAN_HEADER
    assert _header(paths["validation"]) == FANTASYPROS_ADVANCED_VALIDATION_HEADER
    assert result.summary["model_scores_changed"] is False


QB_HEADER = (
    "RK",
    "Player",
    "G",
    "COMP",
    "ATT",
    "PCT",
    "YDS",
    "Y/A",
    "AIR",
    "AIR/A",
    "10+ YDS",
    "20+ YDS",
    "30+ YDS",
    "40+ YDS",
    "50+ YDS",
    "PKT TIME",
    "SACK",
    "KNCK",
    "HRRY",
    "BLITZ",
    "POOR",
    "DROP",
    "RZ ATT",
    "RTG",
)

RB_HEADER = (
    "RK",
    "Player",
    "G",
    "ATT",
    "YDS",
    "Y/ATT",
    "YBCON",
    "YBCON/ATT",
    "YACON",
    "YACON/ATT",
    "BRKTKL",
    "TK LOSS",
    "TK LOSS YDS",
    "LNG TD",
    "10+ YDS",
    "20+ YDS",
    "30+ YDS",
    "40+ YDS",
    "50+ YDS",
    "LNG",
    "REC",
    "TGT",
    "RZ TGT",
    "YACON",
)

RECEIVING_HEADER = (
    "RK",
    "Player",
    "G",
    "REC",
    "YDS",
    "Y/R",
    "YBC",
    "YBC/R",
    "AIR",
    "AIR/R",
    "YAC",
    "YAC/R",
    "YACON",
    "YACON/R",
    "BRKTKL",
    "TGT",
    "% TM",
    "CATCHABLE",
    "DROP",
    "RZ TGT",
    "10+ YDS",
    "20+ YDS",
    "30+ YDS",
    "40+ YDS",
    "50+ YDS",
    "LNG",
)


def _write_index(
    path: Path,
    source: Path,
    *,
    season: int,
    position: str,
    duplicate_headers: str = "",
    validation_status: str = "structurally_clean",
) -> None:
    header_by_position = {
        "QB": QB_HEADER,
        "RB": RB_HEADER,
        "WR": RECEIVING_HEADER,
        "TE": RECEIVING_HEADER,
    }
    _write_csv(
        path,
        (
            "season",
            "position",
            "canonical_file",
            "sha256",
            "row_count",
            "column_count",
            "duplicate_headers",
            "validation_status",
            "first_player",
            "model_intake_role",
        ),
        [
            [
                str(season),
                position,
                str(source),
                _sha256(source),
                "1",
                str(len(header_by_position[position])),
                duplicate_headers,
                validation_status,
                "Example",
                "stats_first_evidence",
            ]
        ],
    )


def _write_csv(path: Path, header: tuple[str, ...], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest().upper()
