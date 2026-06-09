from __future__ import annotations

import html
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.human_labels import human_label
from app.components.player_detail_panel import PlayerDetail, render_player_detail_panel
from app.components.trust_status import REVIEW_ONLY_SURFACE_BANNER
from app.components.ui_framework import page_header, section_label
from src.config.settings import get_settings
from src.services.forced_release_strategy_service import build_forced_release_strategy

MODEL_V4_ROOT = Path("local_exports/model_v4")
PREP_ROOT = MODEL_V4_ROOT / "human_decision_review_prep/latest"
SPRINT1_ROOT = MODEL_V4_ROOT / "decision_board_validation/latest"
BOARD_ROOT = MODEL_V4_ROOT / "june15_decision_board/latest"
PRESSURE_ROOT = MODEL_V4_ROOT / "decision_pressure/latest"
EXTERNAL_ASSET_ROOT = MODEL_V4_ROOT / "external_asset_reviews/latest"
PICK_ROOT = MODEL_V4_ROOT / "pick_trade_defer/latest"
ROOKIE_ROOT = MODEL_V4_ROOT / "rookie_draft_review/latest"
OPPORTUNITY_ROOT = MODEL_V4_ROOT / "roster_opportunity_cost/latest"

PREP_SUMMARY = PREP_ROOT / "human_decision_review_summary.csv"
PICK_CARDS = PREP_ROOT / "pick_review_cards.csv"
ROSTER_CARDS = PREP_ROOT / "roster_pressure_review_cards.csv"
TRADE_CARDS = PREP_ROOT / "trade_review_cards.csv"
ROOKIE_QUEUE = PREP_ROOT / "rookie_manual_scout_queue.csv"
VETERAN_CARDS = PREP_ROOT / "veteran_risk_review_cards.csv"
SPRINT1_FOCUS = SPRINT1_ROOT / "decision_board_validation_focus_rows.csv"
BOARD_ROWS = BOARD_ROOT / "june15_decision_board_review_rows.csv"
BOARD_WARNINGS = BOARD_ROOT / "june15_decision_board_warnings.csv"
BOARD_RECEIPTS = BOARD_ROOT / "june15_decision_board_receipts.csv"
PRESSURE_ROWS = PRESSURE_ROOT / "cut_keep_pressure_review_rows.csv"
TRADE_AWAY_ROWS = EXTERNAL_ASSET_ROOT / "trade_away_candidate_review_rows.csv"
EXTERNAL_ASSET_ROWS = EXTERNAL_ASSET_ROOT / "external_asset_context_review_rows.csv"
PICK_ROWS = PICK_ROOT / "niners_pick_inventory_review_rows.csv"
PICK_DEFER_ROWS = PICK_ROOT / "pick_defer_scenario_review_rows.csv"
ROOKIE_CANDIDATE_ROWS = ROOKIE_ROOT / "rookie_pick_candidate_review_rows.csv"
OPPORTUNITY_COST_ROWS = OPPORTUNITY_ROOT / "roster_opportunity_cost_rows.csv"
OPPORTUNITY_COST_COMPONENT_ROWS = OPPORTUNITY_ROOT / "roster_opportunity_cost_component_rows.csv"
OPPORTUNITY_COST_WARNING_ROWS = OPPORTUNITY_ROOT / "roster_opportunity_cost_warnings.csv"
AGE_ROWS = MODEL_V4_ROOT / "prospect_age/latest/player_age_2026.csv"

CARD_COLUMNS = [
    "review_area",
    "entity_label",
    "position",
    "review_band",
    "model_says",
    "human_needs_to_decide",
    "confidence_or_risk_warnings",
    "receipt_pointer",
]

AREA_LABELS = {
    "pick_by_pick_review": "Pick review",
    "roster_pressure_review": "Roster pressure",
    "trade_away_review": "Trade-away review",
    "external_asset_context_review": "External asset context",
    "rookie_manual_scout_queue": "Rookie scout queue",
    "veteran_age_risk_review": "Veteran risk review",
    "pick_trade_defer_context": "Pick timing context",
    "roster_pressure_trade_context": "Roster pressure/trade context",
    "rookie_pick_window_context": "Rookie pick window context",
}

BAND_LABELS = {
    "future_first_defer_premium_context_review": (
        "Premium pick: compare use, move-down, and 2027 timing"
    ),
    "future_pick_defer_context_review": "Pick has timing/context question to review",
    "missing_pick_value_baseline": "Missing pick value baseline",
    "manual_only_no_exact_model_baseline": "Manual-only: no exact model baseline",
    "matched_pick_value_baseline": "Pick baseline matched",
    "required_pressure_zone_review": "Priority roster pressure review",
    "protectable_depth_review": "Depth piece to review",
    "protected_core_review": "Protected/core context",
    "pressure_shop_watch_review": "Shop/watch before cut pressure",
    "liquidity_check_context_review": "Liquidity context before cut review",
    "depth_liquidity_watch_review": "Depth/name-value liquidity watch",
    "hold_core_unless_overpay_review": "Hold unless overpay",
    "elite_external_asset_context_review": "Elite external asset context",
    "strong_external_asset_context_review": "Strong external asset context",
    "roster_fit_external_asset_context_review": "Roster-fit external asset context",
    "external_asset_context_review": "External asset context",
    "tier_gap_context_review": "Candidate trails pick but remains in tier conversation",
    "significant_pick_value_gap_review": "Large gap to pick value",
    "pick_value_aligned_context_review": "Candidate roughly aligns with pick value",
    "late_watchlist_no_pick_baseline_review": "Late watchlist only; pick baseline missing",
    "expensive_to_cut": "Expensive to cut",
    "trade_context_before_cut_review": "Trade context before cut review",
    "replaceable_depth": "Replaceable depth",
    "manual_review_required": "Manual review required",
    "injury_or_source_uncertain": "Injury/source uncertain",
    "rookie_pick_equivalent_uncertain": "Rookie pick equivalent uncertain",
}

