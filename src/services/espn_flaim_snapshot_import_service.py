"""Deterministic ESPN/Flaim snapshot transform, validation, and activation.

This module deliberately performs no network I/O.  An authenticated session
does the provider fetch and saves one JSON capture; this module turns that
capture into the existing :class:`EspnFlaimSnapshot` schema and installs it
locally only after strict identity validation.

The supported raw capture contract is ``nwr_espn_flaim_raw_capture_v1``::

    {
      "capture_schema": "nwr_espn_flaim_raw_capture_v1",
      "profile_id": "<existing NWR profile id>",
      "retrieved_at_utc": "2026-09-22T06:30:00Z",
      "get_league_info": {
        "league_id": "123", "league_name": "Example", "season": 2026,
        "team_count": 10, "owner_team_id": "7", "owner_team_name": "My Team",
        "scoring_settings": [
          {"name": "passingYards", "value": 0.04, "nwr_setting": "pass_yard"}
        ],
        "provider_as_of_utc": null
      },
      "get_roster": {
        "team_id": "7", "team_name": "My Team",
        "players": [
          {"player_id": "1", "player_name": "Player", "position": "RB",
           "pro_team": "SF", "slot": "STARTER"}
        ]
      },
      "get_free_agents": {
        "coverage": "BOUNDED",
        "bound_description": "First 100 rows returned by Flaim get_free_agents",
        "players": [
          {"player_id": "2", "player_name": "Available", "position": "WR",
           "pro_team": "MIN"}
        ]
      }
    }

The field names above are a best-effort, NWR-owned capture contract, not a
claim about Flaim's undocumented wire format.  Tomorrow's authenticated
session should copy the three tool responses into these named sections while
preserving their factual values.  The transformer intentionally accepts only
this explicit shape: silently guessing aliases in private provider output
would make identity mistakes much harder to detect.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from src.services.espn_flaim_snapshot_service import (
    EspnFlaimSnapshot,
    EspnFlaimSnapshotError,
    espn_flaim_snapshot_path,
    parse_espn_flaim_snapshot,
)
from src.services.redraft_engine_v1_service import (
    LeagueProfile,
    RedraftPersistenceError,
    RedraftValidationError,
    load_profile,
)

RAW_CAPTURE_SCHEMA = "nwr_espn_flaim_raw_capture_v1"
DEFAULT_SOURCE = "Flaim MCP (flaim.app), read-only ESPN league data"

# These are every scalar scoring input on the current Redraft ScoringSettings
# model.  COMPLETE is earned only when all are explicitly mapped.  Bonuses are
# open-ended and therefore cannot honestly be proven complete by this v1 raw
# contract; a capture with any unmapped provider field remains PARTIAL.
_REQUIRED_COMPLETE_NWR_SCORING_FIELDS = frozenset(
    {
        "pass_yard",
        "pass_td",
        "interception",
        "rush_yard",
        "rush_td",
        "reception",
        "rec_yard",
        "rec_td",
        "return_td",
        "fumble_lost",
        "te_premium",
    }
)
_VALID_SLOTS = frozenset({"STARTER", "BENCH", "RESERVE"})
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class EspnSnapshotImportError(ValueError):
    """A raw capture, identity check, backup, or activation failed safely."""


@dataclass(frozen=True)
class SnapshotImportExpectations:
    """Operator-confirmed provider identity not stored on ESPN profiles."""

    provider_league_id: str
    owner_team_id: str
    owner_team_name: str


@dataclass(frozen=True)
class SnapshotActivationResult:
    profile_id: str
    target_path: Path
    backup_path: Path | None
    snapshot_sha256: str
    imported_at_utc: str


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EspnSnapshotImportError(f"{label} must be a JSON object.")
    return value


def _list_of_mappings(value: object, label: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise EspnSnapshotImportError(f"{label} must be a JSON list.")
    rows: list[Mapping[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise EspnSnapshotImportError(f"{label}[{index}] must be a JSON object.")
        rows.append(row)
    return tuple(rows)


def _required_text(row: Mapping[str, Any], key: str, label: str) -> str:
    value = row.get(key)
    text = str(value).strip() if value is not None else ""
    if not text:
        raise EspnSnapshotImportError(f"{label} missing required field {key!r}.")
    return text


def _required_int(row: Mapping[str, Any], key: str, label: str) -> int:
    value = row.get(key)
    if isinstance(value, bool):
        raise EspnSnapshotImportError(f"{label}.{key} must be an integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise EspnSnapshotImportError(f"{label}.{key} must be an integer.") from exc
    if parsed <= 0:
        raise EspnSnapshotImportError(f"{label}.{key} must be positive.")
    return parsed


def _utc_timestamp(value: object, label: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise EspnSnapshotImportError(f"{label} is required.")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EspnSnapshotImportError(f"{label} must be an ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise EspnSnapshotImportError(f"{label} must include an explicit UTC offset.")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _normalized_identity(value: str) -> str:
    return " ".join(value.casefold().split())


def _scoring_rows(
    raw: object,
) -> tuple[list[dict[str, Any]], Literal["COMPLETE", "PARTIAL", "UNKNOWN"]]:
    rows = _list_of_mappings(raw, "get_league_info.scoring_settings")
    transformed: list[dict[str, Any]] = []
    mapped_fields: set[str] = set()
    has_unmapped = False
    for index, row in enumerate(rows):
        label = f"get_league_info.scoring_settings[{index}]"
        name = _required_text(row, "name", label)
        value = row.get("value")
        if isinstance(value, bool):
            raise EspnSnapshotImportError(f"{label}.value must be numeric.")
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise EspnSnapshotImportError(f"{label}.value must be numeric.") from exc
        nwr_setting_raw = row.get("nwr_setting")
        nwr_setting = str(nwr_setting_raw).strip() if nwr_setting_raw not in (None, "") else None
        if nwr_setting is None:
            has_unmapped = True
        else:
            mapped_fields.add(nwr_setting)
        transformed.append(
            {
                "espn_setting_name": name,
                "value": numeric_value,
                "nwr_setting": nwr_setting,
            }
        )
    if not transformed:
        completeness: Literal["COMPLETE", "PARTIAL", "UNKNOWN"] = "UNKNOWN"
    elif not has_unmapped and _REQUIRED_COMPLETE_NWR_SCORING_FIELDS.issubset(mapped_fields):
        completeness = "COMPLETE"
    else:
        completeness = "PARTIAL"
    return transformed, completeness


def transform_flaim_raw_capture(raw: Mapping[str, Any]) -> EspnFlaimSnapshot:
    """Transform the explicit raw-capture contract into the existing schema."""

    if raw.get("capture_schema") != RAW_CAPTURE_SCHEMA:
        raise EspnSnapshotImportError(
            f"capture_schema must be {RAW_CAPTURE_SCHEMA!r}; no other raw shape is guessed."
        )
    profile_id = _required_text(raw, "profile_id", "raw capture")
    retrieved_at_utc = _utc_timestamp(raw.get("retrieved_at_utc"), "retrieved_at_utc")
    league = _mapping(raw.get("get_league_info"), "get_league_info")
    roster = _mapping(raw.get("get_roster"), "get_roster")
    free_agents = _mapping(raw.get("get_free_agents"), "get_free_agents")

    provider_league_id = _required_text(league, "league_id", "get_league_info")
    league_name = _required_text(league, "league_name", "get_league_info")
    season = _required_int(league, "season", "get_league_info")
    team_count = _required_int(league, "team_count", "get_league_info")
    owner_team_id = _required_text(league, "owner_team_id", "get_league_info")
    owner_team_name = _required_text(league, "owner_team_name", "get_league_info")

    if _required_text(roster, "team_id", "get_roster") != owner_team_id:
        raise EspnSnapshotImportError(
            "get_roster.team_id does not match get_league_info.owner_team_id."
        )
    if _normalized_identity(
        _required_text(roster, "team_name", "get_roster")
    ) != _normalized_identity(owner_team_name):
        raise EspnSnapshotImportError(
            "get_roster.team_name does not match get_league_info.owner_team_name."
        )

    roster_rows: list[dict[str, Any]] = []
    for index, player in enumerate(_list_of_mappings(roster.get("players"), "get_roster.players")):
        label = f"get_roster.players[{index}]"
        slot = _required_text(player, "slot", label).upper()
        if slot not in _VALID_SLOTS:
            raise EspnSnapshotImportError(
                f"{label}.slot must be STARTER, BENCH, or RESERVE; got {slot!r}."
            )
        roster_rows.append(
            {
                "provider_player_id": _required_text(player, "player_id", label),
                "player_name": _required_text(player, "player_name", label),
                "position": _required_text(player, "position", label).upper(),
                "team": _required_text(player, "pro_team", label).upper(),
                "slot": slot,
            }
        )
    if not roster_rows:
        raise EspnSnapshotImportError("get_roster.players must contain at least one player.")

    scoring_settings, scoring_completeness = _scoring_rows(league.get("scoring_settings", []))

    coverage = _required_text(free_agents, "coverage", "get_free_agents").upper()
    if coverage == "COMPLETE":
        raise EspnSnapshotImportError(
            "get_free_agents.coverage=COMPLETE is forbidden for Flaim data; use BOUNDED "
            "with an exact bound description or NONE."
        )
    if coverage not in {"BOUNDED", "NONE"}:
        raise EspnSnapshotImportError("get_free_agents.coverage must be BOUNDED or NONE.")
    bound_description_raw = free_agents.get("bound_description")
    bound_description = (
        str(bound_description_raw).strip() if bound_description_raw not in (None, "") else None
    )
    if coverage == "BOUNDED" and not bound_description:
        raise EspnSnapshotImportError(
            "get_free_agents.bound_description is required when coverage is BOUNDED."
        )
    available_rows: list[dict[str, Any]] = []
    for index, player in enumerate(
        _list_of_mappings(free_agents.get("players", []), "get_free_agents.players")
    ):
        label = f"get_free_agents.players[{index}]"
        available_rows.append(
            {
                "provider_player_id": _required_text(player, "player_id", label),
                "player_name": _required_text(player, "player_name", label),
                "position": _required_text(player, "position", label).upper(),
                "team": _required_text(player, "pro_team", label).upper(),
            }
        )
    if coverage == "NONE" and available_rows:
        raise EspnSnapshotImportError(
            "get_free_agents.coverage=NONE cannot accompany available-player rows."
        )

    provider_as_of_raw = league.get("provider_as_of_utc")
    provider_as_of_utc = (
        _utc_timestamp(provider_as_of_raw, "get_league_info.provider_as_of_utc")
        if provider_as_of_raw not in (None, "")
        else None
    )
    document = {
        "profile_id": profile_id,
        "provider_league_id": provider_league_id,
        "league_name": league_name,
        "season": season,
        "team_count": team_count,
        "owner_team_id": owner_team_id,
        "owner_team_name": owner_team_name,
        "roster": roster_rows,
        "scoring_settings": scoring_settings,
        "scoring_completeness": scoring_completeness,
        "available_player_pool": available_rows,
        "available_player_pool_coverage": coverage,
        "available_player_pool_bound_description": bound_description,
        "retrieved_at_utc": retrieved_at_utc,
        "provider_as_of_utc": provider_as_of_utc,
        "source": DEFAULT_SOURCE,
    }
    try:
        snapshot = parse_espn_flaim_snapshot(document)
    except (EspnFlaimSnapshotError, TypeError, ValueError) as exc:
        raise EspnSnapshotImportError(f"Transformed ESPN snapshot is invalid: {exc}") from exc
    _validate_snapshot_semantics(snapshot)
    return snapshot


def _validate_snapshot_semantics(snapshot: EspnFlaimSnapshot) -> None:
    """Enforce completeness claims the base schema cannot infer by itself."""

    if snapshot.scoring_completeness == "COMPLETE":
        mapped = {
            setting.nwr_setting
            for setting in snapshot.scoring_settings
            if setting.nwr_setting is not None
        }
        has_unmapped = any(setting.nwr_setting is None for setting in snapshot.scoring_settings)
        missing = sorted(_REQUIRED_COMPLETE_NWR_SCORING_FIELDS - mapped)
        if has_unmapped or missing:
            detail = ", ".join(missing) if missing else "unmapped provider scoring fields"
            raise EspnSnapshotImportError(
                "scoring_completeness=COMPLETE is not supported by the supplied settings; "
                f"missing/unresolved: {detail}. Use PARTIAL or UNKNOWN."
            )
    if snapshot.available_player_pool_coverage == "BOUNDED":
        if not (snapshot.available_player_pool_bound_description or "").strip():
            raise EspnSnapshotImportError(
                "available_player_pool_bound_description is required for BOUNDED coverage."
            )
    if snapshot.available_player_pool_coverage == "NONE" and snapshot.available_player_pool:
        raise EspnSnapshotImportError(
            "available_player_pool_coverage=NONE cannot accompany available-player rows."
        )


def load_snapshot_input(
    path: str | Path, *, input_kind: Literal["raw", "snapshot"]
) -> EspnFlaimSnapshot:
    source_path = Path(path)
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise EspnSnapshotImportError(f"Could not read input file {source_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EspnSnapshotImportError(
            f"Input file {source_path} is not valid JSON: line {exc.lineno}, column {exc.colno}."
        ) from exc
    if not isinstance(raw, Mapping):
        raise EspnSnapshotImportError("Input JSON must be an object.")
    if input_kind == "raw":
        return transform_flaim_raw_capture(raw)
    try:
        snapshot = parse_espn_flaim_snapshot(dict(raw))
    except (EspnFlaimSnapshotError, KeyError, TypeError, ValueError) as exc:
        raise EspnSnapshotImportError(f"Manual ESPN snapshot is invalid: {exc}") from exc
    _validate_snapshot_semantics(snapshot)
    return snapshot


def validate_snapshot_identity(
    *,
    profile: LeagueProfile,
    snapshot: EspnFlaimSnapshot,
    expectations: SnapshotImportExpectations,
) -> None:
    """Reject any profile/league/team mismatch before preview or activation."""

    mismatches: list[str] = []
    if profile.provider != "espn":
        mismatches.append(f"profile provider is {profile.provider!r}, expected 'espn'")
    if snapshot.profile_id != profile.profile_id:
        mismatches.append(
            f"snapshot profile_id {snapshot.profile_id!r} != target {profile.profile_id!r}"
        )
    if _normalized_identity(snapshot.league_name) != _normalized_identity(profile.league_name):
        mismatches.append(
            f"snapshot league_name {snapshot.league_name!r} != profile {profile.league_name!r}"
        )
    if snapshot.season != profile.season:
        mismatches.append(f"snapshot season {snapshot.season} != profile season {profile.season}")
    if snapshot.team_count != profile.team_count:
        mismatches.append(
            f"snapshot team_count {snapshot.team_count} != profile team_count {profile.team_count}"
        )
    if snapshot.provider_league_id != expectations.provider_league_id:
        mismatches.append(
            "snapshot provider_league_id "
            f"{snapshot.provider_league_id!r} != expected {expectations.provider_league_id!r}"
        )
    if profile.provider_league_id and snapshot.provider_league_id != profile.provider_league_id:
        mismatches.append(
            "snapshot provider_league_id does not match the non-empty profile provider_league_id"
        )
    if snapshot.owner_team_id != expectations.owner_team_id:
        mismatches.append(
            f"snapshot owner_team_id {snapshot.owner_team_id!r} != expected "
            f"{expectations.owner_team_id!r}"
        )
    if _normalized_identity(snapshot.owner_team_name) != _normalized_identity(
        expectations.owner_team_name
    ):
        mismatches.append(
            f"snapshot owner_team_name {snapshot.owner_team_name!r} != expected "
            f"{expectations.owner_team_name!r}"
        )
    if mismatches:
        raise EspnSnapshotImportError("Identity validation failed: " + "; ".join(mismatches))


def prepare_snapshot_import(
    *,
    redraft_root: str | Path,
    profile_id: str,
    input_path: str | Path,
    input_kind: Literal["raw", "snapshot"],
    expectations: SnapshotImportExpectations,
) -> tuple[LeagueProfile, EspnFlaimSnapshot, str]:
    """Load input, validate schema and identity, and return its source hash."""

    if not _SAFE_ID.fullmatch(profile_id):
        raise EspnSnapshotImportError("profile_id contains unsafe path characters.")
    try:
        profile = load_profile(redraft_root, profile_id)
    except (OSError, RedraftPersistenceError, RedraftValidationError, ValueError) as exc:
        raise EspnSnapshotImportError(
            f"Could not load target profile {profile_id!r}: {exc}"
        ) from exc
    snapshot = load_snapshot_input(input_path, input_kind=input_kind)
    validate_snapshot_identity(profile=profile, snapshot=snapshot, expectations=expectations)
    try:
        source_bytes = Path(input_path).read_bytes()
    except OSError as exc:
        raise EspnSnapshotImportError(f"Could not hash input file {input_path}: {exc}") from exc
    return profile, snapshot, hashlib.sha256(source_bytes).hexdigest()


def _snapshot_bytes(snapshot: EspnFlaimSnapshot) -> bytes:
    document = asdict(snapshot)
    # Round-trip through the one authoritative parser before a byte reaches disk.
    parse_espn_flaim_snapshot(document)
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _atomic_write_bytes(
    path: Path,
    payload: bytes,
    *,
    replace_func: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace,
) -> None:
    """Same-volume staged write, flush/fsync, then atomic replacement."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        replace_func(temporary, path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise EspnSnapshotImportError(f"Atomic write failed for {path}: {exc}") from exc


