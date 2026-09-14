"""Canonical identity mapping for the Live Player Intelligence V1 benchmark
cycle (Worker 2 / Work Unit 2/3).

Reuses NWR's EXISTING canonical identity resolver -- `_identity` from
`fantasypros_kdst_consensus_service.py` (the SAME normalizer
`waiver_engine_service.resolve_roster_canonical_ids` and
`live_player_intelligence_shadow_v1_service.match_shadow_records_to_canonical`
already use) -- and does NOT invent a second matcher. This module adds one
thing that did not exist yet: a per-row classification granular enough to
report `matched uniquely / unmatched / ambiguous / team mismatch /
name mismatch / provider-ID mismatch` for ALL rows of a source (not just the
"actionable status" subset `live_player_intelligence_shadow_v1_service`
already filters to), matching Gate 2's "zero guessed joins... ambiguous or
low-confidence match is quarantined, not admitted at reduced confidence."

Pure, network-free, no production wiring: nothing here is imported by
`src/application/desktop_facade.py`, `src/desktop_api/server.py`, or any
recommendation/scoring module.

Classification design (documented here so the counts in the benchmark doc
are reproducible from this one place):

Primary bucket, exactly one per row (priority order below; the first
condition that fires wins):
  1. AMBIGUOUS_CANONICAL_POOL_COLLISION -- two DIFFERENT canonical player_ids
     in the canonical pool itself normalize to the exact same
     `_identity(name, position, team)` key. This would mean the canonical
     pool itself cannot disambiguate the row even in principle. Checked for
     real (not assumed absent) on every run.
  2. AMBIGUOUS_ID_NAME_DISAGREEMENT -- the row's own provider id (e.g.
     `gsis_id`) is a member of the canonical id set AND the row's
     name/position/team independently resolves (via `_identity`) to a
     DIFFERENT canonical player_id. Two independent signals disagreeing is
     exactly the "ambiguous" case Gate 2 requires quarantining rather than
     guessing between.
  3. MATCHED_GSIS_DIRECT -- the row's own provider id is a literal member of
     the canonical pool's id set (and did not conflict per #2). ID-based
     matches always take priority over name-based ones once ambiguity is
     ruled out, per Gate 2's own stated preference ("direct id-scheme match"
     listed first).
  4. UNMATCHED_POSITION_OUT_OF_SCOPE -- no id match, and the row's own
     position does not correspond to any canonical-pool position vocabulary
     at all (e.g. a depth-chart offensive-line/defensive role, or a
     kicker/DST row against a canonical pool that only carries
     QB/RB/WR/TE) -- the row could never validly match, regardless of name,
     and is reported separately from a real "we tried and failed" miss.
  5. MATCHED_NAME_POSITION_TEAM -- no id match, but the row's own
     name+position+team normalizes (via the SAME `_identity` call) to
     exactly one canonical player_id.
  6. TEAM_MISMATCH -- the row DOES carry a non-empty team, no id match, no
     exact name+position+team match, but the row's normalized name+position
     DOES match a canonical player under a DIFFERENT, non-empty team
     (relaxed lookup, same `_identity` normalizer, team ignored).
     Quarantined, not silently treated as a miss or a match -- this is the
     real, disclosed shape of a traded/depth-chart-lag player OR (see
     `team_mismatch_is_known_code_alias` below) a team-abbreviation
     convention difference between sources, never auto-resolved here.
  7. UNMATCHED_NO_TEAM -- the row carries no team value at all. Reported
     even when a name+position candidate exists elsewhere (`_identity`
     requires a non-empty team by design app-wide, so this pass never
     relaxes that requirement to manufacture a match) -- such a candidate
     is recorded in `team_mismatch_candidate_team` for visibility but the
     row still quarantines as NO_TEAM, distinct from a real TEAM_MISMATCH.
  8. UNMATCHED -- none of the above.

"matched uniquely" (as the directive's vocabulary) = buckets 3 + 5.
"ambiguous" = buckets 1 + 2. "team mismatch" = bucket 6.
"unmatched" = buckets 7 + 8 (reported together and separately).
"position out of scope" = bucket 4 (reported separately, not folded into
either matched or unmatched, since it is neither -- the row was never
eligible to match by NWR's own governed-pool position vocabulary).

Three further ORTHOGONAL diagnostic flags (can co-occur with any primary
bucket, reported as their own separate counts per the directive):
  * `name_mismatch` -- set on a MATCHED_GSIS_DIRECT row whose own normalized
    name disagrees with the canonical pool's normalized name for that same
    id (aliases/nicknames/typos -- informational, the id still wins).
  * `provider_id_mismatch` -- set whenever the row is a fantasy-relevant
    position (`position_in_scope`) AND carries a non-empty provider id that
    is NOT a member of the canonical pool's id set at all (a stale/foreign
    id -- a real data-quality signal, since we would otherwise expect this
    id to resolve). Deliberately NOT set for out-of-scope-position rows
    (e.g. a real, valid, correctly-populated id on an offensive-line or
    defensive-role row) -- that id was never going to be in a QB/RB/WR/TE
    canonical pool regardless of data quality, so flagging it as a
    "mismatch" would be noise, not signal.
  * `team_mismatch_is_known_code_alias` -- set on a TEAM_MISMATCH row ONLY
    when the two disagreeing team codes are a KNOWN existing alias pair
    already handled elsewhere in this codebase (`LAR`/`LA`, `JAC`/`JAX` --
    see `nflverse_player_context_display_service.py`,
    `nflverse_player_context_yellow_items_service.py`,
    `nflverse_player_context_hardening_service.py`). This is reporting-only
    -- it does NOT change the row's classification, does NOT un-quarantine
    it, and does NOT add a new matching heuristic to `_identity` itself; it
    exists purely so the benchmark doc can honestly separate "real
    roster-change-shaped team mismatch" from "known team-code spelling
    convention noise" within the same quarantined count.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.services.fantasypros_kdst_consensus_service import SLEEPER_FANTASY_POSITIONS, _identity
from src.services.live_player_intelligence_shadow_v1_service import CanonicalPlayerRow

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANONICAL_POOL_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "model"
    / "nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912"
    / "GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv"
)

_DUMMY_TEAM_FOR_NAME_POSITION_ONLY_LOOKUP = "ZZ_NAME_POSITION_ONLY"

PrimaryClassification = str  # one of the 8 buckets documented above

_MATCHED_BUCKETS = frozenset({"MATCHED_GSIS_DIRECT", "MATCHED_NAME_POSITION_TEAM"})
_AMBIGUOUS_BUCKETS = frozenset(
    {"AMBIGUOUS_CANONICAL_POOL_COLLISION", "AMBIGUOUS_ID_NAME_DISAGREEMENT"}
)
_UNMATCHED_BUCKETS = frozenset({"UNMATCHED", "UNMATCHED_NO_TEAM"})
_QUARANTINE_BUCKETS = _AMBIGUOUS_BUCKETS | frozenset({"TEAM_MISMATCH"})

# Reused, NOT invented here: the same team-code alias pairs already handled
# in `nflverse_player_context_display_service.py` /
# `nflverse_player_context_yellow_items_service.py` /
# `nflverse_player_context_hardening_service.py`. Used ONLY to label a
# TEAM_MISMATCH row as "known convention noise" for reporting -- never to
# change its classification.
_KNOWN_TEAM_CODE_ALIAS_PAIRS = frozenset({frozenset({"LAR", "LA"}), frozenset({"JAC", "JAX"})})


def _is_known_team_code_alias(team_a: str, team_b: str) -> bool:
    return frozenset({team_a, team_b}) in _KNOWN_TEAM_CODE_ALIAS_PAIRS


@dataclass(frozen=True)
class CommonSourceRow:
    """One source row already normalized to the shared name/position/team/
    provider-id shape every source needs to reach `_identity` -- built by a
    small per-source adapter (`common_rows_from_*` below), never by
    duplicating `_identity`'s own normalization logic."""

    source: str
    source_row_id: str
    player_name: str
    position: str
    team: str
    provider_id: str
    position_in_scope: bool
    raw: Mapping[str, Any]


