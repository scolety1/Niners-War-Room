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
# NWR Sunday Readiness overnight cycle, Worker 3 (W7): real, league-exact
# weekly K/DST scoring computed directly from Sleeper's own raw per-stat
# `league.settings.scoring_settings` map (a stat_name -> points_per_unit
# dict -- the SAME field names Sleeper's own weekly-projection raw stat
# payload uses, confirmed by a real live pull this pass) multiplied against
# this row's real raw weekly stat values, wherever both sides genuinely
# match. `KDST_SCORING_LABEL` (generic provider `pts_ppr` passthrough)
# remains the honest fallback when the league's raw scoring map is
# unavailable or has no real K/DST-relevant overlap with the raw stats.
KDST_SCORING_LABEL_EXACT = "NWR_LEAGUE_SCORING_KDST_WEEKLY"
KDST_SCORING_LABEL_PARTIAL = "NWR_LEAGUE_SCORING_KDST_WEEKLY_PARTIAL"

# The real, known Sleeper kicker scoring-category field names (verified this
# pass via a live `GET league/{id}` on both real leagues -- Fantasy Gamers'
# real tiers run fgm_0_19...fgm_60p; Enginerds' real tiers run
# fgm_0_19/20_29/30_39/40_49/50p, with an always-zero redundant fgm_50_59
# key). Sleeper's real weekly-projection payload (verified this pass via a
# live pull) only ever emits fgm_0_19/20_29/30_39/40_49 and xpm/xpmiss as
# discrete raw stat fields -- there is NO raw 50-59/60+ yard field-goal
# breakout anywhere in the projection payload, confirmed by inspecting every
# key across the entire real payload, not just one kicker's row. Any league
# scoring a nonzero 50-59/60+ tier therefore has a real, disclosed gap for
# that tier -- never silently approximated (e.g. by subtracting the other
# tiers from the overall `fgm` total, which would be a fragile, undisclosed
# guess this module explicitly avoids).
_KICKER_KNOWN_SCORING_CATEGORIES: frozenset[str] = frozenset({
    "fgm_0_19", "fgm_20_29", "fgm_30_39", "fgm_40_49", "fgm_50_59", "fgm_50p", "fgm_60p",
    "fgmiss", "fgmiss_0_19", "fgmiss_20_29", "fgmiss_30_39", "fgmiss_40_49", "fgmiss_50p",
    "xpm", "xpmiss",
})
# The real, known Sleeper defense/special-teams scoring-category field
# names, cross-checked against a real live weekly-projection payload for
# multiple real DST rows this pass (sack/int/fum_rec/ff/safe/blk_kick/def_td
# and the real `pts_allow_*` points-allowed tier buckets all confirmed
# present as real raw stat fields).
_DST_KNOWN_SCORING_CATEGORIES: frozenset[str] = frozenset({
    "sack", "int", "fum_rec", "ff", "safe", "blk_kick", "def_td", "def_fum_td",
    "st_td", "pr_td", "kr_td", "pass_int_td", "tkl_loss",
    "pts_allow_0", "pts_allow_1_6", "pts_allow_7_13", "pts_allow_14_20",
    "pts_allow_21_27", "pts_allow_28_34", "pts_allow_35p",
    "yds_allow_0_100", "yds_allow_100_199", "yds_allow_200_299", "yds_allow_300_349",
    "yds_allow_350_399", "yds_allow_400_449", "yds_allow_450_499", "yds_allow_500_549",
    "yds_allow_550p",
})
# A real, live-confirmed Sleeper convention (verified this pass, multiple
# real DST rows): only the ONE points/yards-allowed bucket a team's real
# projection actually lands in appears as a raw stat field at all -- e.g.
# `pts_allow_21_27: 1.0` with no sibling `pts_allow_*` key anywhere on that
# same row, not a "some fields missing" gap. Treating every OTHER
# same-family bucket as individually "unsupported" whenever a league scores
# more than one bucket would be a false-positive disclosure on every real
# DST row. These families are checked for AT-LEAST-ONE-MEMBER-present
# instead: once any one real bucket is confirmed present, every other
# nonzero-weighted member of the SAME family contributes a real, honest
# zero (this team simply did not land in that bucket this week) rather than
# being flagged as a provider gap. A family with ZERO members present at
# all (the provider genuinely never sent this category for this row) is
# still a real, disclosed gap -- one unsupported entry per configured
# member, unchanged.
_DST_MUTUALLY_EXCLUSIVE_FAMILIES: tuple[frozenset[str], ...] = (
    frozenset({
        "pts_allow_0", "pts_allow_1_6", "pts_allow_7_13", "pts_allow_14_20",
        "pts_allow_21_27", "pts_allow_28_34", "pts_allow_35p",
    }),
    frozenset({
        "yds_allow_0_100", "yds_allow_100_199", "yds_allow_200_299", "yds_allow_300_349",
        "yds_allow_350_399", "yds_allow_400_449", "yds_allow_450_499", "yds_allow_500_549",
        "yds_allow_550p",
    }),
)


