from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_stats_first_expected_value_service import (
    COMPONENT_EVIDENCE_HEADER,
    EXPECTED_VALUE_HEADER,
    build_stats_first_expected_value_layer,
    write_stats_first_expected_value_outputs,
)


def test_stats_first_expected_value_ignores_projection_context(
    tmp_path: Path,
) -> None:
    clean_rows = tmp_path / "clean.csv"
    mapping_rows = tmp_path / "mapping.csv"
    projection_rows = tmp_path / "projections.csv"
    _write_clean_rows(
        clean_rows,
        [
            _clean_wr("Player One", "2025", receiving_yards="1200", targets="150"),
            _clean_wr("Player Two", "2025", receiving_yards="800", targets="95"),
        ],
    )
    _write_mapping_rows(
        mapping_rows,
        [
            _mapping("Player One", "2025", "WR", "SEA", sleeper_id="1", gsis_id="gsis-1"),
            _mapping("Player Two", "2025", "WR", "SEA", sleeper_id="2", gsis_id="gsis-2"),
        ],
    )
    _write_csv(
        projection_rows,
        ("player_name", "projected_lve_points_if_calculable"),
        [["Player Two", "999999"]],
    )

    without_projection = build_stats_first_expected_value_layer(
        clean_rows_path=clean_rows,
        identity_mapping_path=mapping_rows,
        production_season_path=tmp_path / "missing_production.csv",
        usage_season_path=tmp_path / "missing_usage.csv",
    )
    with_projection = build_stats_first_expected_value_layer(
        clean_rows_path=clean_rows,
        identity_mapping_path=mapping_rows,
        production_season_path=tmp_path / "missing_production.csv",
        usage_season_path=tmp_path / "missing_usage.csv",
        projection_context_path=projection_rows,
    )

    assert with_projection.expected_value_rows == without_projection.expected_value_rows
    assert with_projection.summary["projection_context_rows_used_for_core_value"] == 0
    assert with_projection.summary["projection_context_explicitly_ignored"] is True
    assert with_projection.summary["market_value_used"] is False
    assert with_projection.summary["league_rank_used"] is False


def test_stats_first_expected_value_records_season_weights_and_route_unavailable(
    tmp_path: Path,
) -> None:
    clean_rows = tmp_path / "clean.csv"
    mapping_rows = tmp_path / "mapping.csv"
    _write_clean_rows(
        clean_rows,
        [
            _clean_wr("Jaxon Smith-Njigba", "2025", receiving_yards="1793", targets="163"),
            _clean_wr("Jaxon Smith-Njigba", "2024", receiving_yards="1130", targets="137"),
        ],
    )
    _write_mapping_rows(
        mapping_rows,
        [
            _mapping("Jaxon Smith-Njigba", "2025", "WR", "SEA"),
            _mapping("Jaxon Smith-Njigba", "2024", "WR", "SEA"),
        ],
    )

    result = build_stats_first_expected_value_layer(
        clean_rows_path=clean_rows,
        identity_mapping_path=mapping_rows,
        production_season_path=tmp_path / "missing_production.csv",
        usage_season_path=tmp_path / "missing_usage.csv",
    )

    row = result.expected_value_rows[0]
    assert "2025:1.0" in str(row["weighted_seasons"])
    assert "2024:0.65" in str(row["weighted_seasons"])
    assert any(
        unavailable["component_or_section"] == "route_metrics"
        and unavailable["reason"]
        == "licensed_route_metrics_not_available;not_used_in_stats_first_value"
        for unavailable in result.unavailable_rows
    )


def test_stats_first_expected_value_buckets_2022_and_older_as_deep_history(
    tmp_path: Path,
) -> None:
    clean_rows = tmp_path / "clean.csv"
    mapping_rows = tmp_path / "mapping.csv"
    _write_clean_rows(
        clean_rows,
        [
            _clean_wr("Old Player", "2022", receiving_yards="1400", targets="160"),
            _clean_wr("Old Player", "2021", receiving_yards="1300", targets="150"),
        ],
    )
    _write_mapping_rows(
        mapping_rows,
        [
            _mapping("Old Player", "2022", "WR", "SEA"),
            _mapping("Old Player", "2021", "WR", "SEA"),
        ],
    )

    result = build_stats_first_expected_value_layer(
        clean_rows_path=clean_rows,
        identity_mapping_path=mapping_rows,
        production_season_path=tmp_path / "missing_production.csv",
        usage_season_path=tmp_path / "missing_usage.csv",
    )

    row = result.expected_value_rows[0]
    assert row["weighted_seasons"] == "deep_history_through_2022:0.12(2021-2022)"
    assert "2021:0.12|2022:0.12" not in str(row["weighted_seasons"])


