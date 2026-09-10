from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from src.services.weekly_projection_service import WeeklyProjectionError
from src.services.weekly_projection_provider_service import (
    SleeperWeeklyProjectionProvider,
    WeeklyProjectionHealth,
    _atomic_json,
    _health_path,
    default_weekly_projection_provider,
    get_weekly_projections,
    validate_weekly_projection_schema,
)


def _plausible_payload(n: int = 1200, nonzero: int = 200) -> dict[str, dict[str, float]]:
    payload: dict[str, dict[str, float]] = {}
    for i in range(n):
        payload[str(i)] = {"pts_ppr": 5.0 if i < nonzero else 0.0, "pass_yd": 10.0}
    return payload


@dataclass
class _FakeProvider:
    provider_name: str = "FAKE"
    source_endpoint: str = "fake://endpoint"
    integration_status: str = "EXPERIMENTAL_EXTERNAL"
    payload: dict | None = None
    error: Exception | None = None
    calls: list = field(default_factory=list)

    def fetch_raw(self, *, season: int, week: int, season_type: str):
        self.calls.append((season, week, season_type))
        if self.error is not None:
            raise self.error
        return self.payload if self.payload is not None else {}


def test_default_provider_is_sleeper_stopgap() -> None:
    provider = default_weekly_projection_provider()
    assert isinstance(provider, SleeperWeeklyProjectionProvider)
    assert provider.provider_name == "SLEEPER"
    assert provider.integration_status == "EXPERIMENTAL_EXTERNAL"


def test_sleeper_provider_delegates_to_the_real_fetch_function(monkeypatch) -> None:
    captured = {}

    def _fake_fetch(*, season, week, season_type, http):
        captured["args"] = (season, week, season_type)
        return {"1": {"pts_ppr": 1.0}}

    monkeypatch.setattr(
        "src.services.weekly_projection_provider_service.fetch_sleeper_weekly_projections", _fake_fetch
    )
    provider = SleeperWeeklyProjectionProvider()
    result = provider.fetch_raw(season=2026, week=1, season_type="regular")
    assert result == {"1": {"pts_ppr": 1.0}}
    assert captured["args"] == (2026, 1, "regular")


def test_schema_validation_flags_empty_payload() -> None:
    assert "EMPTY_PAYLOAD" in validate_weekly_projection_schema({})


def test_schema_validation_flags_low_row_count() -> None:
    issues = validate_weekly_projection_schema({"1": {"pts_ppr": 1.0}})
    assert any(issue.startswith("ROW_COUNT_BELOW_FLOOR") for issue in issues)


def test_schema_validation_flags_all_zero_as_failure_not_legitimate_forecast() -> None:
    payload = {str(i): {"pts_ppr": 0.0} for i in range(1200)}
    issues = validate_weekly_projection_schema(payload)
    assert any(issue.startswith("NONZERO_PROJECTION_COUNT_BELOW_FLOOR") for issue in issues)


def test_schema_validation_flags_majority_malformed_rows() -> None:
    payload = {str(i): "not-a-dict" for i in range(1200)}
    issues = validate_weekly_projection_schema(payload)
    assert any(issue.startswith("MAJORITY_MALFORMED_ROWS") for issue in issues)


def test_valid_payload_has_no_issues() -> None:
    assert validate_weekly_projection_schema(_plausible_payload()) == []


def test_live_fetch_persists_health_and_snapshot(tmp_path) -> None:
    provider = _FakeProvider(payload=_plausible_payload())
    raw, health = get_weekly_projections(
        provider=provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path,
    )
    assert raw == provider.payload
    assert health.status == "OK"
    assert health.freshness == "LIVE"
    assert health.provider == "FAKE"
    assert health.total_rows == 1200
    assert health.nonzero_projection_rows == 200
    assert health.schema_fingerprint
    assert health.payload_hash
    assert _health_path(tmp_path, league_id="league-1", season=2026, week=1).exists()


