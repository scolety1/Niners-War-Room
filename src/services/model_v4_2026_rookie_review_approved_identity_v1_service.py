"""Identity-only authority for the approved 2026 Rookie Review candidate.

This module has no score, rank, or formula behavior.  It admits the seven
former frozen identity blocks only by their unique official 2026 draft pick and
the pinned governed live ID for that exact pick.  Names and positions are
receipts used to reject a mismatch; they are never join keys.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


APPROVED_IDENTITY_CONTRACT = "APPROVED_OFFICIAL_PICK_PLUS_PINNED_GOVERNED_LIVE_ID_V1"
APPROVED_MANUAL_NAMES = frozenset({
    "De'Zhaun Stribling", "Nicholas Singleton", "Joe Royer", "Oscar Delp",
    "Deion Burks", "Colbie Young", "Carson Beck",
})


@dataclass(frozen=True)
class ApprovedRookieIdentity:
    official_draft_asset_id: str
    overall_pick: int
    player_name: str
    position: str
    live_player_id: str
    identity_contract: str = APPROVED_IDENTITY_CONTRACT
    identity_method: str = "EXACT_OFFICIAL_DRAFT_PICK_TO_PINNED_GOVERNED_LIVE_ID"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def approved_manual_identity_rows(
    blockers_path: Path, live_identity_path: Path
) -> tuple[ApprovedRookieIdentity, ...]:
    """Return exactly seven approved identities, or fail closed on any drift."""

    blockers = _rows(blockers_path)
    live_by_pick = {int(row["draft_pick"]): row for row in _rows(live_identity_path)}
    if len(live_by_pick) != 80:
        raise ValueError("live official draft identity universe must contain 80 unique picks")
    if len(blockers) != 7:
        raise ValueError("frozen blocker authority must contain exactly seven rows")
    approved: list[ApprovedRookieIdentity] = []
    for blocked in blockers:
        pick = int(blocked["overall_pick"])
        live = live_by_pick.get(pick)
        if live is None:
            raise ValueError(f"approved official draft pick missing from live identity: {pick}")
        if blocked["player_name"] != live["draft_name"] or blocked["position"] != live["draft_position"]:
            raise ValueError(f"official draft receipt mismatch at pick {pick}")
        if not live["player_id"]:
            raise ValueError(f"pinned governed live ID missing at pick {pick}")
        approved.append(ApprovedRookieIdentity(
            official_draft_asset_id=f"nflverse-draft:2026:{pick}",
            overall_pick=pick,
            player_name=blocked["player_name"],
            position=blocked["position"],
            live_player_id=live["player_id"],
        ))
    if {item.player_name for item in approved} != APPROVED_MANUAL_NAMES:
        raise ValueError("approved manual identity name set drifted")
    if len({item.overall_pick for item in approved}) != 7 or len({item.live_player_id for item in approved}) != 7:
        raise ValueError("approved manual identities are not unique")
    return tuple(sorted(approved, key=lambda item: item.overall_pick))
