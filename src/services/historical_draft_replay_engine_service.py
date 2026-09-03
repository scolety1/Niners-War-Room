"""Historical draft replay engine (directive section 9).

Independent of any specific historical dataset: this module runs a
deterministic, pick-by-pick, round-by-round snake draft over an
already-validated set of point-in-time features
(`point_in_time_feature_store_service`), using the strategy framework
built in section 8 (`draft_strategy_framework_service`).

Opponent behavior uses the historical/platform market model
(PLATFORM_ADP strategy by default) -- never the strategy under test and
never NWR ranks for opponents, matching the directive's own instruction.
Only ONE seat (the "owner" seat) runs the strategy actually being
evaluated. No future pick may influence an earlier decision: every pick
resolves its candidate ranking from the SAME point-in-time feature store
and the SAME `as_of` cutoff (the historical draft's real draft_date, not
a fabricated per-pick date -- a snake draft happens on one real calendar
day, so within a draft, every pick shares the season's real draft_date as
its feature/market cutoff).

Every replay produces a `ReplayReceipt`: deterministic given the same
seed, inputs, and strategies -- re-running it must reproduce the exact
same picks, which the tests below verify directly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.draft_strategy_framework_service import (
    DraftStrategy,
    StrategyDecision,
    StrategyDecisionContext,
    platform_adp_strategy,
)
from src.services.point_in_time_feature_store_service import PointInTimeFeatureStore

REPLAY_ENGINE_VERSION = "historical-draft-replay-engine-v1"


class HistoricalDraftReplayError(ValueError):
    pass


@dataclass(frozen=True)
class ReplaySeatConfig:
    team_slot: int
    strategy_name: str
    strategy: DraftStrategy


@dataclass(frozen=True)
class ReplayPickReceipt:
    pick_number: int
    round_number: int
    team_slot: int
    strategy_name: str
    selected_player_id: str | None
    decision_metadata: Mapping[str, object]


@dataclass(frozen=True)
class ReplayReceipt:
    engine_version: str
    season: int
    team_count: int
    rounds: int
    seed: int
    owner_slot: int
    owner_strategy_name: str
    opponent_strategy_name: str
    picks: tuple[ReplayPickReceipt, ...]
    rosters_by_slot: Mapping[int, tuple[str, ...]]


def _snake_team_slot(pick_index: int, team_count: int) -> int:
    """1-indexed team slot for pick_index (0-based), standard snake order."""
    round_number = pick_index // team_count
    position_in_round = pick_index % team_count
    if round_number % 2 == 0:
        return position_in_round + 1
    return team_count - position_in_round


def run_historical_draft_replay(
    *,
    season: int,
    team_count: int,
    rounds: int,
    available_player_ids: Sequence[str],
    feature_store: PointInTimeFeatureStore,
    as_of: str,
    owner_slot: int,
    owner_strategy_name: str,
    owner_strategy: DraftStrategy,
    league_rules_summary: Mapping[str, object] | None = None,
    opponent_strategy_name: str = "PLATFORM_ADP",
    opponent_strategy: DraftStrategy = platform_adp_strategy,
    seed: int = 0,
) -> ReplayReceipt:
    """Runs one deterministic full snake draft. Every seat other than
    `owner_slot` uses `opponent_strategy` (the market model) -- the owner
    seat alone runs the strategy under test. No future pick's
    availability, and no future season's data, can enter any decision:
    the feature store's own point-in-time lookup already enforces the
    no-leakage guarantee at the feature level (section 4); this engine
    additionally never removes a player from `available` before its own
    pick, and never looks ahead to any later pick's outcome.
    """
    if team_count <= 0 or rounds <= 0:
        raise HistoricalDraftReplayError("team_count and rounds must both be positive.")
    if owner_slot < 1 or owner_slot > team_count:
        raise HistoricalDraftReplayError(f"owner_slot {owner_slot} is outside 1..{team_count}.")

    available = list(available_player_ids)
    rosters: dict[int, list[str]] = {slot: [] for slot in range(1, team_count + 1)}
    picks: list[ReplayPickReceipt] = []
    total_picks = min(team_count * rounds, len(available))
    rules_summary = league_rules_summary or {}

    for pick_index in range(total_picks):
        team_slot = _snake_team_slot(pick_index, team_count)
        round_number = pick_index // team_count + 1
        strategy = owner_strategy if team_slot == owner_slot else opponent_strategy
        strategy_name = owner_strategy_name if team_slot == owner_slot else opponent_strategy_name
        context = StrategyDecisionContext(
            league_rules_summary=rules_summary,
            pick_number=pick_index + 1,
            round_number=round_number,
            available_player_ids=tuple(available),
            roster_player_ids=tuple(rosters[team_slot]),
            feature_store=feature_store,
            as_of=as_of,
            season=season,
            seed=seed,
        )
        decision: StrategyDecision = strategy(context)
        selected = decision.selected_player_id
        if selected is not None:
            available.remove(selected)
            rosters[team_slot].append(selected)
        picks.append(
            ReplayPickReceipt(
                pick_number=pick_index + 1,
                round_number=round_number,
                team_slot=team_slot,
                strategy_name=strategy_name,
                selected_player_id=selected,
                decision_metadata=decision.decision_metadata,
            )
        )
        if selected is None:
            # No candidate could be ranked at all (e.g. every remaining
            # player's feature is UNKNOWN) -- stop rather than loop forever
            # or silently skip a real pick.
            break

    return ReplayReceipt(
        engine_version=REPLAY_ENGINE_VERSION,
        season=season,
        team_count=team_count,
        rounds=rounds,
        seed=seed,
        owner_slot=owner_slot,
        owner_strategy_name=owner_strategy_name,
        opponent_strategy_name=opponent_strategy_name,
        picks=tuple(picks),
        rosters_by_slot={slot: tuple(ids) for slot, ids in rosters.items()},
    )
