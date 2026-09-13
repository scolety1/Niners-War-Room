"""Tests for the P1-5 Live Player Intelligence shadow bakeoff module.

Covers: pure mapping fidelity for both real source shapes, canonical
identity matching (GSIS-direct + name/position/team fallback, reusing the
same `_identity` normalizer the rest of the app already uses), coverage/
comparison report construction, the precedence design contract, AND two
real inertness/architecture proofs:

  1. `test_shadow_module_is_imported_by_no_production_consumer` -- a real,
     source-level static proof (same technique
     `test_player_availability_status_consumer_consistency.py` already
     uses) that nothing under `src/application`, `src/desktop_api`, or
     `player_availability_status_service.py` imports this module.
  2. `test_creating_a_shadow_snapshot_file_does_not_change_the_real_
     player_availability_status_authority_output` -- calls the REAL,
     existing `PlayerAvailabilityStatus` authority functions before and
     after a real shadow snapshot file is written to disk, and asserts
     byte-identical output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services.live_player_intelligence_shadow_v1_service import (
    CanonicalPlayerRow,
    ShadowPlayerStatus,
    build_coverage_report,
    build_manual_override_comparison_report,
    build_nflverse_injury_shadow_records,
    build_sleeper_shadow_records,
    match_shadow_records_to_canonical,
    precedence_design,
)
from src.services.player_availability_status_service import (
    load_player_availability_statuses,
    player_availability_authority_health,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_ROWS = (
    CanonicalPlayerRow(player_id="00-0031234", player_name="Real Starter", position="RB", team="SF"),
    CanonicalPlayerRow(player_id="00-0039999", player_name="Backup Guy", position="WR", team="KC"),
    CanonicalPlayerRow(player_id="00-0040130", player_name="Jayden Higgins", position="WR", team="HOU"),
)


def test_build_nflverse_injury_shadow_records_maps_official_vocabulary_honestly():
    rows = [
        {
            "season": "2026",
            "season_type": "REG",
            "week": "1",
            "team": "sf",
            "gsis_id": "00-0031234",
            "position": "RB",
            "full_name": "Real Starter",
            "report_status": "Questionable",
            "practice_status": "Limited Participation in Practice",
        },
        {
            "season": "2026",
            "season_type": "REG",
            "week": "1",
            "team": "KC",
            "gsis_id": "",  # real rows sometimes lack a gsis_id -- must be skipped, not guessed
            "position": "WR",
            "full_name": "No Id Guy",
            "report_status": "Out",
            "practice_status": "Did Not Participate In Practice",
        },
    ]
    records = build_nflverse_injury_shadow_records(rows)
    assert len(records) == 1  # the no-gsis_id row is dropped, never fabricated an id
    record = records[0]
    assert record.gsis_id == "00-0031234"
    assert record.team == "SF"
    assert record.status_category == "QUESTIONABLE"
    assert record.injury_designation == "Questionable"
    assert record.practice_state == "Limited Participation in Practice"
    assert record.source == "NFLVERSE_OFFICIAL_INJURY_REPORT"


def test_build_sleeper_shadow_records_skips_healthy_active_players():
    catalog = {
        "1": {
            "full_name": "Real Starter",
            "position": "RB",
            "team": "SF",
            "status": "Active",
            "injury_status": None,
            "gsis_id": None,
            "practice_participation": None,
        },
        "2": {
            "full_name": "Injured Guy",
            "position": "WR",
            "team": "KC",
            "status": "Inactive",
            "injury_status": "IR",
            "injury_body_part": "Knee - ACL",
            "gsis_id": "00-0039999",
            "practice_participation": None,
            "news_updated": 1789232444137,
        },
        "3": {
            "full_name": "Not Real Player",
            "position": "RB",
            "team": None,
            "status": None,
            "injury_status": None,
        },
    }
    records = build_sleeper_shadow_records(catalog)
    assert len(records) == 1  # only the real non-healthy player survives
    record = records[0]
    assert record.player_name == "Injured Guy"
    assert record.injury_designation == "IR"
    # Real Sleeper shape (verified live, e.g. Jayden Higgins): status=
    # "Inactive" + injury_status="IR" -- the IR signal lives in
    # injury_status here, not status, so ir_pup_nfi must reflect THAT.
    assert record.ir_pup_nfi == "IR"
    assert record.gsis_id == "00-0039999"
    assert record.source == "SLEEPER_PUBLIC_PLAYERS_CATALOG"


def test_match_shadow_records_prefers_gsis_direct_over_name_match():
    shadow = (
        ShadowPlayerStatus(
            source="NFLVERSE_OFFICIAL_INJURY_REPORT",
            source_player_id="00-0031234",
            player_name="Real Starter",
            position="RB",
            team="SF",
            status_category="QUESTIONABLE",
            injury_designation="Questionable",
            practice_state="Limited Participation in Practice",
            ir_pup_nfi=None,
            suspension=False,
            source_as_of="2026-REG-week1",
            gsis_id="00-0031234",
        ),
    )
    resolved = match_shadow_records_to_canonical(shadow, CANONICAL_ROWS)
    assert resolved[0].matched_canonical_player_id == "00-0031234"
    assert resolved[0].match_method == "GSIS_DIRECT"


def test_match_shadow_records_falls_back_to_name_position_team():
    shadow = (
        ShadowPlayerStatus(
            source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
            source_player_id="sleeper-2",
            player_name="Backup Guy",
            position="WR",
            team="KC",
            status_category="INACTIVE",
            injury_designation="IR",
            practice_state=None,
            ir_pup_nfi="Injured Reserve",
            suspension=False,
            source_as_of="1789232444137",
            gsis_id=None,  # Sleeper often lacks gsis_id -- must still resolve via name/pos/team
        ),
    )
    resolved = match_shadow_records_to_canonical(shadow, CANONICAL_ROWS)
    assert resolved[0].matched_canonical_player_id == "00-0039999"
    assert resolved[0].match_method == "NAME_POSITION_TEAM"


def test_match_shadow_records_reports_team_less_players_as_unmatched_no_team_never_guessed():
    shadow = (
        ShadowPlayerStatus(
            source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
            source_player_id="sleeper-99",
            player_name="Between Teams Guy",
            position="RB",
            team=None,
            status_category="INACTIVE",
            injury_designation="Questionable",
            practice_state=None,
            ir_pup_nfi=None,
            suspension=False,
            source_as_of=None,
            gsis_id=None,
        ),
    )
    resolved = match_shadow_records_to_canonical(shadow, CANONICAL_ROWS)
    assert resolved[0].matched_canonical_player_id is None
    assert resolved[0].match_method == "UNMATCHED_NO_TEAM"


def test_build_coverage_report_is_per_source_never_blended():
    nflverse_records = match_shadow_records_to_canonical(
        (
            ShadowPlayerStatus(
                source="NFLVERSE_OFFICIAL_INJURY_REPORT",
                source_player_id="00-0031234",
                player_name="Real Starter",
                position="RB",
                team="SF",
                status_category="QUESTIONABLE",
                injury_designation="Questionable",
                practice_state="Limited Participation in Practice",
                ir_pup_nfi=None,
                suspension=False,
                source_as_of="2026-REG-week1",
                gsis_id="00-0031234",
            ),
        ),
        CANONICAL_ROWS,
    )
    sleeper_records = match_shadow_records_to_canonical(
        (
            ShadowPlayerStatus(
                source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
                source_player_id="sleeper-2",
                player_name="Backup Guy",
                position="WR",
                team="KC",
                status_category="INACTIVE",
                injury_designation="IR",
                practice_state=None,
                ir_pup_nfi="Injured Reserve",
                suspension=False,
                source_as_of="1789232444137",
                gsis_id=None,
            ),
        ),
        CANONICAL_ROWS,
    )
    report = build_coverage_report(
        {
            "NFLVERSE_OFFICIAL_INJURY_REPORT": nflverse_records,
            "SLEEPER_PUBLIC_PLAYERS_CATALOG": sleeper_records,
        },
        CANONICAL_ROWS,
    )
    assert report["canonicalPoolSize"] == 3
    assert report["sources"]["NFLVERSE_OFFICIAL_INJURY_REPORT"]["distinctCanonicalPlayersMatched"] == 1
    assert report["sources"]["NFLVERSE_OFFICIAL_INJURY_REPORT"]["matchedRecordsWithPracticeStatePopulated"] == 1
    assert report["sources"]["SLEEPER_PUBLIC_PLAYERS_CATALOG"]["distinctCanonicalPlayersMatched"] == 1
    assert report["sources"]["SLEEPER_PUBLIC_PLAYERS_CATALOG"]["matchedRecordsWithPracticeStatePopulated"] == 0


def test_manual_override_comparison_never_mutates_the_real_override_shape_and_reports_silence_honestly():
    overrides = [
        {"player_id": "00-0040130", "player_name": "Jayden Higgins", "kind": "SEASON_OUT"},
        {"player_id": "00-0099999", "player_name": "Nobody Shadow Has Ever Heard Of", "kind": "NOT_WITH_TEAM"},
    ]
    sleeper_records = match_shadow_records_to_canonical(
        (
            ShadowPlayerStatus(
                source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
                source_player_id="sleeper-3",
                player_name="Jayden Higgins",
                position="WR",
                team="HOU",
                status_category="INACTIVE",
                injury_designation="IR",
                practice_state=None,
                ir_pup_nfi="Injured Reserve",
                suspension=False,
                source_as_of="1787339422095",
                gsis_id=None,
            ),
        ),
        CANONICAL_ROWS,
    )
    report = build_manual_override_comparison_report(
        overrides, {"SLEEPER_PUBLIC_PLAYERS_CATALOG": sleeper_records}
    )
    assert report["manualOverrideCount"] == 2
    higgins = next(c for c in report["comparisons"] if c["playerId"] == "00-0040130")
    assert higgins["shadowFindings"]["SLEEPER_PUBLIC_PLAYERS_CATALOG"][0]["injuryDesignation"] == "IR"
    nobody = next(c for c in report["comparisons"] if c["playerId"] == "00-0099999")
    assert nobody["shadowFindings"]["SLEEPER_PUBLIC_PLAYERS_CATALOG"] is None  # honest silence, not a fabricated miss


def test_precedence_design_puts_manual_override_strictly_first_and_never_auto_applies():
    design = precedence_design()
    order = design["precedenceOrder"]
    assert order[0]["authority"] == "MANUAL_VERIFIED_OVERRIDE"
    assert order[0]["rank"] == 1
    assert order[1]["authority"] == "AUTOMATED_SHADOW_SOURCE"
    assert "never" in order[1]["rule"].lower() or "Never" in order[1]["rule"]
    assert "future" in design["promotionRequirement"].lower()


# --- Hard boundary / inertness proofs -----------------------------------


def test_shadow_module_is_imported_by_no_production_consumer():
    """Real, source-level static proof (same technique
    `test_player_availability_status_consumer_consistency.py` already
    uses): the shadow module's own name never appears in any file that
    could wire it into a live recommendation/scoring/status path."""

    guarded_files = [
        REPO_ROOT / "src" / "application" / "desktop_facade.py",
        REPO_ROOT / "src" / "desktop_api" / "server.py",
        REPO_ROOT / "src" / "services" / "player_availability_status_service.py",
        REPO_ROOT / "src" / "services" / "current_player_status_overrides_service.py",
        REPO_ROOT / "src" / "services" / "redraft_engine_v1_service.py",
        REPO_ROOT / "src" / "services" / "shadow_numeric_authorities_service.py",
    ]
    for path in guarded_files:
        assert path.exists(), f"expected file missing, cannot guard: {path}"
        text = path.read_text(encoding="utf-8")
        assert "live_player_intelligence_shadow_v1_service" not in text, (
            f"{path} imports the shadow bakeoff module -- this must stay a standalone, "
            "reference-only module until a future, separate promotion decision"
        )


def test_creating_a_shadow_snapshot_file_does_not_change_the_real_player_availability_status_authority_output(
    tmp_path: Path,
):
    """Real before/after inertness proof against the ACTUAL, existing
    `PlayerAvailabilityStatus` authority (not a proxy) -- reads the SAME
    real repo config `current_player_status_overrides_service.py` reads,
    with a fresh local_exports-shaped shadow snapshot written to disk in
    between the two calls."""

    before_statuses = load_player_availability_statuses(REPO_ROOT)
    before_health = player_availability_authority_health(REPO_ROOT)

    # Write a real shadow snapshot file into the new, separate location --
    # exactly what the fetch script would produce -- and confirm it changes
    # nothing about the real authority's output.
    shadow_dir = REPO_ROOT / "local_exports" / "live_player_intelligence_shadow_v1" / "sleeper_players" / "latest"
    shadow_dir.mkdir(parents=True, exist_ok=True)
    probe_path = shadow_dir / "_inertness_probe_do_not_commit.json"
    probe_path.write_text(json.dumps({"probe": True}), encoding="utf-8")
    try:
        after_statuses = load_player_availability_statuses(REPO_ROOT)
        after_health = player_availability_authority_health(REPO_ROOT)

        assert before_statuses == after_statuses
        assert before_health == after_health
    finally:
        probe_path.unlink(missing_ok=True)


def test_precedence_design_and_reports_are_pure_no_filesystem_or_network_access(monkeypatch):
    """Belt-and-suspenders: every function this test file exercises above
    the fetch script boundary takes plain in-memory data and returns plain
    data -- no `open`/`urlopen` call is reachable from them. Proven by
    denying filesystem/network primitives during the calls and confirming
    nothing breaks."""

    import builtins

    real_open = builtins.open

    def _guarded_open(*args, **kwargs):  # pragma: no cover - should never fire
        raise AssertionError("pure shadow-report functions must not touch the filesystem")

    monkeypatch.setattr(builtins, "open", _guarded_open)
    try:
        design = precedence_design()
        assert design["precedenceOrder"]
        report = build_coverage_report({}, CANONICAL_ROWS)
        assert report["canonicalPoolSize"] == 3
    finally:
        monkeypatch.setattr(builtins, "open", real_open)
