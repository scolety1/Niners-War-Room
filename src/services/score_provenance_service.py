"""Score provenance (directive section 28).

Every owner-facing calculated value must be reproducible: "Where did 87
come from?" must always be answerable. `ScoreProvenance` bundles every
input a SHADOW numeric authority call depended on into one reproducibility
record, plus a single combined `provenance_hash` a caller can compare
against a later re-run to prove nothing silently changed.

This module does not compute any of the underlying hashes itself (league
profile hash, universe hash, etc.) -- those already have real, tested
computations elsewhere (`hash_player_universe` in
`redraft_engine_v1_service.py`, `AdpSnapshot.source_sha256`, etc.); this
module's job is only to assemble them into one bundle and hash the bundle
itself, never to invent a new hashing scheme for data that already has one.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.services.point_in_time_feature_store_service import provenance_hash


@dataclass(frozen=True)
class ScoreProvenance:
    league_profile_hash: str
    roster_state_hash: str
    available_player_hash: str
    universe_hash: str
    projection_model_version: str
    market_snapshot_hash: str
    feature_set_version: str
    team_score_version: str
    championship_equity_version: str
    pick_score_version: str
    optimizer_version: str
    seed: int
    simulation_count: int
    timestamp_utc: str
    bundle_hash: str = ""

    def __post_init__(self) -> None:
        if not self.bundle_hash:
            object.__setattr__(self, "bundle_hash", self._compute_bundle_hash())

    def _compute_bundle_hash(self) -> str:
        payload = {
            "league_profile_hash": self.league_profile_hash,
            "roster_state_hash": self.roster_state_hash,
            "available_player_hash": self.available_player_hash,
            "universe_hash": self.universe_hash,
            "projection_model_version": self.projection_model_version,
            "market_snapshot_hash": self.market_snapshot_hash,
            "feature_set_version": self.feature_set_version,
            "team_score_version": self.team_score_version,
            "championship_equity_version": self.championship_equity_version,
            "pick_score_version": self.pick_score_version,
            "optimizer_version": self.optimizer_version,
            "seed": self.seed,
            "simulation_count": self.simulation_count,
        }
        return provenance_hash(payload)


def build_score_provenance(
    *,
    league_profile_hash: str,
    roster_state_hash: str,
    available_player_hash: str,
    universe_hash: str,
    projection_model_version: str,
    market_snapshot_hash: str,
    feature_set_version: str,
    team_score_version: str,
    championship_equity_version: str,
    pick_score_version: str,
    optimizer_version: str,
    seed: int,
    simulation_count: int,
    timestamp_utc: str,
) -> ScoreProvenance:
    return ScoreProvenance(
        league_profile_hash=league_profile_hash,
        roster_state_hash=roster_state_hash,
        available_player_hash=available_player_hash,
        universe_hash=universe_hash,
        projection_model_version=projection_model_version,
        market_snapshot_hash=market_snapshot_hash,
        feature_set_version=feature_set_version,
        team_score_version=team_score_version,
        championship_equity_version=championship_equity_version,
        pick_score_version=pick_score_version,
        optimizer_version=optimizer_version,
        seed=seed,
        simulation_count=simulation_count,
        timestamp_utc=timestamp_utc,
    )


def provenance_matches(a: ScoreProvenance, b: ScoreProvenance) -> bool:
    """Whether two provenance bundles describe an identical reproducible
    computation -- the single check a caller needs to answer "would
    re-running this produce the same result." Compares the combined hash
    only, not field-by-field, so it stays correct as fields are added."""
    return a.bundle_hash == b.bundle_hash
