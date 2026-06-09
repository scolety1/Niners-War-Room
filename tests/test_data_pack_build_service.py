from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.command_board_service import build_team_command_board
from src.services.data_pack_build_service import (
    build_data_pack_from_refresh,
    data_pack_status_rows,
    find_latest_rank_merge_for_snapshot,
)
from src.services.data_pack_health_service import build_data_pack_health_report


def test_build_data_pack_from_refresh_uses_merged_league_ranks(tmp_path: Path) -> None:
    sleeper_dir = tmp_path / "sleeper" / "league_1_20260505_120000"
    merged_dir = tmp_path / "merged" / "league_1_20260505_120000_pdf_ranks"
    sleeper_dir.mkdir(parents=True)
    merged_dir.mkdir(parents=True)
    _write_csv(sleeper_dir / "sleeper_league_settings.csv", _league_settings())
    _write_csv(sleeper_dir / "sleeper_future_picks.csv", _future_picks())
    _write_csv(sleeper_dir / "sleeper_rosters.csv", [_sleeper_roster_row("")])
    _write_csv(
        merged_dir / "sleeper_rosters_with_pdf_ranks.csv",
        [_sleeper_roster_row("27")],
    )

    result = build_data_pack_from_refresh(
        sleeper_output_dir=sleeper_dir,
        merged_rank_output_dir=merged_dir,
        output_root=tmp_path / "data_packs",
    )

    assert result.counts["fact_rosters.csv"] == 1
    assert result.counts["fact_pick_values.csv"] == 1
    assert not result.warnings
    roster_rows = _read_csv(result.files["fact_rosters.csv"])
    ranking_rows = _read_csv(result.files["fact_official_rankings.csv"])
    assert roster_rows[0]["league_rank"] == "27"
    assert roster_rows[0]["official_rank"] == "27"
    assert ranking_rows[0]["league_rank"] == "27"
    assert ranking_rows[0]["rank_source_date"] == "2026-02-27"
    assert result.files["model_outputs.csv"].exists()
    assert data_pack_status_rows(result)[0]["rows"] == 1

    validated = validate_data_pack(result.output_dir, roster_limit=1)
    assert not validated.has_errors


def test_build_data_pack_generates_real_model_outputs_when_veteran_inputs_exist(
    tmp_path: Path,
) -> None:
    sleeper_dir = tmp_path / "sleeper" / "league_1_20260505_120000"
    merged_dir = tmp_path / "merged" / "league_1_20260505_120000_pdf_ranks"
    veteran_dir = _single_player_veteran_inputs(tmp_path, "p1", "Alpha Back")
    sleeper_dir.mkdir(parents=True)
    merged_dir.mkdir(parents=True)
    _write_csv(sleeper_dir / "sleeper_league_settings.csv", _league_settings())
    _write_csv(sleeper_dir / "sleeper_future_picks.csv", _future_picks())
    _write_csv(sleeper_dir / "sleeper_rosters.csv", [_sleeper_roster_row("")])
    _write_csv(
        merged_dir / "sleeper_rosters_with_pdf_ranks.csv",
        [_sleeper_roster_row("27")],
    )

    result = build_data_pack_from_refresh(
        sleeper_output_dir=sleeper_dir,
        merged_rank_output_dir=merged_dir,
        veteran_model_input_dir=veteran_dir,
        output_root=tmp_path / "data_packs",
    )

    output_rows = _read_csv(result.files["model_outputs.csv"])
    assert output_rows[0]["model_version"] == "veteran_lve_v1_3_0"
    assert output_rows[0]["computed_at"]
    assert output_rows[0]["risk_level"] != "needs_model"
    assert output_rows[0]["private_score"] != "50"
    assert output_rows[0]["veteran_base_value"]
    assert output_rows[0]["horizon_retention_score"]
    assert output_rows[0]["lve_format_fit"]
    assert output_rows[0]["structural_adjustment"]
    assert output_rows[0]["risk_flags"] == ""
    assert output_rows[0]["floor_flags"]
    assert "Neutral placeholder" not in output_rows[0]["notes"]

    health = build_data_pack_health_report(result.output_dir, roster_limit=1)
    assert health.placeholder_model_output_count == 0


def test_build_data_pack_keeps_placeholder_warning_when_veteran_inputs_are_absent(
    tmp_path: Path,
) -> None:
    sleeper_dir = tmp_path / "sleeper" / "league_1_20260505_120000"
    sleeper_dir.mkdir(parents=True)
    _write_csv(sleeper_dir / "sleeper_league_settings.csv", _league_settings())
    _write_csv(sleeper_dir / "sleeper_future_picks.csv", _future_picks())
    _write_csv(sleeper_dir / "sleeper_rosters.csv", [_sleeper_roster_row("27")])

    result = build_data_pack_from_refresh(
        sleeper_output_dir=sleeper_dir,
        output_root=tmp_path / "data_packs",
    )

    health = build_data_pack_health_report(result.output_dir, roster_limit=1)
    assert health.placeholder_model_output_count == 1
    assert health.checks[4].status == "review"


