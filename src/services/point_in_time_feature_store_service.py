"""Point-in-time feature store -- generic interface (directive section 4).

A single, versioned `FeatureValue` shape usable for BOTH current drafting and
historical replay, so a historical calibration pass and a live Draft Room
pick can be evaluated through the same feature contract. This module does
NOT recompute feature research that already exists elsewhere in NWR (dynasty
training features in `nwr_outcome_feature_snapshot_service.py`, projections
in `redraft_engine_v1_service.py`, ADP in `redraft_draft_room_v1_service.py`,
AI hypotheses in `ai_intelligence_backend_service.py`) -- it adapts those
existing, already-governed sources into one common point-in-time shape, and
provides the point-in-time lookup semantic (`feature_as_of`) that a
historical replay needs to stay leakage-safe: never resolves a value whose
own `source_as_of` postdates the requested `as_of`.

Missing data is UNKNOWN, never zero -- every adapter and lookup path in this
module returns an explicit `FeatureValue` with `value=None,
value_status="UNKNOWN"` (or another named non-KNOWN status) rather than
omitting the row or defaulting to 0.0.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

# -- value_status vocabulary (section 4) -------------------------------
KNOWN = "KNOWN"
UNKNOWN = "UNKNOWN"
NOT_APPLICABLE = "NOT_APPLICABLE"
BLOCKED = "BLOCKED"
STALE = "STALE"

FEATURE_VALUE_STATUSES = frozenset({KNOWN, UNKNOWN, NOT_APPLICABLE, BLOCKED, STALE})

# -- feature families (section 4's own list) ----------------------------
FAMILY_PROJECTIONS = "projections"
FAMILY_MARKET_ADP = "platform_market_adp"
FAMILY_CURRENT_TEAM = "current_team"
FAMILY_POSITION = "position"
FAMILY_AGE = "age"
FAMILY_DRAFT_CAPITAL = "nfl_draft_capital"
FAMILY_ROLE_DEPTH = "role_depth"
FAMILY_AVAILABILITY = "availability"
FAMILY_INJURY = "injury"
FAMILY_SUSPENSION = "suspension"
FAMILY_ROOKIE_STATUS = "rookie_status"
FAMILY_REPLACEMENT_LEVEL = "replacement_level"
FAMILY_POSITIONAL_SCARCITY = "positional_scarcity"
FAMILY_NWR_COMPONENT_SCORES = "nwr_component_scores"
FAMILY_EXTERNAL_RESEARCH = "external_research_only_comparison"

FEATURE_FAMILIES = frozenset(
    {
        FAMILY_PROJECTIONS,
        FAMILY_MARKET_ADP,
        FAMILY_CURRENT_TEAM,
        FAMILY_POSITION,
        FAMILY_AGE,
        FAMILY_DRAFT_CAPITAL,
        FAMILY_ROLE_DEPTH,
        FAMILY_AVAILABILITY,
        FAMILY_INJURY,
        FAMILY_SUSPENSION,
        FAMILY_ROOKIE_STATUS,
        FAMILY_REPLACEMENT_LEVEL,
        FAMILY_POSITIONAL_SCARCITY,
        FAMILY_NWR_COMPONENT_SCORES,
        FAMILY_EXTERNAL_RESEARCH,
    }
)


class PointInTimeFeatureError(ValueError):
    """Raised for malformed feature values or point-in-time contract violations."""


def provenance_hash(payload: Mapping[str, Any]) -> str:
    """Deterministic SHA-256 over a canonical (sorted-key) JSON encoding.
    Same inputs always produce the same hash -- used so a caller can prove,
    later, exactly what a stored FeatureValue was derived from."""
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FeatureValue:
    """One point-in-time feature observation. `value` is None whenever
    `value_status` is not KNOWN -- never a fabricated 0.0 or empty string."""

    player_id: str
    season: int
    as_of: str  # ISO date this value is asserted valid for
    feature_name: str
    feature_family: str
    value: float | str | bool | None
    value_status: str
    source: str
    source_as_of: str | None
    retrieved_at: str
    confidence: str  # e.g. "HIGH" / "MEDIUM" / "LOW" / "UNSCORED"
    feature_version: str
    provenance_hash: str

    def __post_init__(self) -> None:
        if self.value_status not in FEATURE_VALUE_STATUSES:
            raise PointInTimeFeatureError(f"Unknown value_status: {self.value_status!r}")
        if self.feature_family not in FEATURE_FAMILIES:
            raise PointInTimeFeatureError(f"Unknown feature_family: {self.feature_family!r}")
        if self.value_status == KNOWN and self.value is None:
            raise PointInTimeFeatureError(
                f"{self.feature_name}: value_status=KNOWN requires a non-None value."
            )
        if self.value_status != KNOWN and self.value is not None:
            raise PointInTimeFeatureError(
                f"{self.feature_name}: value_status={self.value_status} must carry value=None "
                "-- missing data must never be disguised as a real value."
            )


def unknown_feature_value(
    *,
    player_id: str,
    season: int,
    as_of: str,
    feature_name: str,
    feature_family: str,
    reason: str,
    value_status: str = UNKNOWN,
    feature_version: str = "v1",
) -> FeatureValue:
    """The canonical way to represent "we don't have this" -- explicit,
    never a zero. `reason` is folded into the provenance hash so two
    different UNKNOWNs for the same feature/player/date are distinguishable
    if they arose from different causes."""
    if value_status == KNOWN:
        raise PointInTimeFeatureError(
            "unknown_feature_value cannot be used with value_status=KNOWN."
        )
    payload = {
        "player_id": player_id,
        "season": season,
        "as_of": as_of,
        "feature_name": feature_name,
        "value_status": value_status,
        "reason": reason,
    }
    return FeatureValue(
        player_id=player_id,
        season=season,
        as_of=as_of,
        feature_name=feature_name,
        feature_family=feature_family,
        value=None,
        value_status=value_status,
        source="none",
        source_as_of=None,
        retrieved_at=as_of,
        confidence="UNSCORED",
        feature_version=feature_version,
        provenance_hash=provenance_hash(payload),
    )


def known_feature_value(
    *,
    player_id: str,
    season: int,
    as_of: str,
    feature_name: str,
    feature_family: str,
    value: float | str | bool,
    source: str,
    source_as_of: str,
    retrieved_at: str,
    confidence: str = "MEDIUM",
    feature_version: str = "v1",
) -> FeatureValue:
    payload = {
        "player_id": player_id,
        "season": season,
        "as_of": as_of,
        "feature_name": feature_name,
        "value": value,
        "source": source,
        "source_as_of": source_as_of,
    }
    return FeatureValue(
        player_id=player_id,
        season=season,
        as_of=as_of,
        feature_name=feature_name,
        feature_family=feature_family,
        value=value,
        value_status=KNOWN,
        source=source,
        source_as_of=source_as_of,
        retrieved_at=retrieved_at,
        confidence=confidence,
        feature_version=feature_version,
        provenance_hash=provenance_hash(payload),
    )


# --- Adapters from existing, already-governed NWR sources -----------------
# Each adapter converts an existing contract object into a FeatureValue
# rather than recomputing the underlying feature. If the source object
# itself signals missing/blocked data, the adapter returns UNKNOWN/BLOCKED,
# never a fabricated number.


def feature_value_from_projection_stat(
    *,
    player_id: str,
    season: int,
    as_of: str,
    stat_name: str,
    stats: Mapping[str, float | None],
    source_status: str,
    evidence_status: str,
    source_as_of: str,
    retrieved_at: str,
) -> FeatureValue:
    """Adapts one stat field off a `redraft_engine_v1_service.ProjectionPlayer`
    (already-governed projection data) into a FeatureValue. `source_status`
    values that are not real-data-backed (e.g. anything other than
    imported/derived real data) degrade this to BLOCKED rather than KNOWN --
    mirrors the existing projection admission gate, not a new policy."""
    raw = stats.get(stat_name)
    blocked_statuses = {"disabled", "missing_paid_or_charted_data", "unavailable_free_public"}
    if source_status in blocked_statuses or evidence_status.upper().startswith("BLOCKED"):
        return unknown_feature_value(
            player_id=player_id,
            season=season,
            as_of=as_of,
            feature_name=f"projection.{stat_name}",
            feature_family=FAMILY_PROJECTIONS,
            reason=f"source_status={source_status} evidence_status={evidence_status}",
            value_status=BLOCKED,
        )
    if raw is None:
        return unknown_feature_value(
            player_id=player_id,
            season=season,
            as_of=as_of,
            feature_name=f"projection.{stat_name}",
            feature_family=FAMILY_PROJECTIONS,
            reason="stat field absent from ProjectionPlayer.stats",
        )
    return known_feature_value(
        player_id=player_id,
        season=season,
        as_of=as_of,
        feature_name=f"projection.{stat_name}",
        feature_family=FAMILY_PROJECTIONS,
        value=float(raw),
        source=f"redraft_projection:{source_status}",
        source_as_of=source_as_of,
        retrieved_at=retrieved_at,
        confidence="HIGH" if source_status == "imported_real_data" else "MEDIUM",
    )


def feature_value_from_adp_entry(
    *,
    player_id: str,
    season: int,
    as_of: str,
    overall_adp: float | None,
    source_date: str,
    retrieved_at: str,
    match_status: str,
) -> FeatureValue:
    """Adapts an `AdpEntry.overall_adp` (redraft_draft_room_v1_service) into
    a market-ADP FeatureValue. An unmatched/ambiguous market row is BLOCKED,
    never a guessed number."""
    if match_status != "MATCHED" or overall_adp is None:
        return unknown_feature_value(
            player_id=player_id,
            season=season,
            as_of=as_of,
            feature_name="market.overall_adp",
            feature_family=FAMILY_MARKET_ADP,
            reason=f"match_status={match_status}",
            value_status=BLOCKED if match_status != "MATCHED" else UNKNOWN,
        )
    return known_feature_value(
        player_id=player_id,
        season=season,
        as_of=as_of,
        feature_name="market.overall_adp",
        feature_family=FAMILY_MARKET_ADP,
        value=float(overall_adp),
        source="platform_adp_import",
        source_as_of=source_date,
        retrieved_at=retrieved_at,
        confidence="HIGH",
    )


def feature_value_from_impact_hypothesis(
    *,
    player_id: str,
    season: int,
    as_of: str,
    hypothesis_direction: str,
    hypothesis_confidence: str,
    generated_at_utc: str,
) -> FeatureValue:
    """Adapts an AI `ImpactHypothesis` (ai_intelligence_backend_service) into
    an availability-family feature. This is an AI HYPOTHESIS, never treated
    as KNOWN fact -- confidence carries the AI's own stated confidence
    (LOW/MEDIUM/HIGH), and the value itself is the qualitative direction
    string, not an invented numeric adjustment (directive section 3: AI may
    not invent authoritative numeric adjustments)."""
    return known_feature_value(
        player_id=player_id,
        season=season,
        as_of=as_of,
        feature_name="availability.ai_impact_direction",
        feature_family=FAMILY_AVAILABILITY,
        value=hypothesis_direction,
        source="ai_impact_analyst_hypothesis",
        source_as_of=generated_at_utc,
        retrieved_at=generated_at_utc,
        confidence=hypothesis_confidence,
        feature_version="ai-hypothesis-v1",
    )


# --- Point-in-time store + leakage-safe lookup -----------------------------


@dataclass(frozen=True)
class PointInTimeFeatureStore:
    """An immutable, append-only collection of FeatureValues, keyed for
    point-in-time lookup. Multiple values for the same
    (player_id, season, feature_name) are allowed -- e.g. a market ADP
    observed on different dates -- lookup_as_of resolves the correct one."""

    values: tuple[FeatureValue, ...] = field(default_factory=tuple)

    def with_values(self, more: Sequence[FeatureValue]) -> PointInTimeFeatureStore:
        return PointInTimeFeatureStore(values=self.values + tuple(more))

    def lookup_as_of(
        self,
        *,
        player_id: str,
        season: int,
        feature_name: str,
        as_of: str,
    ) -> FeatureValue:
        """Returns the most recent value whose `source_as_of` is on or
        before `as_of` -- the leakage-safe point-in-time read. A value whose
        source_as_of postdates `as_of` is never returned, even if it exists
        in the store; a caller that needs it anyway must ask for it
        explicitly by a different query. If nothing qualifies, returns an
        explicit UNKNOWN rather than raising or defaulting."""
        target = _safe_date(as_of)
        candidates = [
            v
            for v in self.values
            if v.player_id == player_id and v.season == season and v.feature_name == feature_name
        ]
        eligible = []
        for v in candidates:
            if v.source_as_of is None:
                continue
            v_date = _safe_date(v.source_as_of)
            if target is None or v_date is None or v_date <= target:
                eligible.append(v)
        if not eligible:
            family = candidates[0].feature_family if candidates else FAMILY_EXTERNAL_RESEARCH
            return unknown_feature_value(
                player_id=player_id,
                season=season,
                as_of=as_of,
                feature_name=feature_name,
                feature_family=family,
                reason="no feature value with source_as_of <= as_of in the store",
            )
        eligible.sort(key=lambda v: v.source_as_of or "")
        return eligible[-1]


def _safe_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
