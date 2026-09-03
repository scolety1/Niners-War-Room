from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from src.application.contracts import public_json_value
from src.services.redraft_draft_room_v1_service import (
    AdpSnapshot,
    approve_owner_platform_manual_match,
    clear_owner_platform_manual_match,
    clear_pick,
    fill_gap_pick,
    _adp_explanation,
    _asset_pool,
    _freshness_label,
    _owner_platform_rows,
    _recommendations,
    _save_room_state,
    build_draft_room_payload,
    import_owner_adp_csv,
    ingest_read_only_sleeper_pick,
    load_adp_snapshot,
    load_room_state,
    owner_pick_and_advance,
    refresh_fantasy_football_calculator_adp,
    preview_owner_paste_adp,
    replace_pick,
    run_complete_mock,
    save_owner_paste_adp,
    set_owner_platform_selection,
    start_draft_room,
    sync_read_only_sleeper_picks,
    undo_pick_correction,
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
        "Value vs ESPN",
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


def test_ffc_remains_above_generic_owner_csv_in_provider_priority(tmp_path) -> None:
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
    assert load_adp_snapshot(tmp_path, ranking.profile).provider == "FFC"


def test_owner_platform_snapshot_serves_profiles_and_uses_platform_fallbacks(tmp_path) -> None:
    ranking = _ranking()
    refresh_fantasy_football_calculator_adp(
        tmp_path, ranking.profile, ranking, _manual_assets(), fetcher=lambda _: _ffc_response()
    )
    paste = (
        "| Position | Player | Consensus | Sleeper | ESPN | FantasyPros |\n"
        "| --- | --- | ---: | ---: | ---: | ---: |\n"
        "| QB1 | QB 0 | 1.5 | — | 2.1 | 1.8 |\n"
        "| RB1 | RB 0 | 2.5 | 2.2 | 2.7 | 2.4 |\n"
        "| WR1 | Unknown Player | 5.0 | - | 5.1 | 5.2 |\n"
    )
    preview = preview_owner_paste_adp(ranking.profile, ranking, paste, "SLEEPER", _manual_assets())
    assert preview["parserMode"] == "MARKDOWN_TABLE"
    assert preview["matchedRows"] == 2
    assert preview["sourceRows"] == 3
    assert preview["parsedRows"][0]["selected_adp"] is None
    assert preview["parsedRows"][1]["selected_adp"] == 2.2
    assert preview["parsedRows"][2]["unmatched_reason"] == "NOT_IN_ACTIVE_REDRAFT_BOARD"
    snapshot = save_owner_paste_adp(
        tmp_path, ranking.profile, ranking, paste, "CONSENSUS", "Owner platform", _manual_assets()
    )
    assert snapshot.provider == "OWNER_PASTE_CONSENSUS"
    assert len(snapshot.paste_rows) == 3
    active = load_adp_snapshot(tmp_path, ranking.profile)
    assert active.provider == "OWNER_PLATFORM_AUTO_SLEEPER"
    assert active.by_player_id["QB-0"].overall_adp == 1.5
    assert active.by_player_id["RB-0"].overall_adp == 2.2
    assert _adp_explanation(active, "QB-0", active.by_player_id["QB-0"])["source"] == "Consensus fallback"
    assert _adp_explanation(active, "not-in-adp", None)["unavailableReason"] == "NO_ACTIVE_ADP_FOR_PLAYER"
    assert active.source == "Owner-imported Sleeper ADP — Owner platform"
    assert (tmp_path / "adp_provider_cache" / "owner_platform_snapshot" / "snapshot.txt").read_text(encoding="utf-8") == paste
    espn_profile = replace(ranking.profile, profile_id="espn-test", provider="espn", provider_league_id="2026")
    refresh_fantasy_football_calculator_adp(
        tmp_path, espn_profile, ranking, _manual_assets(), fetcher=lambda _: _ffc_response()
    )
    assert load_adp_snapshot(tmp_path, espn_profile).provider == "OWNER_PLATFORM_AUTO_ESPN"
    assert load_adp_snapshot(tmp_path, espn_profile).by_player_id["RB-0"].overall_adp == 2.7
    manual_profile = replace(ranking.profile, profile_id="manual-test", provider="local", provider_league_id=None)
    assert load_adp_snapshot(tmp_path, manual_profile).provider == "OWNER_PLATFORM_AUTO_CONSENSUS"
    set_owner_platform_selection(tmp_path, espn_profile, "FANTASYPROS")
    assert load_adp_snapshot(tmp_path, espn_profile).provider == "OWNER_PLATFORM_FANTASYPROS"
    assert load_adp_snapshot(tmp_path, espn_profile).by_player_id["RB-0"].overall_adp == 2.4
    set_owner_platform_selection(tmp_path, espn_profile, "DISABLED")
    assert load_adp_snapshot(tmp_path, espn_profile).provider == "FFC"
    assert (tmp_path / "adp_provider_cache" / "owner_platform_snapshot" / "snapshot.json").is_file()
    mock = run_complete_mock(ranking.profile, ranking, _manual_assets(), active, owner_slot=9)
    assert any(pick["selection_behavior"] == "CPU_MARKET_ADP_OWNER_AUTO_SLEEPER" for pick in mock["picks"] if pick["actor"] == "CPU")
    room = build_draft_room_payload(ranking.profile, ranking, _manual_assets(), active, {
        "profile_id": ranking.profile.profile_id, "owner_slot": 9, "seed": 1729,
        "speed": "NORMAL", "mode": "MOCK", "drafted": [], "picks": [],
    })
    assert room["adp"]["source"] == "Owner-imported Sleeper ADP — Owner platform"
    assert any(item["playerId"] == "RB-0" and item["overallAdp"] == 2.2 for item in room["decisionRows"])


def test_owner_platform_plain_text_split_and_compact_parser(tmp_path) -> None:
    ranking = _ranking()
    plain_text = """WR
13
WR 0
29.3 28.1 32.0 27.8

RB14
RB 0
32.0 25.2 — 38.9
"""
    preview = preview_owner_paste_adp(ranking.profile, ranking, plain_text, "SLEEPER", _manual_assets())
    assert preview["parserMode"] == "RESPONSIVE_PLATFORM_CLIPBOARD"
    assert preview["sourceRows"] == 2
    assert preview["parsedRows"][0]["consensus_adp"] == 29.3
    assert preview["parsedRows"][0]["sleeper_adp"] == 28.1
    assert preview["parsedRows"][0]["espn_adp"] == 32.0
    assert preview["parsedRows"][0]["fantasypros_adp"] == 27.8
    assert preview["parsedRows"][1]["sleeper_adp"] == 25.2
    assert preview["parsedRows"][1]["espn_adp"] is None
    assert preview["platformCoverage"]["consensus"] == {"available": 2, "total": 2}
    assert preview["platformCoverage"]["sleeper"] == {"available": 2, "total": 2}
    assert preview["platformCoverage"]["espn"] == {"available": 1, "total": 2}
    public_preview = public_json_value({"platformCoverage": preview["platformCoverage"]})
    assert public_preview["platformCoverage"]["sleeper"] == {"available": 2, "total": 2}
    rendered_row = public_json_value(preview["parsedRows"][0])
    assert rendered_row["sourceRowIndex"] == 1
    assert rendered_row["positionRank"] == 13
    assert rendered_row["playerName"] == "WR 0"
    assert rendered_row["consensusAdp"] == 29.3
    assert rendered_row["sleeperAdp"] == 28.1
    rendered_row = public_json_value(preview["parsedRows"][0])
    assert rendered_row["sourceRowIndex"] == 1
    assert rendered_row["positionRank"] == 13
    assert rendered_row["playerName"] == "WR 0"
    assert rendered_row["consensusAdp"] == 29.3
    assert rendered_row["sleeperAdp"] == 28.1
    with pytest.raises(RedraftValidationError, match="markdown pipe table, or plain-text blocks"):
        preview_owner_paste_adp(ranking.profile, ranking, "not a platform table", "CONSENSUS", _manual_assets())


def test_responsive_clipboard_parser_supports_status_team_noise_and_tabs() -> None:
    rows, mode, warnings = _owner_platform_rows("""Position
Player
RB
1

Jahmyr Gibbs
●
DET
1.8\t1.4\t1.0\t3.0

WR7
Ja'Marr Chase
2.6    3.2    3.0    1.6
""")
    assert mode == "RESPONSIVE_PLATFORM_CLIPBOARD"
    assert not warnings
    assert rows[0] == {"position": "RB1", "player": "Jahmyr Gibbs", "team": "DET", "consensus": "1.8", "sleeper": "1.4", "espn": "1.0", "fantasypros": "3.0"}
    assert rows[1]["position"] == "WR7"
    assert rows[1]["player"] == "Ja'Marr Chase"
    assert rows[1]["team"] == ""


def test_owner_platform_manual_alias_is_local_and_applies_on_next_preview(tmp_path) -> None:
    ranking = _ranking()
    paste = "| Position | Player | Consensus | Sleeper | ESPN | FantasyPros |\n| --- | --- | ---: | ---: | ---: | ---: |\n| RB1 | Owner Alias Runner | 12.0 | 11.0 | 13.0 | 12.5 |\n"
    before = preview_owner_paste_adp(ranking.profile, ranking, paste, "SLEEPER", _manual_assets(), root=tmp_path)
    assert before["parsedRows"][0]["unmatched_reason"] in {"POSSIBLE_ALIAS_REVIEW", "NOT_IN_ACTIVE_REDRAFT_BOARD"}
    approve_owner_platform_manual_match(tmp_path, ranking, _manual_assets(), pasted_name="Owner Alias Runner", pasted_position="RB", pasted_position_rank="1", selected_nwr_player_id="RB-0", source_snapshot_hash="snapshot")
    after = preview_owner_paste_adp(ranking.profile, ranking, paste, "SLEEPER", _manual_assets(), root=tmp_path)
    assert after["parsedRows"][0]["matched_nwr_player_id"] == "RB-0"
    assert after["parsedRows"][0]["match_source"] == "OWNER_APPROVED"
    assert (tmp_path / "adp_provider_cache" / "owner_platform_snapshot" / "manual_matches.json").is_file()
    clear_owner_platform_manual_match(tmp_path, pasted_name="Owner Alias Runner", pasted_position="RB")
    assert preview_owner_paste_adp(ranking.profile, ranking, paste, "SLEEPER", _manual_assets(), root=tmp_path)["parsedRows"][0]["match_status"] == "UNMATCHED"


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


def test_suggestions_exclude_a_position_already_at_its_league_maximum() -> None:
    """Directive: 'QB max = 2, owner QB count = 2 -> QB players remain
    visible/searchable in PLAYERS but QB is INELIGIBLE for actionable
    SUGGESTIONS.' Legality filter, not a ranking-formula change -- QB1 in
    _ranking() stays the top-ranked player overall, so this proves the
    exclusion is the position-max filter, not a coincidence of rank."""
    ranking = _ranking()
    adp = _empty_adp(ranking.profile)
    owner_slot = 9
    # Heuristic QB cap with no explicit roster_limits configured is
    # max(profile.roster.qb + 1, 2) = max(1 + 1, 2) = 2.
    state = {
        "owner_slot": owner_slot,
        "picks": [
            {"team_slot": owner_slot, "position": "QB", "player_id": "QB-0"},
            {"team_slot": owner_slot, "position": "QB", "player_id": "QB-1"},
        ],
    }
    result = _recommendations(
        ranking.profile, ranking, adp, state, current_pick=3, next_owner_pick=None
    )
    card_positions = {card["position"] for card in result["cards"]}
    assert "QB" not in card_positions, (
        f"QB card slipped through position-max filter: {result['cards']}"
    )
    # The actual top-ranked player overall in _ranking() is a QB -- it must
    # still exist in the underlying ranked universe and in allRows; only the
    # actionable SUGGESTIONS cards exclude it, per the directive.
    assert any(row.position == "QB" for row in ranking.rows)
    assert any(row["position"] == "QB" for row in result["allRows"])


def test_suggestions_respect_explicit_roster_limits_too() -> None:
    """Same rule via the explicit profile.draft.roster_limits path (not
    just the heuristic fallback)."""
    ranking = _ranking()
    draft = replace(ranking.profile.draft, roster_limits={"RB": 1})
    profile = replace(ranking.profile, draft=draft)
    ranking = replace(ranking, profile=profile)
    adp = _empty_adp(profile)
    owner_slot = 9
    state = {
        "owner_slot": owner_slot,
        "picks": [{"team_slot": owner_slot, "position": "RB", "player_id": "RB-0"}],
    }
    result = _recommendations(
        profile, ranking, adp, state, current_pick=2, next_owner_pick=None
    )
    card_positions = {card["position"] for card in result["cards"]}
    assert "RB" not in card_positions
    assert any(row["position"] == "RB" for row in result["allRows"])


def test_suggestions_are_unrestricted_when_no_position_is_at_its_maximum() -> None:
    """Sanity check the filter isn't overzealous: with an empty roster,
    every position is eligible and Best Available is still the top-ranked
    player overall."""
    ranking = _ranking()
    adp = _empty_adp(ranking.profile)
    state = {"owner_slot": 9, "picks": []}
    result = _recommendations(
        ranking.profile, ranking, adp, state, current_pick=1, next_owner_pick=None
    )
    assert result["cards"], "expected at least one suggestion card with an empty roster"
    best_available = result["cards"][0]
    assert best_available["playerId"] == ranking.rows[0].player_id


# --- Event-sourced pick correction: REPLACE PICK / CLEAR PICK / FILL GAP / UNDO ---
# Test/copy state only (tmp_path), per section 4's "Use copies/TEST state
# only." Never touches real KHA production evidence.


def _seeded_completed_room(tmp_path):
    """A full 150-pick completed mock draft, persisted to tmp_path so the
    correction functions (which load/save through the real root) can be
    exercised end to end, including reopen-persistence."""
    ranking = _ranking()
    adp = _empty_adp(ranking.profile)
    state = run_complete_mock(ranking.profile, ranking, _manual_assets(), adp, owner_slot=9)
    _save_room_state(tmp_path, state)
    return ranking, state


def _first_undrafted(ranking, state) -> str:
    pool = _asset_pool(ranking, _manual_assets())
    drafted = set(state["drafted"])
    return next(asset["player_id"] for asset in pool.values() if asset["player_id"] not in drafted)


def test_replace_pick_various_distances_leave_every_other_pick_byte_identical(tmp_path) -> None:
    ranking, seeded = _seeded_completed_room(tmp_path)
    total = len(seeded["picks"])
    # one pick ago, one round ago (10 picks), five rounds ago (50 picks), and
    # Round 1 (pick 1) corrected late in a fully completed 150-pick draft.
    targets = [total, total - 10, total - 50, 1]
    for pick_number in targets:
        before = load_room_state(tmp_path, ranking.profile, ranking, _manual_assets())
        old_entry = dict(before["picks"][pick_number - 1])
        untouched_snapshot = [
            dict(p) for i, p in enumerate(before["picks"]) if i != pick_number - 1
        ]
        replacement_id = _first_undrafted(ranking, before)
        updated = replace_pick(
            tmp_path, ranking.profile, ranking, _manual_assets(),
            pick_number=pick_number, player_id=replacement_id,
        )
        assert len(updated["picks"]) == total  # no renumbering, no growth/shrink
        changed = updated["picks"][pick_number - 1]
        assert changed["player_id"] == replacement_id
        assert changed["pick_number"] == pick_number
        assert changed["round"] == old_entry["round"]
        assert changed["team_slot"] == old_entry["team_slot"]
        # every other pick byte-for-byte identical except the one slot
        other_after = [dict(p) for i, p in enumerate(updated["picks"]) if i != pick_number - 1]
        assert other_after == untouched_snapshot
        # old player returned to the pool
        assert old_entry["player_id"] not in updated["drafted"]
        assert replacement_id in updated["drafted"]


def test_clear_then_fill_gap_round_1_late_in_a_completed_draft(tmp_path) -> None:
    ranking, seeded = _seeded_completed_room(tmp_path)
    total = len(seeded["picks"])
    pick_number = 1  # Round 1, corrected after all 150 picks exist
    original_player = seeded["picks"][0]["player_id"]

    cleared = clear_pick(
        tmp_path, ranking.profile, ranking, _manual_assets(), pick_number=pick_number
    )
    assert len(cleared["picks"]) == total
    slot = cleared["picks"][0]
    assert slot["status"] == "UNRESOLVED"
    assert slot["player_id"] == ""
    assert slot["pick_number"] == 1
    assert slot["round"] == seeded["picks"][0]["round"]
    assert slot["team_slot"] == seeded["picks"][0]["team_slot"]
    assert original_player not in cleared["drafted"]  # availability restored
    # a second, independent clear elsewhere must not collide via "" == ""
    cleared_two = clear_pick(tmp_path, ranking.profile, ranking, _manual_assets(), pick_number=2)
    assert len(cleared_two["drafted"]) == total - 2

    filled = fill_gap_pick(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        pick_number=pick_number, player_id=original_player,
    )
    assert filled["picks"][0]["player_id"] == original_player
    assert filled["picks"][0]["status"] == "RESOLVED"
    assert len(filled["picks"]) == total


def test_replace_pick_rejects_a_player_already_drafted_elsewhere(tmp_path) -> None:
    ranking, seeded = _seeded_completed_room(tmp_path)
    already_drafted_id = seeded["picks"][5]["player_id"]  # pick 6's player
    with pytest.raises(RedraftValidationError, match="already drafted at pick 6"):
        replace_pick(
            tmp_path, ranking.profile, ranking, _manual_assets(),
            pick_number=1, player_id=already_drafted_id,
        )


def test_fill_gap_requires_unresolved_and_replace_requires_resolved(tmp_path) -> None:
    ranking, seeded = _seeded_completed_room(tmp_path)
    replacement_id = _first_undrafted(ranking, seeded)
    with pytest.raises(RedraftValidationError, match="already resolved"):
        fill_gap_pick(
            tmp_path, ranking.profile, ranking, _manual_assets(),
            pick_number=1, player_id=replacement_id,
        )
    clear_pick(tmp_path, ranking.profile, ranking, _manual_assets(), pick_number=1)
    with pytest.raises(RedraftValidationError, match="unresolved"):
        replace_pick(
            tmp_path, ranking.profile, ranking, _manual_assets(),
            pick_number=1, player_id=replacement_id,
        )


def test_undo_pick_correction_reverses_only_the_latest_correction(tmp_path) -> None:
    ranking, seeded = _seeded_completed_room(tmp_path)
    original_pick_1 = dict(seeded["picks"][0])
    replacement_id = _first_undrafted(ranking, seeded)
    replace_pick(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        pick_number=1, player_id=replacement_id,
    )
    undone = undo_pick_correction(tmp_path, ranking.profile, ranking, _manual_assets())
    assert undone["picks"][0]["player_id"] == original_pick_1["player_id"]
    assert len(undone["picks"]) == len(seeded["picks"])
    with pytest.raises(RedraftValidationError, match="No pick correction"):
        undo_pick_correction(tmp_path, ranking.profile, ranking, _manual_assets())


def test_pick_correction_reopen_persistence(tmp_path) -> None:
    """A correction, closed and reopened, must persist -- not just live
    in-memory for the returned state object."""
    ranking, seeded = _seeded_completed_room(tmp_path)
    replacement_id = _first_undrafted(ranking, seeded)
    replace_pick(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        pick_number=3, player_id=replacement_id,
    )
    reopened = load_room_state(tmp_path, ranking.profile, ranking, _manual_assets())
    assert reopened["picks"][2]["player_id"] == replacement_id
    assert reopened["last_correction"]["pick_number"] == 3
    # and the undo survives a reopen too
    undo_pick_correction(tmp_path, ranking.profile, ranking, _manual_assets())
    reopened_again = load_room_state(tmp_path, ranking.profile, ranking, _manual_assets())
    assert reopened_again["picks"][2]["player_id"] == seeded["picks"][2]["player_id"]


def test_corrections_do_not_disturb_downstream_rosters_or_board_payload(tmp_path) -> None:
    ranking, seeded = _seeded_completed_room(tmp_path)
    adp = _empty_adp(ranking.profile)
    replacement_id = _first_undrafted(ranking, seeded)
    replace_pick(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        pick_number=4, player_id=replacement_id,
    )
    state = load_room_state(tmp_path, ranking.profile, ranking, _manual_assets())
    payload = build_draft_room_payload(ranking.profile, ranking, _manual_assets(), adp, state)
    assert payload["complete"] is True
    assert len(payload["boardCells"]) == len(seeded["picks"])
    clear_pick(tmp_path, ranking.profile, ranking, _manual_assets(), pick_number=5)
    state = load_room_state(tmp_path, ranking.profile, ranking, _manual_assets())
    payload = build_draft_room_payload(ranking.profile, ranking, _manual_assets(), adp, state)
    # cleared slot must not appear as a phantom roster entry anywhere
    for team in payload["teams"]:
        assert all(player["playerId"] for player in team["roster"])


def _sleeper_player(name: str, position: str) -> dict[str, str]:
    return {"full_name": name, "position": position}


def _live_room(tmp_path) -> tuple[RankingResult, dict]:
    ranking = _ranking()
    room = start_draft_room(
        tmp_path,
        ranking.profile,
        ranking,
        _manual_assets(),
        _empty_adp(ranking.profile),
        owner_slot=9,
        mode="LIVE_READ_ONLY",
    )
    assert room["picks"] == []
    return ranking, room


def test_sleeper_auto_sync_applies_sequential_picks_in_order(tmp_path) -> None:
    ranking, _ = _live_room(tmp_path)
    sleeper_picks = [
        {"pick_no": 1, "player_id": "s-1"},
        {"pick_no": 2, "player_id": "s-2"},
        {"pick_no": 3, "player_id": "s-3"},
    ]
    sleeper_players = {
        "s-1": _sleeper_player("QB 0", "QB"),
        "s-2": _sleeper_player("RB 0", "RB"),
        "s-3": _sleeper_player("WR 0", "WR"),
    }
    summary = sync_read_only_sleeper_picks(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        sleeper_picks=sleeper_picks, sleeper_players=sleeper_players,
    )
    assert [row["playerId"] for row in summary["applied"]] == ["QB-0", "RB-0", "WR-0"]
    assert summary["conflicts"] == []
    assert summary["nextExpectedPick"] == 4
    assert summary["boundedBatchHit"] is False
    reopened = load_room_state(tmp_path, ranking.profile, ranking, _manual_assets())
    assert [pick["player_id"] for pick in reopened["picks"]] == ["QB-0", "RB-0", "WR-0"]
    assert all(pick["actor"] == "SLEEPER_READ_ONLY" for pick in reopened["picks"])


def test_sleeper_auto_sync_stops_and_reports_out_of_order_conflict(tmp_path) -> None:
    ranking, _ = _live_room(tmp_path)
    # pick 3 is missing from Sleeper's own feed -- a gap must never be
    # silently skipped past.
    sleeper_picks = [
        {"pick_no": 1, "player_id": "s-1"},
        {"pick_no": 2, "player_id": "s-2"},
        {"pick_no": 4, "player_id": "s-4"},
    ]
    sleeper_players = {
        "s-1": _sleeper_player("QB 0", "QB"),
        "s-2": _sleeper_player("RB 0", "RB"),
        "s-4": _sleeper_player("TE 0", "TE"),
    }
    summary = sync_read_only_sleeper_picks(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        sleeper_picks=sleeper_picks, sleeper_players=sleeper_players,
    )
    assert [row["playerId"] for row in summary["applied"]] == ["QB-0", "RB-0"]
    assert len(summary["conflicts"]) == 1
    assert summary["conflicts"][0]["reason"] == "OUT_OF_ORDER"
    assert summary["conflicts"][0]["pickNumber"] == 4
    assert summary["nextExpectedPick"] == 3


def test_sleeper_auto_sync_reports_unknown_player_conflict(tmp_path) -> None:
    ranking, _ = _live_room(tmp_path)
    summary = sync_read_only_sleeper_picks(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        sleeper_picks=[{"pick_no": 1, "player_id": "s-ghost"}],
        sleeper_players={},
    )
    assert summary["applied"] == []
    assert summary["conflicts"][0]["reason"] == "UNKNOWN_SLEEPER_PLAYER"


def test_sleeper_auto_sync_reports_unresolved_local_identity_conflict(tmp_path) -> None:
    ranking, _ = _live_room(tmp_path)
    summary = sync_read_only_sleeper_picks(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        sleeper_picks=[{"pick_no": 1, "player_id": "s-1"}],
        sleeper_players={"s-1": _sleeper_player("Nobody Real", "QB")},
    )
    assert summary["applied"] == []
    assert summary["conflicts"][0]["reason"] == "UNRESOLVED_LOCAL_IDENTITY"


def test_sleeper_auto_sync_treats_a_locally_taken_identity_as_a_conflict(tmp_path) -> None:
    ranking, _ = _live_room(tmp_path)
    ingest_read_only_sleeper_pick(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        player_id="QB-0", pick_number=1,
    )
    # Sleeper reports a second pick that (per a hypothetically glitched
    # Sleeper player catalog) also resolves to the identity already taken
    # locally -- must be flagged, never silently re-applied or skipped.
    summary = sync_read_only_sleeper_picks(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        sleeper_picks=[{"pick_no": 2, "player_id": "s-dup"}],
        sleeper_players={"s-dup": _sleeper_player("QB 0", "QB")},
    )
    assert summary["applied"] == []
    assert summary["conflicts"][0]["reason"] == "UNRESOLVED_LOCAL_IDENTITY"
    assert summary["conflicts"][0]["pickNumber"] == 2


def test_sleeper_auto_sync_is_bounded_per_call_and_resumable(tmp_path) -> None:
    ranking, _ = _live_room(tmp_path)
    sleeper_picks = [{"pick_no": i + 1, "player_id": f"s-{i}"} for i in range(5)]
    positions = ["QB", "RB", "WR", "TE", "K"]
    sleeper_players = {
        f"s-{i}": _sleeper_player(f"{pos} {i}", pos) for i, pos in enumerate(positions)
    }
    first = sync_read_only_sleeper_picks(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        sleeper_picks=sleeper_picks, sleeper_players=sleeper_players, max_picks=2,
    )
    assert len(first["applied"]) == 2
    assert first["boundedBatchHit"] is True
    assert first["nextExpectedPick"] == 3
    second = sync_read_only_sleeper_picks(
        tmp_path, ranking.profile, ranking, _manual_assets(),
        sleeper_picks=sleeper_picks, sleeper_players=sleeper_players, max_picks=2,
    )
    assert len(second["applied"]) == 2
    assert second["nextExpectedPick"] == 5
    reopened = load_room_state(tmp_path, ranking.profile, ranking, _manual_assets())
    assert len(reopened["picks"]) == 4


def test_sleeper_auto_sync_requires_live_read_only_mode(tmp_path) -> None:
    ranking = _ranking()
    run_complete_mock(
        ranking.profile, ranking, _manual_assets(), _empty_adp(ranking.profile), owner_slot=9
    )
    start_draft_room(
        tmp_path, ranking.profile, ranking, _manual_assets(), _empty_adp(ranking.profile),
        owner_slot=9, mode="MOCK",
    )
    with pytest.raises(RedraftValidationError, match="Live Read-Only"):
        sync_read_only_sleeper_picks(
            tmp_path, ranking.profile, ranking, _manual_assets(),
            sleeper_picks=[], sleeper_players={},
        )
