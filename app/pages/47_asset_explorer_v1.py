from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.owner_mode import owner_intro  # noqa: E402
from app.components.post_release_status import render_source_freshness  # noqa: E402
from app.components.ui_framework import page_header, section_label  # noqa: E402
from src.services.draft_day_app_v1_service import (  # noqa: E402
    load_dynasty_rankings,
    resolve_dynasty_rankings_path,
)
from src.services.governed_asset_registry_service import (  # noqa: E402
    load_governed_asset_registry,
)
from src.services.outcome_v3_display_service import load_outcome_v3_display  # noqa: E402
from src.services.owner_asset_evidence_service import (  # noqa: E402
    compose_owner_asset_evidence,
)
from src.services.owner_caveat_presentation_service import (  # noqa: E402
    owner_caveat_summary,
)
from src.services.personal_workspace_service import load_store  # noqa: E402
from src.services.post_release_usability_service import governed_source_freshness  # noqa: E402
from src.services.unified_research_preview_service import (  # noqa: E402
    load_unified_research_preview,
)


@st.cache_data
def _load_registry():
    current_board_path, _label, _warnings = resolve_dynasty_rankings_path()
    return load_governed_asset_registry(
        repo_root=REPO_ROOT,
        current_board_path=current_board_path,
    )


@st.cache_data
def _load_research_preview():
    return load_unified_research_preview()


registry = _load_registry()
_research = _load_research_preview()
_evidence = compose_owner_asset_evidence(
    registry.rows,
    dynasty_frame=load_dynasty_rankings().frame,
    research_frame=_research.board,
    outcome_frame=load_outcome_v3_display().frame,
)
page_header(
    "All Dynasty Assets",
    eyebrow="Owner Mode · Coverage and research gaps",
    description=(
        "Use this when Rankings does not cover the asset you need. Search veterans, "
        "rookies, blocked prospects, and picks in one catalog while keeping each "
        "source's authority and scale separate."
    ),
    status_items=(
        ("Read-only", "safe"),
        ("No common scale", "review"),
        ("No recommendation", "safe"),
    ),
)
owner_intro(
    "Know what NWR covers—and what still needs work.",
    "Browse ranked players, rookies, future picks, personal flags, research coverage, "
    "and missing-evidence states together.",
)
render_source_freshness(governed_source_freshness())

if registry.errors:
    for error in registry.errors:
        st.error(error)
    st.warning(
        "Invalid or missing authorities stay visible as unavailable; "
        "no fallback values are created."
    )

count_items = list(registry.counts.items())
for start in range(0, len(count_items), 4):
    batch = count_items[start : start + 4]
    for column, (asset_type, count) in zip(st.columns(len(batch)), batch, strict=True):
        column.metric(asset_type, count)

frame = pd.DataFrame(_evidence.rows)
rows_by_id = _evidence.by_id
try:
    research_preview = _load_research_preview()
    research_columns = research_preview.board[
        ["source_asset_id", "research_rank", "research_tier", "status"]
    ].rename(
        columns={
            "research_rank": "Unified Research Rank",
            "research_tier": "Unified Research Tier",
            "status": "Unified Research Status",
        }
    )
    frame = frame.merge(
        research_columns, left_on="asset_id", right_on="source_asset_id", how="left"
    )
