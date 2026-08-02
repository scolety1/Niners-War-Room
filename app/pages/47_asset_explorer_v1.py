from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.post_release_status import render_source_freshness  # noqa: E402
from app.components.ui_framework import page_header, section_label  # noqa: E402
from src.services.governed_asset_registry_service import (  # noqa: E402
    load_governed_asset_registry,
)
from src.services.personal_workspace_service import load_store  # noqa: E402
from src.services.post_release_usability_service import governed_source_freshness  # noqa: E402


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
render_source_freshness(governed_source_freshness())

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
personal = {row["asset_id"]: row for row in load_store("personal_board").records}
frame["My Tier"] = frame["asset_id"].map(lambda key: personal.get(key, {}).get("my_tier", ""))
frame["My Rank"] = frame["asset_id"].map(lambda key: personal.get(key, {}).get("my_rank", ""))
frame["My Tags"] = frame["asset_id"].map(
    lambda key: ", ".join(personal.get(key, {}).get("tags", []))
)
frame["Watchlist"] = frame["asset_id"].map(lambda key: bool(personal.get(key, {}).get("watchlist")))
frame["Target"] = frame["asset_id"].map(lambda key: bool(personal.get(key, {}).get("target")))
frame["Avoid"] = frame["asset_id"].map(lambda key: bool(personal.get(key, {}).get("avoid")))
frame["Notes"] = frame["asset_id"].map(
    lambda key: "Yes" if personal.get(key, {}).get("notes") else ""
)
section_label("Find an asset")
controls = st.columns((2, 2, 1))
query = controls[0].text_input("Search name, team, or ID", placeholder="e.g. Puka, ARI, or 1.03")
types = controls[1].multiselect("Asset type", list(registry.counts), default=list(registry.counts))
blocked_only = controls[2].checkbox("Blocked only")
personal_filters = st.columns(3)
watchlist_only = personal_filters[0].checkbox("Watchlist only")
target_only = personal_filters[1].checkbox("Target only")
avoid_only = personal_filters[2].checkbox("Avoid only")

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
if watchlist_only:
    filtered = filtered[filtered["Watchlist"]]
if target_only:
    filtered = filtered[filtered["Target"]]
if avoid_only:
    filtered = filtered[filtered["Avoid"]]

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
            "My Tier",
            "My Rank",
            "My Tags",
            "Watchlist",
            "Target",
            "Avoid",
            "Notes",
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

workspace_links = st.columns(2)
workspace_links[0].link_button("Quick edit in Personal Board", "/personal-board")
workspace_links[1].link_button("Save an Asset Explorer view", "/saved-scenarios")
