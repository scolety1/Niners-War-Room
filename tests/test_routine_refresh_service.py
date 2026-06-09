from __future__ import annotations

from pathlib import Path

from src.services.routine_refresh_service import (
    routine_refresh_status_rows,
    run_routine_refresh,
)


def test_routine_refresh_success_builds_candidate_pack(tmp_path: Path) -> None:
    rank_text = _rank_text(tmp_path)

    result = run_routine_refresh(
        league_id="league_1",
        rank_text_path=rank_text,
        sleeper_output_root=tmp_path / "sleeper",
        merged_output_root=tmp_path / "merged",
        data_pack_output_root=tmp_path / "data_packs",
        veteran_model_input_dir=tmp_path / "missing_model_inputs",
        client=FakeSleeperClient(),
        run_id="20260507_120000",
    )

    rows = routine_refresh_status_rows(result)
    assert result.status in {"ready", "review"}
    assert result.active_candidate_pack is not None
    assert result.active_candidate_pack.exists()
    assert (result.active_candidate_pack / "fact_rosters.csv").exists()
    assert (result.active_candidate_pack / "model_outputs.csv").exists()
    assert any(row["step"] == "sleeper_snapshot" and row["status"] == "ok" for row in rows)
    assert any(row["step"] == "league_rank_merge" and row["status"] == "ok" for row in rows)
    assert any(row["step"] == "data_pack_build" and row["mutated"] is True for row in rows)
    assert any(row["step"] == "validate_pack" and row["status"] == "ok" for row in rows)
    assert any(row["step"] == "model_scoring" and row["status"] == "skipped" for row in rows)


def test_routine_refresh_partial_failure_reports_sleeper_error(tmp_path: Path) -> None:
    result = run_routine_refresh(
        league_id="league_1",
        rank_text_path=tmp_path / "missing.txt",
        sleeper_output_root=tmp_path / "sleeper",
        merged_output_root=tmp_path / "merged",
        data_pack_output_root=tmp_path / "data_packs",
        client=FailingSleeperClient(),
        run_id="20260507_120000",
    )

    rows = routine_refresh_status_rows(result)
    assert result.status == "blocked"
    assert result.active_candidate_pack is None
    assert any(row["step"] == "sleeper_snapshot" and row["status"] == "error" for row in rows)
    assert not (tmp_path / "data_packs").exists()


def test_routine_refresh_dry_run_does_not_mutate_files(tmp_path: Path) -> None:
    rank_text = _rank_text(tmp_path)

    result = run_routine_refresh(
        league_id="league_1",
        rank_text_path=rank_text,
        sleeper_output_root=tmp_path / "sleeper",
        merged_output_root=tmp_path / "merged",
        data_pack_output_root=tmp_path / "data_packs",
        client=FakeSleeperClient(),
        dry_run=True,
        run_id="20260507_120000",
    )

    rows = routine_refresh_status_rows(result)
    assert result.status == "planned"
    assert result.dry_run is True
    assert result.active_candidate_pack == (
        tmp_path / "data_packs" / "league_1_20260507_120000_routine_refresh"
    )
    assert all(row["mutated"] is False for row in rows)
    assert not (tmp_path / "sleeper").exists()
    assert not (tmp_path / "merged").exists()
    assert not (tmp_path / "data_packs").exists()


def test_routine_refresh_blocks_frozen_output_root(tmp_path: Path) -> None:
    result = run_routine_refresh(
        league_id="league_1",
        rank_text_path=tmp_path / "missing.txt",
        sleeper_output_root=tmp_path / "sleeper",
        data_pack_output_root=tmp_path / "draft_freezes",
        client=FakeSleeperClient(),
        run_id="20260507_120000",
    )

    rows = routine_refresh_status_rows(result)
    assert result.status == "blocked"
    assert any(row["step"] == "output_guard" and row["status"] == "error" for row in rows)
    assert not (tmp_path / "draft_freezes").exists()


def _rank_text(tmp_path: Path) -> Path:
    path = tmp_path / "rank_text.txt"
    path.write_text(
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
    return path


class FakeSleeperClient:
    def get_json(self, path: str):
        return _fake_payload()[path]


class FailingSleeperClient:
    def get_json(self, path: str):
        raise RuntimeError(f"boom: {path}")


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
