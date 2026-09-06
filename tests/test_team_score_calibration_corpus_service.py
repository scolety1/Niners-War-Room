
from src.services.team_score_calibration_corpus_service import (
    build_roster_observation,
    make_noisy_greedy_strategy,
)


def test_make_noisy_greedy_strategy_is_deterministic_given_a_seed() -> None:
    name_a, strategy_a = make_noisy_greedy_strategy(seed=42, noise_scale=5.0)
    name_b, strategy_b = make_noisy_greedy_strategy(seed=42, noise_scale=5.0)
    assert name_a == name_b == "NOISY_GREEDY_NWR_SEED_42"

    class FakeFeature:
        def __init__(self, value):
            self.value = value
            self.value_status = "KNOWN"

    class FakeFeatureStore:
        def __init__(self, values):
            self.values = values

        def lookup_as_of(self, *, player_id, season, feature_name, as_of):
            return FakeFeature(self.values[player_id])

    class FakeContext:
        available_player_ids = ("p1", "p2", "p3")
        season = 2020
        as_of = "2020-09-01"
        feature_store = FakeFeatureStore({"p1": 1.0, "p2": 2.0, "p3": 3.0})

    decision_a = strategy_a(FakeContext())
    decision_b = strategy_b(FakeContext())
    assert decision_a.candidate_ranking == decision_b.candidate_ranking
    assert decision_a.selected_player_id == decision_b.selected_player_id


def test_different_seeds_can_produce_different_rankings() -> None:
    class FakeFeature:
        def __init__(self, value):
            self.value = value
            self.value_status = "KNOWN"

    class FakeFeatureStore:
        def __init__(self, values):
            self.values = values

        def lookup_as_of(self, *, player_id, season, feature_name, as_of):
            return FakeFeature(self.values[player_id])

    class FakeContext:
        available_player_ids = ("p1", "p2", "p3", "p4", "p5")
        season = 2020
        as_of = "2020-09-01"
        feature_store = FakeFeatureStore(
            {"p1": 1.0, "p2": 1.1, "p3": 1.2, "p4": 1.3, "p5": 1.4}
        )

    rankings = set()
    for seed in range(10):
        _, strategy = make_noisy_greedy_strategy(seed=seed, noise_scale=5.0)
        decision = strategy(FakeContext())
        rankings.add(decision.candidate_ranking)
    # With real noise scale >> the tiny rank gaps between these 5 players,
    # different seeds should produce at least some different orderings --
    # otherwise this "stochastic" strategy would be a no-op in disguise.
    assert len(rankings) > 1


def test_build_roster_observation_computes_realized_total_correctly() -> None:
    observation = build_roster_observation(
        season=2020, draft_slot=2, generation_policy="BASELINE_STRATEGY",
        strategy_name="GREEDY_NWR", seed=0, roster_player_ids=("p1", "p2", "p3"),
        team_score_percentile=62.5, team_score_raw_value=100.0,
        realized_by_player={"p1": 10.0, "p2": 20.0}, league_team_count=4,
        draft_date="2020-09-01",
    )
    assert observation.realized_total == 30.0
    assert observation.n_realized_known == 2
    assert observation.roster_size == 3


def test_build_roster_observation_handles_no_known_realized_players() -> None:
    observation = build_roster_observation(
        season=2020, draft_slot=1, generation_policy="BASELINE_STRATEGY",
        strategy_name="PLATFORM_ADP", seed=0, roster_player_ids=("px",),
        team_score_percentile=0.0, team_score_raw_value=0.0, realized_by_player={},
        league_team_count=4, draft_date="2020-09-01",
    )
    assert observation.realized_total == 0.0
    assert observation.n_realized_known == 0
