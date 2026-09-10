"""Canonical weekly-projection PROVIDER abstraction (NWR in-season UI pass,
2026-09-10).

Owner governance decision (2026-09-10): the live Sleeper weekly-projection
endpoint is APPROVED as a TEMPORARY/STOPGAP provider ONLY -- it must not be
hard-wired throughout the architecture. This module is the ONE seam every
consumer goes through. `desktop_facade.py`'s weekly-projections/weekly-
lineup/waivers/weekly-home-actions methods call `get_weekly_projections()`
below; none of them import `SleeperHttpClient` or call
`fetch_sleeper_weekly_projections` directly, and neither does any other
consumer (Compare, Trade). Adding a second provider (ESPN, FantasyPros) is
writing one more `WeeklyProjectionProvider` implementation and changing the
one line in `default_weekly_projection_provider()` -- no consumer changes.

This module also owns FAIL-SAFE behavior, because the wrapped endpoint is
undocumented and could change or degrade without notice (see
`weekly_projection_service.py`'s own module docstring for the full
disclosure this module inherits):

  * Every fetch is schema-validated (`validate_weekly_projection_schema`)
    before it is treated as usable -- a syntactically valid but empty,
    mostly-malformed, or collapsed-coverage payload is a FAILURE SIGNAL,
    never a legitimate all-zero forecast.
  * A structural fingerprint and a full-payload hash are persisted with
    every successful fetch so a real schema change (renamed/removed stat
    fields) or a byte-identical re-serve is visible after the fact, not
    just inferred.
  * A short-TTL on-disk cache (`_CACHE_TTL_MINUTES`) avoids hammering the
    undocumented endpoint when multiple panels (Weekly Home, Start/Sit,
    Waivers) each ask for the same league/season/week within the same
    short window -- NOT a long-lived cache, and never silently reused
    across a DIFFERENT week.
  * On a live-fetch failure (network error, malformed envelope, or failed
    validation), the last known-good snapshot for the SAME league/season/
    week is reused ONLY if it is not older than `_MAX_STALE_SNAPSHOT_AGE_
    HOURS`, and is always labeled `freshness="STALE"` with the failure
    reason recorded in `issues` -- never silently re-served as if live.
    If no usable snapshot exists, the caller gets an honest
    `WeeklyProjectionError`, never a fabricated result.
  * This module NEVER falls back from weekly projections to the season-
    long ranking as a substitute -- that would silently mix incompatible
    scales. A weekly-dependent caller that cannot get a usable weekly
    snapshot must disclose "weekly projections unavailable", not quietly
    substitute a different number.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable
from uuid import uuid4

from src.services.sleeper_import_service import SleeperHttpClient
from src.services.weekly_projection_service import (
    WeeklyProjectionError,
    fetch_sleeper_weekly_projections,
)

WEEKLY_PROJECTION_HEALTH_SCHEMA_VERSION = 1

# Real-world floor from this branch's own live verification (~9,420 total
# rows / ~863 nonzero Week-1 2026 entries, recorded in the prior pass's
# freeze doc). A generous absolute floor meant to catch a genuinely broken
# or empty payload -- NOT tuned to reject real week-to-week variance (bye
# weeks, roster churn, etc. legitimately move these counts around).
_MIN_PLAUSIBLE_TOTAL_ROWS = 1000
_MIN_PLAUSIBLE_NONZERO_ROWS = 50
# A fetch this much smaller than the most recent known-good fetch for the
# SAME league (any week, same season) is treated as a coverage-collapse
# signal rather than legitimate variance. Disclosed heuristic ratio, not a
# statistically derived one.
_COVERAGE_COLLAPSE_RATIO = 0.4
_MAX_STALE_SNAPSHOT_AGE_HOURS = 36
_CACHE_TTL_MINUTES = 5


class WeeklyProjectionSourceError(RuntimeError):
    """A syntactically valid response that failed post-fetch validation
    (empty, malformed-majority, or coverage-collapsed) -- routed through the
    same fail-safe path as a hard network failure."""


@runtime_checkable
class WeeklyProjectionProvider(Protocol):
    """Implement this Protocol to add a new weekly-projection source. No
    other consumer in this codebase should need to change."""

    provider_name: str
    source_endpoint: str
    integration_status: str  # "EXPERIMENTAL_EXTERNAL" | "OFFICIAL_DOCUMENTED"

    def fetch_raw(
        self, *, season: int, week: int, season_type: str
    ) -> Mapping[str, Mapping[str, Any]]:
        """Raw provider payload keyed by the provider's own player id. MUST
        raise on any fetch or parse failure -- never return a fabricated or
        silently-empty payload."""
        ...


@dataclass(frozen=True)
class SleeperWeeklyProjectionProvider:
    """TEMPORARY/STOPGAP provider per the 2026-09-10 owner governance
    decision. This is the ONLY class in the provider layer that mentions
    Sleeper -- see `weekly_projection_service.py` for the full disclosure
    (undocumented endpoint, non-commercial-use posture, no per-player
    variance figure, no schema-stability guarantee)."""

    provider_name: str = "SLEEPER"
    source_endpoint: str = "GET api.sleeper.app/v1/projections/nfl/{season_type}/{season}/{week}"
    integration_status: str = "EXPERIMENTAL_EXTERNAL"
    http: SleeperHttpClient | None = None

    def fetch_raw(
        self, *, season: int, week: int, season_type: str
    ) -> Mapping[str, Mapping[str, Any]]:
        return fetch_sleeper_weekly_projections(
            season=season, week=week, season_type=season_type, http=self.http or SleeperHttpClient()
        )


def default_weekly_projection_provider() -> WeeklyProjectionProvider:
    """The ONE place a caller asks for "whichever provider is currently
    wired in" without naming Sleeper. Swapping the stopgap provider for a
    permanent one, or adding a second provider with its own selection
    policy, is a change confined to this function."""

    return SleeperWeeklyProjectionProvider()


@dataclass(frozen=True)
class WeeklyProjectionHealth:
    schema_version: int
    provider: str
    source_endpoint: str
    integration_status: str
    season: int
    week: int
    season_type: str
    league_id: str
    retrieved_at: str
    schema_fingerprint: str
    payload_hash: str
    total_rows: int
    nonzero_projection_rows: int
    status: str  # OK | DEGRADED | UNAVAILABLE
    freshness: str  # LIVE | STALE
    served_from_cache: bool = False
    issues: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "provider": self.provider,
            "sourceEndpoint": self.source_endpoint,
            "integrationStatus": self.integration_status,
            "season": self.season,
            "week": self.week,
            "seasonType": self.season_type,
            "leagueId": self.league_id,
            "retrievedAt": self.retrieved_at,
            "schemaFingerprint": self.schema_fingerprint,
            "payloadHash": self.payload_hash,
            "totalRows": self.total_rows,
            "nonzeroProjectionRows": self.nonzero_projection_rows,
            "status": self.status,
            "freshness": self.freshness,
            "servedFromCache": self.served_from_cache,
            "issues": list(self.issues),
        }


def _schema_fingerprint(raw: Mapping[str, Mapping[str, Any]]) -> str:
    """Cheap structural fingerprint: the sorted set of stat field names seen
    across a bounded sample. A real schema change (fields renamed/removed)
    changes this fingerprint even though the payload stays syntactically
    valid JSON; ordinary roster churn does not."""

    sample_keys: set[str] = set()
    for _, entry in list(raw.items())[:200]:
        if isinstance(entry, Mapping):
            sample_keys.update(str(key) for key in entry.keys())
    return hashlib.sha256(",".join(sorted(sample_keys)).encode("utf-8")).hexdigest()[:16]


def _payload_hash(raw: Mapping[str, Mapping[str, Any]]) -> str:
    try:
        canonical = json.dumps(raw, sort_keys=True, default=str)
    except (TypeError, ValueError):
        canonical = repr(raw)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_weekly_projection_schema(raw: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Real structural checks distinct from `fetch_sleeper_weekly_
    projections`'s own raise-on-malformed-envelope check -- these catch a
    SYNTACTICALLY valid but substantively broken or degraded payload
    (empty, mostly-malformed rows, or a coverage collapse toward all-zero).
    Zero projections across the board is treated as a failure signal, not
    a legitimate forecast."""

    issues: list[str] = []
    if not raw:
        issues.append("EMPTY_PAYLOAD")
        return issues
    total = len(raw)
    if total < _MIN_PLAUSIBLE_TOTAL_ROWS:
        issues.append(f"ROW_COUNT_BELOW_FLOOR({total}<{_MIN_PLAUSIBLE_TOTAL_ROWS})")
    malformed = 0
    nonzero = 0
    for _, entry in raw.items():
        if not isinstance(entry, Mapping):
            malformed += 1
            continue
        points = entry.get("pts_ppr")
        if isinstance(points, (int, float)) and not isinstance(points, bool) and points:
            nonzero += 1
    if total and malformed > total * 0.5:
        issues.append(f"MAJORITY_MALFORMED_ROWS({malformed}/{total})")
    if nonzero < _MIN_PLAUSIBLE_NONZERO_ROWS:
        issues.append(f"NONZERO_PROJECTION_COUNT_BELOW_FLOOR({nonzero}<{_MIN_PLAUSIBLE_NONZERO_ROWS})")
    return issues


