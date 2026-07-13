from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import streamlit as st

PLAYER_COMPARE_COMPACT_BREAKPOINT_PX = 900
PLAYER_COMPARE_MIN_TOUCH_TARGET_PX = 44
PLAYER_COMPARE_NOT_SELECTED = "No player selected"
PLAYER_COMPARE_REGION_ORDER = (
    "Player Compare",
    "Choose players",
    "Selected-player context",
    "Visible Context Summary",
    "Evidence caveats and trust context",
    "Secondary comparison details",
)


@dataclass(frozen=True)
class SelectedPlayerContext:
    slot: str
    state: str
    player: str


def selected_player_context_rows(
    player_a: object = "",
    player_b: object = "",
    extra_players: Sequence[object] = (),
) -> tuple[SelectedPlayerContext, ...]:
    """Create text-only slot context without resolving or changing player identity."""
    values = (player_a, player_b, *extra_players)
    slots = ("Player A", "Player B") + tuple(
        f"Optional player {index}" for index in range(1, len(extra_players) + 1)
    )
    rows: list[SelectedPlayerContext] = []
    for slot, value in zip(slots, values, strict=True):
        text = str(value or "").strip()
        rows.append(
            SelectedPlayerContext(
                slot=slot,
                state="Selected" if text else "Not selected",
                player=text or PLAYER_COMPARE_NOT_SELECTED,
            )
        )
    return tuple(rows)


def render_player_compare_accessibility_frame() -> None:
    """Add semantic heading and page-scoped compact rules for Player Compare only."""
    st.markdown(
        f"""
        <style>
        .nwr-player-compare-sr-only {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }}
        body:has(#nwr-player-compare-page) .block-container,
        body:has(#nwr-player-compare-page) div[data-testid="stDataFrame"],
        body:has(#nwr-player-compare-page) div[data-testid="stTabs"] {{
            max-width: 100%;
            min-width: 0;
        }}
        body:has(#nwr-player-compare-page) div[data-testid="stMetricValue"] p,
        body:has(#nwr-player-compare-page) div[data-testid="stMetric"] label p,
        body:has(#nwr-player-compare-page) div[data-testid="stTabs"] button p,
        body:has(#nwr-player-compare-page) details summary p {{
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            overflow-wrap: anywhere;
        }}
        body:has(#nwr-player-compare-page) div[data-testid="stTabs"] div[role="tablist"] {{
            max-width: 100%;
            flex-wrap: wrap;
        }}
        body:has(#nwr-player-compare-page) button:focus-visible,
        body:has(#nwr-player-compare-page) [role="combobox"]:focus-visible,
        body:has(#nwr-player-compare-page) [role="tab"]:focus-visible,
        body:has(#nwr-player-compare-page) details summary:focus-visible {{
            outline: 3px solid #005fcc !important;
            outline-offset: 2px !important;
        }}
        @media (max-width: {PLAYER_COMPARE_COMPACT_BREAKPOINT_PX}px) {{
            body:has(#nwr-player-compare-page) div[data-testid="stHorizontalBlock"] {{
                gap: 0.75rem;
                flex-wrap: wrap;
            }}
            body:has(#nwr-player-compare-page) div[data-testid="stColumn"] {{
                flex: 1 1 100% !important;
                width: 100% !important;
                min-width: 0 !important;
            }}
            body:has(#nwr-player-compare-page) div[data-testid="stSelectbox"] [role="combobox"],
            body:has(#nwr-player-compare-page) div[data-testid="stSelectbox"] button,
            body:has(#nwr-player-compare-page) div[data-testid="stMultiSelect"] [role="combobox"],
            body:has(#nwr-player-compare-page) div[data-testid="stMultiSelect"] button,
            body:has(#nwr-player-compare-page) div[data-testid="stDataFrame"] button,
            body:has(#nwr-player-compare-page) div[data-testid="stTabs"] [role="tab"],
            body:has(#nwr-player-compare-page) details summary {{
                min-height: {PLAYER_COMPARE_MIN_TOUCH_TARGET_PX}px;
            }}
            body:has(#nwr-player-compare-page) div[data-testid="stSelectbox"] button,
            body:has(#nwr-player-compare-page) div[data-testid="stSelectbox"] [role="combobox"],
            body:has(#nwr-player-compare-page) div[data-testid="stMultiSelect"] button,
            body:has(#nwr-player-compare-page) div[data-testid="stMultiSelect"] [role="combobox"],
            body:has(#nwr-player-compare-page) div[data-testid="stDataFrame"] button,
            body:has(#nwr-player-compare-page) button[aria-label^="Help for"] {{
                min-width: {PLAYER_COMPARE_MIN_TOUCH_TARGET_PX}px;
            }}
            body:has(#nwr-player-compare-page) button[aria-label^="Help for"] {{
                min-height: {PLAYER_COMPARE_MIN_TOUCH_TARGET_PX}px;
            }}
        }}
        </style>
        <span id="nwr-player-compare-page" aria-hidden="true"></span>
        <h1 class="nwr-player-compare-sr-only">Player Compare</h1>
        """,
        unsafe_allow_html=True,
    )


def render_selected_player_context(
    player_a: object,
    player_b: object,
    extra_players: Sequence[object] = (),
) -> None:
    st.markdown("## Selected-player context")
    rows = selected_player_context_rows(player_a, player_b, extra_players)
    columns = st.columns(len(rows), gap="medium")
    for column, row in zip(columns, rows, strict=True):
        with column:
            st.markdown(f"**{row.slot} — {row.state.lower()}**")
            st.write(row.player)
    st.caption(
        "Player A and Player B are named in text. Comparison-slot identity never depends "
        "on color alone."
    )
