from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.trust_status import render_page_trust_banner
from src.config.settings import get_settings
from src.services.data_pack_health_service import build_data_pack_health_report
from src.services.forced_release_strategy_service import build_forced_release_strategy
from src.services.league_service import build_league_intel
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    RECEIPT_COLUMN_LABELS,
    RECEIPT_DISPLAY_COLUMNS,
    build_player_feature_receipts,
    receipt_rows_for_players,
)
from src.services.ranking_readiness_service import build_ranking_readiness


@st.cache_data
def _load_board(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_league_intel(active_data_pack)


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


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
board = _load_board(active_data_pack, active_fingerprint)
health = _load_health(active_data_pack, active_fingerprint)
ranking_readiness = build_ranking_readiness(active_data_pack)
strategy = _load_strategy(active_data_pack, active_fingerprint)
feature_receipts = _load_feature_receipts(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    path_fingerprint(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
)
pressure_frame = pd.DataFrame(board.pressure_rows)
release_frame = pd.DataFrame(board.default_release_rows)
target_frame = pd.DataFrame(board.target_rows)

st.title("League Targets")
st.caption(f"`{active_data_pack}`")
render_page_trust_banner(
    health,
    calibration_passed=ranking_readiness.calibration_passed,
    review_only_message=ranking_readiness.message if ranking_readiness.review_only else "",
    review_only_detail=(
        "League Targets stays visible for audit, but every target bucket is "
        "review-only until pressure, availability, identity, and source gates pass."
    )
    if ranking_readiness.review_only
    else "",
)
if ranking_readiness.review_only:
    st.caption(
        "Review-only target lab. Pressure rows explain rule-created supply; "
        "target categories are audit prompts, not buy instructions."
    )
    st.info(
        "Start here: check Likely Forced Releases and Cheap Targets first. "
        "Expensive Targets are watch-list names, not bargain targets."
    )
else:
    st.caption("Opponent pressure and target tables passed calibration.")
    st.success(
        "Start here: check Likely Forced Releases and Cheap Targets, then compare "
        "Model vs Market targets."
    )

left, middle, right = st.columns(3)
under_pressure = (
    int((pressure_frame["forced_release_pain"] >= 45).sum())
    if not pressure_frame.empty
    and "forced_release_pain" in pressure_frame.columns
    else int((pressure_frame["pressure_count"] > 0).sum())
    if not pressure_frame.empty
    else 0
)
left.metric("Teams Under Pressure", under_pressure)
middle.metric("Likely Forced Releases", len(board.default_release_rows))
right.metric("Snapshot", board.snapshot_date or "unknown")

if pressure_frame.empty:
    st.dataframe(pressure_frame, use_container_width=True, hide_index=True)
elif health.placeholder_model_output_count:
    st.info(
        "Model scores are not loaded yet. League pressure inventory is visible; "
        "release-target recommendations stay hidden until veteran scores are real."
    )
    st.dataframe(
        pressure_frame[
            [
                "team",
                "pressure_level",
                "pressure_count",
                "forced_release_count",
                "official_top_five_count",
                "roster_count",
                "protect_limit",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.subheader("Target Buckets")
    target_columns = [
        "target_category",
        "team",
        "player",
        "pos",
        "asset_lifecycle_label",
        "availability_signal",
        "acquisition_value",
        "stats_value",
        "market_value",
        "market_edge",
        "confidence",
        "confidence_label",
        "confidence_explanation",
        "opportunity_reason",
    ]
    if target_frame.empty:
        st.info(
            "No opponent target rows are available in this pack. This usually means "
            "the selected pack only contains your roster or model outputs are not complete."
        )
    else:
        category_tabs = st.tabs(board.target_categories or ["All Targets"])
        for tab, category in zip(category_tabs, board.target_categories, strict=False):
            with tab:
                category_frame = pd.DataFrame(board.rows_by_category.get(category, []))
                st.dataframe(
                    category_frame.reindex(columns=target_columns),
                    column_config={
                        "target_category": "Target Category",
                        "team": "Team",
                        "player": "Player",
                        "pos": "Pos",
                        "asset_lifecycle_label": "Lifecycle",
                        "availability_signal": "Availability",
                        "acquisition_value": st.column_config.NumberColumn(
                            "Acquisition Value",
                            help=(
                                "Target score built from stats value, confidence, "
                                "market edge, and rule-created availability."
                            ),
                            format="%.2f",
                        ),
                        "stats_value": st.column_config.NumberColumn(
                            "Model Value",
                            help="Private LVE football/stat value.",
                            format="%.2f",
                        ),
                        "market_value": st.column_config.NumberColumn(
                            "Trade Market",
                            help="Crowd/liquidity cost estimate.",
                            format="%.2f",
                        ),
                        "market_edge": st.column_config.NumberColumn(
                            "Model vs Market",
                            help="Model Value minus Trade Market.",
                            format="%.2f",
                        ),
                        "confidence": st.column_config.NumberColumn(
                            "Confidence",
                            format="%.2f",
                        ),
                        "confidence_label": st.column_config.TextColumn(
                            "Confidence Label",
                            help=(
                                "Plain-English confidence tier: strong, usable, "
                                "review, weak, or blocked."
                            ),
                        ),
                        "confidence_explanation": "Confidence Why",
                        "opportunity_reason": "Why This Is Here",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

    with st.expander("Opportunity pressure by team"):
        levels = st.multiselect(
            "Pressure Level",
            board.pressure_levels,
            default=board.pressure_levels,
        )
        filtered_pressure = pressure_frame[
            pressure_frame["pressure_level"].isin(levels)
        ]
        pressure_display_columns = [
            "team",
            "pressure_level",
            "likely_forced_release",
            "likely_forced_release_value",
            "forced_release_pain",
            "release_decision_difficulty",
            "top_five_value_gap",
            "opportunity_summary",
        ]
        st.dataframe(
            filtered_pressure.reindex(columns=pressure_display_columns),
            column_config={
                "team": "Team",
                "pressure_level": "Pressure",
                "likely_forced_release": "Likely Required Release Slot",
                "likely_forced_release_value": st.column_config.NumberColumn(
                    "Drop Value",
                    help=(
                        "Model/player value of the likely Required Top-Five "
                        "Release Slot from this roster's league-rank top five."
                    ),
                    format="%.2f",
                ),
                "forced_release_pain": st.column_config.NumberColumn(
                    "Pain",
                    help=(
                        "How costly the Required Top-Five Release Slot is by "
                        "model/player value."
                    ),
                    format="%.2f",
                ),
                "release_decision_difficulty": st.column_config.NumberColumn(
                    "Difficulty",
                    help="How hard it is to choose the required roster top-five release.",
                    format="%.2f",
                ),
                "top_five_value_gap": st.column_config.NumberColumn(
                    "Secondary Gap",
                    help=(
                        "Diagnostic only: Required Top-Five Release Slot value "
                        "minus the easiest regular cut value."
                    ),
                    format="%.2f",
                ),
                "opportunity_summary": "Opportunity",
            },
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("**Advanced Pressure Diagnostics**")
        st.caption(
            "Secondary comparison rows are diagnostic only. The likely Required "
            "Top-Five Release Slot is the player to care about; regular cuts only "
            "explain whether that release is painful."
        )
        diagnostics_columns = [
            "team",
            "likely_forced_release",
            "forced_release_pain",
            "easy_drop_available",
            "easy_non_top_five_drop",
            "top_five_value_gap",
            "replacement_depth_count",
        ]
        st.dataframe(
            filtered_pressure.reindex(columns=diagnostics_columns),
            column_config={
                "team": "Team",
                "likely_forced_release": "Likely Required Release Slot",
                "forced_release_pain": st.column_config.NumberColumn("Pain", format="%.2f"),
                "easy_drop_available": "Secondary Easy Cut Exists?",
                "easy_non_top_five_drop": "Secondary Comparison Drop",
                "top_five_value_gap": st.column_config.NumberColumn(
                    "Secondary Gap",
                    format="%.2f",
                ),
                "replacement_depth_count": "Replacement Depth",
            },
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Advanced: likely forced releases"):
        candidate_columns = [
            "team",
            "player",
            "pos",
            "asset_lifecycle_label",
            "availability_signal",
            "acquisition_value",
            "stats_value",
            "market_value",
            "market_edge",
            "league_rank",
            "confidence",
            "confidence_label",
            "confidence_explanation",
            "opportunity_reason",
        ]
        st.dataframe(
            release_frame.reindex(columns=candidate_columns),
            column_config={
                "team": "Team",
                "player": "Player",
                "pos": "Pos",
                "asset_lifecycle_label": "Lifecycle",
                "availability_signal": "Availability",
                "acquisition_value": "Acquisition Value",
                "stats_value": "Model Value",
                "market_value": "Trade Market",
                "market_edge": "Model vs Market",
                "league_rank": "League Rank",
                "confidence": "Confidence",
                "confidence_label": "Confidence Label",
                "confidence_explanation": "Confidence Why",
                "opportunity_reason": "Why This Is Here",
            },
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Advanced: target receipts"):
        target_receipt_source = (
            target_frame.rename(columns={"pos": "position"})
            .head(25)
            .to_dict("records")
        )
        receipt_rows = receipt_rows_for_players(
            feature_receipts,
            target_receipt_source,
            player_column="player",
            position_column="position",
            page_source="League Targets",
        )
        if feature_receipts.issues:
            st.warning("; ".join(feature_receipts.issues))
        if not receipt_rows:
            st.info("No target receipts are available for the current pack.")
        else:
            st.dataframe(
                pd.DataFrame(receipt_rows)[list(RECEIPT_DISPLAY_COLUMNS)].rename(
                    columns=RECEIPT_COLUMN_LABELS
                ),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Advanced: forced-release strategy audit"):
        strategy_team_frame = pd.DataFrame(strategy.team_rows)
        if not strategy_team_frame.empty:
            st.caption(
                "This is the detailed audit behind the pressure table above. The "
                "normal target views are the pressure table and target buckets."
            )
            st.dataframe(
                strategy_team_frame[
                    [
                        "team",
                        "league_rank_top_five",
                        "required_release_count",
                        "default_release",
                        "forced_release_pain",
                        "release_decision_difficulty",
                        "top_five_value_gap",
                        "pressure_level",
                        "decision_status",
                        "team_explanation",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )
        st.write(
            "Pressure matters only when it creates opportunity for us: a likely "
            "release, a discounted trade conversation, or an offline-draft target. "
            "A team having a strong player is not by itself an opportunity."
        )

    with st.expander("Advanced: likely release target audit"):
        target_frame = pd.DataFrame(strategy.opponent_target_rows)
        target_columns = [
            "team",
            "player",
            "pos",
            "league_rank",
            "keeper_score",
            "drop_score",
            "likely_target_value",
            "opponent_release_target_score",
            "rule_explanation",
            "strategy_reason",
            "action_label",
            "score_explanation",
            "next_step",
        ]
        st.dataframe(
            target_frame.reindex(columns=target_columns),
            use_container_width=True,
            hide_index=True,
        )