def test_forced_release_candidate_uses_visible_scored_drop_score(tmp_path: Path) -> None:
    sleeper_dir = tmp_path / "sleeper" / "league_1_20260505_120000"
    merged_dir = tmp_path / "merged" / "league_1_20260505_120000_pdf_ranks"
    veteran_dir = _multi_player_veteran_inputs(tmp_path)
    sleeper_dir.mkdir(parents=True)
    merged_dir.mkdir(parents=True)
    _write_csv(sleeper_dir / "sleeper_league_settings.csv", _league_settings())
    _write_csv(sleeper_dir / "sleeper_future_picks.csv", _future_picks())
    roster_rows = [
        _ranked_roster_row(f"p{index}", f"Player {index}", str(index))
        for index in range(1, 6)
    ]
    _write_csv(sleeper_dir / "sleeper_rosters.csv", roster_rows)
    _write_csv(merged_dir / "sleeper_rosters_with_pdf_ranks.csv", roster_rows)

    result = build_data_pack_from_refresh(
        sleeper_output_dir=sleeper_dir,
        merged_rank_output_dir=merged_dir,
        veteran_model_input_dir=veteran_dir,
        output_root=tmp_path / "data_packs",
    )
    board = build_team_command_board(
        result.output_dir,
        team_id="Niners",
        protect_limit=4,
        official_top_five_keep_limit=4,
    )

    visible_drop_scores = {row["player"]: row["drop_score"] for row in board.top_five_rows}
    assert len(board.forced_release_rows) == 1
    assert board.forced_release_rows[0]["player"] == "Player 3"
    assert board.forced_release_rows[0]["drop_score"] == visible_drop_scores["Player 3"]
    assert board.forced_release_rows[0]["action"] == "shop/release"
    assert visible_drop_scores["Player 3"] == max(visible_drop_scores.values())


def test_build_data_pack_from_refresh_falls_back_to_raw_sleeper_rosters(
    tmp_path: Path,
) -> None:
    sleeper_dir = tmp_path / "sleeper" / "league_1_20260505_120000"
    sleeper_dir.mkdir(parents=True)
    _write_csv(sleeper_dir / "sleeper_league_settings.csv", _league_settings())
    _write_csv(sleeper_dir / "sleeper_future_picks.csv", _future_picks())
    _write_csv(sleeper_dir / "sleeper_rosters.csv", [_sleeper_roster_row("")])

    result = build_data_pack_from_refresh(
        sleeper_output_dir=sleeper_dir,
        output_root=tmp_path / "data_packs",
    )

    assert any("blank league ranks" in warning for warning in result.warnings)
    roster_rows = _read_csv(result.files["fact_rosters.csv"])
    assert roster_rows[0]["league_rank"] == ""
    assert roster_rows[0]["official_rank"] == ""


def test_find_latest_rank_merge_for_snapshot(tmp_path: Path) -> None:
    sleeper_dir = tmp_path / "sleeper" / "league_1_20260505_120000"
    expected = tmp_path / "merged" / "league_1_20260505_120000_pdf_ranks"
    expected.mkdir(parents=True)
    (expected / "sleeper_rosters_with_pdf_ranks.csv").write_text("x\n", encoding="utf-8")

    assert (
        find_latest_rank_merge_for_snapshot(
            sleeper_output_dir=sleeper_dir,
            merged_output_root=tmp_path / "merged",
        )
        == expected
    )


def _league_settings() -> list[dict[str, str]]:
    return [
        {
            "setting_group": "league",
            "setting_key": "league_id",
            "setting_value": "league_1",
            "source": "sleeper_api",
        },
        {
            "setting_group": "league",
            "setting_key": "season",
            "setting_value": "2026",
            "source": "sleeper_api",
        },
    ]


def _future_picks() -> list[dict[str, str]]:
    return [
        {
            "snapshot_date": "2026-pre-draft",
            "season": "2026",
            "pick_year": "2026",
            "round": "1",
            "slot": "1",
            "pick_label": "2026 1.01",
            "overall_pick": "1",
            "original_team_id": "1",
            "original_team_name": "Niners",
            "current_team_id": "1",
            "current_team_name": "Niners",
            "current_owner_name": "Niners",
            "certainty": "sleeper_current_owner",
            "source": "sleeper_api_traded_picks",
        }
    ]


