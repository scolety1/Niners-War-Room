"""Dynasty League Import V1 (Worker 2, 2026-09-18) -- real Sleeper DYNASTY
league import: fetch, real-evidence pick-capital reconciliation, and a pure
ownership-annotation join over Dynasty's already-governed valuation board.

Hard boundary, never crossed by anything in this module: this module NEVER
computes, adjusts, or infers any score/rank/value field.
`governed_asset_registry_service.py`'s valuation core, `CURRENT_BOARD_SHA256`
gating, and the underlying board CSVs are read by callers of this module,
never by this module itself -- everything here is either (a) a real,
read-only (GET-only) fetch of Sleeper league/roster/pick state, or (b) a
pure join that ADDS ownership/roster-context fields onto rows a caller
already built, keyed only by the already-governed `asset_id` string.

Reused as-is, unmodified: `SleeperHttpClient` (GET-only by construction --
no verb parameter, no body argument anywhere in its call chain) and
`sleeper_league_context_service.team_name_by_roster_id` (so Dynasty never
invents a second, drifting team-naming rule versus Redraft's own in-season
surfaces). NOT reused: anything from `sleeper_redraft_owner_service.py` --
that module's `LeagueProfile`/`ScoringSettings` shape is Redraft's own
draft-pool valuation model, out of scope here per the owner's explicit
instruction not to route Dynasty decisions through Redraft valuation.

Persistence follows Redraft's own `redraft_engine_v1_service.py` store
convention (atomic, indent=2, sort_keys=True JSON; a `profiles/<id>.json`-
shaped tree), NOT Redraft's code, under a separate, worktree-isolated
`local_exports/dynasty_v1/` root -- explicitly NOT
`personal_workspace_service`'s shared `C:\\NWR_SHARED_DATA` path (that
module's own validation guard forbids `local_exports` as a workspace root
outright; see `docs/codex/dynasty_league_import_v1/LEDGER.md` Part A/C for
the full reasoning trail).

=== Round-count ambiguity: real, evidence-based resolution ===

League `1344772855908290560` ("Las Vegas Enginerds") has two real,
completed 2026 drafts with different round counts (24 vs. 5). This is not
a data error: a dynasty league commonly runs one large STARTUP draft once,
at league founding, covering every initial roster slot (here: 24 rounds x
10 teams = 240 picks, exactly matching `len(roster_positions) == 24`), and
then small annual ROOKIE-only drafts every subsequent year (here: 5
rounds x 10 teams = 50 picks). Live-verified (2026-09-18, real Sleeper API
GET calls, not the design-reference captures in the ledger): the 24-round
draft's own round-1 picks are established veterans (e.g. Christian Watson,
`years_exp: "4"`); the 5-round draft's own round-1 pick is a real 2026
rookie prospect (Jeremiyah Love, `years_exp: "0"`). `_classify_draft`
below turns this exact real per-pick evidence (`years_exp == "0"` fraction,
cross-checked against the rounds-vs-roster-slot-count startup signature)
into an honest `"startup" | "rookie" | "unknown"` label per draft --
never a guess from round count alone. `resolve_round_count_baseline` then
uses ONLY a real, uniquely-classified recurring "rookie" draft's round
count as the baseline for projecting future (not-yet-drafted) seasons'
pick capital, explicitly excluding the one-time "startup" draft from that
projection, and falls back to the league's own currently-configured
`settings.draft_rounds` -- with the fallback disclosed, never silent --
when classification is ambiguous (zero or more than one real "rookie"
draft found).
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.data.snapshots import utc_snapshot_stamp
from src.services.sleeper_import_service import SleeperHttpClient
from src.services.sleeper_league_context_service import team_name_by_roster_id

DYNASTY_LEAGUE_SCHEMA_VERSION = 1
DEFAULT_PICK_CAPITAL_SEASONS: tuple[str, ...] = ("2026", "2027", "2028")

UNRESOLVED_ROOKIE_OWNERSHIP_REASON = (
    "Rookie board asset IDs use a separate synthetic identity scheme (not a "
    "Sleeper numeric player ID); no live crosswalk exists yet, so ownership "
    "is honestly reported as unresolved rather than guessed."
)


class DynastyLeagueFetchError(RuntimeError):
    """A real Sleeper fetch for a dynasty league returned an unusable shape."""


class DynastyLeaguePersistenceError(RuntimeError):
    """A dynasty league profile/snapshot could not be read or written."""


# --------------------------------------------------------------------------
# Small, local, defensive parsers (deliberately not imported from
# `sleeper_league_context_service`'s private helpers -- each module in this
# codebase owns its own tiny safe-parsing layer rather than depending on
# another module's underscore-prefixed internals).
# --------------------------------------------------------------------------


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return default


def _safe_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _safe_str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item) for item in value if item is not None)
    return ()


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# Typed snapshot shape
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DynastyLeagueSettings:
    league_id: str
    name: str
    season: str
    status: str
    num_teams: int
    scoring_settings: Mapping[str, Any]
    roster_positions: tuple[str, ...]
    taxi_slots: int
    reserve_slots: int
    playoff_teams: int
    playoff_week_start: int
    trade_deadline: int
    pick_trading: int
    waiver_type: int
    waiver_budget: int
    max_keepers: int
    configured_draft_rounds: int


@dataclass(frozen=True)
class DynastyRosterEntry:
    roster_id: int
    owner_id: str
    co_owners: tuple[str, ...]
    team_name: str
    players: tuple[str, ...]
    starters: tuple[str, ...]
    reserve: tuple[str, ...]
    taxi: tuple[str, ...]
    wins: int
    losses: int
    ties: int
    fpts: float
    ppts: float


@dataclass(frozen=True)
class DynastyDraftRecord:
    draft_id: str
    status: str
    draft_type: str
    season: str
    rounds: int
    start_time: int | None
    created: int | None
    pick_count: int
    rookie_pick_fraction: float | None
    classification: str


@dataclass(frozen=True)
class RoundCountBaseline:
    rounds: int
    source: str
    disclosure: str
    startup_draft_id: str | None
    rookie_draft_ids: tuple[str, ...]
    ambiguous: bool


@dataclass(frozen=True)
class DynastyLeagueSnapshot:
    league_id: str
    fetched_at_utc: str
    settings: DynastyLeagueSettings
    rosters: tuple[DynastyRosterEntry, ...]
    owner_id_by_roster_id: Mapping[int, str]
    roster_id_by_owner_id: Mapping[str, int]
    traded_picks: tuple[Mapping[str, Any], ...]
    drafts: tuple[DynastyDraftRecord, ...]
    round_count_baseline: RoundCountBaseline


def _classify_draft(
    *, rounds: int, roster_slot_count: int, rookie_fraction: float | None
) -> str:
    """Real-evidence classification, never a round-count-only guess. See the
    module docstring for the live evidence this is built from."""

    if rookie_fraction is None:
        # No pick-level evidence available (fetch failed / empty) -- fall
        # back to the weaker rounds-vs-roster-slot-count signature only.
        if roster_slot_count and rounds == roster_slot_count:
            return "startup"
        return "unknown"
    if rookie_fraction >= 0.5:
        return "rookie"
    if roster_slot_count and rounds == roster_slot_count:
        return "startup"
    if rookie_fraction < 0.2:
        return "startup"
    return "unknown"


def resolve_round_count_baseline(
    drafts: Sequence[DynastyDraftRecord], *, configured_draft_rounds: int
) -> RoundCountBaseline:
    rookie_drafts = tuple(d for d in drafts if d.classification == "rookie")
    startup_drafts = tuple(d for d in drafts if d.classification == "startup")
    startup_id = startup_drafts[0].draft_id if len(startup_drafts) == 1 else None

    if len(rookie_drafts) == 1:
        chosen = rookie_drafts[0]
        agrees = configured_draft_rounds == chosen.rounds
        fraction_text = (
            f"{chosen.rookie_pick_fraction:.0%}"
            if chosen.rookie_pick_fraction is not None
            else "an unknown fraction of"
        )
        disclosure = (
            f"Resolved from real per-pick evidence: draft {chosen.draft_id} is classified "
            f"as this league's recurring annual ROOKIE draft ({chosen.rounds} rounds, "
            f"{fraction_text} of its picks were real rookies by years_exp==0). "
        )
        if startup_id:
            disclosure += (
                f"A separate one-time STARTUP draft ({startup_id}, "
                f"{startup_drafts[0].rounds} rounds) was found and correctly excluded from "
                "future-season projection. "
            )
        if agrees:
            disclosure += (
                "This matches the league's own currently-configured "
                f"settings.draft_rounds ({configured_draft_rounds})."
            )
        else:
            disclosure += (
                "NOTE: this disagrees with the league's own currently-configured "
                f"settings.draft_rounds ({configured_draft_rounds}); the real, classified "
                "value is used because it is more directly evidenced, but the disagreement "
                "is disclosed here rather than silently resolved."
            )
        return RoundCountBaseline(
            rounds=chosen.rounds,
            source="rookie_draft_classified",
            disclosure=disclosure,
            startup_draft_id=startup_id,
            rookie_draft_ids=(chosen.draft_id,),
            ambiguous=False,
        )

    unknown_count = len(drafts) - len(rookie_drafts) - len(startup_drafts)
    return RoundCountBaseline(
        rounds=configured_draft_rounds,
        source="configured_draft_rounds_fallback",
        disclosure=(
            "Could not classify exactly one real recurring rookie draft from this league's "
            f"draft history ({len(rookie_drafts)} classified 'rookie', {len(startup_drafts)} "
            f"classified 'startup', {unknown_count} 'unknown'); falling back to the league's "
            f"own currently-configured settings.draft_rounds ({configured_draft_rounds}) for "
            "future-season pick-capital projection. This is a disclosed fallback, not a "
            "resolved fact -- a human should confirm it before relying on future-season "
            "pick counts."
        ),
        startup_draft_id=startup_id,
        rookie_draft_ids=tuple(d.draft_id for d in rookie_drafts),
        ambiguous=True,
    )


def fetch_dynasty_league_snapshot(
    league_id: str,
    *,
    client: SleeperHttpClient | None = None,
    fetch_draft_picks: bool = True,
) -> DynastyLeagueSnapshot:
    """Real, read-only (GET-only) fetch of one Sleeper dynasty league's
    current state: league settings/scoring (stored verbatim -- never
    reinterpreted as PPR/standard), every roster, the user/team-name map,
    every traded-pick delta record, and every draft (classified per the
    module docstring). `client` defaults to a fresh `SleeperHttpClient()`
    (unmodified, GET-only by construction); pass one in to reuse an
    existing client or to point at a test double.
    """

    http = client or SleeperHttpClient()
    league = http.get_json(f"league/{league_id}")
    if not isinstance(league, Mapping):
        raise DynastyLeagueFetchError(
            f"Sleeper league {league_id} did not return a valid league object."
        )
    rosters_raw = http.get_json(f"league/{league_id}/rosters")
    users_raw = http.get_json(f"league/{league_id}/users")
    traded_picks_raw = http.get_json(f"league/{league_id}/traded_picks")
    drafts_raw = http.get_json(f"league/{league_id}/drafts")

    settings_block = league.get("settings") if isinstance(league.get("settings"), Mapping) else {}
    scoring_settings = dict(league.get("scoring_settings") or {})
    roster_positions = tuple(str(p) for p in (league.get("roster_positions") or []))

    settings = DynastyLeagueSettings(
        league_id=_safe_str(league.get("league_id")) or str(league_id),
        name=_safe_str(league.get("name")),
        season=_safe_str(league.get("season")),
        status=_safe_str(league.get("status")),
        num_teams=_safe_int(settings_block.get("num_teams") or league.get("total_rosters")),
        scoring_settings=scoring_settings,
        roster_positions=roster_positions,
        taxi_slots=_safe_int(settings_block.get("taxi_slots")),
        reserve_slots=_safe_int(settings_block.get("reserve_slots")),
        playoff_teams=_safe_int(settings_block.get("playoff_teams")),
        playoff_week_start=_safe_int(settings_block.get("playoff_week_start")),
        trade_deadline=_safe_int(settings_block.get("trade_deadline")),
        pick_trading=_safe_int(settings_block.get("pick_trading")),
        waiver_type=_safe_int(settings_block.get("waiver_type")),
        waiver_budget=_safe_int(settings_block.get("waiver_budget")),
        max_keepers=_safe_int(settings_block.get("max_keepers")),
        configured_draft_rounds=_safe_int(settings_block.get("draft_rounds")),
    )

    team_names = team_name_by_roster_id(rosters_raw, users_raw)
    rosters: list[DynastyRosterEntry] = []
    owner_by_roster: dict[int, str] = {}
    roster_by_owner: dict[str, int] = {}
    if isinstance(rosters_raw, list):
        for raw in rosters_raw:
            if not isinstance(raw, Mapping):
                continue
            roster_id = _safe_int(raw.get("roster_id"))
            owner_id = _safe_str(raw.get("owner_id"))
            roster_settings = raw.get("settings") if isinstance(raw.get("settings"), Mapping) else {}
            entry = DynastyRosterEntry(
                roster_id=roster_id,
                owner_id=owner_id,
                co_owners=_safe_str_tuple(raw.get("co_owners")),
                team_name=team_names.get(roster_id) or f"Roster {roster_id}",
                players=_safe_str_tuple(raw.get("players")),
                starters=_safe_str_tuple(raw.get("starters")),
                reserve=_safe_str_tuple(raw.get("reserve")),
                taxi=_safe_str_tuple(raw.get("taxi")),
                wins=_safe_int(roster_settings.get("wins")),
                losses=_safe_int(roster_settings.get("losses")),
                ties=_safe_int(roster_settings.get("ties")),
                fpts=_safe_float(roster_settings.get("fpts"))
                + _safe_float(roster_settings.get("fpts_decimal")) / 100.0,
                ppts=_safe_float(roster_settings.get("ppts"))
                + _safe_float(roster_settings.get("ppts_decimal")) / 100.0,
            )
            rosters.append(entry)
            if owner_id:
                owner_by_roster[roster_id] = owner_id
                roster_by_owner[owner_id] = roster_id

    traded_picks = (
        tuple(dict(record) for record in traded_picks_raw if isinstance(record, Mapping))
        if isinstance(traded_picks_raw, list)
        else ()
    )

    drafts: list[DynastyDraftRecord] = []
    if isinstance(drafts_raw, list):
        for raw in drafts_raw:
            if not isinstance(raw, Mapping):
                continue
            draft_id = _safe_str(raw.get("draft_id"))
            draft_settings = raw.get("settings") if isinstance(raw.get("settings"), Mapping) else {}
            rounds = _safe_int(draft_settings.get("rounds"))
            pick_count = 0
            rookie_fraction: float | None = None
            if fetch_draft_picks and draft_id:
                try:
                    picks = http.get_json(f"draft/{draft_id}/picks")
                except (OSError, ValueError):
                    picks = None
                if isinstance(picks, list) and picks:
                    pick_count = len(picks)
                    rookie_count = sum(
                        1
                        for pick in picks
                        if isinstance(pick, Mapping)
                        and isinstance(pick.get("metadata"), Mapping)
                        and _safe_str(pick["metadata"].get("years_exp")) == "0"
                    )
                    rookie_fraction = rookie_count / pick_count
            classification = _classify_draft(
                rounds=rounds,
                roster_slot_count=len(roster_positions),
                rookie_fraction=rookie_fraction,
            )
            drafts.append(
                DynastyDraftRecord(
                    draft_id=draft_id,
                    status=_safe_str(raw.get("status")),
                    draft_type=_safe_str(raw.get("type")),
                    season=_safe_str(raw.get("season")),
                    rounds=rounds,
                    start_time=_safe_optional_int(raw.get("start_time")),
                    created=_safe_optional_int(raw.get("created")),
                    pick_count=pick_count,
                    rookie_pick_fraction=rookie_fraction,
                    classification=classification,
                )
            )

    baseline = resolve_round_count_baseline(
        tuple(drafts), configured_draft_rounds=settings.configured_draft_rounds
    )

    return DynastyLeagueSnapshot(
        league_id=settings.league_id,
        fetched_at_utc=utc_now(),
        settings=settings,
        rosters=tuple(rosters),
        owner_id_by_roster_id=owner_by_roster,
        roster_id_by_owner_id=roster_by_owner,
        traded_picks=traded_picks,
        drafts=tuple(drafts),
        round_count_baseline=baseline,
    )


# --------------------------------------------------------------------------
# Pick-capital reconciliation
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PickOwnership:
    season: str
    round: int
    original_roster_id: int
    current_roster_id: int
    current_owner_id: str | None
    traded: bool
    round_source: str


def _actual_rounds_by_season(
    drafts: Sequence[DynastyDraftRecord],
) -> dict[str, int]:
    """A season's REAL completed-draft round count, preferring a
    non-"startup"-classified draft (i.e. the recurring/rookie draft) over a
    one-time startup draft when a season genuinely has both, exactly the
    same real-evidence preference `resolve_round_count_baseline` uses for
    future seasons -- see the module docstring."""

    by_season: dict[str, list[DynastyDraftRecord]] = {}
    for draft in drafts:
        if draft.status == "complete" and draft.season and draft.rounds:
            by_season.setdefault(draft.season, []).append(draft)
    resolved: dict[str, int] = {}
    for season, records in by_season.items():
        non_startup = [d for d in records if d.classification != "startup"]
        chosen = non_startup[0] if non_startup else records[0]
        resolved[season] = chosen.rounds
    return resolved


def resolve_owned_pick_capital(
    league_snapshot: DynastyLeagueSnapshot,
    *,
    seasons: Sequence[str] | None = None,
) -> dict[int, tuple[PickOwnership, ...]]:
    """Reconciles Sleeper's `traded_picks` delta list -- which only ever
    lists picks that have moved AT LEAST ONCE from their original owner,
    per Sleeper's own API contract -- against the implicit baseline "every
    roster owns exactly one pick per round of that season's real round
    count" to compute each roster's real, total, current owned-pick
    capital for every requested season. A season with its own real
    completed draft in `league_snapshot.drafts` uses that draft's real
    round count (never the baseline projection); a season with no
    completed draft yet (a genuine future season) uses
    `league_snapshot.round_count_baseline` -- see
    `resolve_round_count_baseline`'s docstring for how that baseline
    itself resolves this league's real startup-vs-rookie-draft ambiguity.
    Every result row discloses which source applied via `round_source`.
    Malformed `traded_picks` records (missing/non-integer round, season,
    roster_id, or owner_id) are skipped, never guessed at or crashed on.
    """

    roster_ids = sorted({roster.roster_id for roster in league_snapshot.rosters})
    target_seasons = tuple(seasons) if seasons is not None else DEFAULT_PICK_CAPITAL_SEASONS

    delta_index: dict[tuple[int, int, str], int] = {}
    for record in league_snapshot.traded_picks:
        try:
            key = (
                int(record["roster_id"]),
                int(record["round"]),
                str(record["season"]),
            )
            delta_index[key] = int(record["owner_id"])
        except (KeyError, TypeError, ValueError):
            continue

    actual_rounds = _actual_rounds_by_season(league_snapshot.drafts)
    result: dict[int, list[PickOwnership]] = {roster_id: [] for roster_id in roster_ids}
    for season in target_seasons:
        if season in actual_rounds:
            rounds = actual_rounds[season]
            round_source = "actual_draft"
        else:
            rounds = league_snapshot.round_count_baseline.rounds
            round_source = "baseline_projection"
        for original_roster_id in roster_ids:
            for round_number in range(1, rounds + 1):
                key = (original_roster_id, round_number, season)
                current_roster_id = delta_index.get(key, original_roster_id)
                traded = key in delta_index
                owner_id = league_snapshot.owner_id_by_roster_id.get(current_roster_id)
                result.setdefault(current_roster_id, []).append(
                    PickOwnership(
                        season=season,
                        round=round_number,
                        original_roster_id=original_roster_id,
                        current_roster_id=current_roster_id,
                        current_owner_id=owner_id,
                        traded=traded,
                        round_source=round_source,
                    )
                )
    return {roster_id: tuple(rows) for roster_id, rows in result.items()}


# --------------------------------------------------------------------------
# Ownership annotation -- pure join, never touches score/rank/value
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _RosterMatch:
    roster_id: int
    owner_id: str
    team_name: str
    slot_status: str


def _index_rosters_by_player_id(
    rosters: Sequence[DynastyRosterEntry],
) -> dict[str, _RosterMatch]:
    index: dict[str, _RosterMatch] = {}
    for roster in rosters:
        taxi = set(roster.taxi)
        reserve = set(roster.reserve)
        starters = set(roster.starters)
        for player_id in roster.players:
            if player_id in taxi:
                slot_status = "taxi"
            elif player_id in reserve:
                slot_status = "reserve"
            elif player_id in starters:
                slot_status = "starter"
            else:
                slot_status = "bench"
            index[player_id] = _RosterMatch(
                roster_id=roster.roster_id,
                owner_id=roster.owner_id,
                team_name=roster.team_name,
                slot_status=slot_status,
            )
    return index


def annotate_ownership(
    asset_rows: Sequence[Mapping[str, Any]],
    league_snapshot: DynastyLeagueSnapshot,
    *,
    my_owner_id: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Pure join, no scoring. `asset_rows` items need only carry an
    `asset_id` (or `assetId`) key using the governed board's own asset-ID
    convention (`current:{sleeper_player_id}`, `rookie:{synthetic_id}`,
    `blocked-rookie:{slug}`, ...); every other field is ignored, and this
    function never reads, writes, or returns any score/rank/value field.

    Returns `{asset_id: ownership_dict}` only for asset IDs this function
    can make an HONEST determination for:
    - `current:*` -- direct Sleeper-ID join (Worker 1 confirmed the
      governed board's current-player asset IDs are the literal Sleeper
      player ID with no crosswalk needed): `OWNED` (with roster/team/slot
      context) or `FREE_AGENT` (matched no roster in this league).
    - `rookie:*` / `blocked-rookie:*` -- always `UNRESOLVED`: the rookie
      board's own asset IDs use a separate synthetic identity scheme (see
      `owner_asset_evidence_service._asset_player_id`), not a Sleeper
      numeric ID, so no live join is possible yet. This is a real, honest
      status, not a silent omission -- a caller can show "ownership
      unknown for this rookie asset" instead of nothing.

    Asset types this function has no ownership concept for at all (e.g.
    `pick:*` / `future-pick:*` -- draft-pick capital is a separate,
    roster-scoped structure, see `resolve_owned_pick_capital`) are simply
    absent from the returned mapping -- never guessed, never defaulted.
    """

    roster_index = _index_rosters_by_player_id(league_snapshot.rosters)
    result: dict[str, dict[str, Any]] = {}
    for row in asset_rows:
        asset_id = _safe_str(row.get("asset_id") if "asset_id" in row else row.get("assetId"))
        if not asset_id or asset_id in result:
            continue
        if asset_id.startswith("current:"):
            sleeper_player_id = asset_id.removeprefix("current:")
            match = roster_index.get(sleeper_player_id)
            if match is None:
                result[asset_id] = {
                    "ownershipStatus": "FREE_AGENT",
                    "rosterId": None,
                    "rosterTeamName": None,
                    "rosterSlotStatus": None,
                    "isMyTeam": False,
                    "reason": "",
                }
            else:
                result[asset_id] = {
                    "ownershipStatus": "OWNED",
                    "rosterId": match.roster_id,
                    "rosterTeamName": match.team_name,
                    "rosterSlotStatus": match.slot_status,
                    "isMyTeam": bool(my_owner_id) and match.owner_id == my_owner_id,
                    "reason": "",
                }
        elif asset_id.startswith(("rookie:", "blocked-rookie:")):
            result[asset_id] = {
                "ownershipStatus": "UNRESOLVED",
                "rosterId": None,
                "rosterTeamName": None,
                "rosterSlotStatus": None,
                "isMyTeam": False,
                "reason": UNRESOLVED_ROOKIE_OWNERSHIP_REASON,
            }
        # else: Draft Pick / Future Pick / any other asset type -- no
        # ownership concept in this function; intentionally left absent.
    return result


