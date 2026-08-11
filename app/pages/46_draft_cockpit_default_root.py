from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.owner_data import load_owner_data  # noqa: E402
from app.components.owner_mode import decision_cards, owner_intro  # noqa: E402
from app.components.ui_framework import page_header, section_label  # noqa: E402
from src.services.personal_workspace_service import load_store, summarize_workspace  # noqa: E402

data = load_owner_data(str(REPO_ROOT))
assets = sorted(
    data.evidence.rows,
    key=lambda row: (
        0 if row["asset_type"] == "Current Player" else 1,
        int(float(row.get("dynasty_rank") or 9999)),
        row["asset_name"],
        row["asset_id"],
    ),
)

page_header(
    "Niners War Room",
    eyebrow="Owner Mode",
    description="Start with the football decision. Evidence and operations stay one level deeper.",
    status_items=(("Dynasty · long term", "safe"), ("10-team · 1QB · non-PPR", "safe")),
)
owner_intro(
    "What do you need to decide?",
    "Evaluate a player, compare options, pressure-test a trade, or review the market—"
    "without navigating the model's internals.",
)

section_label("Most common jobs")
decision_cards(
    (
        ("Evaluate a player", "Rank, range, outcomes, market, and NWR reasons in one hub."),
        ("Compare players", "See who NWR prefers in short-, medium-, and long-term windows."),
        ("Analyze a trade", "Use current roster and pick context before making a move."),
        ("Find market gaps", "Build a watchlist from NWR-versus-consensus disagreement."),
    )
)
primary = st.columns(4)
primary[0].link_button("Open Player Detail", "/player-detail", use_container_width=True)
primary[1].link_button("Compare Players", "/player-compare", use_container_width=True)
primary[2].link_button("Analyze Trade", "/trading-lab", use_container_width=True)
primary[3].link_button("Review Market", "/market-analysis", use_container_width=True)

section_label("Quick player search")
asset_id = st.selectbox(
    "Player, rookie, or future pick",
    [row["asset_id"] for row in assets],
    format_func=lambda key: next(
        f"{row['asset_name']} · {row['asset_type']}" for row in assets if row["asset_id"] == key
    ),
)
search_actions = st.columns(3)
search_actions[0].link_button(
    "Open Player Detail",
    f"/player-detail?asset={quote(asset_id, safe='')}",
    use_container_width=True,
)
if asset_id.startswith("current:"):
    search_actions[1].link_button(
        "Why NWR Ranks Them",
        f"/why-nwr-ranks?asset={quote(asset_id, safe='')}",
        use_container_width=True,
    )
search_actions[2].link_button(
    "Browse All Dynasty Assets", "/asset-explorer", use_container_width=True
)

section_label("Your decision workspace")
workspace = summarize_workspace()
summary = st.columns(5)
summary[0].metric("Watchlist", workspace["watchlist"])
summary[1].metric("Targets", workspace["targets"])
summary[2].metric("Avoid", workspace["avoid"])
summary[3].metric("Open decisions", workspace["open_decisions"])
summary[4].metric("Saved scenarios", workspace["saved_scenarios"])
workspace_actions = st.columns(3)
workspace_actions[0].link_button("My Board", "/personal-board", use_container_width=True)
workspace_actions[1].link_button("Decision Tracker", "/decision-journal", use_container_width=True)
workspace_actions[2].link_button(
    "Scenario Playground", "/saved-scenarios", use_container_width=True
)

recent = sorted(
    load_store("decision_journal").records,
    key=lambda row: str(row.get("created_at_utc", "")),
    reverse=True,
)[:3]
if recent:
    st.caption(
        "Recent: "
        + " · ".join(
            f"{row.get('decision_type', 'Decision')} ({row.get('status', 'Unknown')})"
            for row in recent
        )
    )
else:
    st.caption(
        "No decision receipts yet. Save one when you want to remember what you believed and why."
    )

section_label("Rookies and current-season Redraft")
secondary = st.columns(3)
secondary[0].link_button("Review 2026 Rookies", "/rookie-board", use_container_width=True)
secondary[1].link_button("Open Dynasty Rankings", "/rankings", use_container_width=True)
secondary[2].link_button(
    "Open separate Redraft app", "http://127.0.0.1:8512", use_container_width=True
)
st.caption("Redraft is a separate current-season app and never reorders the Dynasty board.")
with st.expander("Advanced / app operations", expanded=False):
    st.write(
        "Start the separate Redraft app with `powershell -File scripts/start_redraft_app.ps1`."
    )
    controls = st.columns(2)
    controls[0].link_button("Data Health", "/settings-data-health", use_container_width=True)
    controls[1].link_button("Refresh Data", "/refresh-data", use_container_width=True)
