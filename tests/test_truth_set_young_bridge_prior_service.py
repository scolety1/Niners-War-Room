from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_young_bridge_prior_service import (
    TRUTH_SET_YOUNG_BRIDGE_PREVIEW_HEADER,
    build_truth_set_young_bridge_prior,
    write_truth_set_young_bridge_prior,
)


def _write_source(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "player_name",
        "position",
        "nfl_team",
        "draft_year",
        "nfl_draft_round",
        "nfl_draft_pick",
        "college_dominator_or_share_if_available",
        "college_yards",
        "college_tds",
        "college_receptions_or_carries",
        "athletic_testing_if_available",
        "rookie_year_nfl_production_summary",
        "source_name",
        "source_url",
        "source_date",
        "confidence_0_100",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_young_bridge_preview_scores_only_active_bridge_lifecycles(tmp_path: Path) -> None:
    source = tmp_path / "young.csv"
    _write_source(
        source,
        [
            {
                "player_name": "Luther Burden III",
                "position": "WR",
                "nfl_team": "CHI",
                "draft_year": "2025",
                "nfl_draft_round": "2",
                "nfl_draft_pick": "39",
                "college_dominator_or_share_if_available": "high target share",
                "college_yards": "1212",
                "college_tds": "9",
                "college_receptions_or_carries": "86 receptions",
                "source_name": "test",
                "source_url": "https://example.test",
                "source_date": "2026-05-14",
                "confidence_0_100": "85",
                "notes": "Physical receiver note.",
            },
            {
                "player_name": "Wan'Dale Robinson",
                "position": "WR",
                "nfl_team": "TEN",
                "draft_year": "2022",
                "nfl_draft_round": "2",
                "nfl_draft_pick": "43",
                "college_dominator_or_share_if_available": "context",
                "source_name": "test",
                "source_url": "https://example.test",
                "source_date": "2026-05-14",
                "confidence_0_100": "80",
                "notes": "",
            },
        ],
    )

    result = build_truth_set_young_bridge_prior(source)
    by_player = {str(row["player_name"]): row for row in result.rows}

    assert by_player["Luther Burden"]["asset_lifecycle"] == "year_one_nfl_bridge"
    assert by_player["Luther Burden"]["draft_capital_prior_score"] == 82.0
    assert by_player["Wan'Dale Robinson"]["asset_lifecycle"] == "not_applicable_established_veteran"
    assert by_player["Wan'Dale Robinson"]["draft_capital_prior_score"] == ""
    assert "established_veteran_draft_capital_not_scored" in str(
        by_player["Wan'Dale Robinson"]["warning_flags"]
    )


def test_udfa_gets_known_zero_prior_and_missing_pick_flag(tmp_path: Path) -> None:
    source = tmp_path / "young.csv"
    _write_source(
        source,
        [
            {
                "player_name": "Jalen Coker",
                "position": "WR",
                "nfl_team": "CAR",
                "draft_year": "2024",
                "nfl_draft_round": "UDFA",
                "nfl_draft_pick": "-",
                "college_yards": "2684 career",
                "college_tds": "31",
                "college_receptions_or_carries": "163 receptions",
                "source_name": "test",
                "source_url": "https://example.test",
                "source_date": "2026-05-14",
                "confidence_0_100": "80",
                "notes": "",
            }
        ],
    )

    row = build_truth_set_young_bridge_prior(source).rows[0]

    assert row["asset_lifecycle"] == "year_two_nfl_bridge"
    assert row["draft_capital_source_status"] == "udfa_known"
    assert row["draft_capital_prior_score"] == 0.0
    assert "missing_draft_pick" not in str(row["warning_flags"])


def test_missing_expected_young_players_are_flagged_without_invented_scores(tmp_path: Path) -> None:
    source = tmp_path / "young.csv"
    _write_source(source, [])

    result = build_truth_set_young_bridge_prior(source)
    by_player = {str(row["player_name"]): row for row in result.rows}

    assert by_player["Jahmyr Gibbs"]["asset_lifecycle"] == "year_three_nfl_bridge"
    assert by_player["Jahmyr Gibbs"]["draft_capital_prior_score"] == ""
    assert by_player["Jahmyr Gibbs"]["draft_capital_source_status"] == "missing_source_row"
    assert any(flag["flag"] == "missing_young_bridge_source_row" for flag in result.flags)


def test_gap_fill_controls_validate_draft_capital_without_college_context(
    tmp_path: Path,
) -> None:
    source = tmp_path / "young.csv"
    _write_source(
        source,
        [
            {
                "player_name": "Jahmyr Gibbs",
                "position": "RB",
                "nfl_team": "Detroit Lions",
                "draft_year": "2023",
                "nfl_draft_round": "1",
                "nfl_draft_pick": "12",
                "college_yards": "",
                "source_name": "NFL.com",
                "source_url": "https://www.nfl.com/news/lions-select-alabama-rb-jahmyr-gibbs-with-no-12-overall-pick-in-2023-nfl-draft",
                "source_date": "2023-04",
                "confidence_0_100": "95",
                "notes": "Factual draft-capital gap-fill only.",
            },
            {
                "player_name": "Ashton Jeanty",
                "position": "RB",
                "nfl_team": "Las Vegas Raiders",
                "draft_year": "2025",
                "nfl_draft_round": "1",
                "nfl_draft_pick": "6",
                "source_name": "NFL.com",
                "source_url": "https://www.nfl.com/_amp/2025-nfl-draft-raiders-select-boise-state-rb-ashton-jeanty-with-no-6-overall-pick",
                "source_date": "2025-04",
                "confidence_0_100": "95",
                "notes": "Factual draft-capital gap-fill only.",
            },
            {
                "player_name": "Brock Bowers",
                "position": "TE",
                "nfl_team": "Las Vegas Raiders",
                "draft_year": "2024",
                "nfl_draft_round": "1",
                "nfl_draft_pick": "13",
                "source_name": "NFL.com",
                "source_url": "https://www.nfl.com/news/raiders-select-georgia-te-brock-bowers-with-no-13-pick-in-2024-nfl-draft",
                "source_date": "2024-04",
                "confidence_0_100": "95",
                "notes": "Factual draft-capital gap-fill only.",
            },
        ],
    )

    result = build_truth_set_young_bridge_prior(source)
    by_player = {str(row["player_name"]): row for row in result.rows}

    assert by_player["Jahmyr Gibbs"]["asset_lifecycle"] == "year_three_nfl_bridge"
    assert by_player["Ashton Jeanty"]["asset_lifecycle"] == "year_one_nfl_bridge"
    assert by_player["Brock Bowers"]["asset_lifecycle"] == "year_two_nfl_bridge"
    assert by_player["Jahmyr Gibbs"]["draft_capital_source_status"] == "derived_from_round_pick"
    assert by_player["Ashton Jeanty"]["source_url"]
    assert by_player["Brock Bowers"]["draft_capital_prior_score"] != ""
    assert not any(
        flag["player_name"] in {"Jahmyr Gibbs", "Ashton Jeanty", "Brock Bowers"}
        and flag["flag"] == "missing_young_bridge_source_row"
        for flag in result.flags
    )
    assert any(flag["flag"] == "missing_college_production" for flag in result.flags)


def test_receipts_include_context_sections_and_subjective_note_flag(tmp_path: Path) -> None:
    source = tmp_path / "young.csv"
    _write_source(
        source,
        [
            {
                "player_name": "Brian Thomas Jr.",
                "position": "WR",
                "nfl_team": "JAX",
                "draft_year": "2024",
                "nfl_draft_round": "1",
                "nfl_draft_pick": "23",
                "college_yards": "1177",
                "college_tds": "17",
                "college_receptions_or_carries": "68 receptions",
                "athletic_testing_if_available": "4.33 40",
                "rookie_year_nfl_production_summary": "87 rec, 1282 yds, 10 TD",
                "source_name": "test",
                "source_url": "https://example.test",
                "source_date": "2026-05-14",
                "confidence_0_100": "90",
                "notes": "Explosive Pro Bowl rookie.",
            }
        ],
    )

    result = build_truth_set_young_bridge_prior(source)
    sections = {row["receipt_section"] for row in result.receipt_rows}

    assert "draft_capital_prior" in sections
    assert "college_production_context" in sections
    assert "athletic_testing_context" in sections
    assert "rookie_year_context" in sections
    assert any(flag["flag"] == "subjective_note_language" for flag in result.flags)


def test_writer_uses_stable_preview_header(tmp_path: Path) -> None:
    output = tmp_path / "preview.csv"
    write_truth_set_young_bridge_prior(
        output,
        tuple({field: "" for field in TRUTH_SET_YOUNG_BRIDGE_PREVIEW_HEADER} for _ in range(1)),
    )

    header = output.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert tuple(header) == TRUTH_SET_YOUNG_BRIDGE_PREVIEW_HEADER
