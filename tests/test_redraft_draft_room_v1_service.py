from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from src.services.redraft_draft_room_v1_service import (
    AdpSnapshot,
    _freshness_label,
    build_draft_room_payload,
    import_owner_adp_csv,
    load_adp_snapshot,
    load_room_state,
    owner_pick_and_advance,
    refresh_fantasy_football_calculator_adp,
    run_complete_mock,
    start_draft_room,
    undo_room_pick,
    validate_complete_mock,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RedraftValidationError,
    RosterSettings,
    ScoringSettings,
)


def _ranking() -> RankingResult:
    rows: list[RedraftRankingRow] = []
    for position, count in (("QB", 30), ("RB", 80), ("WR", 100), ("TE", 30)):
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank,
                    index + 1,
                    f"{position}-{index}",
                    f"{position} {index}",
                    position,
                    "TST",
                    400 - rank,
                    0,
                    400 - rank,
                    0,
                    "HIGH" if index < 10 else "MEDIUM",
                    1 + (rank - 1) // 20,
                    "fantasy-gamers",
                    "Fantasy Gamers",
                    "GOVERNED",
                    "AVAILABLE",
                    "2026-08-17",
                    False,
                    position_tier=1 + index // 12,
                )
            )
    profile = LeagueProfile(
        "fantasy-gamers",
        "Fantasy Gamers",
        2026,
        10,
        RosterSettings(k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1),
        DraftContext(rounds=15, draft_slot=9),
        practical_mode=True,
        provider="sleeper",
        provider_league_id="1312983576827920384",
    )
    return RankingResult(
        profile,
        tuple(rows),
        (),
        (),
        "2026-08-17T00:00:00+00:00",
        "fixture",
    )


def _manual_assets() -> list[dict[str, str]]:
    return [
        {
            "player_id": f"manual:{position}:{index}",
            "player_name": f"{position} {index}",
            "position": position,
            "team": f"T{index}",
            "authority": "MANUAL — NOT MODELED BY NWR",
        }
        for position in ("K", "DST")
        for index in range(12)
    ]


def _empty_adp(profile: LeagueProfile) -> AdpSnapshot:
    return AdpSnapshot(
        profile.profile_id,
        "",
        "ppr",
        profile.team_count,
        "",
        "",
        "",
        (),
        (),
    )


@pytest.mark.parametrize("slot", [2, 5, 9])
def test_full_150_pick_mock_is_unique_legal_and_deterministic(slot: int) -> None:
    ranking = _ranking()
    first = run_complete_mock(
        ranking.profile,
        ranking,
        _manual_assets(),
        _empty_adp(ranking.profile),
        owner_slot=slot,
    )
    second = run_complete_mock(
        ranking.profile,
        ranking,
        _manual_assets(),
        _empty_adp(ranking.profile),
        owner_slot=slot,
    )
    assert validate_complete_mock(ranking.profile, first) == ()
    assert len(first["picks"]) == 150
    assert len(set(first["drafted"])) == 150
    assert [pick["player_id"] for pick in first["picks"]] == [
        pick["player_id"] for pick in second["picks"]
    ]
    assert all(
        pick["selection_behavior"] == "MANUAL_UNMODELED"
        for pick in first["picks"]
        if pick["position"] in {"K", "DST"}
    )


