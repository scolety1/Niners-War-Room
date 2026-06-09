from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.model_v4_receipts import render_model_v4_shadow_receipt_drilldown
from app.components.trust_status import render_page_trust_banner
from src.config.settings import get_settings
from src.services.command_board_service import (
    TEAM_COLUMN_LABELS,
    TEAM_DECISION_COLUMNS,
    build_team_command_board,
)
from src.services.data_pack_health_service import build_data_pack_health_report
from src.services.forced_release_strategy_service import build_forced_release_strategy
from src.services.legacy_label_quarantine_service import (
    label_quarantine_notice,
    legacy_label_quarantine_active,
    quarantine_legacy_label,
)
from src.services.model_v4_app_review_service import (
    DEFAULT_MODEL_V4_NAMED_PATH,
    DEFAULT_MODEL_V4_PREVIEW_ROOT,
    DEFAULT_MODEL_V4_SANITY_PATH,
    MODEL_V4_SHADOW_MY_TEAM_BANNER,
    MODEL_V4_SHADOW_MY_TEAM_COLUMNS,
    MODEL_V4_SHADOW_MY_TEAM_LABELS,
    build_model_v4_app_review,
    build_model_v4_shadow_my_team_rows,
)
from src.services.model_v4_roster_rank_contract_service import (
    OFFICIAL_NINERS_ROSTER_RANK_PATH,
    validate_official_roster_rank_contract,
)
from src.services.my_team_decision_receipts_service import build_my_team_decision_receipts
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    RECEIPT_COLUMN_LABELS,
    RECEIPT_DISPLAY_COLUMNS,
    build_player_feature_receipts,
    component_summary_rows_for_players,
    receipt_rows_for_players,
)
from src.services.ranking_readiness_service import build_ranking_readiness
from src.services.roster_decision_readiness_service import (
    build_roster_decision_readiness,
    roster_decision_gate_rows,
)
from src.services.table_sort_service import sort_caption

MY_TEAM_UI_REVISION = "my_team_decision_audit_20260515"


def _display_label(label: object) -> str:
    return quarantine_legacy_label(label)


def _team_label(column: str) -> str:
    return TEAM_COLUMN_LABELS.get(column, column.replace("_", " ").title())


def _receipt_text(
    receipt: dict[str, object],
    key: str,
    default: str = "Not available.",
) -> str:
    value = receipt.get(key)
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return str(value)


def _receipt_for_player(
    receipts: list[dict[str, object]],
    player: object,
) -> dict[str, object] | None:
    player_name = str(player or "")
    for receipt in receipts:
        if str(receipt.get("player") or "") == player_name:
            return receipt
    return None


def _number_text(value: object, *, default: str = "n/a") -> str:
    try:
        if value in (None, ""):
            return default
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return default


def _selected_dataframe_rows(event: object) -> list[int]:
    try:
        selection = getattr(event, "selection", None)
        if selection is not None:
            rows = getattr(selection, "rows", None)
            if rows is not None:
                return [int(row) for row in rows]
        if isinstance(event, dict):
            rows = event.get("selection", {}).get("rows", [])
            return [int(row) for row in rows]
    except (TypeError, ValueError):
        return []
    return []


def _first_view_explanation(row: dict[str, object]) -> str:
    text = str(row.get("decision_explanation") or "").strip()
    if "Secondary context:" in text:
        return text.split("Secondary context:", 1)[0].strip()
    return text


def _confidence_text(
    row: dict[str, object],
    receipt: dict[str, object] | None,
) -> str:
    row_label = str(row.get("confidence_label") or "").strip()
    if row_label:
        return row_label
    if receipt is not None:
        receipt_label = str(receipt.get("confidence_label") or "").strip()
        if receipt_label and receipt_label != "unknown":
            return receipt_label
    try:
        score = float(row.get("confidence") or 0.0)
    except (TypeError, ValueError):
        return "unknown"
    if 0 < score <= 1:
        score *= 100.0
    if score >= 85:
        return "strong"
    if score >= 78:
        return "usable"
    if score >= 65:
        return "review"
    if score >= 40:
        return "weak"
    return "blocked"


