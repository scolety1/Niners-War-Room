"""Deterministic Redraft Draft Room, owner ADP boundary, and mock behavior.

NWR rankings remain the player-value authority. ADP is optional market-timing
context. CPU selections use admitted ADP when present and otherwise disclose a
deterministic NWR-order fallback. Sleeper events are accepted read-only; this
module contains no platform write client.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from src.services.redraft_engine_v1_service import (
    LeagueProfile,
    RankingResult,
    RedraftPersistenceError,
    RedraftValidationError,
    load_draft_board,
    utc_now,
)

ROOM_SCHEMA_VERSION = 1
ADP_SCHEMA_VERSION = 1
DEFAULT_SEED = 20260817
SUPPORTED_SPEEDS = frozenset({"FAST", "NORMAL", "STEP"})
SUPPORTED_MODES = frozenset({"MOCK", "LIVE_READ_ONLY"})
ADP_REQUIRED_COLUMNS = frozenset(
    {
        "player",
        "position",
        "overall_adp",
        "source",
        "scoring_format",
        "team_count",
        "date",
    }
)
ADP_OPTIONAL_COLUMNS = frozenset(
    {"player_id", "team", "expected_pick", "min_pick", "max_pick", "std_dev"}
)


@dataclass(frozen=True)
class AdpEntry:
    player_id: str
    player: str
    team: str
    position: str
    overall_adp: float
    expected_pick: float
    min_pick: float | None
    max_pick: float | None
    std_dev: float | None


@dataclass(frozen=True)
class AdpSnapshot:
    profile_id: str
    source: str
    scoring_format: str
    team_count: int
    source_date: str
    imported_at_utc: str
    source_sha256: str
    entries: tuple[AdpEntry, ...]
    unmatched: tuple[str, ...]
    errors: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return bool(self.entries) and not self.errors

    @property
    def by_player_id(self) -> dict[str, AdpEntry]:
        return {entry.player_id: entry for entry in self.entries}


def adp_import_template() -> str:
    columns = [
        "player_id",
        "player",
        "team",
        "position",
        "overall_adp",
        "expected_pick",
        "min_pick",
        "max_pick",
        "std_dev",
        "source",
        "scoring_format",
        "team_count",
        "date",
    ]
    return ",".join(columns) + "\n"


def import_owner_adp_csv(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    csv_text: str,
) -> AdpSnapshot:
    if not csv_text.strip() or len(csv_text.encode("utf-8")) > 2_000_000:
        raise RedraftValidationError("ADP CSV must be non-empty and no larger than 2 MB.")
    try:
        reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    except csv.Error as exc:
        raise RedraftValidationError("ADP CSV could not be parsed.") from exc
    fields = {str(value or "").strip() for value in (reader.fieldnames or [])}
    missing = sorted(ADP_REQUIRED_COLUMNS - fields)
    unknown = sorted(fields - ADP_REQUIRED_COLUMNS - ADP_OPTIONAL_COLUMNS)
    if missing:
        raise RedraftValidationError("ADP CSV is missing columns: " + ", ".join(missing))
    if unknown:
        raise RedraftValidationError("ADP CSV has unsupported columns: " + ", ".join(unknown))

    ranking_by_id = {row.player_id: row for row in ranking.rows}
    ranking_by_identity: dict[tuple[str, str], list[Any]] = {}
    for row in ranking.rows:
        ranking_by_identity.setdefault(
            (_normalized_name(row.player_name), row.position), []
        ).append(row)

    entries: list[AdpEntry] = []
    unmatched: list[str] = []
    sources: set[str] = set()
    scoring_formats: set[str] = set()
    source_dates: set[str] = set()
    seen_ids: set[str] = set()
    for line_number, source_row in enumerate(reader, start=2):
        row = {str(key).strip(): str(value or "").strip() for key, value in source_row.items()}
        player = row["player"]
        position = row["position"].upper()
        if not player or position not in {"QB", "RB", "WR", "TE"}:
            unmatched.append(f"line {line_number}: {player or 'missing player'}")
            continue
        try:
            team_count = int(row["team_count"])
        except ValueError as exc:
            raise RedraftValidationError(f"ADP line {line_number} team_count is invalid.") from exc
        if team_count != profile.team_count:
            raise RedraftValidationError(
                f"ADP line {line_number} is for {team_count} teams; active league uses "
                f"{profile.team_count}."
            )
        scoring = _normalized_scoring(row["scoring_format"])
        if scoring != _profile_scoring(profile):
            raise RedraftValidationError(
                f"ADP line {line_number} scoring format does not match the active league."
            )
        try:
            source_date = date.fromisoformat(row["date"])
        except ValueError as exc:
            raise RedraftValidationError(
                f"ADP line {line_number} date must be YYYY-MM-DD."
            ) from exc
        if source_date > datetime.now(UTC).date():
            raise RedraftValidationError(f"ADP line {line_number} date is in the future.")
        source_name = row["source"]
        if not source_name:
            raise RedraftValidationError(f"ADP line {line_number} source is required.")
        overall = _positive_float(row["overall_adp"], line_number, "overall_adp")
        expected = (
            _positive_float(row["expected_pick"], line_number, "expected_pick")
            if row.get("expected_pick")
            else overall
        )
        minimum = _optional_positive_float(row.get("min_pick", ""), line_number, "min_pick")
        maximum = _optional_positive_float(row.get("max_pick", ""), line_number, "max_pick")
        std_dev = _optional_positive_float(row.get("std_dev", ""), line_number, "std_dev")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise RedraftValidationError(f"ADP line {line_number} min_pick exceeds max_pick.")
        if minimum is not None and expected < minimum:
            raise RedraftValidationError(f"ADP line {line_number} expected_pick is below min_pick.")
        if maximum is not None and expected > maximum:
            raise RedraftValidationError(f"ADP line {line_number} expected_pick exceeds max_pick.")

        requested_id = row.get("player_id", "")
        matched = ranking_by_id.get(requested_id) if requested_id else None
        if matched is None:
            candidates = ranking_by_identity.get((_normalized_name(player), position), [])
            team = row.get("team", "").upper()
            if team:
                candidates = [
                    candidate for candidate in candidates if candidate.team.upper() == team
                ]
            matched = candidates[0] if len(candidates) == 1 else None
        if matched is None:
            unmatched.append(f"line {line_number}: {player} ({position})")
            continue
        if matched.player_id in seen_ids:
            raise RedraftValidationError(
                f"ADP line {line_number} duplicates {matched.player_name}."
            )
        seen_ids.add(matched.player_id)
        sources.add(source_name)
        scoring_formats.add(scoring)
        source_dates.add(source_date.isoformat())
        entries.append(
            AdpEntry(
                player_id=matched.player_id,
                player=matched.player_name,
                team=matched.team,
                position=matched.position,
                overall_adp=round(overall, 2),
                expected_pick=round(expected, 2),
                min_pick=round(minimum, 2) if minimum is not None else None,
                max_pick=round(maximum, 2) if maximum is not None else None,
                std_dev=round(std_dev, 2) if std_dev is not None else None,
            )
        )
    if not entries:
        raise RedraftValidationError("ADP CSV did not match any governed Redraft player IDs.")
    if len(sources) != 1 or len(scoring_formats) != 1 or len(source_dates) != 1:
        raise RedraftValidationError(
            "ADP CSV must contain one source, scoring format, and source date per snapshot."
        )
    entries.sort(key=lambda entry: (entry.expected_pick, entry.player_id))
    snapshot = AdpSnapshot(
        profile_id=profile.profile_id,
        source=next(iter(sources)),
        scoring_format=next(iter(scoring_formats)),
        team_count=profile.team_count,
        source_date=next(iter(source_dates)),
        imported_at_utc=utc_now(),
        source_sha256=hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
        entries=tuple(entries),
        unmatched=tuple(unmatched),
    )
    _atomic_json(_adp_path(root, profile.profile_id), _adp_document(snapshot))
    return snapshot


def load_adp_snapshot(root: str | Path, profile: LeagueProfile) -> AdpSnapshot:
    path = _adp_path(root, profile.profile_id)
    if not path.is_file():
        return AdpSnapshot(
            profile_id=profile.profile_id,
            source="",
            scoring_format=_profile_scoring(profile),
            team_count=profile.team_count,
            source_date="",
            imported_at_utc="",
            source_sha256="",
            entries=(),
            unmatched=(),
        )
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if (
            document.get("schema_version") != ADP_SCHEMA_VERSION
            or document.get("profile_id") != profile.profile_id
            or document.get("team_count") != profile.team_count
            or document.get("scoring_format") != _profile_scoring(profile)
        ):
            raise RedraftValidationError("ADP snapshot does not match the active league.")
        entries = tuple(AdpEntry(**row) for row in document.get("entries", []))
        return AdpSnapshot(
            profile_id=profile.profile_id,
            source=str(document.get("source") or ""),
            scoring_format=str(document.get("scoring_format") or ""),
            team_count=int(document.get("team_count") or 0),
            source_date=str(document.get("source_date") or ""),
            imported_at_utc=str(document.get("imported_at_utc") or ""),
            source_sha256=str(document.get("source_sha256") or ""),
            entries=entries,
            unmatched=tuple(str(value) for value in document.get("unmatched", [])),
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, RedraftValidationError) as exc:
        raise RedraftPersistenceError("ADP snapshot is unreadable or incompatible.") from exc


def draft_order(profile: LeagueProfile) -> tuple[int, ...]:
    order: list[int] = []
    for round_number in range(1, profile.draft.rounds + 1):
        slots = range(1, profile.team_count + 1)
        order.extend(slots if round_number % 2 else reversed(tuple(slots)))
    return tuple(order)


def load_room_state(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    document = load_draft_board(root, profile.profile_id)
    return _coerce_room_state(profile, ranking, manual_assets, document)


def start_draft_room(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    seed: int = DEFAULT_SEED,
    speed: str = "NORMAL",
    mode: str = "MOCK",
) -> dict[str, Any]:
    if profile.draft.draft_type != "snake" or not 1 <= owner_slot <= profile.team_count:
        raise RedraftValidationError("Draft Room requires a valid snake-draft owner slot.")
    normalized_speed = speed.strip().upper()
    normalized_mode = mode.strip().upper()
    if normalized_speed not in SUPPORTED_SPEEDS or normalized_mode not in SUPPORTED_MODES:
        raise RedraftValidationError("Draft Room speed or mode is unsupported.")
    state = {
        "schema_version": ROOM_SCHEMA_VERSION,
        "profile_id": profile.profile_id,
        "owner_slot": owner_slot,
        "seed": int(seed),
        "speed": normalized_speed,
        "mode": normalized_mode,
        "drafted": [],
        "picks": [],
        "updated_at_utc": utc_now(),
    }
    if normalized_mode == "MOCK":
        state = _advance_cpu(
            profile,
            ranking,
            manual_assets,
            adp,
            state,
            stop_at_owner=True,
        )
    _save_room_state(root, state)
    return state


def owner_pick_and_advance(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    player_id: str,
) -> dict[str, Any]:
    state = load_room_state(root, profile, ranking, manual_assets)
    owner_slot = state.get("owner_slot")
    if not isinstance(owner_slot, int):
        raise RedraftValidationError("Start the Draft Room and choose an owner slot first.")
    if _current_team(profile, state) != owner_slot:
        raise RedraftValidationError("The Draft Room is not currently on the owner pick.")
    asset = _asset_pool(ranking, manual_assets).get(player_id)
    if asset is None or player_id in state["drafted"]:
        raise RedraftValidationError("The selected Draft Room player is unavailable.")
    state = _record_pick(profile, state, asset, actor="OWNER", behavior="OWNER_SELECTION")
    if state.get("mode") == "MOCK" and not _complete(profile, state):
        step = state.get("speed") == "STEP"
        state = _advance_cpu(
            profile,
            ranking,
            manual_assets,
            adp,
            state,
            stop_at_owner=not step,
            max_picks=1 if step else None,
        )
    _save_room_state(root, state)
    return state


def advance_cpu_to_owner(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    one_pick: bool = False,
) -> dict[str, Any]:
    state = load_room_state(root, profile, ranking, manual_assets)
    state = _advance_cpu(
        profile,
        ranking,
        manual_assets,
        adp,
        state,
        stop_at_owner=not one_pick,
        max_picks=1 if one_pick else None,
    )
    _save_room_state(root, state)
    return state


def undo_room_pick(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    state = load_room_state(root, profile, ranking, manual_assets)
    if not state["picks"]:
        raise RedraftValidationError("No Draft Room pick is available to undo.")
    state["picks"] = state["picks"][:-1]
    state["drafted"] = [pick["player_id"] for pick in state["picks"]]
    state["updated_at_utc"] = utc_now()
    _save_room_state(root, state)
    return state


def ingest_read_only_sleeper_pick(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    player_id: str,
    pick_number: int,
) -> dict[str, Any]:
    state = load_room_state(root, profile, ranking, manual_assets)
    if state.get("mode") != "LIVE_READ_ONLY":
        raise RedraftValidationError("Sleeper pick ingestion requires Live Read-Only mode.")
    expected = len(state["picks"]) + 1
    if pick_number != expected:
        raise RedraftValidationError(
            f"Sleeper pick {pick_number} does not match next pick {expected}."
        )
    asset = _asset_pool(ranking, manual_assets).get(player_id)
    if asset is None or player_id in state["drafted"]:
        raise RedraftValidationError("Sleeper pick player is unavailable locally.")
    state = _record_pick(
        profile,
        state,
        asset,
        actor="SLEEPER_READ_ONLY",
        behavior="READ_ONLY_PICK_EVENT",
    )
    _save_room_state(root, state)
    return state


def run_complete_mock(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema_version": ROOM_SCHEMA_VERSION,
        "profile_id": profile.profile_id,
        "owner_slot": owner_slot,
        "seed": seed,
        "speed": "FAST",
        "mode": "MOCK",
        "drafted": [],
        "picks": [],
        "updated_at_utc": utc_now(),
    }
    pool = _asset_pool(ranking, manual_assets)
    while not _complete(profile, state):
        team_slot = _current_team(profile, state)
        actor = "OWNER_AUTO_TEST" if team_slot == owner_slot else "CPU"
        asset, behavior = _select_asset(profile, ranking, adp, state, pool, team_slot, actor)
        state = _record_pick(profile, state, asset, actor=actor, behavior=behavior)
    return state


def build_draft_room_payload(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    state: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = _coerce_room_state(profile, ranking, manual_assets, state)
    order = draft_order(profile)
    picks = list(normalized["picks"])
    picks_by_number = {int(pick["pick_number"]): pick for pick in picks}
    owner_slot = normalized.get("owner_slot")
    current_pick = len(picks) + 1
    complete = current_pick > len(order)
    current_team = None if complete else order[current_pick - 1]
    next_owner = _next_owner_pick(profile, current_pick, owner_slot)
    roster_by_team = _rosters(profile, picks)
    board_cells = []
    for pick_number, team_slot in enumerate(order, start=1):
        round_number = ((pick_number - 1) // profile.team_count) + 1
        pick = picks_by_number.get(pick_number)
        board_cells.append(
            {
                "pickNumber": pick_number,
                "round": round_number,
                "teamSlot": team_slot,
                "ownerPick": team_slot == owner_slot,
                "current": pick_number == current_pick and not complete,
                "playerId": str((pick or {}).get("player_id") or ""),
                "playerName": str((pick or {}).get("player_name") or ""),
                "position": str((pick or {}).get("position") or ""),
                "team": str((pick or {}).get("team") or ""),
                "actor": str((pick or {}).get("actor") or ""),
                "selectionBehavior": str((pick or {}).get("selection_behavior") or ""),
            }
        )
    teams = [
        {
            "teamSlot": slot,
            "name": "My Team" if slot == owner_slot else f"Team {slot}",
            "owner": slot == owner_slot,
            "roster": roster_by_team[slot],
            "picks": [pick for pick in picks if pick["team_slot"] == slot],
        }
        for slot in range(1, profile.team_count + 1)
    ]
    available = _available_ranked(ranking, normalized)
    recommendations = _recommendations(
        profile,
        ranking,
        adp,
        normalized,
        current_pick=current_pick,
        next_owner_pick=next_owner,
    )
    return {
        "schemaVersion": ROOM_SCHEMA_VERSION,
        "profileId": profile.profile_id,
        "configured": isinstance(owner_slot, int),
        "ownerSlot": owner_slot,
        "seed": normalized.get("seed", DEFAULT_SEED),
        "speed": normalized.get("speed", "NORMAL"),
        "mode": normalized.get("mode", "MOCK"),
        "drafted": list(normalized["drafted"]),
        "picks": [_pick_payload(pick) for pick in picks],
        "boardCells": board_cells,
        "teams": teams,
        "recentPicks": [_pick_payload(pick) for pick in picks[-8:]],
        "draftLog": [_pick_payload(pick) for pick in picks],
        "myRoster": roster_by_team.get(owner_slot, []) if isinstance(owner_slot, int) else [],
        "currentPick": None if complete else current_pick,
        "currentTeamSlot": current_team,
        "nextOwnerPick": next_owner,
        "isOwnerTurn": current_team == owner_slot and not complete,
        "complete": complete,
        "availableCount": len(available)
        + len([row for row in manual_assets if _manual_id(row) not in normalized["drafted"]]),
        "canUndo": bool(picks),
        "updatedAtUtc": str(normalized.get("updated_at_utc") or ""),
        "recoveredFromBackup": bool(normalized.get("recovered_from_backup")),
        "adp": _adp_status(adp, len(ranking.rows)),
        "beatAdpPool": recommendations["beatAdpPool"],
        "recommendations": recommendations["cards"],
        "positionRun": recommendations["positionRun"],
        "fallbackDisclosure": (
            "CPU uses admitted owner ADP plus seeded variation and roster construction."
            if adp.available
            else "ADP unavailable. CPU uses disclosed deterministic NWR order fallback; "
            "this is not market realism."
        ),
        "sleeperCompatibility": {
            "mode": "READ_ONLY_PICK_EVENTS",
            "pollingDefault": "OFF",
            "writes": "NONE",
        },
    }


def validate_complete_mock(profile: LeagueProfile, state: Mapping[str, Any]) -> tuple[str, ...]:
    picks = list(state.get("picks", []))
    errors: list[str] = []
    expected = profile.team_count * profile.draft.rounds
    if len(picks) != expected:
        errors.append(f"Draft contains {len(picks)} picks; expected {expected}.")
    player_ids = [str(pick.get("player_id") or "") for pick in picks]
    if len(player_ids) != len(set(player_ids)):
        errors.append("Draft contains duplicate player IDs.")
    rosters = _rosters(profile, picks)
    required = {
        "QB": profile.roster.qb,
        "RB": profile.roster.rb,
        "WR": profile.roster.wr,
        "TE": profile.roster.te,
        "K": profile.roster.k,
        "DST": profile.roster.dst,
    }
    for slot, roster in rosters.items():
        counts = Counter(str(player["position"]) for player in roster)
        for position, count in required.items():
            if counts[position] < count:
                errors.append(f"Team {slot} is missing required {position}.")
        flex_total = sum(counts[position] for position in ("RB", "WR", "TE"))
        flex_required = (
            profile.roster.rb + profile.roster.wr + profile.roster.te + profile.roster.flex
        )
        if flex_total < flex_required:
            errors.append(f"Team {slot} is missing a legal FLEX asset.")
    return tuple(errors)


def _advance_cpu(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    state: dict[str, Any],
    *,
    stop_at_owner: bool,
    max_picks: int | None = None,
) -> dict[str, Any]:
    owner_slot = state.get("owner_slot")
    if not isinstance(owner_slot, int):
        raise RedraftValidationError("Draft Room owner slot is not configured.")
    pool = _asset_pool(ranking, manual_assets)
    added = 0
    while not _complete(profile, state):
        team_slot = _current_team(profile, state)
        if team_slot == owner_slot and stop_at_owner:
            break
        if team_slot == owner_slot:
            break
        asset, behavior = _select_asset(profile, ranking, adp, state, pool, team_slot, "CPU")
        state = _record_pick(profile, state, asset, actor="CPU", behavior=behavior)
        added += 1
        if max_picks is not None and added >= max_picks:
            break
    return state


def _select_asset(
    profile: LeagueProfile,
    ranking: RankingResult,
    adp: AdpSnapshot,
    state: Mapping[str, Any],
    pool: Mapping[str, dict[str, Any]],
    team_slot: int,
    actor: str,
) -> tuple[dict[str, Any], str]:
    available = [asset for key, asset in pool.items() if key not in state.get("drafted", [])]
    if not available:
        raise RedraftValidationError("No Draft Room asset remains available.")
    roster = Counter(
        str(pick["position"])
        for pick in state.get("picks", [])
        if int(pick["team_slot"]) == team_slot
    )
    current_pick = len(state.get("picks", [])) + 1
    round_number = ((current_pick - 1) // profile.team_count) + 1
    forced = _forced_position(profile, roster, round_number)
    candidates = [asset for asset in available if forced is None or asset["position"] == forced]
    if not candidates:
        candidates = available
    candidates = [
        asset for asset in candidates if _roster_candidate_allowed(profile, roster, asset)
    ]
    if not candidates:
        candidates = available
    if actor == "OWNER_AUTO_TEST":
        candidates.sort(
            key=lambda asset: (
                _owner_auto_score(profile, roster, round_number, asset),
                str(asset["player_id"]),
            )
        )
        behavior = (
            "MANUAL_UNMODELED"
            if candidates[0]["position"] in {"K", "DST"}
            else "OWNER_TEST_NWR_RECOMMENDATION"
        )
        return candidates[0], behavior

    adp_by_id = adp.by_player_id if adp.available else {}
    seed = int(state.get("seed") or DEFAULT_SEED)
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for asset in candidates:
        entry = adp_by_id.get(str(asset["player_id"]))
        base = entry.expected_pick if entry is not None else float(asset.get("nwr_rank") or 9999)
        spread = _adp_spread(entry) if entry is not None else 5.0
        jitter = _seeded_unit(seed, current_pick, str(asset["player_id"])) * spread
        need_adjustment = _roster_need_adjustment(profile, roster, round_number, asset["position"])
        missing_adp_penalty = 25.0 if adp.available and entry is None else 0.0
        scored.append(
            (base + jitter + need_adjustment + missing_adp_penalty, str(asset["player_id"]), asset)
        )
    scored.sort(key=lambda row: (row[0], row[1]))
    behavior = "ADP_SEEDED_ROSTER_AWARE" if adp.available else "DISCLOSED_NWR_ORDER_FALLBACK"
    if scored[0][2]["position"] in {"K", "DST"}:
        behavior = "MANUAL_UNMODELED"
    return scored[0][2], behavior


def _record_pick(
    profile: LeagueProfile,
    state: Mapping[str, Any],
    asset: Mapping[str, Any],
    *,
    actor: str,
    behavior: str,
) -> dict[str, Any]:
    updated = {**state, "picks": list(state.get("picks", []))}
    pick_number = len(updated["picks"]) + 1
    order = draft_order(profile)
    if pick_number > len(order):
        raise RedraftValidationError("The Draft Room is already complete.")
    player_id = str(asset["player_id"])
    if player_id in state.get("drafted", []):
        raise RedraftValidationError("The Draft Room player is already drafted.")
    round_number = ((pick_number - 1) // profile.team_count) + 1
    team_slot = order[pick_number - 1]
    updated["picks"].append(
        {
            "pick_number": pick_number,
            "round": round_number,
            "team_slot": team_slot,
            "player_id": player_id,
            "player_name": str(asset["player_name"]),
            "position": str(asset["position"]),
            "team": str(asset.get("team") or ""),
            "actor": actor,
            "selection_behavior": behavior,
            "nwr_rank": asset.get("nwr_rank"),
            "picked_at_utc": utc_now(),
        }
    )
    updated["drafted"] = [pick["player_id"] for pick in updated["picks"]]
    updated["updated_at_utc"] = utc_now()
    return updated


def _recommendations(
    profile: LeagueProfile,
    ranking: RankingResult,
    adp: AdpSnapshot,
    state: Mapping[str, Any],
    *,
    current_pick: int,
    next_owner_pick: int | None,
) -> dict[str, Any]:
    available = _available_ranked(ranking, state)
    owner_slot = state.get("owner_slot")
    roster = Counter(
        str(pick["position"])
        for pick in state.get("picks", [])
        if pick.get("team_slot") == owner_slot
    )
    enriched = [
        _decision_row(profile, row, adp, current_pick, next_owner_pick, roster)
        for row in available[:100]
    ]
    beat_pool = sorted(
        [row for row in enriched if row["nwrView"] in {"STRONG VALUE", "VALUE"}],
        key=lambda row: (-float(row.get("nwrEdge") or 0), int(row["nwrRank"])),
    )[:30]
    cards: list[dict[str, Any]] = []
    if enriched:
        cards.append(_card("Best Available", enriched[0], "Highest available NWR Redraft rank."))
        fit = min(
            enriched[:30],
            key=lambda row: (
                _fit_penalty(profile, roster, str(row["position"])),
                int(row["nwrRank"]),
            ),
        )
        cards.append(_card("Best Fit", fit, "Best open-starter and FLEX fit among top options."))
        value_rows = [row for row in enriched if row.get("expectedPick") is not None]
        if value_rows:
            value = max(value_rows, key=lambda row: float(row.get("nwrEdge") or -9999))
            cards.append(_card("Value vs ADP", value, "Largest admitted ADP edge near this pick."))
        else:
            cards.append(
                _card(
                    "Value vs ADP",
                    enriched[0],
                    "ADP unavailable; this card preserves NWR order and makes no market claim.",
                )
            )
        upside = max(enriched[:20], key=lambda row: float(row["replacementAdjustedValue"]))
        cards.append(
            _card("Upside", upside, "Highest replacement-adjusted ceiling proxy available.")
        )
        safe_rows = [row for row in enriched[:30] if str(row["confidence"]).upper() == "HIGH"]
        safer = safe_rows[0] if safe_rows else enriched[0]
        cards.append(
            _card("Safer", safer, "Best high-evidence option; falls back visibly if none.")
        )
    recent_positions = [str(pick["position"]) for pick in state.get("picks", [])[-6:]]
    counts = Counter(recent_positions)
    position_run = [
        {"position": position, "count": count}
        for position, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= 2
    ]
    return {"cards": cards[:5], "beatAdpPool": beat_pool, "positionRun": position_run}


def _decision_row(
    profile: LeagueProfile,
    row: Any,
    adp: AdpSnapshot,
    current_pick: int,
    next_owner_pick: int | None,
    roster: Counter[str],
) -> dict[str, Any]:
    entry = adp.by_player_id.get(row.player_id) if adp.available else None
    edge = round(entry.expected_pick - row.overall_rank, 1) if entry else None
    nwr_view = _nwr_view(edge)
    timing, survival, probability, method = _draft_timing(
        row.overall_rank,
        entry,
        current_pick,
        next_owner_pick,
    )
    return {
        "playerId": row.player_id,
        "playerName": row.player_name,
        "team": row.team,
        "position": row.position,
        "nwrRank": row.overall_rank,
        "positionRank": row.position_rank,
        "overallTier": row.tier,
        "overallTierLabel": getattr(row, "overall_tier_label", f"Tier {row.tier}"),
        "positionTier": getattr(row, "position_tier", row.tier),
        "positionTierLabel": getattr(row, "position_tier_label", f"{row.position} Tier {row.tier}"),
        "replacementAdjustedValue": row.replacement_adjusted_value,
        "confidence": row.confidence,
        "expectedPick": entry.expected_pick if entry else None,
        "overallAdp": entry.overall_adp if entry else None,
        "nwrEdge": edge,
        "nwrView": nwr_view,
        "draftTiming": timing,
        "makeItBack": survival,
        "makeItBackProbability": probability,
        "makeItBackMethod": method,
        "rosterFit": _roster_fit(profile, roster, row.position),
        "adpSource": adp.source if entry else "",
        "adpSourceDate": adp.source_date if entry else "",
    }


def _draft_timing(
    nwr_rank: int,
    entry: AdpEntry | None,
    current_pick: int,
    next_owner_pick: int | None,
) -> tuple[str, str, float | None, str]:
    if entry is None:
        return "ADP UNAVAILABLE", "MAKE-IT-BACK: UNAVAILABLE", None, "NO_ADP_DISTRIBUTION"
    if nwr_rank > current_pick + 35 and entry.expected_pick > current_pick + 20:
        timing = "REACH"
    elif entry.expected_pick <= current_pick + 3:
        timing = "TAKE NOW"
    elif next_owner_pick is not None and entry.expected_pick >= next_owner_pick + 5:
        timing = "WAIT"
    else:
        timing = "VALID"
    if next_owner_pick is None:
        return timing, "MAKE-IT-BACK: UNAVAILABLE", None, "NO_NEXT_OWNER_PICK"
    spread = _adp_distribution_spread(entry)
    if spread is None:
        return timing, "HEURISTIC — LOW CONFIDENCE", None, "EXPECTED_PICK_ONLY_NO_PROBABILITY"
    z = (next_owner_pick - entry.expected_pick) / spread
    probability = 0.5 * math.erfc(z / math.sqrt(2.0))
    probability = round(max(0.0, min(1.0, probability)), 2)
    if probability >= 0.65:
        survival = "LIKELY TO MAKE IT BACK"
    elif probability <= 0.35:
        survival = "UNLIKELY TO MAKE IT BACK"
    else:
        survival = "HEURISTIC — LOW CONFIDENCE"
    return timing, survival, probability, "HEURISTIC_NORMAL_FROM_OWNER_ADP_RANGE"


def _coerce_room_state(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    document: Mapping[str, Any],
) -> dict[str, Any]:
    pool = _asset_pool(ranking, manual_assets)
    drafted = [str(value) for value in document.get("drafted", [])]
    raw_picks = document.get("picks", [])
    picks: list[dict[str, Any]] = []
    if isinstance(raw_picks, list) and raw_picks:
        for expected, raw in enumerate(raw_picks, start=1):
            if not isinstance(raw, Mapping) or int(raw.get("pick_number") or 0) != expected:
                raise RedraftValidationError("Draft Room event sequence is invalid.")
            picks.append(dict(raw))
    elif drafted:
        order = draft_order(profile)
        for index, player_id in enumerate(drafted, start=1):
            asset = pool.get(player_id, _unknown_asset(player_id))
            picks.append(
                {
                    "pick_number": index,
                    "round": ((index - 1) // profile.team_count) + 1,
                    "team_slot": order[index - 1],
                    "player_id": player_id,
                    "player_name": asset["player_name"],
                    "position": asset["position"],
                    "team": asset["team"],
                    "actor": "LEGACY",
                    "selection_behavior": "LEGACY_ORDER_ONLY",
                    "nwr_rank": asset.get("nwr_rank"),
                    "picked_at_utc": str(document.get("updated_at_utc") or ""),
                }
            )
    if [str(pick["player_id"]) for pick in picks] != drafted:
        drafted = [str(pick["player_id"]) for pick in picks]
    if len(drafted) != len(set(drafted)):
        raise RedraftValidationError("Draft Room contains duplicate player IDs.")
    return {
        "schema_version": ROOM_SCHEMA_VERSION,
        "profile_id": profile.profile_id,
        "owner_slot": document.get("owner_slot"),
        "seed": int(document.get("seed") or DEFAULT_SEED),
        "speed": str(document.get("speed") or "NORMAL"),
        "mode": str(document.get("mode") or "MOCK"),
        "drafted": drafted,
        "picks": picks,
        "updated_at_utc": str(document.get("updated_at_utc") or ""),
        "recovered_from_backup": bool(document.get("recovered_from_backup")),
    }


def _save_room_state(root: str | Path, state: Mapping[str, Any]) -> None:
    profile_id = str(state["profile_id"])
    path = Path(root) / "draft_boards" / f"{profile_id}.json"
    document = {
        "schema_version": ROOM_SCHEMA_VERSION,
        "profile_id": profile_id,
        "owner_slot": state.get("owner_slot"),
        "seed": int(state.get("seed") or DEFAULT_SEED),
        "speed": str(state.get("speed") or "NORMAL"),
        "mode": str(state.get("mode") or "MOCK"),
        "drafted": [str(value) for value in state.get("drafted", [])],
        "picks": list(state.get("picks", [])),
        "updated_at_utc": str(state.get("updated_at_utc") or utc_now()),
    }
    _atomic_json(path, document)
    _atomic_json(path.with_suffix(".backup.json"), document)


def _atomic_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _asset_pool(
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    pool = {
        row.player_id: {
            "player_id": row.player_id,
            "player_name": row.player_name,
            "position": row.position,
            "team": row.team,
            "nwr_rank": row.overall_rank,
            "replacement_adjusted_value": row.replacement_adjusted_value,
            "confidence": row.confidence,
        }
        for row in ranking.rows
        if row.position in {"QB", "RB", "WR", "TE"}
    }
    for raw in manual_assets:
        player_id = _manual_id(raw)
        position = str(raw.get("position") or "").upper()
        if player_id and position in {"K", "DST"}:
            pool[player_id] = {
                "player_id": player_id,
                "player_name": str(raw.get("player_name") or raw.get("playerName") or ""),
                "position": position,
                "team": str(raw.get("team") or ""),
                "nwr_rank": None,
                "replacement_adjusted_value": None,
                "confidence": "NOT MODELED",
            }
    return pool


def _forced_position(profile: LeagueProfile, roster: Counter[str], round_number: int) -> str | None:
    if round_number >= max(1, profile.draft.rounds - 1):
        if roster["K"] < profile.roster.k:
            return "K"
        if roster["DST"] < profile.roster.dst:
            return "DST"
    deadlines = (("QB", 8), ("TE", 10), ("RB", 12), ("WR", 12))
    for position, deadline in deadlines:
        required = int(getattr(profile.roster, position.lower()))
        if round_number >= deadline and roster[position] < required:
            return position
    return None


def _roster_candidate_allowed(
    profile: LeagueProfile,
    roster: Counter[str],
    asset: Mapping[str, Any],
) -> bool:
    position = str(asset["position"])
    if position in {"K", "DST"}:
        return roster[position] < int(getattr(profile.roster, position.lower()))
    if position == "QB":
        return roster[position] < max(profile.roster.qb + 1, 2)
    if position == "TE":
        return roster[position] < max(profile.roster.te + 1, 2)
    return roster[position] < profile.draft.rounds


def _roster_need_adjustment(
    profile: LeagueProfile,
    roster: Counter[str],
    round_number: int,
    position: str,
) -> float:
    required = int(getattr(profile.roster, position.lower(), 0))
    if position in {"QB", "RB", "WR", "TE"} and roster[position] < required:
        return -10.0 - round_number
    if position in {"RB", "WR", "TE"}:
        flex_have = sum(roster[value] for value in ("RB", "WR", "TE"))
        flex_need = profile.roster.rb + profile.roster.wr + profile.roster.te + profile.roster.flex
        if flex_have < flex_need:
            return -6.0
    if position in {"QB", "TE"} and roster[position] > required:
        return 18.0
    return float(roster[position]) * 1.5


def _owner_auto_score(
    profile: LeagueProfile,
    roster: Counter[str],
    round_number: int,
    asset: Mapping[str, Any],
) -> float:
    rank = float(asset.get("nwr_rank") or 10_000)
    return rank + _roster_need_adjustment(profile, roster, round_number, str(asset["position"]))


def _fit_penalty(profile: LeagueProfile, roster: Counter[str], position: str) -> float:
    return _roster_need_adjustment(profile, roster, 1, position)


def _roster_fit(profile: LeagueProfile, roster: Counter[str], position: str) -> str:
    required = int(getattr(profile.roster, position.lower(), 0))
    if roster[position] < required:
        return "OPEN STARTER"
    if position in {"RB", "WR", "TE"}:
        flex_have = sum(roster[value] for value in ("RB", "WR", "TE"))
        flex_need = profile.roster.rb + profile.roster.wr + profile.roster.te + profile.roster.flex
        if flex_have < flex_need:
            return "OPEN FLEX"
    return "DEPTH"


def _available_ranked(ranking: RankingResult, state: Mapping[str, Any]) -> list[Any]:
    drafted = {str(value) for value in state.get("drafted", [])}
    return [row for row in ranking.rows if row.player_id not in drafted]


def _rosters(
    profile: LeagueProfile, picks: Sequence[Mapping[str, Any]]
) -> dict[int, list[dict[str, Any]]]:
    rosters: dict[int, list[dict[str, Any]]] = {
        slot: [] for slot in range(1, profile.team_count + 1)
    }
    for pick in picks:
        slot = int(pick["team_slot"])
        rosters[slot].append(
            {
                "pickNumber": int(pick["pick_number"]),
                "playerId": str(pick["player_id"]),
                "playerName": str(pick["player_name"]),
                "position": str(pick["position"]),
                "team": str(pick.get("team") or ""),
            }
        )
    return rosters


def _current_team(profile: LeagueProfile, state: Mapping[str, Any]) -> int | None:
    pick_number = len(state.get("picks", [])) + 1
    order = draft_order(profile)
    return order[pick_number - 1] if pick_number <= len(order) else None


def _next_owner_pick(
    profile: LeagueProfile,
    current_pick: int,
    owner_slot: Any,
) -> int | None:
    if not isinstance(owner_slot, int):
        return None
    order = draft_order(profile)
    return next(
        (
            pick_number
            for pick_number in range(current_pick + 1, len(order) + 1)
            if order[pick_number - 1] == owner_slot
        ),
        None,
    )


def _complete(profile: LeagueProfile, state: Mapping[str, Any]) -> bool:
    return len(state.get("picks", [])) >= profile.team_count * profile.draft.rounds


def _pick_payload(pick: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "pickNumber": int(pick["pick_number"]),
        "round": int(pick["round"]),
        "teamSlot": int(pick["team_slot"]),
        "playerId": str(pick["player_id"]),
        "playerName": str(pick["player_name"]),
        "position": str(pick["position"]),
        "team": str(pick.get("team") or ""),
        "actor": str(pick.get("actor") or ""),
        "selectionBehavior": str(pick.get("selection_behavior") or ""),
        "nwrRank": pick.get("nwr_rank"),
        "pickedAtUtc": str(pick.get("picked_at_utc") or ""),
    }


def _card(label: str, row: Mapping[str, Any], note: str) -> dict[str, Any]:
    return {
        "label": label,
        "playerId": row["playerId"],
        "playerName": row["playerName"],
        "position": row["position"],
        "team": row["team"],
        "nwrRank": row["nwrRank"],
        "nwrView": row["nwrView"],
        "draftTiming": row["draftTiming"],
        "makeItBack": row["makeItBack"],
        "overallTierLabel": row["overallTierLabel"],
        "positionTierLabel": row["positionTierLabel"],
        "rosterFit": row["rosterFit"],
        "note": note,
    }


def _nwr_view(edge: float | None) -> str:
    if edge is None:
        return "ADP UNAVAILABLE"
    if edge >= 24:
        return "STRONG VALUE"
    if edge >= 10:
        return "VALUE"
    if edge <= -24:
        return "STRONG FADE"
    if edge <= -10:
        return "FADE"
    return "ALIGNED"


def _adp_spread(entry: AdpEntry | None) -> float:
    if entry is None:
        return 5.0
    spread = _adp_distribution_spread(entry)
    return max(3.0, min(spread or 6.0, 18.0))


def _adp_distribution_spread(entry: AdpEntry) -> float | None:
    if entry.std_dev is not None:
        return max(entry.std_dev, 1.0)
    if entry.min_pick is not None and entry.max_pick is not None:
        return max((entry.max_pick - entry.min_pick) / 4.0, 1.0)
    return None


def _seeded_unit(seed: int, pick_number: int, player_id: str) -> float:
    digest = hashlib.sha256(f"{seed}:{pick_number}:{player_id}".encode()).digest()
    integer = int.from_bytes(digest[:8], "big")
    return (integer / ((1 << 64) - 1)) * 2.0 - 1.0


def _adp_status(snapshot: AdpSnapshot, ranking_count: int) -> dict[str, Any]:
    return {
        "available": snapshot.available,
        "authority": "OWNER-IMPORTED ADP — MARKET TIMING ONLY",
        "source": snapshot.source,
        "sourceDate": snapshot.source_date,
        "importedAtUtc": snapshot.imported_at_utc,
        "sourceSha256": snapshot.source_sha256,
        "matchedPlayers": len(snapshot.entries),
        "rankingPlayers": ranking_count,
        "coverage": round(len(snapshot.entries) / ranking_count, 3) if ranking_count else 0.0,
        "unmatched": list(snapshot.unmatched),
        "message": (
            "Owner ADP is active for market timing; it does not change NWR rank."
            if snapshot.available
            else "ADP unavailable. Import an owner-authorized CSV; NWR does not invent ADP."
        ),
    }


def _adp_document(snapshot: AdpSnapshot) -> dict[str, Any]:
    return {
        "schema_version": ADP_SCHEMA_VERSION,
        "profile_id": snapshot.profile_id,
        "source": snapshot.source,
        "scoring_format": snapshot.scoring_format,
        "team_count": snapshot.team_count,
        "source_date": snapshot.source_date,
        "imported_at_utc": snapshot.imported_at_utc,
        "source_sha256": snapshot.source_sha256,
        "entries": [entry.__dict__ for entry in snapshot.entries],
        "unmatched": list(snapshot.unmatched),
    }


def _adp_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "adp_snapshots" / f"{profile_id}.json"


def _profile_scoring(profile: LeagueProfile) -> str:
    if profile.scoring.reception == 1:
        return "PPR"
    if profile.scoring.reception == 0.5:
        return "HALF_PPR"
    return "STANDARD"


def _normalized_scoring(value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]+", "_", value.strip().upper()).strip("_")
    aliases = {"HALF": "HALF_PPR", "HALF_POINT_PPR": "HALF_PPR", "STD": "STANDARD"}
    return aliases.get(normalized, normalized)


def _normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _positive_float(value: str, line_number: int, field: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise RedraftValidationError(f"ADP line {line_number} {field} is invalid.") from exc
    if not math.isfinite(number) or number <= 0:
        raise RedraftValidationError(f"ADP line {line_number} {field} must be positive.")
    return number


def _optional_positive_float(value: str, line_number: int, field: str) -> float | None:
    return _positive_float(value, line_number, field) if value else None


def _manual_id(row: Mapping[str, Any]) -> str:
    return str(row.get("player_id") or row.get("playerId") or "")


def _unknown_asset(player_id: str) -> dict[str, Any]:
    return {
        "player_id": player_id,
        "player_name": "Unknown legacy player",
        "position": "",
        "team": "",
        "nwr_rank": None,
    }
