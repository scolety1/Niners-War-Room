from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.owner_data import load_owner_data  # noqa: E402
from app.components.owner_mode import owner_intro  # noqa: E402
from app.components.ui_framework import page_header  # noqa: E402
from src.services.owner_mode_view_service import (  # noqa: E402
    market_decision_label,
    owner_availability,
    owner_range_contract,
    owner_risk,
)
from src.services.player_compare_owner_summary_service import (  # noqa: E402
    build_owner_compare_summary,
)
from src.services.player_compare_universe_service import build_player_compare_universe  # noqa: E402

data = load_owner_data(str(REPO_ROOT))
universe = build_player_compare_universe(data.registry, evidence_rows=data.evidence.rows)
frame = universe.frame

page_header(
    "Player Compare",
    eyebrow="Owner Mode - Make the call",
    description="Compare the decision, the range, and the risk before opening dense source data.",
    status_items=(("Source-separated", "safe"), ("Read-only", "safe")),
)
owner_intro(
    "Who does NWR prefer - and for what window?",
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
    column.caption(f"Authority: {lean.authority}")

st.markdown("### Decision matrix")
matrix: list[dict[str, object]] = []
for row in rows:
    market, _gap = market_decision_label(row.get("nwr_rank"), row.get("market_dp_rank"))
    ranges = owner_range_contract(row)
    signals = tuple(row.get("outcome_signals") or ())
    age_window = f"Age {row.get('age')}" if row.get("age") else "Unavailable"
    dimensions = (
        (
            "Authority",
            row.get("compare_authority_status")
            or row.get("compare_source_label")
            or "-",
        ),
        ("NWR rank", row.get("nwr_rank") or "-"),
        ("Position rank", row.get("position_rank") or "-"),
        ("Age / window", age_window),
        ("Injury / availability", owner_availability(row)),
        ("Floor", ranges["Floor"]),
        ("NWR Expected", ranges["NWR Expected"]),
        ("Ceiling", ranges["Ceiling"]),
        ("Market", market),
        ("Market rank", row.get("market_dp_rank") or "-"),
        ("Outcome context", signals[0] if signals else "Not enough information"),
        (
            "Confidence",
            row.get("source_confidence")
            or row.get("research_confidence")
            or "Not enough information",
        ),
        ("Major risk", owner_risk(row)),
    )
    matrix.extend(
        {"Dimension": dimension, "Player": row["player"], "Value": value}
        for dimension, value in dimensions
    )
matrix_frame = pd.DataFrame(matrix).pivot(index="Dimension", columns="Player", values="Value")
st.dataframe(matrix_frame, width="stretch")

st.markdown("### Biggest advantages and risks")
note_columns = st.columns(len(summary.notes))
for column, note in zip(note_columns, summary.notes, strict=True):
    with column.container(border=True):
        st.markdown(f"#### {note['Player']}")
        st.markdown("**Advantages**")
        for item in note["Advantages"]:
            st.markdown(f"- {item}")
        st.markdown("**Risks / uncertainty**")
        for item in note["Risks"]:
            st.markdown(f"- {item}")

with st.expander("How the ranges are built", expanded=False):
    for range_row in summary.ranges:
        st.markdown(f"**{range_row['Player']}** - {range_row['Range authority']}")
        st.caption(range_row["Range method"])

with st.expander("Advanced comparison data", expanded=False):
    st.caption("The complete source-separated comparison remains available in Advanced / Data.")
    st.link_button("Open Compare Data", "/compare-data")
