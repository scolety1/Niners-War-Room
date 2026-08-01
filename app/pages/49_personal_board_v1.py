from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.components.ui_framework import page_header, section_label  # noqa: E402
from src.services.governed_asset_registry_service import (  # noqa: E402
    load_governed_asset_registry,
)
from src.services.personal_workspace_service import (  # noqa: E402
    WorkspaceValidationError,
    delete_personal_entry,
    export_personal_board,
    import_personal_board,
    load_store,
    save_personal_entry,
)

registry = load_governed_asset_registry(repo_root=ROOT)
assets = {row["asset_id"]: row for row in registry.rows}
asset_types = {asset_id: row["asset_type"] for asset_id, row in assets.items()}
saved = load_store("personal_board")
personal = {row["asset_id"]: row for row in saved.records}

page_header(
    "Personal Board",
    eyebrow="NWR Personal Workspace V1",
    description=(
        "Organize governed assets with your own tiers, order, flags, tags, and notes. "
        "Personal fields never replace canonical source ranks."
    ),
    status_items=(
        ("Local-only", "safe"),
        ("Explicit save", "safe"),
        ("Canonical read-only", "review"),
    ),
)

if registry.errors:
    for error in registry.errors:
        st.warning(error)

counts = st.columns(4)
counts[0].metric("Personal entries", len(personal))
counts[1].metric("Watchlist", sum(bool(row.get("watchlist")) for row in personal.values()))
counts[2].metric("Targets", sum(bool(row.get("target")) for row in personal.values()))
counts[3].metric("Avoid", sum(bool(row.get("avoid")) for row in personal.values()))

section_label("Edit one governed asset")
options = sorted(assets, key=lambda key: (assets[key]["asset_name"], key))
with st.form("personal-board-edit"):
    asset_id = st.selectbox(
        "Governed asset",
        options,
        format_func=lambda key: (
            f"{assets[key]['asset_name']} · {assets[key]['asset_type']} · "
            f"{assets[key]['source_label']}"
        ),
    )
    prior = personal.get(asset_id, {})
    cols = st.columns(3)
    my_tier = cols[0].text_input("My Tier", value=str(prior.get("my_tier", "")))
    my_rank = cols[1].number_input("My Rank", min_value=0, value=int(prior.get("my_rank") or 0))
    conviction = cols[2].selectbox(
        "My Conviction",
        ("Unspecified", "Low", "Medium", "High"),
        index=("Unspecified", "Low", "Medium", "High").index(
            str(prior.get("conviction", "Unspecified"))
        ),
    )
    flags = st.columns(6)
    watchlist = flags[0].checkbox("Watchlist", value=bool(prior.get("watchlist")))
    target = flags[1].checkbox("Target", value=bool(prior.get("target")))
    avoid = flags[2].checkbox("Avoid / DND", value=bool(prior.get("avoid")))
    sleeper = flags[3].checkbox("Sleeper", value=bool(prior.get("sleeper")))
    sell_high = flags[4].checkbox("Sell high", value=bool(prior.get("sell_high")))
    buy_low = flags[5].checkbox("Buy low", value=bool(prior.get("buy_low")))
    tags = st.text_input("My Tags", value=", ".join(prior.get("tags", [])))
    notes = st.text_area("My Notes", value=str(prior.get("notes", "")), max_chars=20_000)
    team_window = st.selectbox(
        "My Team Window", ("Contending", "Balanced", "Rebuilding", "Custom/Unspecified")
    )
    submitted = st.form_submit_button("Save Personal Board entry", type="primary")

st.info(
    "Unsaved form changes remain in this browser session only. "
    "Nothing is written until you choose Save."
)

if submitted:
    entry = {
        "asset_id": asset_id,
        "asset_type": assets[asset_id]["asset_type"],
        "source_authority_version": registry.source_hashes.get(
            assets[asset_id]["source_label"], "governed-context"
        ),
        "my_tier": my_tier,
        "my_rank": my_rank or None,
        "watchlist": watchlist,
        "target": target,
        "avoid": avoid,
        "sleeper": sleeper,
        "sell_high": sell_high,
        "buy_low": buy_low,
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
        "notes": notes,
        "conviction": conviction,
        "team_window": team_window,
    }
    try:
        st.session_state["personal_board_undo"] = {
            "asset_id": asset_id,
            "previous": dict(prior) if prior else None,
        }
        save_personal_entry(entry, asset_registry=asset_types)
        st.success("Personal Board entry saved locally. Canonical ranks were not changed.")
    except WorkspaceValidationError as exc:
        st.error(f"Save blocked: {exc}")

undo = st.session_state.get("personal_board_undo")
if isinstance(undo, dict) and st.button("Undo last Personal Board edit"):
    try:
        if undo.get("previous"):
            save_personal_entry(undo["previous"], asset_registry=asset_types)
        else:
            delete_personal_entry(str(undo["asset_id"]), confirmed=True)
        st.session_state.pop("personal_board_undo", None)
        st.success("Last Personal Board edit was undone locally.")
    except WorkspaceValidationError as exc:
        st.error(f"Undo blocked: {exc}")

