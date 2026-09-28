import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.services.current_player_status_overrides_service import (
    OVERRIDES_RELATIVE_PATH,
    StatusOverride,
    StatusOverrideCorruptionError,
    StatusOverrideIntakeError,
    add_verified_status_override,
    apply_status_overrides_to_ranking,
    load_status_overrides,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)


def _row(player_id, name, position, team, value, projected, rank) -> RedraftRankingRow:
    return RedraftRankingRow(
        rank, 1, player_id, name, position, team, projected, 0, value, 0,
        "HIGH", 1, "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-08-08", False,
    )


def _ranking() -> RankingResult:
    rows = (
        _row("A", "Player A", "WR", "NE", 50.0, 200.0, 1),
        _row("B", "Player B", "WR", "SF", 40.0, 180.0, 2),
        _row("C", "Player C", "WR", "DAL", 30.0, 160.0, 3),
    )
    profile = LeagueProfile(
        "fixture", "Fixture", 2026, 10, RosterSettings(), ScoringSettings(),
        DraftContext(rounds=16),
    )
    return RankingResult(profile, rows, (), (), "2026-08-08T00:00:00Z", "fixture")


def test_load_status_overrides_reads_the_real_committed_file() -> None:
    overrides = load_status_overrides(".")
    kinds = {o.player_id: o.kind for o in overrides}
    assert kinds.get("00-0040130") == "SEASON_OUT"
    assert kinds.get("00-0038608") == "TEAM_CORRECTION"
    # RELEASE-BLOCKER ADDENDUM: Elijah Mitchell -- released, not currently
    # on any NFL roster (a real, distinct NOT_WITH_TEAM reason, never
    # mislabeled as an injury).
    assert kinds.get("00-0036567") == "NOT_WITH_TEAM"
    for override in overrides:
        assert override.sources, f"{override.player_id} has no cited source"


def test_not_with_team_override_zeros_value_same_as_season_out() -> None:
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="B", player_name="Player B", kind="NOT_WITH_TEAM",
            reason="released, unsigned", effective_date="2026-08-01",
            verified_at_utc="2026-09-07T00:00:00Z", sources=("https://example.test/source",),
        ),
    )
    corrected = apply_status_overrides_to_ranking(ranking, overrides)
    row = next(r for r in corrected.rows if r.player_id == "B")
    assert row.replacement_adjusted_value == 0.0
    assert row.player_name == "Player B"


def test_administrative_exempt_override_zeros_value_same_as_season_out() -> None:
    """NWR OVERNIGHT V3 (Lane 1, item 1.12): a real, evidenced taxonomy
    gap -- a player carrying a real, current, sourced roster-status code
    that is neither an injury nor a release (e.g. Commissioner Exempt)
    fit none of the pre-existing three kinds. This is a general kind,
    not scoped to any one player."""
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="C", player_name="Player C", kind="ADMINISTRATIVE_EXEMPT",
            reason="Commissioner Exempt list, still rostered but not practicing/eligible.",
            effective_date="2026-09-08", verified_at_utc="2026-09-08T21:54:00Z",
            sources=("https://example.test/source",),
        ),
    )
    corrected = apply_status_overrides_to_ranking(ranking, overrides)
    row = next(r for r in corrected.rows if r.player_id == "C")
    assert row.replacement_adjusted_value == 0.0
    # Never removed, original projection untouched, distinct reason preserved.
    assert row.player_name == "Player C"
    assert {r.player_id for r in corrected.rows} == {"A", "B", "C"}


def test_season_out_override_zeros_value_but_keeps_player_searchable() -> None:
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="B", player_name="Player B", kind="SEASON_OUT",
            reason="test", effective_date="2026-08-19", verified_at_utc="2026-09-07T00:00:00Z",
            sources=("https://example.test/source",),
        ),
    )
    corrected = apply_status_overrides_to_ranking(ranking, overrides)
    row = next(r for r in corrected.rows if r.player_id == "B")
    assert row.replacement_adjusted_value == 0.0
    # Never removed -- still present and still findable by search/name.
    assert row.player_name == "Player B"
    assert {r.player_id for r in corrected.rows} == {"A", "B", "C"}
    # Sinks to the bottom of the re-derived rank order (worst value now).
    assert row.overall_rank == 3