def _count_nonzero(raw: Mapping[str, Mapping[str, Any]]) -> int:
    return sum(
        1
        for entry in raw.values()
        if isinstance(entry, Mapping)
        and isinstance(entry.get("pts_ppr"), (int, float))
        and not isinstance(entry.get("pts_ppr"), bool)
        and entry.get("pts_ppr")
    )


def _atomic_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def _safe_segment(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in str(value)) or "unknown"


def _health_dir(redraft_root: str | Path) -> Path:
    return Path(redraft_root) / "weekly_projection_health"


def _health_path(redraft_root: str | Path, *, league_id: str, season: int, week: int) -> Path:
    return _health_dir(redraft_root) / f"{_safe_segment(league_id)}_{season}_{week}.json"


def _health_from_dict(document: Mapping[str, Any]) -> WeeklyProjectionHealth:
    return WeeklyProjectionHealth(
        schema_version=int(document.get("schemaVersion", WEEKLY_PROJECTION_HEALTH_SCHEMA_VERSION)),
        provider=str(document["provider"]),
        source_endpoint=str(document["sourceEndpoint"]),
        integration_status=str(document["integrationStatus"]),
        season=int(document["season"]),
        week=int(document["week"]),
        season_type=str(document["seasonType"]),
        league_id=str(document["leagueId"]),
        retrieved_at=str(document["retrievedAt"]),
        schema_fingerprint=str(document["schemaFingerprint"]),
        payload_hash=str(document["payloadHash"]),
        total_rows=int(document["totalRows"]),
        nonzero_projection_rows=int(document["nonzeroProjectionRows"]),
        status=str(document["status"]),
        freshness=str(document["freshness"]),
        served_from_cache=bool(document.get("servedFromCache", False)),
        issues=tuple(document.get("issues", ())),
    )


