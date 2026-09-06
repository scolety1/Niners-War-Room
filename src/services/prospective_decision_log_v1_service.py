"""Prospective 2026 decision log (NWR Big-Draft Readiness Overnight V1,
section 13-15).

Historical validation is finished -- every real practice or real draft pick
from now on is potential prospective evidence for this program's NEXT
piece of independent validation (the 2026 prospective protocol). This
module writes ONE immutable, append-only JSONL row per real decision point,
capturing exactly what the engine knew and recommended, and (once known)
what the owner actually did.

This is a logging-only module: it NEVER trains on what it writes, NEVER
mutates a row once appended (a correction is a NEW row, `event_type=
"OWNER_ACTION_RECORDED"`, referencing the original `decision_id` -- the
original recommendation row is never rewritten), and NEVER blocks a real
draft-state mutation if writing fails (callers should treat this the same
way `owner_test_instrumentation_service` already does: best-effort,
wrapped in a narrow try/except at the call site).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROSPECTIVE_LOG_SCHEMA_VERSION = 1

EVENT_RECOMMENDATION_LOGGED = "RECOMMENDATION_LOGGED"
EVENT_OWNER_ACTION_RECORDED = "OWNER_ACTION_RECORDED"
PROSPECTIVE_LOG_EVENT_TYPES = frozenset({EVENT_RECOMMENDATION_LOGGED, EVENT_OWNER_ACTION_RECORDED})


class ProspectiveDecisionLogError(ValueError):
    pass


@dataclass(frozen=True)
class ProspectiveCandidateSnapshot:
    """One candidate's complete, real, point-in-time evaluation -- every
    field is either a real computed value or explicitly None/DATA_LIMITED,
    never a fabricated placeholder."""

    player_id: str
    player_name: str
    position: str
    player_score: float | None
    team_score_after: float | None
    team_score_delta: float | None
    team_score_v2_after: float | None
    team_score_v2_delta: float | None
    team_score_v2_evidence_level: str | None
    championship_equity_after: float | None
    championship_equity_v2_after: float | None
    championship_equity_v2_evidence_level: str | None
    cost_of_waiting: float | None
    make_it_back_probability: float | None
    pick_score: float | None
    action: str | None
    evidence_status: str  # e.g. "OK", "DATA_LIMITED", "DEGRADED: <reason>"


@dataclass(frozen=True)
class ProspectiveDecisionRecord:
    decision_id: str
    profile_id: str
    event_type: str
    timestamp_utc: str
    source_as_of: str
    league_config_summary: Mapping[str, Any]
    pick_number: int
    draft_slot: int
    owner_roster_before: tuple[str, ...]
    available_pool_size: int
    candidates: tuple[ProspectiveCandidateSnapshot, ...]
    nwr_recommended_player_id: str | None
    model_versions: Mapping[str, str]
    # Populated only on an OWNER_ACTION_RECORDED row, referencing the
    # RECOMMENDATION_LOGGED row's decision_id this action resolves.
    resolves_decision_id: str | None = None
    owner_actual_player_id: str | None = None
    owner_followed_recommendation: bool | None = None
    override_reason: str | None = None
    schema_version: int = PROSPECTIVE_LOG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.event_type not in PROSPECTIVE_LOG_EVENT_TYPES:
            raise ProspectiveDecisionLogError(f"Unknown event_type: {self.event_type!r}")
        if self.event_type == EVENT_OWNER_ACTION_RECORDED and not self.resolves_decision_id:
            raise ProspectiveDecisionLogError(
                "OWNER_ACTION_RECORDED requires resolves_decision_id -- an owner action "
                "must reference the specific recommendation row it resolves."
            )


def _log_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "prospective_decision_log" / profile_id / "decisions.jsonl"


def new_decision_id() -> str:
    return uuid.uuid4().hex


def append_prospective_decision(root: str | Path, record: ProspectiveDecisionRecord) -> None:
    """Append-only. Never rewrites or deletes an existing line."""
    path = _log_path(root, record.profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), sort_keys=True, default=str) + "\n")


def read_prospective_decisions(root: str | Path, profile_id: str) -> list[dict[str, Any]]:
    path = _log_path(root, profile_id)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_candidate_snapshot_from_bundles(
    *,
    v1_candidate: Any,
    v2_candidate: Any | None,
    position: str,
    player_name: str,
) -> ProspectiveCandidateSnapshot:
    """Builds one candidate's snapshot from an already-computed V1
    `CandidateBundle` and (optionally) its matching V2 `CandidateBundleV2`
    -- never recomputes anything, purely a real-value pass-through."""
    ts2 = v2_candidate.team_score_v2 if v2_candidate is not None else None
    eq2 = v2_candidate.championship_equity_v2 if v2_candidate is not None else None
    evidence_status = "OK"
    if v2_candidate is not None and v2_candidate.v2_status != "OK":
        evidence_status = v2_candidate.v2_status
    return ProspectiveCandidateSnapshot(
        player_id=v1_candidate.player_id,
        player_name=player_name,
        position=position,
        player_score=v1_candidate.player_score,
        team_score_after=v1_candidate.team_score_after,
        team_score_delta=v1_candidate.team_score_delta,
        team_score_v2_after=ts2["post_pick_team_score"] if ts2 else None,
        team_score_v2_delta=ts2["team_score_delta"] if ts2 else None,
        team_score_v2_evidence_level=ts2["evidence_level"] if ts2 else None,
        championship_equity_after=v1_candidate.championship_equity_after,
        championship_equity_v2_after=(
            eq2["post_pick_championship_equity"] if eq2 else None
        ),
        championship_equity_v2_evidence_level=eq2["evidence_level"] if eq2 else None,
        cost_of_waiting=v1_candidate.cost_of_waiting,
        make_it_back_probability=v1_candidate.make_it_back_probability,
        pick_score=v1_candidate.pick_score,
        action=v1_candidate.action,
        evidence_status=evidence_status,
    )


def build_recommendation_record(
    *,
    profile_id: str,
    timestamp_utc: str,
    source_as_of: str,
    league_config_summary: Mapping[str, Any],
    pick_number: int,
    draft_slot: int,
    owner_roster_before: Sequence[str],
    available_pool_size: int,
    candidates: Sequence[ProspectiveCandidateSnapshot],
    model_versions: Mapping[str, str],
) -> ProspectiveDecisionRecord:
    nwr_recommended = candidates[0].player_id if candidates else None
    return ProspectiveDecisionRecord(
        decision_id=new_decision_id(),
        profile_id=profile_id,
        event_type=EVENT_RECOMMENDATION_LOGGED,
        timestamp_utc=timestamp_utc,
        source_as_of=source_as_of,
        league_config_summary=dict(league_config_summary),
        pick_number=pick_number,
        draft_slot=draft_slot,
        owner_roster_before=tuple(owner_roster_before),
        available_pool_size=available_pool_size,
        candidates=tuple(candidates),
        nwr_recommended_player_id=nwr_recommended,
        model_versions=dict(model_versions),
    )


def build_owner_action_record(
    *,
    profile_id: str,
    timestamp_utc: str,
    resolves_decision_id: str,
    nwr_recommended_player_id: str | None,
    owner_actual_player_id: str,
    override_reason: str | None = None,
) -> ProspectiveDecisionRecord:
    return ProspectiveDecisionRecord(
        decision_id=new_decision_id(),
        profile_id=profile_id,
        event_type=EVENT_OWNER_ACTION_RECORDED,
        timestamp_utc=timestamp_utc,
        source_as_of="",
        league_config_summary={},
        pick_number=0,
        draft_slot=0,
        owner_roster_before=(),
        available_pool_size=0,
        candidates=(),
        nwr_recommended_player_id=nwr_recommended_player_id,
        model_versions={},
        resolves_decision_id=resolves_decision_id,
        owner_actual_player_id=owner_actual_player_id,
        owner_followed_recommendation=(owner_actual_player_id == nwr_recommended_player_id),
        override_reason=override_reason,
    )
