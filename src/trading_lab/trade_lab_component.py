from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.trade_lab_ui import (
    TRADE_LAB_DATA_CHIPS,
    TRADE_LAB_MODES,
    TRADE_LAB_SUBTITLE,
    TRADE_LAB_TITLE,
    bad_trade_warnings,
    best_trade_package,
    demo_trade_packages,
    format_package_summary,
)

ROUTE_WIRING_STATUS = "isolated_streamlit_page"

LEFT_CONTROL_LABELS = (
    "Mode",
    "Target player",
    "Outgoing player",
    "Opponent team",
    "Include picks",
    "Allow multi-player packages",
    "Untouchable assets",
    "Max offer aggressiveness",
    "Risk preference",
    "Win-now vs long-term preference",
)

CENTER_SECTION_LABELS = (
    "Best trade",
    "Ranked packages",
    "Negotiation ladder",
    "Bad trade warnings",
    "Trade review cards",
)

RIGHT_CONTEXT_LABELS = (
    "Roster aftermath",
    "Keeper impact",
    "Drop pressure impact",
    "Positional depth impact",
    "Rookie/mock draft context",
    "Opponent fit",
    "Data status / needs data",
)

TRAINING_MODE_LABELS = (
    "Training Mode",
    "Practice scenario",
    "NWR value",
    "Market realism",
    "Opponent fit",
    "Roster impact",
    "Negotiation quality",
)


@dataclass(frozen=True)
class TradeLabSection:
    name: str
    labels: tuple[str, ...]


def trade_lab_sections() -> tuple[TradeLabSection, ...]:
    return (
        TradeLabSection("Header", (TRADE_LAB_TITLE, TRADE_LAB_SUBTITLE, *TRADE_LAB_DATA_CHIPS)),
        TradeLabSection("Left control panel", LEFT_CONTROL_LABELS),
        TradeLabSection("Center results", CENTER_SECTION_LABELS),
        TradeLabSection("Right context panel", RIGHT_CONTEXT_LABELS),
        TradeLabSection("Training Mode", TRAINING_MODE_LABELS),
    )


def trade_lab_label_text() -> str:
    return " ".join(
        label
        for section in trade_lab_sections()
        for label in (section.name, *section.labels)
    )


def render_trade_lab_page() -> None:
    import streamlit as st

    st.set_page_config(page_title=TRADE_LAB_TITLE, layout="wide")
    st.title(TRADE_LAB_TITLE)
    st.caption(TRADE_LAB_SUBTITLE)
    st.write(" ".join(f"`{chip}`" for chip in TRADE_LAB_DATA_CHIPS))

    left, center, right = st.columns((0.9, 1.7, 1.1), gap="large")
    packages = demo_trade_packages()
    best = best_trade_package(packages)

    with left:
        st.subheader("Controls")
        st.selectbox("Mode", TRADE_LAB_MODES, index=0)
        st.text_input("Target player", value="Target Player")
        st.text_input("Outgoing player", value="Player A")
        st.selectbox("Opponent team", ("Team Alpha", "Team Bravo"), index=0)
        st.checkbox("Include picks", value=True)
        st.checkbox("Allow multi-player packages", value=True)
        st.text_area("Untouchable assets", value="Player C")
        st.slider("Max offer aggressiveness", 1, 10, 6)
        st.select_slider("Risk preference", options=("Low", "Balanced", "High"), value="Balanced")
        st.select_slider(
            "Win-now vs long-term preference",
            options=("Win-now", "Balanced", "Long-term"),
            value="Balanced",
        )

    with center:
        st.subheader("Best trade")
        st.metric("NWR value gain", f"+{best.nwr_gain:.1f}")
        st.write(format_package_summary(best))
        st.write(best.public_market_fairness)
        st.write(best.verdict)

        st.subheader("Ranked packages")
        for package in sorted(packages, key=lambda item: item.nwr_gain, reverse=True):
            with st.container(border=True):
                st.markdown(f"**{format_package_summary(package)}**")
                st.write(package.opponent_fit)
                st.write(package.roster_impact)

        st.subheader("Negotiation ladder")
        st.write(f"Opening offer: {best.negotiation_ladder.opening_offer}")
        st.write(f"Fair offer: {best.negotiation_ladder.fair_offer}")
        st.write(f"Max offer: {best.negotiation_ladder.max_offer}")
        st.write(f"Walk-away line: {best.negotiation_ladder.walk_away}")

        st.subheader("Bad trade warnings")
        for warning in bad_trade_warnings(best):
            st.warning(warning)

    with right:
        st.subheader("Roster aftermath")
        aftermath = best.roster_aftermath
        st.write(aftermath.summary)
        st.write(f"Keeper impact: {aftermath.keeper_impact}")
        st.write(f"Drop pressure impact: {aftermath.drop_pressure_impact}")
        st.write(f"Positional depth impact: {aftermath.positional_depth_impact}")
        st.write(f"Rookie/mock draft context: {aftermath.rookie_mock_context}")
        st.write(f"Opponent fit: {best.opponent_fit}")
        st.info("Data status / needs data: using fake in-memory placeholders.")

    st.divider()
    st.subheader("Training Mode")
    st.write("Practice scenario placeholder")
    st.write(
        "Scoring dimensions: NWR value, market realism, opponent fit, "
        "roster impact, negotiation quality."
    )
