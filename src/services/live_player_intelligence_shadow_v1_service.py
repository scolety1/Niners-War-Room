"""Live Player Intelligence provider bakeoff -- SHADOW INGESTION ONLY (NWR
Post-UI Product V1, P1-5).

This module is deliberately NOT a second `PlayerAvailabilityStatus`
authority. It reads real, free, publicly available player-status data from
two genuinely admissible sources (see
`docs/codex/post_ui_v1/NWR_PLAYER_INTELLIGENCE_PROVIDER_BAKEOFF_V1.md` for
the full research/verdict), maps it into a REFERENCE-ONLY shape, and
produces coverage/comparison reports against NWR's real canonical player
pool and the real, existing manual-override authority
(`current_player_status_overrides_service.py`).

Hard boundary (verified, not just asserted): nothing in this module is
imported by `src/application/desktop_facade.py`, `src/desktop_api/server.py`,
`player_availability_status_service.py`, or any recommendation/scoring
module. `tests/test_live_player_intelligence_shadow_v1_service.py` includes
an explicit architecture guard proving that, plus a real
before/after-inertness check against the actual
`PlayerAvailabilityStatus` authority functions.

The two admitted sources, and why:
  * nflverse official weekly injury report (`load_injuries()` /
    `injuries_<season>.csv`, public GitHub release, free, no key, no ToS
    restriction found -- the same nflverse family this repo already treats
    as an admissible free source everywhere else). Real, current-season
    rows already carry NWR's own canonical `gsis_id` player-id scheme
    directly (no fuzzy matching needed), plus official `report_status`
    (game-status designation) and `practice_status` (Full/Limited/DNP --
    real practice-participation granularity). Only lists players who are
    ACTUALLY on that week's injury report, so its coverage of the full
    canonical pool is small and expected to be small (see the report) --
    it is a precise, high-confidence, narrow signal, not a broad one.
  * Sleeper's public `players/nfl` catalog (`api.sleeper.app/v1/players/nfl`,
    the SAME free, keyless, already-used-elsewhere-in-this-repo endpoint)
    -- broad roster-level coverage (current team, IR/PUP/Suspended/Inactive
    status, depth-chart order), but its own `practice_participation` field
    is empirically almost never populated (verified: 1 non-null value out
    of 12,227 real players in a real live pull), so it is NOT treated as a
    practice-participation source here despite the field existing in its
    schema. Sleeper is free for non-commercial use only per its own docs
    (https://docs.sleeper.com/) -- flagged in the bakeoff doc as a real
    caveat to revisit if NWR is ever distributed/sold commercially.

Neither source is ever auto-applied to any ranking, recommendation, or
roster-completion path. Promotion (if it ever happens) is a separate,
future, deliberate decision -- this module only builds the evidence for
that decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace as _dc_replace
from typing import Any, Literal, Mapping, Sequence

from src.services.fantasypros_kdst_consensus_service import SLEEPER_FANTASY_POSITIONS, _identity

MatchMethod = Literal["GSIS_DIRECT", "NAME_POSITION_TEAM", "UNMATCHED_NO_TEAM", "UNMATCHED"]

ShadowSourceName = Literal["NFLVERSE_OFFICIAL_INJURY_REPORT", "SLEEPER_PUBLIC_PLAYERS_CATALOG"]

# Real, disclosed report-status/practice-status values (nflverse's own
# vocabulary -- never invented, never remapped to a different word).
_NFLVERSE_DESIGNATION_CATEGORY: dict[str, str] = {
    "Out": "OUT",
    "Doubtful": "DOUBTFUL",
    "Questionable": "QUESTIONABLE",
}

# Sleeper's own `status`/`injury_status` vocabulary, mapped honestly --
# only SEASON_OUT-shaped kinds get a category; everything else passes
# through as its own literal Sleeper string so nothing is silently
# reinterpreted.
_SLEEPER_ZERO_VALUE_STATUSES = frozenset(
    {"Inactive", "Injured Reserve", "Physically Unable to Perform", "Non Football Injury"}
)

# The IR/PUP/NFI signal can live in EITHER real Sleeper field -- `status`
# (e.g. "Injured Reserve", "Physically Unable to Perform") for a roster-
# transaction view, OR `injury_status` (e.g. "IR", "PUP") for a player who
# is merely flagged while `status` still reads "Inactive" (verified live,
# e.g. real player Jayden Higgins: status="Inactive", injury_status="IR").
# Both are checked so neither real shape is silently dropped.
_IR_PUP_NFI_STATUS_VALUES = ("Injured Reserve", "Physically Unable to Perform", "Non Football Injury")
_IR_PUP_NFI_INJURY_STATUS_VALUES = ("IR", "PUP", "NFI")


@dataclass(frozen=True)
class ShadowPlayerStatus:
    """One reference-only, shadow-source status record. Mirrors
    `PlayerAvailabilityStatus`'s field NAMES where the concept genuinely
    exists in the source, but is never written into that authority's own
    storage and never consumed by any live recommendation path."""

    source: ShadowSourceName
    source_player_id: str
    player_name: str
    position: str
    team: str | None
    status_category: str | None
    injury_designation: str | None
    practice_state: str | None
    ir_pup_nfi: str | None
    suspension: bool
    source_as_of: str | None
    gsis_id: str | None = None
    matched_canonical_player_id: str | None = None
    match_method: MatchMethod = "UNMATCHED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "sourcePlayerId": self.source_player_id,
            "playerName": self.player_name,
            "position": self.position,
            "team": self.team,
            "statusCategory": self.status_category,
            "injuryDesignation": self.injury_designation,
            "practiceState": self.practice_state,
            "irPupNfi": self.ir_pup_nfi,
            "suspension": self.suspension,
            "sourceAsOf": self.source_as_of,
            "gsisId": self.gsis_id,
            "matchedCanonicalPlayerId": self.matched_canonical_player_id,
            "matchMethod": self.match_method,
        }


def build_nflverse_injury_shadow_records(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[ShadowPlayerStatus, ...]:
    """Maps real nflverse `injuries_<season>.csv` rows (already loaded as
    plain dicts -- this function performs no network I/O) into shadow
    records. `gsis_id` passes through unchanged as `source_player_id` --
    it is the SAME id scheme NWR's own canonical `player_id` uses, so
    matching against the canonical pool is a direct set-membership check,
    not a fuzzy join (see `match_shadow_records_to_canonical`)."""

    records: list[ShadowPlayerStatus] = []
    for row in rows:
        gsis_id = str(row.get("gsis_id") or "").strip()
        if not gsis_id:
            continue
        report_status = str(row.get("report_status") or "").strip()
        practice_status = str(row.get("practice_status") or "").strip() or None
        category = _NFLVERSE_DESIGNATION_CATEGORY.get(report_status)
        records.append(
            ShadowPlayerStatus(
                source="NFLVERSE_OFFICIAL_INJURY_REPORT",
                source_player_id=gsis_id,
                player_name=str(row.get("full_name") or ""),
                position=str(row.get("position") or ""),
                team=str(row.get("team") or "").upper() or None,
                status_category=category,
                injury_designation=report_status or None,
                practice_state=practice_status,
                ir_pup_nfi=None,
                suspension=False,
                source_as_of=(
                    f"{row.get('season')}-{row.get('season_type')}-week{row.get('week')}"
                    if row.get("season")
                    else None
                ),
                gsis_id=gsis_id,
            )
        )
    return tuple(records)


def build_sleeper_shadow_records(
    players_catalog: Mapping[str, Mapping[str, Any]],
) -> tuple[ShadowPlayerStatus, ...]:
    """Maps a real, already-fetched Sleeper `players/nfl` catalog dict
    (this function performs no network I/O -- the caller is responsible
    for respecting Sleeper's own documented once-per-day fetch/caching
    policy, see `scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py`)
    into shadow records. Only players carrying a real, non-empty
    `injury_status` OR a non-"Active" `status` are included -- a fully
    healthy, active player has nothing to shadow-report."""

    records: list[ShadowPlayerStatus] = []
    for sleeper_id, player in players_catalog.items():
        if not isinstance(player, Mapping):
            continue
        status = str(player.get("status") or "").strip() or None
        injury_status = str(player.get("injury_status") or "").strip() or None
        if not injury_status and status in (None, "Active"):
            continue
        gsis_id = str(player.get("gsis_id") or "").strip() or None
        if status in _IR_PUP_NFI_STATUS_VALUES:
            ir_pup_nfi = status
        elif injury_status in _IR_PUP_NFI_INJURY_STATUS_VALUES:
            ir_pup_nfi = injury_status
        else:
            ir_pup_nfi = None
        suspension = injury_status in ("Sus", "SUSP", "Suspended")
        records.append(
            ShadowPlayerStatus(
                source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
                source_player_id=str(sleeper_id),
                player_name=str(player.get("full_name") or "").strip(),
                position=str(player.get("position") or "").strip(),
                team=str(player.get("team") or "").upper() or None,
                status_category=status.upper().replace(" ", "_") if status else None,
                injury_designation=injury_status,
                practice_state=str(player.get("practice_participation") or "").strip() or None,
                ir_pup_nfi=ir_pup_nfi,
                suspension=suspension,
                source_as_of=str(player.get("news_updated") or "").strip() or None,
                gsis_id=gsis_id,
            )
        )
    return tuple(records)


@dataclass(frozen=True)
class CanonicalPlayerRow:
    player_id: str
    player_name: str
    position: str
    team: str


def match_shadow_records_to_canonical(
    shadow_records: Sequence[ShadowPlayerStatus],
    canonical_rows: Sequence[CanonicalPlayerRow],
) -> tuple[ShadowPlayerStatus, ...]:
    """Resolves each shadow record's `matched_canonical_player_id` against
    NWR's real governed canonical pool. Two methods only, both already
    proven elsewhere in this codebase -- no new identity heuristic is
    invented here:
      1. GSIS_DIRECT -- the shadow record's own player id (nflverse's
         `gsis_id`, or Sleeper's own `gsis_id` field when populated) is a
         literal member of the canonical pool's id set.
      2. NAME_POSITION_TEAM -- the SAME `_identity` normalizer
         `waiver_engine_service.resolve_roster_canonical_ids` already uses
         to join a live Sleeper roster to this pool. Requires a non-empty
         team (by design, matching the existing app-wide identity
         discipline) -- a team-less shadow record (e.g. a released/
         between-teams player) is honestly reported as
         `UNMATCHED_NO_TEAM`, never guessed."""

    canonical_ids = {row.player_id for row in canonical_rows}
    by_identity: dict[tuple[str, str, str], str] = {}
    for row in canonical_rows:
        key = _identity(row.player_name, row.position, row.team, allowed_positions=SLEEPER_FANTASY_POSITIONS)
        if key != ("", "", ""):
            by_identity.setdefault(key, row.player_id)

    resolved: list[ShadowPlayerStatus] = []
    for record in shadow_records:
        if record.gsis_id and record.gsis_id in canonical_ids:
            resolved.append(
                _replace(record, matched_canonical_player_id=record.gsis_id, match_method="GSIS_DIRECT")
            )
            continue
        key = _identity(record.player_name, record.position, record.team, allowed_positions=SLEEPER_FANTASY_POSITIONS)
        canonical_id = by_identity.get(key, "") if key != ("", "", "") else ""
        if canonical_id:
            resolved.append(
                _replace(record, matched_canonical_player_id=canonical_id, match_method="NAME_POSITION_TEAM")
            )
        elif not record.team:
            resolved.append(_replace(record, matched_canonical_player_id=None, match_method="UNMATCHED_NO_TEAM"))
        else:
            resolved.append(_replace(record, matched_canonical_player_id=None, match_method="UNMATCHED"))
    return tuple(resolved)


def _replace(record: ShadowPlayerStatus, **changes: Any) -> ShadowPlayerStatus:
    return _dc_replace(record, **changes)


def build_coverage_report(
    shadow_records_by_source: Mapping[ShadowSourceName, Sequence[ShadowPlayerStatus]],
    canonical_rows: Sequence[CanonicalPlayerRow],
) -> dict[str, Any]:
    """Honest coverage numbers per source -- never a single blended
    percentage that hides which source did the work."""

    pool_size = len(canonical_rows)
    report: dict[str, Any] = {"canonicalPoolSize": pool_size, "sources": {}}
    for source_name, records in shadow_records_by_source.items():
        matched_ids = {r.matched_canonical_player_id for r in records if r.matched_canonical_player_id}
        by_method: dict[str, int] = {}
        for r in records:
            by_method[r.match_method] = by_method.get(r.match_method, 0) + 1
        with_practice_state = sum(1 for r in records if r.matched_canonical_player_id and r.practice_state)
        report["sources"][source_name] = {
            "rawRecordCount": len(records),
            "distinctCanonicalPlayersMatched": len(matched_ids),
            "coverageOfCanonicalPool": round(len(matched_ids) / pool_size, 4) if pool_size else 0.0,
            "matchMethodCounts": by_method,
            "matchedRecordsWithPracticeStatePopulated": with_practice_state,
        }
    return report


def build_manual_override_comparison_report(
    manual_overrides: Sequence[Mapping[str, Any]],
    shadow_records_by_source: Mapping[ShadowSourceName, Sequence[ShadowPlayerStatus]],
) -> dict[str, Any]:
    """For every REAL, already-verified manual override on file, reports
    whether each shadow source independently carries a matching signal for
    that same player -- agreement/disagreement/silence, never auto-applied.
    This is comparison-for-disclosure only; it changes nothing about the
    override file or any consumer of it."""

    comparisons: list[dict[str, Any]] = []
    for override in manual_overrides:
        player_id = str(override.get("player_id") or "")
        entry: dict[str, Any] = {
            "playerId": player_id,
            "playerName": override.get("player_name"),
            "overrideKind": override.get("kind"),
            "shadowFindings": {},
        }
        for source_name, records in shadow_records_by_source.items():
            hits = [r for r in records if r.matched_canonical_player_id == player_id]
            entry["shadowFindings"][source_name] = [h.to_dict() for h in hits] if hits else None
        comparisons.append(entry)
    return {"manualOverrideCount": len(manual_overrides), "comparisons": comparisons}


def precedence_design() -> dict[str, Any]:
    """DESIGN PROPOSAL ONLY -- not implemented anywhere, not read by any
    consumer. Documents the field-level precedence that WOULD apply if a
    shadow source were ever promoted by a future, separate, deliberate
    decision. Returned as data (also reproduced in prose in the bakeoff
    doc) so a future promotion pass has one unambiguous source of truth to
    implement against rather than re-deriving it."""

    return {
        "precedenceOrder": [
            {
                "rank": 1,
                "authority": "MANUAL_VERIFIED_OVERRIDE",
                "source": "current_player_status_overrides_service.py",
                "rule": (
                    "Always wins, unconditionally, on every field it sets. A verified manual "
                    "override must be able to surgically supersede bad or stale automated data -- "
                    "this is non-negotiable per existing project discipline and is never weakened "
                    "by a shadow source's presence, freshness, or agreement/disagreement."
                ),
            },
            {
                "rank": 2,
                "authority": "AUTOMATED_SHADOW_SOURCE",
                "source": "NFLVERSE_OFFICIAL_INJURY_REPORT (preferred for injury_designation/practice_state) "
                "then SLEEPER_PUBLIC_PLAYERS_CATALOG (preferred for team/IR-PUP-Suspended/roster status)",
                "rule": (
                    "Only applies to a player with NO manual override on that field. Between the two "
                    "automated sources, when both report on the SAME field for the SAME player and "
                    "disagree: nflverse's official report_status/practice_status wins for injury "
                    "designation and practice participation (it is the actual official NFL injury "
                    "report, not a community-maintained mirror); Sleeper wins for team/roster-status "
                    "fields (IR/PUP/Suspended/Inactive, current team) that nflverse's weekly injury "
                    "file does not carry at all. Never auto-applied to any ranking/recommendation "
                    "path until a future, separate promotion decision is made and implemented."
                ),
            },
            {
                "rank": 3,
                "authority": "NO_SIGNAL",
                "source": "default",
                "rule": "No override and no shadow signal -- treated as full, healthy value, exactly as today.",
            },
        ],
        "promotionRequirement": (
            "Promotion out of shadow-only status is a future, separate, deliberate decision -- not "
            "automatic, not implied by this module's existence, and not something this pass performs."
        ),
    }
