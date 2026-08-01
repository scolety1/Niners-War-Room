from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header  # noqa: E402
from src.services.governed_asset_registry_service import load_governed_asset_registry  # noqa: E402

registry = load_governed_asset_registry(repo_root=REPO_ROOT)
page_header(
    "2026 Rookie Board",
    eyebrow="Model V4 Rookie Review",
    description=(
        "All 80 drafted prospects: 73 scored review-only assets and seven "
        "visible identity blockers."
    ),
    status_items=(("Review-Only", "review"), ("73 scored", "safe"), ("7 blocked", "blocked")),
)
rookies = pd.DataFrame(
    row for row in registry.rows if row["asset_type"] in {"Rookie Review", "Blocked Rookie"}
)
positions = sorted(rookies["position"].unique())
selected = st.multiselect("Position", positions, default=positions)
show_blocked = st.checkbox("Include blocked rookies", value=True)
filtered = rookies[rookies["position"].isin(selected)].copy()
if not show_blocked:
    filtered = filtered[filtered["asset_type"].eq("Rookie Review")]
filtered["_rank"] = pd.to_numeric(filtered["rank_value"], errors="coerce").fillna(9999)
filtered = filtered.sort_values(["_rank", "position", "asset_name"])
st.dataframe(
    filtered[
        [
            "asset_name",
            "position",
            "team",
            "authority_status",
            "rank_value",
            "tier",
            "score_value",
            "confidence",
            "warnings",
            "blocking_reason",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)
st.info(
    "Rookie Review scores and ranks do not replace Finished V1 and are not directly comparable "
    "with veteran scores, draft picks, or market values."
)
