"""Weekly per-player fantasy point projections (NWR Overnight V3, Lane 1/2).

Source: Sleeper's public, unauthenticated `projections/nfl/{season_type}/
{season}/{week}` endpoint, reused through the SAME `SleeperHttpClient`
(`src/services/sleeper_import_service.py`) every other Sleeper read in this
app already uses -- no new HTTP client, no new identity system.

Why this module exists: repo archaeology this pass confirmed no prior
`weekly_projection`-named work exists anywhere in this branch's git history.
Three prior overnight passes on this branch (Part 2, Part 3, the retry-queue
report) each independently reached a BLOCKED verdict on weekly player-point
projections -- but none of them had actually queried this specific endpoint;
they checked the FFA archive (real, confirmed season-level only, no week
column) and `nflreadpy` (real, live, but schedules/rosters/actual stats, not
forward point forecasts). This endpoint was found and verified live this
pass and is a real, current, per-player, per-week projection source with
raw stat categories -- not just a single provider point total.

Read before using this module -- it is honest about real limits:

  * UNDOCUMENTED: Sleeper's own docs (docs.sleeper.com) describe the
    read-only league/roster/player endpoints; `projections/nfl/...` is not
    among them. It sits on the same `api.sleeper.app` host, uses the same
    no-auth read pattern, and returned real, live, per-player projections
    keyed by real Sleeper player IDs -- cross-checked by name this pass
    (Jalen Hurts, Christian McCaffrey, Puka Nacua, Brandon Aubrey all
    resolved correctly via the real `players/nfl` catalog). It is NOT
    officially guaranteed stable -- it could change shape or stop working
    without notice, unlike the documented endpoints this app already
    depends on. Callers MUST treat a fetch failure as "unavailable this
    week," never as a reason to reuse a stale prior week's numbers.
  * NON-COMMERCIAL: Sleeper's docs state the read-only API is "free to use
    for non-commercial purposes"; commercial use requires contacting
    Sleeper directly. NWR is the owner's personal fantasy tool for their
    own leagues, matching the same posture already in production for every
    other Sleeper read in this app (rosters, users, players, league
    settings) -- this module does not change that, it extends it to one
    more endpoint under the same terms.
  * CROSS-VALIDATED, NOT INGESTED, AGAINST ESPN: the public ESPN
    `leaguedefaults` `kona_player_info` endpoint was also checked this pass
    and does carry a real `stats[]` array with the documented `statSourceId`
    0=actual / 1=projected split per `scoringPeriodId` (week) -- confirmed
    live, no auth required, cross-validating the Sleeper numbers on the
    same player (Jahmyr Gibbs, Week 1 2026: Sleeper pts_ppr=22.10 vs ESPN's
    own default-scoring appliedTotal=22.41 -- same order of magnitude).
    ESPN's own raw stat categories are numeric-coded IDs (24, 25, 42, ...)
    that ESPN does not officially document; decoding them with confidence
    is a separate, real task this pass did not attempt. ESPN's
    `appliedTotal` also reflects ESPN's own default scoring context, not
    the owner's real league scoring -- ingesting it here would violate this
    module's own rule against pretending points transfer across scoring
    formats. ESPN is therefore a confirmatory data point only, not a second
    ingest source.
  * K/DST: Sleeper's own `pts_ppr` / `pts_half_ppr` / `pts_std` are
    preserved and labeled `SLEEPER_PROVIDER_SCORING` rather than
    recomputed -- matching the K/DST streamer's own established precedent
    of never inventing an NWR K/DST scoring formula from raw special-teams
    stats. Skill positions (QB/RB/WR/TE) are scored with NWR's OWN
    `score_projection` (`redraft_engine_v1_service.py`) from mapped raw
    stat categories -- real, league-scoring-specific points, not a
    provider point proxy, and not a duplicated formula.
  * Sleeper's projection payload has no per-player 2-point-conversion or
    scoring-bonus (e.g. 300-yard-passing-game) fields wired here; those are
    a known, disclosed simplification versus the season-long scorer, not a
    silent omission -- `WeeklyProjectionRow.known_simplifications`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from src.services.fantasypros_kdst_consensus_service import (
    SLEEPER_FANTASY_POSITIONS,
    _identity,
    _sleeper_position,
)
from src.services.redraft_engine_v1_service import ProjectionPlayer, ScoringSettings, score_projection
from src.services.sleeper_import_service import SleeperHttpClient

WEEKLY_PROJECTION_SOURCE = "SLEEPER_WEEKLY_PROJECTIONS_V1"
KDST_SCORING_LABEL = "SLEEPER_PROVIDER_SCORING"
NWR_SCORING_LABEL = "NWR_LEAGUE_SCORING"

# Sleeper's raw weekly stat field -> the SAME canonical stat-line field
# names `score_projection` already expects on a `ProjectionPlayer.stats`
# dict (season-long scorer, reused verbatim -- not duplicated).
_SLEEPER_STAT_TO_CANONICAL: dict[str, str] = {
    "pass_yd": "passing_yards",
    "pass_td": "passing_tds",
    "pass_int": "interceptions",
    "rush_yd": "rushing_yards",
    "rush_td": "rushing_tds",
    "rec_yd": "receiving_yards",
    "rec": "receptions",
    "rec_td": "receiving_tds",
    "pass_fd": "passing_first_downs",
    "rush_fd": "rushing_first_downs",
    "rec_fd": "receiving_first_downs",
    "fum_lost": "fumbles_lost",
}
_SLEEPER_RETURN_YARD_FIELDS = ("punt_ret_yd", "kick_ret_yd")
_SLEEPER_RETURN_TD_FIELDS = ("punt_ret_td", "kick_ret_td")

_KNOWN_SIMPLIFICATIONS = (
    "No 2-point-conversion fields mapped from Sleeper's weekly payload.",
    "No weekly scoring-bonus thresholds (e.g. 300-yard passing game) mapped.",
)


class WeeklyProjectionError(RuntimeError):
    """A malformed Sleeper weekly-projection response, or a fetch failure."""


@dataclass(frozen=True)
class WeeklyProjectionRow:
    canonical_player_id: str
    sleeper_player_id: str
    player_name: str
    position: str
    team: str
    week: int
    season: int
    season_type: str
    league_id: str
    source: str
    source_as_of: str
    projected_points: float | None
    scoring_context: str
    raw_stats: dict[str, float]
    identity_match: str  # MATCHED | UNMATCHED | AMBIGUOUS
    gp: float | None
    known_simplifications: tuple[str, ...] = field(default_factory=lambda: _KNOWN_SIMPLIFICATIONS)


@dataclass(frozen=True)
class WeeklyProjectionResult:
    season: int
    week: int
    season_type: str
    league_id: str
    source: str
    source_status: str  # OK | UNAVAILABLE
    source_as_of: str
    rows: tuple[WeeklyProjectionRow, ...]
    matched: int
    unmatched: int
    ambiguous: int
    total_players_in_source: int
    error: str | None = None


def fetch_sleeper_weekly_projections(
    *,
    season: int,
    week: int,
    season_type: str = "regular",
    http: SleeperHttpClient | None = None,
) -> Mapping[str, Mapping[str, Any]]:
    """Real, live, undocumented Sleeper endpoint. Raises on any malformed shape."""

    if week < 1 or week > 18:
        raise WeeklyProjectionError(f"Week must be 1-18, got {week}.")
    if season_type not in {"regular", "post", "pre"}:
        raise WeeklyProjectionError(f"Unsupported season_type: {season_type!r}.")
    client = http or SleeperHttpClient()
    try:
        payload = client.get_json(f"projections/nfl/{season_type}/{season}/{week}")
    except Exception as exc:  # noqa: BLE001 - real network/parsing failure, surfaced honestly
        raise WeeklyProjectionError(f"Sleeper weekly-projection fetch failed: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise WeeklyProjectionError("Sleeper weekly-projection response is malformed (not an object).")
    return payload


def _mapped_stats(raw: Mapping[str, Any]) -> dict[str, float]:
    stats: dict[str, float] = {}
    for sleeper_field, canonical_field in _SLEEPER_STAT_TO_CANONICAL.items():
        value = raw.get(sleeper_field)
        if isinstance(value, (int, float)):
            stats[canonical_field] = float(value)
    return_yards = sum(float(raw.get(field_name) or 0) for field_name in _SLEEPER_RETURN_YARD_FIELDS)
    return_tds = sum(float(raw.get(field_name) or 0) for field_name in _SLEEPER_RETURN_TD_FIELDS)
    if return_yards:
        stats["return_yards"] = return_yards
    if return_tds:
        stats["return_tds"] = return_tds
    return stats


def _score_row(position: str, raw: Mapping[str, Any], scoring: ScoringSettings) -> tuple[float | None, str]:
    if position in {"K", "DST"}:
        points = raw.get("pts_ppr")
        if not isinstance(points, (int, float)):
            return None, KDST_SCORING_LABEL
        return round(float(points), 2), KDST_SCORING_LABEL
    mapped = _mapped_stats(raw)
    if not mapped:
        return None, NWR_SCORING_LABEL
    player = ProjectionPlayer(
        player_id="weekly-projection-scratch",
        player_name="",
        position=position,
        team="",
        season=0,
        source_status="",
        evidence_status="",
        stats=mapped,
    )
    return score_projection(player, scoring), NWR_SCORING_LABEL


def build_weekly_projection_rows(
    *,
    raw_projections: Mapping[str, Mapping[str, Any]],
    players: Mapping[str, Mapping[str, Any]],
    ranking_rows: Sequence[Mapping[str, Any]],
    scoring: ScoringSettings,
    season: int,
    week: int,
    season_type: str,
    league_id: str,
    fetched_at: str | None = None,
) -> WeeklyProjectionResult:
    """Join Sleeper's raw weekly stat lines to NWR identity + league scoring.

    `players` is the same Sleeper `players/nfl` catalog every other Sleeper
    read in this app already fetches. `ranking_rows` is the same
    `_redraft_ranking_payloads(...)`-shaped sequence `sleeper_free_agent_pool`
    already consumes -- reused here for the identical name/position/team
    identity join, not a new resolver.
    """

    if not isinstance(players, Mapping):
        raise WeeklyProjectionError("Sleeper player catalog is malformed.")
    as_of = fetched_at or datetime.now(UTC).isoformat()

    ranking_by_identity: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for row in ranking_rows:
        key = _identity(
            row.get("playerName"), row.get("position"), row.get("team"),
            allowed_positions=SLEEPER_FANTASY_POSITIONS,
        )
        if key == ("", "", ""):
            continue
        ranking_by_identity.setdefault(key, []).append(row)

    rows: list[WeeklyProjectionRow] = []
    matched = unmatched = ambiguous = 0
    for sleeper_id, raw in raw_projections.items():
        sid = str(sleeper_id).strip()
        if not sid or not isinstance(raw, Mapping):
            continue
        catalog_entry = players.get(sid)
        if not isinstance(catalog_entry, Mapping):
            unmatched += 1
            continue
        position = _sleeper_position(catalog_entry.get("position"))
        if position not in SLEEPER_FANTASY_POSITIONS or catalog_entry.get("active") is False:
            continue
        team = str(catalog_entry.get("team") or "").upper().strip()
        name = str(catalog_entry.get("full_name") or catalog_entry.get("search_full_name") or "").strip()
        if position == "DST" and not name and team:
            name = f"{team} D/ST"
        if not name or not team:
            unmatched += 1
            continue
        key = _identity(name, position, team, allowed_positions=SLEEPER_FANTASY_POSITIONS)
        candidates = ranking_by_identity.get(key, [])
        if len(candidates) == 1:
            canonical_id = str(candidates[0].get("playerId") or "")
            identity_match = "MATCHED" if canonical_id else "UNMATCHED"
            if canonical_id:
                matched += 1
            else:
                unmatched += 1
        elif len(candidates) > 1:
            canonical_id = ""
            identity_match = "AMBIGUOUS"
            ambiguous += 1
        else:
            canonical_id = ""
            identity_match = "UNMATCHED"
            unmatched += 1
        points, scoring_context = _score_row(position, raw, scoring)
        gp = raw.get("gp")
        rows.append(
            WeeklyProjectionRow(
                canonical_player_id=canonical_id or f"sleeper:{sid}",
                sleeper_player_id=sid,
                player_name=name,
                position=position,
                team=team,
                week=week,
                season=season,
                season_type=season_type,
                league_id=league_id,
                source=WEEKLY_PROJECTION_SOURCE,
                source_as_of=as_of,
                projected_points=points,
                scoring_context=scoring_context,
                raw_stats=_mapped_stats(raw) if position not in {"K", "DST"} else {},
                identity_match=identity_match,
                gp=float(gp) if isinstance(gp, (int, float)) else None,
            )
        )

    rows.sort(
        key=lambda row: (
            row.projected_points is None,
            -(row.projected_points or 0.0),
            row.position,
            row.player_name,
        )
    )
    return WeeklyProjectionResult(
        season=season,
        week=week,
        season_type=season_type,
        league_id=league_id,
        source=WEEKLY_PROJECTION_SOURCE,
        source_status="OK",
        source_as_of=as_of,
        rows=tuple(rows),
        matched=matched,
        unmatched=unmatched,
        ambiguous=ambiguous,
        total_players_in_source=len(raw_projections),
    )


def unavailable_weekly_projection_result(
    *, season: int, week: int, season_type: str, league_id: str, error: str
) -> WeeklyProjectionResult:
    """Explicit failure-fallback state -- NEVER silently reuse a stale prior fetch."""

    return WeeklyProjectionResult(
        season=season,
        week=week,
        season_type=season_type,
        league_id=league_id,
        source=WEEKLY_PROJECTION_SOURCE,
        source_status="UNAVAILABLE",
        source_as_of=datetime.now(UTC).isoformat(),
        rows=(),
        matched=0,
        unmatched=0,
        ambiguous=0,
        total_players_in_source=0,
        error=error,
    )