def test_team_correction_override_only_touches_team() -> None:
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="A", player_name="Player A", kind="TEAM_CORRECTION",
            corrected_team="HOU", reason="test", effective_date="2026-08-25",
            verified_at_utc="2026-09-07T00:00:00Z", sources=("https://example.test/source",),
        ),
    )
    corrected = apply_status_overrides_to_ranking(ranking, overrides)
    row = next(r for r in corrected.rows if r.player_id == "A")
    assert row.team == "HOU"
    # Value/rank untouched -- a team correction never changes valuation.
    assert row.replacement_adjusted_value == 50.0
    assert row.overall_rank == 1


def test_no_matching_override_leaves_ranking_byte_identical() -> None:
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="ZZZ-not-in-ranking", player_name="Nobody", kind="SEASON_OUT",
            reason="test", effective_date="2026-08-19", verified_at_utc="2026-09-07T00:00:00Z",
            sources=("https://example.test/source",),
        ),
    )
    assert apply_status_overrides_to_ranking(ranking, overrides) == ranking


def test_empty_overrides_is_a_true_no_op() -> None:
    ranking = _ranking()
    assert apply_status_overrides_to_ranking(ranking, ()) is ranking


# --- add_verified_status_override: the real intake contract (NWR
# post-draft overnight, section 13) -- always exercised against a
# disposable tmp_path copy of the config file, never the real committed
# one.


def _fixture_repo_root(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / OVERRIDES_RELATIVE_PATH.name).write_text(
        json.dumps({"schema_version": 1, "overrides": []}), encoding="utf-8"
    )
    return tmp_path


_VALID_KWARGS = dict(
    player_id="00-0099999",
    player_name="Test Player",
    kind="SEASON_OUT",
    reason="Real, specific, verifiable reason.",
    effective_date="2026-09-01",
    verified_at_utc="2026-09-08T00:00:00Z",
    sources=("https://example.test/real-source",),
)


