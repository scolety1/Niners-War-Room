from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.demo_source_labels import demo_source_label
from app.components.human_labels import human_label, human_labels
from app.components.player_detail_panel import PlayerDetail, render_player_detail_panel
from app.components.trust_status import render_page_trust_banner
from src.config.settings import get_settings
from src.services.data_pack_health_service import build_data_pack_health_report
from src.services.market_gap_service import build_market_gap_report
from src.services.ranking_readiness_service import build_ranking_readiness
from src.services.trade_service import build_trade_central


@st.cache_data
def _load_board(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_trade_central(active_data_pack)


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


@st.cache_data
def _load_market_gap(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint
    return build_market_gap_report(active_data_pack)


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
board = _load_board(active_data_pack, active_fingerprint)
health = _load_health(active_data_pack, active_fingerprint)
market_gap = _load_market_gap(active_data_pack, active_fingerprint)
ranking_readiness = build_ranking_readiness(active_data_pack)
player_frame = pd.DataFrame(board.player_rows)
roster_context_frame = pd.DataFrame(board.sell_rows)
external_asset_context_frame = pd.DataFrame(board.buy_rows)
market_context_frame = pd.DataFrame(board.market_edge_rows)
context_pairing_frame = pd.DataFrame(board.package_rows)
path_frame = pd.DataFrame(board.path_rows)
market_gap_frame = pd.DataFrame(market_gap.rows)

MARKET_SIGNAL_LABELS = {
    "opponent_roster_model_gap_context_review": "Opponent Roster Model Gap Context",
    "my_roster_market_premium_context_review": "My Roster Market Premium Context",
    "my_roster_model_gap_context_review": "My Roster Model Gap Context",
    "opponent_roster_market_premium_context_review": (
        "Opponent Roster Market Premium Context"
    ),
    "model_higher_market_context_review": "Model Higher Market Context",
    "market_higher_model_context_review": "Market Higher Model Context",
    "roughly_aligned_review": "Roughly Aligned",
    "partial_market_context_review": "Partial Market Context",
    "missing_inputs_review": "Missing Inputs",
}


def _market_signal_label(value: object) -> str:
    text = str(value or "")
    return MARKET_SIGNAL_LABELS.get(text, human_label(text))


def _trade_detail_options(*frames: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for frame in frames:
        if frame.empty or "player" not in frame:
            continue
        rows.append(frame.copy())
    if not rows:
        return pd.DataFrame()
    detail_frame = pd.concat(rows, ignore_index=True, sort=False).fillna("")
    return detail_frame.drop_duplicates(subset=["player"], keep="first")

st.title("External Asset Reviews")
st.caption(demo_source_label(active_data_pack))
render_page_trust_banner(
    health,
    calibration_passed=ranking_readiness.calibration_passed,
    review_only_message=ranking_readiness.message if ranking_readiness.review_only else "",
    review_only_detail=(
        "External Asset Reviews stays visible for context, but offers are review-only "
        "until stats value, market value, identity, and coverage pass audit."
    )
    if ranking_readiness.review_only
    else "",
)
if ranking_readiness.review_only:
    st.caption(
        "Review-only context. Use it to find possible conversation areas, "
        "not to auto-send offers."
    )
    st.info(
        "Start here: Roster Context is your roster, External Asset Context is opponent players, "
        "and Market Context is where disagreement may create a question to review."
    )
else:
    st.caption("Context groups passed calibration and can be reviewed.")
    st.success(
        "Start here: compare roster context against external asset context, then open "
        "Context Drill-Down when a roster question remains open."
    )

left, middle, right = st.columns(3)
roster_review_count = (
    int((roster_context_frame["signal"] == "Roster Context Review").sum())
    if not roster_context_frame.empty
    else 0
)
left.metric("Roster Reviews", roster_review_count)
middle.metric("External Context", len(external_asset_context_frame))
right.metric("Snapshot", board.snapshot_date or "unknown")

if roster_context_frame.empty and external_asset_context_frame.empty:
    st.dataframe(player_frame, use_container_width=True, hide_index=True)
elif health.placeholder_model_output_count:
    st.info(
        "Model scores are not loaded yet. Trade signals stay hidden until veteran "
        "scoring inputs are real."
    )
    st.dataframe(
        player_frame[["player", "pos", "league_rank"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption(
        "Model Value is our stats-first value. Market Context is liquidity/cost. "
        "Deal Friction is only rough context for how hard a conversation may be."
    )

    detail_frame = _trade_detail_options(
        roster_context_frame,
        external_asset_context_frame,
        player_frame,
    )
    if not detail_frame.empty:
        detail_player = st.selectbox(
            "Inspect trade-context player",
            detail_frame["player"].astype(str).tolist(),
            key="trade_review_detail_player",
        )
        detail_row = detail_frame[detail_frame["player"].astype(str) == detail_player]
        if not detail_row.empty:
            row = detail_row.iloc[0]
            render_player_detail_panel(
                PlayerDetail(
                    player=row.get("player"),
                    position=row.get("pos") or row.get("position"),
                    nfl_team=row.get("team"),
                    model_value=row.get("model_value"),
                    rank_or_slot=row.get("league_rank"),
                    trust_status=row.get("confidence"),
                    why_this_rank=row.get("acquisition_path")
                    or row.get("signal")
                    or row.get("buy_signal"),
                    strongest_signals=(
                        f"Model interest {row.get('model_desirability', 'Missing')}; "
                        f"trade value {row.get('trade_value', 'Missing')}"
                    ),
                    weakest_signals=(
                        f"Risk {row.get('risk', 'Missing')}; "
                        f"deal friction {row.get('acceptance_likelihood', 'Missing')}"
                    ),
                    warning_groups=row.get("warning_reason") or row.get("risk"),
                    market_context=(
                        f"Market Context {row.get('market_value', 'Missing')}; "
                        f"Model vs Market {row.get('market_edge', 'Missing')}; "
                        "display-only context."
                    ),
                    receipt_pointer="Market Context and Context Drill-Down tabs",
                    source_pointer=active_data_pack,
                ),
                label=f"Inspect {detail_player}",
                key=f"trade_review_detail_{detail_player}",
            )

    roster_tab, external_asset_tab, market_tab, context_pairing_tab = st.tabs(
        [
            "Roster Context",
            "External Asset Context",
            "Market Context",
            "Context Drill-Down",
        ]
    )

    with roster_tab:
        signals = st.multiselect("Roster Review Group", board.signals, default=board.signals)
        filtered_players = roster_context_frame[
            roster_context_frame["signal"].isin(signals)
        ]
        st.caption("My roster only. Sorted by review group, then context value.")
        st.dataframe(
            filtered_players[
                [
                    "player",
                    "pos",
                    "signal",
                    "team",
                    "model_value",
                    "market_value",
                    "market_edge",
                    "model_desirability",
                    "acceptance_likelihood",
                    "trade_value",
                    "league_rank",
                    "confidence",
                    "risk",
                ]
            ],
                column_config={
                    "player": "Player",
                    "pos": "Pos",
                    "signal": "Roster Review Group",
                    "team": "Roster",
                    "model_value": "Model Value",
                    "market_value": "Market Context",
                    "market_edge": "Model vs Market",
                    "model_desirability": "Model Roster Review Interest",
                    "acceptance_likelihood": "Conversation Difficulty",
                    "trade_value": "Trade Value",
                    "league_rank": "League Rank",
                "confidence": "Confidence",
                "risk": "Risk",
            },
            use_container_width=True,
            hide_index=True,
        )

    with external_asset_tab:
        st.caption(
            "Opponent players only. Sorted by model context, with deal-friction "
            "context shown separately."
        )
        if external_asset_context_frame.empty:
            st.info("No opponent players are available in the selected pack.")
            st.dataframe(
                external_asset_context_frame,
                use_container_width=True,
                hide_index=True,
            )
        else:
            external_review_groups = st.multiselect(
                "External Review Group",
                board.buy_signals,
                default=board.buy_signals,
            )
            filtered_external_assets = external_asset_context_frame[
                external_asset_context_frame["buy_signal"].isin(external_review_groups)
            ]
            st.dataframe(
                filtered_external_assets[
                    [
                        "player",
                        "pos",
                        "team",
                        "buy_signal",
                        "model_value",
                        "market_value",
                        "market_edge",
                        "model_desirability",
                        "acceptance_likelihood",
                        "acquisition_path",
                        "confidence",
                        "warning_reason",
                    ]
                ],
                column_config={
                    "player": "Player",
                    "pos": "Pos",
                    "team": "Opponent Team",
                    "buy_signal": "External Review Group",
                    "model_value": "Model Value",
                    "market_value": "Market Context",
                    "market_edge": "Model vs Market",
                    "model_desirability": "Model External Context",
                    "acceptance_likelihood": "Conversation Difficulty",
                    "acquisition_path": "Review Path",
                    "confidence": "Confidence",
                    "warning_reason": "Warning",
                },
                use_container_width=True,
                hide_index=True,
            )

    with market_tab:
        st.caption(
            "Review-only market comparison. League rank and dynasty startup ADP "
            "are normalized to 0-100 where rank/ADP 1.0 equals 100. Context rows show "
            "where Model Value and Market Context disagree. None of this changes "
            "private football value."
        )
        st.subheader("Normalized Market Gap")
        if market_gap.issues:
            st.warning("; ".join(market_gap.issues))
        if market_gap_frame.empty:
            st.info("No market-gap rows are available for the selected pack.")
            st.dataframe(market_gap_frame, use_container_width=True, hide_index=True)
        else:
            hint_options = sorted(
                value
                for value in market_gap_frame["application_hint"].dropna().unique()
                if value
            )
            selected_hints = st.multiselect(
                "Market Gap Signal",
                hint_options,
                default=hint_options,
                format_func=_market_signal_label,
            )
            filtered_gap = market_gap_frame[
                market_gap_frame["application_hint"].isin(selected_hints)
            ].copy()
            filtered_gap["application_hint_label"] = filtered_gap["application_hint"].map(
                _market_signal_label
            )
            filtered_gap["warning_label"] = filtered_gap["warning_flags"].map(human_labels)
            st.dataframe(
                filtered_gap[
                    [
                        "player",
                        "position",
                        "owner_team",
                        "owner_side",
                        "model_value",
                        "league_rank",
                        "league_rank_normalized_score",
                        "dynasty_startup_adp",
                        "adp_normalized_score",
                        "market_reference_score",
                        "model_vs_reference_gap",
                        "application_hint_label",
                        "disagreement_band",
                        "warning_label",
                    ]
                ],
                column_config={
                    "player": "Player",
                    "position": "Pos",
                    "owner_team": "Owner",
                    "owner_side": "Side",
                    "model_value": "Model Value",
                    "league_rank": "League Rank",
                    "league_rank_normalized_score": "League Rank 0-100",
                    "dynasty_startup_adp": "Dynasty Startup ADP",
                    "adp_normalized_score": "ADP 0-100",
                    "market_reference_score": "Market Ref 0-100",
                    "model_vs_reference_gap": "Model Gap",
                    "application_hint_label": "Review Context",
                    "disagreement_band": "Gap Band",
                    "warning_label": "Warnings",
                },
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("How to read Market Gap"):
                st.write(
                    "Opponent-roster model-gap rows are opponent players where our "
                    "model is high and both league-rank and ADP scores are low. "
                    "My-roster market-premium rows are our players where the model "
                    "is low and both market/reference scores are high."
                )
                st.write(
                    "If one of league rank or ADP is missing, the row stays visible "
                    "as Partial Market Context instead of a normal watch signal."
                )

        st.subheader("Market Context Finder")
        st.caption(
            "Largest gaps between our Model Value and Market Context. Market "
            "context is a comparison surface only, not a private-value input."
        )
        if market_context_frame.empty:
            st.info("No market-context rows are available yet.")
            st.dataframe(market_context_frame, use_container_width=True, hide_index=True)
        else:
            edge_types = st.multiselect(
                "Context Type",
                board.edge_types,
                default=board.edge_types,
            )
            filtered_edges = market_context_frame[
                market_context_frame["edge_type"].isin(edge_types)
            ]
            st.dataframe(
                filtered_edges[
                    [
                        "side",
                        "player",
                        "pos",
                        "team",
                        "signal",
                        "model_value",
                        "market_value",
                        "market_edge",
                        "edge_type",
                        "model_desirability",
                        "acceptance_likelihood",
                    ]
                ],
                column_config={
                    "side": "Side",
                    "player": "Player",
                    "pos": "Pos",
                    "team": "Team",
                    "signal": "Signal",
                    "model_value": "Model Value",
                    "market_value": "Market Context",
                    "market_edge": "Model vs Market",
                    "edge_type": "Context Type",
                    "model_desirability": "Model Interest",
                    "acceptance_likelihood": "Conversation Difficulty",
                },
                use_container_width=True,
                hide_index=True,
            )

    with context_pairing_tab:
        st.caption(
            "Review-only context. These rows are model-equivalence and "
            "conversation-shape drilldowns only. No offer is created, and the app "
            "does not tell you to send one. Model Gap, Market Context, Deal Friction, and "
            "Roster Spot Cost are separate on purpose."
        )
        if context_pairing_frame.empty:
            st.info(
                "No context rows yet. Add opponent rosters/picks or scored "
                "external context rows to generate review-only context rows."
            )
            st.dataframe(context_pairing_frame, use_container_width=True, hide_index=True)
        else:
            st.dataframe(
                context_pairing_frame[
                    [
                        "package",
                        "counterparty",
                        "incoming",
                        "outgoing",
                        "model_value",
                        "market_value",
                        "model_edge",
                        "acceptance_likelihood",
                        "model_desirability",
                        "roster_spot_cost",
                        "opponent_benefit",
                        "trade_label",
                    ]
                ],
                column_config={
                    "package": "Context Pairing",
                    "counterparty": "Counterparty",
                    "incoming": "Context Asset A",
                    "outgoing": "Context Asset B",
                    "model_value": "Model Value",
                    "market_value": "Market Context",
                    "model_edge": "Model Gap",
                    "acceptance_likelihood": "Conversation Difficulty",
                    "model_desirability": "Model Desirability",
                    "roster_spot_cost": "Roster Spot Cost",
                    "opponent_benefit": "Opponent Benefit",
                    "trade_label": "Review Context",
                },
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Advanced: pick path audit"):
            if path_frame.empty:
                st.dataframe(path_frame, use_container_width=True, hide_index=True)
            else:
                path_signals = st.multiselect(
                    "Path Signal",
                    board.pick_signals,
                    default=board.pick_signals,
                )
                filtered_paths = path_frame[path_frame["path_signal"].isin(path_signals)]
                st.dataframe(
                    filtered_paths[
                        [
                            "player",
                            "signal",
                            "trade_value",
                            "pick",
                            "certainty",
                            "pick_value",
                            "value_gap",
                            "path_signal",
                        ]
                    ],
                    column_config={
                        "player": "Player",
                        "signal": "Signal",
                        "trade_value": "Trade Value",
                        "pick": "Pick",
                        "certainty": "Certainty",
                        "pick_value": "Pick Value",
                        "value_gap": "Gap",
                        "path_signal": "Path",
                    },
                    use_container_width=True,
                    hide_index=True,
                )
