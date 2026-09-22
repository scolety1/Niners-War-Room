"""ESPN league snapshot schema + loader, sourced via Flaim (2026-09-19).

Design and a safe, pure parser only -- as of this pass, no real Flaim
connection exists from any NWR process (the coordinating session's own
Flaim MCP OAuth login is pending; see
``docs/codex/flaim_integration_20260919/LEDGER.md``). Nothing in this
module calls Flaim, ESPN, or any network endpoint, and nothing in it is
wired into any live facade/endpoint yet. It exists so that once a real
snapshot file lands (a later worker's job, after OAuth completes and the
coordinating session actually calls Flaim's MCP tools), this codebase
already has a documented schema, a validating loader, and a known storage
location -- rather than requiring another design pass at that point.

This module defines:

1. The on-disk JSON schema a future, real snapshot-refresh process must
   produce (`EspnFlaimSnapshot` / `parse_espn_flaim_snapshot` below).
2. Where that file lives, mirroring this codebase's existing Sleeper
   import-receipt convention exactly
   (``local_exports/redraft_v1/sleeper_imports/<profile_id>.json`` ->
   ``local_exports/redraft_v1/espn_flaim_snapshots/<profile_id>.json`` --
   see `espn_flaim_snapshot_path`).
3. A loader that parses and validates a snapshot file against that
   schema, raising a clear, specific error for anything missing or
   malformed rather than silently defaulting.

What NWR is authorized to DO with a real snapshot's data, once one
exists, is a separate, already-recorded policy decision -- see
``docs/hq/master/flaim_scoped_capability_reauthorization_v1_20260919/
CAPABILITY_AUTHORIZATION_MAP.md``. This module only concerns the data
SHAPE and its honest provenance/completeness flags, not usage policy.
Usage policy is enforced downstream by ``league_capability_service.py``
and, eventually, by each individual tool's own capability check.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RosterSlotKind = Literal["STARTER", "BENCH", "RESERVE"]
ScoringCompleteness = Literal["COMPLETE", "PARTIAL", "UNKNOWN"]
PlayerPoolCoverage = Literal["COMPLETE", "BOUNDED", "NONE"]

_VALID_SCORING_COMPLETENESS = ("COMPLETE", "PARTIAL", "UNKNOWN")
_VALID_POOL_COVERAGE = ("COMPLETE", "BOUNDED", "NONE")
_VALID_SLOTS = ("STARTER", "BENCH", "RESERVE")


class EspnFlaimSnapshotError(ValueError):
    """A snapshot file/dict is missing a required field or malformed."""


@dataclass(frozen=True)
class EspnRosterPlayer:
    provider_player_id: str
    player_name: str
    position: str
    team: str
    slot: RosterSlotKind


@dataclass(frozen=True)
class EspnScoringSetting:
    espn_setting_name: str
    value: float
    # None when this ESPN setting has no known NWR-recognized equivalent --
    # mirrors the existing Sleeper receipt's `nwr_setting: ""` convention,
    # using None instead of an empty string for an explicit "unmapped"
    # signal.
    nwr_setting: str | None


@dataclass(frozen=True)
class EspnAvailablePlayer:
    provider_player_id: str
    player_name: str
    position: str
    team: str


@dataclass(frozen=True)
class EspnFlaimSnapshot:
    """One retrieval's worth of real ESPN league facts, fetched via Flaim.

    Every field maps to a row of ``docs/hq/master/
    flaim_scoped_capability_reauthorization_v1_20260919/
    CAPABILITY_AUTHORIZATION_MAP.md`` -- see that file for what each field
    is and is not authorized to be used for. Deliberately has NO
    standings field: the July 2026 audit found Flaim's standings
    "materially misrepresented", and this authorization's capability map
    keeps standings constrained to display-only-with-disclosure at most --
    this schema does not even model it yet, rather than modeling it and
    trusting call sites to remember not to rely on it.
    """

    profile_id: str
    provider_league_id: str
    league_name: str
    season: int
    team_count: int
    owner_team_id: str
    owner_team_name: str
    roster: tuple[EspnRosterPlayer, ...]
    scoring_settings: tuple[EspnScoringSetting, ...]
    scoring_completeness: ScoringCompleteness
    available_player_pool: tuple[EspnAvailablePlayer, ...]
    available_player_pool_coverage: PlayerPoolCoverage
    available_player_pool_bound_description: str | None
    # When THIS retrieval actually happened (when Flaim was actually
    # called). Always required, always set by the refresh process, never
    # inferred or defaulted.
    retrieved_at_utc: str
    # The provider's own published as-of time, if Flaim's response exposed
    # one. July's own finding was that most records lacked this -- so this
    # is explicitly optional and must never be backfilled from
    # retrieved_at_utc.
    provider_as_of_utc: str | None
    source: str = "Flaim MCP (flaim.app), read-only ESPN league data"
    # Local import provenance. Older snapshots/fixtures may omit these;
    # the deterministic importer always records all three on activation.
    imported_at_utc: str | None = None
    source_capture_sha256: str | None = None
    source_capture_name: str | None = None


def espn_flaim_snapshot_path(redraft_root: str | Path, profile_id: str) -> Path:
    """Where a real snapshot for ``profile_id`` would live, once one exists.

    Mirrors the existing Sleeper import-receipt convention exactly.
    """

    return Path(redraft_root) / "espn_flaim_snapshots" / f"{profile_id}.json"


def _require(raw: dict, key: str) -> object:
    value = raw.get(key)
    if value in (None, ""):
        raise EspnFlaimSnapshotError(f"ESPN/Flaim snapshot missing required field: {key!r}")
    return value


def parse_espn_flaim_snapshot(raw: dict) -> EspnFlaimSnapshot:
    """Parse+validate an already-loaded JSON dict into an EspnFlaimSnapshot.

    Raises ``EspnFlaimSnapshotError`` with a specific, actionable message
    for any missing/malformed required field. Never fabricates a default
    for a required identity/retrieval field -- only the explicitly
    optional fields (``provider_as_of_utc``,
    ``available_player_pool_bound_description``, unmapped
    ``nwr_setting``) may be absent.
    """

    profile_id = str(_require(raw, "profile_id"))
    provider_league_id = str(_require(raw, "provider_league_id"))
    league_name = str(_require(raw, "league_name"))
    season = int(_require(raw, "season"))  # type: ignore[arg-type]
    team_count = int(_require(raw, "team_count"))  # type: ignore[arg-type]
    owner_team_id = str(_require(raw, "owner_team_id"))
    owner_team_name = str(_require(raw, "owner_team_name"))
    retrieved_at_utc = str(_require(raw, "retrieved_at_utc"))

    roster_raw = raw.get("roster")
    if not isinstance(roster_raw, Sequence):
        raise EspnFlaimSnapshotError(
            "ESPN/Flaim snapshot missing required field: 'roster' (must be a list)"
        )
    roster: list[EspnRosterPlayer] = []
    for i, p in enumerate(roster_raw):
        try:
            slot = p["slot"]
            if slot not in _VALID_SLOTS:
                raise EspnFlaimSnapshotError(
                    f"ESPN/Flaim snapshot roster[{i}].slot must be one of "
                    f"{_VALID_SLOTS}, got {slot!r}"
                )
            roster.append(
                EspnRosterPlayer(
                    provider_player_id=str(p["provider_player_id"]),
                    player_name=str(p["player_name"]),
                    position=str(p["position"]),
                    team=str(p["team"]),
                    slot=slot,
                )
            )
        except KeyError as exc:
            raise EspnFlaimSnapshotError(
                f"ESPN/Flaim snapshot roster[{i}] missing required field: {exc}"
            ) from exc

    scoring_settings = tuple(
        EspnScoringSetting(
            espn_setting_name=str(s["espn_setting_name"]),
            value=float(s["value"]),
            nwr_setting=s.get("nwr_setting"),
        )
        for s in raw.get("scoring_settings", [])
    )
    scoring_completeness = raw.get("scoring_completeness", "UNKNOWN")
    if scoring_completeness not in _VALID_SCORING_COMPLETENESS:
        raise EspnFlaimSnapshotError(
            "ESPN/Flaim snapshot 'scoring_completeness' must be one of "
            f"{_VALID_SCORING_COMPLETENESS}, got {scoring_completeness!r}"
        )

    available_player_pool = tuple(
        EspnAvailablePlayer(
            provider_player_id=str(p["provider_player_id"]),
            player_name=str(p["player_name"]),
            position=str(p["position"]),
            team=str(p["team"]),
        )
        for p in raw.get("available_player_pool", [])
    )
    pool_coverage = raw.get("available_player_pool_coverage", "NONE")
    if pool_coverage not in _VALID_POOL_COVERAGE:
        raise EspnFlaimSnapshotError(
            "ESPN/Flaim snapshot 'available_player_pool_coverage' must be one of "
            f"{_VALID_POOL_COVERAGE}, got {pool_coverage!r}"
        )
    if pool_coverage == "COMPLETE":
        # Per the July 2026 audit's own finding (free-agent retrieval was
        # "capped, alphabetic, noisy, incomplete"), a Flaim-sourced pool
        # claiming COMPLETE coverage is treated as a data error, not a
        # legitimate state, unless a future, explicit reentry-trigger
        # decision revisits this. See CAPABILITY_AUTHORIZATION_MAP.md.
        raise EspnFlaimSnapshotError(
            "ESPN/Flaim snapshot claims available_player_pool_coverage=COMPLETE, which is "
            "not an authorized state for Flaim-sourced data -- see docs/hq/master/"
            "flaim_scoped_capability_reauthorization_v1_20260919/CAPABILITY_AUTHORIZATION_MAP.md"
        )

    return EspnFlaimSnapshot(
        profile_id=profile_id,
        provider_league_id=provider_league_id,
        league_name=league_name,
        season=season,
        team_count=team_count,
        owner_team_id=owner_team_id,
        owner_team_name=owner_team_name,
        roster=tuple(roster),
        scoring_settings=scoring_settings,
        scoring_completeness=scoring_completeness,
        available_player_pool=available_player_pool,
        available_player_pool_coverage=pool_coverage,
        available_player_pool_bound_description=raw.get("available_player_pool_bound_description"),
        retrieved_at_utc=retrieved_at_utc,
        provider_as_of_utc=raw.get("provider_as_of_utc"),
        source=raw.get("source", "Flaim MCP (flaim.app), read-only ESPN league data"),
        imported_at_utc=raw.get("imported_at_utc"),
        source_capture_sha256=raw.get("source_capture_sha256"),
        source_capture_name=raw.get("source_capture_name"),
    )


def load_espn_flaim_snapshot(redraft_root: str | Path, profile_id: str) -> EspnFlaimSnapshot | None:
    """Load a real snapshot from disk if one exists; ``None`` if it doesn't.

    Never raises for a simply-missing file -- that is the normal, current
    state for every real profile as of this pass (no real snapshot has
    been fetched yet; Flaim OAuth is still pending). Raises
    ``EspnFlaimSnapshotError`` for a present-but-malformed file, since
    silently treating a corrupt snapshot as "absent" would be a worse
    failure mode than a loud, specific one.
    """

    path = espn_flaim_snapshot_path(redraft_root, profile_id)
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return parse_espn_flaim_snapshot(raw)