@dataclass(frozen=True)
class IdentityMappingRow:
    source: str
    source_row_id: str
    player_name: str
    position: str
    team: str
    provider_id: str
    primary_classification: PrimaryClassification
    matched_canonical_player_id: str | None
    team_mismatch_candidate_team: str | None
    name_mismatch: bool
    provider_id_mismatch: bool
    team_mismatch_is_known_code_alias: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "sourceRowId": self.source_row_id,
            "playerName": self.player_name,
            "position": self.position,
            "team": self.team,
            "providerId": self.provider_id,
            "primaryClassification": self.primary_classification,
            "matchedCanonicalPlayerId": self.matched_canonical_player_id,
            "teamMismatchCandidateTeam": self.team_mismatch_candidate_team,
            "nameMismatch": self.name_mismatch,
            "providerIdMismatch": self.provider_id_mismatch,
            "teamMismatchIsKnownCodeAlias": self.team_mismatch_is_known_code_alias,
        }


def load_canonical_pool(path: str | Path = DEFAULT_CANONICAL_POOL_PATH) -> tuple[CanonicalPlayerRow, ...]:
    """Loads NWR's real, governed 564-player Freeze V7 canonical pool
    (`player_id` already IS the `gsis_id` scheme -- verified directly in
    the CSV, no second id space). Read-only; never writes this file."""

    rows: list[CanonicalPlayerRow] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            player_id = str(row.get("player_id") or "").strip()
            if not player_id:
                continue
            rows.append(
                CanonicalPlayerRow(
                    player_id=player_id,
                    player_name=str(row.get("player_name") or "").strip(),
                    position=str(row.get("position") or "").strip(),
                    team=str(row.get("team") or "").strip(),
                )
            )
    return tuple(rows)