# --------------------------------------------------------------------------
# Persistence -- local_exports/dynasty_v1/, follows Redraft's own
# `redraft_engine_v1_service.redraft_store_root`/profile-store convention.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DynastyLeagueProfile:
    profile_id: str
    league_id: str
    league_name: str
    season: str
    num_teams: int
    scoring_settings: Mapping[str, Any]
    roster_positions: tuple[str, ...]
    taxi_slots: int
    reserve_slots: int
    playoff_teams: int
    playoff_week_start: int
    trade_deadline: int
    pick_trading: int
    waiver_type: int
    waiver_budget: int
    max_keepers: int
    my_owner_id: str | None
    my_roster_id: int | None
    schema_version: int
    created_at_utc: str
    updated_at_utc: str


@dataclass(frozen=True)
class DynastyPersistedSnapshot:
    profile_id: str
    fetched_at_utc: str
    league_snapshot: DynastyLeagueSnapshot
    pick_capital_by_roster_id: Mapping[int, tuple[PickOwnership, ...]]
    schema_version: int


@dataclass(frozen=True)
class DynastyLeagueImportResult:
    profile: DynastyLeagueProfile
    league_snapshot: DynastyLeagueSnapshot
    pick_capital_by_roster_id: Mapping[int, tuple[PickOwnership, ...]]
    snapshot_path: Path


