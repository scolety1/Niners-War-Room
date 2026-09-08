from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    ProjectionPlayer,
    RedraftPersistenceError,
    RedraftValidationError,
    RosterSettings,
    ScoringSettings,
    active_profile,
    archive_profile,
    build_health_report,
    builtin_presets,
    create_profile,
    delete_profile,
    duplicate_profile,
    generate_rankings,
    install_projection_snapshot,
    list_profiles,
    load_draft_board,
    load_profile,
    load_projection_snapshot,
    mark_player_drafted,
    player_compare_rows,
    profile_store_errors,
    projection_snapshot_path,
    reconcile_sleeper_profile_identities,
    redraft_compare_pool_rows,
    restore_profile,
    save_profile,
    score_projection,
    score_projection_availability_adjusted,
    set_active_profile,
    undo_last_draft_pick,
)


def _profile(
    *,
    name: str = "Test League",
    teams: int = 10,
    reception: float = 0.0,
    te_premium: float = 0.0,
    qb: int = 1,
    rb: int = 2,
    wr: int = 2,
    te: int = 1,
    flex: int = 1,
    superflex: int = 0,
    bench: int = 4,
) -> LeagueProfile:
    return LeagueProfile(
        profile_id="test-profile",
        league_name=name,
        season=2026,
        team_count=teams,
        roster=RosterSettings(
            qb=qb,
            rb=rb,
            wr=wr,
            te=te,
            flex=flex,
            superflex=superflex,
            bench_size=bench,
        ),
        scoring=ScoringSettings(reception=reception, te_premium=te_premium),
        draft=DraftContext(rounds=16),
    )


def _projection_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(1, 41):
        rows.append(
            _row(
                f"qb-{index}",
                f"Quarterback {index:02d}",
                "QB",
                passing_yards=5200 - (index * 65),
                passing_tds=44 - (index * 0.55),
                interceptions=8 + (index * 0.15),
                rushing_yards=max(40, 750 - (index * 18)),
                rushing_tds=max(1, 8 - (index * 0.15)),
            )
        )
    for index in range(1, 81):
        receptions = max(5, 75 - index) if index % 2 == 0 else max(3, 35 - index / 3)
        rows.append(
            _row(
                f"rb-{index}",
                f"Running Back {index:02d}",
                "RB",
                rushing_yards=max(100, 1500 - (index * 15)),
                rushing_tds=max(1, 14 - (index * 0.13)),
                receptions=receptions,
                receiving_yards=receptions * 7.2,
                receiving_tds=max(0, 5 - (index * 0.06)),
            )
        )
    for index in range(1, 101):
        receptions = max(8, 115 - index)
        rows.append(
            _row(
                f"wr-{index}",
                f"Wide Receiver {index:03d}",
                "WR",
                receptions=receptions,
                receiving_yards=max(120, 1750 - (index * 15)),
                receiving_tds=max(1, 13 - (index * 0.10)),
            )
        )
    for index in range(1, 41):
        receptions = max(10, 100 - (index * 2))
        rows.append(
            _row(
                f"te-{index}",
                f"Tight End {index:02d}",
                "TE",
                receptions=receptions,
                receiving_yards=max(100, 1300 - (index * 25)),
                receiving_tds=max(1, 10 - (index * 0.18)),
            )
        )
    rows.append(
        _row(
            "rookie-elite",
            "Rookie Contributor",
            "WR",
            rookie="true",
            receptions=92,
            receiving_yards=1450,
            receiving_tds=10,
            projection_low=120,
            projection_high=320,
        )
    )
    rows.append(
        _row(
            "rookie-blocked",
            "Blocked Rookie",
            "WR",
            rookie="true",
            evidence_status="BLOCKED",
            receptions=120,
            receiving_yards=1900,
            receiving_tds=16,
        )
    )
    return rows