# ---------------------------------------------------------------------------
# Per-source adapters -- extraction only, no matching logic lives here.
# ---------------------------------------------------------------------------

def common_rows_from_nflverse_injuries(rows: Sequence[Mapping[str, Any]]) -> tuple[CommonSourceRow, ...]:
    out: list[CommonSourceRow] = []
    for index, row in enumerate(rows):
        position = str(row.get("position") or "").strip().upper()
        out.append(
            CommonSourceRow(
                source="NFLVERSE_OFFICIAL_INJURY_REPORT",
                source_row_id=str(row.get("gsis_id") or f"row{index}").strip(),
                player_name=str(row.get("full_name") or "").strip(),
                position=position,
                team=str(row.get("team") or "").strip().upper(),
                provider_id=str(row.get("gsis_id") or "").strip(),
                position_in_scope=position in SLEEPER_FANTASY_POSITIONS,
                raw=row,
            )
        )
    return tuple(out)


# Real, disclosed pos_name -> fantasy-position normalization for nflverse
# depth charts. Only the fantasy-relevant roles map to something; every
# other real pos_name (offensive line, defensive front/back seven, punter/
# holder/long-snapper, return-specialist role labels on an otherwise
# offensive skill player) is intentionally left unmapped -- those rows are
# real and are still passed through `common_rows_from_nflverse_depth_charts`
# with `position_in_scope=False`, never silently dropped before counting.
DEPTH_CHART_POSITION_MAP: dict[str, str] = {
    "Quarterback": "QB",
    "Running Back": "RB",
    "Fullback": "RB",  # NWR's canonical pool does not carry a separate FB position; documented normalization, not a new identity heuristic.
    "Wide Receiver": "WR",
    "Tight End": "TE",
    "Place kicker": "K",
}