def dynasty_league_store_root(repo_root: str | Path | None = None) -> Path:
    configured = os.environ.get("NWR_DYNASTY_LEAGUE_HOME", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    base = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[2]
    return base / "local_exports" / "dynasty_v1"


def _safe_profile_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(value or "").strip())
    if not safe:
        raise DynastyLeaguePersistenceError(
            "Dynasty league profile id must contain at least one safe character."
        )
    return safe


def _profile_path(root: Path, profile_id: str) -> Path:
    return root / "league_profiles" / f"{_safe_profile_id(profile_id)}.json"


def _snapshot_dir(root: Path, profile_id: str) -> Path:
    return root / "league_snapshots" / _safe_profile_id(profile_id)


def _atomic_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.{utc_snapshot_stamp()}.tmp")
    try:
        temp_path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temp_path, path)
    except OSError as exc:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise DynastyLeaguePersistenceError(
            f"Could not persist dynasty league state: {exc}"
        ) from exc


def save_league_profile(
    root: str | Path,
    league_snapshot: DynastyLeagueSnapshot,
    *,
    my_owner_id: str | None = None,
    profile_id: str | None = None,
) -> DynastyLeagueProfile:
    root_path = Path(root)
    resolved_profile_id = _safe_profile_id(profile_id or league_snapshot.league_id)
    path = _profile_path(root_path, resolved_profile_id)
    now = utc_now()
    created_at = now
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            created_at = str(existing.get("created_at_utc") or now)
        except (OSError, json.JSONDecodeError, TypeError):
            created_at = now
    my_roster_id = (
        league_snapshot.roster_id_by_owner_id.get(my_owner_id) if my_owner_id else None
    )
    profile = DynastyLeagueProfile(
        profile_id=resolved_profile_id,
        league_id=league_snapshot.league_id,
        league_name=league_snapshot.settings.name,
        season=league_snapshot.settings.season,
        num_teams=league_snapshot.settings.num_teams,
        scoring_settings=dict(league_snapshot.settings.scoring_settings),
        roster_positions=league_snapshot.settings.roster_positions,
        taxi_slots=league_snapshot.settings.taxi_slots,
        reserve_slots=league_snapshot.settings.reserve_slots,
        playoff_teams=league_snapshot.settings.playoff_teams,
        playoff_week_start=league_snapshot.settings.playoff_week_start,
        trade_deadline=league_snapshot.settings.trade_deadline,
        pick_trading=league_snapshot.settings.pick_trading,
        waiver_type=league_snapshot.settings.waiver_type,
        waiver_budget=league_snapshot.settings.waiver_budget,
        max_keepers=league_snapshot.settings.max_keepers,
        my_owner_id=my_owner_id,
        my_roster_id=my_roster_id,
        schema_version=DYNASTY_LEAGUE_SCHEMA_VERSION,
        created_at_utc=created_at,
        updated_at_utc=now,
    )
    _atomic_json(path, asdict(profile))
    return profile


