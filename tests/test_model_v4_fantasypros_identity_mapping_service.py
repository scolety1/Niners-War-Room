from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_fantasypros_identity_mapping_service import (
    FANTASYPROS_IDENTITY_MAPPING_HEADER,
    FANTASYPROS_IDENTITY_UNRESOLVED_HEADER,
    build_fantasypros_identity_mapping,
    normalize_player_name,
    write_fantasypros_identity_mapping_outputs,
)


def test_fantasypros_identity_mapping_handles_known_suffix_names(tmp_path: Path) -> None:
    clean_rows = tmp_path / "clean.csv"
    identity_map = tmp_path / "identity.csv"
    active_bridge = tmp_path / "bridge.csv"
    truth_set = tmp_path / "truth.csv"
    _write_clean_rows(
        clean_rows,
        [
            ("Brian Thomas Jr.", "WR", "JAX", "2024"),
            ("Luther Burden III", "WR", "CHI", "2025"),
            ("De'Von Achane", "RB", "MIA", "2024"),
            ("Jaxon Smith-Njigba", "WR", "SEA", "2025"),
            ("Amon-Ra St. Brown", "WR", "DET", "2025"),
            ("Travis Etienne Jr.", "RB", "NO", "2024"),
            ("Patrick Mahomes II", "QB", "KC", "2025"),
        ],
    )
    _write_identity_rows(
        identity_map,
        [
            ("11631", "00-0039893", "Brian Thomas", "WR", "JAX"),
            ("12519", "00-0040735", "Luther Burden", "WR", "CHI"),
            ("9226", "00-0039040", "De'Von Achane", "RB", "MIA"),
            ("9488", "00-0038543", "Jaxon Smith-Njigba", "WR", "SEA"),
            ("7547", "00-0036963", "Amon-Ra St. Brown", "WR", "DET"),
            ("7543", "00-0036973", "Travis Etienne", "RB", "NO"),
            ("4046", "00-0033873", "Patrick Mahomes", "QB", "KC"),
        ],
    )
    _write_bridge_rows(
        active_bridge,
        [
            ("11631", "Brian Thomas", "WR", "Brian Thomas Jr.", "00-0039893"),
            ("12519", "Luther Burden", "WR", "Luther Burden III", "00-0040735"),
        ],
    )
    _write_truth_rows(truth_set, [])

    result = build_fantasypros_identity_mapping(
        clean_rows_path=clean_rows,
        identity_map_path=identity_map,
        active_bridge_path=active_bridge,
        truth_set_path=truth_set,
    )

    by_name = {row["fantasypros_player_name"]: row for row in result.mapping_rows}
    assert by_name["Brian Thomas Jr."]["matched_model_player"] == "Brian Thomas Jr."
    assert by_name["Luther Burden III"]["matched_model_player"] == "Luther Burden III"
    assert by_name["De'Von Achane"]["sleeper_id"] == "9226"
    assert by_name["Jaxon Smith-Njigba"]["gsis_id"] == "00-0038543"
    assert by_name["Amon-Ra St. Brown"]["match_method"] == "name_team_position"
    assert by_name["Travis Etienne Jr."]["sleeper_id"] == "7543"
    assert by_name["Patrick Mahomes II"]["matched_model_player"] == "Patrick Mahomes"
    assert result.unresolved_rows == ()


def test_fantasypros_identity_mapping_does_not_merge_ambiguous_players(
    tmp_path: Path,
) -> None:
    clean_rows = tmp_path / "clean.csv"
    identity_map = tmp_path / "identity.csv"
    active_bridge = tmp_path / "bridge.csv"
    truth_set = tmp_path / "truth.csv"
    _write_clean_rows(clean_rows, [("Duplicate Name", "WR", "", "2025")])
    _write_identity_rows(
        identity_map,
        [
            ("1", "gsis-1", "Duplicate Name", "WR", "SF"),
            ("2", "gsis-2", "Duplicate Name", "WR", "NYG"),
        ],
    )
    _write_bridge_rows(active_bridge, [])
    _write_truth_rows(truth_set, [])

    result = build_fantasypros_identity_mapping(
        clean_rows_path=clean_rows,
        identity_map_path=identity_map,
        active_bridge_path=active_bridge,
        truth_set_path=truth_set,
    )

    row = result.mapping_rows[0]
    assert row["matched_model_player"] == ""
    assert row["match_method"] == "ambiguous_name_position"
    assert row["warning"] == "ambiguous_name_position"
    assert result.summary["ambiguous_rows_silently_merged"] is False
    assert len(result.unresolved_rows) == 1


