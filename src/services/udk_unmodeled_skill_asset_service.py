"""Missing-skill-player manual assets, sourced from an owner-authorized UDK
identity snapshot.

Generalizes the existing K/DST "manual asset" pattern
(sleeper_redraft_owner_service.manual_kdst_assets_from_sleeper_players) to
skill positions: a real, externally-known QB/RB/WR/TE that has no match in
NWR's own modeled player universe becomes an explicit, clearly-labeled,
unranked draftable asset instead of forcing the owner to substitute a
random available player just to advance a live draft.

Root evidence: the real 2026 KHA draft. 5 real ESPN picks (Jonathon Brooks,
MarShawn Lloyd, Stefon Diggs, Tank Dell, Deebo Samuel Sr.) had no NWR
universe match and were recorded as owner placeholder substitutions --
see sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.md
(OWNER_PLACEHOLDER_FOR_MISSING_PLAYER). All 5, plus 9 more players not yet
hit by that specific draft, are already flagged `identity_status:
UNMATCHED` by an existing owner-run UDK identity-reconciliation pass
(sample_data/kha_real_draft_2026/udk_skill_position_snapshot_with_identity_status.csv).

This module never scores, ranks, or projects these players -- matching
section 17's rule for K/DST (EXTERNAL_UNMODELED_BY_NWR / "no invented NWR
model scores"), extended to any universe gap rather than a second bespoke
mechanism.
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

SKILL_POSITIONS = frozenset({"QB", "RB", "WR", "TE"})
UNMODELED_SKILL_AUTHORITY = "MANUAL — UNMODELED SKILL PLAYER (no NWR universe match)"


class UdkUnmodeledSkillAssetError(ValueError):
    """Raised when the UDK snapshot cannot be parsed into safe manual assets."""


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "unknown"


def parse_udk_unmatched_skill_assets(csv_path: str | Path) -> tuple[dict[str, str], ...]:
    """Read a UDK identity-reconciliation snapshot and return manual assets
    for every row explicitly flagged `identity_status: UNMATCHED` at a
    skill position. Rows already MATCHED to an NWR player are skipped --
    they are already represented in the ranked universe and must not get a
    second, conflicting manual entry.
    """

    path = Path(csv_path)
    if not path.is_file():
        raise UdkUnmodeledSkillAssetError(f"UDK snapshot not found: {path}")

    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"player_name_raw", "position", "team_raw", "identity_status"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise UdkUnmodeledSkillAssetError(
                f"UDK snapshot is missing required columns: {sorted(missing)}"
            )
        for raw in reader:
            if str(raw.get("identity_status") or "").strip().upper() != "UNMATCHED":
                continue
            position = str(raw.get("position") or "").strip().upper()
            if position not in SKILL_POSITIONS:
                continue
            name = str(raw.get("player_name_raw") or "").strip()
            team = str(raw.get("team_raw") or "").strip().upper()
            if not name or not team:
                # Known real defect in this source: at least one row has
                # commentary text merged into player_name_raw instead of a
                # real player (see docs/codex/KDST_AND_UNIVERSE_GAP_EVIDENCE_20260903.md).
                # Skip rather than admit garbage as a draftable identity.
                continue
            player_id = f"manual:{position}:{_slug(name)}"
            if player_id in seen_ids:
                continue
            seen_ids.add(player_id)
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": name,
                    "position": position,
                    "team": team,
                    "authority": UNMODELED_SKILL_AUTHORITY,
                }
            )
    return tuple(sorted(rows, key=lambda row: (row["position"], row["team"], row["player_name"])))


def merge_manual_assets(
    existing: Sequence[Mapping[str, str]],
    new_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Additive merge, keyed by player_id. Never overwrites an existing
    row (K/DST or otherwise) -- idempotent, safe to run repeatedly as the
    UDK snapshot is refreshed.
    """

    merged: dict[str, dict[str, str]] = {
        str(row.get("player_id") or ""): dict(row) for row in existing if row.get("player_id")
    }
    added = 0
    for row in new_rows:
        player_id = str(row.get("player_id") or "")
        if not player_id or player_id in merged:
            continue
        merged[player_id] = dict(row)
        added += 1
    ordered = sorted(
        merged.values(),
        key=lambda row: (row.get("position", ""), row.get("team", ""), row.get("player_name", "")),
    )
    return ordered


def write_manual_assets_file(
    path: str | Path, *, profile_id: str, assets: Sequence[Mapping[str, str]]
) -> None:
    """Atomic, additive-safe write matching the existing manual_assets file
    convention (desktop_facade.start_practical_redraft_mock): temp file
    then replace, schema_version 1.
    """

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "profile_id": profile_id, "assets": list(assets)}
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)