with st.expander("Archive or permanently remove one personal overlay entry"):
    st.caption("Only the personal overlay is removed. The governed asset remains unchanged.")
    remove_id = st.selectbox(
        "Personal entry to remove",
        sorted(personal),
        format_func=lambda key: assets.get(key, {}).get("asset_name", key),
        disabled=not personal,
    )
    confirm_remove = st.checkbox("Confirm permanent removal of this personal entry")
    if st.button("Remove personal entry", disabled=not personal):
        result = delete_personal_entry(remove_id, confirmed=confirm_remove)
        if result.status == "DELETED":
            st.success("Personal overlay entry removed; canonical source data was untouched.")
        else:
            st.warning("Removal requires explicit confirmation.")

section_label("My source-separated board")
rows = []
for asset_id_value, row in assets.items():
    overlay = personal.get(asset_id_value, {})
    rows.append(
        {
            "Asset": row["asset_name"],
            "Asset Type": row["asset_type"],
            "Source": row["source_label"],
            "Source Rank": row["rank_value"],
            "Position": row["position"],
            "Team": row["team"],
            "My Tier": overlay.get("my_tier", ""),
            "My Rank": overlay.get("my_rank", ""),
            "My Tags": ", ".join(overlay.get("tags", [])),
            "Watchlist": bool(overlay.get("watchlist")),
            "Target": bool(overlay.get("target")),
            "Avoid": bool(overlay.get("avoid")),
            "My Conviction": overlay.get("conviction", ""),
            "Notes": "Yes" if overlay.get("notes") else "",
            "Warnings": row["warnings"] or row["blocking_reason"],
        }
    )
frame = pd.DataFrame(rows)
frame["_canonical_order"] = range(len(frame))
filters = st.columns(4)
personal_only = filters[0].checkbox("Personal entries only")
watch_only = filters[1].checkbox("Watchlist only")
target_only = filters[2].checkbox("Target only")
avoid_only = filters[3].checkbox("Avoid only")
if personal_only:
    frame = frame[frame["My Tier"].ne("") | frame["My Rank"].ne("") | frame["Notes"].eq("Yes")]
if watch_only:
    frame = frame[frame["Watchlist"]]
if target_only:
    frame = frame[frame["Target"]]
if avoid_only:
    frame = frame[frame["Avoid"]]
scope_filters = st.columns(4)
source_types = scope_filters[0].multiselect(
    "Source types",
    sorted(frame["Asset Type"].unique()),
    default=sorted(frame["Asset Type"].unique()),
)
positions = scope_filters[1].multiselect(
    "Positions", sorted(frame["Position"].unique()), default=sorted(frame["Position"].unique())
)
teams = scope_filters[2].multiselect(
    "Teams", sorted(frame["Team"].unique()), default=sorted(frame["Team"].unique())
)
evidence = scope_filters[3].selectbox("Evidence state", ("All", "Warnings only", "No warnings"))
frame = frame[
    frame["Asset Type"].isin(source_types)
    & frame["Position"].isin(positions)
    & frame["Team"].isin(teams)
]
if evidence == "Warnings only":
    frame = frame[frame["Warnings"].astype(str).str.strip().ne("")]
elif evidence == "No warnings":
    frame = frame[frame["Warnings"].astype(str).str.strip().eq("")]
order = st.selectbox(
    "Board order",
    ("Canonical order", "My Rank", "My Tier then My Rank"),
)
frame["_my_rank_order"] = pd.to_numeric(frame["My Rank"], errors="coerce").fillna(999999)
if order == "My Rank":
    frame = frame.sort_values(["_my_rank_order", "_canonical_order"], kind="stable")
elif order == "My Tier then My Rank":
    frame = frame.sort_values(["My Tier", "_my_rank_order", "_canonical_order"], kind="stable")
st.dataframe(
    frame.drop(columns=["_canonical_order", "_my_rank_order"]),
    hide_index=True,
    use_container_width=True,
)

with st.expander("Import, export, and local-data location"):
    st.caption(
        "Workspace data remains local under "
        "C:\\NWR_SHARED_DATA\\nwr_personal_workspace_v1 unless you export it."
    )
    st.download_button(
        "Export Personal Board JSON",
        export_personal_board(),
        "nwr-personal-board-v1.json",
        "application/json",
    )
    upload = st.file_uploader("Import Personal Board JSON", type=("json",))
    confirm_import = st.checkbox(
        "I reviewed this import and want to replace the Personal Board store"
    )
    if st.button("Import Personal Board", disabled=upload is None):
        try:
            result = import_personal_board(
                upload.getvalue(), asset_registry=asset_types, confirmed=confirm_import
            )
            if result.status == "IMPORTED":
                st.success("Personal Board imported with a backup of the previous store.")
            else:
                st.warning(result.message)
        except WorkspaceValidationError as exc:
            st.error(f"Import blocked: {exc}")