def test_room_starts_at_owner_persists_advances_and_undoes(tmp_path) -> None:
    ranking = _ranking()
    adp = _empty_adp(ranking.profile)
    state = start_draft_room(
        tmp_path,
        ranking.profile,
        ranking,
        _manual_assets(),
        adp,
        owner_slot=9,
    )
    assert len(state["picks"]) == 8
    assert state["picks"][-1]["team_slot"] == 8
    chosen = next(row.player_id for row in ranking.rows if row.player_id not in state["drafted"])
    state = owner_pick_and_advance(
        tmp_path,
        ranking.profile,
        ranking,
        _manual_assets(),
        adp,
        player_id=chosen,
    )
    assert len(state["picks"]) == 11
    recovered = load_room_state(tmp_path, ranking.profile, ranking, _manual_assets())
    assert recovered["drafted"] == state["drafted"]
    undone = undo_room_pick(tmp_path, ranking.profile, ranking, _manual_assets())
    assert len(undone["picks"]) == 10
    payload = build_draft_room_payload(
        ranking.profile,
        ranking,
        _manual_assets(),
        adp,
        undone,
    )
    assert len(payload["boardCells"]) == 150
    assert [card["label"] for card in payload["recommendations"]] == [
        "Best Available",
        "Best Fit",
        "Value vs ADP",
        "Upside",
        "Safer",
    ]
    assert payload["adp"]["available"] is False
    assert "not market realism" in payload["fallbackDisclosure"]


def test_owner_adp_is_validated_and_kept_separate_from_nwr_rank(tmp_path) -> None:
    ranking = _ranking()
    row = ranking.rows[19]
    csv_text = (
        "player_id,player,team,position,overall_adp,expected_pick,min_pick,max_pick,"
        "std_dev,source,scoring_format,team_count,date\n"
        f"{row.player_id},{row.player_name},{row.team},{row.position},60,60,40,80,8,"
        "Owner Export,ppr,10,2026-08-16\n"
    )
    snapshot = import_owner_adp_csv(tmp_path, ranking.profile, ranking, csv_text)
    assert snapshot.entries[0].expected_pick == 60
    assert load_adp_snapshot(tmp_path, ranking.profile).source == "Owner Export"
    state = replace(ranking.profile, draft=replace(ranking.profile.draft, draft_slot=9))
    assert state.draft.draft_slot == 9
    room = start_draft_room(
        tmp_path,
        ranking.profile,
        ranking,
        _manual_assets(),
        snapshot,
        owner_slot=9,
    )
    payload = build_draft_room_payload(
        ranking.profile,
        ranking,
        _manual_assets(),
        snapshot,
        room,
    )
    decision = next(item for item in payload["beatAdpPool"] if item["playerId"] == row.player_id)
    assert decision["nwrRank"] == 20
    assert decision["nwrView"] == "STRONG VALUE"
    assert decision["makeItBackProbability"] is not None
    bad = csv_text.replace(",ppr,10,", ",standard,10,")
    with pytest.raises(RedraftValidationError):
        import_owner_adp_csv(tmp_path, ranking.profile, ranking, bad)


def _ffc_response() -> dict[str, object]:
    return {
        "status": "Success",
        "meta": {
            "type": "PPR",
            "teams": 10,
            "rounds": 15,
            "total_drafts": 6665,
            "start_date": "2026-08-10",
            "end_date": "2026-08-17",
        },
        "players": [
            {
                "player_id": 1, "name": "RB 0", "position": "RB", "team": "TST",
                "adp": 1.7, "times_drafted": 1000, "high": 1, "low": 4, "stdev": 0.7,
            },
            {
                "player_id": 2, "name": "QB 0", "position": "QB", "team": "TST",
                "adp": 20.2, "times_drafted": 900, "high": 12, "low": 28, "stdev": 3.2,
            },
            {
                "player_id": 3, "name": "K 0", "position": "PK", "team": "T0",
                "adp": 130.0, "times_drafted": 300, "high": 115, "low": 150, "stdev": 7.0,
            },
            {
                "player_id": 4, "name": "Test Defense", "position": "DEF", "team": "T0",
                "adp": 140.0, "times_drafted": 250, "high": 120, "low": 150, "stdev": 8.0,
            },
            {
                "player_id": 5, "name": "No Safe Match", "position": "WR", "team": "XXX",
                "adp": 200.0, "times_drafted": 3, "high": 180, "low": 210, "stdev": 5.0,
            },
        ],
    }


