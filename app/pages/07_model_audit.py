from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import get_settings
from src.models.pick_values import BRIEF_PICK_VALUE_CURVE_1000, PickValueConfig

settings = get_settings()

st.title("Model Audit")
st.caption(f"`{settings.active_data_pack}`")

st.write(
    "This page shows the formulas the app is using or is queued to implement. "
    "Use it as the math room before trusting any recommendation."
)

formula_rows = [
    {
        "area": "Pick Value",
        "status": "implemented",
        "equation": (
            "FinalPickValue = BaseCurve * FutureDiscount * CertaintyAdjustment "
            "+ DeclarationAdjustment"
        ),
        "inputs": "pick_year, round, slot, certainty, declaration adjustment",
        "output": "final_pick_value",
        "code": "src/models/pick_values.py",
        "notes": "Exact 50-pick 1,000-point curve is now implemented.",
    },
    {
        "area": "Overall Pick",
        "status": "implemented",
        "equation": "overall_pick = 10 * (round - 1) + slot",
        "inputs": "round, slot",
        "output": "overall_pick",
        "code": "src/models/pick_values.py",
        "notes": "Uses the 10-team league structure from the brief.",
    },
    {
        "area": "Future Discount",
        "status": "implemented",
        "equation": "FutureDiscount = annual_future_discount ^ years_out",
        "inputs": "pick_year, current_pick_year, annual_future_discount",
        "output": "future_discount",
        "code": "src/models/pick_values.py",
        "notes": "Default annual discount is 0.80; config allows 0.80-0.82.",
    },
    {
        "area": "Private Player Score",
        "status": "queued for spec alignment",
        "equation": "QB/RB/WR/TE weighted position formulas from the brief",
        "inputs": "normalized 0-100 position feature inputs",
        "output": "private_score",
        "code": "src/models/player_scores.py",
        "notes": "Current code still has prototype weights; queued task should replace them.",
    },
    {
        "area": "Keeper Score",
        "status": "queued for spec alignment",
        "equation": (
            "0.30*LongTermPrivateValue + 0.20*Next2YearStarterValue "
            "+ 0.15*ScarcityBonus + 0.10*TradeLiquidity + 0.10*AgeCurve "
            "+ 0.10*RiskAdj + 0.05*BuildFit"
        ),
        "inputs": (
            "long-term value, next-2-year value, scarcity, liquidity, "
            "age curve, risk, build fit"
        ),
        "output": "keeper_score",
        "code": "src/models/keeper_scores.py",
        "notes": "Current code still has prototype keeper math; queued task should replace it.",
    },
    {
        "area": "Drop Candidate Score",
        "status": "queued for spec alignment",
        "equation": (
            "0.45*InverseKeeperScore + 0.25*(OfficialValue - PrivateValue) "
            "+ 0.15*RosterRedundancy + 0.15*DeclineRisk"
        ),
        "inputs": "keeper score, official value, private value, redundancy, decline risk",
        "output": "drop_candidate_score",
        "code": "src/models/keeper_scores.py",
        "notes": "Current code still has prototype drop math; queued task should replace it.",
    },
    {
        "area": "Confidence",
        "status": "queued for spec alignment",
        "equation": (
            "0.35*data_completeness + 0.25*historical_cohort_size "
            "+ 0.20*market_agreement + 0.20*model_separation"
        ),
        "inputs": "data completeness, cohort size, market agreement, model separation",
        "output": "confidence_score",
        "code": "src/models/confidence.py",
        "notes": "Current code still has prototype confidence math; queued task should replace it.",
    },
    {
        "area": "Trade Value",
        "status": "queued for spec alignment",
        "equation": (
            "PrivateTradeScore, MarketTradeScore, KeeperImpactScore, "
            "NinersEdgeScore, OpponentBenefitScore, AcceptanceChance"
        ),
        "inputs": (
            "assets in/out, market value, keeper pressure, lineup delta, "
            "owner/complexity/risk factors"
        ),
        "output": "trade labels and score components",
        "code": "src/models/trade_scores.py",
        "notes": "Current code only has a small placeholder trade-value helper.",
    },
    {
        "area": "Official Top 5 Rule",
        "status": "implemented",
        "equation": "sort roster by official_rank ascending, take first 5, protect at most 4",
        "inputs": "roster rows, official_rank, official_top_five_keep_limit",
        "output": "forced_release_candidates",
        "code": "src/models/keeper_scores.py",
        "notes": "This rule correctly uses official rank, not private rank.",
    },
]

