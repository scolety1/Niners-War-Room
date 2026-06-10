from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.demo_source_labels import demo_source_label
from app.components.model_v4_receipts import render_model_v4_shadow_receipt_drilldown
from app.components.trust_status import render_page_trust_banner
from src.config.settings import get_settings
from src.services.command_board_service import (
    WAR_BOARD_COLUMN_LABELS,
    build_war_board,
)
from src.services.confidence_rebuild_service import build_confidence_rebuild_report
from src.services.data_pack_health_service import build_data_pack_health_report
from src.services.identity_audit_service import build_identity_audit
from src.services.legacy_label_quarantine_service import (
    label_quarantine_notice,
    legacy_label_quarantine_active,
    quarantine_legacy_label,
)
from src.services.market_edge_service import build_market_edge_report
from src.services.model_outlier_service import build_model_outlier_report
from src.services.model_v4_app_review_service import (
    DEFAULT_MODEL_V4_NAMED_PATH,
    DEFAULT_MODEL_V4_PREVIEW_ROOT,
    DEFAULT_MODEL_V4_SANITY_PATH,
    MODEL_V4_OLD_VS_V4_BANNER,
    MODEL_V4_OLD_VS_V4_COLUMNS,
    MODEL_V4_OLD_VS_V4_LABELS,
    MODEL_V4_PROMOTION_BLOCKER_COLUMNS,
    MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS,
    MODEL_V4_PROMOTION_BLOCKER_LABELS,
    MODEL_V4_PROMOTION_BLOCKERS_BANNER,
    MODEL_V4_SHADOW_WAR_BOARD_BANNER,
    MODEL_V4_SHADOW_WAR_BOARD_COLUMNS,
    MODEL_V4_SHADOW_WAR_BOARD_LABELS,
    build_model_v4_app_review,
    build_model_v4_old_vs_v4_comparison_rows,
    build_model_v4_promotion_blocker_rows,
    build_model_v4_promotion_blocker_summary_rows,
    build_model_v4_shadow_war_board_rows,
)
from src.services.player_comparison_service import (
    build_player_compare_options,
    compare_players,
)
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    RECEIPT_COLUMN_LABELS,
    RECEIPT_DISPLAY_COLUMNS,
    build_player_feature_receipts,
    compact_receipt_preview_for_player,
    component_summary_rows_for_players,
    receipt_rows_for_players,
)
from src.services.ranking_audit_service import (
    build_ranking_audit,
    ranking_audit_summary_rows,
)
from src.services.ranking_readiness_service import build_ranking_readiness
from src.services.ranking_surface_service import (
    FORCED_RELEASE_PAIN,
    KEEPER_DECISION,
    PURE_MODEL_VALUE,
    TRADE_LIQUIDITY,
    apply_ranking_surface,
    surface_for_id,
    surface_summary_row,
)
from src.services.source_coverage_audit_service import build_source_coverage_audit


