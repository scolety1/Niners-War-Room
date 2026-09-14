import json
from pathlib import Path

from src.services.current_player_status_overrides_service import (
    OVERRIDES_RELATIVE_PATH,
    add_verified_status_override,
)
from src.services.player_availability_status_service import (
    PlayerAvailabilityStatus,
    compute_freshness_seconds,
    load_player_availability_statuses,
    player_availability_authority_health,
)


def _seeded_repo_root(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / OVERRIDES_RELATIVE_PATH.name).write_text(
        json.dumps({"schema_version": 1, "overrides": []}), encoding="utf-8"
    )
    return tmp_path


def test_empty_when_no_overrides_file_exists(tmp_path: Path):
    assert load_player_availability_statuses(tmp_path) == ()
    health = player_availability_authority_health(tmp_path)
    assert health["entryCount"] == 0
    assert health["automatedFeed"] is False


def test_season_out_maps_to_out_for_season_with_injury_designation(tmp_path: Path):
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-1",
        player_name="Test Player",
        kind="SEASON_OUT",
        reason="ACL tear, placed on IR.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
    )
    statuses = load_player_availability_statuses(tmp_path)
    assert len(statuses) == 1
    status = statuses[0]
    assert status.status_category == "OUT_FOR_SEASON"
    assert status.injury_designation == "OUT"
    assert status.administrative_exempt is False
    assert status.released is False
    assert status.source == "MANUAL_VERIFIED_OVERRIDE"


def test_administrative_exempt_is_not_relabeled_as_injury(tmp_path: Path):
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-2",
        player_name="Exempt Player",
        kind="ADMINISTRATIVE_EXEMPT",
        reason="Placed on Commissioner Exempt list.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
    )
    status = load_player_availability_statuses(root)[0]
    assert status.status_category == "ADMINISTRATIVE_EXEMPT"
    assert status.injury_designation is None
    assert status.administrative_exempt is True


def test_not_with_team_marks_released_not_injured(tmp_path: Path):
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-3",
        player_name="Released Player",
        kind="NOT_WITH_TEAM",
        reason="Released, unsigned.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
    )
    status = load_player_availability_statuses(root)[0]
    assert status.status_category == "NOT_WITH_TEAM"
    assert status.released is True
    assert status.injury_designation is None


def test_team_correction_carries_corrected_team_as_current_team(tmp_path: Path):
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-4",
        player_name="Traded Player",
        kind="TEAM_CORRECTION",
        reason="Traded.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
        corrected_team="SF",
    )
    status = load_player_availability_statuses(root)[0]
    assert status.status_category == "TEAM_CORRECTION"
    assert status.current_team == "SF"


def test_authority_health_discloses_no_automated_feed(tmp_path: Path):
    health = player_availability_authority_health(tmp_path)
    assert health["automatedFeed"] is False
    assert any("no automated" in issue.lower() for issue in health["issues"])


# --- Work Unit 4: normalized factual status schema (structure/defaults) ---


def test_new_factual_fields_default_to_none_unknown_not_guessed():
    """Gate 1: a field with no available source must render absent/unknown,
    never a guessed/healthy default. Constructing with only the ORIGINAL
    (pre-Work-Unit-4) required fields must leave every new field `None`."""
    status = PlayerAvailabilityStatus(
        player_id="p1",
        player_name="Test Player",
        status_category="OUT_FOR_SEASON",
        injury_designation="OUT",
        practice_state=None,
        ir_pup_nfi=None,
        suspension=False,
        administrative_exempt=False,
        released=False,
        current_team=None,
        reason="test",
        source="MANUAL_VERIFIED_OVERRIDE",
        source_as_of="2026-09-01",
        override_kind="SEASON_OUT",
    )
    assert status.game_status is None
    assert status.on_injured_reserve is None
    assert status.on_pup is None
    assert status.on_nfi is None
    assert status.active_inactive is None
    assert status.depth_chart_position is None
    assert status.depth_chart_context is None
    assert status.fetched_at is None
    assert status.freshness_seconds is None


def test_new_factual_fields_round_trip_through_to_dict():
    status = PlayerAvailabilityStatus(
        player_id="p1",
        player_name="Test Player",
        status_category="OUT_FOR_SEASON",
        injury_designation="OUT",
        practice_state="DNP",
        ir_pup_nfi="Injured Reserve",
        suspension=False,
        administrative_exempt=False,
        released=False,
        current_team="SF",
        reason="test",
        source="MANUAL_VERIFIED_OVERRIDE",
        source_as_of="2026-09-01",
        override_kind="SEASON_OUT",
        game_status="INACTIVE",
        on_injured_reserve=True,
        on_pup=False,
        on_nfi=False,
        active_inactive="INACTIVE",
        depth_chart_position="RB1",
        depth_chart_context="starter",
        fetched_at="2026-09-13T12:00:00+00:00",
        freshness_seconds=3600.0,
    )
    payload = status.to_dict()
    assert payload["gameStatus"] == "INACTIVE"
    assert payload["onInjuredReserve"] is True
    assert payload["onPup"] is False
    assert payload["onNfi"] is False
    assert payload["activeInactive"] == "INACTIVE"
    assert payload["depthChartPosition"] == "RB1"
    assert payload["depthChartContext"] == "starter"
    assert payload["fetchedAt"] == "2026-09-13T12:00:00+00:00"
    assert payload["freshnessSeconds"] == 3600.0


def test_real_manual_override_wrapper_leaves_all_new_fields_none(tmp_path: Path):
    """The ONLY real source wired up today (the manual override wrapper)
    must leave every Work-Unit-4 field unknown -- it has no automated
    game-status/IR-PUP-NFI-breakdown/depth-chart/fetch signal to offer.
    Proves this pass changed nothing about CURRENT production behavior."""
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-5",
        player_name="Wrapper Check Player",
        kind="SEASON_OUT",
        reason="ACL tear, placed on IR.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
    )
    status = load_player_availability_statuses(root)[0]
    for field in (
        status.game_status,
        status.on_injured_reserve,
        status.on_pup,
        status.on_nfi,
        status.active_inactive,
        status.depth_chart_position,
        status.depth_chart_context,
        status.fetched_at,
        status.freshness_seconds,
    ):
        assert field is None


# --- compute_freshness_seconds: pure function, known small examples ---


def test_compute_freshness_seconds_real_iso_timestamps():
    seconds = compute_freshness_seconds("2026-09-13T12:00:00+00:00", "2026-09-13T12:30:00+00:00")
    assert seconds == 1800.0


def test_compute_freshness_seconds_handles_z_suffix():
    seconds = compute_freshness_seconds("2026-09-13T12:00:00Z", "2026-09-13T13:00:00Z")
    assert seconds == 3600.0


def test_compute_freshness_seconds_none_when_source_as_of_missing():
    assert compute_freshness_seconds(None, "2026-09-13T12:00:00+00:00") is None


def test_compute_freshness_seconds_none_when_fetched_at_missing():
    assert compute_freshness_seconds("2026-09-13T12:00:00+00:00", None) is None


def test_compute_freshness_seconds_none_for_week_granularity_label_not_a_timestamp():
    """nflverse injuries' real `source_as_of` shape (`2026-REG-week1`) is
    honestly NOT a timestamp -- must return None, never a guess."""
    assert compute_freshness_seconds("2026-REG-week1", "2026-09-13T12:00:00+00:00") is None
