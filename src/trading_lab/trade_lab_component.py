from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.trade_comparison import PACKAGE_BOARD_LABELS
from src.trading_lab.trade_lab_adapters import disabled_provider_status_labels
from src.trading_lab.trade_lab_ui import (
    TRADE_LAB_DATA_CHIPS,
    TRADE_LAB_FIRST_SCREEN_HELP_TEXT,
    TRADE_LAB_MODES,
    TRADE_LAB_REVIEW_QUESTIONS,
    TRADE_LAB_SUBTITLE,
    TRADE_LAB_TITLE,
    TRAINING_MODE_DISCLAIMER,
    TRAINING_SCORING_DIMENSIONS,
    WARNING_LABELS,
    WARNING_SEVERITIES,
    bad_trade_warning_details,
    bad_trade_warnings,
    best_trade_package,
    format_negotiation_ladder,
    format_package_summary,
    mode_context_for,
    mode_guidance_lines,
    packages_for_mode,
    sort_packages_by_review_score,
    training_scenarios,
)
from src.trading_lab.trade_negotiation import NEGOTIATION_POLISH_LABELS, NEGOTIATION_REVIEW_NOTE
from src.trading_lab.trade_provenance import ui_data_status_labels
from src.trading_lab.trade_review_queue import review_queue_placeholder_labels
from src.trading_lab.trade_scenarios import scenario_titles

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

PLACEHOLDER_INTEGRATION_BOUNDARY_LABELS = (
    "NWR private value integration: placeholder only; not wired; needs approval.",
    "Public fantasy market value integration: placeholder only; not wired; needs approval.",
    "Roster context integration: placeholder only; not wired; needs approval.",
    "Drop pressure integration: placeholder only; not wired; needs approval.",
    "Rookie board integration: placeholder only; not wired; needs approval.",
    "Mock draft integration: placeholder only; not wired; needs approval.",
    "No generated outputs.",
    "No automated trade submission or automatic decisioning.",
)

PROVENANCE_STATUS_LABELS = ui_data_status_labels()
REVIEW_QUEUE_PLACEHOLDER_LABELS = review_queue_placeholder_labels()
DISABLED_PROVIDER_STATUS_LABELS = disabled_provider_status_labels()
SCENARIO_COVERAGE_LABELS = scenario_titles()

FAKE_DATA_DISCLAIMER = (
    "Fixture-only review build: fake in-memory examples only, using fake players, "
    "picks, teams, and values. Real integrations are not wired yet."
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
    "Keeper core before",
    "Keeper core after",
    "Drop pressure impact",
    "Drop pressure before",
    "Drop pressure after",
    "Positional depth impact",
    "Positional depth before",
    "Positional depth after",
    "Rookie/mock draft context",
    "Mock draft context placeholder",
    "Roster risk notes",
    "Opponent fit",
    "Data status / needs data",
)

RESULT_CARD_LABELS = (
    "Package summary",
    "Give",
    "Get",
    "NWR value gain",
    "Public fantasy market fairness",
    "Opponent fit",
    "Roster impact",
    "Risk flags",
    "Manual review verdict",
    "Fixture-only caveat",
)

BEST_TRADE_CARD_LABELS = RESULT_CARD_LABELS

NEGOTIATION_LADDER_LABELS = (
    "Opening offer",
    "Fair offer",
    "Max offer",
    "Walk-away line",
    "Do-not-include assets",
    "Counteroffer ideas",
    "If they reject",
    "If they ask for more",
)

TRAINING_MODE_LABELS = (
    "Training Mode",
    "Practice scenario",
    *TRAINING_SCORING_DIMENSIONS,
    "Negotiation quality",
    TRAINING_MODE_DISCLAIMER,
)