def test_repeated_call_within_ttl_is_served_from_cache_without_refetching(tmp_path) -> None:
    provider = _FakeProvider(payload=_plausible_payload())
    get_weekly_projections(
        provider=provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path,
    )
    assert len(provider.calls) == 1
    _raw, health = get_weekly_projections(
        provider=provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path,
    )
    assert len(provider.calls) == 1  # no second live fetch -- served from cache
    assert health.served_from_cache is True
    assert health.freshness == "LIVE"


def test_force_refresh_bypasses_the_cache(tmp_path) -> None:
    provider = _FakeProvider(payload=_plausible_payload())
    get_weekly_projections(
        provider=provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path,
    )
    _raw, health = get_weekly_projections(
        provider=provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path, force_refresh=True,
    )
    assert len(provider.calls) == 2
    assert health.served_from_cache is False


def test_stale_snapshot_reused_on_live_failure_and_labeled_stale(tmp_path) -> None:
    good_provider = _FakeProvider(payload=_plausible_payload())
    get_weekly_projections(
        provider=good_provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path,
    )
    failing_provider = _FakeProvider(error=WeeklyProjectionError("network down"))
    raw, health = get_weekly_projections(
        provider=failing_provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path, force_refresh=True,
    )
    assert raw == good_provider.payload
    assert health.status == "DEGRADED"
    assert health.freshness == "STALE"
    assert any(issue.startswith("LIVE_FETCH_FAILED") for issue in health.issues)


def test_no_snapshot_and_failed_fetch_raises_honestly(tmp_path) -> None:
    failing_provider = _FakeProvider(error=WeeklyProjectionError("network down"))
    with pytest.raises(WeeklyProjectionError):
        get_weekly_projections(
            provider=failing_provider, season=2026, week=1, season_type="regular",
            league_id="league-1", redraft_root=tmp_path,
        )


def test_stale_snapshot_too_old_is_not_reused(tmp_path) -> None:
    good_provider = _FakeProvider(payload=_plausible_payload())
    _raw, health = get_weekly_projections(
        provider=good_provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path,
    )
    # Manually age the persisted snapshot beyond the stale-reuse ceiling.
    path = _health_path(tmp_path, league_id="league-1", season=2026, week=1)
    import json

    document = json.loads(path.read_text(encoding="utf-8"))
    ancient = (datetime.now(UTC) - timedelta(hours=999)).isoformat()
    document["health"]["retrievedAt"] = ancient
    _atomic_json(path, document)

    failing_provider = _FakeProvider(error=WeeklyProjectionError("network down"))
    with pytest.raises(WeeklyProjectionError):
        get_weekly_projections(
            provider=failing_provider, season=2026, week=1, season_type="regular",
            league_id="league-1", redraft_root=tmp_path, force_refresh=True,
        )


def test_coverage_collapse_with_no_fallback_snapshot_raises(tmp_path) -> None:
    good_provider = _FakeProvider(payload=_plausible_payload(n=9000, nonzero=800))
    get_weekly_projections(
        provider=good_provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path,
    )
    collapsed_provider = _FakeProvider(payload=_plausible_payload(n=1500, nonzero=100))
    with pytest.raises(WeeklyProjectionError):
        get_weekly_projections(
            provider=collapsed_provider, season=2026, week=2, season_type="regular",
            league_id="league-1", redraft_root=tmp_path,
        )


def test_health_to_dict_round_trips_camel_case_keys(tmp_path) -> None:
    provider = _FakeProvider(payload=_plausible_payload())
    _raw, health = get_weekly_projections(
        provider=provider, season=2026, week=1, season_type="regular",
        league_id="league-1", redraft_root=tmp_path,
    )
    document = health.to_dict()
    for key in ("provider", "sourceEndpoint", "integrationStatus", "retrievedAt", "totalRows", "freshness", "issues"):
        assert key in document
