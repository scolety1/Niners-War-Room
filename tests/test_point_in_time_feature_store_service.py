import pytest

from src.services.point_in_time_feature_store_service import (
    BLOCKED,
    FAMILY_AVAILABILITY,
    FAMILY_MARKET_ADP,
    FAMILY_PROJECTIONS,
    KNOWN,
    UNKNOWN,
    FeatureValue,
    PointInTimeFeatureError,
    PointInTimeFeatureStore,
    feature_value_from_adp_entry,
    feature_value_from_impact_hypothesis,
    feature_value_from_projection_stat,
    known_feature_value,
    provenance_hash,
    unknown_feature_value,
)


def test_provenance_hash_is_deterministic_and_order_independent() -> None:
    a = provenance_hash({"x": 1, "y": 2})
    b = provenance_hash({"y": 2, "x": 1})
    assert a == b
    assert len(a) == 64


def test_known_feature_value_requires_a_real_value() -> None:
    with pytest.raises(PointInTimeFeatureError):
        FeatureValue(
            player_id="P1", season=2026, as_of="2026-08-01", feature_name="x",
            feature_family=FAMILY_PROJECTIONS, value=None, value_status=KNOWN,
            source="s", source_as_of="2026-08-01", retrieved_at="2026-08-01",
            confidence="HIGH", feature_version="v1", provenance_hash="deadbeef",
        )


def test_non_known_status_must_not_carry_a_value() -> None:
    with pytest.raises(PointInTimeFeatureError):
        FeatureValue(
            player_id="P1", season=2026, as_of="2026-08-01", feature_name="x",
            feature_family=FAMILY_PROJECTIONS, value=5.0, value_status=UNKNOWN,
            source="s", source_as_of=None, retrieved_at="2026-08-01",
            confidence="UNSCORED", feature_version="v1", provenance_hash="deadbeef",
        )


def test_unknown_feature_value_never_carries_a_fabricated_zero() -> None:
    value = unknown_feature_value(
        player_id="P1", season=2026, as_of="2026-08-01", feature_name="x",
        feature_family=FAMILY_PROJECTIONS, reason="no data",
    )
    assert value.value is None
    assert value.value_status == UNKNOWN


def test_feature_value_from_projection_stat_blocks_on_non_real_source_status() -> None:
    value = feature_value_from_projection_stat(
        player_id="P1", season=2026, as_of="2026-08-01", stat_name="passing_yards",
        stats={"passing_yards": 4000.0}, source_status="missing_paid_or_charted_data",
        evidence_status="OK", source_as_of="2026-08-01", retrieved_at="2026-08-01",
    )
    assert value.value_status == BLOCKED
    assert value.value is None


def test_feature_value_from_projection_stat_returns_known_for_real_data() -> None:
    value = feature_value_from_projection_stat(
        player_id="P1", season=2026, as_of="2026-08-01", stat_name="passing_yards",
        stats={"passing_yards": 4000.0}, source_status="imported_real_data",
        evidence_status="OK", source_as_of="2026-08-01", retrieved_at="2026-08-01",
    )
    assert value.value_status == KNOWN
    assert value.value == 4000.0
    assert value.confidence == "HIGH"


def test_feature_value_from_adp_entry_blocks_unmatched_rows() -> None:
    value = feature_value_from_adp_entry(
        player_id="P1", season=2026, as_of="2026-08-01", overall_adp=45.0,
        source_date="2026-08-01", retrieved_at="2026-08-01", match_status="AMBIGUOUS",
    )
    assert value.value_status == BLOCKED
    assert value.feature_family == FAMILY_MARKET_ADP


def test_feature_value_from_impact_hypothesis_is_never_treated_as_known_numeric_fact() -> None:
    value = feature_value_from_impact_hypothesis(
        player_id="P2", season=2026, as_of="2026-09-01",
        hypothesis_direction="POSITIVE", hypothesis_confidence="LOW",
        generated_at_utc="2026-09-01T00:00:00Z",
    )
    assert value.feature_family == FAMILY_AVAILABILITY
    assert value.value == "POSITIVE"  # qualitative direction, not an invented number
    assert value.confidence == "LOW"


def test_lookup_as_of_never_returns_a_value_from_after_the_requested_date() -> None:
    early = known_feature_value(
        player_id="P1", season=2026, as_of="2026-08-01", feature_name="market.overall_adp",
        feature_family=FAMILY_MARKET_ADP, value=50.0, source="s", source_as_of="2026-08-01",
        retrieved_at="2026-08-01",
    )
    late = known_feature_value(
        player_id="P1", season=2026, as_of="2026-08-20", feature_name="market.overall_adp",
        feature_family=FAMILY_MARKET_ADP, value=30.0, source="s", source_as_of="2026-08-20",
        retrieved_at="2026-08-20",
    )
    store = PointInTimeFeatureStore().with_values([early, late])

    # A query for a date BEFORE the late value's source_as_of must never see it.
    resolved = store.lookup_as_of(
        player_id="P1", season=2026, feature_name="market.overall_adp", as_of="2026-08-10",
    )
    assert resolved.value == 50.0

    # A query for a date on/after the late value resolves to the newer one.
    resolved_late = store.lookup_as_of(
        player_id="P1", season=2026, feature_name="market.overall_adp", as_of="2026-08-25",
    )
    assert resolved_late.value == 30.0


def test_lookup_as_of_returns_explicit_unknown_when_nothing_qualifies() -> None:
    store = PointInTimeFeatureStore()
    resolved = store.lookup_as_of(
        player_id="ghost", season=2026, feature_name="market.overall_adp", as_of="2026-08-10",
    )
    assert resolved.value is None
    assert resolved.value_status == UNKNOWN


def test_lookup_as_of_is_the_core_no_leakage_guarantee_for_historical_replay() -> None:
    # A feature "observed" only after the decision date must never leak into
    # a decision made before it exists -- this is the same guarantee the
    # historical replay data contract enforces at the row level, exercised
    # here at the point-in-time feature-store level.
    future_only = known_feature_value(
        player_id="P9", season=2020, as_of="2021-01-01", feature_name="injury.status",
        feature_family=FAMILY_AVAILABILITY, value="OUT", source="s",
        source_as_of="2021-01-01", retrieved_at="2021-01-01",
    )
    store = PointInTimeFeatureStore().with_values([future_only])
    at_draft_time = store.lookup_as_of(
        player_id="P9", season=2020, feature_name="injury.status", as_of="2020-08-01",
    )
    assert at_draft_time.value_status == UNKNOWN
    assert at_draft_time.value is None
