"""Canonical owner-facing evidence composition across NWR product surfaces.

The composer preserves valid Finished V1 fields when optional evidence is absent.  Market,
research, and Outcome rows are appended as explicitly labeled context and never replace the
canonical identity, rank, position rank, or score.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.market_baseline_service import (
    DEFAULT_ARTIFACT_DIR,
    join_market_to_players,
    load_market_freshness,
)
from src.services.owner_caveat_presentation_service import owner_caveats, owner_evidence_status

NOT_AVAILABLE = "Not available"
NOT_APPLICABLE = "Not applicable"
EXACT_IDENTITY = "Exact governed identity"

_OUTCOME_THRESHOLD = {"QB": 12, "RB": 24, "WR": 24, "TE": 12}
_OUTCOME_HORIZONS = ("THIS_YEAR", "WITHIN_3Y")


@dataclass(frozen=True)
class OwnerAssetEvidenceBundle:
    rows: tuple[dict[str, Any], ...]
    market_freshness: dict[str, str]
    errors: tuple[str, ...]

    @property
    def by_id(self) -> dict[str, dict[str, Any]]:
        return {str(row["asset_id"]): row for row in self.rows}


def compose_owner_asset_evidence(
    registry_rows: Sequence[Mapping[str, Any]],
    *,
    dynasty_frame: pd.DataFrame | None = None,
    research_frame: pd.DataFrame | None = None,
    outcome_frame: pd.DataFrame | None = None,
    market_artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
    include_market: bool = True,
) -> OwnerAssetEvidenceBundle:
    """Compose one canonical display row per governed asset ID."""

    errors: list[str] = []
    dynasty = (dynasty_frame if dynasty_frame is not None else pd.DataFrame()).copy()
    market_freshness: dict[str, str] = {}
    if include_market and not dynasty.empty:
        try:
            dynasty = join_market_to_players(dynasty, market_artifact_dir)
            market_freshness = load_market_freshness(market_artifact_dir)
        except (OSError, ValueError, AssertionError) as exc:
            errors.append(f"Market context unavailable: {exc}")
    by_player_id = _rows_by(dynasty, "player_id")
    research_by_asset = _rows_by(
        research_frame if research_frame is not None else pd.DataFrame(),
        "source_asset_id",
    )
    outcome = outcome_frame if outcome_frame is not None else pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for source in registry_rows:
        row = dict(source)
        asset_id = _text(row.get("asset_id"))
        current = {}
        if asset_id.startswith("current:"):
            current = by_player_id.get(asset_id.removeprefix("current:"), {})
        research = research_by_asset.get(asset_id, {})
        raw_caveats = _first_present(
            current.get("warning_flags"),
            row.get("warnings"),
            row.get("blocking_reason"),
        )

        # Canonical Finished V1 values win. Optional enrichments only fill context fields.
        row.update(
            {
                "player_id": _first_present(current.get("player_id"), _asset_player_id(asset_id)),
                "asset_name": _first_present(current.get("player_name"), row.get("asset_name")),
                "position": _first_present(current.get("position"), row.get("position")),
                "team": _first_present(current.get("nfl_team"), row.get("team")),
                "age": _first_present(current.get("age")),
                "dynasty_rank": _first_present(
                    current.get("nwr_rank"),
                    row.get("rank_value") if row.get("asset_type") == "Current Player" else "",
                ),
                "position_rank": _first_present(current.get("nwr_position_rank")),
                "nwr_dynasty_score": _first_present(
                    current.get("nwr_dynasty_score"),
                    row.get("score_value") if row.get("asset_type") == "Current Player" else "",
                ),
                "value_band": _first_present(current.get("candidate_value_band"), row.get("tier")),
                "confidence": _first_present(
                    current.get("confidence_band"),
                    current.get("confidence_status"),
                    row.get("confidence"),
                ),
                "identity_status": EXACT_IDENTITY if asset_id else NOT_AVAILABLE,
                "raw_caveat_codes": raw_caveats,
                "owner_caveats": owner_caveats(raw_caveats),
                "market_dp_value": _first_present(current.get("dp_value_1qb")),
                "market_dp_rank": _first_present(current.get("dp_market_rank_1qb")),
                "market_dp_ecr": _first_present(current.get("dp_ecr_pos")),
                "market_dp_age": _first_present(current.get("dp_age")),
                "market_join": _first_present(current.get("market_join_confidence")),
                "market_sanity_label": _first_present(current.get("market_sanity_label")),
                "market_status": _market_status(current, market_freshness),
                "market_evidence_date": _first_present(
                    market_freshness.get("upstream_scrape_date")
                ),
                "research_rank": _first_present(research.get("research_rank")),
                "research_tier": _first_present(research.get("research_tier")),
                "research_status": _first_present(research.get("status")),
                "research_status_owner": owner_evidence_status(research.get("status")),
                "research_confidence": _first_present(research.get("confidence")),
                "research_outlook_3y": _first_present(research.get("outlook_3y")),
                "research_outlook_5y": _first_present(research.get("outlook_5y")),
                "research_ceiling_signal": _first_present(research.get("ceiling_signal")),
                "research_downside_signal": _first_present(research.get("downside_signal")),
                "outcome_signals": _outcome_signals(asset_id, row, outcome),
            }
        )
        rows.append(row)
    return OwnerAssetEvidenceBundle(tuple(rows), market_freshness, tuple(errors))


def _rows_by(frame: pd.DataFrame, key: str) -> dict[str, dict[str, Any]]:
    if frame.empty or key not in frame.columns:
        return {}
    return {_text(row.get(key)): row for row in frame.to_dict("records") if _text(row.get(key))}


def _asset_player_id(asset_id: str) -> str:
    if asset_id.startswith(("current:", "rookie:")):
        return asset_id.split(":", maxsplit=1)[1]
    return ""


def _first_present(*values: object) -> str:
    for value in values:
        text = _text(value)
        if text and text.casefold() not in {
            "nan",
            "none",
            "null",
            "n/a",
            "not enough information",
        }:
            return text
    return ""


def _text(value: object) -> str:
    return str(value if value is not None else "").strip()


def _market_status(current: Mapping[str, Any], freshness: Mapping[str, str]) -> str:
    if not _first_present(current.get("dp_value_1qb"), current.get("dp_market_rank_1qb")):
        return NOT_AVAILABLE
    status = _first_present(freshness.get("freshness_status"), current.get("freshness_status"))
    evidence_date = _first_present(freshness.get("upstream_scrape_date"))
    if "STALE" in status or "FETCH_FAILED" in status:
        return f"Stale as of {evidence_date}" if evidence_date else "Stale"
    if status.startswith("GREEN"):
        return f"Current as of {evidence_date}" if evidence_date else "Current"
    return f"Available as of {evidence_date}" if evidence_date else "Available"


def _outcome_signals(
    asset_id: str,
    asset: Mapping[str, Any],
    outcome: pd.DataFrame,
) -> tuple[str, ...]:
    if not asset_id.startswith("current:") or outcome.empty:
        return ()
    player_id = asset_id.removeprefix("current:")
    position = _text(asset.get("position")).upper()
    threshold = _OUTCOME_THRESHOLD.get(position)
    if threshold is None or not {"player_id", "position", "threshold", "horizon"}.issubset(
        outcome.columns
    ):
        return ()
    selected = outcome.loc[
        outcome["player_id"].astype(str).eq(player_id)
        & outcome["position"].astype(str).str.upper().eq(position)
        & pd.to_numeric(outcome["threshold"], errors="coerce").eq(threshold)
        & outcome["horizon"].astype(str).str.upper().isin(_OUTCOME_HORIZONS)
    ]
    signals: list[str] = []
    for horizon in _OUTCOME_HORIZONS:
        match = selected.loc[selected["horizon"].astype(str).str.upper().eq(horizon)]
        if match.empty:
            continue
        row = match.iloc[0]
        probability = _first_present(row.get("probability_display"))
        evidence = _first_present(row.get("evidence_state"))
        if not probability or evidence in {
            "insufficient_current_evidence",
            "blocked_or_unsupported",
        }:
            continue
        horizon_label = _first_present(row.get("horizon_label"), horizon.replace("_", " ").title())
        signals.append(f"{position} T{threshold} {horizon_label}: {probability}")
    return tuple(signals)
