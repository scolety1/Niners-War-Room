"""Shared read-only data loader for Owner Mode pages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from src.services.draft_day_app_v1_service import (
    load_dynasty_rankings,
    resolve_dynasty_rankings_path,
)
from src.services.governed_asset_registry_service import (
    GovernedAssetRegistry,
    load_governed_asset_registry,
)
from src.services.outcome_v3_display_service import OutcomeV3DisplayBundle, load_outcome_v3_display
from src.services.owner_asset_evidence_service import (
    OwnerAssetEvidenceBundle,
    compose_owner_asset_evidence,
)
from src.services.unified_research_preview_service import (
    UnifiedResearchPreview,
    load_unified_research_preview,
)


@dataclass(frozen=True)
class OwnerData:
    registry: GovernedAssetRegistry
    dynasty: object
    research: UnifiedResearchPreview
    outcome: OutcomeV3DisplayBundle
    evidence: OwnerAssetEvidenceBundle

    @property
    def current_rows(self) -> tuple[dict[str, object], ...]:
        return tuple(row for row in self.evidence.rows if row["asset_type"] == "Current Player")


@st.cache_data(show_spinner="Loading governed owner evidence...")
def load_owner_data(repo_root_text: str) -> OwnerData:
    repo_root = Path(repo_root_text)
    current_path, _label, _warnings = resolve_dynasty_rankings_path()
    registry = load_governed_asset_registry(repo_root=repo_root, current_board_path=current_path)
    dynasty = load_dynasty_rankings()
    research = load_unified_research_preview()
    outcome = load_outcome_v3_display()
    evidence = compose_owner_asset_evidence(
        registry.rows,
        dynasty_frame=dynasty.frame,
        research_frame=research.board,
        outcome_frame=outcome.frame,
    )
    return OwnerData(registry, dynasty, research, outcome, evidence)


def current_row_by_id(data: OwnerData, asset_id: str) -> dict[str, object] | None:
    player_id = asset_id.removeprefix("current:")
    match = data.dynasty.frame.loc[data.dynasty.frame["player_id"].astype(str).eq(player_id)]
    return None if match.empty else match.iloc[0].to_dict()