except (OSError, ValueError):
    frame["Unified Research Rank"] = pd.NA
    frame["Unified Research Tier"] = ""
    frame["Unified Research Status"] = ""
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
frame["Major Caveat"] = frame["raw_caveat_codes"].map(owner_caveat_summary)
frame["Blocking Context"] = frame["blocking_reason"].map(owner_caveat_summary)
frame["Research Readiness"] = frame["research_status_owner"].replace("", "No research row")
section_label("Find an asset")
controls = st.columns((2, 2, 1, 2))
query = controls[0].text_input("Search name, team, or ID", placeholder="e.g. Puka, ARI, or 1.03")
types = controls[1].multiselect("Asset type", list(registry.counts), default=list(registry.counts))
blocked_only = controls[2].checkbox("Blocked only")
coverage_filter = controls[3].selectbox(
    "Coverage",
    ("All", "Ranked", "Research covered", "Missing research", "Blocked / pending"),
)
personal_filters = st.columns(3)
watchlist_only = personal_filters[0].checkbox("Watchlist only")
target_only = personal_filters[1].checkbox("Target only")
avoid_only = personal_filters[2].checkbox("Avoid only")
show_research_rank = st.checkbox(
    "Show Unified Research Rank (Research Only)",
    value=False,
    help="Optional frozen research context. Never a production rank or recommendation.",
)

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
if coverage_filter == "Ranked":
    filtered = filtered[filtered["rank_value"].astype(str).str.strip().ne("")]
elif coverage_filter == "Research covered":
    filtered = filtered[filtered["Unified Research Rank"].notna()]
elif coverage_filter == "Missing research":
    filtered = filtered[filtered["Unified Research Rank"].isna()]
elif coverage_filter == "Blocked / pending":
    filtered = filtered[
        filtered["blocking_reason"].astype(str).str.strip().ne("")
        | filtered["asset_type"].eq("Blocked Rookie")
    ]
if watchlist_only:
    filtered = filtered[filtered["Watchlist"]]
if target_only:
    filtered = filtered[filtered["Target"]]
if avoid_only:
    filtered = filtered[filtered["Avoid"]]

type_order = {name: index for index, name in enumerate(registry.counts)}
filtered["_type_order"] = filtered["asset_type"].map(type_order)
filtered["_rank_order"] = pd.to_numeric(filtered["rank_value"], errors="coerce").fillna(9999)
sort_mode = st.selectbox(
    "Sort",
    ("Source rank", "Unified Research Rank (Research Only)")
    if show_research_rank
    else ("Source rank",),
)
if sort_mode == "Unified Research Rank (Research Only)":
    filtered["_research_rank_order"] = pd.to_numeric(
        filtered["Unified Research Rank"], errors="coerce"
    ).fillna(9999)
    filtered = filtered.sort_values(["_research_rank_order", "asset_name"])
else:
    filtered = filtered.sort_values(["_type_order", "_rank_order", "asset_name"])
st.caption(
    f"Showing {len(filtered)} of {len(frame)} assets. "
    "Source ranks are never compared across asset types."
)
display_columns = [
    "asset_name",
    "asset_type",
    "position",
    "team",
    "rank_label",
    "rank_value",
    "position_rank",
    "tier",
    "confidence",
    "market_dp_rank",
    "market_status",
    "Major Caveat",
    "Blocking Context",
    "Research Readiness",
    "Unified Research Rank",
    "Unified Research Tier",
    "Unified Research Status",
    "My Tier",
    "My Rank",
    "My Tags",
    "Watchlist",
    "Target",
    "Avoid",
    "Notes",
]
if show_research_rank:
    st.warning(
        "Research Only — Not Production Authority. Calibration is not fully validated; no "
        "fresh mature 5Y rookie cohort exists. Decision support only."
    )
st.dataframe(
    filtered[display_columns],
    use_container_width=True,
    hide_index=True,
)
with st.expander("Advanced source and score columns", expanded=False):
    st.dataframe(
        filtered[
            [
                "asset_name",
                "asset_id",
                "source_label",
                "authority_status",
                "score_label",
                "score_value",
                "nwr_dynasty_score",
                "market_dp_value",
                "comparison_scope",
                "Unified Research Status",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )
if not filtered.empty:
    detail_asset = st.selectbox(
        "Open asset detail",
        filtered["asset_id"].astype(str).tolist(),
        format_func=lambda key: rows_by_id[key]["asset_name"],
    )
    st.markdown(f"[Open Player Detail](/player-detail?asset={quote(detail_asset, safe='')})")

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
