"""Read-only, owner-authorized external draft-day intelligence for display
next to NWR in the Redraft Draft Room -- UDK, FantasyPros, and current-alert
context already merged into a local CSV by a separate, already-run tool.

This module does NOT modify NWR Core, projections, replacement/scarcity
math, recommendation scoring, or persist any external field as model
authority. It only reads an existing file and returns a lightweight,
player-id-keyed lookup map. Any failure (file missing, unreadable, malformed)
returns an "unavailable" result -- it must never raise, and must never block
the Draft Room.
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

from src.services.redraft_engine_v1_service import RankingResult

DEFAULT_CHEAT_SHEET_PATH = Path(r"C:\NWR_DRAFT_DAY_TOOLS\KHA_FINAL_CHEAT_SHEET.csv")


def _cheat_sheet_path() -> Path:
    override = os.environ.get("NWR_KHA_CHEAT_SHEET_PATH", "").strip()
    return Path(override) if override else DEFAULT_CHEAT_SHEET_PATH


def _norm_name(name: str) -> str:
    name = re.sub(r"\b(Jr\.?|Sr\.?|II|III|IV|V)\b\.?", "", name, flags=re.I)
    return "".join(ch for ch in name.lower() if ch.isalnum())


_DISPLAY_FIELDS = {
    "espn_adp": "espnAdp", "nwr_vs_espn_gap": "nwrVsEspnGap",
    "fantasypros_ecr": "fantasyProsEcr", "fantasypros_tier": "fantasyProsTier",
    "fantasypros_projected_points": "fantasyProsProjectedPoints", "nwr_vs_fantasypros_gap": "nwrVsFantasyProsGap",
    "udk_position_rank": "udkPositionRank", "udk_tier": "udkTier", "udk_adp_raw": "udkAdp",
    "udk_risk": "udkRisk", "udk_upside": "udkUpside", "udk_projected_points": "udkProjectedPoints",
    "current_alert": "currentAlert", "current_alert_severity": "currentAlertSeverity",
    "udk_current_conflict_flag": "udkCurrentConflictFlag",
}


def load_external_intelligence(ranking: RankingResult) -> dict[str, Any]:
    """Returns {"available": bool, "generatedNote": str, "byPlayerId": {player_id: {...fields}}}.
    Never raises."""
    path = _cheat_sheet_path()
    if not path.is_file():
        return {"available": False, "generatedNote": "EXTERNAL INTEL UNAVAILABLE -- file not found", "byPlayerId": {}}
    try:
        with path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return {"available": False, "generatedNote": "EXTERNAL INTEL UNAVAILABLE -- file unreadable", "byPlayerId": {}}

    nwr_by_key = {
        (row.position, _norm_name(row.player_name), row.team): row.player_id
        for row in ranking.rows
    }
    by_player_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        try:
            key = (str(row.get("position", "")), _norm_name(str(row.get("player_name", ""))), str(row.get("team", "")))
        except Exception:  # noqa: BLE001 -- a malformed row must not break the whole map
            continue
        player_id = nwr_by_key.get(key)
        if not player_id:
            continue  # unmatched external row simply does not enrich any NWR player
        entry: dict[str, Any] = {}
        for csv_field, js_field in _DISPLAY_FIELDS.items():
            value = row.get(csv_field, "")
            entry[js_field] = value if value not in ("", None, "API_TIER_NOT_RETURNED") else None
        by_player_id[player_id] = entry

    return {
        "available": True,
        "generatedNote": f"{len(by_player_id)} of {len(ranking.rows)} NWR players enriched from the owner's external cheat sheet",
        "byPlayerId": by_player_id,
    }