def _row(
    player_id: str,
    player_name: str,
    position: str,
    **values: object,
) -> dict[str, object]:
    row: dict[str, object] = {
        "player_id": player_id,
        "player_name": player_name,
        "position": position,
        "team": "TST",
        "season": 2026,
        "source_status": "GOVERNED",
        "evidence_status": "AVAILABLE",
        "source_as_of": "2026-08-08",
        "rookie": "false",
        "games": 17,
        "passing_yards": 0,
        "passing_tds": 0,
        "interceptions": 0,
        "rushing_yards": 0,
        "rushing_tds": 0,
        "receiving_yards": 0,
        "receptions": 0,
        "receiving_tds": 0,
        "passing_first_downs": 0,
        "rushing_first_downs": 0,
        "receiving_first_downs": 0,
        "return_yards": 0,
        "return_tds": 0,
        "fumbles_lost": 0,
        "projection_low": 0,
        "projection_high": 0,
        "availability_probability": 0.95,
    }
    row.update(values)
    return row


def _write_projection(path: Path, rows: list[dict[str, object]] | None = None) -> None:
    rows = rows or _projection_rows()
    columns = sorted({column for row in rows for column in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_approval(path: Path, source: Path, **overrides: object) -> None:
    receipt: dict[str, object] = {
        "schema_version": 1,
        "authority": "NWR_DATA_GOVERNANCE",
        "approval_status": "APPROVED_FOR_REDRAFT_V1",
        "season": 2026,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_id": "test-governed-projections-2026-v1",
        "approved_by": "independent-test-governance",
        "approved_at_utc": "2026-08-08T12:00:00+00:00",
        "valid_until": "2026-09-07",
    }
    receipt.update(overrides)
    path.write_text(json.dumps(receipt), encoding="utf-8")


@pytest.fixture()
def snapshot(tmp_path: Path):
    path = tmp_path / "projections.csv"
    _write_projection(path)
    result = load_projection_snapshot(path, season=2026)
    assert not result.errors
    return result


def _rank(result, player_id: str):
    return next(row for row in result.rows if row.player_id == player_id)


def _replacement(result, position: str):
    return next(row for row in result.replacement_levels if row.position == position)


def test_scoring_engine_applies_profile_rules_and_te_premium(snapshot) -> None:
    receiver = next(player for player in snapshot.players if player.player_id == "wr-2")
    tight_end = next(player for player in snapshot.players if player.player_id == "te-1")
    standard = ScoringSettings()
    ppr = ScoringSettings(reception=1.0)
    premium = ScoringSettings(reception=1.0, te_premium=0.5)
    assert score_projection(receiver, ppr) - score_projection(receiver, standard) == pytest.approx(
        receiver.stats["receptions"]
    )
    assert score_projection(tight_end, premium) - score_projection(tight_end, ppr) == pytest.approx(
        0.5 * tight_end.stats["receptions"]
    )


def test_scoring_engine_applies_all_supported_components_and_k_dst_override() -> None:
    player = ProjectionPlayer(
        player_id="complete",
        player_name="Complete Player",
        position="TE",
        team="TST",
        season=2026,
        source_status="GOVERNED",
        evidence_status="AVAILABLE",
        source_as_of="2026-08-08",
        stats={
            "passing_yards": 25,
            "passing_tds": 1,
            "interceptions": 1,
            "rushing_yards": 10,
            "rushing_tds": 1,
            "receiving_yards": 10,
            "receptions": 2,
            "receiving_tds": 1,
            "passing_first_downs": 1,
            "rushing_first_downs": 1,
            "receiving_first_downs": 1,
            "return_yards": 10,
            "return_tds": 1,
            "fumbles_lost": 1,
            "passing_300_games": 1,
            "rushing_100_games": 1,
            "receiving_100_games": 1,
        },
    )
    scoring = ScoringSettings(
        reception=1,
        passing_first_down=0.5,
        rushing_first_down=0.5,
        receiving_first_down=0.5,
        return_yards=0.1,
        te_premium=0.5,
        bonuses={
            "passing_300_game": 1,
            "rushing_100_game": 2,
            "receiving_100_game": 3,
        },
    )
    assert score_projection(player, scoring) == pytest.approx(32.5)
    kicker = replace(player, player_id="k", position="K", stats={"projected_points_override": 123})
    assert score_projection(kicker, scoring) == 123


def test_profile_create_edit_duplicate_archive_delete_and_active_isolation(tmp_path: Path) -> None:
    preset = builtin_presets()[0]
    created = create_profile(tmp_path, preset, league_name="Work League")
    second = create_profile(tmp_path, builtin_presets()[3], league_name="Friends League")
    assert len(list_profiles(tmp_path)) == 2
    set_active_profile(tmp_path, created.profile_id)
    assert active_profile(tmp_path) == created
    edited = save_profile(
        tmp_path,
        replace(created, team_count=14, league_name="Work League Edited"),
    )
    assert load_profile(tmp_path, created.profile_id).team_count == 14
    assert load_profile(tmp_path, second.profile_id).team_count == 12
    copied = duplicate_profile(tmp_path, edited.profile_id)
    assert copied.profile_id != edited.profile_id
    assert copied.team_count == edited.team_count
    archived = archive_profile(tmp_path, edited.profile_id)
    assert archived.archived
    assert active_profile(tmp_path) is None
    with pytest.raises(RedraftValidationError):
        delete_profile(tmp_path, copied.profile_id, confirmed=False)
    delete_profile(tmp_path, copied.profile_id, confirmed=True)
    assert {profile.profile_id for profile in list_profiles(tmp_path)} == {second.profile_id}


def test_receipt_backed_sleeper_profile_identity_migration_preserves_existing_settings(
    tmp_path: Path,
) -> None:
    legacy = create_profile(
        tmp_path,
        _profile(name="Fantasy Gamers", teams=10, reception=1.0),
        league_name="Fantasy Gamers",
    )
    receipt_path = tmp_path / "sleeper_imports" / f"{legacy.profile_id}.json"
    receipt_path.parent.mkdir()
    receipt_path.write_text(
        json.dumps(
            {
                "league": {
                    "league_id": "1312983576827920384",
                    "season": 2026,
                }
            }
        ),
        encoding="utf-8",
    )

    reconciled = reconcile_sleeper_profile_identities(tmp_path)

    assert reconciled[0].profile_id == legacy.profile_id
    assert reconciled[0].league_name == "Fantasy Gamers"
    assert reconciled[0].team_count == 10
    assert reconciled[0].scoring.reception == 1.0
    assert reconciled[0].provider == "sleeper"
    assert reconciled[0].provider_league_id == "1312983576827920384"


def test_malformed_profile_is_reported_without_hiding_healthy_profiles(tmp_path: Path) -> None:
    healthy = create_profile(tmp_path, builtin_presets()[0], league_name="Healthy")
    malformed = tmp_path / "profiles" / "broken.json"
    malformed.write_text('{"profile_id":', encoding="utf-8")
    assert [profile.profile_id for profile in list_profiles(tmp_path)] == [healthy.profile_id]
    assert profile_store_errors(tmp_path) == ("broken.json: unreadable or invalid profile state",)


def test_projection_install_is_separate_and_hash_verified(tmp_path: Path) -> None:
    source = tmp_path / "incoming.csv"
    approval = tmp_path / "approval.json"
    store = tmp_path / "redraft-store"
    _write_projection(source)
    _write_approval(approval, source)
    installed = install_projection_snapshot(store, 2026, source, approval)
    assert installed.source_path == projection_snapshot_path(store, 2026)
    assert installed.source_sha256
    assert installed.source_path.read_bytes() == source.read_bytes()
    assert installed.source_path.with_suffix(".manifest.json").is_file()
    assert installed.source_path.with_suffix(".approval.json").is_file()
    manifest_path = installed.source_path.with_suffix(".manifest.json")
    manifest_path.write_text("{}", encoding="utf-8")
    tampered = load_projection_snapshot(installed.source_path, season=2026, require_manifest=True)
    assert any("manifest mismatch" in error for error in tampered.errors)


def test_projection_install_requires_separate_bound_approval_receipt(tmp_path: Path) -> None:
    source = tmp_path / "incoming.csv"
    approval = tmp_path / "approval.json"
    _write_projection(source)
    with pytest.raises(RedraftValidationError, match="approval receipt is missing"):
        install_projection_snapshot(tmp_path / "store", 2026, source, tmp_path / "missing.json")
    _write_approval(approval, source, source_sha256="0" * 64)
    with pytest.raises(RedraftValidationError, match="does not bind"):
        install_projection_snapshot(tmp_path / "store", 2026, source, approval)


def test_review_only_stale_and_shallow_projection_evidence_fail_closed(tmp_path: Path) -> None:
    review_path = tmp_path / "review.csv"
    review_rows = _projection_rows()
    review_rows[0]["source_status"] = "REVIEW_ONLY"
    review_rows[1]["source_as_of"] = "2020-01-01"
    _write_projection(review_path, review_rows)
    review = load_projection_snapshot(review_path, season=2026)
    blocked_reasons = {row["reason"] for row in review.blocked_rows}
    assert any("not admitted" in reason for reason in blocked_reasons)
    assert any("stale" in reason for reason in blocked_reasons)
    aged_rows = _projection_rows()
    for row in aged_rows:
        row["source_as_of"] = "2026-06-01"
    aged_path = tmp_path / "aged.csv"
    _write_projection(aged_path, aged_rows)
    aged = load_projection_snapshot(aged_path, season=2026)
    assert any("30-day freshness window" in row["reason"] for row in aged.blocked_rows)
    shallow_path = tmp_path / "shallow.csv"
    _write_projection(shallow_path, [_row("only", "Only Player", "QB", passing_yards=100)])
    shallow = load_projection_snapshot(shallow_path, season=2026)
    assert any("minimum admitted depth" in error for error in shallow.errors)
    health = build_health_report(_profile(), shallow, None)
    assert not health.current_season_forecast_available
    assert health.status == "BLOCKED_CURRENT_SEASON_EVIDENCE"


def test_page_open_read_functions_create_no_state(tmp_path: Path) -> None:
    root = tmp_path / "redraft-store"
    assert list_profiles(root) == ()
    assert active_profile(root) is None
    missing = load_projection_snapshot(projection_snapshot_path(root, 2026), season=2026)
    assert missing.errors
    assert not root.exists()


def test_rankings_are_deterministic_and_block_missing_evidence(snapshot) -> None:
    profile = _profile()
    first = generate_rankings(profile, snapshot)
    second = generate_rankings(profile, snapshot)
    assert first.rows == second.rows
    assert first.replacement_levels == second.replacement_levels
    assert all(row.player_id != "rookie-blocked" for row in first.rows)
    assert any(row["player_id"] == "rookie-blocked" for row in first.blocked_rows)
    rookie = _rank(first, "rookie-elite")
    assert rookie.rookie
    assert rookie.confidence == "LOW"


def test_tiers_are_deep_bounded_and_position_specific(snapshot) -> None:
    ranking = generate_rankings(_profile(), snapshot)
    overall = Counter(row.tier for row in ranking.rows)
    assert len(overall) >= 10
    assert max(overall.values()) <= 24
    assert all(row.overall_tier_label.startswith(f"Tier {row.tier}") for row in ranking.rows)
    for position in ("QB", "RB", "WR", "TE"):
        rows = [row for row in ranking.rows if row.position == position]
        tiers = Counter(row.position_tier for row in rows)
        assert len(tiers) >= 2
        assert max(tiers.values()) <= 14
        assert all(row.position_tier_label.startswith(f"{position} Tier ") for row in rows)


def test_kdst_roster_slots_keep_kdst_out_of_nwr_math_without_blocking_the_board(
    snapshot,
) -> None:
    """NWR LAST PRE-DRAFT BLOCKER CLOSURE (section 1, "remove the owner
    Practical Mode footgun"): this used to require `practical_mode=True`
    to avoid a blocked ranking -- a real, confirmed footgun, since K/DST
    are never part of the ranked universe in ANY mode. K/DST roster slots
    now work unconditionally; `practical_mode` itself is untouched and
    keeps its own separate meaning elsewhere (gating the standalone
    Practical Mock QA simulator)."""
    exact = replace(_profile(), roster=replace(_profile().roster, k=1, dst=1))
    ranking = generate_rankings(exact, snapshot)
    assert not ranking.errors
    assert ranking.ready
    assert {row.position for row in ranking.rows} == {"QB", "RB", "WR", "TE"}
    assert "manual and unmodeled" in " ".join(
        build_health_report(exact, snapshot, ranking).messages
    )
    # practical_mode remains a real, independent flag -- explicitly
    # enabling it changes nothing about whether K/DST rostering succeeds.
    practical = replace(exact, practical_mode=True)
    practical_ranking = generate_rankings(practical, snapshot)
    assert not practical_ranking.errors
    assert practical_ranking.ready


def test_superflex_materially_increases_qb_value_and_rank(snapshot) -> None:
    one_qb = generate_rankings(_profile(superflex=0), snapshot)
    superflex = generate_rankings(_profile(superflex=1), snapshot)
    qb = "qb-10"
    assert (
        _rank(superflex, qb).replacement_adjusted_value
        > _rank(one_qb, qb).replacement_adjusted_value + 40
    )
    assert _rank(superflex, qb).overall_rank < _rank(one_qb, qb).overall_rank
    assert (
        _replacement(superflex, "QB").replacement_points
        < _replacement(one_qb, "QB").replacement_points
    )


def test_ppr_changes_pass_catcher_relative_to_rusher(snapshot) -> None:
    standard = generate_rankings(_profile(reception=0.0), snapshot)
    ppr = generate_rankings(_profile(reception=1.0), snapshot)
    pass_catcher = "rb-2"
    rusher = "rb-1"
    standard_gap = (
        _rank(standard, pass_catcher).projected_points - _rank(standard, rusher).projected_points
    )
    ppr_gap = _rank(ppr, pass_catcher).projected_points - _rank(ppr, rusher).projected_points
    assert ppr_gap > standard_gap + 30


def test_three_wr_and_extra_flex_raise_wr_depth_value(snapshot) -> None:
    two_wr = generate_rankings(_profile(wr=2, flex=0), snapshot)
    three_wr = generate_rankings(_profile(wr=3, flex=0), snapshot)
    extra_flex = generate_rankings(_profile(wr=2, flex=2), snapshot)
    assert (
        _replacement(three_wr, "WR").replacement_points
        < _replacement(two_wr, "WR").replacement_points
    )
    assert (
        _rank(three_wr, "wr-1").replacement_adjusted_value
        > _rank(two_wr, "wr-1").replacement_adjusted_value
    )
    assert (
        _replacement(extra_flex, "WR").replacement_points
        <= _replacement(two_wr, "WR").replacement_points
    )


def test_fourteen_teams_increases_scarcity(snapshot) -> None:
    ten = generate_rankings(_profile(teams=10), snapshot)
    fourteen = generate_rankings(_profile(teams=14), snapshot)
    assert (
        _replacement(fourteen, "WR").replacement_points < _replacement(ten, "WR").replacement_points
    )
    assert (
        _rank(fourteen, "wr-1").replacement_adjusted_value
        > _rank(ten, "wr-1").replacement_adjusted_value
    )


def test_te_premium_changes_te_value(snapshot) -> None:
    ppr = generate_rankings(_profile(reception=1.0), snapshot)
    premium = generate_rankings(_profile(reception=1.0, te_premium=0.75), snapshot)
    assert _rank(premium, "te-1").projected_points > _rank(ppr, "te-1").projected_points
    assert _rank(premium, "te-1").overall_rank < _rank(ppr, "te-1").overall_rank


def test_profile_specific_draft_boards_are_isolated(tmp_path: Path) -> None:
    first = create_profile(tmp_path, builtin_presets()[0], league_name="A")
    second = create_profile(tmp_path, builtin_presets()[1], league_name="B")
    mark_player_drafted(tmp_path, first.profile_id, "wr-1", drafted=True)
    assert load_draft_board(tmp_path, first.profile_id)["drafted"] == ["wr-1"]
    assert load_draft_board(tmp_path, second.profile_id)["drafted"] == []
    mark_player_drafted(tmp_path, first.profile_id, "wr-1", drafted=False)
    assert load_draft_board(tmp_path, first.profile_id)["drafted"] == []


def test_archived_profile_can_be_restored_with_its_draft_state(tmp_path: Path) -> None:
    profile = create_profile(tmp_path, builtin_presets()[0], league_name="Archive Restore")
    mark_player_drafted(tmp_path, profile.profile_id, "wr-1", drafted=True)
    archive_profile(tmp_path, profile.profile_id)
    restored = restore_profile(tmp_path, profile.profile_id)
    assert restored.archived is False
    assert load_draft_board(tmp_path, profile.profile_id)["drafted"] == ["wr-1"]
    with pytest.raises(RedraftValidationError):
        restore_profile(tmp_path, profile.profile_id)


def test_draft_board_preserves_pick_order_and_recovers_latest_backup(tmp_path: Path) -> None:
    profile = create_profile(tmp_path, builtin_presets()[0], league_name="Recovery")
    mark_player_drafted(tmp_path, profile.profile_id, "wr-2", drafted=True)
    mark_player_drafted(tmp_path, profile.profile_id, "wr-1", drafted=True)
    board_path = tmp_path / "draft_boards" / f"{profile.profile_id}.json"
    assert load_draft_board(tmp_path, profile.profile_id)["drafted"] == ["wr-2", "wr-1"]
    board_path.write_text('{"drafted": [', encoding="utf-8")
    recovered = load_draft_board(tmp_path, profile.profile_id)
    assert recovered["drafted"] == ["wr-2", "wr-1"]
    assert recovered["recovered_from_backup"] is True


def test_undo_last_pick_persists_exact_new_latest_state(tmp_path: Path) -> None:
    profile = create_profile(tmp_path, builtin_presets()[0], league_name="Undo")
    mark_player_drafted(tmp_path, profile.profile_id, "wr-2", drafted=True)
    mark_player_drafted(tmp_path, profile.profile_id, "wr-1", drafted=True)
    assert undo_last_draft_pick(tmp_path, profile.profile_id)["drafted"] == ["wr-2"]
    board_path = tmp_path / "draft_boards" / f"{profile.profile_id}.json"
    board_path.write_text("truncated", encoding="utf-8")
    assert load_draft_board(tmp_path, profile.profile_id)["drafted"] == ["wr-2"]


def test_draft_board_corruption_without_backup_is_bounded(tmp_path: Path) -> None:
    profile = create_profile(tmp_path, builtin_presets()[0], league_name="Bounded Failure")
    board_path = tmp_path / "draft_boards" / f"{profile.profile_id}.json"
    board_path.parent.mkdir(parents=True)
    board_path.write_text('{"drafted": [', encoding="utf-8")
    with pytest.raises(RedraftPersistenceError, match="no valid profile backup"):
        load_draft_board(tmp_path, profile.profile_id)


def test_player_compare_is_explicitly_redraft_and_profile_specific(snapshot) -> None:
    profile = _profile(name="Work League", reception=1.0)
    result = generate_rankings(profile, snapshot)
    rows = player_compare_rows(
        result,
        [
            {"player_id": "wr-1", "player": "Wide Receiver 001", "position": "WR"},
            {"player_id": "missing", "player": "Unknown", "position": "WR"},
        ],
    )
    assert rows[0]["League Profile"] == "Work League"
    assert rows[0]["Redraft Status"] == "REDRAFT V1 - REVIEW"
    assert rows[1]["Redraft Status"] == "NOT_ENOUGH_INFORMATION"
    wrong_id_same_name = player_compare_rows(
        result,
        [{"player_id": "wrong", "player": "Wide Receiver 001", "position": "WR"}],
    )
    assert wrong_id_same_name[0]["Redraft Status"] == "NOT_ENOUGH_INFORMATION"
    assert "exact stable player_id" in wrong_id_same_name[0]["Blocking / Missing Evidence"]
    blocked_conflict = player_compare_rows(
        result,
        [{"player_id": "00-0041081", "player": "Max Bredeson", "position": "RB"}],
    )
    assert blocked_conflict[0]["Redraft Status"] == "NOT_ENOUGH_INFORMATION"


def test_redraft_compare_pool_exposes_every_ranked_exact_id(snapshot) -> None:
    result = generate_rankings(_profile(), snapshot)
    pool = redraft_compare_pool_rows(result)
    assert len(pool) == len(result.rows)
    assert {row["player_id"] for row in pool} == {row.player_id for row in result.rows}
    assert {row["Redraft Status"] for row in player_compare_rows(result, pool)} == {
        "REDRAFT V1 - REVIEW"
    }


def test_profile_roster_limits_are_normalized_on_save(tmp_path: Path) -> None:
    created = create_profile(tmp_path, builtin_presets()[0], league_name="Limits")
    updated = save_profile(
        tmp_path,
        replace(created, draft=replace(created.draft, roster_limits={"qb": 2, "wr": 6})),
    )
    assert updated.draft.roster_limits == {"QB": 2, "WR": 6}


def test_health_distinguishes_optional_blocked_rows_from_total_failure(snapshot) -> None:
    profile = _profile()
    ranking = generate_rankings(profile, snapshot)
    health = build_health_report(profile, snapshot, ranking)
    assert health.status == "READY_WITH_BLOCKED_PLAYERS"
    assert health.ranked_players > 200
    assert health.blocked_players == 1
    missing = load_projection_snapshot(Path("does-not-exist.csv"), season=2026)
    blocked = build_health_report(profile, missing, None)
    assert blocked.status == "BLOCKED_CURRENT_SEASON_EVIDENCE"


def test_profile_validation_rejects_unsupported_bonus() -> None:
    profile = replace(
        _profile(),
        scoring=replace(ScoringSettings(), bonuses={"touchdown_80_yards": 3.0}),
    )
    with pytest.raises(RedraftValidationError):
        generate_rankings(
            profile,
            load_projection_snapshot(Path("missing.csv"), season=2026),
        )


# NWR post-draft overnight (phase 6): score_projection_availability_adjusted
# is a documented, tested, NOT-adopted challenger -- see its own docstring
# for the real double-counting finding that disqualified it as written.
# Constructed directly (no CSV/freshness fixture) so this stays independent
# of the unrelated, environmental source_as_of date-cliff affecting this
# file's other fixtures.
def _projection_player(**overrides: object) -> ProjectionPlayer:
    base = dict(
        player_id="P1", player_name="Test Player", position="RB", team="TST",
        season=2026, source_status="GOVERNED", evidence_status="ADMITTED_CURRENT_SEASON",
        stats={"rushing_yards": 1000.0, "rushing_tds": 8.0},
    )
    base.update(overrides)
    return ProjectionPlayer(**base)  # type: ignore[arg-type]


def test_availability_adjusted_scorer_is_a_no_op_when_fully_available() -> None:
    player = _projection_player(stats={"rushing_yards": 1000.0, "availability_probability": 1.0})
    scoring = ScoringSettings()
    assert score_projection_availability_adjusted(player, scoring) == score_projection(player, scoring)


def test_availability_adjusted_scorer_is_a_no_op_when_availability_missing() -> None:
    player = _projection_player(stats={"rushing_yards": 1000.0})
    scoring = ScoringSettings()
    assert score_projection_availability_adjusted(player, scoring) == score_projection(player, scoring)


def test_availability_adjusted_scorer_discounts_reduced_availability() -> None:
    player = _projection_player(stats={"rushing_yards": 1000.0, "availability_probability": 0.8824})
    scoring = ScoringSettings()
    base = score_projection(player, scoring)
    adjusted = score_projection_availability_adjusted(player, scoring)
    assert adjusted == round(base * 0.8824, 4)
    assert adjusted < base


def test_availability_adjusted_scorer_never_touches_kdst_governed_override() -> None:
    """K/DST use a flat governed override, not a decomposed stat line --
    the challenger must never apply a second discount on top of it."""
    player = _projection_player(
        position="K", stats={"projected_points_override": 120.0, "availability_probability": 0.5},
    )
    scoring = ScoringSettings()
    assert score_projection_availability_adjusted(player, scoring) == score_projection(player, scoring) == 120.0


def test_generate_rankings_scorer_parameter_defaults_to_byte_identical_behavior(snapshot) -> None:
    """The new optional `scorer` parameter on generate_rankings must be a
    pure additive no-op for every existing caller that doesn't pass it."""
    profile = _profile()
    without_param = generate_rankings(profile, snapshot)
    with_default = generate_rankings(profile, snapshot, scorer=score_projection)
    assert without_param.rows == with_default.rows