def _score_kdst_from_raw_sleeper_scoring(
    position: str, raw: Mapping[str, Any], league_scoring_settings: Mapping[str, Any] | None
) -> tuple[float, tuple[str, ...]] | None:
    """Real, league-exact weekly K/DST points computed directly from
    Sleeper's own raw `scoring_settings` map (real per-stat point values)
    multiplied against this row's real raw weekly stat values -- never a
    recomputed/duplicated formula, just a direct real-data dot product.

    Returns `None` (never a fabricated number) when the league's raw
    scoring map is unavailable, or has no real nonzero-weighted category
    that this row's raw stats can actually support -- the caller then falls
    back to the existing generic provider-points passthrough, honestly
    labeled. When a real, partial match exists, returns
    `(points, unsupported_category_names)` -- `unsupported_category_names`
    lists every real, nonzero-weighted league scoring category for this
    position that this row's raw stats do NOT support (e.g. a 50+ yard
    field-goal tier the projection payload never breaks out), so the caller
    can disclose the exact gap rather than silently presenting a partial sum
    as a complete one.
    """

    if not isinstance(league_scoring_settings, Mapping):
        return None
    if position == "K":
        known = _KICKER_KNOWN_SCORING_CATEGORIES
    elif position == "DST":
        known = _DST_KNOWN_SCORING_CATEGORIES
    else:
        return None
    # A key's family is present when ANY of its members has a real raw
    # value on this row -- see `_DST_MUTUALLY_EXCLUSIVE_FAMILIES`'s own
    # docstring. Irrelevant for K (no families defined there).
    families = _DST_MUTUALLY_EXCLUSIVE_FAMILIES if position == "DST" else ()
    family_present: dict[frozenset[str], bool] = {
        family: any(
            isinstance(raw.get(member), (int, float)) and not isinstance(raw.get(member), bool)
            for member in family
        )
        for family in families
    }

    total = 0.0
    matched_any = False
    unsupported: list[str] = []
    for key in sorted(known):
        weight = league_scoring_settings.get(key)
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight == 0:
            continue
        raw_value = raw.get(key)
        if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
            total += float(raw_value) * float(weight)
            matched_any = True
            continue
        owning_family = next((family for family in families if key in family), None)
        if owning_family is not None and family_present.get(owning_family):
            # A real sibling bucket in the same family IS present on this
            # row -- this specific bucket is a real, honest zero (this
            # team did not land here this week), not a provider gap.
            matched_any = True
            continue
        unsupported.append(key)
    if not matched_any:
        return None
    return round(total, 2), tuple(unsupported)

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
    # NWR Sunday Readiness overnight cycle, Worker 3 (W7): populated only for
    # K/DST rows scored via `KDST_SCORING_LABEL_PARTIAL` -- the real, named
    # league scoring categories (nonzero weight) this row's raw stats could
    # NOT support (e.g. a 50+ yard field-goal tier the provider does not
    # break out). Empty for every other `scoring_context`.
    unsupported_scoring_categories: tuple[str, ...] = ()


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


def _score_row(
    position: str,
    raw: Mapping[str, Any],
    scoring: ScoringSettings,
    sleeper_scoring_settings: Mapping[str, Any] | None = None,
) -> tuple[float | None, str, tuple[str, ...]]:
    if position in {"K", "DST"}:
        # NWR Sunday Readiness overnight cycle, Worker 3 (W7 fix): try a
        # real, league-exact score from Sleeper's own raw scoring_settings
        # map first -- only falls back to the generic provider `pts_ppr`
        # passthrough when the league's raw scoring map is unavailable or
        # has no real overlap with this row's raw stats. Never blends the
        # two into one number silently labeled as exact.
        custom = _score_kdst_from_raw_sleeper_scoring(position, raw, sleeper_scoring_settings)
        if custom is not None:
            points, unsupported = custom
            label = KDST_SCORING_LABEL_PARTIAL if unsupported else KDST_SCORING_LABEL_EXACT
            return points, label, unsupported
        points = raw.get("pts_ppr")
        if not isinstance(points, (int, float)):
            return None, KDST_SCORING_LABEL, ()
        return round(float(points), 2), KDST_SCORING_LABEL, ()
    mapped = _mapped_stats(raw)
    if not mapped:
        return None, NWR_SCORING_LABEL, ()
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
    return score_projection(player, scoring), NWR_SCORING_LABEL, ()


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
    sleeper_scoring_settings: Mapping[str, Any] | None = None,
) -> WeeklyProjectionResult:
    """Join Sleeper's raw weekly stat lines to NWR identity + league scoring.

    `players` is the same Sleeper `players/nfl` catalog every other Sleeper
    read in this app already fetches. `ranking_rows` is the same
    `_redraft_ranking_payloads(...)`-shaped sequence `sleeper_free_agent_pool`
    already consumes -- reused here for the identical name/position/team
    identity join, not a new resolver.

    NWR Sunday Readiness overnight cycle, Worker 3 (W7 fix):
    `sleeper_scoring_settings` is the league's own raw
    `league.settings.scoring_settings` map (optional -- when omitted, K/DST
    scoring falls back to the pre-existing generic `pts_ppr` passthrough,
    unchanged). When supplied, K/DST rows are scored league-exactly wherever
    the raw weekly stats genuinely support it (see
    `_score_kdst_from_raw_sleeper_scoring`); any real, nonzero-weighted
    scoring category this row's raw stats could not support is disclosed on
    the row itself (`unsupported_scoring_categories`), never silently
    dropped or blended into a falsely-exact total.
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
        points, scoring_context, unsupported_categories = _score_row(
            position, raw, scoring, sleeper_scoring_settings
        )
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
                unsupported_scoring_categories=unsupported_categories,
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