def load_league_profile(root: str | Path, profile_id: str) -> DynastyLeagueProfile:
    path = _profile_path(Path(root), profile_id)
    if not path.is_file():
        raise DynastyLeaguePersistenceError(f"Dynasty league profile not found: {profile_id}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        return DynastyLeagueProfile(
            profile_id=str(doc["profile_id"]),
            league_id=str(doc["league_id"]),
            league_name=str(doc.get("league_name", "")),
            season=str(doc.get("season", "")),
            num_teams=int(doc.get("num_teams", 0)),
            scoring_settings=dict(doc.get("scoring_settings") or {}),
            roster_positions=tuple(str(v) for v in doc.get("roster_positions") or ()),
            taxi_slots=int(doc.get("taxi_slots", 0)),
            reserve_slots=int(doc.get("reserve_slots", 0)),
            playoff_teams=int(doc.get("playoff_teams", 0)),
            playoff_week_start=int(doc.get("playoff_week_start", 0)),
            trade_deadline=int(doc.get("trade_deadline", 0)),
            pick_trading=int(doc.get("pick_trading", 0)),
            waiver_type=int(doc.get("waiver_type", 0)),
            waiver_budget=int(doc.get("waiver_budget", 0)),
            max_keepers=int(doc.get("max_keepers", 0)),
            my_owner_id=(str(doc["my_owner_id"]) if doc.get("my_owner_id") else None),
            my_roster_id=(
                int(doc["my_roster_id"]) if doc.get("my_roster_id") is not None else None
            ),
            schema_version=int(doc.get("schema_version", 0)),
            created_at_utc=str(doc.get("created_at_utc", "")),
            updated_at_utc=str(doc.get("updated_at_utc", "")),
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise DynastyLeaguePersistenceError(
            f"Invalid dynasty league profile document: {exc}"
        ) from exc


def _league_snapshot_from_dict(doc: Mapping[str, Any]) -> DynastyLeagueSnapshot:
    settings_doc = doc.get("settings") or {}
    settings = DynastyLeagueSettings(
        league_id=str(settings_doc.get("league_id", "")),
        name=str(settings_doc.get("name", "")),
        season=str(settings_doc.get("season", "")),
        status=str(settings_doc.get("status", "")),
        num_teams=int(settings_doc.get("num_teams", 0)),
        scoring_settings=dict(settings_doc.get("scoring_settings") or {}),
        roster_positions=tuple(str(v) for v in settings_doc.get("roster_positions") or ()),
        taxi_slots=int(settings_doc.get("taxi_slots", 0)),
        reserve_slots=int(settings_doc.get("reserve_slots", 0)),
        playoff_teams=int(settings_doc.get("playoff_teams", 0)),
        playoff_week_start=int(settings_doc.get("playoff_week_start", 0)),
        trade_deadline=int(settings_doc.get("trade_deadline", 0)),
        pick_trading=int(settings_doc.get("pick_trading", 0)),
        waiver_type=int(settings_doc.get("waiver_type", 0)),
        waiver_budget=int(settings_doc.get("waiver_budget", 0)),
        max_keepers=int(settings_doc.get("max_keepers", 0)),
        configured_draft_rounds=int(settings_doc.get("configured_draft_rounds", 0)),
    )
    rosters = tuple(
        DynastyRosterEntry(
            roster_id=int(r.get("roster_id", 0)),
            owner_id=str(r.get("owner_id", "")),
            co_owners=tuple(str(v) for v in r.get("co_owners") or ()),
            team_name=str(r.get("team_name", "")),
            players=tuple(str(v) for v in r.get("players") or ()),
            starters=tuple(str(v) for v in r.get("starters") or ()),
            reserve=tuple(str(v) for v in r.get("reserve") or ()),
            taxi=tuple(str(v) for v in r.get("taxi") or ()),
            wins=int(r.get("wins", 0)),
            losses=int(r.get("losses", 0)),
            ties=int(r.get("ties", 0)),
            fpts=float(r.get("fpts", 0.0)),
            ppts=float(r.get("ppts", 0.0)),
        )
        for r in doc.get("rosters") or ()
    )
    drafts = tuple(
        DynastyDraftRecord(
            draft_id=str(d.get("draft_id", "")),
            status=str(d.get("status", "")),
            draft_type=str(d.get("draft_type", "")),
            season=str(d.get("season", "")),
            rounds=int(d.get("rounds", 0)),
            start_time=_safe_optional_int(d.get("start_time")),
            created=_safe_optional_int(d.get("created")),
            pick_count=int(d.get("pick_count", 0)),
            rookie_pick_fraction=(
                float(d["rookie_pick_fraction"])
                if d.get("rookie_pick_fraction") is not None
                else None
            ),
            classification=str(d.get("classification", "unknown")),
        )
        for d in doc.get("drafts") or ()
    )
    baseline_doc = doc.get("round_count_baseline") or {}
    baseline = RoundCountBaseline(
        rounds=int(baseline_doc.get("rounds", 0)),
        source=str(baseline_doc.get("source", "")),
        disclosure=str(baseline_doc.get("disclosure", "")),
        startup_draft_id=(
            str(baseline_doc["startup_draft_id"]) if baseline_doc.get("startup_draft_id") else None
        ),
        rookie_draft_ids=tuple(str(v) for v in baseline_doc.get("rookie_draft_ids") or ()),
        ambiguous=bool(baseline_doc.get("ambiguous", False)),
    )
    owner_by_roster = {int(k): str(v) for k, v in (doc.get("owner_id_by_roster_id") or {}).items()}
    roster_by_owner = {
        str(k): int(v) for k, v in (doc.get("roster_id_by_owner_id") or {}).items()
    }
    traded_picks = tuple(dict(r) for r in doc.get("traded_picks") or ())
    return DynastyLeagueSnapshot(
        league_id=str(doc.get("league_id", "")),
        fetched_at_utc=str(doc.get("fetched_at_utc", "")),
        settings=settings,
        rosters=rosters,
        owner_id_by_roster_id=owner_by_roster,
        roster_id_by_owner_id=roster_by_owner,
        traded_picks=traded_picks,
        drafts=drafts,
        round_count_baseline=baseline,
    )


def save_league_snapshot(
    root: str | Path,
    profile_id: str,
    league_snapshot: DynastyLeagueSnapshot,
    pick_capital_by_roster_id: Mapping[int, Sequence[PickOwnership]],
) -> Path:
    root_path = Path(root)
    resolved_profile_id = _safe_profile_id(profile_id)
    filename = utc_snapshot_stamp() + ".json"
    path = _snapshot_dir(root_path, resolved_profile_id) / filename
    document = {
        "schema_version": DYNASTY_LEAGUE_SCHEMA_VERSION,
        "profile_id": resolved_profile_id,
        "fetched_at_utc": league_snapshot.fetched_at_utc,
        "league_snapshot": asdict(league_snapshot),
        "pick_capital_by_roster_id": {
            str(roster_id): [asdict(row) for row in rows]
            for roster_id, rows in pick_capital_by_roster_id.items()
        },
    }
    _atomic_json(path, document)
    return path


def load_latest_league_snapshot(
    root: str | Path, profile_id: str
) -> DynastyPersistedSnapshot | None:
    directory = _snapshot_dir(Path(root), profile_id)
    if not directory.is_dir():
        return None
    files = sorted(path for path in directory.glob("*.json") if not path.name.startswith("."))
    if not files:
        return None
    latest = files[-1]
    try:
        doc = json.loads(latest.read_text(encoding="utf-8"))
        league_snapshot = _league_snapshot_from_dict(doc.get("league_snapshot") or {})
        pick_capital = {
            int(roster_id): tuple(PickOwnership(**row) for row in rows)
            for roster_id, rows in (doc.get("pick_capital_by_roster_id") or {}).items()
        }
        return DynastyPersistedSnapshot(
            profile_id=str(doc.get("profile_id", profile_id)),
            fetched_at_utc=str(doc.get("fetched_at_utc", "")),
            league_snapshot=league_snapshot,
            pick_capital_by_roster_id=pick_capital,
            schema_version=int(doc.get("schema_version", 0)),
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise DynastyLeaguePersistenceError(
            f"Invalid dynasty league snapshot document ({latest.name}): {exc}"
        ) from exc


def import_dynasty_league(
    league_id: str,
    root: str | Path,
    *,
    client: SleeperHttpClient | None = None,
    my_owner_id: str | None = None,
    profile_id: str | None = None,
    seasons: Sequence[str] | None = None,
) -> DynastyLeagueImportResult:
    """End-to-end orchestration: real fetch -> real pick-capital
    reconciliation -> persist (profile + a new timestamped snapshot).
    This is the one function `desktop_facade.import_dynasty_sleeper_league`
    delegates to; kept here, not in the facade, so it is directly testable
    without an HTTP server."""

    league_snapshot = fetch_dynasty_league_snapshot(league_id, client=client)
    pick_capital = resolve_owned_pick_capital(league_snapshot, seasons=seasons)
    profile = save_league_profile(
        root, league_snapshot, my_owner_id=my_owner_id, profile_id=profile_id
    )
    snapshot_path = save_league_snapshot(
        root, profile.profile_id, league_snapshot, pick_capital
    )
    return DynastyLeagueImportResult(
        profile=profile,
        league_snapshot=league_snapshot,
        pick_capital_by_roster_id=pick_capital,
        snapshot_path=snapshot_path,
    )