def _write_snapshot(
    redraft_root: str | Path,
    *,
    health: WeeklyProjectionHealth,
    raw: Mapping[str, Mapping[str, Any]],
) -> None:
    path = _health_path(redraft_root, league_id=health.league_id, season=health.season, week=health.week)
    try:
        _atomic_json(path, {"health": health.to_dict(), "raw": raw})
    except OSError:
        pass  # Persistence is best-effort -- a write failure must not break a live fetch that just succeeded.


def _read_snapshot(
    redraft_root: str | Path, *, league_id: str, season: int, week: int
) -> tuple[WeeklyProjectionHealth, Mapping[str, Mapping[str, Any]]] | None:
    path = _health_path(redraft_root, league_id=league_id, season=season, week=week)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        return _health_from_dict(document["health"]), document["raw"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _latest_health_for_league(redraft_root: str | Path, league_id: str) -> WeeklyProjectionHealth | None:
    """Most recent OK snapshot for this league across ANY week -- used only
    as a coverage-collapse baseline, never served as the answer to a
    different week's request."""

    directory = _health_dir(redraft_root)
    prefix = f"{_safe_segment(league_id)}_"
    best: WeeklyProjectionHealth | None = None
    try:
        candidates = list(directory.glob(f"{prefix}*.json"))
    except OSError:
        return None
    for candidate in candidates:
        try:
            document = json.loads(candidate.read_text(encoding="utf-8"))
            health = _health_from_dict(document["health"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if health.status != "OK":
            continue
        if best is None or health.retrieved_at > best.retrieved_at:
            best = health
    return best


def _age_hours(retrieved_at: str, *, now: datetime) -> float:
    try:
        retrieved = datetime.fromisoformat(retrieved_at)
    except ValueError:
        return float("inf")
    if retrieved.tzinfo is None:
        retrieved = retrieved.replace(tzinfo=UTC)
    return (now - retrieved).total_seconds() / 3600.0


def get_weekly_projections(
    *,
    provider: WeeklyProjectionProvider,
    season: int,
    week: int,
    season_type: str,
    league_id: str,
    redraft_root: str | Path,
    force_refresh: bool = False,
) -> tuple[Mapping[str, Mapping[str, Any]], WeeklyProjectionHealth]:
    """THE canonical seam every in-season consumer calls -- never
    `fetch_sleeper_weekly_projections` directly. Returns the raw payload
    plus a health record describing exactly how fresh/trustworthy it is.
    Raises `WeeklyProjectionError` only when there is truly nothing usable
    to return (no live fetch succeeded and no recent-enough snapshot
    exists) -- callers must treat that as "unavailable this week", never
    substitute season-long projections."""

    now = datetime.now(UTC)

    if not force_refresh:
        cached = _read_snapshot(redraft_root, league_id=league_id, season=season, week=week)
        if cached is not None:
            cached_health, cached_raw = cached
            if (
                cached_health.status == "OK"
                and cached_health.freshness == "LIVE"
                and _age_hours(cached_health.retrieved_at, now=now) * 60 <= _CACHE_TTL_MINUTES
            ):
                return cached_raw, replace(cached_health, served_from_cache=True)

    try:
        raw = provider.fetch_raw(season=season, week=week, season_type=season_type)
        issues = validate_weekly_projection_schema(raw)
        baseline = _latest_health_for_league(redraft_root, league_id)
        total = len(raw)
        if baseline is not None and baseline.total_rows > 0 and total < baseline.total_rows * _COVERAGE_COLLAPSE_RATIO:
            issues.append(
                f"COVERAGE_COLLAPSE_VS_RECENT_BASELINE({total}<{_COVERAGE_COLLAPSE_RATIO:.0%}_of_{baseline.total_rows})"
            )
        if issues:
            # Syntactically valid but substantively broken -- route through
            # the SAME fail-safe path a hard network failure takes below.
            raise WeeklyProjectionSourceError(
                f"Weekly-projection payload from {provider.provider_name} failed validation: "
                + ", ".join(issues)
            )
        health = WeeklyProjectionHealth(
            schema_version=WEEKLY_PROJECTION_HEALTH_SCHEMA_VERSION,
            provider=provider.provider_name,
            source_endpoint=provider.source_endpoint,
            integration_status=provider.integration_status,
            season=season,
            week=week,
            season_type=season_type,
            league_id=league_id,
            retrieved_at=now.isoformat(),
            schema_fingerprint=_schema_fingerprint(raw),
            payload_hash=_payload_hash(raw),
            total_rows=total,
            nonzero_projection_rows=_count_nonzero(raw),
            status="OK",
            freshness="LIVE",
        )
        _write_snapshot(redraft_root, health=health, raw=raw)
        return raw, health
    except (WeeklyProjectionError, WeeklyProjectionSourceError, OSError, ValueError) as exc:
        stale = _read_snapshot(redraft_root, league_id=league_id, season=season, week=week)
        if stale is not None:
            stale_health, stale_raw = stale
            if stale_health.status == "OK" and _age_hours(stale_health.retrieved_at, now=now) <= _MAX_STALE_SNAPSHOT_AGE_HOURS:
                degraded = replace(
                    stale_health,
                    status="DEGRADED",
                    freshness="STALE",
                    served_from_cache=False,
                    issues=stale_health.issues + (f"LIVE_FETCH_FAILED:{exc}",),
                )
                return stale_raw, degraded
        raise WeeklyProjectionError(
            f"Weekly projections are UNAVAILABLE for week {week}: live fetch failed ({exc}) and no "
            "usable recent snapshot exists. Never silently reused a stale, fabricated, or season-long "
            "substitute."
        ) from exc
