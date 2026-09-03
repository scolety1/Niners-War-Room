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
DEFAULT_UDK_SNAPSHOT_PATH = Path(r"C:\NWR_DRAFT_DAY_TOOLS\2026-09-02\udk\KHA_UDK_2026_SNAPSHOT.csv")


def _cheat_sheet_path() -> Path:
    override = os.environ.get("NWR_KHA_CHEAT_SHEET_PATH", "").strip()
    return Path(override) if override else DEFAULT_CHEAT_SHEET_PATH


def _udk_snapshot_path() -> Path:
    override = os.environ.get("NWR_KHA_UDK_SNAPSHOT_PATH", "").strip()
    return Path(override) if override else DEFAULT_UDK_SNAPSHOT_PATH


_UDK_SNAPSHOT_FIELDS = {
    "udk_position_rank": "udkPositionRank", "udk_tier": "udkTier", "udk_adp_raw": "udkAdp",
    "udk_risk": "udkRisk", "udk_upside": "udkUpside", "udk_projected_points": "udkProjectedPoints",
}


def _load_udk_by_player_id() -> dict[str, dict[str, Any]]:
    """UDK fields keyed directly by the nwr_player_id the UDK ingestion pipeline
    already resolved (KHA_UDK_2026_SNAPSHOT.csv's own identity-matching pass,
    which tolerates provider team-code differences like LAR/LA, ARI/AZ,
    JAC/JAX and Jr./Sr./III suffixes). No re-matching, no team-code
    comparison, no fuzzy logic here -- a plain dict lookup by the identity
    that pipeline already committed to. Returns {} on any failure."""
    path = _udk_snapshot_path()
    if not path.is_file():
        return {}
    try:
        with path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return {}
    by_player_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        player_id = str(row.get("nwr_player_id", "")).strip()
        if not player_id or str(row.get("identity_status", "")).strip() != "MATCHED":
            continue
        fields: dict[str, Any] = {}
        for csv_field, js_field in _UDK_SNAPSHOT_FIELDS.items():
            value = row.get(csv_field, "")
            fields[js_field] = value if value not in ("", None, "UNKNOWN") else None
        # A player can appear on the snapshot from both default.pdf and
        # expanded.pdf reconciliation; keep the first (they're checked
        # identical -- zero field-mismatch -- at ingestion time).
        by_player_id.setdefault(player_id, fields)
    return by_player_id


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
    """Returns {"available": bool, "generatedNote": str, "entries": [{"playerId": ..., ...fields}]}.

    Deliberately a LIST, not a dict keyed by player_id: the shared desktop-API
    response envelope (src/application/contracts.py:public_json_value)
    recursively camelCases every dict key for contract consistency, which
    silently mangles opaque identifiers like "00-0034857" into "000034857"
    -- a dict-of-player-id-keys would round-trip through the API with none
    of its keys matching the original player IDs. Keeping player_id as an
    ordinary field value inside each list entry avoids that entirely.
    Never raises."""
    path = _cheat_sheet_path()
    if not path.is_file():
        return {"available": False, "generatedNote": "EXTERNAL INTEL UNAVAILABLE -- file not found", "entries": []}
    try:
        with path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return {"available": False, "generatedNote": "EXTERNAL INTEL UNAVAILABLE -- file unreadable", "entries": []}

    nwr_by_key = {
        (row.position, _norm_name(row.player_name), row.team): row.player_id
        for row in ranking.rows
    }
    udk_by_player_id = _load_udk_by_player_id()
    udk_overlay_count = 0
    entries: list[dict[str, Any]] = []
    for row in rows:
        try:
            key = (str(row.get("position", "")), _norm_name(str(row.get("player_name", ""))), str(row.get("team", "")))
        except Exception:  # noqa: BLE001 -- a malformed row must not break the whole map
            continue
        player_id = nwr_by_key.get(key)
        if not player_id:
            continue  # unmatched external row simply does not enrich any NWR player
        entry: dict[str, Any] = {"playerId": player_id}
        for csv_field, js_field in _DISPLAY_FIELDS.items():
            value = row.get(csv_field, "")
            entry[js_field] = value if value not in ("", None, "API_TIER_NOT_RETURNED") else None
        # Overlay UDK fields from the already-resolved identity mapping,
        # not the cheat sheet's own (provider-team-code-sensitive) copy of
        # them -- this is what recovers players like Puka Nacua (LAR/LA),
        # Matthew Stafford (LAR/LA), and Trey McBride (ARI/AZ) whose UDK
        # data the cheat-sheet build's own exact-team-match had missed.
        resolved = udk_by_player_id.get(player_id)
        if resolved is not None:
            entry.update(resolved)
            udk_overlay_count += 1
        entries.append(entry)

    return {
        "available": True,
        "generatedNote": (
            f"{len(entries)} of {len(ranking.rows)} NWR players enriched from the owner's external cheat sheet "
            f"({udk_overlay_count} with identity-resolved UDK data)"
        ),
        "entries": entries,
    }
