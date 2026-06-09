from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.identity_audit_service import build_identity_audit


def test_identity_audit_accepts_name_punctuation_changes(tmp_path: Path) -> None:
    data_pack = _fixture_data_pack(tmp_path)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _append_data_pack_player(
        data_pack,
        player_id="dj_moore",
        player_name="DJ Moore",
        position="WR",
        nfl_team="CHI",
        sleeper_id="dj_moore",
        pfr_id="MoorDJ00",
        war_score=87,
    )
    _write_bridge(
        source_root,
        [
            _bridge_row(
                sleeper_id="dj_moore",
                player_name="D.J. Moore",
                position="WR",
                gsis_id="00-0031234",
                pfr_id="MoorDJ00",
                method="sleeper_gsis_exact",
                status="matched",
            )
        ],
    )

    report = build_identity_audit(data_pack, source_root=source_root)
    row = _audit_row(report.rows, "DJ Moore")

    assert row["audit_status"] == "ready"
    assert row["identity_status"] == "exact_id_match"
    assert row["name_agreement"] == "normalized"
    assert row["ranking_blocked"] is False


def test_identity_audit_flags_duplicate_names_without_stable_ids(tmp_path: Path) -> None:
    data_pack = _fixture_data_pack(tmp_path)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _write_bridge(source_root, [])
    _append_data_pack_player(
        data_pack,
        player_id="michael_thomas_a",
        player_name="Michael Thomas",
        position="WR",
        nfl_team="NO",
        sleeper_id="",
        pfr_id="",
        war_score=70,
    )
    _append_data_pack_player(
        data_pack,
        player_id="michael_thomas_b",
        player_name="Michael Thomas",
        position="WR",
        nfl_team="CIN",
        sleeper_id="",
        pfr_id="",
        war_score=70,
    )

    report = build_identity_audit(data_pack, source_root=source_root)
    row = _audit_row(report.rows, "Michael Thomas")

    assert row["duplicate_name_count"] == 2
    assert row["duplicate_name_flag"] is True
    assert row["audit_status"] == "blocked"
    assert row["identity_status"] == "missing_match"
    assert row["manual_review_required"] is True


def test_identity_audit_blocks_rookie_missing_nflverse_id(tmp_path: Path) -> None:
    data_pack = _fixture_data_pack(tmp_path)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _append_data_pack_player(
        data_pack,
        player_id="rookie_missing_id",
        player_name="Rookie Missing",
        position="WR",
        nfl_team="FA",
        sleeper_id="rookie_missing_id",
        pfr_id="",
        rookie_year="2026",
        war_score=88,
    )
    _write_bridge(
        source_root,
        [
            _bridge_row(
                sleeper_id="rookie_missing_id",
                player_name="Rookie Missing",
                position="WR",
                gsis_id="",
                pfr_id="",
                method="dynastyprocess_sleeper_to_gsis",
                status="matched",
            )
        ],
    )

    report = build_identity_audit(data_pack, source_root=source_root)
    row = _audit_row(report.rows, "Rookie Missing")

    assert row["rookie_flag"] is True
    assert row["missing_gsis_id"] is True
    assert row["audit_status"] == "blocked"
    assert row["identity_status"] == "missing_match"
    assert row["ranking_trust_status"] == "blocked_identity_review"


def test_identity_audit_allows_team_change_with_strong_id(tmp_path: Path) -> None:
    data_pack = _fixture_data_pack(tmp_path)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _append_data_pack_player(
        data_pack,
        player_id="team_change_player",
        player_name="Stefon Diggs",
        position="WR",
        nfl_team="NE",
        sleeper_id="team_change_player",
        pfr_id="DiggSt00",
        war_score=84,
    )
    _write_bridge(
        source_root,
        [
            _bridge_row(
                sleeper_id="team_change_player",
                player_name="Stefon Diggs",
                position="WR",
                gsis_id="00-0031235",
                pfr_id="DiggSt00",
                method="sleeper_gsis_exact",
                status="matched",
                team="HOU",
            )
        ],
    )

    report = build_identity_audit(data_pack, source_root=source_root)
    row = _audit_row(report.rows, "Stefon Diggs")

    assert row["team_agreement"] == "team_change_or_mismatch"
    assert row["audit_status"] == "ready"
    assert row["identity_status"] == "exact_id_match"
    assert row["ranking_blocked"] is False


