from __future__ import annotations

# ruff: noqa: E402
import re
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.decision_trust_strip import render_decision_trust_strips
from app.components.draft_day_v1 import (
    render_final_board_table,
    render_yellow_hold,
)
from app.components.player_compare_accessibility import (
    render_player_compare_accessibility_frame,
    render_selected_player_context,
)
from app.components.post_release_status import render_save_status, render_source_freshness
from app.components.ui_framework import page_header
from src.services.decision_trust_strip_service import build_decision_trust_strip
from src.services.display_only_ngs_context_service import (
    REVIEW_ONLY_WARNING,
    blocked_ngs_metric_rows,
    player_compare_ngs_rows,
)
from src.services.draft_day_app_v1_service import (
    APPROVED_OUTCOME_DISPLAY_FIELDS,
    OUTCOME_DISPLAY_FIELD_POSITIONS,
    OUTCOME_NOT_APPLICABLE,
    OUTCOME_NOT_ENOUGH_INFORMATION,
    display_lane_prop_frame,
    load_lane_prop_file,
    load_outcome_v2_current_player_display,
    resolve_dynasty_rankings_path,
)
from src.services.governed_asset_registry_service import load_governed_asset_registry
from src.services.injury_availability_context_service import (
    build_nflverse_availability_panel_rows,
    nflverse_availability_status_rows,
)
from src.services.outcome_v3_display_service import (
    load_outcome_v3_display,
    player_compare_outcome_v3_rows,
)
from src.services.personal_workspace_service import (
    WorkspaceValidationError,
    load_store,
    save_personal_entry,
    save_scenario,
)
from src.services.player_compare_decision_service import (
    MARKET_DISPLAY_ONLY_NOTE,
    build_player_compare_decision_summary,
    build_player_compare_nflverse_context,
    decision_summary_rows,
)
from src.services.player_compare_universe_service import (
    CURRENT_PLAYER,
    NO_COMMON_SCALE_NOTE,
    build_player_compare_universe,
    governed_source_identity,
)
from src.services.post_release_usability_service import (
    freshness_for_sources,
    initial_save_status,
    perform_workspace_write,
)
from src.services.unified_research_preview_service import (
    load_unified_research_preview,
    research_context_for_assets,
)

OUTCOME_PROP_LABELS = tuple(label for _source, _target, label in APPROVED_OUTCOME_DISPLAY_FIELDS)
HORIZON_CANDIDATE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_8h_emergency_20260622"
    / "outcome_horizon_candidate.csv"
)
INJURY_PER_GAME_AUDIT_PATH = (
    REPO_ROOT / "docs" / "hq" / "draft_day_v2" / "injury_per_game_risk_audit_20260623.csv"
)


def _position_outcome_labels(position: object) -> tuple[str, ...]:
    normalized = str(position or "").strip().upper()
    return tuple(
        label
        for _source, target, label in APPROVED_OUTCOME_DISPLAY_FIELDS
        if OUTCOME_DISPLAY_FIELD_POSITIONS[target] == normalized
    )