WARNING_LABELS = {
    "review_only_no_final_decision_recommendation": "Review-only: no final decision",
    "review_only_no_pick_trade_recommendation": "No pick-trade final call",
    "review_only_no_final_rookie_pick_recommendation": "No final rookie pick call",
    "pick_value_baseline_missing": "Pick baseline missing",
    "heuristic_pick_curve_requires_audit": "Pick curve is heuristic",
    "future_pick_baseline_higher_than_current_same_slot": "Future same-slot baseline is higher",
    "missing_role_evidence": "Missing role evidence",
    "missing_or_review_route_target_snap_evidence": "Missing route/share/snap evidence",
    "missing_lifecycle_or_role_shape_evidence": "Missing lifecycle/role-shape evidence",
    "missing_prospect_or_college_evidence": "Missing prospect or college evidence",
    "combine_absent_not_zero_filled": "Combine data absent, not zero-filled",
    "missing_market_share_component": "Missing college team-share component",
    "missing_athletic_prior_component": "Missing athletic prior",
    "missing_recruiting_prior_component": "Missing recruiting prior",
    "missing_landing_context_review": "Missing landing context",
    "current_college_team_mismatch_quarantined": "College/team mismatch quarantined",
    "third_party_combine_source_limited": "Third-party combine source is limited",
    "source_limited_evidence_cap": "Source-limited evidence cap",
    "identity_review_cap": "Identity review cap",
    "partial_or_quarantined_join_cap": "Partial/quarantined join cap",
    "review_only_no_cut_keep_recommendation": "No cut/keep final call",
    "rookie_pick_equivalent_uncertain": "Rookie pick equivalent uncertain",
    "manual_only_no_exact_model_baseline": "Manual-only: no exact model baseline",
}

DISPLAY_LABELS = {
    "allowed_use": "Use",
    "blocked_use": "Blocked",
    "confidence_cap": "Trust Cap",
    "market_share_score": "College Team Share",
    "draft_capital_score": "NFL Draft Pick Signal",
    "source_risk_level": "Evidence Risk",
    "model_edge_weirdness": "Model Separation",
    "source_shape_warning": "Data Shape Warning",
    "format_discipline_case": "Format Discipline",
}

WARNING_GROUP_RULES = (
    (
        "Data incomplete",
        (
            "missing_",
            "combine_absent",
            "partial_or_quarantined",
            "workout_metric_missing",
        ),
    ),
    (
        "Low draft investment",
        (
            "day_three",
            "missing_draft_capital",
            "draft_capital_anchor_warning",
        ),
    ),
    ("No-premium TE caution", ("no_premium_te",)),
    ("1QB QB caution", ("one_qb",)),
    (
        "Source-limited role data",
        (
            "source_limited",
            "third_party_combine_source_limited",
            "route_target_snap",
            "licensed_route",
        ),
    ),
    (
        "Manual review required",
        (
            "manual",
            "quarantined",
            "identity_review",
            "source_shape_warning",
            "manual_only_no_exact_model_baseline",
        ),
    ),
)


@st.cache_data
def _load_csv(path_text: str, fingerprint: tuple[str, int, int, int]) -> pd.DataFrame:
    _ = fingerprint
    path = Path(path_text)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str).fillna("")


def _frame(path: Path) -> pd.DataFrame:
    return _load_csv(str(path), path_fingerprint(path))


def _filter_frame(
    frame: pd.DataFrame,
    *,
    decision_area: list[str],
    picks: list[str],
    positions: list[str],
    bands: list[str],
    warning_terms: list[str],
) -> pd.DataFrame:
    filtered = frame.copy()
    if filtered.empty:
        return filtered
    if decision_area and "review_area" in filtered:
        filtered = filtered[filtered["review_area"].isin(decision_area)]
    if decision_area and "decision_area" in filtered:
        filtered = filtered[filtered["decision_area"].isin(decision_area)]
    if picks:
        pick_columns = [
            column
            for column in ("related_pick_label", "pick_label", "entity_label")
            if column in filtered
        ]
        if pick_columns:
            mask = False
            for column in pick_columns:
                mask = mask | filtered[column].isin(picks)
            filtered = filtered[mask]
    if positions and "position" in filtered:
        filtered = filtered[filtered["position"].isin(positions)]
    band_column = _first_existing_column(filtered, ("review_band", "primary_review_band"))
    if bands and band_column:
        filtered = filtered[filtered[band_column].isin(bands)]
    warning_column = _first_existing_column(
        filtered,
        ("confidence_or_risk_warnings", "warning_flags", "warning_code"),
    )
    if warning_terms and warning_column:
        mask = False
        for term in warning_terms:
            mask = mask | filtered[warning_column].astype(str).str.contains(
                term,
                case=False,
                regex=False,
            )
        filtered = filtered[mask]
    return filtered


def _first_existing_column(frame: pd.DataFrame, candidates: tuple[str, ...]) -> str:
    return next((column for column in candidates if column in frame), "")


def _options(*frames: pd.DataFrame, columns: tuple[str, ...]) -> list[str]:
    values: set[str] = set()
    for frame in frames:
        for column in columns:
            if column in frame:
                values.update(value for value in frame[column].dropna().astype(str) if value)
    return sorted(values)


def _warning_options(*frames: pd.DataFrame) -> list[str]:
    values: set[str] = set()
    for frame in frames:
        for column in ("confidence_or_risk_warnings", "warning_flags", "warning_code"):
            if column not in frame:
                continue
            for text in frame[column].dropna().astype(str):
                values.update(flag for flag in text.split("|") if flag)
    return sorted(values)