def test_identity_audit_blocks_high_value_missing_ids(tmp_path: Path) -> None:
    data_pack = _fixture_data_pack(tmp_path)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _write_bridge(source_root, [])
    _append_data_pack_player(
        data_pack,
        player_id="missing_ids_star",
        player_name="Missing IDs Star",
        position="RB",
        nfl_team="FA",
        sleeper_id="",
        pfr_id="",
        war_score=91,
    )

    report = build_identity_audit(data_pack, source_root=source_root)
    row = _audit_row(report.rows, "Missing IDs Star")

    assert row["audit_status"] == "blocked"
    assert row["identity_status"] == "missing_match"
    assert row["ranking_trust_status"] == "blocked_identity_review"
    assert row["ranking_blocked"] is True
    assert row["manual_review_required"] is True


def test_identity_audit_blocks_stale_or_retired_player(tmp_path: Path) -> None:
    data_pack = _fixture_data_pack(tmp_path)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _append_data_pack_player(
        data_pack,
        player_id="retired_player",
        player_name="Retired Player",
        position="WR",
        nfl_team="FA",
        sleeper_id="retired_player",
        pfr_id="RetiPl00",
        war_score=60,
        active_flag="0",
    )
    _write_bridge(
        source_root,
        [
            _bridge_row(
                sleeper_id="retired_player",
                player_name="Retired Player",
                position="WR",
                gsis_id="00-0099999",
                pfr_id="RetiPl00",
                method="sleeper_gsis_exact",
                status="matched",
            )
        ],
    )

    report = build_identity_audit(data_pack, source_root=source_root)
    row = _audit_row(report.rows, "Retired Player")

    assert row["identity_status"] == "stale_player"
    assert row["audit_status"] == "blocked"
    assert row["ranking_trust_status"] == "blocked_identity_review"


def test_identity_audit_sends_ambiguous_name_match_to_review(tmp_path: Path) -> None:
    data_pack = _fixture_data_pack(tmp_path)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _append_data_pack_player(
        data_pack,
        player_id="ambiguous_wr",
        player_name="Ambiguous Wideout",
        position="WR",
        nfl_team="FA",
        sleeper_id="ambiguous_wr",
        pfr_id="",
        war_score=70,
    )
    _write_bridge(
        source_root,
        [
            _bridge_row(
                sleeper_id="ambiguous_wr",
                player_name="Ambiguous Wideout",
                position="WR",
                gsis_id="00-0088888",
                pfr_id="",
                method="name_position_team",
                status="ambiguous",
            )
        ],
    )

    report = build_identity_audit(data_pack, source_root=source_root)
    row = _audit_row(report.rows, "Ambiguous Wideout")

    assert row["identity_status"] == "ambiguous_match"
    assert row["audit_status"] == "review"
    assert row["manual_review_required"] is True


def test_identity_audit_allows_free_agent_with_stable_crosswalk(tmp_path: Path) -> None:
    data_pack = _fixture_data_pack(tmp_path)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _append_data_pack_player(
        data_pack,
        player_id="free_agent_player",
        player_name="Free Agent Player",
        position="RB",
        nfl_team="FA",
        sleeper_id="free_agent_player",
        pfr_id="FreeAg00",
        war_score=65,
    )
    _write_bridge(
        source_root,
        [
            _bridge_row(
                sleeper_id="free_agent_player",
                player_name="Free Agent Player",
                position="RB",
                gsis_id="00-0077777",
                pfr_id="FreeAg00",
                method="dynastyprocess_sleeper_to_gsis",
                status="matched",
            )
        ],
    )

    report = build_identity_audit(data_pack, source_root=source_root)
    row = _audit_row(report.rows, "Free Agent Player")

    assert row["team_agreement"] in {"not_available", "team_change_or_mismatch"}
    assert row["identity_status"] == "crosswalk_match"
    assert row["audit_status"] == "ready"


