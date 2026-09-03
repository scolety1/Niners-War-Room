from src.services.score_provenance_service import build_score_provenance, provenance_matches


def _bundle(**overrides):
    defaults = dict(
        league_profile_hash="lp1", roster_state_hash="rs1", available_player_hash="ap1",
        universe_hash="u1", projection_model_version="proj-v1",
        market_snapshot_hash="mk1", feature_set_version="fs-v1",
        team_score_version="ts-v1", championship_equity_version="ce-v1",
        pick_score_version="ps-v1", optimizer_version="opt-v1", seed=42,
        simulation_count=300, timestamp_utc="2026-09-03T12:00:00Z",
    )
    defaults.update(overrides)
    return build_score_provenance(**defaults)


def test_bundle_hash_is_deterministic_for_identical_inputs() -> None:
    a = _bundle()
    b = _bundle()
    assert a.bundle_hash == b.bundle_hash
    assert provenance_matches(a, b)


def test_bundle_hash_changes_when_any_input_changes() -> None:
    a = _bundle()
    b = _bundle(seed=43)
    assert a.bundle_hash != b.bundle_hash
    assert not provenance_matches(a, b)


def test_timestamp_is_not_part_of_the_reproducibility_hash() -> None:
    # Two runs of the identical computation at two different real times
    # should still be recognized as "the same computation, reproducible" --
    # only the inputs that affect the actual numeric result belong in the
    # hash, not the wall-clock time it happened to run.
    a = _bundle(timestamp_utc="2026-09-03T12:00:00Z")
    b = _bundle(timestamp_utc="2026-09-03T18:00:00Z")
    assert provenance_matches(a, b)


def test_every_declared_field_is_present_on_the_bundle() -> None:
    bundle = _bundle()
    assert bundle.league_profile_hash == "lp1"
    assert bundle.team_score_version == "ts-v1"
    assert bundle.seed == 42
    assert bundle.simulation_count == 300
    assert len(bundle.bundle_hash) == 64
