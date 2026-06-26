from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.nfl_usage_evidence_review_page_service import (
    export_csv,
    load_nfl_usage_evidence_review_data,
    table_columns,
)


def _metric_grid(summary: dict[str, object]) -> None:
    cards = [
        ("Sources inventoried", summary["sources_inventoried"]),
        ("Sources GREEN", summary["sources_green"]),
        ("Quarantined/skipped", summary["sources_quarantined_or_skipped"]),
        ("True factual fields", summary["true_factual_fields"]),
        ("Derived proxy fields", summary["derived_proxy_fields"]),
        ("Licensed gaps", summary["licensed_data_gaps"]),
        ("Field quarantines", summary["field_quarantines"]),
        ("Validation GREEN", summary["validation_green"]),
        ("App wiring allowed", summary["app_wiring_allowed"]),
        ("Model input allowed", summary["model_input_allowed"]),
        ("Display approved", summary["promotion_display_approved"]),
        ("Research-only", summary["promotion_research_only"]),
        ("Blocked/gaps", summary["promotion_blocked"]),
    ]
    columns = st.columns(5)
    for index, (label, value) in enumerate(cards):
        with columns[index % 5]:
            st.metric(label, value)


data = load_nfl_usage_evidence_review_data()

page_header(
    "NFL Usage Evidence Review",
    eyebrow="Review-only Artifact",
    description=(
        "Inspect live nflreadpy field inventories, source coverage, proxy labels, "
        "and validation/quarantine status without approving model or app use."
    ),
    status_items=(
        ("Review-only", "review"),
        ("Not model input", "safe"),
        ("No decision wiring", "blocked"),
    ),
)

st.warning(
    "Review-only. This page does not feed rankings, Drafting Mode, Player Compare, "
    "Trading Lab, Post-Draft, or model features."
)
st.caption(
    "This page reads only committed summary artifacts. It does not load raw "
    "play-by-play, snap counts, NGS, FTN, PFR, participation, or shared-cache payloads."
)

_metric_grid(data.summary)

tabs = st.tabs(
    [
        "Sources",
        "Field Coverage",
        "Proxy vs True",
        "Gaps",
        "Validation",
        "Promotion Gate",
    ]
)

with tabs[0]:
    source_table = table_columns(
        data.smoke,
        [
            "source_family",
            "loader_name",
            "status",
            "season_sampled",
            "row_count",
            "column_count",
            "raw_committed",
            "notes",
        ],
    )
    st.dataframe(source_table, use_container_width=True, hide_index=True)
    st.download_button(
        "Download source status CSV",
        data=export_csv(source_table),
        file_name="nfl_usage_source_status.csv",
        mime="text/csv",
    )

with tabs[1]:
    field_table = table_columns(
        data.field_inventory,
        [
            "source_family",
            "field_name",
            "dtype_observed",
            "allowlist_status",
            "blocklist_status",
            "field_type",
            "grain",
            "model_input_allowed",
            "app_wiring_allowed",
            "caveats",
        ],
    )
    st.dataframe(field_table, use_container_width=True, hide_index=True)

with tabs[2]:
    st.dataframe(data.proxy_true, use_container_width=True, hide_index=True)

with tabs[3]:
    st.dataframe(data.field_gaps, use_container_width=True, hide_index=True)

with tabs[4]:
    st.markdown("#### Validation")
    st.dataframe(data.validation, use_container_width=True, hide_index=True)
    st.markdown("#### Quarantine")
    st.dataframe(data.quarantine, use_container_width=True, hide_index=True)

with tabs[5]:
    st.warning(
        "Review-only. Promotion status shown here does not feed rankings, Drafting Mode, "
        "Player Compare, Trading Lab, Post-Draft, Cheat Sheets, hidden sorts, or model features."
    )
    st.metric("Predictive backtest status", data.summary["promotion_backtest_status"])

    st.markdown("#### Promotion Decision Matrix")
    decision_table = table_columns(
        data.promotion_decision_matrix,
        [
            "field_name",
            "source_family",
            "field_type",
            "coverage_status",
            "backtest_status",
            "display_context_status",
            "final_promotion_status",
            "approved_for_display_only",
            "approved_for_model_candidate",
            "model_input_allowed",
            "app_wiring_allowed",
            "required_next_gate",
            "caveats",
        ],
    )
    st.dataframe(decision_table, use_container_width=True, hide_index=True)

    st.markdown("#### Display-Only Approved")
    display_approved = (
        decision_table["approved_for_display_only"].astype(str).str.lower() == "yes"
    )
    st.dataframe(
        decision_table[display_approved],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Research-Only")
    st.dataframe(
        decision_table[decision_table["final_promotion_status"].astype(str) == "RESEARCH_ONLY"],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Blocked / Licensed Gaps")
    st.dataframe(
        decision_table[
            decision_table["final_promotion_status"].astype(str).str.startswith("BLOCKED")
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Backtest And Diagnostics")
    st.dataframe(data.promotion_backtest_results, use_container_width=True, hide_index=True)
    st.dataframe(data.promotion_coverage_diagnostics, use_container_width=True, hide_index=True)
    st.dataframe(data.promotion_display_sanity, use_container_width=True, hide_index=True)

    st.markdown("#### V0 Legacy Promotion Candidates")
    st.dataframe(data.promotion_candidates, use_container_width=True, hide_index=True)