def _sleeper_roster_row(league_rank: str) -> dict[str, str]:
    return {
        "snapshot_date": "2026-pre-draft",
        "season": "2026",
        "team_id": "1",
        "team_name": "Niners",
        "owner_name": "Niners",
        "player_id": "p1",
        "player_name": "Alpha Back",
        "position": "RB",
        "nfl_team": "MIA",
        "roster_status": "rostered",
        "league_rank": league_rank,
        "source": "sleeper_api",
        "paper_source": "lve_rosters_pdf_033126_rosters" if league_rank else "",
    }


def _ranked_roster_row(player_id: str, player_name: str, league_rank: str) -> dict[str, str]:
    row = _sleeper_roster_row(league_rank)
    row["player_id"] = player_id
    row["player_name"] = player_name
    row["position"] = "RB"
    return row


def _single_player_veteran_inputs(
    tmp_path: Path,
    player_id: str,
    player_name: str,
) -> Path:
    veteran_dir = tmp_path / f"veteran_inputs_{player_id}"
    shutil.copytree("sample_data/veteran_model_v1", veteran_dir)
    player_rows = _read_csv(veteran_dir / "veteran_player_inputs.csv")
    feature_rows = _read_csv(veteran_dir / "veteran_feature_scores.csv")
    source_player_id = "devon_achane"
    for row in player_rows:
        if row["player_id"] == source_player_id:
            row["player_id"] = player_id
            row["player_name"] = player_name
            row["team_id"] = "1"
            row["team_name"] = "Niners"
            row["league_rank"] = "27"
    for row in feature_rows:
        if row["player_id"] == source_player_id:
            row["player_id"] = player_id
    _write_csv(veteran_dir / "veteran_player_inputs.csv", player_rows)
    _write_csv(veteran_dir / "veteran_feature_scores.csv", feature_rows)
    return veteran_dir


def _multi_player_veteran_inputs(tmp_path: Path) -> Path:
    veteran_dir = tmp_path / "veteran_inputs_forced_release"
    veteran_dir.mkdir()
    _write_csv(
        veteran_dir / "veteran_feature_registry.csv",
        [
            row
            for row in _read_csv("sample_data/veteran_model_v1/veteran_feature_registry.csv")
            if row["position"] == "RB"
        ],
    )
    _write_csv(
        veteran_dir / "veteran_source_catalog.csv",
        _read_csv("sample_data/veteran_model_v1/veteran_source_catalog.csv"),
    )
    _write_csv(
        veteran_dir / "veteran_audit_notes.csv",
        [
            {
                "note_id": "note_forced_release_fixture",
                "season": "2026",
                "player_id": "p1",
                "feature_name": "role_security",
                "note_scope": "validation",
                "note_text": "Fixture note for forced release model output test.",
                "source_key": "manual_fixture_2026",
                "affects_score": "false",
                "created_at": "2026-05-05T08:30:00-06:00",
            }
        ],
    )
    _write_csv(
        veteran_dir / "veteran_player_inputs.csv",
        [
            {
                "season": "2026",
                "snapshot_date": "2026-05-05",
                "player_id": f"p{index}",
                "player_name": f"Player {index}",
                "position": "RB",
                "nfl_team": "MIA",
                "age": "26.0",
                "team_id": "1",
                "team_name": "Niners",
                "league_rank": str(index),
                "is_league_rank_top5": "true",
                "source_snapshot_id": "phase19_fixture",
                "source_name": "manual_fixture",
                "source_date": "2026-05-05",
                "data_quality_tier": "verified",
            }
            for index in range(1, 6)
        ],
    )
    values_by_player = {
        "p1": (88, 86, 84, 82, 80),
        "p2": (86, 84, 82, 80, 78),
        "p3": (42, 40, 35, 30, 70),
        "p4": (84, 83, 82, 81, 80),
        "p5": (82, 82, 80, 78, 78),
    }
    feature_names = (
        "lve_projection_value",
        "role_security",
        "age_curve",
        "first_down_td_fit",
        "injury_durability",
    )
    feature_rows = []
    for player_id, values in values_by_player.items():
        for feature_name, value in zip(feature_names, values, strict=True):
            feature_rows.append(
                {
                    "season": "2026",
                    "snapshot_date": "2026-05-05",
                    "player_id": player_id,
                    "position": "RB",
                    "feature_name": feature_name,
                    "normalized_score": str(value),
                    "source_key": "manual_fixture_2026",
                    "source_confidence": "manual",
                    "is_missing": "false",
                    "missing_reason": "",
                    "is_user_override": "false",
                    "override_reason": "",
                }
            )
    _write_csv(veteran_dir / "veteran_feature_scores.csv", feature_rows)
    return veteran_dir


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
