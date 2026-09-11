"""DecisionResultEnvelope (NWR pre-UI architecture pass, 2026-09-10).

An OWNER-FACING contract only (directive section 4) -- it does not compute
anything itself and never replaces an engine's own real fields. Every
existing tool keeps returning its own real, engine-specific response shape
unchanged; this module just builds one additional, additive
`decisionEnvelope` block from data the caller already computed, so every
migrated tool can answer "what should I do, why, what else did you
consider, how confident, on what data, prove it" in the same shape.

Migration order per the directive: Start/Sit, then Waivers/Add-Drop/FAAB,
then Trades, then Streamers, then Draft. This pass wires Start/Sit and
Waivers (see `desktop_facade.redraft_weekly_lineup` /
`redraft_waivers`) -- Trade Analysis, Trade Finder, and the K/DST Streamer
gain the identification fields this envelope depends on (`traceId`,
`leagueSnapshotId`) this same pass, but not yet the full
`decisionEnvelope` block itself; Draft is untouched. See
`DECISION_CONTRACTS.md` for the exact real/deferred split.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

CONFIDENCE_STATES = ("HIGH", "NOMINAL", "LOW", "UNAVAILABLE")


@dataclass(frozen=True)
class DecisionResultEnvelope:
    task: str
    profile_id: str
    league_snapshot_id: str | None
    generated_at_utc: str
    primary_recommendation: dict[str, Any] | None
    alternatives: tuple[dict[str, Any], ...]
    rationale: str
    confidence_state: str
    confidence_basis: str
    data_health: dict[str, Any] | None
    trace_id: str | None
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "profileId": self.profile_id,
            "leagueSnapshotId": self.league_snapshot_id,
            "generatedAtUtc": self.generated_at_utc,
            "primaryRecommendation": self.primary_recommendation,
            "alternatives": list(self.alternatives),
            "rationale": self.rationale,
            "confidenceState": self.confidence_state,
            "confidenceBasis": self.confidence_basis,
            "dataHealth": self.data_health,
            "traceId": self.trace_id,
            "issues": list(self.issues),
        }


def build_decision_envelope(
    *,
    task: str,
    profile_id: str,
    league_snapshot_id: str | None,
    primary_recommendation: dict[str, Any] | None,
    rationale: str,
    confidence_state: str,
    confidence_basis: str,
    alternatives: Sequence[Mapping[str, Any]] = (),
    data_health: dict[str, Any] | None = None,
    trace_id: str | None = None,
    issues: Sequence[str] = (),
) -> DecisionResultEnvelope:
    if confidence_state not in CONFIDENCE_STATES:
        raise ValueError(
            f"confidence_state must be one of {CONFIDENCE_STATES}, got {confidence_state!r}"
        )
    return DecisionResultEnvelope(
        task=task,
        profile_id=profile_id,
        league_snapshot_id=league_snapshot_id,
        generated_at_utc=datetime.now(UTC).isoformat(timespec="seconds"),
        primary_recommendation=primary_recommendation,
        alternatives=tuple(dict(row) for row in alternatives),
        rationale=rationale,
        confidence_state=confidence_state,
        confidence_basis=confidence_basis,
        data_health=data_health,
        trace_id=trace_id,
        issues=tuple(issues),
    )
