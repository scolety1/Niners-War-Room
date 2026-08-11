from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class WorkflowTile:
    title: str
    status: str
    detail: str
    page_path: str
    button_label: str


def apply_app_shell() -> None:
    st.markdown(
        """
        <style>
        :root {
            --nwr-bg: #f7f8fa;
            --nwr-ink: #17202a;
            --nwr-muted: #5f6b7a;
            --nwr-line: #d9dee7;
            --nwr-panel: #ffffff;
            --nwr-accent: #b3995d;
            --nwr-safe: #1f7a4d;
            --nwr-review: #9a6a00;
            --nwr-blocked: #b3261e;
        }
        .stApp {
            background: var(--nwr-bg);
            color: var(--nwr-ink);
        }
        #MainMenu,
        footer,
        [data-testid="stStatusWidget"] {
            visibility: hidden;
            height: 0;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--nwr-line);
        }
        .nwr-page-header {
            border-bottom: 1px solid var(--nwr-line);
            padding: 0.25rem 0 1rem 0;
            margin-bottom: 1rem;
        }
        .nwr-eyebrow {
            color: var(--nwr-muted);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0;
            text-transform: uppercase;
        }
        .nwr-title {
            font-size: 2.05rem;
            line-height: 1.15;
            font-weight: 760;
            margin: 0.15rem 0 0.35rem 0;
        }
        .nwr-description {
            color: var(--nwr-muted);
            max-width: 74rem;
            margin: 0;
        }
        .nwr-status-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.85rem;
        }
        .nwr-pill {
            border: 1px solid var(--nwr-line);
            border-radius: 6px;
            background: var(--nwr-panel);
            padding: 0.3rem 0.55rem;
            color: var(--nwr-muted);
            font-size: 0.82rem;
            font-weight: 650;
        }
        .nwr-pill.safe { color: var(--nwr-safe); border-color: #bdd9ca; }
        .nwr-pill.review { color: var(--nwr-review); border-color: #e5cf94; }
        .nwr-pill.blocked { color: var(--nwr-blocked); border-color: #e7b8b3; }
        .nwr-tile {
            border: 1px solid var(--nwr-line);
            border-radius: 8px;
            background: var(--nwr-panel);
            padding: 0.85rem 0.9rem;
            min-height: 9.25rem;
            overflow-wrap: anywhere;
        }
        .nwr-tile h3 {
            font-size: 1.0rem;
            margin: 0 0 0.35rem 0;
        }
        .nwr-tile p {
            color: var(--nwr-muted);
            font-size: 0.88rem;
            margin: 0.35rem 0 0 0;
        }
        .nwr-card {
            border: 1px solid var(--nwr-line);
            border-radius: 8px;
            background: var(--nwr-panel);
            padding: 0.85rem 0.95rem;
            min-height: 11rem;
            margin-bottom: 0.75rem;
            overflow-wrap: anywhere;
        }
        .nwr-card-kicker {
            color: var(--nwr-review);
            font-size: 0.78rem;
            font-weight: 760;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }
        .nwr-card-title {
            color: var(--nwr-ink);
            font-size: 1.05rem;
            font-weight: 760;
            margin-bottom: 0.45rem;
        }
        .nwr-card-body {
            color: var(--nwr-muted);
            font-size: 0.88rem;
            line-height: 1.45;
        }
        .nwr-owner-hero {
            background: linear-gradient(135deg, #151b23 0%, #27313d 100%);
            border-left: 5px solid var(--nwr-accent);
            border-radius: 10px;
            color: #ffffff;
            padding: 1.1rem 1.25rem;
            margin: 0.25rem 0 1rem 0;
        }
        .nwr-owner-hero h2 { color: #ffffff; margin: 0 0 0.35rem 0; }
        .nwr-owner-hero p { color: #e6e9ed; margin: 0; max-width: 70rem; }
        .nwr-decision-card {
            border: 1px solid var(--nwr-line);
            border-top: 4px solid var(--nwr-accent);
            border-radius: 9px;
            background: var(--nwr-panel);
            padding: 0.85rem 0.95rem;
            min-height: 8.5rem;
            margin-bottom: 0.75rem;
        }
        .nwr-decision-card h3 { font-size: 1rem; margin: 0 0 0.3rem 0; }
        .nwr-decision-card p { color: var(--nwr-muted); font-size: 0.88rem; margin: 0; }
        .nwr-range-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.65rem; }
        .nwr-range-cell {
            border: 1px solid var(--nwr-line); border-radius: 8px;
            background: var(--nwr-panel); padding: 0.75rem;
        }
        .nwr-range-cell.expected {
            border-color: var(--nwr-accent);
            box-shadow: inset 0 3px 0 var(--nwr-accent);
        }
        .nwr-range-cell strong { display: block; margin-bottom: 0.25rem; }
        .nwr-range-cell span { color: var(--nwr-muted); font-size: 0.88rem; }
        .nwr-market-buy { color: var(--nwr-safe); font-weight: 750; }
        .nwr-market-sell { color: var(--nwr-blocked); font-weight: 750; }
        .nwr-market-even { color: var(--nwr-muted); font-weight: 750; }
        .nwr-section-label {
            color: var(--nwr-muted);
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            margin: 1rem 0 0.35rem 0;
        }
        div[data-testid="stMetric"] {
            background: var(--nwr-panel);
            border: 1px solid var(--nwr-line);
            border-radius: 8px;
            padding: 0.55rem 0.65rem;
            min-width: 0;
            overflow-wrap: anywhere;
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: var(--nwr-ink) !important;
            overflow-wrap: anywhere;
            white-space: normal;
        }
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
            color: var(--nwr-muted) !important;
        }
        div[data-testid="stDataFrame"] {
            max-width: 100%;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stLinkButton"] a,
        div[data-testid="stDownloadButton"] button {
            min-height: 2.25rem;
            white-space: normal;
            overflow-wrap: anywhere;
            line-height: 1.2;
        }
        div[data-testid="stTabs"] button {
            white-space: normal;
            line-height: 1.15;
        }
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
            overflow-wrap: anywhere;
        }
        @media (max-width: 1100px) {
            .nwr-title {
                font-size: 1.55rem;
            }
            .nwr-tile,
            .nwr-card {
                min-height: auto;
            }
            div[data-testid="column"] {
                min-width: min(100%, 18rem) !important;
            }
            div[data-testid="stHorizontalBlock"] {
                gap: 0.75rem;
                flex-wrap: wrap;
            }
            div[data-testid="stTabs"] div[role="tablist"] {
                flex-wrap: wrap;
            }
        }
        @media (max-width: 760px) {
            .block-container {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }
            div[data-testid="column"] {
                flex: 1 1 100% !important;
                width: 100% !important;
            }
            .nwr-range-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(
    title: str,
    *,
    eyebrow: str,
    description: str,
    status_items: Iterable[tuple[str, str]] = (),
) -> None:
    pills = " ".join(
        f'<span class="nwr-pill {kind}">{label}</span>' for label, kind in status_items
    )
    status_html = f'<div class="nwr-status-row">{pills}</div>' if pills else ""
    st.markdown(
        f"""
        <div class="nwr-page-header">
          <div class="nwr-eyebrow">{eyebrow}</div>
          <h1 class="nwr-title">{title}</h1>
          <p class="nwr-description">{description}</p>
          {status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(label: str) -> None:
    st.markdown(f'<div class="nwr-section-label">{label}</div>', unsafe_allow_html=True)


def render_workflow_tiles(tiles: Iterable[WorkflowTile]) -> None:
    for column, tile in zip(st.columns(4), tiles, strict=False):
        with column:
            st.markdown(
                f"""
                <div class="nwr-tile">
                  <h3>{tile.title}</h3>
                  <span class="nwr-pill review">{tile.status}</span>
                  <p>{tile.detail}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.link_button(tile.button_label, tile.page_path, use_container_width=True)
