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

DESKTOP_SECTION_LABELS = (
    "Build the trade",
    "Review candidate packages",
    "Understand roster aftermath",
)

MODE_HELP_TEXT = (
    "Choose the fantasy trade question first, then adjust package constraints. "
    "All results use fake in-memory demo data until real integrations are approved."
)

UNWIRED_INTEGRATION_NOTICE = (
    "Real NWR value, public fantasy market value, roster context, drop pressure, "
    "rookie board, and mock draft integrations are not wired yet."
)

FAKE_DATA_DISCLAIMER = (
    "Desktop smoke build: fake in-memory examples only. Real integrations are "
    "not wired yet."
)

SCORE_LABELS = (
    "NWR Gain",
    "Market Fairness",
    "Opponent Fit",
    "Roster Impact",
    "Keeper/Drop Impact",
    "Risk",
    "Verdict",
)

LEFT_CONTROL_LABELS = (
    "Trade question",
    "Mode",
    "Target player",
    "Outgoing player",
    "Opponent team",
    "Package constraints",
    "Include picks",
    "Allow multi-player packages",
    "Untouchable assets",
    "Preference controls",
    "Max offer aggressiveness",
    "Risk preference",
    "Win-now vs long-term preference",
)

CENTER_SECTION_LABELS = (
    "Review board",
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

RESULT_CARD_LABELS = (
    "Package summary",
    "NWR value gain",
    "Public fantasy market fairness",
    "Opponent fit",
    "Roster impact",
    "Risk flags",
    "Manual review verdict",
)

NEGOTIATION_LADDER_LABELS = (
    "Opening offer",
    "Fair offer",
    "Max offer",
    "Walk-away line",
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
        TradeLabSection(
    "Header",
            (
                TRADE_LAB_TITLE,
                TRADE_LAB_SUBTITLE,
                *TRADE_LAB_DATA_CHIPS,
                FAKE_DATA_DISCLAIMER,
                UNWIRED_INTEGRATION_NOTICE,
            ),
        ),
        TradeLabSection("Desktop layout", DESKTOP_SECTION_LABELS),
        TradeLabSection("Left control panel", LEFT_CONTROL_LABELS),
        TradeLabSection(
            "Center results",
            (*CENTER_SECTION_LABELS, *RESULT_CARD_LABELS, *SCORE_LABELS),
        ),
        TradeLabSection("Right context panel", RIGHT_CONTEXT_LABELS),
        TradeLabSection("Negotiation ladder", NEGOTIATION_LADDER_LABELS),
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
    st.subheader(TRADE_LAB_SUBTITLE)
    st.caption("Fantasy trade package simulator - desktop review build")
    st.write(" ".join(f"`{chip}`" for chip in TRADE_LAB_DATA_CHIPS))
    st.warning(FAKE_DATA_DISCLAIMER)
    st.info(UNWIRED_INTEGRATION_NOTICE)

    left, center, right = st.columns((0.9, 1.7, 1.1), gap="large")
    packages = demo_trade_packages()
    best = best_trade_package(packages)

    with left:
        st.subheader("Build the trade")
        st.caption(MODE_HELP_TEXT)
        st.markdown("**Trade question**")
        st.selectbox("Mode", TRADE_LAB_MODES, index=0, help=MODE_HELP_TEXT)
        st.text_input("Target player", value="Target Player")
        st.text_input("Outgoing player", value="Player A")
        st.selectbox("Opponent team", ("Team Alpha", "Team Bravo"), index=0)
        st.markdown("**Package constraints**")
        st.checkbox("Include picks", value=True)
        st.checkbox("Allow multi-player packages", value=True)
        st.text_area("Untouchable assets", value="Player C")
        st.markdown("**Preference controls**")
        st.slider("Max offer aggressiveness", 1, 10, 6)
        st.select_slider("Risk preference", options=("Low", "Balanced", "High"), value="Balanced")
        st.select_slider(
            "Win-now vs long-term preference",
            options=("Win-now", "Balanced", "Long-term"),
            value="Balanced",
        )

    with center:
        st.subheader("Review board")
        st.caption("Ranked by fake NWR gain, market realism, opponent fit, and roster effect.")
        st.markdown("### Best trade")
        with st.container(border=True):
            st.markdown(f"**Package summary:** {format_package_summary(best)}")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("NWR Gain", f"+{best.nwr_gain:.1f}")
            col_b.metric("Market Fairness", "Realistic")
            col_c.metric("Opponent Fit", "Strong")
            st.write(f"Roster Impact: {best.roster_impact}")
            st.write(f"Keeper/Drop Impact: {best.keeper_drop_impact}")
            st.write(f"Risk: {', '.join(best.risk_flags)}")
            st.write(f"Verdict: {best.verdict}")

        st.subheader("Ranked packages")
        for rank, package in enumerate(
            sorted(packages, key=lambda item: item.nwr_gain, reverse=True),
            start=1,
        ):
            with st.container(border=True):
                st.markdown(f"**#{rank}: {format_package_summary(package)}**")
                st.write(f"Market Fairness: {package.public_market_fairness}")
                st.write(f"Opponent Fit: {package.opponent_fit}")
                st.write(f"Roster Impact: {package.roster_impact}")
                st.write(f"Keeper/Drop Impact: {package.keeper_drop_impact}")
                st.write(f"Risk: {', '.join(package.risk_flags)}")
                st.write(f"Verdict: {package.verdict}")

        st.subheader("Negotiation ladder")
        st.markdown(f"- **Opening offer:** {best.negotiation_ladder.opening_offer}")
        st.markdown(f"- **Fair offer:** {best.negotiation_ladder.fair_offer}")
        st.markdown(f"- **Max offer:** {best.negotiation_ladder.max_offer}")
        st.markdown(f"- **Walk-away line:** {best.negotiation_ladder.walk_away}")

        st.subheader("Bad trade warnings")
        st.caption("Warnings flag packages that need manual review before making an offer.")
        for warning in bad_trade_warnings(best):
            st.warning(warning)

    with right:
        st.subheader("Understand roster aftermath")
        aftermath = best.roster_aftermath
        st.markdown("**Roster aftermath**")
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
