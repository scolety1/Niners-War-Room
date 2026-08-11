"""Small, reusable owner-facing decision components."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape

import streamlit as st


def owner_intro(title: str, description: str) -> None:
    st.markdown(
        f'<div class="nwr-owner-hero"><h2>{escape(title)}</h2><p>{escape(description)}</p></div>',
        unsafe_allow_html=True,
    )


def decision_cards(cards: Iterable[tuple[str, str]]) -> None:
    items = tuple(cards)
    if not items:
        return
    for column, (title, body) in zip(st.columns(len(items)), items, strict=False):
        with column:
            st.markdown(
                f'<div class="nwr-decision-card"><h3>{escape(title)}</h3>'
                f"<p>{escape(body)}</p></div>",
                unsafe_allow_html=True,
            )


def floor_expected_ceiling(values: Mapping[str, object], *, note: str = "") -> None:
    cells = []
    for label in ("Floor", "Expected", "Ceiling"):
        value = _text(values.get(label)) or "Not enough information"
        css = " expected" if label == "Expected" else ""
        cells.append(
            f'<div class="nwr-range-cell{css}"><strong>{label}</strong>'
            f"<span>{escape(value)}</span></div>"
        )
    st.markdown(
        '<div class="nwr-range-grid">' + "".join(cells) + "</div>",
        unsafe_allow_html=True,
    )
    if note:
        st.caption(note)


def market_readout(label: str, *, gap: str = "", status: str = "") -> None:
    normalized = label.casefold()
    css = (
        "nwr-market-buy"
        if "buy" in normalized or "higher" in normalized
        else (
            "nwr-market-sell"
            if "sell" in normalized or "caution" in normalized
            else "nwr-market-even"
        )
    )
    details = " · ".join(value for value in (gap, status) if value)
    st.markdown(
        f'<span class="{css}">{escape(label)}</span>'
        + (f'<div class="nwr-card-body">{escape(details)}</div>' if details else ""),
        unsafe_allow_html=True,
    )


def advanced_details(title: str, details: Mapping[str, object]) -> None:
    with st.expander(title, expanded=False):
        st.json({key: _text(value) for key, value in details.items()})


def _text(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.casefold() in {"", "nan", "none", "null", "<na>"} else text