def test_fantasypros_identity_mapping_writes_stable_reports(tmp_path: Path) -> None:
    clean_rows = tmp_path / "clean.csv"
    identity_map = tmp_path / "identity.csv"
    active_bridge = tmp_path / "bridge.csv"
    truth_set = tmp_path / "truth.csv"
    _write_clean_rows(clean_rows, [("Patrick Mahomes II", "QB", "KC", "2025")])
    _write_identity_rows(
        identity_map,
        [("4046", "00-0033873", "Patrick Mahomes", "QB", "KC")],
    )
    _write_bridge_rows(active_bridge, [])
    _write_truth_rows(truth_set, [])
    result = build_fantasypros_identity_mapping(
        clean_rows_path=clean_rows,
        identity_map_path=identity_map,
        active_bridge_path=active_bridge,
        truth_set_path=truth_set,
    )

    paths = write_fantasypros_identity_mapping_outputs(tmp_path / "out", result)

    assert _header(paths["mapping"]) == FANTASYPROS_IDENTITY_MAPPING_HEADER
    assert _header(paths["unresolved"]) == FANTASYPROS_IDENTITY_UNRESOLVED_HEADER
    assert result.summary["model_scores_changed"] is False


def test_normalized_name_removes_suffixes_and_punctuation() -> None:
    assert normalize_player_name("Brian Thomas Jr.") == "brianthomas"
    assert normalize_player_name("Luther Burden III") == "lutherburden"
    assert normalize_player_name("De'Von Achane") == "devonachane"
    assert normalize_player_name("Amon-Ra St. Brown") == "amonrastbrown"


def _write_clean_rows(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    _write_csv(
        path,
        (
            "player_name",
            "position",
            "nfl_team",
            "season",
            "source_file",
            "source_hash",
        ),
        [
            [name, position, team, season, "source.csv", "hash"]
            for name, position, team, season in rows
        ],
    )


def _write_identity_rows(
    path: Path,
    rows: list[tuple[str, str, str, str, str]],
) -> None:
    _write_csv(
        path,
        (
            "sleeper_id",
            "gsis_id",
            "nfl_id",
            "espn_id",
            "fantasy_data_id",
            "pfr_id",
            "player_id",
            "player_name",
            "normalized_name",
            "position",
            "team",
            "match_method",
            "match_confidence",
            "review_status",
            "notes",
        ),
        [
            [
                sleeper_id,
                gsis_id,
                "",
                "",
                "",
                "",
                sleeper_id,
                player_name,
                normalize_player_name(player_name),
                position,
                team,
                "sleeper_id",
                "98",
                "ready",
                "",
            ]
            for sleeper_id, gsis_id, player_name, position, team in rows
        ],
    )


def _write_bridge_rows(
    path: Path,
    rows: list[tuple[str, str, str, str, str]],
) -> None:
    _write_csv(
        path,
        (
            "sleeper_id",
            "player_name",
            "position",
            "sleeper_gsis_id",
            "bridge_gsis_id",
            "bridge_pfr_id",
            "bridge_name",
            "matched_gsis_id",
            "stat_player_name",
            "match_method",
            "match_status",
            "manual_review_required",
        ),
        [
            [
                sleeper_id,
                player_name,
                position,
                "",
                gsis_id,
                "",
                stat_player_name,
                gsis_id,
                stat_player_name,
                "test",
                "matched",
                "false",
            ]
            for sleeper_id, player_name, position, stat_player_name, gsis_id in rows
        ],
    )


def _write_truth_rows(path: Path, rows: list[tuple[str, str, str]]) -> None:
    _write_csv(
        path,
        ("player_name", "position", "nfl_team"),
        [[name, position, team] for name, position, team in rows],
    )


def _write_csv(path: Path, header: tuple[str, ...], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
