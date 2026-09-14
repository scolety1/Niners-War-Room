"""Tests for `live_player_intelligence_composition_v1_service.py` (Worker 4,
Work Unit 6). Covers the exact scenarios the directive named: newer-arrives-
after-older, manual-override-then-automated-arrives (override wins),
automated-then-manual-override-arrives (override still wins), conflicting
source fields, an unknown field staying unknown (never defaulting to a
guessed "healthy"), and a released/team-change state -- plus the structural
REJECT enforcement for Sleeper `injury_designation` and an architecture
guard proving this module is not wired into any production/consumer path.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.services.live_player_intelligence_composition_v1_service import (
    COMPOSABLE_FIELDS,
    PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE,
    PRECEDENCE_MANUAL_VERIFIED_OVERRIDE,
    PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
    REJECTED_SOURCE_FIELD_PAIRS,
    ComposedField,
    FieldObservation,
    compose_field,
    compose_player_availability,
    observations_from_manual_override,
    observations_from_nflverse_depth_chart_shadow,
    observations_from_nflverse_injury_shadow,
    observations_from_sleeper_shadow,
)
from src.services.live_player_intelligence_identity_mapping_v1_service import (
    CommonSourceRow,
    classify_rows,
)
from src.services.live_player_intelligence_shadow_v1_service import CanonicalPlayerRow, ShadowPlayerStatus
from src.services.player_availability_status_service import PlayerAvailabilityStatus

REPO_ROOT = Path(__file__).resolve().parents[1]


def _shadow(
    source,
    player_id="00-1000001",
    name="Test Player",
    position="WR",
    team="SF",
    injury_designation=None,
    practice_state=None,
    ir_pup_nfi=None,
    status_category=None,
    suspension=False,
    source_as_of=None,
    matched_canonical_player_id="canon-1",
) -> ShadowPlayerStatus:
    return ShadowPlayerStatus(
        source=source,
        source_player_id=player_id,
        player_name=name,
        position=position,
        team=team,
        status_category=status_category,
        injury_designation=injury_designation,
        practice_state=practice_state,
        ir_pup_nfi=ir_pup_nfi,
        suspension=suspension,
        source_as_of=source_as_of,
        matched_canonical_player_id=matched_canonical_player_id,
        match_method="GSIS_DIRECT",
    )


# ---------------------------------------------------------------------------
# compose_field -- the core precedence + freshness-monotonicity rules
# ---------------------------------------------------------------------------


def test_first_observation_is_always_accepted():
    obs = FieldObservation(
        field="injury_designation",
        value="Out",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_OFFICIAL_INJURY_REPORT",
        fetched_at="2026-09-13T10:00:00Z",
    )
    result = compose_field(None, obs)
    assert result.value == "Out"
    assert result.source == "NFLVERSE_OFFICIAL_INJURY_REPORT"


def test_newer_arrives_after_older_is_accepted():
    older = ComposedField(
        field="injury_designation",
        value="Questionable",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_OFFICIAL_INJURY_REPORT",
        source_as_of=None,
        fetched_at="2026-09-13T10:00:00Z",
    )
    newer_incoming = FieldObservation(
        field="injury_designation",
        value="Out",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_OFFICIAL_INJURY_REPORT",
        fetched_at="2026-09-13T14:00:00Z",
    )
    result = compose_field(older, newer_incoming)
    assert result.value == "Out"
    assert result.fetched_at == "2026-09-13T14:00:00Z"


def test_older_arrives_after_newer_is_rejected_freshness_monotonicity():
    """The directive's core requirement: an out-of-order-arriving OLDER
    record must never silently overwrite an already-composed NEWER one,
    even at the same precedence tier."""

    newer_already_composed = ComposedField(
        field="injury_designation",
        value="Out",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_OFFICIAL_INJURY_REPORT",
        source_as_of=None,
        fetched_at="2026-09-13T14:00:00Z",
    )
    older_arriving_late = FieldObservation(
        field="injury_designation",
        value="Questionable",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_OFFICIAL_INJURY_REPORT",
        fetched_at="2026-09-13T10:00:00Z",
    )
    result = compose_field(newer_already_composed, older_arriving_late)
    assert result.value == "Out"
    assert result.fetched_at == "2026-09-13T14:00:00Z"


def test_manual_override_then_automated_arrives_override_wins():
    manual = ComposedField(
        field="current_team",
        value="KC",
        precedence_tier=PRECEDENCE_MANUAL_VERIFIED_OVERRIDE,
        source="MANUAL_VERIFIED_OVERRIDE",
        source_as_of="2026-09-01",
        fetched_at="2026-09-01T00:00:00Z",
    )
    automated_incoming = FieldObservation(
        field="current_team",
        value="LAC",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
        fetched_at="2026-09-13T23:00:00Z",  # much newer, must still lose
    )
    result = compose_field(manual, automated_incoming)
    assert result.value == "KC"
    assert result.source == "MANUAL_VERIFIED_OVERRIDE"


def test_automated_then_manual_override_arrives_override_still_wins():
    automated = ComposedField(
        field="current_team",
        value="LAC",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
        source_as_of=None,
        fetched_at="2026-09-13T23:00:00Z",  # newer than the manual override below
    )
    manual_incoming = FieldObservation(
        field="current_team",
        value="KC",
        precedence_tier=PRECEDENCE_MANUAL_VERIFIED_OVERRIDE,
        source="MANUAL_VERIFIED_OVERRIDE",
        fetched_at="2026-09-01T00:00:00Z",  # older, must still win on precedence alone
    )
    result = compose_field(automated, manual_incoming)
    assert result.value == "KC"
    assert result.source == "MANUAL_VERIFIED_OVERRIDE"


def test_conflicting_source_fields_same_tier_resolved_by_freshness():
    nflverse_existing = ComposedField(
        field="injury_designation",
        value="Doubtful",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_OFFICIAL_INJURY_REPORT",
        source_as_of=None,
        fetched_at="2026-09-13T08:00:00Z",
    )
    conflicting_but_older = FieldObservation(
        field="injury_designation",
        value="Out",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_OFFICIAL_INJURY_REPORT",
        fetched_at="2026-09-13T06:00:00Z",
    )
    result = compose_field(nflverse_existing, conflicting_but_older)
    assert result.value == "Doubtful"  # the real, newer value survives the conflict


def test_conflicting_source_fields_no_timestamps_falls_back_to_preferred_source():
    # depth_chart_context prefers NFLVERSE_DEPTH_CHARTS; simulate a
    # hypothetical second tier-3 source with no documented preference and
    # no usable timestamp on either side.
    existing = ComposedField(
        field="depth_chart_context",
        value="WR3",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="SOME_OTHER_SHADOW_SOURCE",
        source_as_of=None,
        fetched_at=None,
    )
    incoming = FieldObservation(
        field="depth_chart_context",
        value="WR1",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_DEPTH_CHARTS",
        fetched_at=None,
    )
    result = compose_field(existing, incoming)
    assert result.value == "WR1"
    assert result.source == "NFLVERSE_DEPTH_CHARTS"


def test_unknown_field_stays_unknown_never_defaults_to_healthy():
    composed = compose_player_availability("canon-1", "Test Player", observations=())
    assert composed.get("injury_designation") is None
    assert composed.fields["injury_designation"].precedence_tier == 0
    assert composed.fields["injury_designation"].source == "NONE"
    # every declared composable field is present and explicitly unknown
    for field in COMPOSABLE_FIELDS:
        assert composed.fields[field].value is None


def test_released_and_team_change_state_composed_correctly():
    released_override = PlayerAvailabilityStatus(
        player_id="canon-2",
        player_name="Released Guy",
        status_category="NOT_WITH_TEAM",
        injury_designation=None,
        practice_state=None,
        ir_pup_nfi=None,
        suspension=False,
        administrative_exempt=False,
        released=True,
        current_team=None,
        reason="Waived by team, unsigned as of verification date",
        source="MANUAL_VERIFIED_OVERRIDE",
        source_as_of="2026-09-10",
        override_kind="NOT_WITH_TEAM",
    )
    observations = observations_from_manual_override(released_override)
    composed = compose_player_availability("canon-2", "Released Guy", observations)
    assert composed.get("released") is True
    assert composed.get("status_category") == "NOT_WITH_TEAM"
    assert composed.get("current_team") is None  # unknown, not fabricated
    assert composed.get("injury_designation") is None  # never mislabeled as an injury

    team_correction = PlayerAvailabilityStatus(
        player_id="canon-3",
        player_name="Traded Guy",
        status_category="TEAM_CORRECTION",
        injury_designation=None,
        practice_state=None,
        ir_pup_nfi=None,
        suspension=False,
        administrative_exempt=False,
        released=False,
        current_team="LV",
        reason="Trade corrected to new team",
        source="MANUAL_VERIFIED_OVERRIDE",
        source_as_of="2026-09-11",
        override_kind="TEAM_CORRECTION",
    )
    composed2 = compose_player_availability(
        "canon-3", "Traded Guy", observations_from_manual_override(team_correction)
    )
    assert composed2.get("current_team") == "LV"
    assert composed2.get("released") is False


def test_a_lower_precedence_source_arriving_first_still_loses_later():
    """Order of arrival does not change precedence outcomes: automated
    arrives first, override arrives later -- override wins regardless of
    which one was composed first."""

    composed = compose_player_availability("canon-4", "P", observations=())
    automated_obs = FieldObservation(
        field="current_team",
        value="LAC",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
        fetched_at="2026-09-01T00:00:00Z",
    )
    composed = compose_player_availability("canon-4", "P", (automated_obs,), existing=composed)
    assert composed.get("current_team") == "LAC"

    manual_obs = FieldObservation(
        field="current_team",
        value="KC",
        precedence_tier=PRECEDENCE_MANUAL_VERIFIED_OVERRIDE,
        source="MANUAL_VERIFIED_OVERRIDE",
        fetched_at="2026-08-01T00:00:00Z",  # older in wall-clock terms, still wins
    )
    composed = compose_player_availability("canon-4", "P", (manual_obs,), existing=composed)
    assert composed.get("current_team") == "KC"


# ---------------------------------------------------------------------------
# Rejected-field structural enforcement
# ---------------------------------------------------------------------------


def test_sleeper_shadow_builder_never_emits_injury_designation():
    records = (
        _shadow(
            "SLEEPER_PUBLIC_PLAYERS_CATALOG",
            injury_designation="Out",  # present on the raw record, must NOT be surfaced
            ir_pup_nfi="IR",
            status_category="Inactive",
            team="BAL",
        ),
    )
    observations = observations_from_sleeper_shadow(records, fetched_at="2026-09-14T03:00:00Z")
    fields_emitted = {obs.field for obs in observations}
    assert "injury_designation" not in fields_emitted
    assert "current_team" in fields_emitted
    assert "on_injured_reserve" in fields_emitted


def test_compose_field_defensively_rejects_sleeper_injury_designation_even_if_passed():
    bad_observation = FieldObservation(
        field="injury_designation",
        value="Out",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
        fetched_at="2026-09-14T03:00:00Z",
    )
    assert ("SLEEPER_PUBLIC_PLAYERS_CATALOG", "injury_designation") in REJECTED_SOURCE_FIELD_PAIRS
    result = compose_field(None, bad_observation)
    assert result.value is None
    assert result.source == "NONE"

    # And it must not clobber a real, already-composed nflverse value either.
    existing_nflverse = ComposedField(
        field="injury_designation",
        value="Questionable",
        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
        source="NFLVERSE_OFFICIAL_INJURY_REPORT",
        source_as_of=None,
        fetched_at="2026-09-14T02:00:00Z",
    )
    result2 = compose_field(existing_nflverse, bad_observation)
    assert result2.value == "Questionable"
    assert result2.source == "NFLVERSE_OFFICIAL_INJURY_REPORT"


def test_compose_player_availability_end_to_end_drops_rejected_sleeper_field():
    sleeper_records = (
        _shadow(
            "SLEEPER_PUBLIC_PLAYERS_CATALOG",
            injury_designation="Out",
            ir_pup_nfi=None,
            status_category="Active",
            team="ARI",
        ),
    )
    nflverse_records = (
        _shadow(
            "NFLVERSE_OFFICIAL_INJURY_REPORT",
            injury_designation="Questionable",
            practice_state="Limited Participation in Practice",
            team="ARI",
        ),
    )
    observations = observations_from_sleeper_shadow(
        sleeper_records, fetched_at="2026-09-14T03:00:00Z"
    ) + observations_from_nflverse_injury_shadow(nflverse_records, fetched_at="2026-09-14T02:00:00Z")
    composed = compose_player_availability("canon-1", "Test Player", observations)
    # The real nflverse SHADOW signal is present...
    assert composed.get("injury_designation") == "Questionable"
    # ...and Sleeper's REJECTED signal never overwrote it, even though the
    # Sleeper record in this test carries no injury_designation observation
    # at all (structural exclusion), and even if it had, the defensive
    # filter would still have caught it.
    assert composed.get("current_team") == "ARI"


# ---------------------------------------------------------------------------
# Builder adapters
# ---------------------------------------------------------------------------


def test_observations_from_manual_override_skips_none_fields():
    status = PlayerAvailabilityStatus(
        player_id="canon-5",
        player_name="Season Out Guy",
        status_category="OUT_FOR_SEASON",
        injury_designation="OUT",
        practice_state=None,
        ir_pup_nfi=None,
        suspension=False,
        administrative_exempt=False,
        released=False,
        current_team=None,
        reason="Season-ending ACL tear",
        source="MANUAL_VERIFIED_OVERRIDE",
        source_as_of="2026-09-05",
        override_kind="SEASON_OUT",
    )
    observations = observations_from_manual_override(status)
    fields_emitted = {obs.field for obs in observations}
    assert "injury_designation" in fields_emitted
    assert "practice_state" not in fields_emitted  # was None -- no fake observation
    assert "ir_pup_nfi" not in fields_emitted
    assert "current_team" not in fields_emitted
    assert "game_status" not in fields_emitted
    for obs in observations:
        assert obs.precedence_tier == PRECEDENCE_MANUAL_VERIFIED_OVERRIDE


def test_observations_from_nflverse_injury_shadow_only_matched_records():
    unmatched = _shadow(
        "NFLVERSE_OFFICIAL_INJURY_REPORT",
        injury_designation="Out",
        matched_canonical_player_id=None,
    )
    matched = _shadow(
        "NFLVERSE_OFFICIAL_INJURY_REPORT",
        injury_designation="Out",
        practice_state="Full Participation in Practice",
        matched_canonical_player_id="canon-6",
    )
    observations = observations_from_nflverse_injury_shadow(
        (unmatched, matched), fetched_at="2026-09-14T02:00:00Z"
    )
    assert all(obs.value != "" for obs in observations)
    assert len(observations) == 2  # only the matched record contributes
    fields_emitted = {obs.field for obs in observations}
    assert fields_emitted == {"injury_designation", "practice_state"}


def test_observations_from_nflverse_depth_chart_shadow_matches_by_index():
    canonical_pool = (CanonicalPlayerRow(player_id="00-0034381", player_name="Josh Sweat", position="LB", team="ARI"),)
    common_rows = (
        CommonSourceRow(
            source="NFLVERSE_DEPTH_CHARTS",
            source_row_id="00-0034381",
            player_name="Josh Sweat",
            position="LB",
            team="ARI",
            provider_id="00-0034381",
            position_in_scope=False,
            raw={"pos_abb": "LDE", "pos_rank": "1", "dt": "2026-09-13T12:42:08Z"},
        ),
    )
    classified = classify_rows(common_rows, canonical_pool)
    observations = observations_from_nflverse_depth_chart_shadow(
        common_rows, classified, fetched_at="2026-09-14T03:00:00Z"
    )
    values = {obs.field: obs.value for obs in observations}
    assert values.get("depth_chart_position") == "LDE"
    assert values.get("depth_chart_context") == "LDE1"
    for obs in observations:
        assert obs.source_as_of == "2026-09-13T12:42:08Z"


def test_observations_from_nflverse_depth_chart_shadow_rejects_length_mismatch():
    with pytest.raises(ValueError):
        observations_from_nflverse_depth_chart_shadow((), (object(),), fetched_at=None)  # type: ignore[arg-type]


def test_admitted_automated_factual_source_tier_is_reserved_but_unused():
    """No builder in this module emits an observation at
    PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE -- confirmed by grepping
    this module's own source for that name's usage: it must appear only in
    its own definition and in this reservation comment/docstring context,
    never as an argument passed to a real FieldObservation construction."""

    module_path = (
        REPO_ROOT / "src" / "services" / "live_player_intelligence_composition_v1_service.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    calls_using_tier2 = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if isinstance(kw.value, ast.Name) and kw.value.id == "PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE":
                    calls_using_tier2.append(node)
    assert calls_using_tier2 == []
    assert PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE == 2


# ---------------------------------------------------------------------------
# Architecture guard -- proves this module is still SHADOW-only
# ---------------------------------------------------------------------------


def test_not_imported_by_any_production_or_consumer_path():
    forbidden_importers = (
        REPO_ROOT / "src" / "application" / "desktop_facade.py",
        REPO_ROOT / "src" / "desktop_api" / "server.py",
        REPO_ROOT / "src" / "services" / "player_availability_status_service.py",
    )
    for path in forbidden_importers:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        assert "live_player_intelligence_composition_v1_service" not in content, (
            f"{path} must not import the shadow composition module yet (Work Unit 9 territory)"
        )
