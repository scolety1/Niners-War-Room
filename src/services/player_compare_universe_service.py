"""Source-separated selector universe for owner-facing Player Compare."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.governed_asset_registry_service import GovernedAssetRegistry

CURRENT_PLAYER = "Current Player"
ROOKIE_REVIEW = "Rookie Review"
BLOCKED_ROOKIE = "Blocked Rookie"
COMPARE_ASSET_TYPES = (CURRENT_PLAYER, ROOKIE_REVIEW, BLOCKED_ROOKIE)
EXPECTED_COMPARE_COUNTS = {
    CURRENT_PLAYER: 240,
    ROOKIE_REVIEW: 73,
    BLOCKED_ROOKIE: 7,
}
NO_COMMON_SCALE_NOTE = (
    "No common scale: veteran and rookie evidence stays source-separated. "
    "Display/review only; no automatic recommendation is calculated."
)


@dataclass(frozen=True)
class PlayerCompareUniverse:
    frame: pd.DataFrame
    errors: tuple[str, ...]
    counts: dict[str, int]

    @property
    def loaded(self) -> bool:
        return not self.errors and self.counts == EXPECTED_COMPARE_COUNTS


def build_player_compare_universe(
    registry: GovernedAssetRegistry,
    *,
    evidence_rows: Sequence[Mapping[str, Any]] | None = None,
) -> PlayerCompareUniverse:
    """Build compare rows from governed asset IDs without identity inference or scale blending."""

    counts = {asset_type: registry.counts.get(asset_type, 0) for asset_type in COMPARE_ASSET_TYPES}
    errors = list(registry.errors)
    for asset_type, expected in EXPECTED_COMPARE_COUNTS.items():
        if counts[asset_type] != expected:
            errors.append(
                f"Player Compare requires {expected} governed {asset_type} rows; "
                f"found {counts[asset_type]}."
            )

    source_rows = evidence_rows if evidence_rows is not None else registry.rows
    rows = [_compare_row(row) for row in source_rows if row["asset_type"] in COMPARE_ASSET_TYPES]
    if len({row["asset_id"] for row in rows}) != len(rows):
        errors.append("Player Compare governed asset IDs are not unique.")
    if len({row["compare_select_label"] for row in rows}) != len(rows):
        errors.append("Player Compare governed selector labels are not unique.")

    frame = pd.DataFrame(rows)
    if not frame.empty:
        type_order = {asset_type: index for index, asset_type in enumerate(COMPARE_ASSET_TYPES)}
        frame["_type_order"] = frame["compare_asset_type"].map(type_order)
        frame["_rank_order"] = pd.to_numeric(frame["source_rank_value"], errors="coerce")
        frame = (
            frame.sort_values(
                ["_type_order", "_rank_order", "player"],
                na_position="last",
                kind="stable",
            )
            .drop(columns=["_type_order", "_rank_order"])
            .reset_index(drop=True)
        )
    return PlayerCompareUniverse(frame=frame, errors=tuple(dict.fromkeys(errors)), counts=counts)


def governed_source_identity(label: str, artifact_path: str | Path | None = None) -> str:
    """Return owner-facing provenance without exposing a filesystem location."""

    source = str(label or "Governed source").strip() or "Governed source"
    if artifact_path is None:
        return source
    basename = Path(artifact_path).name
    if not basename or basename.casefold() in source.casefold():
        return source
    return f"{source} ({basename})"


def _compare_row(asset: Mapping[str, Any]) -> dict[str, Any]:
    asset_type = asset["asset_type"]
    asset_id = asset["asset_id"]
    player_id = ""
    if asset_type in {CURRENT_PLAYER, ROOKIE_REVIEW}:
        player_id = asset_id.split(":", maxsplit=1)[1]
    source_rank_value = asset["rank_value"]
    canonical_complete = all(
        str(asset.get(field, "")).strip()
        for field in ("dynasty_rank", "position_rank", "nwr_dynasty_score")
    )
    return {
        "asset_id": asset_id,
        "player_id": player_id,
        "player": asset["asset_name"],
        "position": asset["position"],
        "nfl_team": asset["team"],
        "age": asset.get("age", ""),
        "compare_asset_type": asset_type,
        "compare_source_key": asset["source_label"],
        "compare_source_label": asset["source_label"],
        "compare_authority_status": asset["authority_status"],
        "source_rank_label": asset["rank_label"],
        "source_rank_value": source_rank_value,
        "source_score_label": asset["score_label"],
        "source_score_value": asset["score_value"],
        "source_tier": asset["tier"],
        "source_confidence": asset["confidence"],
        "source_warnings": asset["warnings"],
        "blocking_reason": asset["blocking_reason"],
        "comparison_scope": asset["comparison_scope"],
        "source_coverage": asset["source_label"],
        "source_status": f"Available: {asset['source_label']}",
        "freshness_status": asset.get("market_status", ""),
        "identity_status": asset.get("identity_status", ""),
        "missing_evidence": "Complete" if canonical_complete else "Optional evidence unavailable",
        "warning_flags": " ".join(asset.get("owner_caveats", ())),
        "dynasty_asset_rank": source_rank_value if asset_type == CURRENT_PLAYER else "",
        "nwr_rank": asset.get(
            "dynasty_rank", source_rank_value if asset_type == CURRENT_PLAYER else ""
        ),
        "position_rank": asset.get("position_rank", ""),
        "nwr_position_rank": asset.get("position_rank", ""),
        "nwr_dynasty_score": asset.get("nwr_dynasty_score", asset.get("score_value", "")),
        "market_dp_value": asset.get("market_dp_value", ""),
        "market_dp_rank": asset.get("market_dp_rank", ""),
        "market_status": asset.get("market_status", ""),
        "candidate_value_band": asset["tier"] if asset_type == ROOKIE_REVIEW else "",
        "risk_notes": asset["blocking_reason"] or asset["warnings"],
        "compare_select_label": (f"{asset['asset_name']} — {asset_type} · {asset['source_label']}"),
    }
