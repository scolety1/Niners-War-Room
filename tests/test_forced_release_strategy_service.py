from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.draft_service import build_draft_room
from src.services.forced_release_strategy_service import (
    build_forced_release_strategy,
    forced_release_candidate_score,
    forced_release_pressure_score,
    opponent_release_target_score,
    pre_declaration_trade_urgency,
    reacquisition_priority,
    strategy_reason_code,
    team_release_pressure_profile,
)

SAMPLE_PACK = Path("sample_data/2026_pre_declaration")


def test_forced_release_strategy_requires_real_model_outputs() -> None:
    board = build_forced_release_strategy(SAMPLE_PACK)

    assert board.has_real_model_outputs is False
    assert board.candidate_rows == []


def test_forced_release_strategy_uses_lowest_value_inside_top_five(tmp_path: Path) -> None:
    pack = _scored_sample_pack(tmp_path)
    board = build_forced_release_strategy(pack)

    assert board.has_real_model_outputs is True
    niners_default = [
        row for row in board.niners_action_rows if row["is_default_release"]
    ]
    assert [row["player"] for row in niners_default] == ["Luther Burden"]
    assert niners_default[0]["rule_requirement"] == "must_release_top_five"
    assert niners_default[0]["action"] == "shop"
    assert niners_default[0]["strategy_reason"] == "shop_before_declaration"
    assert niners_default[0]["forced_release_pressure_score"] > 0
    assert "Required Top-Five Release Slot" in str(niners_default[0]["rule_explanation"])
    assert "Keeper" in str(niners_default[0]["score_explanation"])
    assert "Shop before declaration" in str(niners_default[0]["next_step"])
    assert niners_default[0]["action_label"] == "shop / reacquire"
    assert "default rule cut" in str(niners_default[0]["explanation"])
    assert niners_default[0]["top_five_value_gap"] >= 0
    assert "lowest model value inside" in str(niners_default[0]["explanation"])


def test_forced_release_strategy_handles_top_five_edge_with_no_required_cut(
    tmp_path: Path,
) -> None:
    pack = _scored_sample_pack(tmp_path)
    rankings_path = pack / "fact_official_rankings.csv"
    rows = _read_csv(rankings_path)
    for row in rows:
        if row["player_id"] not in {
            "p_achane",
            "p_lamar",
            "p_chase_brown",
            "p_luther_burden",
        }:
            row["official_rank"] = ""
            row["rank_tier"] = ""
    _write_csv(rankings_path, rows)
    roster_path = pack / "fact_rosters.csv"
    roster_rows = _read_csv(roster_path)
    for row in roster_rows:
        if row["player_id"] not in {
            "p_achane",
            "p_lamar",
            "p_chase_brown",
            "p_luther_burden",
        }:
            row["official_rank"] = ""
    _write_csv(roster_path, roster_rows)

    board = build_forced_release_strategy(pack)

    niners_team = next(row for row in board.team_rows if row["team"] == "Niners")
    assert niners_team["league_rank_top_five"] == 4
    assert niners_team["required_release_count"] == 0
    assert niners_team["decision_status"] == "no_forced_release"
    assert "no Required Top-Five Release Slot" in str(niners_team["team_explanation"])
    assert not any(row["is_default_release"] for row in board.niners_action_rows)


def test_forced_release_strategy_formulas_are_capped_and_directional() -> None:
    assert forced_release_pressure_score(
        required_release_count=1,
        keeper_score=90,
        market_score=90,
        drop_score=10,
        confidence_score=90,
        is_default_release=True,
    ) > forced_release_pressure_score(
        required_release_count=0,
        keeper_score=90,
        market_score=90,
        drop_score=10,
        confidence_score=90,
        is_default_release=True,
    )
    assert forced_release_candidate_score(
        keeper_score=80,
        drop_score=30,
        confidence_score=90,
    ) < forced_release_candidate_score(
        keeper_score=60,
        drop_score=55,
        confidence_score=70,
    )
    assert pre_declaration_trade_urgency(
        keeper_score=90,
        market_score=90,
        drop_score=10,
        confidence_score=90,
        is_default_release=True,
    ) > pre_declaration_trade_urgency(
        keeper_score=60,
        market_score=60,
        drop_score=55,
        confidence_score=80,
        is_default_release=True,
    )
    assert reacquisition_priority(
        likely_target_value=85,
        keeper_score=82,
        drop_score=20,
        is_own_team=True,
        is_default_release=True,
    ) > 60
    assert opponent_release_target_score(
        likely_target_value=85,
        keeper_score=82,
        market_score=84,
        drop_score=20,
        is_opponent=True,
        is_default_release=True,
    ) > 60
    assert strategy_reason_code(
        action="trade non-forced player",
        draft_action="",
        is_own_team=True,
        is_default_release=True,
        keeper_score=88,
        drop_score=20,
        trade_urgency=40,
        reacquisition_score=50,
        opponent_target_score=0,
    ) == "protect_top_five_by_trading_elsewhere"