def test_ffc_fetch_parse_metadata_cache_matching_and_kdst(tmp_path) -> None:
    ranking = _ranking()
    seen: list[str] = []
    snapshot = refresh_fantasy_football_calculator_adp(
        tmp_path,
        ranking.profile,
        ranking,
        _manual_assets(),
        fetcher=lambda endpoint: seen.append(endpoint) or _ffc_response(),
    )
    assert seen == [
        "https://fantasyfootballcalculator.com/api/v1/adp/ppr?teams=10&year=2026"
    ]
    assert snapshot.provider == "FFC"
    assert snapshot.source == "Fantasy Football Calculator ADP"
    assert snapshot.sample_size == 6665
    assert snapshot.date_window == "2026-08-10 to 2026-08-17"
    assert snapshot.freshness == "FRESH"
    assert {entry.position for entry in snapshot.entries} == {"QB", "RB", "K", "DST"}
    assert snapshot.entries[0].expected_round == 1
    assert len(snapshot.unmatched) == 1
    assert any(
        row["unmatched_reason"]
        for row in snapshot.match_report
        if row["match_status"] == "UNMATCHED"
    )
    loaded = load_adp_snapshot(tmp_path, ranking.profile)
    assert loaded.source_sha256 == snapshot.source_sha256
    assert loaded.provider == "FFC"


def test_ffc_failure_uses_last_known_good_cache(tmp_path) -> None:
    ranking = _ranking()
    first = refresh_fantasy_football_calculator_adp(
        tmp_path, ranking.profile, ranking, _manual_assets(), fetcher=lambda _: _ffc_response()
    )

    def fail(_: str) -> object:
        raise OSError("provider offline")

    cached = refresh_fantasy_football_calculator_adp(
        tmp_path, ranking.profile, ranking, _manual_assets(), fetcher=fail
    )
    assert cached.source_sha256 == first.source_sha256
    assert cached.available is True
    assert cached.last_refresh_error == "provider offline"
    assert load_adp_snapshot(tmp_path, ranking.profile).last_refresh_error == "provider offline"


def test_owner_imported_sleeper_alias_schema_overrides_ffc(tmp_path) -> None:
    ranking = _ranking()
    refresh_fantasy_football_calculator_adp(
        tmp_path, ranking.profile, ranking, _manual_assets(), fetcher=lambda _: _ffc_response()
    )
    row = ranking.rows[0]
    csv_text = (
        "player,position,team,rank,source,date,format,team_count\n"
        f"{row.player_name},{row.position},{row.team},12,Sleeper manual export,2026-08-17,PPR,10\n"
    )
    imported = import_owner_adp_csv(
        tmp_path, ranking.profile, ranking, csv_text, _manual_assets()
    )
    assert imported.source == "Owner-imported Sleeper ADP"
    assert imported.provider == "OWNER_SLEEPER_CSV"
    assert load_adp_snapshot(tmp_path, ranking.profile).provider == "OWNER_SLEEPER_CSV"


def test_ffc_cpu_source_pick_nine_and_freshness_labels(tmp_path) -> None:
    ranking = _ranking()
    snapshot = refresh_fantasy_football_calculator_adp(
        tmp_path, ranking.profile, ranking, _manual_assets(), fetcher=lambda _: _ffc_response()
    )
    mock = run_complete_mock(
        ranking.profile, ranking, _manual_assets(), snapshot, owner_slot=9
    )
    assert validate_complete_mock(ranking.profile, mock) == ()
    assert any(
        pick["selection_behavior"] == "CPU_MARKET_ADP_FFC"
        for pick in mock["picks"]
        if pick["actor"] == "CPU"
    )
    now = datetime.now(UTC)
    assert _freshness_label((now - timedelta(hours=25)).isoformat(), now=now) == "RECENT"
    assert _freshness_label((now - timedelta(hours=73)).isoformat(), now=now) == "STALE"