st.subheader("Formula Registry")
formula_frame = pd.DataFrame(formula_rows)
status_filter = st.multiselect(
    "Status",
    sorted(formula_frame["status"].unique()),
    default=sorted(formula_frame["status"].unique()),
)
st.dataframe(
    formula_frame[formula_frame["status"].isin(status_filter)],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Pick Value Curve")
config = PickValueConfig()
curve_rows = []
for index, base_value in enumerate(BRIEF_PICK_VALUE_CURVE_1000, start=1):
    draft_round = ((index - 1) // config.teams_per_round) + 1
    slot = index - ((draft_round - 1) * config.teams_per_round)
    curve_rows.append(
        {
            "pick": f"{draft_round}.{slot:02d}",
            "overall_pick": index,
            "base_value_1000": base_value,
        }
    )

st.dataframe(pd.DataFrame(curve_rows), use_container_width=True, hide_index=True)

st.subheader("Position Private Score Targets")
position_rows = [
    {"position": "QB", "term": "draft_cap", "weight": 0.40},
    {"position": "QB", "term": "rush_profile", "weight": 0.30},
    {"position": "QB", "term": "start_path", "weight": 0.15},
    {"position": "QB", "term": "passing_trait", "weight": 0.10},
    {"position": "QB", "term": "environment", "weight": 0.05},
    {"position": "RB", "term": "draft_cap", "weight": 0.28},
    {"position": "RB", "term": "opportunity", "weight": 0.22},
    {"position": "RB", "term": "production", "weight": 0.15},
    {"position": "RB", "term": "receiving", "weight": 0.14},
    {"position": "RB", "term": "elusiveness", "weight": 0.12},
    {"position": "RB", "term": "size_durability", "weight": 0.05},
    {"position": "RB", "term": "athleticism", "weight": 0.04},
    {"position": "WR", "term": "draft_cap", "weight": 0.27},
    {"position": "WR", "term": "age_adj_production", "weight": 0.21},
    {"position": "WR", "term": "target_earning_efficiency", "weight": 0.17},
    {"position": "WR", "term": "breakout_class", "weight": 0.12},
    {"position": "WR", "term": "film_separation", "weight": 0.11},
    {"position": "WR", "term": "size_role", "weight": 0.05},
    {"position": "WR", "term": "athleticism", "weight": 0.03},
    {"position": "WR", "term": "environment", "weight": 0.04},
    {"position": "TE", "term": "draft_cap", "weight": 0.23},
    {"position": "TE", "term": "receiving_production", "weight": 0.22},
    {"position": "TE", "term": "route_role", "weight": 0.17},
    {"position": "TE", "term": "athleticism", "weight": 0.12},
    {"position": "TE", "term": "film_receiving", "weight": 0.11},
    {"position": "TE", "term": "role_path", "weight": 0.08},
    {"position": "TE", "term": "age_timeline", "weight": 0.04},
    {"position": "TE", "term": "environment", "weight": 0.03},
]
st.dataframe(pd.DataFrame(position_rows), use_container_width=True, hide_index=True)

st.subheader("Queue Warning")
st.info(
    "Pick values are the newest spec-aligned algorithm. Player, keeper, confidence, "
    "and trade formulas are visible here as targets but still need the queued "
    "formula-alignment tasks."
)