def _backup_path(target: Path, old_payload: bytes) -> Path:
    digest = hashlib.sha256(old_payload).hexdigest()[:16]
    try:
        old = parse_espn_flaim_snapshot(json.loads(old_payload.decode("utf-8")))
        stamp_source = old.retrieved_at_utc
    except (
        EspnFlaimSnapshotError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        stamp_source = "unknown-retrieval-time"
    stamp = re.sub(r"[^0-9A-Za-z]+", "", stamp_source) or "unknown"
    return target.parent / "history" / target.stem / f"{stamp}--{digest}.json"


def activate_snapshot(
    *,
    redraft_root: str | Path,
    snapshot: EspnFlaimSnapshot,
    input_path: str | Path,
    source_sha256: str,
    imported_at_utc: str | None = None,
    replace_func: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace,
) -> SnapshotActivationResult:
    """Archive the current file, then atomically activate the validated snapshot."""

    _validate_snapshot_semantics(snapshot)
    imported_at = _utc_timestamp(
        imported_at_utc or datetime.now(UTC).isoformat(), "imported_at_utc"
    )
    provenance_snapshot = replace(
        snapshot,
        imported_at_utc=imported_at,
        source_capture_sha256=source_sha256,
        source_capture_name=Path(input_path).name,
    )
    payload = _snapshot_bytes(provenance_snapshot)
    target = espn_flaim_snapshot_path(redraft_root, snapshot.profile_id)
    backup: Path | None = None
    if target.exists():
        try:
            previous = target.read_bytes()
        except OSError as exc:
            raise EspnSnapshotImportError(
                f"Could not read current snapshot before replacement: {exc}"
            ) from exc
        try:
            previous_snapshot = parse_espn_flaim_snapshot(json.loads(previous.decode("utf-8")))
        except (
            EspnFlaimSnapshotError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:
            raise EspnSnapshotImportError(
                "Current snapshot is malformed; refusing to replace it silently. Move or repair "
                f"{target} manually after preserving it. ({exc})"
            ) from exc
        if previous_snapshot.profile_id != snapshot.profile_id:
            raise EspnSnapshotImportError(
                "Current snapshot belongs to a different profile; refusing to overwrite it."
            )
        backup = _backup_path(target, previous)
        if backup.exists():
            if backup.read_bytes() != previous:
                raise EspnSnapshotImportError(
                    f"Backup collision at {backup}; current snapshot was not changed."
                )
        else:
            _atomic_write_bytes(backup, previous, replace_func=replace_func)
    _atomic_write_bytes(target, payload, replace_func=replace_func)
    return SnapshotActivationResult(
        profile_id=snapshot.profile_id,
        target_path=target,
        backup_path=backup,
        snapshot_sha256=hashlib.sha256(payload).hexdigest(),
        imported_at_utc=imported_at,
    )