def _fixture_data_pack(tmp_path: Path) -> Path:
    data_pack = tmp_path / "data_pack"
    shutil.copytree(Path("sample_data/2026_pre_declaration"), data_pack)
    return data_pack


def _append_data_pack_player(
    data_pack: Path,
    *,
    player_id: str,
    player_name: str,
    position: str,
    nfl_team: str,
    sleeper_id: str,
    pfr_id: str,
    war_score: float,
    rookie_year: str = "2021",
    active_flag: str = "1",
) -> None:
    players_path = data_pack / "dim_players.csv"
    players = _read_rows(players_path)
    players.append(
        {
            "player_id": player_id,
            "player_name": player_name,
            "merge_name": player_name.lower().replace(".", ""),
            "position": position,
            "nfl_team": nfl_team,
            "birth_date": "",
            "rookie_year": rookie_year,
            "height_in": "",
            "weight_lb": "",
            "sleeper_id": sleeper_id,
            "fantasypros_id": "",
            "ktc_id": "",
            "fantasycalc_id": "",
            "pfr_id": pfr_id,
            "cfb_id": "",
            "active_flag": active_flag,
            "created_at": "2026-08-01",
            "updated_at": "2026-08-01",
        }
    )
    _write_rows(players_path, players)

    rosters_path = data_pack / "fact_rosters.csv"
    rosters = _read_rows(rosters_path)
    rosters.append(
        {
            "snapshot_date": "2026-08-01",
            "season": "2026",
            "league_id": "lve",
            "team_id": "fixture",
            "team_name": "Fixture Team",
            "owner_name": "Fixture",
            "player_id": player_id,
            "player_name": player_name,
            "position": position,
            "nfl_team": nfl_team,
            "roster_status": "rostered",
            "official_rank": "99",
            "source": "fixture",
        }
    )
    _write_rows(rosters_path, rosters)

    outputs_path = data_pack / "model_outputs.csv"
    outputs = _read_rows(outputs_path)
    outputs.append(
        {
            "snapshot_date": "2026-08-01",
            "player_id": player_id,
            "player_name": player_name,
            "position": position,
            "private_score": str(war_score),
            "market_score": str(war_score),
            "war_score": str(war_score),
            "keeper_score": str(war_score),
            "drop_candidate_score": "10",
            "smash_prob": "",
            "hit_prob": "",
            "useful_prob": "",
            "replaceable_prob": "",
            "miss_prob": "",
            "bust_prob": "",
            "pick_adjusted_value": "",
            "confidence_score": "0.9",
            "risk_level": "low",
            "recommendation": "keep",
            "do_not_draft_before_pick": "",
            "notes": "",
        }
    )
    _write_rows(outputs_path, outputs)


def _bridge_row(
    *,
    sleeper_id: str,
    player_name: str,
    position: str,
    gsis_id: str,
    pfr_id: str,
    method: str,
    status: str,
    team: str = "",
) -> dict[str, str]:
    return {
        "sleeper_id": sleeper_id,
        "player_name": player_name,
        "position": position,
        "sleeper_gsis_id": gsis_id,
        "bridge_gsis_id": gsis_id,
        "bridge_pfr_id": pfr_id,
        "bridge_name": player_name,
        "matched_gsis_id": gsis_id,
        "stat_player_name": player_name,
        "match_method": method,
        "match_status": status,
        "manual_review_required": "false",
        "team": team,
    }


def _write_bridge(source_root: Path, rows: list[dict[str, str]]) -> None:
    path = source_root / "sleeper_nflverse_identity_bridge.csv"
    fieldnames = [
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
        "team",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _audit_row(rows: list[dict[str, object]], player: str) -> dict[str, object]:
    matches = [row for row in rows if row["player"] == player]
    assert matches
    return matches[0]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
