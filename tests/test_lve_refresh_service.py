from __future__ import annotations

from pathlib import Path

from src.services.lve_refresh_service import (
    find_latest_sleeper_snapshot,
    refresh_status_rows,
    run_full_refresh,
)


def test_run_full_refresh_writes_sleeper_snapshot_and_rank_merge(tmp_path: Path) -> None:
    rank_text_path = tmp_path / "rank_text.txt"
    rank_text_path.write_text(
        "\n".join(
            [
                (
                    "1 Alpha Back RB MIA 10 1 Beta Passer QB BAL 20 "
                    "1 Gamma Receiver WR LAC 30 1 Delta Tight TE DAL 40 "
                    "1 Epsilon Flex WR SEA 50"
                ),
                "Free Agents",
                "194 Free Agent LAC WR71",
            ]
        ),
        encoding="utf-8",
    )

    result = run_full_refresh(
        league_id="league_1",
        rank_text_path=rank_text_path,
        sleeper_output_root=tmp_path / "sleeper",
        merged_output_root=tmp_path / "merged",
        client=FakeSleeperClient(),
        snapshot_name="20260505_120000",
    )

    assert result.sleeper_result is not None
    assert result.rank_merge_result is not None
    assert (
        result.sleeper_result.output_dir
        == tmp_path / "sleeper" / "league_1_20260505_120000"
    )
    assert result.sleeper_result.counts["rosters"] == 5
    assert result.rank_merge_result.counts["sleeper_rosters_with_pdf_ranks"] == 5
    assert all(step.status == "ok" for step in result.steps)
    assert any("summer/declaration" in warning for warning in result.warnings)

    status_rows = refresh_status_rows(result)
    assert any(row["step"] == "sleeper_rosters" for row in status_rows)
    assert any(row["step"] == "league_rank_comparison_summary" for row in status_rows)


def test_run_full_refresh_skips_rank_merge_when_rank_text_is_missing(
    tmp_path: Path,
) -> None:
    result = run_full_refresh(
        league_id="league_1",
        rank_text_path=tmp_path / "missing.txt",
        sleeper_output_root=tmp_path / "sleeper",
        merged_output_root=tmp_path / "merged",
        client=FakeSleeperClient(),
        snapshot_name="20260505_120000",
    )

    assert result.sleeper_result is not None
    assert result.rank_merge_result is None
    assert any(step.step_name == "league_rank_merge" for step in result.steps)
    assert any(step.status == "skipped" for step in result.steps)
    assert any("missing" in warning for warning in result.warnings)


def test_find_latest_sleeper_snapshot(tmp_path: Path) -> None:
    older = tmp_path / "league_1_20260505_010000"
    newer = tmp_path / "league_1_20260505_020000"
    older.mkdir()
    newer.mkdir()
    (older / "sleeper_rosters.csv").write_text("x\n", encoding="utf-8")
    (newer / "sleeper_rosters.csv").write_text("x\n", encoding="utf-8")

    assert (
        find_latest_sleeper_snapshot(league_id="league_1", output_root=tmp_path)
        == newer
    )


class FakeSleeperClient:
    def get_json(self, path: str):
        return _fake_payload()[path]


def _fake_payload() -> dict[str, object]:
    league = {
        "league_id": "league_1",
        "season": "2026",
        "name": "Test League",
        "roster_positions": ["QB", "RB", "WR", "TE", "FLEX"],
        "scoring_settings": {"rec": 0, "rush_fd": 0.4},
    }
    users = [
        _user("u1", "Alpha Team"),
        _user("u2", "Beta Team"),
        _user("u3", "Gamma Team"),
        _user("u4", "Delta Team"),
        _user("u5", "Epsilon Team"),
    ]
    rosters = [
        _roster(1, "u1", "p1"),
        _roster(2, "u2", "p2"),
        _roster(3, "u3", "p3"),
        _roster(4, "u4", "p4"),
        _roster(5, "u5", "p5"),
    ]
    players = {
        "p1": _player("Alpha Back", "RB", "MIA"),
        "p2": _player("Beta Passer", "QB", "BAL"),
        "p3": _player("Gamma Receiver", "WR", "LAC"),
        "p4": _player("Delta Tight", "TE", "DAL"),
        "p5": _player("Epsilon Flex", "WR", "SEA"),
    }
    draft = {
        "draft_id": "draft_1",
        "season": "2026",
        "status": "pre_draft",
        "type": "linear",
        "draft_order": {"u1": 1, "u2": 2, "u3": 3, "u4": 4, "u5": 5},
        "settings": {"rounds": 5, "teams": 5},
    }
    return {
        "league/league_1": league,
        "league/league_1/users": users,
        "league/league_1/rosters": rosters,
        "league/league_1/traded_picks": [],
        "league/league_1/drafts": [draft],
        "players/nfl": players,
    }


def _user(user_id: str, team_name: str) -> dict[str, object]:
    return {
        "user_id": user_id,
        "display_name": team_name,
        "metadata": {"team_name": team_name},
    }


def _roster(roster_id: int, owner_id: str, player_id: str) -> dict[str, object]:
    return {"roster_id": roster_id, "owner_id": owner_id, "players": [player_id]}


def _player(name: str, position: str, team: str) -> dict[str, str]:
    return {"full_name": name, "position": position, "team": team}