def _section_caption(section_name: str) -> str:
    captions = {
        "Forced-Release Decision": (
            "This is the player currently satisfying the required release from "
            "the roster's league-rank top-five group."
        ),
        "Core Holds": "Players the current model says are clearly worth protecting.",
        "Needs Data Review": (
            "Do not act from the label alone. These rows need source or confidence "
            "review before they become real calls."
        ),
        "Bubble Players": "Close calls. Review receipts before deciding hold versus shop.",
        "Shop Candidates": "Players the model would explore moving before the deadline.",
        "Bench/Stash": "Lowest current roster priority or easiest cut/stash decisions.",
    }
    caption = captions.get(section_name, "")
    if legacy_label_quarantine_active() and section_name in {
        "Core Holds",
        "Bubble Players",
        "Shop Candidates",
        "Bench/Stash",
    }:
        return (
            "Legacy review bucket during Model v4 freeze. Inspect receipts; do not "
            "treat this as a trusted roster call. "
            + caption
        )
    return caption


def _render_receipt_detail(
    receipt: dict[str, object],
    *,
    section_name: str,
) -> None:
    top_five_rule = _receipt_text(receipt, "top_five_rule")
    recommendation = _receipt_text(receipt, "model_recommendation", "review")
    st.markdown(f"**Lifecycle**: {_receipt_text(receipt, 'lifecycle', 'Unknown')}")
    st.write(
        _receipt_text(
            receipt,
            "lifecycle_explanation",
            "Lifecycle explanation is not available for this row.",
        )
    )
    st.markdown(f"**Top-Five Rule Status**: {top_five_rule}")
    st.markdown(f"**Model Recommendation**: {recommendation}")
    if section_name == "Forced-Release Decision":
        st.write(
            _receipt_text(
                receipt,
                "release_pain_explanation",
                "Release-pain explanation is not available for this row.",
            )
        )
    st.markdown(
        "**Top Positive Drivers**: "
        + _receipt_text(
            receipt,
            "top_positive_drivers",
            "No positive receipt drivers available.",
        )
    )
    st.markdown(
        "**Top Negative Drivers**: "
        + _receipt_text(
            receipt,
            "top_negative_drivers",
            "No negative receipt drivers available.",
        )
    )
    st.markdown(
        "**Young Bridge Contribution**: "
        + _receipt_text(
            receipt,
            "bridge_prior",
            "No bridge-prior contribution shown.",
        )
    )
    st.markdown(
        "**Model vs Market**: "
        + _receipt_text(receipt, "market_edge", "No market edge available.")
    )
    st.markdown(
        "**Source Warnings**: "
        + _receipt_text(receipt, "source_warnings", "No active source warning.")
    )
    st.markdown(f"**Confidence**: {_receipt_text(receipt, 'confidence_label', 'unknown')}")
    st.write(
        _receipt_text(
            receipt,
            "confidence_explanation",
            "Confidence explanation is not available for this row.",
        )
    )


def _render_player_decision_card(
    row: dict[str, object],
    receipt: dict[str, object] | None,
    *,
    section_name: str,
) -> None:
    player = str(row.get("player") or "Unknown player")
    action = str(row.get("model_recommendation") or row.get("recommendation") or "review")
    action_label = _display_label(action)
    position = str(row.get("pos") or "")
    nfl_team = str(row.get("nfl_team") or "")
    lifecycle = str(row.get("asset_lifecycle_label") or "Unknown lifecycle")
    top_five_rule = str(row.get("top_five_rule") or "")
    explanation = _first_view_explanation(row)
    with st.container(border=True):
        name_col, value_col, risk_col, action_col = st.columns([2.7, 1.1, 1.1, 1.5])
        name_col.markdown(f"**{player}**")
        name_col.caption(" · ".join(part for part in (position, nfl_team, lifecycle) if part))
        value_col.metric("Model Value", _number_text(row.get("stats_value")))
        risk_col.metric(
            "Keep / Cut",
            f"{_number_text(row.get('keep_priority'))} / {_number_text(row.get('cut_risk'))}",
        )
        action_col.markdown(f"**{action_label.replace('_', ' ').title()}**")
        action_col.caption(f"Confidence: {_confidence_text(row, receipt)}")
        st.caption(top_five_rule)
        if explanation:
            st.write(explanation)
        if receipt:
            with st.expander("Why this call?"):
                _render_receipt_detail(receipt, section_name=section_name)
        else:
            st.caption("No compact receipt is available for this row.")


