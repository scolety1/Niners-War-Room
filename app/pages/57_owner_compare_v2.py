from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.owner_data import load_owner_data  # noqa: E402
from app.components.owner_mode import floor_expected_ceiling, owner_intro  # noqa: E402
from app.components.ui_framework import page_header  # noqa: E402
from src.services.owner_mode_view_service import market_decision_label, owner_range  # noqa: E402
from src.services.player_compare_owner_summary_service import (  # noqa: E402
    build_owner_compare_summary,
)
from src.services.player_compare_universe_service import build_player_compare_universe  # noqa: E402

data = load_owner_data(str(REPO_ROOT))
universe = build_player_compare_universe(data.registry, evidence_rows=data.evidence.rows)
frame = universe.frame

page_header(
    "Player Compare",
    eyebrow="Owner Mode · Make the call",
    description="Compare the decision, the range, and the risk before opening dense source data.",
    status_items=(("Source-separated", "safe"), ("Read-only", "safe")),
)
owner_intro(
    "Who does NWR prefer—and for what window?",
    "Short-, medium-, and long-term leans stay separate when their evidence comes "
    "from different authorities.",
)
if universe.errors:
    for error in universe.errors:
        st.warning(error)

options = frame["asset_id"].tolist()
defaults = options[:2]
selected = st.multiselect(
    "Choose two to four players",
    options,
    default=defaults,
    max_selections=4,
    format_func=lambda key: frame.loc[frame["asset_id"].eq(key), "compare_select_label"].iloc[0],
)
if len(selected) < 2:
    st.info("Choose at least two players to compare.")
    st.stop()

rows = frame.loc[frame["asset_id"].isin(selected)].to_dict("records")
summary = build_owner_compare_summary(rows)

st.markdown("### NWR preference by horizon")
lean_columns = st.columns(len(summary.leans))
for column, lean in zip(lean_columns, summary.leans, strict=True):
    column.metric(lean.horizon, lean.preferred)
    column.caption(lean.reason)

st.markdown("### Decision matrix")
matrix: list[dict[str, object]] = []
for row in rows:
    market, gap = market_decision_label(row.get("nwr_rank"), row.get("market_dp_rank"))
    ranges = owner_range(row)
    matrix.append(
        {
            "Player": row["player"],
            "NWR Rank": row.get("nwr_rank") or "—",
            "Pos Rank": row.get("position_rank") or "—",
            "NWR Score": row.get("nwr_dynasty_score") or "—",
            "Expected": ranges["Expected"],
            "Market": market,
            "Gap": gap or "—",
            "Risk": row.get("warning_flags") or row.get("risk_notes") or "No admitted warning",
        }
    )
st.dataframe(pd.DataFrame(matrix), hide_index=True, use_container_width=True)

st.markdown("### Player ranges")
for row in rows:
    with st.container(border=True):
        st.markdown(f"#### {row['player']}")
        floor_expected_ceiling(
            owner_range(row),
            note="Unified Research Preview only; not a new production rank or score.",
        )
        signals = tuple(row.get("outcome_signals") or ())
        if signals:
            st.caption("Outcome evidence: " + " · ".join(signals))

with st.expander("Advanced comparison data", expanded=False):
    st.caption("The complete source-separated comparison remains available in Advanced / Data.")
    st.link_button("Open Compare Data", "/compare-data")
