from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from app.components.demo_source_labels import demo_source_label
from app.components.human_labels import human_labels

MISSING_LABEL = "Missing"


@dataclass(frozen=True)
class PlayerDetail:
    player: str
    age: object = ""
    position: object = ""
    nfl_team: object = ""
    college: object = ""
    owner: object = ""
    model_value: object = ""
    rank_or_slot: object = ""
    rookie_pick_equivalent: object = ""
    trust_status: object = ""
    why_this_rank: object = ""
    strongest_signals: object = ""
    weakest_signals: object = ""
    warning_groups: object = ""
    nearby_context: object = ""
    market_context: object = ""
    receipt_pointer: object = ""
    source_pointer: object = ""


def display_value(value: object, *, missing: str = MISSING_LABEL) -> str:
    if value is None:
        return missing
    if isinstance(value, float) and pd.isna(value):
        return missing
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return missing
    return text


def detail_summary(detail: PlayerDetail) -> dict[str, str]:
    return {
        "Player": display_value(detail.player),
        "Age": display_value(detail.age, missing="Age missing"),
        "Position": display_value(detail.position),
        "NFL Team / College": _team_or_college(detail),
        "Owner": display_value(detail.owner),
        "Model Value": display_value(detail.model_value),
        "Rank / Internal Slot": display_value(detail.rank_or_slot),
        "Rookie Pick Equivalent": display_value(detail.rookie_pick_equivalent),
        "Trust": display_value(detail.trust_status, missing="Trust unknown"),
        "Warnings": warning_summary(detail.warning_groups),
    }


def warning_summary(value: object) -> str:
    text = display_value(value, missing="")
    if not text:
        return "No major warning"
    return human_labels(text)


def render_player_detail_panel(
    detail: PlayerDetail,
    *,
    label: str | None = None,
    key: str | None = None,
    expanded: bool = False,
) -> None:
    _ = key
    expander_label = label or f"Inspect {display_value(detail.player, missing='player')}"
    with st.expander(expander_label, expanded=expanded):
        summary = detail_summary(detail)
        top_cols = st.columns(4)
        top_cols[0].metric("Player", summary["Player"])
        top_cols[1].metric("Age", summary["Age"])
        top_cols[2].metric("Model Value", summary["Model Value"])
        top_cols[3].metric("Rank / Slot", summary["Rank / Internal Slot"])

        basics = st.columns(4)
        basics[0].caption(f"Position: {summary['Position']}")
        basics[1].caption(f"Team/College: {summary['NFL Team / College']}")
        basics[2].caption(f"Owner: {summary['Owner']}")
        basics[3].caption(f"Rookie pick equivalent: {summary['Rookie Pick Equivalent']}")

        st.markdown("**Model evidence**")
        st.write(
            display_value(
                detail.why_this_rank,
                missing="Why-this-rank text is missing for this row.",
            )
        )
        signal_cols = st.columns(2)
        signal_cols[0].write(
            f"**Strongest signals:** {display_value(detail.strongest_signals)}"
        )
        signal_cols[1].write(
            f"**Weakest signals:** {display_value(detail.weakest_signals)}"
        )
        st.write(f"**Trust / evidence risk:** {summary['Trust']}")
        st.write(f"**Warnings:** {summary['Warnings']}")

        if display_value(detail.nearby_context, missing=""):
            st.write(f"**Nearby players / picks:** {display_value(detail.nearby_context)}")

        if display_value(detail.market_context, missing=""):
            st.markdown("**Market context (display-only, not model value)**")
            st.write(display_value(detail.market_context))

        st.markdown("**Receipts / source pointers**")
        st.caption(
            f"Receipt pointer: {display_value(detail.receipt_pointer)} | "
            f"Source pointer: {demo_source_label(detail.source_pointer)}"
        )
        st.caption(
            "Review-only detail. This panel explains evidence and context; it "
            "does not make a final cut, trade, or draft recommendation."
        )

def _team_or_college(detail: PlayerDetail) -> str:
    nfl_team = display_value(detail.nfl_team, missing="")
    college = display_value(detail.college, missing="")
    if nfl_team and college:
        return f"{nfl_team} / {college}"
    return nfl_team or college or MISSING_LABEL
