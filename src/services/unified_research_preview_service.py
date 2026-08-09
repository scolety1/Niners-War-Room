"""Read-only access to the frozen unified dynasty research preview."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PACKET_DIR = ROOT / "docs/hq/model/nwr_unified_research_preview_v1_20260808"
BOARD_PATH = PACKET_DIR / "UNIFIED_DYNASTY_RESEARCH_PREVIEW.csv"
NEIGHBORHOODS_PATH = PACKET_DIR / "ROOKIE_VETERAN_NEIGHBORHOODS.csv"
MANIFEST_PATH = PACKET_DIR / "MANIFEST.json"
EXPECTED_BOARD_SHA256 = "8ab1bf7e1d33736d7609c7f8373cc7031dc24afed026278b8754a659a4af5dc0"
EXPECTED_NEIGHBORHOODS_SHA256 = "5ff806c997d385fcc85911b419fad53a9bf6af4f1f8c9da6b7cdc6a6bf7bcb82"
EXPECTED_SOURCE_HASHES = {
    "eligible_predictions.csv": "0b45e61b3b565d1ffae0ed81e930b1788edfb47cc7cda0bc95fe4f01706c3420",
    "current_veteran_frame.csv": "cbff65ec9e8397709724b3fbfea474c72c5fd5fe0835d4a533c334ebbd0a0d9e",
    "current_rookie_frame.csv": "6a0f6dc58416b2a87ac4454ab8b8e6ddfc8b070ff534f756e990e7633c136afd",
    "fresh_cohort_manifest.json": (
        "3b6b290dcc89b405d2188beb2e7854a8a0b4793f6425dec3a1ca2f2dc8ee66c2"
    ),
}
AUTHORITY = "RESEARCH_ONLY_NOT_PRODUCTION"
RANKED_STATUS = "RESEARCH_ONLY_NOT_ADMITTED"
BLOCKED_STATUS = "INSUFFICIENT / OUTSIDE MODEL SUPPORT"


@dataclass(frozen=True)
class UnifiedResearchPreview:
    board: pd.DataFrame
    neighborhoods: pd.DataFrame
    manifest: dict

    @property
    def ranked(self) -> pd.DataFrame:
        return self.board.loc[self.board["status"].eq(RANKED_STATUS)].copy()

    @property
    def blocked(self) -> pd.DataFrame:
        return self.board.loc[self.board["status"].eq(BLOCKED_STATUS)].copy()


def file_sha256(path: Path) -> str:
    """Hash canonical text bytes while tolerating Git's Windows newline checkout."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def load_unified_research_preview() -> UnifiedResearchPreview:
    """Load and fully validate the immutable research-only preview packet."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("authority") != AUTHORITY:
        raise ValueError("Unified research preview authority mismatch")
    if manifest.get("source_hashes") != EXPECTED_SOURCE_HASHES:
        raise ValueError("Unified research preview frozen source hashes mismatch")
    if file_sha256(BOARD_PATH) != EXPECTED_BOARD_SHA256:
        raise ValueError("Unified research preview board hash mismatch")
    if file_sha256(NEIGHBORHOODS_PATH) != EXPECTED_NEIGHBORHOODS_SHA256:
        raise ValueError("Unified research preview neighborhood hash mismatch")

    board = pd.read_csv(BOARD_PATH, dtype={"source_asset_id": "string"}, low_memory=False)
    neighborhoods = pd.read_csv(NEIGHBORHOODS_PATH, low_memory=False)
    if len(board) != 320 or len(neighborhoods) != 73:
        raise ValueError("Unified research preview row-count contract failed")
    if set(board["authority"].dropna()) != {AUTHORITY}:
        raise ValueError("Unified research preview contains non-research authority")
    ranked = board.loc[board["status"].eq(RANKED_STATUS)].copy()
    blocked = board.loc[board["status"].eq(BLOCKED_STATUS)].copy()
    if len(ranked) != 304 or len(blocked) != 16:
        raise ValueError("Unified research preview eligibility contract failed")
    if int(ranked["asset_type"].eq("VETERAN").sum()) != 231:
        raise ValueError("Unified research preview veteran count mismatch")
    if int(ranked["asset_type"].eq("ROOKIE").sum()) != 73:
        raise ValueError("Unified research preview rookie count mismatch")
    ranks = pd.to_numeric(ranked["research_rank"], errors="raise").astype(int).tolist()
    if ranks != list(range(1, 305)) or blocked["research_rank"].notna().any():
        raise ValueError("Blocked assets must be unranked and research ranks must be 1..304")
    if int(blocked["position"].eq("K").sum()) != 8:
        raise ValueError("Unified research preview kicker block count mismatch")
    prohibited = {"recommendation", "trade_verdict", "production_rank", "fair_value"}
    if prohibited.intersection(board.columns):
        raise ValueError("Unified research preview contains prohibited decision columns")
    return UnifiedResearchPreview(board=board, neighborhoods=neighborhoods, manifest=manifest)


def research_context_for_assets(
    preview: UnifiedResearchPreview, asset_ids: list[str]
) -> pd.DataFrame:
    """Return research context in caller order without changing caller authority."""
    order = {str(asset_id): index for index, asset_id in enumerate(asset_ids)}
    frame = preview.board.loc[preview.board["source_asset_id"].astype(str).isin(order)].copy()
    frame["_caller_order"] = frame["source_asset_id"].astype(str).map(order)
    return frame.sort_values("_caller_order", kind="stable").drop(columns="_caller_order")
