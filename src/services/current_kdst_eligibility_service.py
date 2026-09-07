"""Current-eligibility cross-check for the manual K/DST candidate pool.

RELEASE-BLOCKER FIX (urgent addendum): `manual_kdst_assets_from_sleeper_players`
(sleeper_redraft_owner_service.py) trusts Sleeper's own `active`/`team` fields
alone. Live-verified this pass: Sleeper's public `players/nfl` endpoint still
reports a real kicker as `active: true`, `team: "CAR"` after he had already
been cut -- confirmed stale relative to NWR's own already-admitted nflverse
`players` snapshot, whose `status` field for the exact same player already
says `CUT`. K/DST are never in the ranked/admitted projection universe (no
NWR model for them), so nothing was ever cross-checking the manual K/DST pool
against that already-admitted, more authoritative source -- a real, systemic
gap, not a name-specific one; nothing here references any specific player.

`STATUS_LABEL`: nflverse's own real status vocabulary (ACT/DEV/RES/CUT/RSN/
PUP/NWT/RSR/SUS/RET/EXE/INA/RLS -- see the dictionary this snapshot ships
with), mapped to the six real categories requested: a player is only
excluded from normal auto-recommendation when the status is UNAMBIGUOUSLY
structural (cut/released/retired/not-with-team/inactive-roster) -- never for
an injury-adjacent status (RES/PUP/SUS/DEV), which needs the same
individually-sourced, per-player judgment `current_player_status_overrides_service.py`
already uses for skill positions (never a blanket "every RES/PUP player is
season-out" rule). A player never removed from the candidate pool -- only
demoted out of normal auto-recommendation/CPU-selection eligibility; still
searchable/directly draftable to record a real external pick.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Status codes that unambiguously mean "not on any current NFL roster" --
# structural facts, never a medical/injury judgment call.
NOT_CURRENT_STATUSES = frozenset({"CUT", "RET", "NWT", "RLS", "INA"})
# Real, on-roster but not unrestricted -- eligible, disclosed separately,
# never blanket-excluded (matches the existing Higgins/Dell precedent).
LIMITED_BUT_ELIGIBLE_STATUSES = frozenset({"RES", "PUP", "SUS", "DEV", "RSN", "RSR", "EXE"})
ACTIVE_STATUSES = frozenset({"ACT"})

DEFAULT_PLAYERS_SNAPSHOT = Path(
    r"C:\NWR_SHARED_DATA\source_snapshots\nflverse\players\20260907T034013Z-8016e96a5623"
    r"\raw\players.parquet"
)


def _normalize_name(name: str) -> str:
    value = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", value)
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


@dataclass(frozen=True)
class EligibilityCounts:
    active: int = 0
    limited_but_eligible: int = 0
    season_out: int = 0
    not_with_team: int = 0
    retired_inactive: int = 0
    unknown: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "ACTIVE_ELIGIBLE": self.active,
            "TEMPORARILY_LIMITED_BUT_ELIGIBLE": self.limited_but_eligible,
            "SEASON_OUT": self.season_out,
            "NOT_WITH_TEAM": self.not_with_team,
            "RETIRED_INACTIVE": self.retired_inactive,
            "UNKNOWN": self.unknown,
        }


def load_nflverse_status_by_name(
    snapshot_path: Path = DEFAULT_PLAYERS_SNAPSHOT,
) -> dict[tuple[str, str], str]:
    """(normalized_name, position) -> nflverse status. Real, already-admitted
    identity data -- never fabricated, never re-fetched here."""
    try:
        frame = pd.read_parquet(snapshot_path)
    except (OSError, ValueError):
        return {}
    lookup: dict[tuple[str, str], str] = {}
    for _, row in frame.iterrows():
        name = str(row.get("display_name") or "")
        position = str(row.get("position") or "").upper()
        status = str(row.get("status") or "").upper()
        if not name or not position or not status:
            continue
        lookup[(_normalize_name(name), position)] = status
    return lookup


def classify_status(status: str | None, *, verified_season_out: bool = False) -> str:
    """One of the six real categories -- SEASON_OUT is reserved for an
    individually-sourced, verified override (never inferred from a bare
    RES/PUP status alone, which is TEMPORARILY_LIMITED_BUT_ELIGIBLE)."""
    if verified_season_out:
        return "SEASON_OUT"
    if not status:
        return "UNKNOWN"
    code = status.upper()
    if code in ACTIVE_STATUSES:
        return "ACTIVE_ELIGIBLE"
    if code in LIMITED_BUT_ELIGIBLE_STATUSES:
        return "TEMPORARILY_LIMITED_BUT_ELIGIBLE"
    if code == "NWT":
        return "NOT_WITH_TEAM"
    if code in {"RET"}:
        return "RETIRED_INACTIVE"
    if code in {"CUT", "RLS", "INA"}:
        return "NOT_WITH_TEAM"
    return "UNKNOWN"


def filter_current_kdst_assets(
    assets: Sequence[Mapping[str, str]],
    status_by_name: Mapping[tuple[str, str], str],
) -> tuple[tuple[dict[str, str], ...], dict[str, int]]:
    """Excludes a K asset ONLY when the cross-referenced nflverse status is
    unambiguously non-current (NOT_CURRENT_STATUSES) -- never for an
    injury-adjacent status, and never by name. DST assets (team defenses,
    not individual players) pass through unchanged; their own "real current
    NFL team" check is structural (a valid 32-team abbreviation), not a
    per-player status lookup.
    """
    kept: list[dict[str, str]] = []
    counts = {"kept": 0, "excluded_not_current": 0, "unknown": 0}
    for asset in assets:
        position = str(asset.get("position") or "").upper()
        if position != "K":
            kept.append(dict(asset))
            counts["kept"] += 1
            continue
        name = str(asset.get("player_name") or "")
        status = status_by_name.get((_normalize_name(name), "K"))
        if status is None:
            counts["unknown"] += 1
            kept.append(dict(asset))  # unknown != excluded -- disclosed, not silently dropped
            counts["kept"] += 1
            continue
        if status.upper() in NOT_CURRENT_STATUSES:
            counts["excluded_not_current"] += 1
            continue
        kept.append(dict(asset))
        counts["kept"] += 1
    return tuple(kept), counts
