from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header, section_label  # noqa: E402
from src.services.governed_asset_registry_service import (  # noqa: E402
    load_governed_asset_registry,
)


@st.cache_data
def _load_registry():
    return load_governed_asset_registry(repo_root=REPO_ROOT)


registry = _load_registry()
page_header(
    "Asset Explorer",
    eyebrow="Source-separated registry",
    description=(
        "Search current players, 2026 rookie-review assets, visibly blocked rookies, "
        "and draft picks without blending their ranks or scores."
    ),
    status_items=(
        ("Read-only", "safe"),
        ("No common scale", "review"),
        ("No recommendation", "safe"),
    ),
)

if registry.errors:
    for error in registry.errors:
        st.error(error)
    st.warning(
        "Invalid or missing authorities stay visible as unavailable; "
        "no fallback values are created."
    )

metrics = st.columns(4)
for column, asset_type in zip(metrics, registry.counts, strict=True):
    column.metric(asset_type, registry.counts[asset_type])

frame = pd.DataFrame(registry.rows)
section_label("Find an asset")
controls = st.columns((2, 2, 1))
query = controls[0].text_input("Search name, team, or ID", placeholder="e.g. Puka, ARI, or 1.03")
types = controls[1].multiselect("Asset type", list(registry.counts), default=list(registry.counts))
blocked_only = controls[2].checkbox("Blocked only")

filtered = frame[frame["asset_type"].isin(types)].copy()
if query.strip():
    needle = query.strip().casefold()
    searchable = filtered[["asset_id", "asset_name", "team", "position"]].fillna("")
    mask = searchable.apply(
        lambda column: column.str.casefold().str.contains(needle, regex=False)
    ).any(axis=1)
    filtered = filtered[mask]
if blocked_only:
    filtered = filtered[filtered["asset_type"].eq("Blocked Rookie")]

type_order = {name: index for index, name in enumerate(registry.counts)}
filtered["_type_order"] = filtered["asset_type"].map(type_order)
filtered["_rank_order"] = pd.to_numeric(filtered["rank_value"], errors="coerce").fillna(9999)
filtered = filtered.sort_values(["_type_order", "_rank_order", "asset_name"])
st.caption(
    f"Showing {len(filtered)} of {len(frame)} assets. "
    "Source ranks are never compared across asset types."
)
st.dataframe(
    filtered[
        [
            "asset_name",
            "asset_type",
            "position",
            "team",
            "source_label",
            "authority_status",
            "rank_label",
            "rank_value",
            "tier",
            "score_label",
            "score_value",
            "confidence",
            "warnings",
            "blocking_reason",
            "comparison_scope",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

with st.expander("Authority and safe-use guide"):
    st.markdown(
        """
        - **Finished V1:** production current-player rank and score;
          comparable only within Finished V1.
        - **Rookie Review:** review-only rank and score;
          comparable only within the 2026 rookie cohort.
        - **Blocked rookies:** visible but unranked and unscored until exact identity is resolved.
        - **Draft picks:** draft-order context only; no player-value equivalence.

        Asset Explorer never recommends, reorders canonical sources, or creates a
        cross-source value.
        """
    )