def _humanize_code(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace("_", " ").replace("|", ", ")


def _friendly_area(value: object) -> str:
    text = str(value or "")
    return AREA_LABELS.get(text, _humanize_code(text))


def _friendly_band(value: object) -> str:
    text = str(value or "")
    return BAND_LABELS.get(text, _humanize_code(text))


def _friendly_warning(value: object) -> str:
    text = str(value or "")
    return WARNING_LABELS.get(text, human_label(text))


def _warning_summary(value: object) -> str:
    flags = [flag for flag in str(value or "").split("|") if flag]
    if not flags:
        return "No specific warning flags."
    friendly = [_friendly_warning(flag) for flag in flags[:4]]
    if len(flags) > 4:
        friendly.append(f"{len(flags) - 4} more")
    return "; ".join(friendly)


def _warning_group_summary(value: object) -> str:
    flags = [flag.strip() for flag in str(value or "").split("|") if flag.strip()]
    if not flags:
        return "No major warning group."
    groups: list[str] = []
    for label, patterns in WARNING_GROUP_RULES:
        if any(any(pattern in flag for pattern in patterns) for flag in flags):
            groups.append(label)
    if not groups:
        groups.append("General review note")
    return "; ".join(dict.fromkeys(groups))


def _display_cards_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    output = pd.DataFrame()
    output["Area"] = frame.get("review_area", "").map(_friendly_area)
    output["Item"] = frame.get("entity_label", "")
    output["Pos"] = frame.get("position", "")
    output["Status"] = frame.get("review_band", "").map(_friendly_band)
    output["What the model says"] = frame.get("model_says", "")
    output["What you decide"] = frame.get("human_needs_to_decide", "")
    output["Warning Groups"] = frame.get("confidence_or_risk_warnings", "").map(
        _warning_group_summary
    )
    output["Warning Details"] = frame.get("confidence_or_risk_warnings", "").map(
        _warning_summary
    )
    return output


def _display_opportunity_cost_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    output = pd.DataFrame()
    output["Player"] = frame.get("player_name", "")
    output["Pos"] = frame.get("position", "")
    output["Score"] = frame.get("current_model_score", "")
    output["Context Slot"] = frame.get("startup_slot_rank", "")
    output["Pick Equivalent"] = frame.get("rookie_pick_equivalent", "")
    output["Baseline Status"] = frame.get("pick_baseline_status", "").map(_friendly_band)
    output["Equivalent Trust"] = frame.get("pick_equivalent_confidence", "").map(_friendly_band)
    output["Equivalent Warning"] = frame.get("pick_equivalent_warning", "").map(
        _warning_summary
    )
    output["Nearest Rookies Above"] = frame.get("nearest_rookies_above", "")
    output["Nearest Rookies Below"] = frame.get("nearest_rookies_below", "")
    output["Nearby Replacements"] = frame.get("replacement_options_nearby", "")
    output["Pressure"] = frame.get("pressure_status", "").map(_friendly_band)
    output["Trade Context"] = frame.get("trade_context_status", "").map(_friendly_band)
    output["Cut Cost Label"] = frame.get("opportunity_cost_label", "").map(_friendly_band)
    output["Review Note"] = frame.get("opportunity_cost_note", "")
    output["Warning Groups"] = frame.get("warning_flags", "").map(_warning_group_summary)
    output["Warning Details"] = frame.get("warning_flags", "").map(_warning_summary)
    return output


def _filter_opportunity_cost(
    frame: pd.DataFrame,
    *,
    positions: list[str],
    bands: list[str],
    warning_terms: list[str],
) -> pd.DataFrame:
    if frame.empty:
        return frame
    filtered = frame.copy()
    if positions and "position" in filtered:
        filtered = filtered[filtered["position"].isin(positions)]
    if bands and "opportunity_cost_label" in filtered:
        filtered = filtered[filtered["opportunity_cost_label"].isin(bands)]
    if warning_terms and "warning_flags" in filtered:
        mask = False
        for term in warning_terms:
            mask = mask | filtered["warning_flags"].astype(str).str.contains(
                term,
                case=False,
                regex=False,
            )
        filtered = filtered[mask]
    return filtered


def _opportunity_by_player(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if frame.empty or "player_name" not in frame:
        return {}
    return {
        _normalize_name(row.get("player_name")): dict(row)
        for _, row in frame.iterrows()
        if _normalize_name(row.get("player_name"))
    }


def _sort_opportunity_for_cut_review(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    sorted_frame = frame.copy()
    sorted_frame["_score"] = pd.to_numeric(
        sorted_frame.get("current_model_score", 0), errors="coerce"
    ).fillna(0)
    sorted_frame["_slot"] = pd.to_numeric(
        sorted_frame.get("startup_slot_rank", 9999), errors="coerce"
    ).fillna(9999)
    return sorted_frame.sort_values(
        by=["_score", "_slot", "player_name"],
        ascending=[False, True, True],
        kind="stable",
    )


def _opportunity_subset(
    frame: pd.DataFrame,
    labels: set[str],
    *,
    limit: int = 4,
) -> pd.DataFrame:
    if frame.empty or "opportunity_cost_label" not in frame:
        return pd.DataFrame()
    subset = frame[frame["opportunity_cost_label"].isin(labels)]
    return _sort_opportunity_for_cut_review(subset).head(limit)


def _review_priority_roster_rows(
    roster_frame: pd.DataFrame,
    opportunity_frame: pd.DataFrame,
) -> pd.DataFrame:
    if roster_frame.empty:
        return pd.DataFrame()
    rows = roster_frame.copy()
    band_weight = {
        "required_pressure_zone_review": 0,
        "protectable_depth_review": 1,
        "pressure_shop_watch_review": 2,
        "rookie_pick_equivalent_uncertain": 3,
        "protected_core_review": 4,
    }
    rows["_band_weight"] = rows.get("review_band", "").map(
        lambda value: band_weight.get(str(value), 9)
    )
    rows["_player_key"] = rows.get("entity_label", "").map(_normalize_name)
    opportunity_lookup = _opportunity_by_player(opportunity_frame)
    rows["_score"] = rows["_player_key"].map(
        lambda key: float(opportunity_lookup.get(key, {}).get("current_model_score") or 0)
    )
    return rows.sort_values(
        by=["_band_weight", "_score", "entity_label"],
        ascending=[True, True, True],
        kind="stable",
    ).head(8)


def _render_plain_candidate_cards(
    roster_frame: pd.DataFrame,
    opportunity_frame: pd.DataFrame,
    *,
    age_lookup: dict[str, str],
) -> None:
    section_label("Normal Cut Candidates")
    st.caption(
        "These are the first pressure rows to review. They are not cut calls."
    )
    priority_rows = _review_priority_roster_rows(roster_frame, opportunity_frame)
    if priority_rows.empty:
        st.info("No roster-pressure cards are available.")
        return

    opportunity_lookup = _opportunity_by_player(opportunity_frame)
    for row_group_start in range(0, len(priority_rows), 2):
        columns = st.columns(2)
        for column, (_, row) in zip(
            columns,
            priority_rows.iloc[row_group_start : row_group_start + 2].iterrows(),
            strict=False,
        ):
            player = str(row.get("entity_label") or "")
            opportunity = opportunity_lookup.get(_normalize_name(player), {})
            score = _format_number(opportunity.get("current_model_score"))
            slot = str(opportunity.get("startup_slot_rank") or "n/a")
            pick_equivalent = str(opportunity.get("rookie_pick_equivalent") or "No pick context")
            cut_label = _friendly_band(opportunity.get("opportunity_cost_label"))
            warnings = _warning_group_summary(
                opportunity.get("warning_flags") or row.get("confidence_or_risk_warnings")
            )
            human_check = str(row.get("human_needs_to_decide") or "")
            age_text = _display_age(player, age_lookup)
            position = row.get("position", "")
            team = opportunity.get("nfl_team") or row.get("nfl_team") or "Team missing"
            title_html = (
                f"{_safe_html(player)} &middot; {_safe_html(position)} &middot; "
                f"{_safe_html(team)} &middot; Age {_safe_html(age_text)}"
            )
            human_check_html = _safe_html(_short_text(human_check, max_length=170))
            with column:
                st.markdown(
                    f"""
                    <div class="nwr-card">
                      <div class="nwr-card-kicker">{_safe_html(cut_label)}</div>
                      <div class="nwr-card-title">{title_html}</div>
                      <div class="nwr-card-body">
                        <strong>Model value:</strong> {_safe_html(score or "n/a")} &middot;
                        <strong>Internal slot:</strong> {_safe_html(slot)}<br>
                        <strong>Rookie pick equivalent:</strong> {_safe_html(pick_equivalent)}<br>
                        <strong>Top risk:</strong> {_safe_html(warnings)}<br>
                        <strong>Human check:</strong> {human_check_html}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_player_detail_panel(
                    PlayerDetail(
                        player=player,
                        age=age_text,
                        position=position,
                        nfl_team=team,
                        model_value=score,
                        rank_or_slot=slot,
                        rookie_pick_equivalent=pick_equivalent,
                        trust_status=row.get("confidence_or_risk_warnings"),
                        why_this_rank=human_check,
                        strongest_signals=cut_label,
                        weakest_signals=warnings,
                        warning_groups=(
                            opportunity.get("warning_flags")
                            or row.get("confidence_or_risk_warnings")
                        ),
                        nearby_context=opportunity.get("replacement_options_nearby"),
                        receipt_pointer=row.get("receipt_pointer"),
                        source_pointer=opportunity.get("formula_version"),
                    ),
                    label=f"Inspect {player}",
                    key=f"normal_cut_detail_{_normalize_name(player)}",
                )


def _render_opportunity_cards(
    frame: pd.DataFrame,
    *,
    age_lookup: dict[str, str],
    section_title: str,
    section_caption: str,
    empty_message: str,
) -> None:
    section_label(section_title)
    st.caption(section_caption)
    if frame.empty:
        st.info(empty_message)
        return

    for row_group_start in range(0, len(frame), 2):
        columns = st.columns(2)
        for column, (_, row) in zip(
            columns,
            frame.iloc[row_group_start : row_group_start + 2].iterrows(),
            strict=False,
        ):
            player = str(row.get("player_name") or "")
            position = str(row.get("position") or "")
            team = str(row.get("nfl_team") or "Team missing")
            score = _format_number(row.get("current_model_score"))
            slot = str(row.get("startup_slot_rank") or "n/a")
            pick_equivalent = str(
                row.get("rookie_pick_equivalent") or "No pick context"
            )
            cut_label = _friendly_band(row.get("opportunity_cost_label"))
            warnings = _warning_group_summary(row.get("warning_flags"))
            human_check = str(row.get("opportunity_cost_note") or "")
            age_text = _display_age(player, age_lookup)
            title_html = (
                f"{_safe_html(player)} &middot; {_safe_html(position)} &middot; "
                f"{_safe_html(team)} &middot; Age {_safe_html(age_text)}"
            )
            human_check_html = _safe_html(_short_text(human_check, max_length=170))
            with column:
                st.markdown(
                    f"""
                    <div class="nwr-card">
                      <div class="nwr-card-kicker">{_safe_html(cut_label)}</div>
                      <div class="nwr-card-title">{title_html}</div>
                      <div class="nwr-card-body">
                        <strong>Model value:</strong> {_safe_html(score or "n/a")} &middot;
                        <strong>Internal slot:</strong> {_safe_html(slot)}<br>
                        <strong>Rookie pick equivalent:</strong> {_safe_html(pick_equivalent)}<br>
                        <strong>Top risk:</strong> {_safe_html(warnings)}<br>
                        <strong>Human check:</strong> {human_check_html}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_player_detail_panel(
                    PlayerDetail(
                        player=player,
                        age=age_text,
                        position=position,
                        nfl_team=team,
                        model_value=score,
                        rank_or_slot=slot,
                        rookie_pick_equivalent=pick_equivalent,
                        trust_status=row.get("pressure_status"),
                        why_this_rank=human_check,
                        strongest_signals=cut_label,
                        weakest_signals=warnings,
                        warning_groups=row.get("warning_flags"),
                        nearby_context=(
                            f"Above: {row.get('nearest_rookies_above') or 'Missing'}; "
                            f"Below: {row.get('nearest_rookies_below') or 'Missing'}"
                        ),
                        receipt_pointer=row.get("receipt_pointer"),
                        source_pointer=row.get("formula_version"),
                    ),
                    label=f"Inspect {player}",
                    key=f"opportunity_detail_{_normalize_name(player)}",
                )


def _render_trade_check_cards(
    opportunity_frame: pd.DataFrame,
    *,
    age_lookup: dict[str, str],
) -> None:
    frame = _opportunity_subset(
        opportunity_frame,
        {"expensive_to_cut", "trade_context_before_cut_review"},
        limit=4,
    )
    _render_opportunity_cards(
        frame,
        age_lookup=age_lookup,
        section_title="Do Not Cut Without Trade Check",
        section_caption=(
            "These players carry enough internal value or uncertainty that the board "
            "should check trade/replacement context before any cut discussion."
        ),
        empty_message="No trade-check-first players are available.",
    )


def _render_cut_cost_context_cards(
    opportunity_frame: pd.DataFrame,
    *,
    age_lookup: dict[str, str],
) -> None:
    frame = _opportunity_subset(
        opportunity_frame,
        {"replaceable_depth", "rookie_pick_equivalent_uncertain"},
        limit=4,
    )
    _render_opportunity_cards(
        frame,
        age_lookup=age_lookup,
        section_title="Cut Cost / Replacement Context",
        section_caption=(
            "These cards show what the model thinks the roster spot costs in internal "
            "slot and rookie-pick-equivalent terms. Missing exact pick baselines stay "
            "manual-only."
        ),
        empty_message="No cut-cost context rows are available.",
    )


def _render_decision_start_here(
    strategy: object,
    roster_frame: pd.DataFrame,
    opportunity_frame: pd.DataFrame,
) -> None:
    rows = list(getattr(strategy, "niners_action_rows", []) or [])
    default_rows = [row for row in rows if bool(row.get("is_default_release"))]
    priority_rows = _review_priority_roster_rows(roster_frame, opportunity_frame)
    first_candidate = (
        str(priority_rows.iloc[0].get("entity_label"))
        if not priority_rows.empty
        else "No pressure row"
    )
    top_five_player = (
        str(default_rows[0].get("player"))
        if default_rows
        else "No active top-five release slot"
    )
    columns = st.columns(3)
    columns[0].metric("Top-Five Rule Slot", top_five_player)
    columns[1].metric("First Normal Cut Review", first_candidate)
    columns[2].metric("Final Calls Created", "No")
    st.caption(
        "Use this page in order: confirm the special top-five rule slot, inspect the "
        "normal cut candidates, then check cut cost before any human decision. Raw "
        "rows and receipts are under Advanced."
    )


def _render_cards_table(frame: pd.DataFrame, key: str) -> None:
    if frame.empty:
        st.info("No rows match the current filters.")
        return
    st.caption("Quick read")
    for index, row in _display_cards_frame(frame).head(12).iterrows():
        st.markdown(
            "\n".join(
                [
                    f"**{row['Item']}**",
                    f"- **Area:** {row['Area']} | **Status:** {row['Status']}",
                    f"- **What the model says:** {row['What the model says']}",
                    f"- **What you decide:** {row['What you decide']}",
                    f"- **Warning groups:** {row['Warning Groups']}",
                ]
            )
        )
        if index < min(len(frame), 12) - 1:
            st.divider()
    if len(frame) > 12:
        st.caption(f"Showing first 12 quick cards. Table below contains all {len(frame)} rows.")
    st.dataframe(
        _display_cards_frame(frame),
        width="stretch",
        hide_index=True,
        key=key,
    )
    with st.expander("Advanced: technical card rows"):
        columns = [column for column in CARD_COLUMNS if column in frame]
        st.dataframe(
            frame.reindex(columns=columns),
            width="stretch",
            hide_index=True,
            key=f"{key}_technical",
        )


def _render_download(frame: pd.DataFrame, label: str, file_name: str, key: str) -> None:
    if frame.empty:
        return
    st.download_button(
        label,
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
        key=key,
    )


def _metric(label: str, value: object) -> None:
    st.metric(label, str(value))


def _normalize_name(value: object) -> str:
    return "".join(character for character in str(value or "").lower() if character.isalnum())


def _age_lookup(frame: pd.DataFrame) -> dict[str, str]:
    if frame.empty:
        return {}
    output: dict[str, str] = {}
    for _, row in frame.iterrows():
        key = str(row.get("normalized_player_name") or _normalize_name(row.get("player")))
        age = str(row.get("age_years_decimal") or row.get("age_years") or "").strip()
        if key and age:
            output[key] = age
    return output


def _display_age(player_name: object, lookup: dict[str, str]) -> str:
    age = lookup.get(_normalize_name(player_name), "")
    if not age:
        return "Age missing"
    try:
        return f"{float(age):.1f}"
    except ValueError:
        return age


def _short_text(value: object, *, max_length: int = 150) -> str:
    text = str(value or "").strip()
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3].rstrip()}..."


def _safe_html(value: object) -> str:
    return html.escape(str(value or "").strip())


@st.cache_data
def _load_forced_release_strategy(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint
    return build_forced_release_strategy(active_data_pack)


def _yes_no_label(value: object) -> str:
    return "Current top-five drop slot" if bool(value) else "Top-five candidate"


def _format_number(value: object) -> str:
    try:
        if value in (None, ""):
            return ""
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return str(value or "")


def _top_five_drop_frame(
    rows: list[dict[str, object]],
    age_lookup: dict[str, str] | None = None,
) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    age_lookup = age_lookup or {}
    frame = pd.DataFrame(rows).copy()
    frame = frame.sort_values(
        by=["is_default_release", "league_rank"],
        ascending=[False, True],
        kind="stable",
    )
    output = pd.DataFrame()
    output["Status"] = frame.get("is_default_release", False).map(_yes_no_label)
    output["Player"] = frame.get("player", "")
    output["Age"] = frame.get("player", "").map(lambda player: _display_age(player, age_lookup))
    output["Pos"] = frame.get("pos", "")
    output["League Rank"] = frame.get("league_rank", "")
    output["Model Value"] = frame.get("likely_target_value", "").map(_format_number)
    output["Release Pain"] = frame.get("forced_release_pain", "").map(_format_number)
    output["Gap vs Easy Drop"] = frame.get("top_five_value_gap", "").map(_format_number)
    output["Easy Non-Top-Five Drop"] = frame.get("easy_non_top_five_drop", "")
    output["Rule Explanation"] = frame.get("rule_explanation", "")
    return output


def _render_top_five_drop_decision(
    strategy: object,
    *,
    age_lookup: dict[str, str],
) -> None:
    rows = list(getattr(strategy, "niners_action_rows", []) or [])
    default_rows = [row for row in rows if bool(row.get("is_default_release"))]
    section_label("Top-Five Drop Rule")
    st.info(
        "This is the specific league-rule question: from your roster's five highest "
        "league-ranked players, which one is the current Required Top-Five Release "
        "Slot? It is separate from the generic roster-pressure cut list."
    )
    if not rows:
        st.warning(
            "No top-five rule rows are available from the active data pack. Check "
            "the My Team page or active snapshot before using this page for the "
            "top-five decision."
        )
        return

    if default_rows:
        release_row = default_rows[0]
        release_player = str(release_row.get("player") or "Unknown")
        easy_drop = str(release_row.get("easy_non_top_five_drop") or "No comparison row")
        pain = _format_number(release_row.get("forced_release_pain"))
        gap = _format_number(release_row.get("top_five_value_gap"))
        metric_cols = st.columns(4)
        metric_cols[0].metric("Current Rule Slot", release_player)
        metric_cols[1].metric("Release Pain", pain or "n/a")
        metric_cols[2].metric("Easy Non-Top-Five Drop", easy_drop)
        metric_cols[3].metric("Value Gap", gap or "n/a")
        st.warning(
            f"Review-only read: **{release_player}** is currently the Required "
            "Top-Five Release Slot. The comparison non-top-five drop is "
            f"**{easy_drop}**, but that comparison does **not** satisfy the "
            "top-five rule by itself."
        )
    else:
        st.success("No Required Top-Five Release Slot is active from the current data pack.")

    st.dataframe(
        _top_five_drop_frame(rows, age_lookup),
        width="stretch",
        hide_index=True,
        key="june15_top_five_drop_decision_table",
    )
    with st.expander("Advanced: technical top-five rule rows"):
        st.dataframe(
            pd.DataFrame(rows),
            width="stretch",
            hide_index=True,
            key="june15_top_five_drop_decision_technical_rows",
        )


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_data_pack_fingerprint = path_fingerprint(active_data_pack)
forced_release_strategy = _load_forced_release_strategy(
    active_data_pack,
    active_data_pack_fingerprint,
)

summary = _frame(PREP_SUMMARY)
pick_cards = _frame(PICK_CARDS)
roster_cards = _frame(ROSTER_CARDS)
trade_cards = _frame(TRADE_CARDS)
rookie_queue = _frame(ROOKIE_QUEUE)
veteran_cards = _frame(VETERAN_CARDS)
focus_rows = _frame(SPRINT1_FOCUS)
board_rows = _frame(BOARD_ROWS)
board_warnings = _frame(BOARD_WARNINGS)
board_receipts = _frame(BOARD_RECEIPTS)
pressure_rows = _frame(PRESSURE_ROWS)
trade_away_rows = _frame(TRADE_AWAY_ROWS)
external_asset_rows = _frame(EXTERNAL_ASSET_ROWS)
pick_rows = _frame(PICK_ROWS)
defer_rows = _frame(PICK_DEFER_ROWS)
rookie_candidate_rows = _frame(ROOKIE_CANDIDATE_ROWS)
opportunity_cost_rows = _frame(OPPORTUNITY_COST_ROWS)
opportunity_cost_component_rows = _frame(OPPORTUNITY_COST_COMPONENT_ROWS)
opportunity_cost_warning_rows = _frame(OPPORTUNITY_COST_WARNING_ROWS)
age_rows = _frame(AGE_ROWS)
player_age_lookup = _age_lookup(age_rows)

page_header(
    "Decision Board",
    eyebrow="June 15 Review-Only Deadline Board",
    description=(
        "Start with the actual roster deadline problem: the top-five rule slot, "
        "the first drop-pressure players, and what it costs to cut anyone. "
        "Everything else is supporting context."
    ),
    status_items=(
        ("Review-only", "review"),
        ("No My Team mutation", "safe"),
        ("No War Board mutation", "safe"),
        ("No final recommendations", "blocked"),
    ),
)
st.warning(REVIEW_ONLY_SURFACE_BANNER)

if summary.empty:
    st.error(
        "Human decision review prep outputs are missing. Run "
        "`python scripts/build_model_v4_human_decision_review_prep.py` first."
    )
    st.stop()

summary_map = dict(zip(summary["summary_key"], summary["summary_value"], strict=False))

_render_decision_start_here(
    forced_release_strategy,
    roster_cards,
    opportunity_cost_rows,
)
_render_top_five_drop_decision(
    forced_release_strategy,
    age_lookup=player_age_lookup,
)
_render_plain_candidate_cards(
    roster_cards,
    opportunity_cost_rows,
    age_lookup=player_age_lookup,
)
_render_trade_check_cards(opportunity_cost_rows, age_lookup=player_age_lookup)
_render_cut_cost_context_cards(opportunity_cost_rows, age_lookup=player_age_lookup)

with st.expander("Review-only status and output counts", expanded=False):
    st.warning(
        "Review-only surface. Use this to inspect evidence, warnings, and receipt "
        "pointers. Do not treat any row as a final action."
    )
    metric_cols = st.columns(6)
    with metric_cols[0]:
        _metric("Pick Cards", summary_map.get("pick_review_cards", 0))
    with metric_cols[1]:
        _metric("Roster Cards", summary_map.get("roster_pressure_review_cards", 0))
    with metric_cols[2]:
        _metric("External Asset Cards", summary_map.get("trade_review_cards", 0))
    with metric_cols[3]:
        _metric("Scout Queue", summary_map.get("rookie_manual_scout_queue_rows", 0))
    with metric_cols[4]:
        _metric("Veteran Risk", summary_map.get("veteran_risk_review_cards", 0))
    with metric_cols[5]:
        _metric("Final Calls", summary_map.get("final_recommendations_created", "False"))

st.caption("Review progress: Start Here -> Drop Candidates -> Cut Cost -> Context -> Advanced.")
with st.expander("June 15 review progress checklist", expanded=False):
    st.markdown(
        """
        **Start Here**

        1. **Top-Five Drop Decision**
           Confirm the special deadline slot first. It is separate from the normal
           roster-pressure cut list.
           Human question: what must be reviewed before any normal cut logic?

        **Main Review**

        2. **Pick & Roster Review**
           Check owned picks, roster pressure, and manual-only 5.04 context.
           Human question: which roster and pick rows need a final human pass?

        3. **Cut Cost**
           Review what model value would leave the roster if a player is dropped.
           Human question: what opportunity cost would the roster lose?

        **Supporting Context**

        4. **External Asset & Rookie Context**
           Use as supporting context for conversations and draft prep.
           Human question: does context change what needs manual review?

        **Receipts / Advanced**

        5. **Advanced**
           Open receipts, warnings, and raw rows only when a card needs backup.
           Human question: what evidence explains the row?

        This page prepares the review. It does not make the final cut, keep,
        trade, timing, or draft call.
        """
    )

with st.expander("What this page is for", expanded=False):
    st.markdown(
        """
        Use this page to answer one simple question: **what do I need to review before
        June 15?**

        - **Pick review** means decide whether to use, move down, or hold timing on a pick.
        - **Top-five drop** means the special league-rule slot. It is not the same
          as the easiest normal roster cut.
        - **Roster pressure** means review players who may matter for cuts or roster spots.
        - **External asset context** means possible conversations, not offers.
        - **Rookie scout queue** means names the model surfaced but humans must verify.
        - **Veteran risk** means age, role, QB/TE format, or window questions.

        The plain-English tables are the main view. The technical rows are kept in
        advanced sections only so receipts are still available.
        """
    )

with st.expander("Audit notes to keep in mind", expanded=False):
    st.markdown(
        """
        - Route, usage-share, and snap gaps lower confidence; they are not zero evidence.
        - Aging veterans need manual review when age-cliff or rushing-age guardrails
          are unavailable.
        - TE scores are disciplined for **no TE premium**, but still require a human check if a TE
          appears near RB/WR values.
        - Market, ADP, rankings, and projections remain context only and do not change Model Value.
        """
    )

all_card_rows = pd.concat(
    [pick_cards, roster_cards, trade_cards, rookie_queue, veteran_cards],
    ignore_index=True,
)

with st.expander("Filters", expanded=False):
    filter_cols = st.columns(5)
    with filter_cols[0]:
        selected_areas = st.multiselect(
            "Decision area",
            _options(
                all_card_rows, board_rows, columns=("review_area", "decision_area")
            ),
            format_func=_friendly_area,
            key="june15_decision_area_filter",
        )
    with filter_cols[1]:
        selected_picks = st.multiselect(
            "Pick",
            _options(
                all_card_rows,
                board_rows,
                rookie_candidate_rows,
                columns=("related_pick_label", "pick_label", "entity_label"),
            ),
            key="june15_pick_filter",
        )
    with filter_cols[2]:
        selected_positions = st.multiselect(
            "Position",
            _options(
                all_card_rows, board_rows, opportunity_cost_rows, columns=("position",)
            ),
            key="june15_position_filter",
        )
    with filter_cols[3]:
        selected_bands = st.multiselect(
            "Review band",
            _options(
                all_card_rows,
                board_rows,
                opportunity_cost_rows,
                columns=(
                    "review_band",
                    "primary_review_band",
                    "opportunity_cost_label",
                ),
            ),
            format_func=_friendly_band,
            key="june15_review_band_filter",
        )
    with filter_cols[4]:
        selected_warnings = st.multiselect(
            "Warning type",
            _warning_options(
                all_card_rows,
                board_rows,
                board_warnings,
                opportunity_cost_rows,
                opportunity_cost_warning_rows,
            ),
            format_func=_friendly_warning,
            key="june15_warning_filter",
        )

filtered_cards = _filter_frame(
    all_card_rows,
    decision_area=selected_areas,
    picks=selected_picks,
    positions=selected_positions,
    bands=selected_bands,
    warning_terms=selected_warnings,
)

tabs = st.tabs(
    [
        "Pick & Roster Review",
        "Cut Cost",
        "External Asset & Rookie Context",
        "Advanced",
    ]
)

with tabs[0]:
    section_label("Pick Review Cards")
    filtered = _filter_frame(
        pick_cards,
        decision_area=selected_areas,
        picks=selected_picks,
        positions=selected_positions,
        bands=selected_bands,
        warning_terms=selected_warnings,
    )
    _render_cards_table(filtered, "june15_pick_cards")
    section_label("Roster Pressure")
    filtered = _filter_frame(
        roster_cards,
        decision_area=selected_areas,
        picks=selected_picks,
        positions=selected_positions,
        bands=selected_bands,
        warning_terms=selected_warnings,
    )
    _render_cards_table(filtered, "june15_roster_cards")
    section_label("Veteran Risk")
    filtered = _filter_frame(
        veteran_cards,
        decision_area=selected_areas,
        picks=selected_picks,
        positions=selected_positions,
        bands=selected_bands,
        warning_terms=selected_warnings,
    )
    _render_cards_table(filtered, "june15_veteran_cards")
    _render_download(
        filtered_cards,
        "Download filtered review cards",
        "filtered_human_decision_review_cards.csv",
        "download_filtered_review_cards",
    )

with tabs[1]:
    section_label("Cut Cost")
    st.caption(
        "Shows what each roster player costs in internal slot and rookie-pick "
        "terms. Labels are review context only, not cut/keep instructions."
    )
    filtered_opportunity = _filter_opportunity_cost(
        opportunity_cost_rows,
        positions=selected_positions,
        bands=selected_bands,
        warning_terms=selected_warnings,
    )
    if filtered_opportunity.empty:
        st.info("No opportunity-cost rows match the current filters.")
    else:
        st.dataframe(
            _display_opportunity_cost_frame(filtered_opportunity),
            width="stretch",
            hide_index=True,
        )
        _render_download(
            filtered_opportunity,
            "Download opportunity-cost rows",
            "filtered_roster_opportunity_cost.csv",
            "download_filtered_roster_opportunity_cost",
        )

with tabs[2]:
    section_label("External Asset Context")
    filtered = _filter_frame(
        trade_cards,
        decision_area=selected_areas,
        picks=selected_picks,
        positions=selected_positions,
        bands=selected_bands,
        warning_terms=selected_warnings,
    )
    _render_cards_table(filtered, "june15_trade_cards")
    section_label("Rookie Candidate Windows")
    filtered = _filter_frame(
        rookie_queue,
        decision_area=selected_areas,
        picks=selected_picks,
        positions=selected_positions,
        bands=selected_bands,
        warning_terms=selected_warnings,
    )
    _render_cards_table(filtered, "june15_rookie_queue")

with tabs[3]:
    section_label("Warning And Receipt Drilldowns")
    warning_frame = _filter_frame(
        board_warnings,
        decision_area=selected_areas,
        picks=selected_picks,
        positions=selected_positions,
        bands=selected_bands,
        warning_terms=selected_warnings,
    )
    st.caption("Sprint 14F warnings")
    warning_display = warning_frame.copy()
    if not warning_display.empty and "warning_code" in warning_display:
        warning_display["plain_english_warning"] = warning_display["warning_code"].map(
            _friendly_warning
        )
    st.dataframe(warning_display, width="stretch", hide_index=True)
    with st.expander("Advanced: Sprint 14F receipts"):
        st.dataframe(board_receipts, width="stretch", hide_index=True)
    with st.expander("Advanced: Sprint 1 focus rows"):
        st.dataframe(focus_rows, width="stretch", hide_index=True)
    with st.expander("Advanced: pick inventory source rows"):
        st.dataframe(pick_rows, width="stretch", hide_index=True)
    with st.expander("Advanced: pick timing source rows"):
        st.dataframe(defer_rows, width="stretch", hide_index=True)
    with st.expander("Advanced: source pressure rows"):
        st.dataframe(pressure_rows, width="stretch", hide_index=True)
    with st.expander("Advanced: external asset review source rows"):
        trade_tabs = st.tabs(["Roster Pressure Context", "External Asset Context"])
        with trade_tabs[0]:
            st.dataframe(trade_away_rows, width="stretch", hide_index=True)
        with trade_tabs[1]:
            st.dataframe(external_asset_rows, width="stretch", hide_index=True)
    with st.expander("Advanced: source rookie pick windows"):
        st.dataframe(rookie_candidate_rows, width="stretch", hide_index=True)
    with st.expander("Advanced: opportunity-cost components"):
        st.dataframe(opportunity_cost_component_rows, width="stretch", hide_index=True)
    with st.expander("Advanced: opportunity-cost warnings"):
        st.dataframe(opportunity_cost_warning_rows, width="stretch", hide_index=True)
    with st.expander("Advanced: raw June 15 decision board"):
        raw_filtered = _filter_frame(
            board_rows,
            decision_area=selected_areas,
            picks=selected_picks,
            positions=selected_positions,
            bands=selected_bands,
            warning_terms=selected_warnings,
        )
        st.dataframe(raw_filtered, width="stretch", hide_index=True)
        _render_download(
            raw_filtered,
            "Download filtered raw board",
            "filtered_june15_decision_board.csv",
            "download_filtered_raw_board",
        )