@st.cache_data
def _load_board(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_war_board(active_data_pack)


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


@st.cache_data
def _load_ranking_audit(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint
    return build_ranking_audit(active_data_pack)


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


@st.cache_data
def _load_compare_options(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_player_compare_options(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_player_compare(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
    player_a: str,
    player_b: str,
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return compare_players(
        active_data_pack,
        player_a,
        player_b,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_model_outliers(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_model_outlier_report(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_market_edge(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint
    return build_market_edge_report(active_data_pack)


@st.cache_data
def _load_confidence_rebuild(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_confidence_rebuild_report(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_identity_audit(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    source_root: str,
    source_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, source_fingerprint
    return build_identity_audit(
        active_data_pack,
        source_root=source_root,
    )


@st.cache_data
def _load_source_coverage_audit(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_source_coverage_audit(
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


def _player_key(player: object, position: object) -> str:
    name = "".join(character.lower() for character in str(player) if character.isalnum())
    return f"{name}::{position}"


def _action_priority_for_display(action: object) -> int:
    return {
        "shop/release": 0,
        "drop": 1,
        "shop": 2,
        "bubble": 3,
        "review": 4,
        "risk": 5,
        "hold": 6,
        "keep": 7,
    }.get(str(action or "").lower(), 99)


def _apply_confidence_rebuild(
    data_frame: pd.DataFrame,
    confidence_rows: list[dict[str, object]],
) -> pd.DataFrame:
    if data_frame.empty:
        return data_frame
    lookup = {
        _player_key(row.get("player", ""), row.get("position", "")): row
        for row in confidence_rows
    }
    output = data_frame.copy()
    output["confidence_audit"] = output.apply(
        lambda row: lookup.get(_player_key(row.get("player", ""), row.get("pos", "")), {}).get(
            "rebuilt_confidence_score",
            "",
        ),
        axis=1,
    )
    output["action_certainty"] = output.apply(
        lambda row: lookup.get(_player_key(row.get("player", ""), row.get("pos", "")), {}).get(
            "action_certainty",
            "not_audited",
        ),
        axis=1,
    )
    output["confidence_reason"] = output.apply(
        lambda row: lookup.get(_player_key(row.get("player", ""), row.get("pos", "")), {}).get(
            "certainty_reason",
            "",
        ),
        axis=1,
    )
    return output


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


def _format_metric(value: object) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value or "")


def _snapshot_table(
    data_frame: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    if data_frame.empty:
        return pd.DataFrame(columns=columns)
    output = data_frame.reindex(columns=columns).copy()
    if "action" in output:
        output["action"] = output["action"].map(quarantine_legacy_label)
    return output


def _as_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _sorted_text_options(data_frame: pd.DataFrame, column: str) -> list[str]:
    if column not in data_frame:
        return []
    return sorted(
        value
        for value in data_frame[column].dropna().astype(str).unique()
        if value
    )


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
veteran_model_fingerprint = path_fingerprint(DEFAULT_RECEIPT_VETERAN_MODEL_DIR)
model_v4_preview_fingerprint = path_fingerprint(DEFAULT_MODEL_V4_PREVIEW_ROOT)
model_v4_sanity_fingerprint = path_fingerprint(DEFAULT_MODEL_V4_SANITY_PATH)
model_v4_named_fingerprint = path_fingerprint(DEFAULT_MODEL_V4_NAMED_PATH)
board = _load_board(active_data_pack, active_fingerprint, veteran_model_fingerprint)
health = _load_health(active_data_pack, active_fingerprint)
ranking_readiness = build_ranking_readiness(active_data_pack)
ranking_audit = _load_ranking_audit(active_data_pack, active_fingerprint)
feature_receipts = _load_feature_receipts(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    veteran_model_fingerprint,
)
compare_options = _load_compare_options(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    veteran_model_fingerprint,
)
model_outliers = _load_model_outliers(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    veteran_model_fingerprint,
)
market_edge = _load_market_edge(active_data_pack, active_fingerprint)
confidence_rebuild = _load_confidence_rebuild(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    veteran_model_fingerprint,
)
identity_audit = _load_identity_audit(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    veteran_model_fingerprint,
)
source_coverage = _load_source_coverage_audit(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    veteran_model_fingerprint,
)
model_v4_review = _load_model_v4_review(
    str(DEFAULT_MODEL_V4_PREVIEW_ROOT),
    model_v4_preview_fingerprint,
    str(DEFAULT_MODEL_V4_SANITY_PATH),
    model_v4_sanity_fingerprint,
    str(DEFAULT_MODEL_V4_NAMED_PATH),
    model_v4_named_fingerprint,
)
frame = pd.DataFrame(board.rows)
frame = _apply_confidence_rebuild(frame, confidence_rebuild.rows)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.4rem; }
    div[data-testid="stAlert"] { padding: 0.45rem 0.7rem; }
    div[data-testid="stAlert"] p { margin-bottom: 0; }
    div[data-testid="stExpander"] details summary { padding-top: 0.45rem; padding-bottom: 0.45rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("War Board")
st.caption(demo_source_label(active_data_pack))
render_page_trust_banner(
    health,
    calibration_passed=ranking_readiness.calibration_passed,
    review_only_message=ranking_readiness.message if ranking_readiness.review_only else "",
    review_only_detail=(
        "War Board rankings remain visible as audit prompts only. Use the receipts, "
        "outliers, identity, and coverage sections below to find what is wrong before "
        "trusting any order."
    )
    if ranking_readiness.review_only
    else "",
    compact=True,
)
st.caption("Model Value is stats-first private value; Trade Market is liquidity only.")
if legacy_label_quarantine_active():
    st.caption(label_quarantine_notice())
if board.data_source_audit_rows:
    audit_row = board.data_source_audit_rows[0]
    if audit_row.get("status") == "warning" and _as_int(
        audit_row.get("stale_pack_fallback_rows")
    ):
        st.warning(str(audit_row.get("warning") or "Score source sync needs review."))
    with st.expander("Advanced: score source audit"):
        st.caption(
            "This confirms whether visible scores came from the selected data pack "
            "or a newer active stats-first preview matched through the identity bridge."
        )
        st.dataframe(
            pd.DataFrame(board.data_source_audit_rows),
            use_container_width=True,
            hide_index=True,
        )

if frame.empty:
    st.dataframe(frame, use_container_width=True, hide_index=True)
elif health.placeholder_model_output_count:
    st.info(
        "Model scores are not loaded yet. This page is showing roster and league-rank "
        "inventory only; keeper/drop recommendations stay hidden until model outputs are real."
    )
    st.dataframe(
        frame[["player", "pos", "team", "league_rank"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    with st.expander("Filters", expanded=False):
        control_top = st.columns(5)
        positions = control_top[0].multiselect(
            "Position",
            board.positions,
            default=board.positions,
        )
        actions = control_top[1].multiselect(
            "Action",
            board.actions,
            default=board.actions,
        )
        edge_types = control_top[2].multiselect(
            "Edge Type",
            board.edge_types,
            default=board.edge_types,
        )
        confidence_buckets = control_top[3].multiselect(
            "Confidence",
            board.confidence_buckets,
            default=board.confidence_buckets,
        )
        teams = control_top[4].multiselect(
            "Fantasy Team",
            board.teams,
            default=board.teams,
        )
        top_five_only = st.checkbox(
            "Roster's League-Rank Top Five",
            value=False,
            help=(
                "Shows each roster's five highest league-ranked players. This is "
                "not league ranks 1-5 overall, and league rank is a rule signal, "
                "not player quality."
            ),
        )

    filtered = frame[
        frame["pos"].isin(positions)
        & frame["team"].isin(teams)
        & frame["action"].isin(actions)
        & frame["edge_type"].isin(edge_types)
        & frame["confidence_bucket"].isin(confidence_buckets)
    ]
    if top_five_only:
        filtered = (
            filtered.sort_values(["team", "league_rank", "player"])
            .groupby("team", group_keys=False)
            .head(5)
        )

    st.subheader("Decision Snapshot")
    snapshot_columns = ["player", "pos", "action", "stats_value", "market_edge"]
    snapshot_config = {
        "player": "Player",
        "pos": "Pos",
        "action": "Action",
        "stats_value": st.column_config.NumberColumn("Model Value", format="%.2f"),
        "market_edge": st.column_config.NumberColumn("Model vs Market", format="%.2f"),
    }
    top_ranked = filtered.sort_values(["overall_rank", "player"], ascending=[True, True]).head(8)
    action_queue = filtered.sort_values(
        ["action", "overall_rank", "player"],
        key=lambda column: column.map(_action_priority_for_display)
        if column.name == "action"
        else column,
    ).head(8)
    model_edge = filtered.sort_values(
        ["market_edge", "overall_rank", "player"],
        ascending=[False, True, True],
    ).head(8)
    snap_left, snap_middle, snap_right = st.columns(3)
    with snap_left:
        st.markdown("**Top Ranked**")
        st.dataframe(
            _snapshot_table(top_ranked, snapshot_columns),
            column_config=snapshot_config,
            use_container_width=True,
            hide_index=True,
        )
    with snap_middle:
        st.markdown("**Action Queue**")
        st.dataframe(
            _snapshot_table(action_queue, snapshot_columns),
            column_config=snapshot_config,
            use_container_width=True,
            hide_index=True,
        )
    with snap_right:
        st.markdown("**Model vs Market**")
        st.dataframe(
            _snapshot_table(model_edge, snapshot_columns),
            column_config=snapshot_config,
            use_container_width=True,
            hide_index=True,
        )

    surface_options = {
        "Pure Model Value": PURE_MODEL_VALUE,
        "Keeper Decision": KEEPER_DECISION,
        "Trade/Liquidity": TRADE_LIQUIDITY,
        "Forced-Release Pain": FORCED_RELEASE_PAIN,
    }
    sort_mode = st.radio(
        "Ranking Surface",
        list(surface_options),
        horizontal=True,
        index=0,
        help=(
            "Each surface has its own rank source. Pure Model Value is player value; "
            "Keeper Decision adds roster context; Trade/Liquidity is market edge; "
            "Forced-Release Pain only inspects each roster's league-rank top-five "
            "rule candidates."
        ),
    )
    surface_id = surface_options[sort_mode]
    surface = surface_for_id(surface_id)
    surface_summary = surface_summary_row(surface_id)
    st.caption(
        f"Rank source: {surface_summary['rank_source']}. "
        f"Use: {surface_summary['intended_use']}"
    )
    st.caption(f"Sorted by {surface_summary['sort']}")
    st.caption(
        "Model Value is stats-first private value; Trade Market is liquidity only."
    )
    surface_rows = apply_ranking_surface(
        filtered.to_dict("records"),
        surface_id,
    )
    surface_frame = pd.DataFrame(surface_rows)
    surface_columns = [
        column for column in surface.display_columns if column in surface_frame.columns
    ]
    if surface_frame.empty:
        st.info("No rows match this ranking surface and the current filters.")
        display_frame = pd.DataFrame(columns=surface_columns)
    else:
        display_frame = surface_frame[surface_columns].reset_index(drop=True).copy()
        if "action" in display_frame:
            display_frame["action"] = display_frame["action"].map(quarantine_legacy_label)
    column_labels = {
        **WAR_BOARD_COLUMN_LABELS,
        "surface_rank": "Rank",
        "keeper_score": "Keep Priority",
        "drop_score": "Cut Risk",
        "edge_type": "Edge Type",
        "league_rank": "League Rank",
    }
    selected_event = st.dataframe(
        display_frame,
        column_config={
            "surface_rank": st.column_config.NumberColumn(
                column_labels["surface_rank"],
                help="Rank within the selected ranking surface.",
                pinned=True,
            ),
            "overall_rank": st.column_config.NumberColumn(
                column_labels["overall_rank"],
                help="Overall model rank before the action-priority display sort.",
                pinned=True,
            ),
            "position_rank_label": st.column_config.TextColumn(
                column_labels["position_rank_label"],
                pinned=True,
            ),
            "player": st.column_config.TextColumn(
                column_labels["player"],
                pinned=True,
            ),
            "pos": st.column_config.TextColumn(column_labels["pos"]),
            "asset_lifecycle_label": st.column_config.TextColumn(
                column_labels["asset_lifecycle_label"],
            ),
            "team": st.column_config.TextColumn(column_labels["team"]),
            "action": st.column_config.TextColumn(column_labels["action"]),
            "league_rank": st.column_config.NumberColumn(column_labels["league_rank"]),
            "keeper_score": st.column_config.NumberColumn(
                column_labels["keeper_score"],
                help="Roster-context keep priority; not pure model value.",
                format="%.2f",
            ),
            "drop_score": st.column_config.NumberColumn(
                column_labels["drop_score"],
                help="Roster-context cut risk; not pure model value.",
                format="%.2f",
            ),
            "stats_value": st.column_config.NumberColumn(
                column_labels["stats_value"],
                help=(
                    "Private stats-first/LVE football value. Market is not "
                    "allowed to dominate this."
                ),
                format="%.2f",
            ),
            "market_value": st.column_config.NumberColumn(
                column_labels["market_value"],
                help="Public crowd/liquidity value for trade execution, not model truth.",
                format="%.2f",
            ),
            "market_edge": st.column_config.NumberColumn(
                column_labels["market_edge"],
                help=(
                    "Model Value minus Trade Market. Positive means model higher "
                    "than the trade market."
                ),
                format="%.2f",
            ),
            "edge_type": st.column_config.TextColumn(column_labels["edge_type"]),
            "confidence": st.column_config.NumberColumn(
                column_labels["confidence"],
                help="Decision-safety confidence after source, identity, and warning checks.",
                format="%.2f",
            ),
            "confidence_label": st.column_config.TextColumn(
                column_labels["confidence_label"],
                help="Plain-English confidence tier: strong, usable, review, weak, or blocked.",
            ),
            "warning_reason": column_labels["warning_reason"],
        },
        on_select="rerun",
        selection_mode="single-row",
        use_container_width=True,
        hide_index=True,
        key="war_board_main_table",
    )

    with st.expander("Why Ranked Here", expanded=True):
        selected_indices = _selected_dataframe_rows(selected_event)
        if not selected_indices:
            st.info("Select one player row above to see the compact ranking receipt.")
        else:
            selected_index = selected_indices[0]
            selected_row = surface_frame.reset_index(drop=True).iloc[selected_index].to_dict()
            preview = compact_receipt_preview_for_player(
                feature_receipts,
                selected_row,
                page_source="War Board",
            )
            summary = preview["summary"]
            summary_columns = st.columns(5)
            summary_columns[0].metric("Rank", summary.get("rank") or "")
            summary_columns[1].metric("Position Rank", summary.get("position_rank") or "")
            summary_columns[2].metric(
                "Model Value",
                _format_metric(summary.get("model_value")),
            )
            summary_columns[3].metric(
                "Confidence",
                str(summary.get("confidence_label") or ""),
            )
            summary_columns[4].metric("Lifecycle", str(summary.get("lifecycle") or ""))
            st.caption(str(summary.get("confidence_explanation") or ""))
            st.caption(str(preview["lifecycle_explanation"]))
            warnings = preview["source_warnings"]
            if warnings:
                st.warning(" ".join(str(warning) for warning in warnings))
            else:
                st.success("No active source warning for this selected player.")

            driver_left, driver_right = st.columns(2)
            with driver_left:
                st.markdown("**Top model drivers**")
                positive_frame = pd.DataFrame(preview["positive_drivers"])
                if positive_frame.empty:
                    st.caption("No model driver rows found.")
                else:
                    st.dataframe(positive_frame, use_container_width=True, hide_index=True)
            with driver_right:
                st.markdown("**Drags / review flags**")
                negative_frame = pd.DataFrame(preview["negative_drivers"])
                if negative_frame.empty:
                    st.caption("No negative, low-score, or warning driver rows found.")
                else:
                    st.dataframe(negative_frame, use_container_width=True, hide_index=True)

            context_left, context_right = st.columns(2)
            with context_left:
                bridge_frame = pd.DataFrame(preview["bridge_drivers"])
                if not bridge_frame.empty:
                    st.markdown("**Young-player bridge prior**")
                    st.dataframe(bridge_frame, use_container_width=True, hide_index=True)
            with context_right:
                market_frame = pd.DataFrame(preview["market_context"])
                if not market_frame.empty:
                    st.markdown("**Trade market context**")
                    st.caption(
                        "Market rows explain liquidity/trade context, "
                        "not private model value."
                    )
                    st.dataframe(market_frame, use_container_width=True, hide_index=True)

            with st.expander("Advanced: full receipt rows"):
                advanced_frame = pd.DataFrame(preview["advanced_receipt_rows"])
                if advanced_frame.empty:
                    st.caption("No full receipt rows found for this player.")
                else:
                    st.dataframe(
                        advanced_frame[list(RECEIPT_DISPLAY_COLUMNS)].rename(
                            columns=RECEIPT_COLUMN_LABELS
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

st.divider()
st.subheader("V4 Shadow War Board")
st.warning(MODEL_V4_SHADOW_WAR_BOARD_BANNER)
st.caption(
    "This is the Model v4 preview board for inspection only. It does not feed the "
    "active War Board, action queue, roster decisions, or readiness gates."
)
if model_v4_review.issues:
    st.error("Some Model v4 review files are missing or unreadable.")
    st.dataframe(
        pd.DataFrame({"issue": model_v4_review.issues}),
        use_container_width=True,
        hide_index=True,
    )
v4_gate_frame = pd.DataFrame(model_v4_review.gate_rows)
if not v4_gate_frame.empty and (v4_gate_frame["status"].astype(str) == "blocked").any():
    st.error("A Model v4 isolation guard failed. Do not use the shadow board.")
    st.dataframe(v4_gate_frame, use_container_width=True, hide_index=True)
else:
    shadow_rows = build_model_v4_shadow_war_board_rows(model_v4_review.preview_rows)
    shadow_frame = pd.DataFrame(shadow_rows)
    if shadow_frame.empty:
        st.info("No Model v4 shadow ranking rows are available.")
    else:
        with st.expander("V4 Shadow Filters", expanded=False):
            v4_filter_cols = st.columns([1, 1, 1, 1, 1.2])
            v4_positions = _sorted_text_options(shadow_frame, "position")
            v4_lifecycles = _sorted_text_options(shadow_frame, "lifecycle")
            v4_confidence = _sorted_text_options(shadow_frame, "confidence_label")
            selected_v4_positions = v4_filter_cols[0].multiselect(
                "Position",
                v4_positions,
                default=v4_positions,
                key="war_board_v4_shadow_position_filter",
            )
            selected_v4_lifecycles = v4_filter_cols[1].multiselect(
                "Lifecycle",
                v4_lifecycles,
                default=v4_lifecycles,
                key="war_board_v4_shadow_lifecycle_filter",
            )
            selected_v4_confidence = v4_filter_cols[2].multiselect(
                "Confidence Label",
                v4_confidence,
                default=v4_confidence,
                key="war_board_v4_shadow_confidence_filter",
            )
            v4_warning_contains = v4_filter_cols[3].text_input(
                "Warning Contains",
                "",
                key="war_board_v4_shadow_warning_filter",
            )
            v4_search = v4_filter_cols[4].text_input(
                "Search",
                "",
                key="war_board_v4_shadow_search",
            )

        shadow_filtered = shadow_frame[
            shadow_frame["position"].astype(str).isin(selected_v4_positions)
            & shadow_frame["lifecycle"].astype(str).isin(selected_v4_lifecycles)
            & shadow_frame["confidence_label"].astype(str).isin(selected_v4_confidence)
        ].copy()
        if v4_warning_contains:
            shadow_filtered = shadow_filtered[
                shadow_filtered["review_warnings"].astype(str).str.contains(
                    v4_warning_contains,
                    case=False,
                    na=False,
                )
            ]
        if v4_search:
            shadow_filtered = shadow_filtered[
                shadow_filtered["player"].astype(str).str.contains(
                    v4_search,
                    case=False,
                    na=False,
                )
                | shadow_filtered["nfl_team"].astype(str).str.contains(
                    v4_search,
                    case=False,
                    na=False,
                )
            ]

        st.caption(
            "Sorted by V4 Overall Rank. Active rankings remain on the current War "
            "Board above."
        )
        shadow_display = shadow_filtered.reindex(
            columns=list(MODEL_V4_SHADOW_WAR_BOARD_COLUMNS)
        ).reset_index(drop=True)
        shadow_event = st.dataframe(
            shadow_display,
            column_config={
                "overall_preview_rank": st.column_config.NumberColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["overall_preview_rank"],
                    pinned=True,
                ),
                "position_preview_rank": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["position_preview_rank"],
                    pinned=True,
                ),
                "player": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["player"],
                    pinned=True,
                ),
                "position": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["position"],
                ),
                "nfl_team": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["nfl_team"],
                ),
                "lifecycle": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["lifecycle"],
                ),
                "dynasty_asset_value": st.column_config.NumberColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["dynasty_asset_value"],
                    format="%.2f",
                ),
                "confidence_label": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["confidence_label"],
                ),
                "review_warnings": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["review_warnings"],
                ),
                "unavailable_sections": st.column_config.TextColumn(
                    MODEL_V4_SHADOW_WAR_BOARD_LABELS["unavailable_sections"],
                ),
            },
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="war_board_v4_shadow_table",
        )
        with st.expander("V4 Shadow Receipt Drilldown", expanded=True):
            shadow_selected_indices = _selected_dataframe_rows(shadow_event)
            selected_shadow_row = (
                shadow_display.iloc[shadow_selected_indices[0]].to_dict()
                if shadow_selected_indices
                else None
            )
            render_model_v4_shadow_receipt_drilldown(
                selected_shadow_row,
                model_v4_review.preview_rows,
                model_v4_review.receipt_rows,
                key_prefix="war_board_v4_shadow",
            )

        st.subheader("Old vs V4 Comparison")
        st.info(MODEL_V4_OLD_VS_V4_BANNER)
        st.caption(
            "This compares the current active War Board to the v4 shadow board. "
            "Large unexplained movement is a review flag only; it does not replace "
            "active ranks."
        )
        comparison_rows = build_model_v4_old_vs_v4_comparison_rows(
            frame.to_dict("records"),
            model_v4_review.preview_rows,
            model_v4_review.movement_rows,
        )
        comparison_frame = pd.DataFrame(comparison_rows)
        if comparison_frame.empty:
            st.info("No active-vs-v4 comparison rows are available.")
        else:
            large_unexplained_count = int(
                comparison_frame["large_unexplained_movement"].fillna(False).sum()
            )
            if large_unexplained_count:
                st.warning(
                    f"{large_unexplained_count} large active-vs-v4 movements do not "
                    "have an available explanation yet."
                )
            with st.expander("Old vs V4 Filters", expanded=False):
                comparison_filter_cols = st.columns([1, 1, 1, 1, 1.3])
                comparison_niners_only = comparison_filter_cols[0].checkbox(
                    "Niners roster",
                    value=False,
                    key="war_board_v4_compare_niners_only",
                )
                comparison_top_50_only = comparison_filter_cols[1].checkbox(
                    "Top 50",
                    value=False,
                    key="war_board_v4_compare_top_50_only",
                )
                comparison_positions = _sorted_text_options(
                    comparison_frame,
                    "position",
                )
                selected_comparison_positions = comparison_filter_cols[2].multiselect(
                    "Position",
                    comparison_positions,
                    default=comparison_positions,
                    key="war_board_v4_compare_position_filter",
                )
                comparison_large_only = comparison_filter_cols[3].checkbox(
                    "Large movement only",
                    value=False,
                    key="war_board_v4_compare_large_only",
                )
                comparison_warning_contains = comparison_filter_cols[4].text_input(
                    "Warning Contains",
                    "",
                    key="war_board_v4_compare_warning_filter",
                )

            comparison_filtered = comparison_frame[
                comparison_frame["position"].astype(str).isin(
                    selected_comparison_positions
                )
            ].copy()
            if comparison_niners_only:
                comparison_filtered = comparison_filtered[
                    comparison_filtered["in_niners_roster"].fillna(False)
                ]
            if comparison_top_50_only:
                comparison_filtered = comparison_filtered[
                    comparison_filtered["in_top_50"].fillna(False)
                ]
            if comparison_large_only:
                comparison_filtered = comparison_filtered[
                    comparison_filtered["movement_size"].astype(str) == "large"
                ]
            if comparison_warning_contains:
                comparison_filtered = comparison_filtered[
                    comparison_filtered["warning_search_text"].astype(str).str.contains(
                        comparison_warning_contains,
                        case=False,
                        na=False,
                    )
                ]

            comparison_display = comparison_filtered.reindex(
                columns=list(MODEL_V4_OLD_VS_V4_COLUMNS)
            ).reset_index(drop=True)
            st.dataframe(
                comparison_display,
                column_config={
                    "player": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["player"],
                        pinned=True,
                    ),
                    "position": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["position"],
                    ),
                    "fantasy_team": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["fantasy_team"],
                    ),
                    "active_overall_rank": st.column_config.NumberColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["active_overall_rank"],
                    ),
                    "v4_shadow_rank": st.column_config.NumberColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["v4_shadow_rank"],
                    ),
                    "active_value": st.column_config.NumberColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["active_value"],
                        format="%.2f",
                    ),
                    "v4_dynasty_asset_value": st.column_config.NumberColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["v4_dynasty_asset_value"],
                        format="%.2f",
                    ),
                    "active_confidence": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["active_confidence"],
                    ),
                    "v4_confidence": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["v4_confidence"],
                    ),
                    "active_warning": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["active_warning"],
                    ),
                    "v4_warning": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["v4_warning"],
                    ),
                    "movement_direction": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["movement_direction"],
                    ),
                    "movement_size": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["movement_size"],
                    ),
                    "movement_reason": st.column_config.TextColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["movement_reason"],
                    ),
                    "large_unexplained_movement": st.column_config.CheckboxColumn(
                        MODEL_V4_OLD_VS_V4_LABELS["large_unexplained_movement"],
                    ),
                },
                use_container_width=True,
                hide_index=True,
                key="war_board_v4_old_vs_v4_table",
            )

        st.subheader("V4 Promotion Blockers")
        st.warning(MODEL_V4_PROMOTION_BLOCKERS_BANNER)
        st.caption(
            "This panel explains what prevents v4 from becoming the live model. "
            "Some limitations can be accepted only if they stay visible; none of "
            "these rows unlock readiness."
        )
        blocker_rows = build_model_v4_promotion_blocker_rows(
            model_v4_review.preview_rows,
            model_v4_review.source_gap_detail_rows,
            model_v4_review.sanity_fixture_rows,
            model_v4_review.named_player_rows,
        )
        blocker_frame = pd.DataFrame(blocker_rows)
        summary_frame = pd.DataFrame(
            build_model_v4_promotion_blocker_summary_rows(blocker_rows)
        )
        st.dataframe(
            summary_frame,
            column_config={
                "blocker_group_label": st.column_config.TextColumn(
                    "Blocker Group"
                ),
                "blocker_count": st.column_config.NumberColumn("Blockers"),
                "app_promotion_blockers": st.column_config.NumberColumn(
                    "Blocks App Promotion"
                ),
                "final_decision_ready_blockers": st.column_config.NumberColumn(
                    "Blocks Final Ready"
                ),
            },
            use_container_width=True,
            hide_index=True,
            key="war_board_v4_promotion_blocker_summary_table",
        )
        if blocker_frame.empty:
            st.success("No V4 promotion blockers are currently listed.")
        else:
            for group_key, group_label in MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS.items():
                group_frame = blocker_frame[
                    blocker_frame["blocker_group"].astype(str) == group_key
                ]
                with st.expander(
                    group_label,
                    expanded=not group_frame.empty,
                ):
                    if group_frame.empty:
                        st.caption(f"No {group_label.lower()} rows currently shown.")
                    else:
                        display_columns = list(MODEL_V4_PROMOTION_BLOCKER_COLUMNS)
                        st.dataframe(
                            group_frame.reindex(columns=display_columns),
                            column_config={
                                "blocker_group_label": st.column_config.TextColumn(
                                    MODEL_V4_PROMOTION_BLOCKER_LABELS[
                                        "blocker_group_label"
                                    ]
                                ),
                                "blocker": st.column_config.TextColumn(
                                    MODEL_V4_PROMOTION_BLOCKER_LABELS["blocker"]
                                ),
                                "why_it_matters": st.column_config.TextColumn(
                                    MODEL_V4_PROMOTION_BLOCKER_LABELS[
                                        "why_it_matters"
                                    ]
                                ),
                                "affected_players_surfaces": (
                                    st.column_config.TextColumn(
                                        MODEL_V4_PROMOTION_BLOCKER_LABELS[
                                            "affected_players_surfaces"
                                        ]
                                    )
                                ),
                                "next_action": st.column_config.TextColumn(
                                    MODEL_V4_PROMOTION_BLOCKER_LABELS["next_action"]
                                ),
                                "promotion_blocking_scope": (
                                    st.column_config.TextColumn(
                                        MODEL_V4_PROMOTION_BLOCKER_LABELS[
                                            "promotion_blocking_scope"
                                        ]
                                    )
                                ),
                                "blocks_app_promotion": (
                                    st.column_config.CheckboxColumn(
                                        MODEL_V4_PROMOTION_BLOCKER_LABELS[
                                            "blocks_app_promotion"
                                        ]
                                    )
                                ),
                                "blocks_final_decision_ready": (
                                    st.column_config.CheckboxColumn(
                                        MODEL_V4_PROMOTION_BLOCKER_LABELS[
                                            "blocks_final_decision_ready"
                                        ]
                                    )
                                ),
                                "evidence_status": st.column_config.TextColumn(
                                    MODEL_V4_PROMOTION_BLOCKER_LABELS[
                                        "evidence_status"
                                    ]
                                ),
                            },
                            use_container_width=True,
                            hide_index=True,
                            key=f"war_board_v4_promotion_blockers_{group_key}",
                        )