def _load_board(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_fingerprint: tuple[str, int, int, int],
    ui_revision: str,
):
    _ = data_pack_fingerprint, veteran_model_fingerprint, ui_revision
    return build_team_command_board(active_data_pack)


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


@st.cache_data
def _load_strategy(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_forced_release_strategy(active_data_pack)


@st.cache_data
def _load_feature_receipts(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_player_feature_receipts(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


def _load_roster_readiness(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
    ui_revision: str,
):
    _ = data_pack_fingerprint, veteran_model_fingerprint, ui_revision
    return build_roster_decision_readiness(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_model_v4_review(
    preview_root: str,
    preview_fingerprint: tuple[str, int, int, int],
    sanity_path: str,
    sanity_fingerprint: tuple[str, int, int, int],
    named_path: str,
    named_fingerprint: tuple[str, int, int, int],
):
    _ = preview_fingerprint, sanity_fingerprint, named_fingerprint
    return build_model_v4_app_review(preview_root, sanity_path, named_path)


@st.cache_data
def _load_v4_roster_rank_contract(
    roster_rank_path: str,
    roster_rank_fingerprint: tuple[str, int, int, int],
):
    _ = roster_rank_fingerprint
    return validate_official_roster_rank_contract(roster_rank_path)


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
veteran_model_fingerprint = path_fingerprint(DEFAULT_RECEIPT_VETERAN_MODEL_DIR)
model_v4_preview_fingerprint = path_fingerprint(DEFAULT_MODEL_V4_PREVIEW_ROOT)
model_v4_sanity_fingerprint = path_fingerprint(DEFAULT_MODEL_V4_SANITY_PATH)
model_v4_named_fingerprint = path_fingerprint(DEFAULT_MODEL_V4_NAMED_PATH)
model_v4_roster_rank_fingerprint = path_fingerprint(OFFICIAL_NINERS_ROSTER_RANK_PATH)
board = _load_board(
    active_data_pack,
    active_fingerprint,
    veteran_model_fingerprint,
    MY_TEAM_UI_REVISION,
)
health = _load_health(active_data_pack, active_fingerprint)
ranking_readiness = build_ranking_readiness(active_data_pack)
strategy = _load_strategy(active_data_pack, active_fingerprint)
feature_receipts = _load_feature_receipts(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    veteran_model_fingerprint,
)
roster_readiness = _load_roster_readiness(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    veteran_model_fingerprint,
    MY_TEAM_UI_REVISION,
)
model_v4_review = _load_model_v4_review(
    str(DEFAULT_MODEL_V4_PREVIEW_ROOT),
    model_v4_preview_fingerprint,
    str(DEFAULT_MODEL_V4_SANITY_PATH),
    model_v4_sanity_fingerprint,
    str(DEFAULT_MODEL_V4_NAMED_PATH),
    model_v4_named_fingerprint,
)
model_v4_roster_contract = _load_v4_roster_rank_contract(
    str(OFFICIAL_NINERS_ROSTER_RANK_PATH),
    model_v4_roster_rank_fingerprint,
)
pressure = board.keeper_board.pressure
v4_freeze_active = legacy_label_quarantine_active()
has_placeholder_scores = health.placeholder_model_output_count > 0
default_release = (
    str(board.forced_release_rows[0].get("player"))
    if board.forced_release_rows and not has_placeholder_scores
    else "None"
)
default_strategy_rows = [
    row for row in strategy.niners_action_rows if row.get("is_default_release")
]
release_pain = (
    float(default_strategy_rows[0].get("forced_release_pain") or 0.0)
    if default_strategy_rows
    else None
)

st.title("My Team")
st.caption(f"`{active_data_pack}`")
if roster_readiness.passed and not has_placeholder_scores and not v4_freeze_active:
    st.success(
        "**Roster Decisions Ready.** My Team is cleared for pre-declaration "
        "drop/shop review. Draft boards and final money decisions still have "
        "separate gates."
    )
    with st.expander("What passed, and what is still blocked?"):
        st.write(
            "Passed: current rosters, league ranks, stats-first outputs, lifecycle "
            "separation, critical source coverage, identity, young bridge receipts, "
            "and my-roster outlier review."
        )
        st.write(
            "Still separate: Draft Ready waits on the real draft pool/released "
            "veterans; Final Money Decisions Ready waits on final calibration and "
            "freeze gates."
        )
        st.dataframe(
            pd.DataFrame(roster_decision_gate_rows(roster_readiness)),
            use_container_width=True,
            hide_index=True,
        )
elif not has_placeholder_scores and v4_freeze_active:
    st.warning(f"**Roster Decisions Review Only.** {label_quarantine_notice()}")
    with st.expander("Why are action labels quarantined?"):
        st.write(
            "The page still shows roster facts, league-rank top-five mechanics, "
            "source data, and receipts. Legacy action labels are kept only as "
            "audit clues until Model v4 defines new thresholds and passes sanity "
            "fixtures."
        )
        st.dataframe(
            pd.DataFrame(roster_decision_gate_rows(roster_readiness)),
            use_container_width=True,
            hide_index=True,
        )
else:
    render_page_trust_banner(
        health,
        calibration_passed=ranking_readiness.calibration_passed,
        review_only_message=ranking_readiness.message if ranking_readiness.review_only else "",
        review_only_detail=(
            "My Team keeps model columns visible for audit, but recommendations "
            "are not roster-ready until source coverage, identity, lifecycle, "
            "receipt, and outlier gates pass."
        )
        if ranking_readiness.review_only
        else "",
    )
if has_placeholder_scores:
    st.info(
        "Model scores are not loaded yet. The roster's league-rank top-five list "
        "is usable for rule review; keep/shop/release recommendations stay hidden."
    )
elif roster_readiness.passed:
    st.info(
        "Start here: review the Required Top-Five Release Slot, then the legacy "
        "review buckets. Open each Why? receipt for any close call."
    )
elif ranking_readiness.review_only:
    st.info(
        "Start here: review the Required Top-Five Release Slot, then the legacy "
        "review buckets. Use each Why? receipt before acting because recommendations "
        "are still review-only."
    )
else:
    st.success(
        "Start here: confirm the Forced-Release Decision, then work through Bubble "
        "Players and Shop Candidates."
    )

left, middle, right, far_right = st.columns(4)
left.metric("Roster", pressure.roster_count)
middle.metric("Protect Limit", pressure.protect_limit)
right.metric("Over Limit", max(0, pressure.roster_count - pressure.protect_limit))
far_right.metric(
    "Release Pain" if release_pain is not None else "Pressure",
    f"{release_pain:.1f}" if release_pain is not None else pressure.pressure_level.upper(),
)

with st.expander("Roster's League-Rank Top Five audit"):
    if has_placeholder_scores:
        st.caption(
            "Use this to verify this roster's five highest league-ranked players. "
            "Model recommendations are hidden until scored outputs are available."
        )
    else:
        st.caption(
            "Roster's League-Rank Top Five means the five highest league-ranked "
            "players on this roster, not league ranks 1-5 overall. League rank is "
            "a rule signal, not player quality. The model only chooses the least "
            f"painful required release slot. Current default: {default_release}."
        )
    top_five_frame = pd.DataFrame(board.top_five_rows).drop(columns=["rank"], errors="ignore")
    if has_placeholder_scores:
        top_five_frame = top_five_frame.drop(
            columns=[
                "keep_priority",
                "cut_risk",
                "keeper_score",
                "drop_score",
                "model_recommendation",
                "action",
            ],
            errors="ignore",
        )
    else:
        top_five_columns = [
            "player",
            "pos",
            "nfl_team",
            "asset_lifecycle_label",
            "league_rank",
            "top_five_rule",
            "model_recommendation",
            "stats_value",
            "keep_priority",
            "cut_risk",
            "confidence",
            "confidence_label",
        ]
        top_five_frame = top_five_frame[
            [column for column in top_five_columns if column in top_five_frame.columns]
        ]
        if "model_recommendation" in top_five_frame:
            top_five_frame = top_five_frame.copy()
            top_five_frame["model_recommendation"] = top_five_frame[
                "model_recommendation"
            ].map(_display_label)
    st.dataframe(
        top_five_frame,
        column_config={
            "league_rank": "League Rank",
            "player": "Player",
            "pos": "Pos",
            "nfl_team": "NFL Team",
            "asset_lifecycle_label": "Lifecycle",
            "top_five_rule": "Top-Five Rule Status",
            "model_recommendation": "Model Recommendation",
            "stats_value": "Model Value",
            "keep_priority": "Keep Priority",
            "cut_risk": "Cut Risk",
                "confidence": "Confidence",
                "confidence_label": "Confidence Label",
                "keeper_score": "Keep Priority",
            "drop_score": "Cut Risk",
            "action": "Model Recommendation",
        },
        use_container_width=True,
        hide_index=True,
    )
    if not has_placeholder_scores and st.checkbox(
        "Show advanced roster top-five rows",
        value=False,
        key="team_show_advanced_top_five_rows",
    ):
        details_frame = pd.DataFrame(board.top_five_rows).drop(
            columns=["rank", "asset_lifecycle"],
            errors="ignore",
        )
        st.dataframe(
            details_frame,
            column_config={
                "league_rank": "League Rank",
                "player": "Player",
                "pos": "Pos",
                "nfl_team": "NFL Team",
                "asset_lifecycle_label": "Lifecycle",
                "top_five_rule": "Top-Five Rule Status",
                "model_recommendation": "Model Recommendation",
                "keep_priority": "Keep Priority",
                "cut_risk": "Cut Risk",
                "release_pain": "Release Pain",
                "decision_explanation": "Explanation",
            },
            use_container_width=True,
            hide_index=True,
        )

st.subheader("V4 Shadow My Team")
st.warning(MODEL_V4_SHADOW_MY_TEAM_BANNER)
st.caption(
    "This joins the locked Niners roster/rank context to review-only Model v4 "
    "preview rows. It does not replace active My Team or unlock roster readiness."
)
context_cols = st.columns(3)
context_cols[0].markdown("**Rule context**")
context_cols[0].caption(
    "Roster rank, league rank, and top-five status are league-rule context only."
)
context_cols[1].markdown("**Football value**")
context_cols[1].caption(
    "V4 Dynasty Asset Value is review-only football value from the v4 preview."
)
context_cols[2].markdown("**Confidence/source warnings**")
context_cols[2].caption(
    "Weak confidence, missing evidence, and unavailable sections remain visible."
)
if model_v4_review.issues:
    st.error("Some Model v4 review files are missing or unreadable.")
    st.dataframe(
        pd.DataFrame({"issue": model_v4_review.issues}),
        use_container_width=True,
        hide_index=True,
    )
if model_v4_roster_contract.status != "ready":
    st.error("The locked Niners roster-rank contract is not ready.")
    st.dataframe(
        pd.DataFrame(issue.__dict__ for issue in model_v4_roster_contract.issues),
        use_container_width=True,
        hide_index=True,
    )
v4_gate_frame = pd.DataFrame(model_v4_review.gate_rows)
if not v4_gate_frame.empty and (v4_gate_frame["status"].astype(str) == "blocked").any():
    st.error("A Model v4 isolation guard failed. Do not use the shadow team view.")
    st.dataframe(v4_gate_frame, use_container_width=True, hide_index=True)
elif model_v4_roster_contract.status == "ready":
    shadow_team_rows = build_model_v4_shadow_my_team_rows(
        list(model_v4_roster_contract.rows),
        model_v4_review.preview_rows,
        top_five_names=model_v4_roster_contract.top_five_names,
    )
    shadow_team_frame = pd.DataFrame(shadow_team_rows)
    if shadow_team_frame.empty:
        st.info("No V4 Shadow My Team rows are available.")
    else:
        display_shadow_team = shadow_team_frame.copy()
        for numeric_column in (
            "roster_rank",
            "league_rank",
            "v4_dynasty_asset_value",
            "v4_roster_decision_value",
        ):
            if numeric_column in display_shadow_team:
                display_shadow_team[numeric_column] = pd.to_numeric(
                    display_shadow_team[numeric_column],
                    errors="coerce",
                )
        shadow_team_display = display_shadow_team.reindex(
            columns=list(MODEL_V4_SHADOW_MY_TEAM_COLUMNS)
        ).reset_index(drop=True)
        shadow_team_event = st.dataframe(
            shadow_team_display,
            column_config={
                "player": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["player"],
                    pinned=True,
                ),
                "position": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["position"],
                ),
                "nfl_team": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["nfl_team"],
                ),
                "roster_rank": st.column_config.NumberColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["roster_rank"],
                    help="Locked roster rank from the March 31 Niners input.",
                    format="%d",
                ),
                "league_rank": st.column_config.NumberColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["league_rank"],
                    help="League-rank rule context only; not player quality.",
                    format="%d",
                ),
                "top_five_rule_status": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["top_five_rule_status"],
                    help=(
                        "Roster's League-Rank Top Five means this roster's five "
                        "highest league-ranked players, not league ranks 1-5 overall."
                    ),
                ),
                "v4_dynasty_asset_value": st.column_config.NumberColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["v4_dynasty_asset_value"],
                    help="Review-only Model v4 private football value.",
                    format="%.2f",
                ),
                "v4_roster_decision_value": st.column_config.NumberColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["v4_roster_decision_value"],
                    help="Reserved for a later v4 roster-decision lane.",
                    format="%.2f",
                ),
                "confidence_label": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["confidence_label"],
                ),
                "warnings": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["warnings"],
                ),
                "unavailable_sections": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_MY_TEAM_LABELS["unavailable_sections"],
                ),
            },
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="team_v4_shadow_my_team_table",
        )
        with st.expander("V4 Shadow Receipt Drilldown", expanded=True):
            selected_shadow_indices = _selected_dataframe_rows(shadow_team_event)
            selected_shadow_row = (
                shadow_team_frame.reset_index(drop=True)
                .iloc[selected_shadow_indices[0]]
                .to_dict()
                if selected_shadow_indices
                else None
            )
            render_model_v4_shadow_receipt_drilldown(
                selected_shadow_row,
                model_v4_review.preview_rows,
                model_v4_review.receipt_rows,
                key_prefix="team_v4_shadow",
            )
        with st.expander("Advanced: V4 shadow My Team join audit"):
            st.caption(
                "This audit proves the shadow table is joined for display only. "
                "It does not feed active My Team action labels."
            )
            st.dataframe(
                shadow_team_frame.reindex(
                    columns=[
                        "player",
                        "matched_v4_player",
                        "v4_match_status",
                        "rule_context",
                        "football_value_context",
                        "warning_context",
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

roster_frame = pd.DataFrame(board.roster_rows)

if has_placeholder_scores:
    st.subheader("Roster Inventory")
    st.caption("Showing roster inventory only until scored model outputs are available.")
    st.dataframe(
        roster_frame[["player", "pos", "league_rank"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    if ranking_readiness.review_only:
        st.subheader("Roster Decision Board")
    else:
        st.subheader("What Should I Do?")
    st.caption(
        "`Keep Priority` and `Cut Risk` are roster-decision labels. `Model Value` "
        "is stats-first private value. `Model vs Market` is Model Value minus the "
        "trade market and is for finding trade opportunity."
    )

    def _render_team_section(section_name: str, rows: list[dict[str, object]]) -> None:
        display_name = {
            "Bench/Stash": "Cut/Stash Candidates",
        }.get(section_name, section_name)
        display_name = _display_label(display_name)
        st.markdown(f"### {display_name}")
        caption = _section_caption(section_name)
        if caption:
            st.caption(caption)
        if not rows:
            st.caption("No players in this bucket.")
            return
        section_frame = pd.DataFrame(rows)
        decision_receipts = build_my_team_decision_receipts(rows, feature_receipts)
        for row in rows:
            _render_player_decision_card(
                row,
                _receipt_for_player(decision_receipts, row.get("player")),
                section_name=section_name,
            )

        with st.expander(f"Advanced table: {display_name}"):
            st.caption(
                "Full row values for audit. Use the cards above for normal roster "
                "review."
            )
            display_columns = [
                column
                for column in TEAM_DECISION_COLUMNS
                if column not in {"receipt_link", "compare_link", "decision_explanation"}
            ]
            if section_name != "Forced-Release Decision":
                display_columns = [
                    column
                    for column in display_columns
                    if column not in {"release_pain", "decision_explanation"}
                ]
            st.dataframe(
                section_frame[display_columns],
                column_config={
                    "player": _team_label("player"),
                    "pos": _team_label("pos"),
                    "nfl_team": _team_label("nfl_team"),
                    "asset_lifecycle_label": _team_label("asset_lifecycle_label"),
                    "league_rank": _team_label("league_rank"),
                    "top_five_rule": st.column_config.TextColumn(
                        _team_label("top_five_rule"),
                        help=(
                            "Roster's League-Rank Top Five means this roster's five "
                            "highest league-ranked players, not league ranks 1-5 "
                            "overall. League rank is a rule signal, not player quality."
                        ),
                    ),
                    "model_recommendation": _team_label("model_recommendation"),
                    "keep_priority": st.column_config.NumberColumn(
                        _team_label("keep_priority"),
                        help="Higher means stronger keep priority.",
                        format="%.2f",
                    ),
                    "cut_risk": st.column_config.NumberColumn(
                        _team_label("cut_risk"),
                        help="Higher means stronger cut/shop risk.",
                        format="%.2f",
                    ),
                    "stats_value": st.column_config.NumberColumn(
                        _team_label("stats_value"),
                        help="Private LVE football/stat value.",
                        format="%.2f",
                    ),
                    "market_edge": st.column_config.NumberColumn(
                        _team_label("market_edge"),
                        help="Model Value minus trade market.",
                        format="%.2f",
                    ),
                    "release_pain": st.column_config.NumberColumn(
                        _team_label("release_pain"),
                        help=(
                            "How painful the Required Top-Five Release Slot is. This "
                            "is only shown for the current least-painful roster "
                            "top-five release."
                        ),
                        format="%.2f",
                    ),
                    "decision_explanation": _team_label("decision_explanation"),
                    "confidence": st.column_config.NumberColumn(
                        _team_label("confidence"),
                        format="%.2f",
                    ),
                    "confidence_label": st.column_config.TextColumn(
                        _team_label("confidence_label"),
                        help=(
                            "Plain-English confidence tier: strong, usable, review, "
                            "weak, or blocked."
                        ),
                    ),
                },
                use_container_width=True,
                hide_index=True,
            )

    section_order = [
        "Forced-Release Decision",
        "Core Holds",
        "Needs Data Review",
        "Bubble Players",
        "Shop Candidates",
        "Bench/Stash",
    ]
    for section in section_order:
        _render_team_section(section, board.rows_by_section.get(section, []))

if strategy.has_real_model_outputs and strategy.niners_action_rows:
    with st.expander("Advanced: forced-release strategy audit"):
        st.caption(
            "Strategy detail keeps the rule requirement separate from the model "
            "recommendation. Only rows marked `must_release_top_five` satisfy the "
            "Required Top-Five Release Slot."
        )
        strategy_frame = pd.DataFrame(strategy.niners_action_rows)
        st.dataframe(
            strategy_frame[
                [
                    "player",
                    "pos",
                    "league_rank",
                    "rule_requirement",
                    "rule_explanation",
                    "keeper_score",
                    "drop_score",
                    "forced_release_pain",
                    "release_decision_difficulty",
                    "forced_release_pressure_score",
                    "trade_urgency",
                    "action_label",
                    "strategy_reason",
                    "score_explanation",
                    "next_step",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        with st.expander("Secondary roster context"):
            st.caption(
                "These rows do not choose the forced-release player. They only explain "
                "whether the Required Top-Five Release Slot is painful compared "
                "with easier regular cuts."
            )
            st.dataframe(
                strategy_frame[
                    [
                        "player",
                        "league_rank",
                        "is_default_release",
                        "top_five_value_gap",
                        "easy_non_top_five_drop",
                        "replacement_depth_count",
                    ]
                ],
                column_config={
                    "player": "Roster Top-Five Player",
                    "league_rank": "League Rank",
                    "is_default_release": "Current Required Release Slot",
                    "top_five_value_gap": "Secondary Value Gap",
                    "easy_non_top_five_drop": "Secondary Comparison Drop",
                    "replacement_depth_count": "Replacement Depth",
                },
                use_container_width=True,
                hide_index=True,
            )

with st.expander("Advanced: roster feature receipts"):
    st.caption(
        "Inspect the normalized features, weights, and source rows behind a "
        "roster player's model score. This is the place to catch bad inputs."
    )
    if feature_receipts.issues:
        st.warning("; ".join(feature_receipts.issues))
    else:
        receipt_frame = pd.DataFrame(feature_receipts.rows)
        if receipt_frame.empty:
            st.dataframe(receipt_frame, use_container_width=True, hide_index=True)
        else:
            roster_players = [
                player
                for player in roster_frame.get("player", pd.Series(dtype=str)).tolist()
                if player in feature_receipts.players
            ]
            selected_players = st.multiselect(
                "Roster Receipt Player",
                roster_players,
                default=roster_players[:3],
                key="team_receipt_players",
            )
            selected_components = st.multiselect(
                "Roster Receipt Component",
                feature_receipts.components,
                default=feature_receipts.components,
                key="team_receipt_components",
            )
            receipt_filtered = receipt_frame[
                receipt_frame["player"].isin(selected_players)
                & receipt_frame["component"].isin(selected_components)
            ]
            selected_player_rows = (
                roster_frame[roster_frame["player"].isin(selected_players)]
                .rename(columns={"pos": "position"})
                .to_dict("records")
            )
            summary_filtered = pd.DataFrame(
                component_summary_rows_for_players(
                    feature_receipts,
                    selected_player_rows,
                    player_column="player",
                    position_column="position",
                )
            )
            if not summary_filtered.empty:
                summary_filtered = summary_filtered[
                    summary_filtered["component"].isin(selected_components)
                ]
            sorted_receipts = pd.DataFrame(
                receipt_rows_for_players(
                    feature_receipts,
                    receipt_filtered.to_dict("records"),
                    player_column="player",
                    position_column="position",
                    include_fallback_rows=False,
                    page_source="My Team",
                )
            )
            st.subheader("Component Reconciliation")
            st.dataframe(summary_filtered, use_container_width=True, hide_index=True)
            st.subheader("Feature Receipts")
            if sorted_receipts.empty:
                st.info("No feature receipts for the selected roster players.")
            else:
                st.dataframe(
                    sorted_receipts[list(RECEIPT_DISPLAY_COLUMNS)].rename(
                        columns=RECEIPT_COLUMN_LABELS
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

with st.expander("Advanced: league keeper pressure"):
    st.caption(sort_caption(board.sort_metadata["pressure_rows"]))
    st.dataframe(
        pd.DataFrame(board.pressure_rows),
        column_config={"team": "Fantasy Team"},
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Advanced: rules used"):
    st.write(
        f"Protect limit is {board.rules.protect_limit}. "
        f"Only {board.rules.official_top_five_keep_limit} players from a team's "
        "Roster's League-Rank Top Five can be protected. That means the five "
        "highest league-ranked players on that roster, not league ranks 1-5 "
        "overall. League rank is a rule signal, not player quality. The default "
        "release table chooses the lowest model/player value inside that roster "
        "top-five group; cut risk is only a tiebreaker."
    )
