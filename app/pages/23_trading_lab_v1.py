from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_source_of_truth_badge,
    render_yellow_hold,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import load_frozen_board, load_lane_prop_frame

bundle = load_frozen_board()

page_header(
    "Trading Lab",
    eyebrow="Draft-Day App V1",
    description=(
        "Package compare shell using frozen ranks, tiers, and visible board scores as "
        "base context. No trade simulation or final trade advice is run here."
    ),
    status_items=(("Decision support only", "review"), ("No simulations", "safe")),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

prop_frame, prop_path = load_lane_prop_frame("trading_lab")
if prop_path is None:
    render_yellow_hold("Trading Lab props are missing; package compare is board-context only.")
else:
    st.caption(f"Trading Lab props loaded: {prop_path}")

players = bundle.frame["player"].astype(str).tolist() if "player" in bundle.frame.columns else []
cols = st.columns(2)
give = cols[0].multiselect("Give side", players, key="trade_give_side")
get = cols[1].multiselect("Get side", players, key="trade_get_side")

def _package_rows(names: list[str]) -> pd.DataFrame:
    return bundle.frame.loc[bundle.frame["player"].astype(str).isin(names)].copy()


def _package_summary(names: list[str]) -> dict[str, object]:
    rows = _package_rows(names)
    score = pd.to_numeric(rows.get("final_board_score_visible", 0), errors="coerce").fillna(0)
    return {
        "players": ", ".join(names) if names else "none",
        "count": len(names),
        "best_rank": int(rows["final_board_rank"].min()) if len(rows) else "",
        "visible_score_sum": round(float(score.sum()), 2),
        "tiers": ", ".join(sorted(set(rows.get("final_tier", pd.Series(dtype=str)).astype(str)))),
    }


st.subheader("Package Context")
st.dataframe(
    pd.DataFrame(
        [
            {"side": "give", **_package_summary(give)},
            {"side": "get", **_package_summary(get)},
        ]
    ),
    use_container_width=True,
    hide_index=True,
)
st.caption(
    "Visible score sums are context only. They are not a trade simulator, private value, "
    "or final trade advice."
)
