"""Historical row -> RankingResult bridge (section 1-2 of the follow-up directive).

Converts point-in-time historical rows (the same
`historical_replay_data_adapter_service.REQUIRED_PRE_DRAFT_FIELDS`
contract, plus the optional projection-stat columns this module defines)
into a REAL `RankingResult` by constructing a real `ProjectionSnapshot`
and calling the real, unmodified
`redraft_engine_v1_service.generate_rankings()` -- the exact function a
live draft uses. This is deliberately NOT a second, historical-only
scoring engine: every derived field (tier, confidence,
replacement_adjusted_value, ...) is computed by production code.

Missingness discipline: a player whose historical row cannot supply the
real stat components `score_projection()` needs (or a real
`projected_points_override` for K/DST) is EXCLUDED from the snapshot
entirely -- never scored as an implicit 0.0. Every exclusion is recorded
in `HistoricalRankingBridgeResult.excluded_players` with an explicit
reason and value_status (never silently dropped).

See `docs/codex/HISTORICAL_RANKINGRESULT_FIELD_MAP_20260903.md` for the
full field-by-field mapping this module implements.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.point_in_time_feature_store_service import (
    FAMILY_AVAILABILITY,
    FAMILY_CURRENT_TEAM,
    FAMILY_POSITION,
    FAMILY_ROOKIE_STATUS,
    PointInTimeFeatureStore,
    known_feature_value,
)
from src.services.redraft_draft_room_v1_service import AdpEntry, AdpSnapshot
from src.services.redraft_engine_v1_service import (
    LeagueProfile,
    ProjectionPlayer,
    ProjectionSnapshot,
    RankingResult,
    generate_rankings,
)

BRIDGE_VERSION = "historical-ranking-bridge-v1"

# Mirrors redraft_engine_v1_service.score_projection()'s exact stat keys
# -- deliberately the SAME names, so a historical archive that already
# uses this vocabulary (or is mapped to it) needs no translation layer,
# and so this bridge cannot silently drift from what the real scoring
# function actually reads.
PROJECTION_STAT_FIELDS = (
    "passing_yards", "passing_tds", "interceptions", "rushing_yards", "rushing_tds",
    "receiving_yards", "receptions", "receiving_tds", "passing_first_downs",
    "rushing_first_downs", "receiving_first_downs", "return_yards", "return_tds",
    "fumbles_lost",
)
KDST_OVERRIDE_FIELD = "projected_points_override"

MISSING_PROJECTION_STATS = "MISSING_PROJECTION_STATS"
UNAVAILABLE_HISTORICALLY = "UNAVAILABLE_HISTORICALLY"
NOT_APPLICABLE = "NOT_APPLICABLE"

HISTORICAL_SOURCE_STATUS = "imported_real_data"
HISTORICAL_EVIDENCE_STATUS = "HISTORICAL_REPLAY_IMPORT"


class HistoricalRankingBridgeError(ValueError):
    pass


@dataclass(frozen=True)
class ExcludedHistoricalPlayer:
    player_id: str
    reason: str
    value_status: str


@dataclass(frozen=True)
class HistoricalRankingBridgeResult:
    bridge_version: str
    ranking: RankingResult
    adp: AdpSnapshot
    feature_store: PointInTimeFeatureStore
    included_player_ids: tuple[str, ...]
    excluded_players: tuple[ExcludedHistoricalPlayer, ...]


def build_projection_player_from_historical_row(
    row: Mapping[str, Any], *, source_as_of: str
) -> ProjectionPlayer | None:
    """Returns None (never a fabricated ProjectionPlayer) when the row
    cannot supply real projection stat components."""
    position = str(row.get("position") or "").strip().upper()
    stats: dict[str, float | None] = {}
    if position in {"K", "DST"}:
        override = row.get(KDST_OVERRIDE_FIELD)
        if override in (None, ""):
            return None
        stats[KDST_OVERRIDE_FIELD] = float(override)
    else:
        found_any = False
        for field_name in PROJECTION_STAT_FIELDS:
            raw = row.get(field_name)
            if raw not in (None, ""):
                stats[field_name] = float(raw)
                found_any = True
        if not found_any:
            return None
    try:
        season = int(row["season"])
    except (KeyError, TypeError, ValueError):
        return None
    player_id = str(row.get("player_id") or "").strip()
    if not player_id:
        return None
    return ProjectionPlayer(
        player_id=player_id,
        player_name=str(row.get("player_name") or player_id),
        position=position,
        team=str(row.get("team") or ""),
        season=season,
        source_status=HISTORICAL_SOURCE_STATUS,
        evidence_status=HISTORICAL_EVIDENCE_STATUS,
        source_as_of=source_as_of,
        rookie=bool(row.get("rookie", False)),
        stats=stats,
    )


def _feature_values_for_row(row: Mapping[str, Any], *, draft_date: str) -> list:
    player_id = str(row["player_id"])
    season = int(row["season"])
    values = []
    if row.get("team"):
        values.append(
            known_feature_value(
                player_id=player_id, season=season, as_of=draft_date,
                feature_name="current_team.historical", feature_family=FAMILY_CURRENT_TEAM,
                value=str(row["team"]), source="historical_dataset",
                source_as_of=draft_date, retrieved_at=draft_date,
            )
        )
    if row.get("position"):
        values.append(
            known_feature_value(
                player_id=player_id, season=season, as_of=draft_date,
                feature_name="position", feature_family=FAMILY_POSITION,
                value=str(row["position"]), source="historical_dataset",
                source_as_of=draft_date, retrieved_at=draft_date,
            )
        )
    if row.get("rookie") is not None:
        values.append(
            known_feature_value(
                player_id=player_id, season=season, as_of=draft_date,
                feature_name="rookie_status.is_rookie", feature_family=FAMILY_ROOKIE_STATUS,
                value=bool(row["rookie"]), source="historical_dataset",
                source_as_of=draft_date, retrieved_at=draft_date,
            )
        )
    status_as_of = row.get("status_as_of")
    if row.get("availability_status") and status_as_of:
        values.append(
            known_feature_value(
                player_id=player_id, season=season, as_of=draft_date,
                feature_name="availability.status", feature_family=FAMILY_AVAILABILITY,
                value=str(row["availability_status"]), source="historical_dataset",
                source_as_of=str(status_as_of), retrieved_at=draft_date,
            )
        )
    return values


def build_ranking_result_from_historical_rows(
    rows: Sequence[Mapping[str, Any]],
    profile: LeagueProfile,
    *,
    generated_at_utc: str,
    source_sha256: str,
) -> HistoricalRankingBridgeResult:
    """The bridge entry point. `profile` should already carry the
    historical league's real scoring/roster rules (the caller's
    responsibility -- this function never guesses league rules)."""
    if not rows:
        raise HistoricalRankingBridgeError("No historical rows supplied.")

    players: list[ProjectionPlayer] = []
    excluded: list[ExcludedHistoricalPlayer] = []
    feature_values = []
    adp_entries: list[AdpEntry] = []
    unmatched_adp: list[str] = []
    draft_date = str(rows[0].get("draft_date") or "")

    for row in rows:
        player_id = str(row.get("player_id") or "")
        source_as_of = str(row.get("projection_as_of") or row.get("draft_date") or "")
        player = build_projection_player_from_historical_row(row, source_as_of=source_as_of)
        if player is None:
            excluded.append(
                ExcludedHistoricalPlayer(
                    player_id=player_id or "<missing player_id>",
                    reason=(
                        "No real projection stat components (or K/DST "
                        f"{KDST_OVERRIDE_FIELD}) present in this historical row -- "
                        "excluded rather than scored as an implicit zero."
                    ),
                    value_status=MISSING_PROJECTION_STATS,
                )
            )
        else:
            players.append(player)

        feature_values.extend(_feature_values_for_row(row, draft_date=draft_date))

        adp_value = row.get("platform_adp")
        if adp_value not in (None, ""):
            adp_entries.append(
                AdpEntry(
                    player_id=player_id, player=str(row.get("player_name") or player_id),
                    team=str(row.get("team") or ""), position=str(row.get("position") or ""),
                    overall_adp=float(adp_value), expected_pick=float(adp_value),
                    min_pick=None, max_pick=None, std_dev=None,
                )
            )
        elif player_id:
            unmatched_adp.append(player_id)

    if not players:
        raise HistoricalRankingBridgeError(
            "No historical row supplied any real projection stat components -- cannot "
            "build a RankingResult without fabricating projected points."
        )

    snapshot = ProjectionSnapshot(
        season=profile.season,
        source_path=Path("historical_replay_rows.csv"),
        source_sha256=source_sha256,
        players=tuple(players),
        blocked_rows=(),
        errors=(),
        source_as_of=generated_at_utc,
    )
    ranking = generate_rankings(profile, snapshot)

    adp = AdpSnapshot(
        profile_id=profile.profile_id, source="historical_dataset",
        scoring_format="historical", team_count=profile.team_count,
        source_date=draft_date, imported_at_utc=generated_at_utc,
        source_sha256=source_sha256, entries=tuple(adp_entries),
        unmatched=tuple(unmatched_adp),
    )

    return HistoricalRankingBridgeResult(
        bridge_version=BRIDGE_VERSION,
        ranking=ranking,
        adp=adp,
        feature_store=PointInTimeFeatureStore().with_values(feature_values),
        included_player_ids=tuple(p.player_id for p in players),
        excluded_players=tuple(excluded),
    )
