from __future__ import annotations

import csv
from pathlib import Path

from src.services.forced_release_strategy_service import team_release_pressure_profile
from src.services.model_v4_roster_rank_contract_service import (
    EXPECTED_NINERS_TOP_FIVE,
    OFFICIAL_NINERS_ROSTER_RANK_PATH,
    validate_official_roster_rank_contract,
)


def test_official_niners_roster_rank_contract_is_ready() -> None:
    report = validate_official_roster_rank_contract()

    assert report.status == "ready"
    assert report.row_count == 24
    assert report.top_five_names == EXPECTED_NINERS_TOP_FIVE
    assert {row.roster_rank for row in report.rows} == set(range(1, 25))
    assert all(isinstance(row.league_rank, int) for row in report.rows)
    assert report.league_rank_usage_policy == "rule_context_only"
    assert report.league_rank_allowed_in_dynasty_asset_value is False


def test_roster_rank_contract_blocks_incomplete_niners_roster(tmp_path: Path) -> None:
    path = _mutated_contract_csv(
        tmp_path,
        lambda rows: [row for row in rows if row["player_name"] != "Devin Singletary"],
    )

    report = validate_official_roster_rank_contract(path)

    assert report.status == "blocked"
    assert any("expected 24" in issue.issue for issue in report.issues)


def test_roster_rank_contract_blocks_non_numeric_league_rank(tmp_path: Path) -> None:
    def mutate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        for row in rows:
            if row["player_name"] == "De'Von Achane":
                row["league_rank"] = "ten"
        return rows

    report = validate_official_roster_rank_contract(_mutated_contract_csv(tmp_path, mutate))

    assert report.status == "blocked"
    assert any(
        issue.field == "league_rank" and "must be numeric" in issue.issue
        for issue in report.issues
    )


def test_roster_rank_contract_blocks_wrong_top_five(tmp_path: Path) -> None:
    def mutate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        for row in rows:
            if row["player_name"] == "Ricky Pearsall":
                row["league_rank"] = "12"
        return rows

    report = validate_official_roster_rank_contract(_mutated_contract_csv(tmp_path, mutate))

    assert report.status == "blocked"
    assert any("expected" in issue.issue for issue in report.issues)
    assert report.top_five_names != EXPECTED_NINERS_TOP_FIVE


def test_forced_release_candidate_pool_is_top_five_only() -> None:
    report = validate_official_roster_rank_contract()
    rows = _strategy_rows(report.rows)

    profile = team_release_pressure_profile(rows)

    assert [row["player_name"] for row in profile.top_five_rows] == list(
        EXPECTED_NINERS_TOP_FIVE
    )
    assert profile.required_release_count == 1
    assert {
        row["player_name"] for row in profile.default_release_rows
    }.issubset(EXPECTED_NINERS_TOP_FIVE)
    assert "Devin Singletary" not in {
        row["player_name"] for row in profile.default_release_rows
    }
    assert profile.easy_drop_row is not None
    assert profile.easy_drop_row["player_name"] == "Devin Singletary"


def test_league_rank_contract_matches_feature_source_policy() -> None:
    with Path("docs/model_v4/FEATURE_SOURCE_CONTRACT.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(csv.DictReader(handle))

    league_rank = next(row for row in rows if row["input_name"] == "league rank")

    assert league_rank["classification"] == "context_only"
    assert league_rank["source_status"] == "rule_context_only"
    assert "Required Top-Five Release Analysis" in league_rank["model_lane_allowed"]
    assert "Dynasty Asset Value" not in league_rank["model_lane_allowed"]


def _strategy_rows(rows: tuple[object, ...]) -> list[dict[str, object]]:
    strategy_rows: list[dict[str, object]] = []
    for row in rows:
        player_name = row.player_name
        is_forced_top_five_release = player_name == "Luther Burden"
        is_easy_non_top_five_drop = player_name == "Devin Singletary"
        value = 42 if is_forced_top_five_release else 86
        if is_easy_non_top_five_drop:
            value = 1
        strategy_rows.append(
            {
                "team_id": "niners",
                "team_name": "Niners",
                "player_id": _player_id(player_name),
                "player_name": player_name,
                "position": row.position,
                "roster_status": "rostered",
                "league_rank": row.league_rank,
                "keeper_score": value,
                "private_score": value,
                "war_score": value,
                "drop_candidate_score": 100 - value,
                "market_score": 50,
                "confidence_score": 90,
            }
        )
    return strategy_rows


def _mutated_contract_csv(
    tmp_path: Path,
    mutate: object,
) -> Path:
    rows = _read_csv(OFFICIAL_NINERS_ROSTER_RANK_PATH)
    mutated_rows = mutate(rows)
    path = tmp_path / "niners_roster_rank_contract.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(mutated_rows)
    return path


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _player_id(player_name: str) -> str:
    return "p_" + "".join(
        character.lower() for character in player_name if character.isalnum()
    )