def _outcome_display_value(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return text


def _render_position_aware_outcome_compare(
    compare_frame: pd.DataFrame,
    prop_frame: pd.DataFrame,
    prop_path: Path,
) -> None:
    st.subheader("Outcome V1 / V2 Compatibility Context")
    st.caption(
        "Outcome probabilities are display-only. By default each player shows only the "
        "approved heads for that player's position."
    )
    show_all = st.toggle(
        "Show all Outcome columns",
        value=False,
        key="player_compare_show_all_outcomes",
        help="Wrong-position Outcome heads show N/A in this advanced view.",
    )
    st.caption(governed_source_identity("Outcome compatibility source", prop_path))

    base_columns = [column for column in ("player", "position") if column in compare_frame.columns]
    if len(base_columns) < 2:
        st.warning("Outcome comparison needs player and position context.")
        return
    merged = pd.merge(
        compare_frame[base_columns],
        prop_frame,
        on=base_columns,
        how="left",
    )
    rows: list[dict[str, str]] = []
    visible_heads: set[str] = set()
    for row in merged.to_dict("records"):
        player = str(row.get("player", ""))
        position = str(row.get("position", ""))
        labels = OUTCOME_PROP_LABELS if show_all else _position_outcome_labels(position)
        visible_heads.update(labels)
        for label in labels:
            applicable = label in _position_outcome_labels(position)
            rows.append(
                {
                    "Player": player,
                    "Pos": position,
                    "Outcome": f"{label} (Display-Only)",
                    "Probability": (
                        _outcome_display_value(row.get(label))
                        if applicable
                        else OUTCOME_NOT_APPLICABLE
                    ),
                }
            )
    if not rows:
        st.info("No applicable Outcome heads for the selected players.")
        return
    st.caption(
        "Visible Outcome heads: "
        + ", ".join(f"{head} (Display-Only)" for head in sorted(visible_heads))
    )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_outcome_v3_compare(compare_frame: pd.DataFrame) -> None:
    st.subheader("Outcome Columns V3")
    artifact = load_outcome_v3_display()
    st.info(
        "NWR_OUTCOME_COLUMNS_V3_RC1 shows calibrated dynasty-horizon context only. "
        "It does not score, rank, recommend, or reorder players."
    )
    if not artifact.loaded:
        render_yellow_hold(
            "Outcome V3 is unavailable; applicable values remain Not enough information."
        )
        if artifact.errors:
            st.error("Governed Outcome V3 source failed validation; see internal diagnostics.")
        return
    rows = player_compare_outcome_v3_rows(compare_frame, artifact.frame)
    if rows.empty:
        st.info(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    horizon_labels = rows["Horizon"].drop_duplicates().astype(str).tolist()
    horizon_text = ", ".join(horizon_labels)
    if len(horizon_labels) > 1:
        horizon_text = f"{', '.join(horizon_labels[:-1])}, and {horizon_labels[-1]}"
    st.caption(f"Expanded horizons: {horizon_text}. Exact player_id joins only.")
    columns = [
        "Player",
        "Pos",
        "Threshold",
        "Horizon",
        "Probability",
        "Calibration status",
        "Evidence",
        "Historical sample",
        "Confidence",
        "Missing-state explanation",
    ]
    st.dataframe(
        rows.loc[:, columns],
        use_container_width=True,
        hide_index=True,
        key="player_compare_outcome_v3_expanded",
    )
    st.caption(
        f"Release: {artifact.release_identifier} | Artifact rows: {artifact.row_count} | "
        f"SHA-256: {artifact.source_hash}"
    )


def _render_horizon_candidate_compare(compare_frame: pd.DataFrame) -> None:
    if not HORIZON_CANDIDATE_PATH.exists():
        return
    try:
        horizon = pd.read_csv(HORIZON_CANDIDATE_PATH, dtype=str).fillna(
            OUTCOME_NOT_ENOUGH_INFORMATION
        )
    except Exception:
        render_yellow_hold("Outcome horizon candidate file could not be loaded.")
        return
    required = {"player", "pos", "horizon_metric", "horizon_value_or_band"}
    if not required.issubset(horizon.columns):
        render_yellow_hold("Outcome horizon candidate file is missing required columns.")
        return
    selected_keys = {
        (
            str(row.get("player", "")).strip().casefold(),
            str(row.get("position", "")).strip().upper(),
        )
        for row in compare_frame.to_dict("records")
    }
    rows = [
        row
        for row in horizon.to_dict("records")
        if (
            str(row.get("player", "")).strip().casefold(),
            str(row.get("pos", "")).strip().upper(),
        )
        in selected_keys
    ]
    if not rows:
        return
    st.subheader("Horizon Outcome Candidate")
    st.caption(
        "Candidate / Review-Only bands for 2026, 2027, and Next 5Y. These are not "
        "approved probabilities and do not replace current Outcome display."
    )
    display = pd.DataFrame(rows)
    columns = [
        "player",
        "pos",
        "horizon_metric",
        "horizon_value_or_band",
        "horizon_confidence",
        "horizon_reason",
        "display_status",
    ]
    st.dataframe(
        display.loc[:, [column for column in columns if column in display.columns]].rename(
            columns={
                "player": "Player",
                "pos": "Pos",
                "horizon_metric": "Horizon Metric",
                "horizon_value_or_band": "Band (Candidate / Review-Only)",
                "horizon_confidence": "Review Coverage",
                "horizon_reason": "Reason",
                "display_status": "Status",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_visible_context_summary(compare_frame: pd.DataFrame) -> None:
    st.markdown("## Visible Context Summary")
    st.caption(
        "Fast visible-context read first. Frozen baseline rank, Dynasty Rank, tiers, "
        "and model values are not changed."
    )
    st.info(
        "Player Compare shows visible context only. It does not create a model score, "
        "recommend a player, value trades, project injuries, or change rankings."
    )
    if compare_frame.empty:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return

    records = compare_frame.to_dict("records")
    summary = build_player_compare_decision_summary(
        records[0],
        records[1],
        records[2:],
    )
    cols = st.columns(4)
    cols[0].metric("Visible-context read", summary.visible_context_read)
    cols[1].metric("Evidence coverage", summary.evidence_coverage)
    cols[2].metric("Context note", summary.context_note)
    cols[3].metric("Open review flags", str(len(summary.open_review_flags)))

    reason_col, flag_col = st.columns(2)
    with reason_col:
        st.markdown("**Visible facts / context notes**")
        for reason in summary.context_bullets:
            st.markdown(f"- {reason}")
    with flag_col:
        st.markdown("**Open review flags**")
        for flag in summary.open_review_flags:
            st.markdown(f"- {flag}")

    if summary.multi_player_note:
        st.caption(summary.multi_player_note)
    if summary.display_only_market_note:
        st.caption(summary.display_only_market_note)

    st.markdown("**Visible per-player context**")
    st.dataframe(
        pd.DataFrame(_visible_context_rows(records)),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Advanced visible-context fields", expanded=False):
        st.dataframe(
            pd.DataFrame(decision_summary_rows(records)),
            use_container_width=True,
            hide_index=True,
        )


def _render_how_to_use_compare() -> None:
    st.subheader("How to use this comparison")
    st.markdown(
        "- Start with the display-only Visible Context Summary.\n"
        "- Check Stability evidence, Ceiling evidence, roster-window context, "
        "and Main review flags.\n"
        "- Use Injury / Availability Context for review-only caveats and recent-sample gaps.\n"
        "- Open advanced expanders only when you need the underlying evidence.\n"
        "- Final roster preference stays a human decision; this page does not change ranks or "
        "model values."
    )


def _render_player_compare_policy() -> None:
    st.info(
        "Player Compare shows visible context only. It does not create a model score, "
        "recommend a player, value trades, project injuries, or change rankings."
    )


def _visible_context_rows(records: list[dict[str, object]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in records:
        player = str(record.get("player") or OUTCOME_NOT_ENOUGH_INFORMATION)
        flags = _plain_review_flags(record)
        rows.append(
            {
                "Player": player,
                "Stability evidence": _stability_evidence(record),
                "Ceiling evidence": _ceiling_evidence(record),
                "League/scoring fit": _league_fit(record),
                "Roster-window context": _plain_roster_window_context(record),
                "Main review flags": _plain_review_signal(record),
                "What still needs review": "; ".join(flags[:3])
                if flags
                else "No major open review flag in visible context.",
            }
        )
    return rows


def _stability_evidence(record: dict[str, object]) -> str:
    age = _plain_field(record, "age")
    if _plain_review_signal(record) != OUTCOME_NOT_ENOUGH_INFORMATION:
        return "Review notes available below"
    if age != OUTCOME_NOT_ENOUGH_INFORMATION:
        return f"Age shown: {age}"
    return OUTCOME_NOT_ENOUGH_INFORMATION


def _ceiling_evidence(record: dict[str, object]) -> str:
    outcome = _plain_outcome_signal(record)
    if outcome != OUTCOME_NOT_ENOUGH_INFORMATION:
        return outcome
    if _plain_field(record, "candidate_value_band") != OUTCOME_NOT_ENOUGH_INFORMATION:
        return "Review band shown below"
    return OUTCOME_NOT_ENOUGH_INFORMATION


def _league_fit(record: dict[str, object]) -> str:
    position = _plain_field(record, "position")
    if position == "QB":
        return "1QB format context; roster need stays human-reviewed"
    if position == "TE":
        return "TE context depends on role and league scarcity"
    if position in {"RB", "WR"}:
        return "RB/WR depth matters, but this is not lineup advice"
    return OUTCOME_NOT_ENOUGH_INFORMATION


def _plain_roster_window_context(record: dict[str, object]) -> str:
    age = _plain_float(record.get("age"))
    position = _plain_field(record, "position")
    if age is not None and age >= 30:
        return "Age-window review"
    if position == "QB":
        return "1QB format context requires human roster fit"
    if age is not None:
        return "Age context shown; roster fit is a human decision"
    return OUTCOME_NOT_ENOUGH_INFORMATION


def _plain_review_signal(record: dict[str, object]) -> str:
    for key in ("main_risk", "candidate_key_caveat", "on_clock_warning", "risk_notes"):
        value = _plain_field(record, key)
        if value != OUTCOME_NOT_ENOUGH_INFORMATION:
            return "Review notes available below"
    return OUTCOME_NOT_ENOUGH_INFORMATION


def _plain_review_flags(record: dict[str, object]) -> list[str]:
    flags: list[str] = []
    player = str(record.get("player") or OUTCOME_NOT_ENOUGH_INFORMATION)
    for label, key in (
        ("age missing", "age"),
        ("unsupported outcome", "outcome_applicable_summary"),
    ):
        if _plain_field(record, key) == OUTCOME_NOT_ENOUGH_INFORMATION:
            flags.append(f"{player}: {label}.")
    if _plain_review_signal(record) != OUTCOME_NOT_ENOUGH_INFORMATION:
        flags.append(f"{player}: review notes available below.")
    return flags


def _plain_outcome_signal(record: dict[str, object]) -> str:
    value = _plain_field(record, "outcome_applicable_summary")
    if value.lower() in {"unsupported", "no", "none"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return value


def _plain_field(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return text


def _plain_float(value: object) -> float | None:
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _player_index(players: list[str], preferred: str = "") -> int:
    if preferred and preferred in players:
        return players.index(preferred)
    return 0


def _non_duplicate_options(players: list[str], selected: set[str]) -> list[str]:
    return [player for player in players if player not in selected]


def _render_compare_source_status(counts: dict[str, int], source_hashes: dict[str, str]) -> None:
    current_hash = source_hashes.get("Finished V1", "Not enough information")
    st.info(
        "Governed Player Compare registry | "
        f"Finished V1 current players: {counts.get('Current Player', 0)} | "
        f"Scored rookie-review players: {counts.get('Rookie Review', 0)} | "
        f"Blocked rookies visible: {counts.get('Blocked Rookie', 0)} | "
        f"Finished V1 SHA-256: {current_hash}."
    )
    st.caption(NO_COMMON_SCALE_NOTE)


def _render_source_separated_evidence(compare_frame: pd.DataFrame) -> None:
    columns = [
        "player",
        "position",
        "nfl_team",
        "compare_asset_type",
        "compare_source_label",
        "compare_authority_status",
        "source_rank_label",
        "source_rank_value",
        "source_score_label",
        "source_score_value",
        "source_tier",
        "source_confidence",
        "blocking_reason",
        "comparison_scope",
    ]
    available = [column for column in columns if column in compare_frame.columns]
    display = compare_frame.loc[:, available].copy().fillna("")
    display = display.rename(
        columns={
            "player": "Player",
            "position": "Pos",
            "nfl_team": "NFL Team",
            "compare_asset_type": "Asset Type",
            "compare_source_label": "Governed Source",
            "compare_authority_status": "Authority",
            "source_rank_label": "Source Rank Label",
            "source_rank_value": "Source Rank",
            "source_score_label": "Source Score Label",
            "source_score_value": "Source Score",
            "source_tier": "Source Tier",
            "source_confidence": "Evidence Confidence",
            "blocking_reason": "Blocking / Missing Evidence",
            "comparison_scope": "Comparison Boundary",
        }
    )
    st.markdown("## Source-separated evidence")
    st.dataframe(display, use_container_width=True, hide_index=True)
    if compare_frame.get("compare_source_key", pd.Series(dtype=str)).nunique() > 1:
        st.warning(NO_COMMON_SCALE_NOTE)
    elif compare_frame.get("compare_asset_type", pd.Series(dtype=str)).eq("Blocked Rookie").any():
        st.warning(
            "Blocked rookie evidence remains visible but unranked and unscored. "
            "The blocking reason is not inferred or bypassed."
        )


def _render_dynasty_context(compare_frame: pd.DataFrame) -> None:
    render_final_board_table(compare_frame, key="player_compare_board")


def _render_candidate_context(compare_frame: pd.DataFrame) -> None:
    compare_columns = [
        "cross_asset_candidate_rank",
        "final_board_rank",
        "player",
        "position",
        "nfl_team",
        "age",
        "position_rank",
        "cross_asset_candidate_value",
        "candidate_value_band",
        "confidence_band",
        "candidate_vs_frozen_note",
        "candidate_action_summary",
        "candidate_key_caveat",
    ]
    available_compare_columns = [
        column for column in compare_columns if column in compare_frame.columns
    ]
    if not available_compare_columns:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    st.caption(
        "Tuned V2 review-only candidate metrics. They do not replace Final Board Rank, "
        "Dynasty Rank, or the frozen baseline checkpoint."
    )
    candidate_display = (
        compare_frame.loc[:, available_compare_columns]
        .copy()
        .fillna(OUTCOME_NOT_ENOUGH_INFORMATION)
    )
    st.dataframe(
        candidate_display.rename(
            columns={
                "cross_asset_candidate_rank": "Tuned V2 Candidate Rank (Review-Only)",
                "final_board_rank": "Final Board Rank",
                "player": "Player",
                "position": "Pos",
                "nfl_team": "NFL Team",
                "age": "Age",
                "position_rank": "Position Rank",
                "cross_asset_candidate_value": "Tuned V2 Candidate Value (Review-Only)",
                "candidate_value_band": "Candidate Band",
                "confidence_band": "Review Coverage",
                "candidate_vs_frozen_note": "Candidate vs Frozen Note",
                "candidate_action_summary": "Candidate Action Summary",
                "candidate_key_caveat": "Key Caveat / Review Flag",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_market_context(compare_frame: pd.DataFrame) -> None:
    market_columns = [
        "player",
        "position",
        "adp",
        "startup_adp_display",
        "available_pool_adp_rank",
        "available_pool_adp_range",
    ]
    columns = [column for column in market_columns if column in compare_frame.columns]
    if len(columns) <= 2:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    st.caption(MARKET_DISPLAY_ONLY_NOTE)
    st.dataframe(
        compare_frame.loc[:, columns]
        .fillna(OUTCOME_NOT_ENOUGH_INFORMATION)
        .rename(
            columns={
                "player": "Player",
                "position": "Pos",
                "adp": "ADP (Display-Only)",
                "startup_adp_display": "Startup ADP (Display-Only)",
                "available_pool_adp_rank": "Available-Pool ADP Rank (Display-Only)",
                "available_pool_adp_range": "Available-Pool ADP Range (Display-Only)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_age_risk_context(compare_frame: pd.DataFrame) -> None:
    risk_columns = [
        "player",
        "position",
        "age",
        "main_risk",
        "risk_notes",
        "candidate_key_caveat",
        "needs_manual_review",
        "human_review_flag",
    ]
    columns = [column for column in risk_columns if column in compare_frame.columns]
    if len(columns) <= 2:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    st.caption(
        "Age/injury/risk fields are shown only where the current approved data supports them."
    )
    st.dataframe(
        compare_frame.loc[:, columns]
        .fillna(OUTCOME_NOT_ENOUGH_INFORMATION)
        .rename(
            columns={
                "player": "Player",
                "position": "Pos",
                "age": "Age",
                "main_risk": "Main Risk",
                "risk_notes": "Risk Notes",
                "candidate_key_caveat": "Candidate Caveat",
                "needs_manual_review": "Needs Manual Review",
                "human_review_flag": "Human Review Flag",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_injury_per_game_context(compare_frame: pd.DataFrame) -> None:
    st.subheader("Injury / Availability Context")
    st.caption("Review-only context. No medical projection or injury-risk score is made.")
    st.caption(
        "Availability context is review-only. It does not project recovery, estimate "
        "injury risk, or change rankings. Missing injury context does not mean clean health."
    )
    st.caption(
        "Missing injury context is not clean health. Missing / limited recent sample is "
        "not a low-probability signal. This panel does not change comparison scoring, "
        "ranking, visible-context read, or hidden decision logic."
    )
    with st.expander("Injury / Availability Data Status", expanded=True):
        _render_injury_availability_status()
    outcome_bundle = load_outcome_v2_current_player_display()
    nflverse_rows = build_nflverse_availability_panel_rows(compare_frame.to_dict("records"))
    st.markdown("**NFLVerse Availability Context**")
    st.dataframe(pd.DataFrame(nflverse_rows), use_container_width=True, hide_index=True)
    st.markdown("**Outcome V2 Injury Context Flags**")
    outcome_rows = [
        _injury_display_row(record, outcome_bundle.frame)
        for record in compare_frame.to_dict("records")
    ]
    with st.expander("Selected-player injury / availability rows", expanded=True):
        st.dataframe(pd.DataFrame(outcome_rows), use_container_width=True, hide_index=True)


def _render_injury_availability_status() -> None:
    st.markdown("**Injury / Availability Data Status**")
    status_rows = [
        {
            "Question": "Outcome V2 Injury Context Flags V0 loaded?",
            "Status": "Review-only display context when the enhanced artifact loads",
            "Guardrail": "Does not change rank, tier, model value, or source truth.",
        },
        {
            "Question": "Missing injury context interpretation",
            "Status": "Not enough information",
            "Guardrail": "No approved injury context available does not mean clean health.",
        },
        {
            "Question": "Medical projection",
            "Status": "Not made",
            "Guardrail": "No recovery estimate or ranking adjustment.",
        },
    ]
    status_rows.extend(nflverse_availability_status_rows())
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)


def _injury_display_row(
    record: dict[str, object],
    outcome_frame: pd.DataFrame,
) -> dict[str, str]:
    player = str(record.get("player") or OUTCOME_NOT_ENOUGH_INFORMATION)
    position = str(record.get("position") or OUTCOME_NOT_ENOUGH_INFORMATION)
    row, match_basis, match_note = _outcome_v2_context_row_for_player(record, outcome_frame)
    if not row:
        return {
            "Player": player,
            "Pos": position,
            "Match Basis": match_basis,
            "Match Note": match_note,
            "Injury Context Available": "No approved injury context available",
            "Availability Caveat": (
                "No approved injury context available. This does not mean clean health."
            ),
            "Limited Recent Sample": OUTCOME_NOT_ENOUGH_INFORMATION,
            "Last Materially Active Season": OUTCOME_NOT_ENOUGH_INFORMATION,
            "Seasons Since Material Activity": OUTCOME_NOT_ENOUGH_INFORMATION,
            "Not Enough Information Reason": (
                "No approved injury context available for this comparison row."
            ),
        }
    available = _context_value(row, "injury_context_available")
    return {
        "Player": player,
        "Pos": position,
        "Match Basis": match_basis,
        "Match Note": match_note,
        "Injury Context Available": (
            "Available" if available == "true" else "No approved injury context available"
        ),
        "Availability Caveat": _context_value(row, "availability_caveat"),
        "Limited Recent Sample": _context_value(row, "limited_recent_sample"),
        "Last Materially Active Season": _context_value(
            row,
            "last_materially_active_season",
        ),
        "Seasons Since Material Activity": _context_value(
            row,
            "seasons_since_material_activity",
        ),
        "Not Enough Information Reason": _context_value(
            row,
            "not_enough_information_reason",
        ),
    }


def _outcome_v2_context_row_for_player(
    record: dict[str, object],
    outcome_frame: pd.DataFrame,
) -> tuple[dict[str, object], str, str]:
    if outcome_frame.empty:
        return {}, "No approved artifact match", OUTCOME_NOT_ENOUGH_INFORMATION
    player_id = str(record.get("player_id") or "").strip()
    if player_id and "nwr_player_id" in outcome_frame.columns:
        rows = outcome_frame.loc[outcome_frame["nwr_player_id"].astype(str).eq(player_id)]
        if not rows.empty:
            return rows.iloc[0].to_dict(), "Stable player_id", "Deterministic artifact match."

    if {"player_name", "position"}.issubset(outcome_frame.columns):
        key = (_player_key(record.get("player")), str(record.get("position") or "").upper())
        candidates = outcome_frame.loc[
            outcome_frame["player_name"].map(_player_key).eq(key[0])
            & outcome_frame["position"].astype(str).str.upper().eq(key[1])
        ]
        if len(candidates) == 1:
            return (
                candidates.iloc[0].to_dict(),
                "Name + position fallback",
                "Review-only fallback match; not treated as deterministic identity truth.",
            )
        if len(candidates) > 1:
            return (
                {},
                "Ambiguous name + position fallback",
                "Multiple artifact rows matched; affected context stays Not enough information.",
            )
    return {}, "No approved artifact match", OUTCOME_NOT_ENOUGH_INFORMATION


def _render_nflverse_player_context(compare_frame: pd.DataFrame) -> None:
    st.subheader("NFLVerse Player Context")
    st.caption(
        "Display-only context from the tracked NFLVerse player-context artifact. "
        "No recommendation calculated. Not model input."
    )
    st.caption(
        "Rows must match on NWR player id, have identity_join_status=SAFE_NOW_DISPLAY_ONLY, "
        "review_required=false, and pass the SAFE_NOW_DISPLAY_ONLY schema manifest. "
        "Needs identity review rows show only identity-review status."
    )
    context = build_player_compare_nflverse_context(compare_frame.to_dict("records"))
    if not context.artifact_available:
        render_yellow_hold(context.caveat)
        return

    cols = st.columns(4)
    cols[0].metric("Artifact rows", str(context.artifact_rows))
    cols[1].metric("Safe display rows", str(context.safe_display_rows))
    cols[2].metric("Identity review rows", str(context.identity_review_rows))
    cols[3].metric("Schedule rows", str(context.schedule_available_rows))
    st.caption(
        governed_source_identity("NFLVerse player context display source", context.artifact_path)
    )
    st.caption(
        "Missing data remains Not enough information. Missing injury is not healthy; "
        "missing depth is not no-role; missing snaps is not zero; missing draft capital "
        "is not confirmed UDFA."
    )

    with st.expander("Identity / Join Transparency", expanded=True):
        st.dataframe(pd.DataFrame(context.identity_rows), use_container_width=True, hide_index=True)

    with st.expander("Recent Production / Activity Context", expanded=False):
        st.dataframe(
            pd.DataFrame(context.recent_activity_rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Usage / Role Context", expanded=False):
        st.dataframe(
            pd.DataFrame(context.usage_role_rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Availability Timeline", expanded=False):
        st.caption(
            "Availability context is factual and review-only. No injury-risk score, medical "
            "projection, or comeback projection is calculated."
        )
        st.dataframe(
            pd.DataFrame(context.availability_rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Roster-Window Context", expanded=False):
        st.caption(
            "Roster-window context is non-financial. It does not create contract valuation, "
            "trade value, pick value, or ranking changes."
        )
        st.dataframe(
            pd.DataFrame(context.roster_window_rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Schedule Context", expanded=False):
        st.caption(
            "Schedule context is factual and display-only. It does not create matchup advice, "
            "recommendations, hidden sort, or projections."
        )
        st.dataframe(
            pd.DataFrame(context.schedule_rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Dataset Freshness / Coverage Badges", expanded=False):
        st.dataframe(
            pd.DataFrame(context.dataset_badge_rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Deferred / Manual Review Items", expanded=False):
        st.dataframe(pd.DataFrame(context.deferred_rows), use_container_width=True, hide_index=True)


def _render_display_only_ngs_context(compare_frame: pd.DataFrame) -> None:
    st.subheader("Review-only NGS Context")
    st.caption(REVIEW_ONLY_WARNING)
    st.caption(
        "Values are side-by-side context only. They do not create a winner, recommendation, "
        "verdict, boost, score, hidden sort, ranking change, trade decision, or draft decision."
    )
    rows = player_compare_ngs_rows(compare_frame.to_dict("records"))
    if not rows:
        render_yellow_hold(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Unavailable/thresholded means the safe identity chain or public NGS threshold coverage "
        "did not support a value. It is not converted to zero."
    )
    with st.expander("Blocked advanced metrics kept out of Player Compare", expanded=False):
        st.dataframe(
            pd.DataFrame(blocked_ngs_metric_rows()),
            use_container_width=True,
            hide_index=True,
        )


def _context_value(row: dict[str, object], column: str) -> str:
    text = str(row.get(column, "") if row else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return text


def _player_key(value: object) -> str:
    text = str(value or "").lower().replace("jr.", "jr")
    text = text.replace("brian thomas jr", "brian thomas")
    return re.sub(r"[^a-z0-9]+", "", text)


render_player_compare_accessibility_frame()

current_board_path, _current_board_label, _current_board_warnings = resolve_dynasty_rankings_path()
governed = load_governed_asset_registry(
    repo_root=REPO_ROOT,
    current_board_path=current_board_path,
)
compare_universe = build_player_compare_universe(governed)
compare_pool = compare_universe.frame

page_header(
    "Player Compare",
    eyebrow="Draft-Day App V1",
    description=(
        "Compare 2 to 4 governed current players or 2026 rookie-review players while "
        "keeping their source ranks, scores, and evidence boundaries separate."
    ),
    status_items=(("Governed registry", "safe"), ("No common scale", "review")),
)
render_source_freshness(freshness_for_sources(("Finished V1", "Outcome V3")))
st.caption(
    "Deep tool: visible-context aid only. Comparison output does not mutate ranks, tiers, "
    "model values, or source-truth files."
)
_render_compare_source_status(compare_universe.counts, governed.source_hashes)
if compare_universe.errors:
    st.error(
        "Player Compare cannot load the complete governed player universe. "
        "No fallback or fabricated players were substituted."
    )
    for error in compare_universe.errors:
        st.error(error)
    st.stop()
_render_player_compare_policy()

asset_ids = (
    compare_pool["asset_id"].astype(str).tolist() if "asset_id" in compare_pool.columns else []
)
labels_by_id = (
    compare_pool.set_index("asset_id")["compare_select_label"].astype(str).to_dict()
    if asset_ids
    else {}
)
selector_labels = [labels_by_id[asset_id] for asset_id in asset_ids]
ids_by_label = {label: asset_id for asset_id, label in labels_by_id.items()}
names_by_id = (
    compare_pool.set_index("asset_id")["player"].astype(str).to_dict() if asset_ids else {}
)
ids_by_name = {name: asset_id for asset_id, name in names_by_id.items()}
query_assets = []
for query_value in st.query_params.get_all("player"):
    if query_value in labels_by_id:
        query_assets.append(labels_by_id[query_value])
    elif query_value in ids_by_name:
        query_assets.append(labels_by_id[ids_by_name[query_value]])
st.markdown("## Choose players")
if len(selector_labels) < 2:
    st.warning("Not enough information: player pool has fewer than two players.")
else:
    selector_cols = st.columns(2)
    player_a_default = query_assets[0] if query_assets else ""
    player_b_default = query_assets[1] if len(query_assets) > 1 else ""
    player_a_label = selector_cols[0].selectbox(
        "Player A selector",
        selector_labels,
        index=_player_index(selector_labels, player_a_default),
        key="player_compare_a",
    )
    player_b_options = _non_duplicate_options(selector_labels, {player_a_label})
    player_b_label = selector_cols[1].selectbox(
        "Player B selector",
        player_b_options,
        index=_player_index(player_b_options, player_b_default),
        key="player_compare_b",
    )
    extra_options = _non_duplicate_options(
        selector_labels,
        {player_a_label, player_b_label},
    )
    extra_player_labels = st.multiselect(
        "Optional extra players",
        extra_options,
        default=[player for player in query_assets[2:4] if player in extra_options],
        max_selections=2,
        help="Use this only when you want a 3- or 4-player decision check.",
    )
    player_a_id = ids_by_label[player_a_label]
    player_b_id = ids_by_label[player_b_label]
    extra_player_ids = [ids_by_label[label] for label in extra_player_labels]
    selected = [player_a_id, player_b_id, *extra_player_ids]
    compare = compare_pool.loc[compare_pool["asset_id"].astype(str).isin(selected)].copy()
    compare["_selection_order"] = (
        compare["asset_id"]
        .astype(str)
        .map({asset_id: index for index, asset_id in enumerate(selected)})
    )
    compare = compare.sort_values("_selection_order", kind="stable").drop(
        columns=["_selection_order"]
    )
    player_a = names_by_id[player_a_id]
    player_b = names_by_id[player_b_id]
    extra_players = [names_by_id[asset_id] for asset_id in extra_player_ids]
    render_selected_player_context(player_a, player_b, extra_players)
    _render_source_separated_evidence(compare)
    st.markdown("## Unified Research Context")
    st.warning(
        "RESEARCH ONLY — NOT PRODUCTION AUTHORITY. Calibration is not fully validated and "
        "there is no fresh mature 5Y rookie cohort. Decision support only. "
        "No common production scale is created."
    )
    try:
        unified_research_preview = load_unified_research_preview()
        research_context = research_context_for_assets(
            unified_research_preview, compare["asset_id"].astype(str).tolist()
        )
    except (OSError, ValueError) as exc:
        st.info(f"Unified research context is unavailable: {exc}")
    else:
        if research_context.empty:
            st.info("No frozen Unified Research Context exists for the selected assets.")
        else:
            st.dataframe(
                research_context[
                    [
                        "player",
                        "position",
                        "asset_type",
                        "research_rank",
                        "research_tier",
                        "outlook_3y",
                        "outlook_5y",
                        "ceiling_signal",
                        "downside_signal",
                        "confidence",
                        "evidence_coverage",
                        "status",
                        "blocking_reason",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "This frozen common research framework does not override the source-separated "
                "production and rookie-review evidence above."
            )
            selected_rookie_ids = set(
                research_context.loc[
                    research_context["asset_type"].eq("ROOKIE"), "governed_player_id"
                ].astype(str)
            )
            rookie_neighborhoods = unified_research_preview.neighborhoods
            rookie_neighborhoods = rookie_neighborhoods.loc[
                rookie_neighborhoods["rookie_governed_id"].astype(str).isin(selected_rookie_ids)
            ]
            if not rookie_neighborhoods.empty:
                st.caption(
                    "Nearby veterans above and below are frozen research-order context, not "
                    "production comparables."
                )
                st.dataframe(
                    rookie_neighborhoods[
                        [
                            "rookie",
                            "position",
                            "research_rank",
                            "research_tier",
                            "veterans_above",
                            "veterans_below",
                            "confidence",
                            "evidence_coverage",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
    _render_visible_context_summary(compare)

    st.markdown("## Evidence caveats and trust context")
    render_decision_trust_strips(
        [
            build_decision_trust_strip(
                row,
                surface="Player Compare",
                entity_label=str(row.get("player") or "Selected player"),
                receipt_label="Existing comparison detail and diagnostic disclosures",
                receipt_available=bool(str(row.get("source_coverage") or "").strip()),
            )
            for row in compare.to_dict("records")
        ],
        heading="Selected-player evidence trust",
    )
    _render_how_to_use_compare()

    st.markdown("## Secondary comparison details")
    detail_tabs = st.tabs(
        [
            "Dynasty / NWR Context",
            "Market timing context",
            "Injury / Availability Context",
            "Outcome / Horizon",
            "Age / Injury / Risk",
            "NFLVerse Player Context",
            "Review-only NGS Context",
            "Raw Details / Diagnostics",
        ]
    )
    with detail_tabs[0]:
        _render_candidate_context(compare)
        with st.expander("Frozen board detail", expanded=False):
            _render_dynasty_context(compare)
    with detail_tabs[1]:
        _render_market_context(compare)
    with detail_tabs[2]:
        _render_injury_per_game_context(compare)
    with detail_tabs[4]:
        _render_age_risk_context(compare)
    with detail_tabs[5]:
        _render_nflverse_player_context(compare)
    with detail_tabs[6]:
        _render_display_only_ngs_context(compare)

    prop_files = {
        "outcome_columns": "outcome_player_context.csv",
        "trading_lab": "trade_helper_context.csv",
        "rookie_hq": "rookie_overlay_context.csv",
        "decision_board": "decision_flags_context.csv",
    }
    with detail_tabs[3]:
        _render_outcome_v3_compare(compare)
        outcome_frame, outcome_path = load_lane_prop_file(
            "outcome_columns",
            "outcome_player_context.csv",
        )
        with st.expander("Legacy Outcome compatibility context", expanded=False):
            if outcome_path is None or outcome_frame.empty:
                render_yellow_hold("Outcome props are missing.")
            else:
                _render_position_aware_outcome_compare(compare, outcome_frame, outcome_path)
                _render_horizon_candidate_compare(compare)

    with detail_tabs[7]:
        st.caption(
            "Raw context is diagnostic-only and intentionally below the visible context summary."
        )
        for lane, file_name in prop_files.items():
            with st.expander(f"{lane} props", expanded=False):
                prop_frame, prop_path = load_lane_prop_file(lane, file_name)
                if prop_path is None:
                    render_yellow_hold(f"{lane} props are missing.")
                    continue
                if prop_frame.empty:
                    render_yellow_hold(
                        f"{governed_source_identity(f'{lane} governed props', prop_path)} "
                        "is unavailable."
                    )
                    continue
                st.caption(governed_source_identity(f"{lane} governed props", prop_path))
                join_columns = [
                    column
                    for column in ("player", "position", "final_board_rank")
                    if column in prop_frame.columns
                ]
                if not join_columns:
                    st.dataframe(
                        display_lane_prop_frame(prop_frame).head(25),
                        use_container_width=True,
                        hide_index=True,
                    )
                    continue
                base_columns = [column for column in join_columns if column in compare.columns]
                context = pd.merge(compare[base_columns], prop_frame, on=base_columns, how="left")
                st.dataframe(
                    display_lane_prop_frame(context),
                    use_container_width=True,
                    hide_index=True,
                )

    st.markdown("## Personal Workspace")
    governed_by_id = {row["asset_id"]: row for row in governed.rows}
    exact_ids = [
        str(row["asset_id"])
        for row in compare.to_dict("records")
        if row.get("compare_asset_type") == CURRENT_PLAYER
        and str(row.get("asset_id")) in governed_by_id
    ]
    personal_store = load_store("personal_board")
    scenario_store = load_store("saved_scenarios")
    overlays = {row["asset_id"]: row for row in personal_store.records}
    render_save_status(initial_save_status(scenario_store.status, scenario_store.updated_at_utc))
    if exact_ids:
        st.dataframe(
            pd.DataFrame(
                {
                    "Asset": governed_by_id[key]["asset_name"],
                    "Source": governed_by_id[key]["source_label"],
                    "Source Rank": governed_by_id[key]["rank_value"],
                    "My Tier": overlays.get(key, {}).get("my_tier", ""),
                    "My Rank": overlays.get(key, {}).get("my_rank", ""),
                    "My Tags": ", ".join(overlays.get(key, {}).get("tags", [])),
                    "Notes": "Yes" if overlays.get(key, {}).get("notes") else "",
                }
                for key in exact_ids
            ),
            hide_index=True,
            width="stretch",
        )
        action_columns = st.columns(2)
        action_asset = action_columns[0].selectbox(
            "Personal action asset",
            exact_ids,
            format_func=lambda key: governed_by_id[key]["asset_name"],
        )
        personal_action = action_columns[1].selectbox(
            "Explicit personal action", ("Add to watchlist", "Mark as target")
        )
        if st.button("Apply personal action"):
            overlay = dict(overlays.get(action_asset, {}))
            overlay.update(
                {
                    "asset_id": action_asset,
                    "asset_type": "Current Player",
                    "source_authority_version": governed.source_hashes.get(
                        "Finished V1", "governed-context"
                    ),
                    "team_window": overlay.get("team_window", "Custom/Unspecified"),
                    "watchlist": personal_action == "Add to watchlist"
                    or bool(overlay.get("watchlist")),
                    "target": personal_action == "Mark as target" or bool(overlay.get("target")),
                }
            )
            try:
                write_status = perform_workspace_write(
                    lambda: save_personal_entry(
                        overlay,
                        asset_registry={
                            key: row["asset_type"] for key, row in governed_by_id.items()
                        },
                    ),
                    observer=render_save_status,
                )
                if write_status.state == "Save failed":
                    st.error("The personal action was not persisted; retry explicitly.")
            except WorkspaceValidationError as exc:
                st.error(f"Personal action blocked: {exc}")

        with st.form("save-player-compare-scenario"):
            scenario_title = st.text_input("Comparison scenario title")
            scenario_notes = st.text_area("Comparison notes", max_chars=20_000)
            save_compare = st.form_submit_button("Save comparison scenario")
        if save_compare:
            visible_fields = [
                column
                for column in ("player_id", "player", "position", "nfl_team", "nwr_rank")
                if column in compare.columns
            ]
            try:
                write_status = perform_workspace_write(
                    lambda: save_scenario(
                        {
                            "scenario_id": f"compare-{uuid4()}",
                            "scenario_type": "player_compare",
                            "title": scenario_title or "Saved Player Compare",
                            "assets": exact_ids,
                            "source_versions": governed.source_hashes,
                            "payload": {
                                "visible_comparison_fields": compare[visible_fields].to_dict(
                                    "records"
                                ),
                                "notes": scenario_notes,
                            },
                        },
                        asset_registry={
                            key: row["asset_type"] for key, row in governed_by_id.items()
                        },
                    ),
                    observer=render_save_status,
                )
                if write_status.state == "Save failed":
                    st.error("The comparison remains in the current session but was not saved.")
            except WorkspaceValidationError as exc:
                st.error(f"Scenario blocked: {exc}")
    else:
        st.warning("Exact governed IDs are unavailable; personal actions remain blocked.")
    workspace_links = st.columns(2)
    workspace_links[0].link_button("Open Personal Board", "/personal-board")
    workspace_links[1].link_button("Create decision receipt", "/decision-journal")
