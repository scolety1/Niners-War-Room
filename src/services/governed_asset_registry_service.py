"""Read-only, source-separated registry for governed NWR assets."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_BOARD_RELATIVE = Path(
    "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
)
ROOKIE_PACKET_RELATIVE = Path("docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730")
ROOKIE_BOARD_RELATIVE = ROOKIE_PACKET_RELATIVE / "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv"
BLOCKED_ROOKIES_RELATIVE = ROOKIE_PACKET_RELATIVE / "2026_ROOKIE_IDENTITY_BLOCKERS.csv"
PICKS_RELATIVE = Path(
    "docs/draft_day_exports/final_board_v1_20260622/app_props/mock_draft/mock_pick_context.csv"
)
FUTURE_PICKS_RELATIVE = Path("config/nwr_future_pick_context_v1.csv")

CURRENT_BOARD_SHA256 = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
ROOKIE_BOARD_SHA256 = "06853164a41cd9715accfc3c4f3e54d0cc915be6c55ebab040de6fc0abd96c2f"
BLOCKED_ROOKIES_SHA256 = "361011524dfbabc62cecaf4286d201b219e275a5fa8b43b57c93017eca56d19a"
EXPECTED_BLOCKED = {
    "Carson Beck",
    "Colbie Young",
    "De'Zhaun Stribling",
    "Deion Burks",
    "Joe Royer",
    "Nicholas Singleton",
    "Oscar Delp",
}


@dataclass(frozen=True)
class GovernedAssetRegistry:
    rows: tuple[dict[str, str], ...]
    errors: tuple[str, ...]
    counts: dict[str, int]
    source_hashes: dict[str, str]


def finished_v1_coverage_counts(frame: pd.DataFrame) -> dict[str, int]:
    positions = frame.get("position", pd.Series(index=frame.index, dtype=str)).astype(str)
    ranks = frame.get("nwr_rank", pd.Series(index=frame.index, dtype=str)).astype(str).str.strip()
    skill = positions.isin(("QB", "RB", "WR", "TE"))
    kickers = positions.eq("K")
    return {
        "structural_assets": int(frame.shape[0]),
        "ranked_skill_players": int((skill & ranks.ne("")).sum()),
        "unranked_kickers": int((kickers & ranks.eq("")).sum()),
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [{key: value or "" for key, value in row.items()} for row in csv.DictReader(handle)]


def _current_assets(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "asset_id": f"current:{row['player_id']}",
            "asset_type": "Current Player",
            "asset_name": row["player_name"],
            "position": row["position"],
            "team": row["nfl_team"],
            "source_label": "Finished V1",
            "authority_status": "Production" if row["nwr_rank"] else "Structural / Unranked",
            "rank_label": "NWR Dynasty Rank",
            "rank_value": row["nwr_rank"],
            "tier": "",
            "score_label": "NWR Dynasty Score",
            "score_value": row["nwr_dynasty_score"],
            "confidence": row.get("confidence_status", ""),
            "warnings": row.get("warning_flags", ""),
            "blocking_reason": "",
            "comparison_scope": "Comparable only with other Finished V1 current players",
        }
        for row in rows
    ]


def _rookie_assets(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "asset_id": f"rookie:{row['player_id']}",
            "asset_type": "Rookie Review",
            "asset_name": row["player_name"],
            "position": row["position"],
            "team": row["nfl_team"],
            "age": row["age_at_draft"],
            "source_label": "Model V4 2026 Rookie Review",
            "authority_status": "Review-Only",
            "rank_label": row["rank_label"],
            "rank_value": row["overall_review_rank"],
            "tier": row["tier"],
            "score_label": row["score_label"],
            "score_value": row["final_review_score"],
            "confidence": row["evidence_confidence"],
            "warnings": row["warning_codes"],
            "blocking_reason": row["blocking_reason"],
            "comparison_scope": "Comparable only within the 2026 Rookie Review",
        }
        for row in rows
    ]


def _blocked_assets(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "asset_id": f"blocked-rookie:{_slug(row['player_name'])}",
            "asset_type": "Blocked Rookie",
            "asset_name": row["player_name"],
            "position": row["position"],
            "team": row["nfl_team"],
            "source_label": "Model V4 2026 Rookie Review",
            "authority_status": "Blocked - Visible",
            "rank_label": "Not ranked",
            "rank_value": "",
            "tier": "",
            "score_label": "Not scored",
            "score_value": "",
            "confidence": "blocked",
            "warnings": row["identity_status"],
            "blocking_reason": row["blocking_reason"],
            "comparison_scope": "Visible for identity review; not comparable or rankable",
        }
        for row in rows
    ]


def _pick_assets(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "asset_id": f"pick:2026:{row['pick_label']}",
            "asset_type": "Draft Pick",
            "asset_name": f"2026 {row['pick_label']}",
            "position": "PICK",
            "team": row["current_owner"],
            "source_label": "Frozen 2026 Draft Context",
            "authority_status": "Context-Only",
            "rank_label": "Draft order",
            "rank_value": row["overall_pick"],
            "tier": "",
            "score_label": "No common value",
            "score_value": "",
            "confidence": row["source_status"],
            "warnings": "" if row["is_nwr_pick"].lower() == "true" else "owned_by_other_team",
            "blocking_reason": "",
            "comparison_scope": "Draft-order context only; no player-value equivalence",
        }
        for row in rows
    ]


def _future_pick_assets(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "asset_id": row["asset_id"],
            "asset_type": "Future Pick",
            "asset_name": row["asset_name"],
            "position": "PICK",
            "team": "Owner not encoded",
            "source_label": row["evidence_source"],
            "authority_status": row["evidence_status"],
            "rank_label": "No common rank",
            "rank_value": "",
            "tier": row["draft_context_tier"],
            "score_label": "No common value",
            "score_value": "",
            "confidence": row["uncertainty"],
            "warnings": f"slot_{row['slot'].lower()}; player_equivalence_unavailable",
            "blocking_reason": "",
            "comparison_scope": row["comparison_scope"],
        }
        for row in rows
    ]


def _slug(value: str) -> str:
    return "-".join(value.lower().replace("'", "").split())


def load_governed_asset_registry(
    *,
    repo_root: str | Path = REPO_ROOT,
    current_board_path: str | Path | None = None,
    expected_current_hash: str = CURRENT_BOARD_SHA256,
) -> GovernedAssetRegistry:
    root = Path(repo_root)
    current_path = (
        Path(current_board_path)
        if current_board_path is not None
        else root / CURRENT_BOARD_RELATIVE
    )
    rookie_path = root / ROOKIE_BOARD_RELATIVE
    blocked_path = root / BLOCKED_ROOKIES_RELATIVE
    picks_path = root / PICKS_RELATIVE
    future_picks_path = root / FUTURE_PICKS_RELATIVE
    errors: list[str] = []
    hashes: dict[str, str] = {}

    current: list[dict[str, str]] = []
    if not current_path.is_file():
        errors.append("Finished V1 board missing: governed current-player source unavailable")
    else:
        hashes["Finished V1"] = file_sha256(current_path)
        current = _rows(current_path)
        if hashes["Finished V1"] != expected_current_hash:
            errors.append("Finished V1 hash mismatch")
        if len(current) != 240 or len({row.get("player_id", "") for row in current}) != 240:
            errors.append("Finished V1 must contain 240 unique player IDs")

    hashes["Rookie Review"] = file_sha256(rookie_path)
    hashes["Blocked Rookies"] = file_sha256(blocked_path)
    rookie_authority = _rows(rookie_path)
    rookie = [row for row in rookie_authority if row["final_review_score"]]
    blocked = _rows(blocked_path)
    picks = _rows(picks_path)
    future_picks = _rows(future_picks_path)
    hashes["Future Pick Context"] = file_sha256(future_picks_path)
    if (
        hashes["Rookie Review"] != ROOKIE_BOARD_SHA256
        or len(rookie_authority) != 80
        or len(rookie) != 73
    ):
        errors.append("Rookie Review authority mismatch")
    if hashes["Blocked Rookies"] != BLOCKED_ROOKIES_SHA256:
        errors.append("blocked-rookie authority hash mismatch")
    if {row["player_name"] for row in blocked} != EXPECTED_BLOCKED:
        errors.append("blocked-rookie identity set mismatch")
    if len(picks) != 50 or len({row["pick_label"] for row in picks}) != 50:
        errors.append("draft context must contain 50 unique picks")
    if len(future_picks) != 9 or len({row["asset_id"] for row in future_picks}) != 9:
        errors.append("future-pick context must contain nine unique 2027-2029 round assets")

    rows = (
        *_current_assets(current),
        *_rookie_assets(rookie),
        *_blocked_assets(blocked),
        *_pick_assets(picks),
        *_future_pick_assets(future_picks),
    )
    if len({row["asset_id"] for row in rows}) != len(rows):
        errors.append("governed asset IDs are not unique")
    counts = {
        asset_type: sum(row["asset_type"] == asset_type for row in rows)
        for asset_type in (
            "Current Player",
            "Rookie Review",
            "Blocked Rookie",
            "Draft Pick",
            "Future Pick",
        )
    }
    return GovernedAssetRegistry(tuple(rows), tuple(errors), counts, hashes)
