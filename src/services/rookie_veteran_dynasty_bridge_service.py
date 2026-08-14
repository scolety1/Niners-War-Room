"""Truthful multi-authority rookie/veteran comparison support.

This module deliberately does not create a common dynasty score.  It combines:

* exact-ID, current-season Redraft evidence for the shared win-now question;
* source-separated Finished V1 and Rookie Review evidence for floor/uncertainty; and
* the frozen Unified Research Preview only where a result is explicitly research-only.

Missing identities or evidence fail closed.  Player names are never used as join keys.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RosterSettings,
    ScoringSettings,
    generate_rankings,
    load_projection_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]
REDRAFT_PACKET_RELATIVE = Path(
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
)
REDRAFT_SOURCE_NAME = "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv"
REDRAFT_SOURCE_SHA256 = "e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25"

BRIDGE_MODE = "ROOKIE_VETERAN"
PRODUCTION = "PRODUCTION"
REVIEW = "REVIEW"
RESEARCH_ONLY = "RESEARCH ONLY"
INSUFFICIENT = "INSUFFICIENT EVIDENCE"

CURRENT_PLAYER = "Current Player"
ROOKIE_TYPES = {"Rookie Review", "Blocked Rookie"}
WIN_NOW_TOO_CLOSE_VBD = 5.0
RESEARCH_NEIGHBORHOOD_RANK_GAP = 3
RESEARCH_OUTLOOK_TOO_CLOSE_RATIO = 0.05
RESEARCH_CEILING_TOO_CLOSE_GAP = 0.05


@dataclass(frozen=True)
class ImmediateProductionEvidence:
    asset_id: str
    player: str
    available: bool
    projected_points: float | None
    overall_rank: int | None
    position_rank: int | None
    replacement_points: float | None
    replacement_adjusted_value: float | None
    confidence: str
    rookie: bool | None
    authority: str
    source_as_of: str
    uncertainty: str


@dataclass(frozen=True)
class BridgeDecision:
    key: str
    label: str
    preferred: str
    badge: str
    authority: str
    reason: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class RookieVeteranBridge:
    mode: str
    decisions: tuple[BridgeDecision, ...]
    immediate_production: tuple[ImmediateProductionEvidence, ...]
    why: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "players": [value.player for value in self.immediate_production],
            "decisions": [
                {
                    **asdict(value),
                    "evidence": list(value.evidence),
                }
                for value in self.decisions
            ],
            "immediateProduction": [
                immediate_production_payload(value) for value in self.immediate_production
            ],
            "why": list(self.why),
            "warnings": list(self.warnings),
        }


def immediate_production_payload(value: ImmediateProductionEvidence) -> dict[str, Any]:
    return {
        "assetId": value.asset_id,
        "player": value.player,
        "available": value.available,
        "projectedPoints": value.projected_points,
        "overallRank": value.overall_rank,
        "positionRank": value.position_rank,
        "replacementPoints": value.replacement_points,
        "replacementAdjustedValue": value.replacement_adjusted_value,
        "confidence": value.confidence,
        "rookie": value.rookie,
        "authority": value.authority,
        "sourceAsOf": value.source_as_of,
        "uncertainty": value.uncertainty,
    }


@dataclass(frozen=True)
class RedraftBridgeContext:
    by_player_id: Mapping[str, Mapping[str, Any]]
    source_sha256: str
    source_as_of: str
    errors: tuple[str, ...]


def owner_redraft_profile() -> LeagueProfile:
    """Return the owner's offensive roster/scoring overlay without persisting a profile.

    K consumes one of the owner's 24 roster places, but the admitted projection universe
    has no kickers.  The offensive calculation therefore uses nine offensive starters plus
    fourteen offensive bench places (23 offensive roster places).  Two-point conversion
    projection fields are absent from the admitted snapshot and remain explicitly unavailable.
    """

    return LeagueProfile(
        profile_id="bridge:10_TEAM_1QB_NONPPR_FIRST_DOWN",
        league_name="NWR 10-team 1QB non-PPR first-down bridge",
        season=2026,
        team_count=10,
        roster=RosterSettings(qb=1, rb=2, wr=3, te=1, flex=2, k=0, dst=0, bench_size=14),
        scoring=ScoringSettings(
            passing_yards=1.0 / 30.0,
            passing_td=3.0,
            interception=-1.0,
            rushing_yards=0.1,
            rushing_td=4.0,
            receiving_yards=0.1,
            reception=0.0,
            receiving_td=4.0,
            passing_first_down=0.0,
            rushing_first_down=0.4,
            receiving_first_down=0.4,
            return_yards=1.0 / 30.0,
            return_td=4.0,
            fumble_lost=-1.0,
        ),
        draft=DraftContext(rounds=24, replacement_method="expected_available"),
    )


@lru_cache(maxsize=8)
def load_redraft_bridge_context(repo_root: str | Path = ROOT) -> RedraftBridgeContext:
    root = Path(repo_root).resolve()
    source = root / REDRAFT_PACKET_RELATIVE / REDRAFT_SOURCE_NAME
    if not source.is_file():
        return RedraftBridgeContext({}, "", "", ("Governed 2026 Redraft source is missing.",))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != REDRAFT_SOURCE_SHA256:
        return RedraftBridgeContext(
            {}, digest, "", ("Governed 2026 Redraft source hash mismatch.",)
        )
    snapshot = load_projection_snapshot(source, season=2026)
    if snapshot.errors:
        return RedraftBridgeContext({}, digest, snapshot.source_as_of, snapshot.errors)
    ranking = generate_rankings(owner_redraft_profile(), snapshot)
    if ranking.errors:
        return RedraftBridgeContext({}, digest, snapshot.source_as_of, ranking.errors)
    projection_by_id = {player.player_id: player for player in snapshot.players}
    by_player_id: dict[str, Mapping[str, Any]] = {}
    for row in ranking.rows:
        projection = projection_by_id[row.player_id]
        availability = projection.stats.get("availability_probability")
        by_player_id[row.player_id] = {
            "player_id": row.player_id,
            "player": row.player_name,
            "projected_points": row.projected_points,
            "overall_rank": row.overall_rank,
            "position_rank": row.position_rank,
            "replacement_points": row.replacement_points,
            "replacement_adjusted_value": row.replacement_adjusted_value,
            "confidence": row.confidence,
            "rookie": row.rookie,
            "source_as_of": row.source_as_of,
            "availability_probability": availability,
        }
    return RedraftBridgeContext(by_player_id, digest, snapshot.source_as_of, ())


def immediate_production_for_row(
    row: Mapping[str, Any],
    context: RedraftBridgeContext,
) -> ImmediateProductionEvidence:
    asset_id = _text(row.get("asset_id"))
    player = _text(row.get("player") or row.get("asset_name")) or "Unknown player"
    governed_id = _governed_player_id(row)
    evidence = context.by_player_id.get(governed_id) if governed_id else None
    if evidence is None:
        return ImmediateProductionEvidence(
            asset_id=asset_id,
            player=player,
            available=False,
            projected_points=None,
            overall_rank=None,
            position_rank=None,
            replacement_points=None,
            replacement_adjusted_value=None,
            confidence="UNAVAILABLE",
            rookie=None,
            authority=INSUFFICIENT,
            source_as_of=context.source_as_of,
            uncertainty=(
                "No exact governed player-ID match to the admitted 2026 Redraft projection."
                if not context.errors
                else "; ".join(context.errors)
            ),
        )
    availability = _number(evidence.get("availability_probability"))
    uncertainty = f"{_text(evidence.get('confidence')) or 'LOW'} projection confidence"
    if availability is not None:
        uncertainty += f"; availability input {availability:.1%}"
    return ImmediateProductionEvidence(
        asset_id=asset_id,
        player=player,
        available=True,
        projected_points=_number(evidence.get("projected_points")),
        overall_rank=_integer(evidence.get("overall_rank")),
        position_rank=_integer(evidence.get("position_rank")),
        replacement_points=_number(evidence.get("replacement_points")),
        replacement_adjusted_value=_number(evidence.get("replacement_adjusted_value")),
        confidence=_text(evidence.get("confidence")) or "LOW",
        rookie=bool(evidence.get("rookie")),
        authority="Redraft 2026",
        source_as_of=_text(evidence.get("source_as_of")) or context.source_as_of,
        uncertainty=uncertainty,
    )


def build_rookie_veteran_bridge(
    rows: Sequence[Mapping[str, Any]],
    *,
    redraft_context: RedraftBridgeContext,
) -> RookieVeteranBridge | None:
    if len(rows) != 2:
        return None
    asset_types = {_asset_type(row) for row in rows}
    if CURRENT_PLAYER not in asset_types or not asset_types.intersection(ROOKIE_TYPES):
        return None
    veteran = next(row for row in rows if _asset_type(row) == CURRENT_PLAYER)
    rookie = next(row for row in rows if _asset_type(row) in ROOKIE_TYPES)
    immediate = tuple(immediate_production_for_row(row, redraft_context) for row in rows)
    immediate_by_asset = {row.asset_id: row for row in immediate}
    decisions = (
        _win_now(rows, immediate),
        _research_rank_decision("dynasty_today", "DYNASTY TODAY", rows),
        _research_outlook_decision("three_year", "3-YEAR OUTLOOK", rows, "research_outlook_3y"),
        _research_outlook_decision("long_term", "LONG-TERM", rows, "research_outlook_5y"),
        _safety(veteran, rookie),
        _upside(rows),
        _uncertainty(veteran, rookie),
    )
    why = _why(rows, veteran, rookie, immediate_by_asset)
    warnings = (
        "Rookie Review score and veteran Finished V1 score are not directly comparable.",
        "The 3-year and long-term preferences are frozen research signals, "
        "not production authority.",
        "Two-point conversion projections are unavailable in the admitted Redraft "
        "snapshot; they are not imputed as zero.",
        "No common dynasty 0-100 value or hidden additive package score is created.",
    )
    return RookieVeteranBridge(BRIDGE_MODE, decisions, immediate, why, warnings)


def _win_now(
    rows: Sequence[Mapping[str, Any]],
    evidence: Sequence[ImmediateProductionEvidence],
) -> BridgeDecision:
    if len(evidence) != len(rows) or any(not row.available for row in evidence):
        missing = [row.player for row in evidence if not row.available]
        return BridgeDecision(
            "win_now",
            "WIN NOW / 2026",
            INSUFFICIENT,
            INSUFFICIENT,
            "Redraft 2026",
            "A common current-season comparison requires exact-ID Redraft evidence "
            "for both players.",
            tuple(f"Missing: {name}." for name in missing),
        )
    ordered = sorted(
        evidence,
        key=lambda row: (
            -(
                row.replacement_adjusted_value
                if row.replacement_adjusted_value is not None
                else -1e9
            ),
            row.player,
        ),
    )
    best, other = ordered
    gap = (best.replacement_adjusted_value or 0.0) - (other.replacement_adjusted_value or 0.0)
    preferred = "TOO CLOSE" if gap <= WIN_NOW_TOO_CLOSE_VBD else best.player
    reason = (
        f"The available-scoring VBD gap is {gap:.1f}, inside the "
        f"{WIN_NOW_TOO_CLOSE_VBD:.1f}-point descriptive tie band."
        if preferred == "TOO CLOSE"
        else f"Higher 2026 replacement-adjusted production by {gap:.1f} available-scoring points."
    )
    return BridgeDecision(
        "win_now",
        "WIN NOW / 2026",
        preferred,
        PRODUCTION,
        "Redraft 2026",
        reason,
        tuple(
            f"{row.player}: {row.projected_points:.1f} projected; "
            f"VBD {row.replacement_adjusted_value:.1f}; overall #{row.overall_rank}; "
            f"{row.confidence} confidence."
            for row in evidence
            if row.projected_points is not None
            and row.replacement_adjusted_value is not None
            and row.overall_rank is not None
        ),
    )


def _research_rank_decision(
    key: str,
    label: str,
    rows: Sequence[Mapping[str, Any]],
) -> BridgeDecision:
    ranked = [(_integer(row.get("research_rank")), _player(row)) for row in rows]
    if any(rank is None for rank, _player_name in ranked):
        return _research_unavailable(
            key, label, "Frozen research rank is unavailable for at least one player."
        )
    ordered = sorted((int(rank), player) for rank, player in ranked if rank is not None)
    best, other = ordered
    gap = other[0] - best[0]
    preferred = "TOO CLOSE" if gap <= RESEARCH_NEIGHBORHOOD_RANK_GAP else best[1]
    return BridgeDecision(
        key,
        label,
        preferred,
        RESEARCH_ONLY,
        "Unified dynasty research preview",
        (
            "Both players occupy the same frozen research neighborhood."
            if preferred == "TOO CLOSE"
            else f"Higher frozen research neighborhood (rank gap {gap})."
        ),
        tuple(f"{player}: frozen research rank #{rank}." for rank, player in ordered),
    )


def _research_outlook_decision(
    key: str,
    label: str,
    rows: Sequence[Mapping[str, Any]],
    field: str,
) -> BridgeDecision:
    values = [(_number(row.get(field)), _player(row)) for row in rows]
    if any(value is None for value, _player_name in values):
        return _research_unavailable(
            key, label, "Frozen horizon research is unavailable for at least one player."
        )
    ordered = sorted(
        ((float(value), player) for value, player in values if value is not None), reverse=True
    )
    best, other = ordered
    denominator = max(abs(best[0]), abs(other[0]), 1.0)
    ratio = abs(best[0] - other[0]) / denominator
    preferred = "TOO CLOSE" if ratio <= RESEARCH_OUTLOOK_TOO_CLOSE_RATIO else best[1]
    return BridgeDecision(
        key,
        label,
        preferred,
        RESEARCH_ONLY,
        "Unified dynasty research preview",
        (
            "The frozen horizon signals are inside the descriptive 5% tie band."
            if preferred == "TOO CLOSE"
            else "One player has the stronger frozen horizon signal; production "
            "validation is not admitted."
        ),
        (
            "Research-only ordering; the underlying horizon values are not owner-facing "
            "dynasty prices.",
            "No 3Y or 5Y production common scale has passed promotion gates.",
        ),
    )


def _safety(veteran: Mapping[str, Any], rookie: Mapping[str, Any]) -> BridgeDecision:
    veteran_name, rookie_name = _player(veteran), _player(rookie)
    if _integer(veteran.get("nwr_rank") or veteran.get("dynasty_rank")) is None:
        return BridgeDecision(
            "safety",
            "SAFETY",
            INSUFFICIENT,
            INSUFFICIENT,
            "Finished V1 + Rookie Review",
            "The veteran lacks the required established-production authority.",
            (),
        )
    return BridgeDecision(
        "safety",
        "SAFETY",
        veteran_name,
        REVIEW,
        "Finished V1 + Rookie Review",
        "Established NFL production provides more downside protection than a pre-NFL "
        "rookie profile.",
        (
            f"{veteran_name}: established Finished V1 production authority.",
            f"{rookie_name}: rookie evidence with no NFL regular-season production yet.",
        ),
    )


def _upside(rows: Sequence[Mapping[str, Any]]) -> BridgeDecision:
    values = [(_number(row.get("research_ceiling_signal")), _player(row)) for row in rows]
    if any(value is None for value, _player_name in values):
        return _research_unavailable(
            "upside", "UPSIDE", "Comparable frozen ceiling evidence is unavailable."
        )
    ordered = sorted(
        ((float(value), player) for value, player in values if value is not None), reverse=True
    )
    best, other = ordered
    gap = best[0] - other[0]
    preferred = "TOO CLOSE" if gap <= RESEARCH_CEILING_TOO_CLOSE_GAP else best[1]
    return BridgeDecision(
        "upside",
        "UPSIDE",
        preferred,
        RESEARCH_ONLY,
        "Unified dynasty research preview",
        (
            "Frozen ceiling signals are too close to separate."
            if preferred == "TOO CLOSE"
            else "Higher frozen ceiling signal; not a calibrated production probability."
        ),
        ("Ceiling evidence remains research-only because rookie calibration failed.",),
    )


def _uncertainty(veteran: Mapping[str, Any], rookie: Mapping[str, Any]) -> BridgeDecision:
    rookie_name = _player(rookie)
    manual = _asset_type(rookie) == "Blocked Rookie" or not _truth(
        rookie.get("model_score_eligible")
    )
    return BridgeDecision(
        "uncertainty",
        "UNCERTAINTY",
        rookie_name,
        REVIEW,
        "Rookie Review evidence contract",
        (
            "The rookie has a manual-review evidence block plus no NFL production history."
            if manual
            else "The rookie has no NFL production history and carries capped prospect evidence."
        ),
        (
            f"{rookie_name}: "
            f"{'manual review / unscored' if manual else 'review-only rookie authority'}.",
            f"{_player(veteran)}: established NFL evidence narrows the evidence range.",
        ),
    )


def _research_unavailable(key: str, label: str, reason: str) -> BridgeDecision:
    return BridgeDecision(
        key,
        label,
        INSUFFICIENT,
        INSUFFICIENT,
        "Unified dynasty research preview",
        reason,
        ("Missing research evidence remains unavailable, never zero.",),
    )


def _why(
    rows: Sequence[Mapping[str, Any]],
    veteran: Mapping[str, Any],
    rookie: Mapping[str, Any],
    immediate_by_asset: Mapping[str, ImmediateProductionEvidence],
) -> tuple[str, ...]:
    bullets: list[str] = []
    for row in rows:
        immediate = immediate_by_asset.get(_text(row.get("asset_id")))
        if (
            immediate
            and immediate.available
            and immediate.projected_points is not None
            and immediate.replacement_adjusted_value is not None
        ):
            bullets.append(
                f"{immediate.player}: {immediate.projected_points:.1f} "
                "available-scoring 2026 points, "
                f"VBD {immediate.replacement_adjusted_value:.1f}, "
                f"{immediate.confidence} confidence."
            )
    veteran_rank = _integer(veteran.get("nwr_rank") or veteran.get("dynasty_rank"))
    if veteran_rank is not None:
        bullets.append(f"{_player(veteran)} has established Finished V1 rank #{veteran_rank}.")
    draft_round = _integer(rookie.get("draft_round"))
    overall_pick = _integer(rookie.get("overall_pick"))
    if draft_round is not None and overall_pick is not None:
        bullets.append(
            f"{_player(rookie)} carries NFL Round {draft_round}, pick {overall_pick} "
            "rookie evidence."
        )
    if _integer(rookie.get("research_rank")) is not None:
        bullets.append(
            "The frozen shared-target preview supplies a research-only neighborhood, "
            "not a production value."
        )
    bullets.append(
        "Five-year rookie calibration remains blocked; no long-term production winner is claimed."
    )
    return tuple(dict.fromkeys(bullets))[:5]


def _governed_player_id(row: Mapping[str, Any]) -> str:
    for key in ("governed_player_id", "live_governed_player_id", "player_id"):
        value = _text(row.get(key))
        if value:
            return value
    return ""


def _asset_type(row: Mapping[str, Any]) -> str:
    return _text(row.get("compare_asset_type") or row.get("asset_type"))


def _player(row: Mapping[str, Any]) -> str:
    return _text(row.get("player") or row.get("asset_name")) or "Unknown player"


def _text(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.casefold() in {"", "nan", "none", "null", "<na>"} else text


def _number(value: object) -> float | None:
    try:
        text = _text(value).replace(",", "")
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def _integer(value: object) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _truth(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).casefold() in {"1", "true", "yes", "y"}