with st.expander("Advanced: confidence rebuild"):
    st.caption(
        "This is the decision-safety confidence layer. It does not change player "
        "scores. Low confidence changes action certainty so shaky rankings are "
        "reviewed instead of silently buried or trusted."
    )
    if confidence_rebuild.issues:
        st.warning("; ".join(confidence_rebuild.issues))
    st.subheader("Action Certainty")
    st.dataframe(
        pd.DataFrame(confidence_rebuild.summary_rows),
        use_container_width=True,
        hide_index=True,
    )
    confidence_frame = pd.DataFrame(confidence_rebuild.rows)
    explanation_frame = pd.DataFrame(confidence_rebuild.explanation_rows)
    if confidence_frame.empty:
        st.dataframe(confidence_frame, use_container_width=True, hide_index=True)
    else:
        confidence_controls = st.columns(2)
        selected_actions = confidence_controls[0].multiselect(
            "Action Certainty",
            confidence_rebuild.action_certainty_levels,
            default=confidence_rebuild.action_certainty_levels,
            key="war_board_confidence_actions",
        )
        selected_players = confidence_controls[1].multiselect(
            "Confidence Player",
            sorted(confidence_frame["player"].dropna().unique()),
            default=[],
            key="war_board_confidence_players",
        )
        confidence_filtered = confidence_frame[
            confidence_frame["action_certainty"].isin(selected_actions)
        ]
        if selected_players:
            confidence_filtered = confidence_filtered[
                confidence_filtered["player"].isin(selected_players)
            ]
        st.subheader("Players")
        st.dataframe(
            confidence_filtered[
                [
                    "action_certainty",
                    "player",
                    "position",
                    "current_model_confidence",
                    "rebuilt_confidence_score",
                    "confidence_delta",
                    "confidence_warning_reasons",
                    "source_coverage_score",
                    "source_freshness_score",
                    "identity_confidence",
                    "core_field_completeness",
                    "feature_agreement",
                    "model_outlier_score",
                    "certainty_reason",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.subheader("Explanation Rows")
        explanation_filtered = explanation_frame
        if selected_players:
            explanation_filtered = explanation_filtered[
                explanation_filtered["player"].isin(selected_players)
            ]
        st.dataframe(
            explanation_filtered[
                [
                    "player",
                    "position",
                    "component",
                    "component_score",
                    "component_weight",
                    "weighted_contribution",
                    "reason",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

with st.expander("Advanced: market edge"):
    st.caption(
        "This is the advantage table: stats/private value minus trade-market value. "
        "Positive means the model is higher than market; negative means the market "
        "is higher than the model. It never feeds private value."
    )
    if market_edge.issues:
        st.warning("; ".join(market_edge.issues))
    else:
        st.subheader("Edge Buckets")
        st.dataframe(
            pd.DataFrame(market_edge.classification_rows),
            use_container_width=True,
            hide_index=True,
        )
        tab_model, tab_market, tab_all = st.tabs(
            ["Model Higher Than Market", "Market Higher Than Model", "All Edges"]
        )
        edge_columns = [
            "edge_confidence_label",
            "player",
            "position",
            "team",
            "private_lve_value",
            "market_trade_value",
            "market_edge_score",
            "edge_classification",
            "confidence_score",
            "warning_summary",
            "source_warning",
        ]
        with tab_model:
            st.dataframe(
                pd.DataFrame(market_edge.model_higher_rows)[edge_columns]
                if market_edge.model_higher_rows
                else pd.DataFrame(columns=edge_columns),
                use_container_width=True,
                hide_index=True,
            )
        with tab_market:
            st.dataframe(
                pd.DataFrame(market_edge.market_higher_rows)[edge_columns]
                if market_edge.market_higher_rows
                else pd.DataFrame(columns=edge_columns),
                use_container_width=True,
                hide_index=True,
            )
        with tab_all:
            all_edges = pd.DataFrame(market_edge.rows)
            st.dataframe(
                all_edges[edge_columns] if not all_edges.empty else all_edges,
                use_container_width=True,
                hide_index=True,
            )

with st.expander("Advanced: player feature receipts"):
    st.caption(
        "Drill into the scoring ingredients for a player. Stats-first source "
        "features are listed first; proxy rows explain when a formula feature is "
        "using a broader normalized source feature."
    )
    if feature_receipts.issues:
        st.warning("; ".join(feature_receipts.issues))
    else:
        receipt_frame = pd.DataFrame(feature_receipts.rows)
        if receipt_frame.empty:
            st.dataframe(receipt_frame, use_container_width=True, hide_index=True)
        else:
            default_players = [
                player
                for player in frame.head(3).get("player", pd.Series(dtype=str)).tolist()
                if player in feature_receipts.players
            ]
            selected_players = st.multiselect(
                "Receipt Player",
                feature_receipts.players,
                default=default_players,
                key="war_board_receipt_players",
            )
            selected_components = st.multiselect(
                "Receipt Component",
                feature_receipts.components,
                default=feature_receipts.components,
                key="war_board_receipt_components",
            )
            receipt_filtered = receipt_frame[
                receipt_frame["player"].isin(selected_players)
                & receipt_frame["component"].isin(selected_components)
            ]
            selected_player_rows = (
                frame[frame["player"].isin(selected_players)]
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
                    page_source="War Board",
                )
            )
            st.subheader("Component Reconciliation")
            st.dataframe(summary_filtered, use_container_width=True, hide_index=True)
            st.subheader("Feature Receipts")
            if sorted_receipts.empty:
                st.info("No feature receipts for the selected players.")
            else:
                st.dataframe(
                    sorted_receipts[list(RECEIPT_DISPLAY_COLUMNS)].rename(
                        columns=RECEIPT_COLUMN_LABELS
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

with st.expander("Advanced: identity audit"):
    st.caption(
        "Checks Sleeper, local player IDs, and nflverse/stat IDs before trusting "
        "stats. High-value players with low identity confidence are blocked from "
        "decision trust."
    )
    if identity_audit.issues:
        st.warning("; ".join(identity_audit.issues))
    else:
        st.subheader("Identity Summary")
        st.dataframe(
            pd.DataFrame(identity_audit.summary_rows),
            use_container_width=True,
            hide_index=True,
        )
        if identity_audit.blocked_rows:
            st.subheader("Blocked High-Value Rankings")
            st.dataframe(
                pd.DataFrame(identity_audit.blocked_rows),
                use_container_width=True,
                hide_index=True,
            )
        identity_frame = pd.DataFrame(identity_audit.rows)
        if identity_frame.empty:
            st.dataframe(identity_frame, use_container_width=True, hide_index=True)
        else:
            identity_controls = st.columns(3)
            selected_statuses = identity_controls[0].multiselect(
                "Identity Status",
                identity_audit.statuses,
                default=identity_audit.statuses,
                key="war_board_identity_statuses",
            )
            selected_methods = identity_controls[1].multiselect(
                "Match Method",
                identity_audit.match_methods,
                default=identity_audit.match_methods,
                key="war_board_identity_methods",
            )
            blocked_only = identity_controls[2].checkbox(
                "Blocked Only",
                key="war_board_identity_blocked_only",
            )
            identity_filtered = identity_frame[
                identity_frame["audit_status"].isin(selected_statuses)
                & identity_frame["match_method"].isin(selected_methods)
            ]
            if blocked_only:
                identity_filtered = identity_filtered[
                    identity_filtered["ranking_trust_status"] == "blocked_identity_review"
                ]
            st.dataframe(
                identity_filtered[
                    [
                        "ranking_trust_status",
                        "audit_status",
                        "player",
                        "position",
                        "team",
                        "identity_confidence",
                        "high_value_score",
                        "match_method",
                        "match_status",
                        "name_agreement",
                        "position_agreement",
                        "team_agreement",
                        "duplicate_name_count",
                        "sleeper_id",
                        "nflverse_gsis_id",
                        "pfr_id",
                        "manual_review_required",
                        "manual_review_status",
                        "manual_resolution",
                        "manual_review_note",
                        "review_owner",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

with st.expander("Advanced: source coverage audit"):
    st.caption(
        "Shows which players have real source data by bucket and which features "
        "are missing, estimated, or only covered by another source type. Missing "
        "core buckets lower coverage-adjusted confidence; this does not fill fake "
        "stats into the model. Projection rows marked local baseline are local "
        "baseline, not forecast."
    )
    if source_coverage.issues:
        st.warning("; ".join(source_coverage.issues))
    else:
        st.subheader("Coverage Summary")
        st.dataframe(
            pd.DataFrame(source_coverage.summary_rows),
            use_container_width=True,
            hide_index=True,
        )

        player_coverage_frame = pd.DataFrame(source_coverage.player_rows)
        bucket_coverage_frame = pd.DataFrame(source_coverage.bucket_rows)
        feature_coverage_frame = pd.DataFrame(source_coverage.feature_rows)
        if player_coverage_frame.empty:
            st.dataframe(player_coverage_frame, use_container_width=True, hide_index=True)
        else:
            coverage_controls = st.columns(4)
            selected_coverage_statuses = coverage_controls[0].multiselect(
                "Coverage Status",
                source_coverage.statuses,
                default=source_coverage.statuses,
                key="war_board_source_coverage_statuses",
            )
            selected_coverage_buckets = coverage_controls[1].multiselect(
                "Coverage Bucket",
                source_coverage.buckets,
                default=source_coverage.buckets,
                key="war_board_source_coverage_buckets",
            )
            missing_or_low_only = coverage_controls[2].checkbox(
                "Missing/Low Only",
                key="war_board_source_coverage_low_only",
            )
            critical_only = coverage_controls[3].checkbox(
                "Critical Buckets Only",
                key="war_board_source_coverage_critical_only",
            )

            player_filtered = player_coverage_frame[
                player_coverage_frame["coverage_status"].isin(selected_coverage_statuses)
            ]
            if missing_or_low_only:
                player_filtered = player_filtered[
                    (player_filtered["coverage_pct"] < 75)
                    | (player_filtered["missing_critical_count"] > 0)
                ]

            st.subheader("Players")
            st.dataframe(
                player_filtered[
                    [
                        "coverage_status",
                        "player",
                        "position",
                        "team",
                        "source_gap_summary",
                        "source_gap_scopes",
                        "coverage_pct",
                        "model_confidence",
                        "coverage_confidence_penalty",
                        "coverage_adjusted_confidence",
                        "missing_critical_inputs",
                        "missing_bucket_count",
                        "imputed_bucket_count",
                        "high_value_score",
                        "warning_summary",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Bucket Coverage")
            bucket_filtered = bucket_coverage_frame[
                bucket_coverage_frame["bucket"].isin(selected_coverage_buckets)
            ]
            if critical_only:
                bucket_filtered = bucket_filtered[bucket_filtered["critical_bucket"]]
            if missing_or_low_only:
                bucket_filtered = bucket_filtered[bucket_filtered["coverage_pct"] < 75]
            st.dataframe(
                bucket_filtered,
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Feature Coverage Receipts")
            feature_filtered = feature_coverage_frame[
                feature_coverage_frame["bucket"].isin(selected_coverage_buckets)
            ]
            if critical_only:
                feature_filtered = feature_filtered[feature_filtered["critical_bucket"]]
            if missing_or_low_only:
                feature_filtered = feature_filtered[
                    feature_filtered["feature_data_status"].isin(
                        ["missing", "covered_elsewhere", "estimated_or_proxy"]
                    )
                ]
            st.dataframe(
                feature_filtered[
                    [
                        "player",
                        "position",
                        "bucket",
                        "feature_name",
                        "feature_data_status",
                        "coverage_credit",
                        "normalized_score",
                        "source_key",
                        "source_type",
                        "source_confidence",
                        "source_reliability",
                        "missing_reason",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

with st.expander("Advanced: outlier detector"):
    st.caption(
        "Automatic tripwires for suspicious rankings. Missing market references, "
        "missing injury/projection data, identity issues, one-feature-driven ranks, "
        "and true ranking weirdness are separated so the next action is clear."
    )
    if model_outliers.issues:
        st.warning("; ".join(model_outliers.issues))
    else:
        st.subheader("Buckets")
        st.dataframe(
            pd.DataFrame(model_outliers.bucket_rows),
            use_container_width=True,
            hide_index=True,
        )
        st.subheader("Outlier Types")
        st.dataframe(
            pd.DataFrame(model_outliers.summary_rows),
            use_container_width=True,
            hide_index=True,
        )
        outlier_frame = pd.DataFrame(model_outliers.rows)
        if outlier_frame.empty:
            st.dataframe(outlier_frame, use_container_width=True, hide_index=True)
        else:
            outlier_controls = st.columns(3)
            selected_buckets = outlier_controls[0].multiselect(
                "Outlier Bucket",
                model_outliers.buckets,
                default=model_outliers.buckets,
                key="war_board_outlier_buckets",
            )
            selected_types = outlier_controls[1].multiselect(
                "Outlier Type",
                model_outliers.outlier_types,
                default=model_outliers.outlier_types,
                key="war_board_outlier_types",
            )
            selected_severity = outlier_controls[2].multiselect(
                "Severity",
                sorted(outlier_frame["severity"].dropna().unique()),
                default=sorted(outlier_frame["severity"].dropna().unique()),
                key="war_board_outlier_severity",
            )
            outlier_filtered = outlier_frame[
                outlier_frame["bucket"].isin(selected_buckets)
                & outlier_frame["outlier_type"].isin(selected_types)
                & outlier_frame["severity"].isin(selected_severity)
            ]
            st.dataframe(
                outlier_filtered[
                    [
                        "bucket",
                        "outlier_type",
                        "severity",
                        "review_status",
                        "next_action",
                        "player",
                        "position",
                        "team",
                        "model_rank",
                        "position_rank",
                        "private_rank",
                        "market_rank",
                        "war_score",
                        "private_score",
                        "trade_liquidity",
                        "confidence_score",
                        "component",
                        "source_feature",
                        "reason",
                        "suggested_review",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

with st.expander("Advanced: player compare tool"):
    st.caption(
        "Compare two players side by side. The gap-driver table shows which "
        "feature contributions create the scoring gap."
    )
    if len(compare_options) < 2:
        st.info("Need at least two scored players to compare.")
    else:
        labels_by_id = {
            str(option["player_id"]): str(option["label"]) for option in compare_options
        }
        player_ids = list(labels_by_id)
        compare_controls = st.columns(2)
        player_a = compare_controls[0].selectbox(
            "Player A",
            player_ids,
            index=0,
            format_func=lambda player_id: labels_by_id[player_id],
            key="war_board_compare_player_a",
        )
        player_b = compare_controls[1].selectbox(
            "Player B",
            player_ids,
            index=1,
            format_func=lambda player_id: labels_by_id[player_id],
            key="war_board_compare_player_b",
        )
        comparison = _load_player_compare(
            active_data_pack,
            active_fingerprint,
            str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
            path_fingerprint(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
            player_a,
            player_b,
        )
        if comparison.issues:
            st.warning("; ".join(comparison.issues))
        else:
            st.subheader("Final Score Gap")
            st.dataframe(
                pd.DataFrame(comparison.score_rows),
                use_container_width=True,
                hide_index=True,
            )
            st.subheader("Market Edge")
            st.dataframe(
                pd.DataFrame(comparison.market_edge_rows),
                use_container_width=True,
                hide_index=True,
            )
            st.subheader("Component Gap")
            st.dataframe(
                pd.DataFrame(comparison.component_rows),
                use_container_width=True,
                hide_index=True,
            )
            st.subheader("Top Gap Drivers")
            st.dataframe(
                pd.DataFrame(comparison.gap_driver_rows),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("All Compared Features"):
                st.dataframe(
                    pd.DataFrame(comparison.feature_rows),
                    use_container_width=True,
                    hide_index=True,
                )
            with st.expander("Warnings And Flags"):
                st.dataframe(
                    pd.DataFrame(comparison.warning_rows),
                    use_container_width=True,
                    hide_index=True,
                )

with st.expander("Advanced: ranking audit"):
    st.caption(
        "This table shows which column drives each visible board order. It is for "
        "model debugging, not a recommendation."
    )
    audit_summary = pd.DataFrame(ranking_audit_summary_rows(ranking_audit))
    st.dataframe(audit_summary, use_container_width=True, hide_index=True)
    audit_frame = pd.DataFrame(ranking_audit.rows)
    if audit_frame.empty:
        st.dataframe(audit_frame, use_container_width=True, hide_index=True)
    else:
        audit_controls = st.columns(3)
        audit_pages = audit_controls[0].multiselect(
            "Audit Page",
            ranking_audit.pages,
            default=ranking_audit.pages,
        )
        audit_sources = audit_controls[1].multiselect(
            "Audit Source",
            ranking_audit.sources,
            default=ranking_audit.sources,
        )
        audit_rank_columns = audit_controls[2].multiselect(
            "Rank Column",
            ranking_audit.rank_columns,
            default=ranking_audit.rank_columns,
        )
        audit_filtered = audit_frame[
            audit_frame["page"].isin(audit_pages)
            & audit_frame["source"].isin(audit_sources)
            & audit_frame["rank_column"].isin(audit_rank_columns)
        ]
        st.dataframe(audit_filtered, use_container_width=True, hide_index=True)
