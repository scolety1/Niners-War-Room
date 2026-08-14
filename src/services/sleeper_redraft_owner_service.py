"""Read-only Sleeper-to-Redraft profile import.

This module deliberately builds on :mod:`sleeper_import_service`; it does not
create a second Sleeper client.  The import is a one-time, explicit owner
action which saves a local receipt and never issues a write request to Sleeper.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RosterSettings,
    ScoringSettings,
    create_profile,
    list_profiles,
    reconcile_sleeper_profile_identities,
    save_profile,
)
from src.services.sleeper_import_service import SleeperHttpClient


class SleeperRedraftImportError(ValueError):
    """A malformed or incomplete read-only Sleeper response."""


@dataclass(frozen=True)
class SleeperRedraftImport:
    profile: LeagueProfile
    receipt: dict[str, Any]
    unsupported_scoring: tuple[str, ...]


# Sleeper fields that have a direct, governed Redraft V1 stat equivalent.
_SCORING_FIELDS = {
    "pass_yd": "passing_yards",
    "pass_td": "passing_td",
    "pass_int": "interception",
    "rush_yd": "rushing_yards",
    "rush_td": "rushing_td",
    "rec_yd": "receiving_yards",
    "rec": "reception",
    "rec_td": "receiving_td",
    "fum_lost": "fumble_lost",
}
_ROSTER_SLOT_MAP = {"QB": "qb", "RB": "rb", "WR": "wr", "TE": "te", "FLEX": "flex", "SUPER_FLEX": "superflex", "K": "k", "DEF": "dst", "BN": "bench_size"}


def import_sleeper_redraft_profile(
    *,
    league_id: str,
    username: str,
    redraft_root: str | Path,
    client: SleeperHttpClient | None = None,
) -> SleeperRedraftImport:
    """Read a league and create an isolated local Redraft profile.

    Unknown non-zero scoring fields are retained in the receipt and reported to
    the caller.  They are never coerced to zero or silently treated as an NWR
    projection field.
    """

    normalized_league_id = _identifier(league_id, "league id")
    normalized_username = _identifier(username, "username")
    http = client or SleeperHttpClient()
    league = _object(http.get_json(f"league/{normalized_league_id}"), "league")
    user = _object(http.get_json(f"user/{normalized_username}"), "user")
    users = _objects(http.get_json(f"league/{normalized_league_id}/users"), "users")
    rosters = _objects(http.get_json(f"league/{normalized_league_id}/rosters"), "rosters")
    drafts = _objects(http.get_json(f"league/{normalized_league_id}/drafts"), "drafts")

    user_id = _identifier(user.get("user_id"), "Sleeper user id")
    if str(user.get("username") or "").casefold() != normalized_username.casefold():
        raise SleeperRedraftImportError("Sleeper user lookup did not resolve the requested username.")
    if user_id not in {str(value.get("user_id") or "") for value in users}:
        raise SleeperRedraftImportError("Resolved Sleeper user is not a member of this league.")
    roster = next((value for value in rosters if str(value.get("owner_id") or "") == user_id), None)
    if roster is None:
        raise SleeperRedraftImportError("Resolved Sleeper user does not have a league roster.")
    league_user = next((value for value in users if str(value.get("user_id") or "") == user_id), {})

    selected_draft, draft_candidates = _select_draft(league, drafts)
    roster_settings, roster_unknown = _roster_settings(league.get("roster_positions"))
    scoring, scoring_reconciliation, unsupported_scoring = _scoring_settings(league.get("scoring_settings"))
    season = _integer(league.get("season"), "season")
    team_count = _integer((league.get("settings") or {}).get("num_teams") or league.get("total_rosters"), "team count")
    draft_settings = (selected_draft or {}).get("settings") or {}
    draft_order = (selected_draft or {}).get("draft_order") or {}
    draft_slot = _optional_slot(draft_order, user_id, team_count)
    rounds = _integer(draft_settings.get("rounds") or (league.get("settings") or {}).get("draft_rounds") or 1, "draft rounds")
    draft_type = str((selected_draft or {}).get("type") or "snake").casefold()
    if draft_type not in {"snake", "auction"}:
        raise SleeperRedraftImportError(f"Unsupported Sleeper draft type: {draft_type or 'missing'}.")
    keeper_count = len(roster.get("keepers") or [])
    league_name = str(league.get("name") or f"Sleeper — {normalized_league_id}").strip()
    template = LeagueProfile(
        profile_id=f"sleeper-{normalized_league_id}",
        league_name=league_name,
        season=season,
        team_count=team_count,
        roster=roster_settings,
        scoring=scoring,
        draft=DraftContext(
            draft_type=draft_type,
            draft_slot=draft_slot,
            rounds=rounds,
            keeper_count=keeper_count,
            roster_limits={"K": roster_settings.k, "DST": roster_settings.dst},
        ),
        provider="sleeper",
        provider_league_id=normalized_league_id,
    )
    reconcile_sleeper_profile_identities(redraft_root)
    existing = next(
        (
            value
            for value in list_profiles(redraft_root, include_archived=True)
            if value.provider == "sleeper"
            and value.provider_league_id == normalized_league_id
            and value.season == season
        ),
        None,
    )
    if existing is None:
        profile = create_profile(redraft_root, template, league_name=league_name)
    else:
        profile = save_profile(
            redraft_root,
            replace(template, profile_id=existing.profile_id, archived=False),
        )
    receipt = {
        "schema_version": 1,
        "source": "Sleeper public read-only API via existing SleeperHttpClient",
        "write_behavior": "NO_SLEEPER_WRITES",
        "league": {"league_id": normalized_league_id, "name": league_name, "season": season, "status": str(league.get("status") or ""), "team_count": team_count},
        "owner": {"username": normalized_username, "user_id": user_id, "roster_id": roster.get("roster_id"), "team_name": ((league_user.get("metadata") or {}).get("team_name") or user.get("display_name") or normalized_username), "keepers": list(roster.get("keepers") or [])},
        "draft": {"draft_id": (selected_draft or {}).get("draft_id"), "status": (selected_draft or {}).get("status"), "type": (selected_draft or {}).get("type"), "rounds": rounds, "teams": draft_settings.get("teams") or team_count, "pick_timer": draft_settings.get("pick_timer"), "start_time": (selected_draft or {}).get("start_time"), "draft_order_assigned": bool(draft_order), "owner_draft_slot": draft_slot, "candidates": draft_candidates},
        "roster_positions": list(league.get("roster_positions") or []),
        "roster_mapping": {"nwr": asdict(roster_settings), "unknown_sleeper_slots": roster_unknown},
        "scoring_reconciliation": scoring_reconciliation,
        "unsupported_scoring": list(unsupported_scoring),
        "profile_id": profile.profile_id,
    }
    _write_receipt(Path(redraft_root), profile.profile_id, receipt)
    return SleeperRedraftImport(profile=profile, receipt=receipt, unsupported_scoring=tuple(unsupported_scoring))


def load_sleeper_draft_picks(*, draft_id: str, client: SleeperHttpClient | None = None) -> tuple[dict[str, Any], ...]:
    """Safely read active-draft picks for a future local companion mode."""

    values = _objects((client or SleeperHttpClient()).get_json(f"draft/{_identifier(draft_id, 'draft id')}/picks"), "draft picks")
    return tuple(dict(value) for value in values)


def manual_kdst_assets_from_sleeper_players(value: object) -> tuple[dict[str, str], ...]:
    """Create selectable, unranked K/DST assets from Sleeper's public identities.

    These are draft-state assets only.  They intentionally contain no projection,
    rank, score, tier, or confidence field.
    """

    if not isinstance(value, Mapping):
        raise SleeperRedraftImportError("Sleeper player response is malformed.")
    rows: list[dict[str, str]] = []
    for sleeper_id, raw in value.items():
        if not isinstance(raw, Mapping):
            continue
        position = str(raw.get("position") or "").upper()
        position = "DST" if position == "DEF" else position
        if position not in {"K", "DST"} or raw.get("active") is False:
            continue
        team = str(raw.get("team") or "").upper().strip()
        name = str(raw.get("full_name") or raw.get("search_full_name") or "").strip()
        if position == "DST" and not name and team:
            name = f"{team} D/ST"
        if not team or not name:
            continue
        safe_id = str(sleeper_id).strip()
        if not safe_id:
            continue
        rows.append(
            {
                "player_id": f"manual:{position}:{safe_id}",
                "player_name": name,
                "position": position,
                "team": team,
                "authority": "MANUAL — NOT MODELED BY NWR",
            }
        )
    return tuple(sorted(rows, key=lambda row: (row["position"], row["team"], row["player_name"], row["player_id"])))


def _select_draft(league: Mapping[str, Any], drafts: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    season = str(league.get("season") or "")
    candidates = [value for value in drafts if str(value.get("season") or "") == season and str(value.get("type") or "").casefold() in {"snake", "auction"}]
    candidates.sort(key=lambda value: (0 if value.get("status") == "pre_draft" else 1, str(value.get("draft_id") or "")))
    receipt = [{"draft_id": str(value.get("draft_id") or ""), "status": str(value.get("status") or ""), "type": str(value.get("type") or ""), "season": str(value.get("season") or "")} for value in candidates]
    if not candidates:
        return None, receipt
    first_priority = 0 if candidates[0].get("status") == "pre_draft" else 1
    top = [value for value in candidates if (0 if value.get("status") == "pre_draft" else 1) == first_priority]
    if len(top) > 1:
        raise SleeperRedraftImportError(
            "Sleeper draft candidates are ambiguous: "
            + ", ".join(str(value.get("draft_id") or "<missing>") for value in top)
        )
    return top[0], receipt


def _roster_settings(value: object) -> tuple[RosterSettings, list[str]]:
    slots = value if isinstance(value, list) else []
    counts = {field: 0 for field in _ROSTER_SLOT_MAP.values()}
    unknown: list[str] = []
    for raw in slots:
        slot = str(raw or "").upper()
        field = _ROSTER_SLOT_MAP.get(slot)
        if field is None:
            unknown.append(slot or "<blank>")
        else:
            counts[field] += 1
    if not slots or unknown:
        raise SleeperRedraftImportError("Sleeper roster positions are missing or contain unsupported slots: " + ", ".join(unknown or ["missing"]))
    return RosterSettings(**counts), unknown


def _scoring_settings(value: object) -> tuple[ScoringSettings, list[dict[str, object]], list[str]]:
    raw = _object(value, "scoring settings")
    values = {field: 0.0 for field in _SCORING_FIELDS.values()}
    reconciliation: list[dict[str, object]] = []
    unsupported: list[str] = []
    for sleeper_field, score in sorted(raw.items()):
        numeric = _finite_number(score, f"scoring setting {sleeper_field}")
        target = _SCORING_FIELDS.get(str(sleeper_field))
        if target:
            values[target] = numeric
            reconciliation.append({"sleeper_setting": sleeper_field, "nwr_setting": target, "value": numeric, "status": "exact"})
        elif numeric != 0:
            unsupported.append(str(sleeper_field))
            reconciliation.append({"sleeper_setting": sleeper_field, "nwr_setting": "", "value": numeric, "status": "unsupported"})
        else:
            reconciliation.append({"sleeper_setting": sleeper_field, "nwr_setting": "", "value": numeric, "status": "unsupported_zero"})
    return ScoringSettings(**values, return_td=0.0), reconciliation, unsupported


def _write_receipt(root: Path, profile_id: str, receipt: Mapping[str, Any]) -> None:
    target = root / "sleeper_imports" / f"{profile_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)


def _optional_slot(order: object, user_id: str, team_count: int) -> int | None:
    if not isinstance(order, Mapping) or user_id not in order:
        return None
    slot = _integer(order[user_id], "draft slot")
    if not 1 <= slot <= team_count:
        raise SleeperRedraftImportError("Sleeper draft order contains an invalid owner slot.")
    return slot


def _objects(value: object, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise SleeperRedraftImportError(f"Sleeper {name} response is malformed.")
    return [dict(item) for item in value]


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SleeperRedraftImportError(f"Sleeper {name} response is malformed.")
    return dict(value)


def _identifier(value: object, name: str) -> str:
    output = str(value or "").strip()
    if not output or len(output) > 128 or not re.fullmatch(r"[A-Za-z0-9_-]+", output):
        raise SleeperRedraftImportError(f"Sleeper {name} is invalid.")
    return output


def _integer(value: object, name: str) -> int:
    try:
        output = int(str(value))
    except (TypeError, ValueError) as exc:
        raise SleeperRedraftImportError(f"Sleeper {name} is invalid.") from exc
    if output < 1:
        raise SleeperRedraftImportError(f"Sleeper {name} is invalid.")
    return output


def _finite_number(value: object, name: str) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError) as exc:
        raise SleeperRedraftImportError(f"Sleeper {name} is not numeric.") from exc
    if output != output or output in {float("inf"), float("-inf")}:
        raise SleeperRedraftImportError(f"Sleeper {name} is not finite.")
    return output