def test_pressure_profile_low_when_top_five_release_is_easy() -> None:
    profile = team_release_pressure_profile(
        _pressure_team_rows(
            "easy",
            "Easy Drop Team",
            top_five_values=[95, 90, 85, 80, 45],
            non_top_values=[35, 55],
        )
    )

    assert [row["player_name"] for row in profile.default_release_rows] == [
        "Easy Drop Team Top 5"
    ]
    assert profile.pressure_level == "low"
    assert profile.forced_release_pain < 45
    assert profile.easy_drop_available is True


def test_pressure_profile_high_for_dirt_devils_style_hard_decision() -> None:
    profile = team_release_pressure_profile(
        _pressure_team_rows(
            "dirt",
            "Dirt Devils",
            top_five_values=[96, 94, 93, 92, 91],
            non_top_values=[45, 52],
        )
    )

    assert profile.pressure_level == "high"
    assert profile.forced_release_pain >= 70
    assert profile.top_five_value_gap >= 35
    assert "real forced-release pain" in profile.explanation


def test_pressure_profile_low_for_shallow_bad_team() -> None:
    profile = team_release_pressure_profile(
        _pressure_team_rows(
            "shallow",
            "Shallow Bad Team",
            top_five_values=[70, 62, 55, 48, 40],
            non_top_values=[35, 30],
        )
    )

    assert profile.pressure_level == "low"
    assert profile.forced_release_pain < 45
    assert profile.top_five_value_gap <= 10


def test_pressure_profile_tracks_multiple_bubble_players() -> None:
    profile = team_release_pressure_profile(
        _pressure_team_rows(
            "bubble",
            "Bubble Team",
            top_five_values=[90, 85, 80, 75, 70],
            non_top_values=[50, 45, 42],
        )
    )

    assert profile.pressure_level == "medium"
    assert len(profile.bubble_rows) == 3
    assert profile.easy_drop_available is True
    assert profile.release_decision_difficulty >= 60


def test_draft_room_exposes_forced_release_draft_targets(tmp_path: Path) -> None:
    pack = _scored_sample_pack(tmp_path)
    board = build_draft_room(pack)

    assert any(row["player"] == "Luther Burden" for row in board.release_target_rows)


def _scored_sample_pack(tmp_path: Path) -> Path:
    pack = tmp_path / "scored_pack"
    shutil.copytree(SAMPLE_PACK, pack)
    output_rows = _read_csv(pack / "model_outputs.csv")
    for row in output_rows:
        row["model_version"] = "veteran_lve_v1_0_0"
        row["computed_at"] = "2026-05-05T08:00:00-06:00"
        row["notes"] = "Scored fixture output."
        if row["player_id"] == "p_luther_burden":
            row["drop_candidate_score"] = "28"
            row["keeper_score"] = "83"
            row["market_score"] = "88"
            row["private_score"] = "83"
            row["war_score"] = "83"
            row["confidence_score"] = "88"
        if row["player_id"] == "p_chase_brown":
            row["drop_candidate_score"] = "12"
            row["keeper_score"] = "84"
            row["market_score"] = "82"
            row["private_score"] = "84"
            row["war_score"] = "84"
            row["confidence_score"] = "82"
    _write_csv(pack / "model_outputs.csv", output_rows)
    return pack


def _pressure_team_rows(
    team_id: str,
    team_name: str,
    *,
    top_five_values: list[float],
    non_top_values: list[float],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, value in enumerate(top_five_values, start=1):
        rows.append(
            _pressure_row(
                team_id,
                team_name,
                player_id=f"{team_id}_top_{index}",
                player_name=f"{team_name} Top {index}",
                keeper_score=value,
                league_rank=index,
            )
        )
    for index, value in enumerate(non_top_values, start=1):
        rows.append(
            _pressure_row(
                team_id,
                team_name,
                player_id=f"{team_id}_bench_{index}",
                player_name=f"{team_name} Bench {index}",
                keeper_score=value,
                league_rank=None,
            )
        )
    return rows


def _pressure_row(
    team_id: str,
    team_name: str,
    *,
    player_id: str,
    player_name: str,
    keeper_score: float,
    league_rank: int | None,
) -> dict[str, object]:
    return {
        "team_id": team_id,
        "team_name": team_name,
        "player_id": player_id,
        "player_name": player_name,
        "position": "WR",
        "roster_status": "rostered",
        "league_rank": league_rank,
        "keeper_score": keeper_score,
        "private_score": keeper_score,
        "war_score": keeper_score,
        "drop_candidate_score": max(0.0, 100.0 - keeper_score),
        "confidence_score": 90,
    }


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
