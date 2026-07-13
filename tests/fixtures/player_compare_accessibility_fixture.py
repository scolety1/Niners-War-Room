from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.components.decision_trust_strip import render_decision_trust_strips
from app.components.player_compare_accessibility import (
    render_player_compare_accessibility_frame,
    render_selected_player_context,
)
from src.services.decision_trust_strip_service import build_decision_trust_strip

st.set_page_config(page_title="Synthetic Player Compare accessibility fixture", layout="wide")
render_player_compare_accessibility_frame()

scenario = str(st.query_params.get("scenario", "partial")).strip().lower()
st.markdown("## Synthetic Player Compare accessibility fixture")
st.warning(
    "SYNTHETIC TEST FIXTURE — labels and states on this page are not production player facts."
)

if scenario == "partial":
    render_selected_player_context("Synthetic Player A", "")
    st.info(
        "Partial-selection proof: Player A is selected. Player B is explicitly No player selected."
    )
elif scenario == "long":
    render_selected_player_context(
        "Synthetic Long Display Label — Wide Receiver — Identity Review Required — 2026",
        "Synthetic Player B With An Intentionally Long Display Label For Wrapping Review",
    )
    st.markdown("## Synthetic large comparison table")
    st.caption("Synthetic values exercise the existing Streamlit dataframe containment only.")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Player slot": "Player A" if index % 2 == 0 else "Player B",
                    "Synthetic evidence field": f"Long evidence label {index:02d}",
                    "Synthetic state": "Not enough information",
                    "Synthetic caveat": (
                        "Long synthetic caveat text for wrapping and bounded internal scrolling."
                    ),
                    "Synthetic source status": "Review-only synthetic fixture",
                    "Synthetic identity status": "Identity exception — synthetic fixture",
                }
                for index in range(30)
            ]
        ),
        hide_index=True,
        width="stretch",
    )
elif scenario == "states":
    render_selected_player_context("Synthetic Gated Player", "Synthetic Unavailable Player")
    strips = [
        build_decision_trust_strip(
            {
                "source_status": "Gated; not admitted",
                "freshness_status": "YELLOW_STALE",
                "identity_join_status": "identity review required",
                "missing_evidence": "Missing evidence: 2",
                "warnings": "source caveat: partial receipt",
            },
            surface="Player Compare synthetic fixture",
            entity_label="Synthetic Gated Player",
            receipt_label="Synthetic fixture disclosure",
            receipt_available=True,
        ),
        build_decision_trust_strip(
            {
                "source_status": "Unavailable",
                "freshness_status": "Not enough information",
                "identity_join_status": "Not enough information",
                "missing_evidence": "Not enough information",
                "warnings": "Not enough information",
            },
            surface="Player Compare synthetic fixture",
            entity_label="Synthetic Unavailable Player",
            receipt_label="Synthetic fixture disclosure",
            receipt_available=False,
        ),
    ]
    st.markdown("## Synthetic missing and gated evidence states")
    render_decision_trust_strips(strips, heading="Synthetic evidence trust", expanded=True)
else:
    st.error(f"Unknown synthetic fixture scenario: {scenario}")