def test_add_verified_status_override_accepts_a_real_cited_event(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    result = add_verified_status_override(root, **_VALID_KWARGS)
    assert result.player_id == "00-0099999"
    assert result.sources == ("https://example.test/real-source",)
    # Real write: load_status_overrides sees it back immediately.
    reloaded = load_status_overrides(root)
    assert any(o.player_id == "00-0099999" and o.kind == "SEASON_OUT" for o in reloaded)


def test_add_verified_status_override_accepts_administrative_exempt(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    kwargs = {**_VALID_KWARGS, "kind": "ADMINISTRATIVE_EXEMPT"}
    result = add_verified_status_override(root, **kwargs)
    assert result.kind == "ADMINISTRATIVE_EXEMPT"
    reloaded = load_status_overrides(root)
    assert any(o.player_id == "00-0099999" and o.kind == "ADMINISTRATIVE_EXEMPT" for o in reloaded)


def test_add_verified_status_override_rejects_an_uncited_event(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    kwargs = {**_VALID_KWARGS, "sources": ()}
    with pytest.raises(StatusOverrideIntakeError, match="cited source"):
        add_verified_status_override(root, **kwargs)
    # Refused, not silently dropped or partially written.
    assert load_status_overrides(root) == ()


def test_add_verified_status_override_rejects_an_invalid_kind(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    kwargs = {**_VALID_KWARGS, "kind": "RUMORED_INJURY"}
    with pytest.raises(StatusOverrideIntakeError, match="kind must be one of"):
        add_verified_status_override(root, **kwargs)


def test_add_verified_status_override_rejects_malformed_dates(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    kwargs = {**_VALID_KWARGS, "effective_date": "sometime last week"}
    with pytest.raises(StatusOverrideIntakeError, match="effective_date"):
        add_verified_status_override(root, **kwargs)


def test_add_verified_status_override_requires_corrected_team_for_team_correction(
    tmp_path: Path,
) -> None:
    root = _fixture_repo_root(tmp_path)
    kwargs = {**_VALID_KWARGS, "kind": "TEAM_CORRECTION", "corrected_team": ""}
    with pytest.raises(StatusOverrideIntakeError, match="TEAM_CORRECTION requires corrected_team"):
        add_verified_status_override(root, **kwargs)


def test_add_verified_status_override_rejects_corrected_team_on_non_team_correction(
    tmp_path: Path,
) -> None:
    root = _fixture_repo_root(tmp_path)
    kwargs = {**_VALID_KWARGS, "corrected_team": "HOU"}
    with pytest.raises(StatusOverrideIntakeError, match="only valid for TEAM_CORRECTION"):
        add_verified_status_override(root, **kwargs)


def test_add_verified_status_override_rejects_a_duplicate_player_id(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    add_verified_status_override(root, **_VALID_KWARGS)
    with pytest.raises(StatusOverrideIntakeError, match="already has an override"):
        add_verified_status_override(root, **_VALID_KWARGS)


def test_add_verified_status_override_team_correction_accepted(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    kwargs = {**_VALID_KWARGS, "kind": "TEAM_CORRECTION", "corrected_team": "HOU"}
    result = add_verified_status_override(root, **kwargs)
    assert result.corrected_team == "HOU"
    reloaded = load_status_overrides(root)
    assert next(o for o in reloaded if o.player_id == "00-0099999").corrected_team == "HOU"


# --- Full Trust Hardening V1 (Worker 3): missing-injury-becomes-healthy
# bug found+fixed. Before this pass, `load_status_overrides` caught a
# missing file and a genuinely CORRUPT/unparseable file with the exact
# same `(OSError, ValueError)` clause and silently returned `()` for both
# -- meaning a real SEASON_OUT/NOT_WITH_TEAM/ADMINISTRATIVE_EXEMPT
# override would silently vanish app-wide (recommendations, CPU picks,
# roster completion all treat the player as fully healthy/available again)
# the instant the file was even slightly malformed, with zero error
# surfaced anywhere. Fixed: a MISSING file still honestly returns `()`;
# an EXISTING-but-corrupt file now raises `StatusOverrideCorruptionError`
# instead of silently emptying out.


def test_missing_overrides_file_is_honestly_empty_not_an_error(tmp_path: Path) -> None:
    # A repo root with no overrides file at all (e.g. a fresh worktree/
    # fixture) is a real, legitimate "no overrides configured yet" -- must
    # NOT raise.
    assert load_status_overrides(tmp_path) == ()


def test_corrupt_overrides_file_fails_loudly_not_silently_empty(tmp_path: Path) -> None:
    # THE BUG, reproduced: before the fix, this returned `()` -- exactly
    # indistinguishable from "no injuries on file" to every live caller
    # (waivers, trade analysis, weekly lineup, bootstrap, ranking).
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / OVERRIDES_RELATIVE_PATH.name).write_text(
        '{"schema_version": 1, "overrides": [', encoding="utf-8"  # truncated/corrupt JSON
    )
    with pytest.raises(StatusOverrideCorruptionError):
        load_status_overrides(tmp_path)


def test_overrides_file_with_malformed_top_level_shape_fails_loudly(tmp_path: Path) -> None:
    # Valid JSON, but not the expected document shape (missing/wrong-typed
    # "overrides" field) -- also a real malformed document, not a
    # legitimate empty override set.
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / OVERRIDES_RELATIVE_PATH.name).write_text(
        json.dumps({"schema_version": 1}), encoding="utf-8"
    )
    with pytest.raises(StatusOverrideCorruptionError):
        load_status_overrides(tmp_path)


def test_add_verified_status_override_writes_atomically_via_temp_and_replace(
    tmp_path: Path,
) -> None:
    # Full Trust Hardening V1 (Worker 3): a direct `path.write_text(...)`
    # to the final path (pre-fix) risks leaving a truncated/corrupt file
    # behind if the process is interrupted mid-write -- which, combined
    # with the bug above, used to silently discard EVERY real, previously
    # -verified override on file. The fix writes to a `.tmp` sibling and
    # atomically replaces the real file -- proven here by confirming no
    # leftover `.tmp` file survives a real, successful write, and the real
    # file itself always parses as complete, valid JSON immediately after.
    root = _fixture_repo_root(tmp_path)
    real_path = root / OVERRIDES_RELATIVE_PATH
    add_verified_status_override(root, **_VALID_KWARGS)
    temp_path = real_path.with_suffix(real_path.suffix + ".tmp")
    assert not temp_path.exists()
    # The real file is complete, valid JSON with the new entry present --
    # never a half-written intermediate state.
    on_disk = json.loads(real_path.read_text(encoding="utf-8"))
    assert any(entry.get("player_id") == "00-0099999" for entry in on_disk["overrides"])
