from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from src.data.snapshots import utc_snapshot_stamp

SLEEPER_API_BASE = "https://api.sleeper.app/v1"
DEFAULT_LEAGUE_ID = "1344772855908290560"


@dataclass(frozen=True)
class SleeperSnapshotResult:
    league_id: str
    output_dir: Path
    files: dict[str, Path]
    counts: dict[str, int]


class SleeperHttpClient:
    def __init__(self, api_base: str = SLEEPER_API_BASE) -> None:
        self.api_base = api_base.rstrip("/")

    def get_json(self, path: str) -> Any:
        url = f"{self.api_base}/{path.lstrip('/')}"
        with urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))


def export_sleeper_snapshot(
    league_id: str = DEFAULT_LEAGUE_ID,
    output_root: str | Path = "local_exports/sleeper",
    *,
    client: SleeperHttpClient | None = None,
    snapshot_name: str | None = None,
) -> SleeperSnapshotResult:
    http = client or SleeperHttpClient()
    league = http.get_json(f"league/{league_id}")
    users = http.get_json(f"league/{league_id}/users")
    rosters = http.get_json(f"league/{league_id}/rosters")
    traded_picks = http.get_json(f"league/{league_id}/traded_picks")
    drafts = http.get_json(f"league/{league_id}/drafts")
    players = http.get_json("players/nfl")

    snapshot = snapshot_name or utc_snapshot_stamp()
    output_dir = Path(output_root) / f"{league_id}_{snapshot}"
    output_dir.mkdir(parents=True, exist_ok=True)

    users_by_id = {str(user.get("user_id")): user for user in users}
    rosters_by_id = {int(roster["roster_id"]): roster for roster in rosters}
    team_rows = _team_rows(rosters, users_by_id)
    active_draft = _active_draft(drafts, str(league.get("season") or ""))
    files = {
        "league_settings": output_dir / "sleeper_league_settings.csv",
        "teams": output_dir / "sleeper_teams.csv",
        "rosters": output_dir / "sleeper_rosters.csv",
        "future_picks": output_dir / "sleeper_future_picks.csv",
        "drafts": output_dir / "sleeper_drafts.csv",
        "metadata": output_dir / "sleeper_metadata.csv",
    }

    _write_csv(files["league_settings"], _league_settings_rows(league))
    _write_csv(files["teams"], team_rows)
    _write_csv(files["rosters"], _roster_rows(league, rosters, users_by_id, players))
    _write_csv(
        files["future_picks"],
        _future_pick_rows(league, active_draft, rosters_by_id, team_rows, traded_picks),
    )
    _write_csv(files["drafts"], _draft_rows(drafts))
    _write_csv(files["metadata"], _metadata_rows(league_id, league, files))

    return SleeperSnapshotResult(
        league_id=league_id,
        output_dir=output_dir,
        files=files,
        counts={name: _row_count(path) for name, path in files.items()},
    )


def _active_draft(drafts: list[dict[str, Any]], season: str) -> dict[str, Any] | None:
    season_drafts = [draft for draft in drafts if str(draft.get("season")) == season]
    pre_draft = [draft for draft in season_drafts if draft.get("status") == "pre_draft"]
    if pre_draft:
        return pre_draft[0]
    return season_drafts[0] if season_drafts else None


def _league_settings_rows(league: dict[str, Any]) -> list[dict[str, object]]:
    scoring = league.get("scoring_settings") or {}
    rows = [
        {
            "setting_group": "league",
            "setting_key": "league_id",
            "setting_value": league.get("league_id"),
            "source": "sleeper_api",
        },
        {
            "setting_group": "league",
            "setting_key": "name",
            "setting_value": league.get("name"),
            "source": "sleeper_api",
        },
        {
            "setting_group": "league",
            "setting_key": "season",
            "setting_value": league.get("season"),
            "source": "sleeper_api",
        },
        {
            "setting_group": "league",
            "setting_key": "roster_positions",
            "setting_value": "|".join(league.get("roster_positions") or []),
            "source": "sleeper_api",
        },
    ]
    rows.extend(
        {
            "setting_group": "scoring",
            "setting_key": key,
            "setting_value": value,
            "source": "sleeper_api",
        }
        for key, value in sorted(scoring.items())
    )
    return rows


