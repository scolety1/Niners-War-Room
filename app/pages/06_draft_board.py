from __future__ import annotations

# ruff: noqa: E402
import html
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.player_detail_card import render_player_detail_card
from src.config.settings import get_settings
from src.services.player_detail_card_service import build_player_detail_card_payload

DRAFT_PREP_ROOT = REPO_ROOT / "local_exports/model_v4/draft_prep/latest"
SCOUTING_PREP_POOL_ROWS = DRAFT_PREP_ROOT / "scouting_prep_pool_review_rows.csv"
DRAFTABLE_POOL_SOURCE_READINESS = DRAFT_PREP_ROOT / "draftable_pool_source_readiness.csv"
PRIOR_LEAGUE_DRAFT_BEHAVIOR_SUMMARY = (
    DRAFT_PREP_ROOT / "prior_league_draft_behavior_summary.csv"
)
PRIOR_LEAGUE_DRAFT_HISTORY_ROWS = (
    DRAFT_PREP_ROOT / "prior_league_draft_history_review_rows.csv"
)
PICK_DECISION_ROWS = (
    REPO_ROOT
    / "local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv"
)

OWNED_PICK_LABELS = ("2026 1.03", "2026 1.04", "2026 2.04", "2026 2.08", "2026 5.04")
FLEX_POSITIONS = {"RB", "WR", "TE"}
MISSING = "—"

SCOUTING_PREP_COLUMNS = [
    "Player",
    "Pos",
    "NFL Team",
    "Source Type",
    "Draftable Status",
    "NWR Draft Value / Rookie Score",
    "Trust",
    "Warnings",
    "Data Needed",
    "Pick Window / Fit Band",
    "Context Notes",
]

CANDIDATE_COLUMNS = [
    "Fit Band",
    "Player",
    "Pos",
    "NFL Team",
    "Source Type",
    "NWR Draft Value / Rookie Score",
    "Trust",
    "Warnings",
    "Data Needed",
    "Draftable Status",
]


