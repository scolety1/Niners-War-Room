from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.ui_framework import (  # noqa: E402
    WorkflowTile,
    page_header,
    render_workflow_tiles,
    section_label,
)
from src.services.draft_day_app_v1_service import resolve_dynasty_rankings_path  # noqa: E402
from src.services.governed_asset_registry_service import load_governed_asset_registry  # noqa: E402
from src.services.personal_workspace_service import (  # noqa: E402
    load_store,
    summarize_workspace,
    workspace_root,
)

page_header(
    "Niners War Room",
    eyebrow="Start Here",
    description=(
        "Choose the decision surface that matches the job in front of you. "
        "The accepted dynasty board stays read-only; draft actions remain explicit and local."
    ),
    status_items=(
        ("10-team · 1QB · non-PPR", "safe"),
        ("First-down scoring", "safe"),
        ("Private local runtime", "safe"),
    ),
)

section_label("Choose a workflow")
render_workflow_tiles(
    (
        WorkflowTile(
            "Dynasty Rankings",
            "Canonical board",
            "Scan all 232 production-ranked QB/RB/WR/TE players, tiers, and evidence warnings.",
            "/rankings",
            "Open Rankings",
        ),
        WorkflowTile(
            "Player Compare",
            "Read-only",
            "Compare specific players without changing rankings or draft state.",
            "/player-compare",
            "Compare Players",
        ),
        WorkflowTile(
            "Trading Lab",
            "Manual decision aid",
            "Review player and pick value context; no trade is submitted automatically.",
            "/trading-lab",
            "Open Trading Lab",
        ),
        WorkflowTile(
            "Draft Cockpit",
            "Live local state",
            "Use explicit controls for a real draft session. Mock Drafts stay separate.",
            "/draft-cockpit",
            "Open Draft Cockpit",
        ),
    )
)

section_label("Search")
_current_path, _source_label, _warnings = resolve_dynasty_rankings_path()
_registry = load_governed_asset_registry(
    repo_root=Path(__file__).resolve().parents[2],
    current_board_path=_current_path,
)
_assets = sorted(_registry.rows, key=lambda row: (row["asset_name"], row["asset_id"]))
_asset_id = st.selectbox(
    "Find a veteran, rookie, blocked prospect, or future pick",
    [row["asset_id"] for row in _assets],
    format_func=lambda key: next(
        f"{row['asset_name']} · {row['asset_type']} · {row['authority_status']}"
        for row in _assets
        if row["asset_id"] == key
    ),
)
st.markdown(f"[Open Player Detail](/player-detail?asset={quote(_asset_id, safe='')})")

st.info(
    "Recommended first visit: confirm Data Health, then open Dynasty Rankings. "
    "Enter Draft Cockpit only when you intend to manage live local draft state."
)

section_label("Know what can change")
read_only, stateful = st.columns(2)
with read_only:
    st.markdown("**Read-only decision surfaces**")
    st.write(
        "Rankings, Player Compare, and Trading Lab present accepted local evidence. "
        "Opening them does not change the canonical board."
    )
with stateful:
    st.markdown("**Explicit or gated actions**")
    st.write(
        "Draft Cockpit changes local session state only through its controls. "
        "Refresh and recovery actions remain in Admin with confirmation and status details."
    )

health, workflow = st.columns(2)
health.link_button(
    "Check Data Health",
    "/settings-data-health",
    use_container_width=True,
)
workflow.link_button(
    "Open the Review Workflow",
    "/review-workflow",
    use_container_width=True,
)

catalog, rookies = st.columns(2)
catalog.link_button("Search Asset Explorer", "/asset-explorer", use_container_width=True)
rookies.link_button("Open 2026 Rookie Board", "/rookie-board", use_container_width=True)

section_label("My workspace")
workspace = summarize_workspace()
summary_columns = st.columns(4)
summary_columns[0].metric("Watchlist", workspace["watchlist"])
summary_columns[1].metric("Targets", workspace["targets"])
summary_columns[2].metric("Open decisions", workspace["open_decisions"])
summary_columns[3].metric("Saved scenarios", workspace["saved_scenarios"])
secondary_summary = st.columns(3)
secondary_summary[0].metric("Avoid / DND", workspace["avoid"])
secondary_summary[1].metric("Follow-ups due", workspace["followups_due"])
backup_root = workspace_root() / "backups"
latest_backups = (
    sorted(backup_root.glob("workspace-*"), reverse=True) if backup_root.exists() else []
)
secondary_summary[2].metric("Workspace backups", len(latest_backups))
recent_decisions = sorted(
    load_store("decision_journal").records,
    key=lambda row: str(row.get("created_at_utc", "")),
    reverse=True,
)[:3]
if recent_decisions:
    st.caption(
        "Recent decisions: "
        + " · ".join(
            f"{row.get('decision_type', 'decision')} ({row.get('status', 'Unknown')})"
            for row in recent_decisions
        )
    )
else:
    st.caption("No decision receipts yet. Create one when you want a prospective record.")
st.caption(
    f"Backup status: {'available' if latest_backups else 'none yet'} · "
    f"Local workspace: {workspace_root()}"
)
personal_board, journal, scenarios = st.columns(3)
personal_board.link_button("Open Personal Board", "/personal-board", use_container_width=True)
journal.link_button("Open Decision Journal", "/decision-journal", use_container_width=True)
scenarios.link_button("Open Saved Scenarios", "/saved-scenarios", use_container_width=True)