def latest_snapshot_only(rows: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    """Depth charts is one 177-daily-snapshot file (`dt` column); this
    returns only the rows for the single most-recent `dt`, matching Worker
    1's own characterization methodology (the latest single-day snapshot),
    not the full 516k-row history."""

    latest_dt = max((str(row.get("dt") or "") for row in rows), default="")
    return tuple(row for row in rows if str(row.get("dt") or "") == latest_dt)


def common_rows_from_nflverse_depth_charts(rows: Sequence[Mapping[str, Any]]) -> tuple[CommonSourceRow, ...]:
    out: list[CommonSourceRow] = []
    for index, row in enumerate(rows):
        raw_pos_name = str(row.get("pos_name") or "").strip()
        mapped_position = DEPTH_CHART_POSITION_MAP.get(raw_pos_name, "")
        out.append(
            CommonSourceRow(
                source="NFLVERSE_DEPTH_CHARTS",
                source_row_id=str(row.get("gsis_id") or f"row{index}").strip(),
                player_name=str(row.get("player_name") or "").strip(),
                position=mapped_position or raw_pos_name.upper(),
                team=str(row.get("team") or "").strip().upper(),
                provider_id=str(row.get("gsis_id") or "").strip(),
                position_in_scope=bool(mapped_position) and mapped_position in SLEEPER_FANTASY_POSITIONS,
                raw=row,
            )
        )
    return tuple(out)


def _sleeper_position_upper(value: object) -> str:
    position = str(value or "").upper()
    return "DST" if position == "DEF" else position


def common_rows_from_sleeper_catalog(players_catalog: Mapping[str, Mapping[str, Any]]) -> tuple[CommonSourceRow, ...]:
    out: list[CommonSourceRow] = []
    for sleeper_id, player in players_catalog.items():
        if not isinstance(player, Mapping):
            continue
        position = _sleeper_position_upper(player.get("position"))
        team = str(player.get("team") or "").strip().upper()
        name = str(player.get("full_name") or player.get("search_full_name") or "").strip()
        if position == "DST" and not name and team:
            name = f"{team} D/ST"
        out.append(
            CommonSourceRow(
                source="SLEEPER_PUBLIC_PLAYERS_CATALOG",
                source_row_id=str(sleeper_id),
                player_name=name,
                position=position,
                team=team,
                provider_id=str(player.get("gsis_id") or "").strip(),
                position_in_scope=position in SLEEPER_FANTASY_POSITIONS,
                raw=player,
            )
        )
    return tuple(out)


# ---------------------------------------------------------------------------
# Shared classification -- the ONLY place `_identity` is called for matching.
# ---------------------------------------------------------------------------

def _name_position_key(name: str, position: str) -> tuple[str, str]:
    """Reuses `_identity`'s own name/position normalization (a dummy
    non-empty team is passed through solely to satisfy `_identity`'s
    required-team guard, then discarded) instead of writing a second name
    normalizer."""

    full_key = _identity(
        name, position, _DUMMY_TEAM_FOR_NAME_POSITION_ONLY_LOOKUP, allowed_positions=SLEEPER_FANTASY_POSITIONS
    )
    return full_key[0], full_key[1]


def classify_rows(
    common_rows: Sequence[CommonSourceRow],
    canonical_rows: Sequence[CanonicalPlayerRow],
) -> tuple[IdentityMappingRow, ...]:
    canonical_by_id: dict[str, CanonicalPlayerRow] = {row.player_id: row for row in canonical_rows}

    identity_owners: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    canonical_by_identity: dict[tuple[str, str, str], str] = {}
    canonical_by_name_position: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for row in canonical_rows:
        key = _identity(row.player_name, row.position, row.team, allowed_positions=SLEEPER_FANTASY_POSITIONS)
        if key != ("", "", ""):
            identity_owners[key].add(row.player_id)
            canonical_by_identity.setdefault(key, row.player_id)
        name_pos_key = _name_position_key(row.player_name, row.position)
        if name_pos_key != ("", ""):
            canonical_by_name_position[name_pos_key].add((row.team, row.player_id))

    pool_collision_keys = {key for key, owners in identity_owners.items() if len(owners) > 1}

    results: list[IdentityMappingRow] = []
    for row in common_rows:
        id_match = canonical_by_id.get(row.provider_id) if row.provider_id else None
        identity_key = _identity(row.player_name, row.position, row.team, allowed_positions=SLEEPER_FANTASY_POSITIONS)
        identity_match_id = canonical_by_identity.get(identity_key) if identity_key != ("", "", "") else None
        is_pool_collision = identity_key in pool_collision_keys
        provider_id_mismatch = (
            row.position_in_scope and bool(row.provider_id) and row.provider_id not in canonical_by_id
        )

        name_mismatch = False
        if id_match is not None:
            canonical_name_key = _name_position_key(id_match.player_name, id_match.position)[0]
            row_name_key = _name_position_key(row.player_name, row.position)[0]
            name_mismatch = bool(canonical_name_key) and bool(row_name_key) and canonical_name_key != row_name_key

        team_mismatch_team: str | None = None
        matched_canonical_player_id: str | None = None
        is_known_alias = False

        if is_pool_collision:
            primary = "AMBIGUOUS_CANONICAL_POOL_COLLISION"
        elif id_match is not None and identity_match_id is not None and id_match.player_id != identity_match_id:
            primary = "AMBIGUOUS_ID_NAME_DISAGREEMENT"
        elif id_match is not None:
            primary = "MATCHED_GSIS_DIRECT"
            matched_canonical_player_id = id_match.player_id
        elif not row.position_in_scope:
            primary = "UNMATCHED_POSITION_OUT_OF_SCOPE"
        elif identity_match_id is not None:
            primary = "MATCHED_NAME_POSITION_TEAM"
            matched_canonical_player_id = identity_match_id
        else:
            relaxed_key = _name_position_key(row.player_name, row.position)
            candidates = canonical_by_name_position.get(relaxed_key) if relaxed_key != ("", "") else None
            other_team_candidates = (
                sorted({team for team, _pid in candidates if team != row.team}) if candidates else []
            )
            if row.team and other_team_candidates:
                # A real, non-empty team disagrees with a name+position hit
                # under a different real team -- a genuine team-mismatch
                # candidate (trade/roster-lag OR a team-code convention
                # difference, see `team_mismatch_is_known_code_alias`).
                primary = "TEAM_MISMATCH"
                team_mismatch_team = other_team_candidates[0]
                is_known_alias = _is_known_team_code_alias(row.team, team_mismatch_team)
            elif not row.team:
                # No team to compare at all -- `_identity` requires a
                # non-empty team by design app-wide, so this is never
                # relaxed into a match. A same-name/position candidate
                # (if any) is still surfaced for visibility, not admitted.
                primary = "UNMATCHED_NO_TEAM"
                if other_team_candidates:
                    team_mismatch_team = other_team_candidates[0]
            else:
                primary = "UNMATCHED"

        results.append(
            IdentityMappingRow(
                source=row.source,
                source_row_id=row.source_row_id,
                player_name=row.player_name,
                position=row.position,
                team=row.team,
                provider_id=row.provider_id,
                primary_classification=primary,
                matched_canonical_player_id=matched_canonical_player_id,
                team_mismatch_candidate_team=team_mismatch_team,
                name_mismatch=name_mismatch,
                provider_id_mismatch=provider_id_mismatch,
                team_mismatch_is_known_code_alias=is_known_alias,
            )
        )
    return tuple(results)


def summarize_identity_mapping(
    rows: Sequence[IdentityMappingRow],
    *,
    canonical_pool_size: int | None = None,
) -> dict[str, Any]:
    by_bucket: dict[str, int] = defaultdict(int)
    name_mismatch_count = 0
    provider_id_mismatch_count = 0
    team_mismatch_known_alias_count = 0
    distinct_canonical_ids_matched: set[str] = set()
    for row in rows:
        by_bucket[row.primary_classification] += 1
        if row.name_mismatch:
            name_mismatch_count += 1
        if row.provider_id_mismatch:
            provider_id_mismatch_count += 1
        if row.primary_classification == "TEAM_MISMATCH" and row.team_mismatch_is_known_code_alias:
            team_mismatch_known_alias_count += 1
        if row.matched_canonical_player_id:
            distinct_canonical_ids_matched.add(row.matched_canonical_player_id)

    matched_uniquely = sum(by_bucket.get(bucket, 0) for bucket in _MATCHED_BUCKETS)
    ambiguous = sum(by_bucket.get(bucket, 0) for bucket in _AMBIGUOUS_BUCKETS)
    unmatched = sum(by_bucket.get(bucket, 0) for bucket in _UNMATCHED_BUCKETS)
    team_mismatch = by_bucket.get("TEAM_MISMATCH", 0)
    position_out_of_scope = by_bucket.get("UNMATCHED_POSITION_OUT_OF_SCOPE", 0)

    summary: dict[str, Any] = {
        "totalRows": len(rows),
        "matchedUniquely": matched_uniquely,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
        "teamMismatch": team_mismatch,
        "teamMismatchKnownCodeAlias": team_mismatch_known_alias_count,
        "teamMismatchGenuine": team_mismatch - team_mismatch_known_alias_count,
        "positionOutOfScope": position_out_of_scope,
        "nameMismatch": name_mismatch_count,
        "providerIdMismatch": provider_id_mismatch_count,
        "distinctCanonicalPlayersMatched": len(distinct_canonical_ids_matched),
        "primaryClassificationCounts": dict(sorted(by_bucket.items())),
    }
    if canonical_pool_size:
        summary["coverageOfCanonicalPool"] = round(len(distinct_canonical_ids_matched) / canonical_pool_size, 4)
    return summary


def quarantined_rows(rows: Sequence[IdentityMappingRow]) -> tuple[IdentityMappingRow, ...]:
    """Ambiguous + team-mismatch rows -- explicitly listed, never silently
    dropped, and never included in any 'clean'/matched dataset."""

    return tuple(row for row in rows if row.primary_classification in _QUARANTINE_BUCKETS)