def _team_rows(
    rosters: list[dict[str, Any]], users_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for roster in sorted(rosters, key=lambda item: int(item["roster_id"])):
        owner_id = str(roster.get("owner_id") or "")
        user = users_by_id.get(owner_id, {})
        metadata = user.get("metadata") or {}
        rows.append(
            {
                "roster_id": roster.get("roster_id"),
                "owner_id": owner_id,
                "display_name": user.get("display_name") or user.get("username") or "",
                "team_name": metadata.get("team_name") or user.get("display_name") or owner_id,
                "source": "sleeper_api",
            }
        )
    return rows


def _roster_rows(
    league: dict[str, Any],
    rosters: list[dict[str, Any]],
    users_by_id: dict[str, dict[str, Any]],
    players: dict[str, dict[str, Any]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    snapshot_date = _snapshot_date(league)
    season = league.get("season")
    for roster in sorted(rosters, key=lambda item: int(item["roster_id"])):
        owner_id = str(roster.get("owner_id") or "")
        user = users_by_id.get(owner_id, {})
        team_name = (
            (user.get("metadata") or {}).get("team_name")
            or user.get("display_name")
            or owner_id
        )
        player_ids = sorted(str(player_id) for player_id in roster.get("players") or [])
        for player_id in player_ids:
            player = players.get(player_id, {})
            player_name = (
                player.get("full_name")
                or player.get("search_full_name")
                or player_id
            )
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "season": season,
                    "team_id": str(roster.get("roster_id")),
                    "team_name": team_name,
                    "owner_name": user.get("display_name") or user.get("username") or "",
                    "player_id": player_id,
                    "player_name": player_name,
                    "position": player.get("position") or "",
                    "nfl_team": player.get("team") or "",
                    "roster_status": "rostered",
                    "league_rank": "",
                    "source": "sleeper_api",
                }
            )
    return rows


def _future_pick_rows(
    league: dict[str, Any],
    active_draft: dict[str, Any] | None,
    rosters_by_id: dict[int, dict[str, Any]],
    team_rows: list[dict[str, object]],
    traded_picks: list[dict[str, Any]],
) -> list[dict[str, object]]:
    if active_draft is None:
        return []

    season = int(str(active_draft.get("season") or league.get("season")))
    rounds = int((active_draft.get("settings") or {}).get("rounds") or 5)
    draft_slots = _draft_slots(active_draft, rosters_by_id)
    team_by_roster_id = {int(row["roster_id"]): row for row in team_rows}
    current_owner_by_pick = {
        (int(pick["season"]), int(pick["round"]), int(pick["roster_id"])): int(pick["owner_id"])
        for pick in traded_picks
        if str(pick.get("season")) == str(season)
    }

    rows: list[dict[str, object]] = []
    for round_number in range(1, rounds + 1):
        for original_roster_id, slot in sorted(draft_slots.items(), key=lambda item: item[1]):
            current_roster_id = current_owner_by_pick.get(
                (season, round_number, original_roster_id), original_roster_id
            )
            original_team = team_by_roster_id.get(original_roster_id, {})
            current_team = team_by_roster_id.get(current_roster_id, {})
            overall_pick = (round_number - 1) * len(draft_slots) + slot
            rows.append(
                {
                    "snapshot_date": _snapshot_date(league),
                    "season": season,
                    "pick_year": season,
                    "round": round_number,
                    "slot": slot,
                    "pick_label": f"{season} {round_number}.{slot:02d}",
                    "overall_pick": overall_pick,
                    "original_team_id": original_roster_id,
                    "original_team_name": original_team.get("team_name", original_roster_id),
                    "current_team_id": current_roster_id,
                    "current_team_name": current_team.get("team_name", current_roster_id),
                    "current_owner_name": current_team.get("display_name", ""),
                    "certainty": "sleeper_current_owner",
                    "source": "sleeper_api_traded_picks",
                }
            )
    return rows


def _draft_slots(
    active_draft: dict[str, Any], rosters_by_id: dict[int, dict[str, Any]]
) -> dict[int, int]:
    draft_order = active_draft.get("draft_order") or {}
    owner_to_roster = {
        str(roster.get("owner_id")): int(roster["roster_id"])
        for roster in rosters_by_id.values()
        if roster.get("owner_id")
    }
    slots: dict[int, int] = {}
    for owner_id, slot in draft_order.items():
        roster_id = owner_to_roster.get(str(owner_id))
        if roster_id is not None:
            slots[roster_id] = int(slot)
    if slots:
        return slots
    return {roster_id: roster_id for roster_id in sorted(rosters_by_id)}


def _draft_rows(drafts: list[dict[str, Any]]) -> list[dict[str, object]]:
    return [
        {
            "draft_id": draft.get("draft_id"),
            "season": draft.get("season"),
            "status": draft.get("status"),
            "type": draft.get("type"),
            "rounds": (draft.get("settings") or {}).get("rounds"),
            "teams": (draft.get("settings") or {}).get("teams"),
            "source": "sleeper_api",
        }
        for draft in sorted(drafts, key=lambda item: str(item.get("draft_id")))
    ]


def _metadata_rows(
    league_id: str, league: dict[str, Any], files: dict[str, Path]
) -> list[dict[str, object]]:
    return [
        {
            "snapshot_date": _snapshot_date(league),
            "league_id": league_id,
            "file_name": path.name,
            "source_name": "Sleeper API",
            "source_type": "read_only_api_snapshot",
            "review_status": "needs_review",
            "notes": (
                "Runtime app should consume this local CSV snapshot. "
                "League ranks must be merged from the league paper/ranking sheet."
            ),
        }
        for path in files.values()
    ]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _row_count(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def _snapshot_date(league: dict[str, Any]) -> str:
    return f"{league.get('season')}-pre-draft"