def _render_css() -> None:
    st.markdown(
        """
        <style>
        .draft-prep-banner {
            border: 1px solid #f2c76e;
            background: #fff8e6;
            color: #4f3600;
            padding: 0.85rem 1rem;
            border-radius: 8px;
            margin: 0.75rem 0 1rem;
        }
        .pick-card {
            border: 1px solid #d7dde8;
            border-radius: 8px;
            padding: 0.85rem;
            min-height: 188px;
            background: #ffffff;
        }
        .pick-card h3 {
            margin: 0 0 0.35rem;
            font-size: 1.15rem;
        }
        .pick-meta {
            color: #536276;
            font-size: 0.85rem;
            line-height: 1.35;
        }
        .soft-pill {
            display: inline-block;
            padding: 0.16rem 0.45rem;
            margin: 0.08rem 0.12rem 0.08rem 0;
            border-radius: 999px;
            border: 1px solid #d7dde8;
            background: #f6f8fb;
            font-size: 0.76rem;
            white-space: nowrap;
        }
        .warn-pill {
            border-color: #f2c76e;
            background: #fff8e6;
            color: #6a4a00;
        }
        .source-note {
            color: #536276;
            font-size: 0.85rem;
        }
        .source-card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
            gap: 0.55rem;
            margin: 0.75rem 0 0.35rem;
        }
        .source-card {
            border: 1px solid #d7dde8;
            border-radius: 8px;
            background: #ffffff;
            padding: 0.7rem 0.75rem;
            min-height: 82px;
        }
        .source-card-label {
            color: #536276;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        .source-card-value {
            color: #1d2633;
            font-size: 0.98rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 0.28rem;
            overflow-wrap: anywhere;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def _load_csv(path_text: str, fingerprint: tuple[str, int, int, int]) -> pd.DataFrame:
    _ = fingerprint
    path = Path(path_text)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path).fillna("")


def _frame(path: Path) -> pd.DataFrame:
    return _load_csv(str(path), path_fingerprint(path))


def _clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none"} else text


def _score_value(row: pd.Series) -> float | None:
    for column in ("nwr_draft_value", "nwr_rookie_score", "nwr_dynasty_score"):
        value = pd.to_numeric(row.get(column, ""), errors="coerce")
        if pd.notna(value):
            return float(value)
    return None


def _display_score(row: pd.Series) -> str:
    value = _score_value(row)
    return MISSING if value is None else f"{value:.2f}"


def _warning_count(value: object) -> int:
    text = _clean_text(value)
    if not text:
        return 0
    return len([part for part in re.split(r"[|;]", text) if part.strip()])


def _warning_summary(value: object) -> str:
    count = _warning_count(value)
    if count == 0:
        return MISSING
    return f"{count} warning" if count == 1 else f"{count} warnings"


def _display_source_type(value: object) -> str:
    text = _clean_text(value)
    return text.replace("_", " ").title() if text else MISSING


def _display_status(value: object) -> str:
    text = _clean_text(value)
    return text.replace("_", " ").title() if text else MISSING


def _display_draftable_status(value: object) -> str:
    text = _clean_text(value).lower()
    if text == "rookie_draftable":
        return "Rookie Scouting Prep"
    if text == "free_agent_draftable":
        return "Free-Agent/Veteran Preview"
    if text == "dropped_veteran_draftable":
        return "Dropped Veteran Pending Source"
    if text == "protected_not_draftable":
        return "Protected - Not Draftable"
    if text == "no_baseline":
        return "No Baseline"
    return _display_status(value)


def _normalized_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _history_context(history_frame: pd.DataFrame) -> dict[str, str]:
    if history_frame.empty or "player" not in history_frame.columns:
        return {}
    context: dict[str, list[str]] = {}
    for _, row in history_frame.iterrows():
        key = _normalized_name(row.get("player", ""))
        if not key:
            continue
        labels: list[str] = []
        if str(row.get("user_must_draft_at_cost_flag", "")).lower() == "true":
            labels.append("Must Review At Cost")
        if str(row.get("user_drafted_flag", "")).lower() == "true":
            labels.append("User Drafted Context")
        note = _clean_text(row.get("user_note", ""))
        if note:
            labels.append(note[:80])
        if labels:
            context.setdefault(key, [])
            for label in labels:
                if label not in context[key]:
                    context[key].append(label)
    return {key: "; ".join(values[:3]) for key, values in context.items()}


def _fit_band_for_row(row: pd.Series, pick_label: str) -> str:
    if pick_label == "2026 5.04":
        return "Manual Watchlist"
    slot_context = _clean_text(row.get("nwr_slot_context", "")).lower()
    data_needed = _clean_text(row.get("data_needed", "")).lower()
    warnings = _clean_text(row.get("warning_flags", "")).lower()
    pick_round = pick_label.split()[1].split(".")[0]

    if "source_limited" in warnings or "missing" in warnings or data_needed:
        if "first_round" in slot_context and pick_round != "1":
            return "Value If Falls"
        return "Source Limited"
    if pick_round == "1" and "first_round" in slot_context:
        return "In Range"
    if pick_round == "2" and "second_round" in slot_context:
        return "In Range"
    if pick_round == "2" and "first_round" in slot_context:
        return "Value If Falls"
    if pick_round == "1" and "second_round" in slot_context:
        return "Possible Reach"
    return "Needs Scouting"


def _candidate_pool_for_pick(pool_frame: pd.DataFrame, pick_label: str) -> pd.DataFrame:
    if pool_frame.empty:
        return pd.DataFrame()
    frame = pool_frame.copy()
    frame["_score"] = frame.apply(_score_value, axis=1)
    frame["_position"] = frame.get("position", "").astype(str).str.upper()
    frame = frame[frame["_position"] != "K"]
    if pick_label == "2026 5.04":
        frame["_fit_band"] = "Manual Watchlist"
        return frame.sort_values(["_score", "player"], ascending=[False, True]).head(12)

    round_number = pick_label.split()[1].split(".")[0]
    slot_context = frame.get("nwr_slot_context", "").astype(str).str.lower()
    if round_number == "1":
        filtered = frame[slot_context.str.contains("first_round", na=False)]
    elif round_number == "2":
        filtered = frame[
            slot_context.str.contains("second_round|first_round", regex=True, na=False)
        ]
    else:
        filtered = frame
    if filtered.empty:
        filtered = frame
    filtered = filtered.copy()
    filtered["_fit_band"] = filtered.apply(lambda row: _fit_band_for_row(row, pick_label), axis=1)
    return filtered.sort_values(["_score", "player"], ascending=[False, True]).head(12)


def _candidate_display(frame: pd.DataFrame, pick_label: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "Fit Band": row.get("_fit_band") or _fit_band_for_row(row, pick_label),
                "Player": _clean_text(row.get("player", "")) or MISSING,
                "Pos": _clean_text(row.get("position", "")) or MISSING,
                "NFL Team": _clean_text(row.get("nfl_team", "")) or MISSING,
                "Source Type": _display_source_type(row.get("source_type", "")),
                "NWR Draft Value / Rookie Score": _display_score(row),
                "Trust": _display_status(row.get("trust_status", "")),
                "Warnings": _warning_summary(row.get("warning_flags", "")),
                "Data Needed": _clean_text(row.get("data_needed", "")) or MISSING,
                "Draftable Status": _display_draftable_status(row.get("draftable_status", "")),
            }
        )
    return pd.DataFrame(rows, columns=CANDIDATE_COLUMNS)


def _scouting_display(
    frame: pd.DataFrame,
    history_context: dict[str, str],
    *,
    pick_label: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        player = _clean_text(row.get("player", ""))
        context_note = history_context.get(_normalized_name(player), "")
        fit_band = _fit_band_for_row(row, pick_label)
        if context_note.startswith("Must Review At Cost"):
            fit_band = "Must Review At Cost"
        rows.append(
            {
                "Player": player or MISSING,
                "Pos": _clean_text(row.get("position", "")) or MISSING,
                "NFL Team": _clean_text(row.get("nfl_team", "")) or MISSING,
                "Source Type": _display_source_type(row.get("source_type", "")),
                "Draftable Status": _display_draftable_status(row.get("draftable_status", "")),
                "NWR Draft Value / Rookie Score": _display_score(row),
                "Trust": _display_status(row.get("trust_status", "")),
                "Warnings": _warning_summary(row.get("warning_flags", "")),
                "Data Needed": _clean_text(row.get("data_needed", "")) or MISSING,
                "Pick Window / Fit Band": fit_band,
                "Context Notes": context_note or MISSING,
            }
        )
    return pd.DataFrame(rows, columns=SCOUTING_PREP_COLUMNS)


def _render_scouting_player_detail(
    frame: pd.DataFrame,
    history_context: dict[str, str],
    *,
    pick_label: str,
) -> None:
    if frame.empty:
        return
    detail_frame = frame.head(250).copy()
    labels: dict[str, int] = {}
    for index, row in detail_frame.iterrows():
        player = _clean_text(row.get("player", "")) or MISSING
        position = _clean_text(row.get("position", "")) or MISSING
        source_type = _display_source_type(row.get("source_type", ""))
        team = _clean_text(row.get("nfl_team", "")) or MISSING
        label = f"{player} | {position} | {source_type} | {team}"
        if label in labels:
            label = f"{label} | row {index}"
        labels[label] = int(index)
    selected_label = st.selectbox(
        "Scouting player detail",
        list(labels),
        help="Open a source-safe Draft Prep detail card for a scouting row.",
    )
    selected_index = labels[str(selected_label)]
    detail_row = detail_frame.loc[selected_index].copy()
    detail_row["pick_window"] = pick_label
    detail_row["fit_band"] = _fit_band_for_row(detail_row, pick_label)
    detail_row["user_context_tags"] = history_context.get(
        _normalized_name(detail_row.get("player", "")),
        "",
    )
    payload = build_player_detail_card_payload(detail_row.to_dict(), context="draft_prep")
    with st.expander(f"Player Detail Card: {payload.player}", expanded=False):
        render_player_detail_card(payload)


def _readiness_row(readiness_frame: pd.DataFrame, source_area: str) -> pd.Series | None:
    if readiness_frame.empty or "source_area" not in readiness_frame.columns:
        return None
    matches = readiness_frame[
        readiness_frame["source_area"].astype(str).str.lower() == source_area.lower()
    ]
    if matches.empty:
        return None
    return matches.iloc[0]


def _readiness_rows(readiness_frame: pd.DataFrame) -> dict[str, pd.Series | None]:
    return {
        "active_legal": _readiness_row(readiness_frame, "active confirmed legal draftable pool"),
        "rookie_preview": _readiness_row(readiness_frame, "preview rookie draftables"),
        "fa_preview": _readiness_row(readiness_frame, "preview free agents / available veterans"),
        "dropped": _readiness_row(readiness_frame, "dropped/released veterans"),
    }


def _row_count(row: pd.Series | None) -> int:
    if row is None:
        return 0
    value = pd.to_numeric(row.get("rows", 0), errors="coerce")
    return int(value) if pd.notna(value) else 0


def _pick_decision_for(pick_frame: pd.DataFrame, pick_label: str) -> pd.Series | None:
    if pick_frame.empty or "pick_label" not in pick_frame.columns:
        return None
    matches = pick_frame[pick_frame["pick_label"].astype(str) == pick_label]
    if matches.empty:
        return None
    return matches.iloc[0]


def _pick_score_status(pick_frame: pd.DataFrame, pick_label: str) -> tuple[str, str]:
    row = _pick_decision_for(pick_frame, pick_label)
    if row is None:
        return "Source pending", "No pick-decision row loaded."
    score = pd.to_numeric(row.get("pick_value_score", ""), errors="coerce")
    tier = _clean_text(row.get("pick_tier", ""))
    warnings = _clean_text(row.get("warning_flags", ""))
    if pick_label == "2026 5.04" or pd.isna(score):
        return "No Baseline", "Manual late-round watchlist; no exact equivalence."
    meta = f"Review baseline {score:.1f}"
    if tier:
        meta += f" | {tier.replace('_', ' ')}"
    if "not_one_for_one_trade_equivalent" in warnings:
        meta += " | context only"
    return "Review Baseline", meta


def _top_snippets(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return []
    snippets: list[str] = []
    for _, row in frame.head(3).iterrows():
        player = _clean_text(row.get("player", ""))
        pos = _clean_text(row.get("position", ""))
        score = _display_score(row)
        if player:
            snippets.append(f"{player} {pos} ({score})")
    return snippets


def _render_pick_card(pool_frame: pd.DataFrame, pick_frame: pd.DataFrame, pick_label: str) -> None:
    compact_label = pick_label.replace("2026 ", "")
    candidates = _candidate_pool_for_pick(pool_frame, pick_label)
    status, meta = _pick_score_status(pick_frame, pick_label)
    source_note = "Scouting pool candidate window"
    if pick_label == "2026 5.04":
        source_note = "No exact baseline; manual late-round watchlist"
    snippets = _top_snippets(candidates)
    snippet_markup = "".join(
        f'<span class="soft-pill">{snippet}</span>' for snippet in snippets
    ) or '<span class="soft-pill">Needs scouting rows</span>'
    st.markdown(
        f"""
        <div class="pick-card">
          <h3>{compact_label}</h3>
          <div><span class="soft-pill warn-pill">{status}</span></div>
          <div class="pick-meta">{meta}</div>
          <div class="pick-meta" style="margin-top:0.55rem;">
            Candidates shown: {len(candidates)}
          </div>
          <div class="pick-meta">{source_note}</div>
          <div style="margin-top:0.55rem;">
            {snippet_markup}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _filter_pool(frame: pd.DataFrame, history_context: dict[str, str]) -> tuple[pd.DataFrame, str]:
    if frame.empty:
        return frame, "2026 1.03"
    filtered = frame.copy()
    filtered["_position"] = filtered.get("position", "").astype(str).str.upper()
    filtered["_source_type"] = filtered.get("source_type", "").astype(str).str.lower()
    filtered["_warnings"] = filtered.get("warning_flags", "").astype(str).str.lower()
    filtered["_data_needed"] = filtered.get("data_needed", "").astype(str)
    filtered["_history_context"] = filtered.get("player", "").map(
        lambda value: history_context.get(_normalized_name(value), "")
    )

    search = st.text_input("Search", placeholder="Player name, team, source, or note")
    filter_cols = st.columns([1.3, 1.1, 1.1, 1.0])
    with filter_cols[0]:
        pool_filter = st.selectbox(
            "Player Pool",
            [
                "All",
                "Rookies",
                "Free Agent / Veteran Preview",
                "Needs Scouting",
                "Source Limited",
                "Manual Watchlist",
                "Must Review At Cost",
            ],
        )
    with filter_cols[1]:
        position_filter = st.selectbox("Position", ["All", "QB", "RB", "WR", "TE", "FLEX"])
    with filter_cols[2]:
        pick_window = st.selectbox("Pick Window", list(OWNED_PICK_LABELS), index=0)
    with filter_cols[3]:
        include_k = st.toggle("Include K", value=False)

    if search:
        haystack = (
            filtered.get("player", "").astype(str)
            + " "
            + filtered.get("nfl_team", "").astype(str)
            + " "
            + filtered.get("source_type", "").astype(str)
            + " "
            + filtered["_history_context"].astype(str)
        ).str.lower()
        filtered = filtered[haystack.str.contains(search.lower(), regex=False, na=False)]

    if not include_k:
        filtered = filtered[filtered["_position"] != "K"]

    if position_filter == "FLEX":
        filtered = filtered[filtered["_position"].isin(FLEX_POSITIONS)]
        st.caption("FLEX means RB + WR + TE only. QB is excluded.")
    elif position_filter != "All":
        filtered = filtered[filtered["_position"] == position_filter]

    if pool_filter == "Rookies":
        filtered = filtered[filtered["_source_type"] == "rookie"]
    elif pool_filter == "Free Agent / Veteran Preview":
        filtered = filtered[filtered["_source_type"] == "free_agent"]
    elif pool_filter == "Needs Scouting":
        filtered = filtered[
            filtered["_data_needed"].astype(bool)
            | filtered["_warnings"].str.contains("missing|manual|review", regex=True, na=False)
        ]
    elif pool_filter == "Source Limited":
        filtered = filtered[filtered["_warnings"].str.contains("source_limited", na=False)]
    elif pool_filter == "Manual Watchlist":
        manual_mask = filtered.apply(
            lambda row: _fit_band_for_row(row, pick_window) == "Manual Watchlist",
            axis=1,
        )
        filtered = filtered[manual_mask]
    elif pool_filter == "Must Review At Cost":
        filtered = filtered[filtered["_history_context"].str.contains("Must Review At Cost")]

    filtered = filtered.copy()
    filtered["_score"] = filtered.apply(_score_value, axis=1)
    filtered = filtered.sort_values(["_score", "player"], ascending=[False, True])
    return filtered, pick_window


def _render_source_cards(pool_frame: pd.DataFrame, readiness_frame: pd.DataFrame) -> None:
    rows = _readiness_rows(readiness_frame)
    rookie_count = int((pool_frame.get("source_type", "").astype(str) == "rookie").sum())
    veteran_count = int((pool_frame.get("source_type", "").astype(str) == "free_agent").sum())
    card_rows = (
        ("Scouting Pool Rows", str(len(pool_frame))),
        ("Rookie Rows", str(rookie_count or _row_count(rows["rookie_preview"]))),
        (
            "Free-Agent/Veteran Preview Rows",
            str(veteran_count or _row_count(rows["fa_preview"])),
        ),
        ("Legal Draft Pool", "Pending"),
        ("Dropped Veterans", "Missing"),
        ("My Picks", "1.03, 1.04, 2.04, 2.08, 5.04"),
    )
    st.markdown(_source_card_grid(card_rows), unsafe_allow_html=True)


def _source_card_grid(rows: tuple[tuple[str, str], ...]) -> str:
    cards = "".join(
        (
            '<div class="source-card">'
            f'<div class="source-card-label">{html.escape(label)}</div>'
            f'<div class="source-card-value">{html.escape(value)}</div>'
            "</div>"
        )
        for label, value in rows
    )
    return f'<div class="source-card-grid">{cards}</div>'


def _render_candidate_windows(pool_frame: pd.DataFrame) -> None:
    st.subheader("Pick-by-Pick Candidate Windows")
    st.caption(
        "Candidate windows are scouting context only. Missing expected slot, NWR slot, "
        "or value-threshold fields are shown as unavailable rather than estimated."
    )
    tabs = st.tabs([label.replace("2026 ", "") for label in OWNED_PICK_LABELS])
    for tab, pick_label in zip(tabs, OWNED_PICK_LABELS, strict=True):
        with tab:
            if pick_label == "2026 5.04":
                st.warning(
                    "2026 5.04 has no admitted exact baseline. Treat this as a "
                    "manual late-round watchlist with no exact equivalence."
                )
            candidates = _candidate_pool_for_pick(pool_frame, pick_label)
            if candidates.empty:
                st.info("No scouting candidates available for this pick window.")
            else:
                st.dataframe(
                    _candidate_display(candidates, pick_label),
                    use_container_width=True,
                    hide_index=True,
                )


def _render_league_history(behavior_frame: pd.DataFrame, history_frame: pd.DataFrame) -> None:
    with st.expander("League History Context", expanded=False):
        st.caption(
            "Prior draft history, spreadsheet highlights, and user notes are display-only "
            "context. They do not alter NWR Draft Value or private player value."
        )
        if behavior_frame.empty:
            st.info("No prior league draft behavior summary loaded.")
        else:
            years = sorted(
                {
                    str(int(year))
                    for year in pd.to_numeric(
                        behavior_frame.get("draft_year", pd.Series(dtype=object)),
                        errors="coerce",
                    ).dropna()
                }
            )
            st.write(f"Prior drafts loaded: {', '.join(years) if years else MISSING}")
            st.dataframe(behavior_frame, use_container_width=True, hide_index=True)

        if not history_frame.empty:
            must_review = history_frame[
                history_frame.get("user_must_draft_at_cost_flag", "").astype(str).str.lower()
                == "true"
            ]
            user_drafted = history_frame[
                history_frame.get("user_drafted_flag", "").astype(str).str.lower() == "true"
            ]
            summary_cols = st.columns(3)
            summary_cols[0].metric("History Rows", len(history_frame))
            summary_cols[1].metric("Must Review At Cost", len(must_review))
            summary_cols[2].metric("User Drafted Context", len(user_drafted))
            st.caption(
                "Yellow spreadsheet context means must review at cost, not a final "
                "selection instruction. Green context is not treated as drafted unless "
                "the explicit drafted list says so."
            )
            st.dataframe(
                history_frame[
                    [
                        column
                        for column in (
                            "draft_year",
                            "row_source_area",
                            "draft_slot_label",
                            "drafted_at",
                            "player",
                            "position",
                            "draft_capital",
                            "age",
                            "user_note",
                            "user_drafted_flag",
                            "user_must_draft_at_cost_flag",
                        )
                        if column in history_frame.columns
                    ]
                ].head(120),
                use_container_width=True,
                hide_index=True,
            )


def _render_advanced(
    pool_frame: pd.DataFrame,
    readiness_frame: pd.DataFrame,
    pick_frame: pd.DataFrame,
    history_frame: pd.DataFrame,
) -> None:
    with st.expander("Advanced Audit", expanded=False):
        st.caption(
            "Raw receipts, warning tables, pick-decision context, and prior draft "
            "transcription details live here so the default page stays product-first."
        )
        audit_tabs = st.tabs(["Source Readiness", "Pick Rows", "Scouting Receipts", "History Raw"])
        with audit_tabs[0]:
            st.dataframe(readiness_frame, use_container_width=True, hide_index=True)
        with audit_tabs[1]:
            st.dataframe(pick_frame, use_container_width=True, hide_index=True)
        with audit_tabs[2]:
            receipt_columns = [
                column
                for column in (
                    "player",
                    "position",
                    "source_type",
                    "source_path",
                    "source_column",
                    "lineage_class",
                    "allowed_use",
                    "blocked_use",
                    "warning_flags",
                    "data_needed",
                )
                if column in pool_frame.columns
            ]
            st.dataframe(
                pool_frame[receipt_columns].head(250),
                use_container_width=True,
                hide_index=True,
            )
        with audit_tabs[3]:
            st.dataframe(history_frame.head(250), use_container_width=True, hide_index=True)

    with st.expander("Live Draft Room tools moved", expanded=False):
        st.info(
            "Mock/live draft controls now live on the separate Live Draft Room page. "
            "Draft Prep stays planning-only and does not mutate draft state."
        )
        st.markdown("[Open Live Draft Room](/live-draft-room)")


def main() -> None:
    settings = get_settings()
    render_data_pack_selector(settings)
    _render_css()

    pool_frame = _frame(SCOUTING_PREP_POOL_ROWS)
    readiness_frame = _frame(DRAFTABLE_POOL_SOURCE_READINESS)
    behavior_frame = _frame(PRIOR_LEAGUE_DRAFT_BEHAVIOR_SUMMARY)
    history_frame = _frame(PRIOR_LEAGUE_DRAFT_HISTORY_ROWS)
    pick_frame = _frame(PICK_DECISION_ROWS)
    history_notes = _history_context(history_frame)

    st.title("Draft Prep")
    st.caption(
        "Pick-by-pick planning using the scouting pool. Final legal draft pool is "
        "pending dropped-player data."
    )
    st.markdown(
        """
        <div class="draft-prep-banner">
          <strong>Scouting prep mode:</strong> Scouting Only / Legal Pool Pending.
          Final legal draftable pool is not complete until dropped/released veterans
          are supplied.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if pool_frame.empty:
        st.error(
            "Scouting prep pool is missing. Run "
            "`scripts/build_draft_prep_data_foundation.py` before using Draft Prep."
        )
        return

    _render_source_cards(pool_frame, readiness_frame)
    st.caption(
        "Confirmed legal pool not ready; scouting prep pool available. Market, league, "
        "prior draft history, and spreadsheet highlights are context-only and never "
        "used as private value."
    )

    st.subheader("My Pick Cards")
    pick_cols = st.columns(5)
    for column, pick_label in zip(pick_cols, OWNED_PICK_LABELS, strict=True):
        with column:
            _render_pick_card(pool_frame, pick_frame, pick_label)

    _render_candidate_windows(pool_frame)

    st.subheader("Scouting Prep Pool")
    st.caption(
        "Rows are scouting/prep candidates, not a finalized legal draft pool. "
        "Dropped/released veterans remain pending until Roster Declaration Day data is supplied."
    )
    filtered_pool, selected_pick_window = _filter_pool(pool_frame, history_notes)
    if filtered_pool.empty:
        st.info("No scouting rows match the current filters.")
    else:
        display = _scouting_display(
            filtered_pool,
            history_notes,
            pick_label=selected_pick_window,
        )
        st.dataframe(display.head(250), use_container_width=True, hide_index=True)
        _render_scouting_player_detail(
            filtered_pool,
            history_notes,
            pick_label=selected_pick_window,
        )

    _render_league_history(behavior_frame, history_frame)
    _render_advanced(pool_frame, readiness_frame, pick_frame, history_frame)


main()