WARNING_SYSTEM_LABELS = (*WARNING_LABELS, *WARNING_SEVERITIES)


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
                TRADE_LAB_FIRST_SCREEN_HELP_TEXT,
                *TRADE_LAB_REVIEW_QUESTIONS,
                *TRADE_LAB_DATA_CHIPS,
                FAKE_DATA_DISCLAIMER,
                UNWIRED_INTEGRATION_NOTICE,
                *PROVENANCE_STATUS_LABELS,
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
        TradeLabSection("Negotiation guidance polish", NEGOTIATION_POLISH_LABELS),
        TradeLabSection("Bad trade detector", WARNING_SYSTEM_LABELS),
        TradeLabSection("Training Mode", TRAINING_MODE_LABELS),
        TradeLabSection(
            "Placeholder integration boundaries",
            PLACEHOLDER_INTEGRATION_BOUNDARY_LABELS,
        ),
        TradeLabSection("Review queue placeholder", REVIEW_QUEUE_PLACEHOLDER_LABELS),
        TradeLabSection("Disabled provider states", DISABLED_PROVIDER_STATUS_LABELS),
        TradeLabSection("Scenario coverage", SCENARIO_COVERAGE_LABELS),
        TradeLabSection("Package board polish", PACKAGE_BOARD_LABELS),
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
    st.caption(TRADE_LAB_FIRST_SCREEN_HELP_TEXT)
    st.markdown("**What this page answers**")
    for question in TRADE_LAB_REVIEW_QUESTIONS:
        st.write(f"- {question}")
    st.caption("Manual review required. Fixture-only values are for desktop review.")
    st.write(" ".join(f"`{chip}`" for chip in TRADE_LAB_DATA_CHIPS))
    st.warning(FAKE_DATA_DISCLAIMER)
    st.info(UNWIRED_INTEGRATION_NOTICE)
    st.write(" ".join(f"`{label}`" for label in PROVENANCE_STATUS_LABELS))
    with st.expander("Placeholder integration boundaries", expanded=False):
        for boundary in PLACEHOLDER_INTEGRATION_BOUNDARY_LABELS:
            st.write(f"- {boundary}")
    with st.expander("Review queue placeholder", expanded=False):
        for label in REVIEW_QUEUE_PLACEHOLDER_LABELS:
            st.write(f"- {label}")

    left, center, right = st.columns((0.9, 1.7, 1.1), gap="large")
    with left:
        st.subheader("Build the trade")
        st.caption(MODE_HELP_TEXT)
        st.markdown("**Trade question**")
        selected_mode = st.selectbox("Mode", TRADE_LAB_MODES, index=0, help=MODE_HELP_TEXT)
        mode_context = mode_context_for(selected_mode)
        st.info(mode_context.user_question)
        st.caption(mode_context.explanation)
        for guidance_line in mode_guidance_lines(selected_mode):
            st.caption(guidance_line)
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
        st.markdown("**Mode-specific controls**")
        for control in mode_context.relevant_controls:
            st.write(f"- {control}")

    packages = packages_for_mode(selected_mode)
    best = best_trade_package(packages)

    with center:
        st.subheader("Review board")
        st.caption("Ranked by fake NWR gain, market realism, opponent fit, and roster effect.")
        st.markdown("### Best trade")
        with st.container(border=True):
            st.markdown(f"**Package summary:** {format_package_summary(best)}")
            st.write(f"**Give:** {' + '.join(best.give)}")
            st.write(f"**Get:** {' + '.join(best.get)}")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("NWR Gain", f"+{best.nwr_gain:.1f}")
            col_b.metric("Market Fairness", best.public_market_fairness)
            col_c.metric("Opponent Fit", best.opponent_fit)
            st.write(f"Roster Impact: {best.roster_impact}")
            st.write(f"Keeper/Drop Impact: {best.keeper_drop_impact}")
            st.write(f"Risk: {', '.join(best.risk_flags)}")
            st.write(f"Verdict: {best.verdict}")
            st.caption(best.explanation_summary)
            st.caption(" | ".join(best.trust_labels[:3]))
            st.caption("Fixture-only caveat: values are for manual desktop review.")

        st.subheader("Ranked packages")
        for rank, package in enumerate(sort_packages_by_review_score(packages), start=1):
            with st.container(border=True):
                st.markdown(f"**#{rank}: {format_package_summary(package)}**")
                st.write(f"Market Fairness: {package.public_market_fairness}")
                st.write(f"Opponent Fit: {package.opponent_fit}")
                st.write(f"Roster Impact: {package.roster_impact}")
                st.write(f"Keeper/Drop Impact: {package.keeper_drop_impact}")
                st.write(f"Risk: {', '.join(package.risk_flags)}")
                st.write(f"Verdict: {package.verdict}")
                st.caption(package.explanation_summary)
                st.caption(" | ".join(package.trust_labels[:3]))

        st.subheader("Negotiation ladder")
        st.caption(NEGOTIATION_REVIEW_NOTE)
        for ladder_line in format_negotiation_ladder(best.negotiation_ladder):
            label, value = ladder_line.split(": ", 1)
            st.markdown(f"- **{label}:** {value}")

        st.subheader("Bad trade warnings")
        st.caption("Warnings flag packages that need manual review before making an offer.")
        for warning in mode_context.warning_examples:
            st.warning(warning)
        for warning in bad_trade_warning_details(best):
            st.warning(f"[{warning.severity}] {warning.label}: {warning.message}")
        for warning in bad_trade_warnings(best):
            if warning not in {detail.message for detail in bad_trade_warning_details(best)}:
                st.warning(warning)

    with right:
        st.subheader("Understand roster aftermath")
        aftermath = best.roster_aftermath
        st.markdown("**Roster aftermath**")
        st.write(aftermath.summary)
        st.write(f"Keeper impact: {aftermath.keeper_impact}")
        st.write(f"Keeper core before: {', '.join(aftermath.keeper_core_before)}")
        st.write(f"Keeper core after: {', '.join(aftermath.keeper_core_after)}")
        st.write(f"Drop pressure impact: {aftermath.drop_pressure_impact}")
        st.write(f"Drop pressure before: {aftermath.drop_pressure_before}")
        st.write(f"Drop pressure after: {aftermath.drop_pressure_after}")
        st.write(f"Positional depth impact: {aftermath.positional_depth_impact}")
        st.write(f"Positional depth before: {aftermath.positional_depth_before}")
        st.write(f"Positional depth after: {aftermath.positional_depth_after}")
        st.write(f"Rookie/mock draft context: {aftermath.rookie_mock_context}")
        st.write(f"Mock draft context placeholder: {aftermath.mock_draft_placeholder}")
        st.write(f"Roster risk notes: {', '.join(aftermath.roster_risk_notes)}")
        st.info(aftermath.needs_real_integration_note)
        st.write(f"Opponent fit: {best.opponent_fit}")
        st.info("Data status / needs data: using fake in-memory placeholders.")

    st.divider()
    st.subheader("Training Mode")
    st.caption(TRAINING_MODE_DISCLAIMER)
    st.write(f"Scoring dimensions: {', '.join(TRAINING_SCORING_DIMENSIONS)}.")
    for scenario in training_scenarios():
        with st.container(border=True):
            st.markdown(f"**Practice scenario:** {scenario.scenario_prompt}")
            st.write("Choices:")
            for choice in scenario.choices:
                st.write(f"- {choice}")
            st.write(f"Explanation: {scenario.explanation}")