def test_stats_first_expected_value_prefers_nflverse_production_when_available(
    tmp_path: Path,
) -> None:
    clean_rows = tmp_path / "clean.csv"
    mapping_rows = tmp_path / "mapping.csv"
    production_rows = tmp_path / "production.csv"
    _write_clean_rows(
        clean_rows,
        [
            _clean_wr(
                "Brian Thomas Jr.",
                "2025",
                team="JAX",
                receiving_yards="100",
                targets="10",
            )
        ],
    )
    _write_mapping_rows(
        mapping_rows,
        [_mapping("Brian Thomas Jr.", "2025", "WR", "JAX", sleeper_id="11631")],
    )
    _write_csv(
        production_rows,
        (
            "truth_set_player_name",
            "season",
            "passing_yards",
            "passing_tds",
            "interceptions",
            "rushing_yards",
            "rushing_tds",
            "receiving_yards",
            "receiving_tds",
            "rushing_first_downs",
            "receiving_first_downs",
            "fumbles_lost",
        ),
        [
            [
                "Brian Thomas Jr.",
                "2025",
                "0",
                "0",
                "0",
                "0",
                "0",
                "1300",
                "8",
                "0",
                "65",
                "0",
            ]
        ],
    )

    result = build_stats_first_expected_value_layer(
        clean_rows_path=clean_rows,
        identity_mapping_path=mapping_rows,
        production_season_path=production_rows,
        usage_season_path=tmp_path / "missing_usage.csv",
    )

    production_component = next(
        row
        for row in result.component_evidence_rows
        if row["component"] == "production_trend"
    )
    assert production_component["source_name"] == "nflverse_player_stats"
    assert "nflverse_receiving_yards" in str(production_component["source_fields"])
    assert float(production_component["raw_value"]) > 100


def test_stats_first_expected_value_joins_canonical_team_aliases(tmp_path: Path) -> None:
    clean_rows = tmp_path / "clean.csv"
    mapping_rows = tmp_path / "mapping.csv"
    _write_clean_rows(
        clean_rows,
        [_clean_wr("Brian Thomas Jr.", "2025", team="JAC")],
    )
    _write_mapping_rows(
        mapping_rows,
        [_mapping("Brian Thomas Jr.", "2025", "WR", "JAX", sleeper_id="11631")],
    )

    result = build_stats_first_expected_value_layer(
        clean_rows_path=clean_rows,
        identity_mapping_path=mapping_rows,
        production_season_path=tmp_path / "missing_production.csv",
        usage_season_path=tmp_path / "missing_usage.csv",
    )

    assert result.expected_value_rows[0]["matched_model_player"] == "Brian Thomas Jr."


def test_stats_first_expected_value_writes_stable_outputs(tmp_path: Path) -> None:
    clean_rows = tmp_path / "clean.csv"
    mapping_rows = tmp_path / "mapping.csv"
    _write_clean_rows(clean_rows, [_clean_wr("Player One", "2025")])
    _write_mapping_rows(mapping_rows, [_mapping("Player One", "2025", "WR", "SEA")])
    result = build_stats_first_expected_value_layer(
        clean_rows_path=clean_rows,
        identity_mapping_path=mapping_rows,
        production_season_path=tmp_path / "missing_production.csv",
        usage_season_path=tmp_path / "missing_usage.csv",
    )

    paths = write_stats_first_expected_value_outputs(tmp_path / "out", result)

    assert _header(paths["expected"]) == EXPECTED_VALUE_HEADER
    assert _header(paths["components"]) == COMPONENT_EVIDENCE_HEADER


def _clean_wr(
    player: str,
    season: str,
    *,
    team: str = "SEA",
    receiving_yards: str = "1000",
    targets: str = "120",
) -> list[str]:
    return [
        player,
        "WR",
        team,
        season,
        targets,
        receiving_yards,
        "25.0",
        "1200",
        "500",
        "100",
        "5",
        "90",
        "4",
        "15",
        "60",
        "20",
        "8",
        "4",
        "2",
        "source.csv",
        "hash",
    ]


def _mapping(
    player: str,
    season: str,
    position: str,
    team: str,
    *,
    sleeper_id: str = "1",
    gsis_id: str = "gsis",
) -> list[str]:
    return [
        player,
        player.lower().replace(" ", ""),
        season,
        position,
        team,
        player,
        sleeper_id,
        gsis_id,
        "name_team_position",
        "98",
        "",
        "1",
        player,
        "source.csv",
        "hash",
    ]


def _write_clean_rows(path: Path, rows: list[list[str]]) -> None:
    _write_csv(
        path,
        (
            "player_name",
            "position",
            "nfl_team",
            "season",
            "targets",
            "receiving_yards",
            "team_target_share_pct",
            "receiving_air_yards",
            "receiving_yards_after_catch",
            "receiving_yards_after_contact",
            "broken_tackles",
            "catchable_targets",
            "drops",
            "red_zone_targets",
            "receiving_10_plus",
            "receiving_20_plus",
            "receiving_30_plus",
            "receiving_40_plus",
            "receiving_50_plus",
            "source_file",
            "source_hash",
        ),
        rows,
    )


def _write_mapping_rows(path: Path, rows: list[list[str]]) -> None:
    _write_csv(
        path,
        (
            "fantasypros_player_name",
            "normalized_player_name",
            "season",
            "position",
            "fantasypros_team",
            "matched_model_player",
            "sleeper_id",
            "gsis_id",
            "match_method",
            "match_confidence",
            "warning",
            "candidate_count",
            "candidate_players",
            "source_file",
            "source_hash",
        ),
        rows,
    )


def _write_csv(path: Path, header: tuple[str, ...], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
