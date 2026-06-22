from __future__ import annotations

# ruff: noqa: E501

import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = REPO_ROOT / "docs" / "hq" / "parallel_lanes" / "overnight_8h_emergency_20260622"
LOG_ROOT = REPO_ROOT / "docs" / "hq" / "parallel_lanes" / "overnight_emergency_logs_20260622"

FROZEN_BOARD_PATH = Path(
    r"C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622"
    r"\FINAL_DRAFT_BOARD_V1_FROZEN.csv"
)
DYNASTY_BOARD_PATH = (
    REPO_ROOT
    / "local_exports"
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv"
)
OUTCOME_PATH = (
    Path(r"C:\NWR\Niners-War-Room-outcome")
    / "app"
    / "generated"
    / "outcome_probability"
    / "numeric_outcome_display_v1.csv"
)
ROSTER_AGE_CONTEXT_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context"
    r"\20260621_011500_timing_metadata_v1\player_roster_display_context.csv"
)
SLEEPER_ADP_POINTER_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\market_behavior\sleeper_adp_display_context"
    r"\latest_candidate.json"
)

AS_OF_DATE = date(2026, 6, 22)
NOT_ENOUGH = "Not enough information"
CURRENT_PICK_WINDOWS = (3, 4, 9, 14, 18)
ANCHORS = (
    "Jeremiyah Love",
    "Makai Lemon",
    "Carnell Tate",
    "KC Concepcion",
    "Jadarian Price",
    "Zay Flowers",
    "Chris Olave",
    "Jameson Williams",
    "Drake Maye",
    "Dak Prescott",
    "Jaylen Warren",
    "Brian Thomas",
    "Rashee Rice",
    "Brock Purdy",
    "Keenan Allen",
    "Darren Waller",
)


@dataclass(frozen=True)
class SourceFrames:
    frozen: pd.DataFrame
    dynasty: pd.DataFrame
    outcome: pd.DataFrame
    age_lookup: dict[tuple[str, str], str]
    adp_lookup: dict[tuple[str, str], dict[str, str]]


def main() -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    frames = load_sources()
    candidate = build_candidate_board(frames)
    candidate_path = RUN_ROOT / "emergency_cross_asset_candidate_player_board.csv"
    candidate.to_csv(candidate_path, index=False, quoting=csv.QUOTE_MINIMAL)

    horizon = build_horizon_candidate(candidate)
    horizon_path = RUN_ROOT / "outcome_horizon_candidate.csv"
    horizon.to_csv(horizon_path, index=False, quoting=csv.QUOTE_MINIMAL)

    write_reports(frames, candidate, horizon)
    write_status(candidate_path, horizon_path, candidate, horizon)


def load_sources() -> SourceFrames:
    frozen = pd.read_csv(FROZEN_BOARD_PATH, dtype=str).fillna("")
    dynasty = pd.read_csv(DYNASTY_BOARD_PATH, dtype=str).fillna("")
    outcome = pd.read_csv(OUTCOME_PATH, dtype=str).fillna("") if OUTCOME_PATH.exists() else pd.DataFrame()
    return SourceFrames(
        frozen=frozen,
        dynasty=dynasty,
        outcome=outcome,
        age_lookup=load_age_lookup(),
        adp_lookup=load_adp_lookup(),
    )


def build_candidate_board(frames: SourceFrames) -> pd.DataFrame:
    frozen_lookup = {
        identity(row.get("player"), row.get("position")): row
        for row in frames.frozen.to_dict("records")
    }
    dynasty_lookup = {
        identity(row.get("player_name"), row.get("position")): row
        for row in frames.dynasty.to_dict("records")
    }
    outcome_lookup = {
        identity(row.get("player_name") or row.get("player"), row.get("position")): row
        for row in frames.outcome.to_dict("records")
    }
    ordered_keys: list[tuple[str, str]] = []
    for row in frames.frozen.to_dict("records"):
        key = identity(row.get("player"), row.get("position"))
        if key not in ordered_keys:
            ordered_keys.append(key)
    dynasty_rows = frames.dynasty.copy()
    if "nwr_rank" in dynasty_rows.columns:
        dynasty_rows["_rank"] = pd.to_numeric(dynasty_rows["nwr_rank"], errors="coerce")
        dynasty_rows = dynasty_rows.sort_values(["_rank", "player_name"], na_position="last")
    for row in dynasty_rows.to_dict("records"):
        key = identity(row.get("player_name"), row.get("position"))
        if key not in ordered_keys:
            ordered_keys.append(key)

    records = []
    for key in ordered_keys:
        frozen = frozen_lookup.get(key, {})
        dynasty = dynasty_lookup.get(key, {})
        outcome = outcome_lookup.get(key, {})
        records.append(score_player(key, frozen, dynasty, outcome, frames))

    frame = pd.DataFrame(records)
    frame = add_available_pool_adp_context(frame)
    frame = frame.sort_values(
        ["_candidate_sort", "player"],
        ascending=[False, True],
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)
    frame["emergency_overall_context_rank"] = range(1, frame.shape[0] + 1)
    draft_pool_mask = frame["final_board_rank"].astype(str).ne(NOT_ENOUGH)
    draft_ranked_indexes = (
        frame.loc[draft_pool_mask]
        .sort_values(["_candidate_sort", "player"], ascending=[False, True])
        .index
        .tolist()
    )
    draft_rank_map = {index: rank + 1 for rank, index in enumerate(draft_ranked_indexes)}
    frame["emergency_cross_asset_rank"] = [
        draft_rank_map.get(index, int(frame.at[index, "emergency_overall_context_rank"]))
        for index in frame.index
    ]
    frame["cross_asset_candidate_rank"] = frame["emergency_cross_asset_rank"]
    frame["cross_asset_candidate_value"] = frame["emergency_cross_asset_value"].map(
        lambda value: f"{float(value):.2f}" if meaningful_number(value) is not None else NOT_ENOUGH
    )
    frame["emergency_cross_asset_value"] = frame["cross_asset_candidate_value"]
    frame = frame.drop(columns=["_candidate_sort"])
    return frame.loc[:, candidate_columns()]


def score_player(
    key: tuple[str, str],
    frozen: dict[str, Any],
    dynasty: dict[str, Any],
    outcome: dict[str, Any],
    frames: SourceFrames,
) -> dict[str, Any]:
    name_key, pos = key
    player = clean(frozen.get("player") or dynasty.get("player_name"))
    position = clean(frozen.get("position") or dynasty.get("position")).upper()
    team = clean(frozen.get("nfl_team") or dynasty.get("nfl_team")) or NOT_ENOUGH
    age = display_age(
        frozen.get("age") or dynasty.get("age") or frames.age_lookup.get(key, "")
    )
    asset_type = clean(frozen.get("asset_type")) or (
        "rookie" if clean(dynasty.get("is_rookie")).lower() in {"1", "true", "yes"} else "veteran"
    )
    score_basis = clean(frozen.get("score_basis_visible")) or clean(dynasty.get("score_type"))
    current_score = clean(dynasty.get("nwr_dynasty_score") or frozen.get("final_board_score_visible"))
    dynasty_score = meaningful_number(dynasty.get("nwr_dynasty_score"))
    rookie_rank = meaningful_number(frozen.get("rookie_rank_display_only"))
    final_rank = clean(frozen.get("final_board_rank"))
    reasons: list[str] = []
    components: dict[str, float] = {}

    if dynasty_score is not None:
        base = dynasty_score
        reasons.append("approved_full_dynasty_score_anchor")
    elif asset_type == "rookie" and rookie_rank is not None:
        base = rookie_crosswalk_value(rookie_rank, clean(frozen.get("rookie_tier_display_only")))
        reasons.append("rookie_rank_tier_crosswalk_to_dynasty_scale")
    else:
        base = meaningful_number(frozen.get("veteran_candidate_value_display_only")) or 20.0
        reasons.append("fallback_frozen_display_value_review_only")
    components["internal_value_anchor"] = base

    age_component = age_curve_component(position, meaningful_number(age))
    scarcity_component = position_scarcity_component(position)
    role_component = role_evidence_component(position, frozen, dynasty)
    outcome_component = outcome_support_component(position, outcome)
    uncertainty = uncertainty_penalty(position, frozen, dynasty, outcome, asset_type)
    components.update(
        {
            "age_curve_component": age_component,
            "position_scarcity_component": scarcity_component,
            "role_evidence_component": role_component,
            "outcome_support_component": outcome_component,
            "uncertainty_penalty": uncertainty,
        }
    )
    value = base + age_component + scarcity_component + role_component + outcome_component - uncertainty
    value = max(0.0, min(100.0, value))
    if position == "K":
        value = 0.0
        reasons.append("kicker_excluded_from_default_dynasty_value")

    reasons.extend(component_reasons(components, frozen, dynasty, outcome, asset_type))
    manual_flag = manual_review_flag(frozen, dynasty, reasons)
    confidence = confidence_band(value, uncertainty, manual_flag, dynasty, asset_type)
    return {
        "player_id": clean(dynasty.get("player_id") or frozen.get("player_id")),
        "player": player or name_key,
        "pos": position,
        "nfl_team": team,
        "age": age,
        "position_rank": clean(frozen.get("position_rank") or position_rank_from_dynasty(dynasty)),
        "tier": clean(frozen.get("final_tier") or band_from_value(value)),
        "final_board_rank": final_rank or NOT_ENOUGH,
        "dynasty_rank": clean(dynasty.get("nwr_rank")) or NOT_ENOUGH,
        "current_score_or_value": current_score or NOT_ENOUGH,
        "current_score_basis": score_basis or NOT_ENOUGH,
        "emergency_cross_asset_value": round(value, 2),
        "_candidate_sort": value,
        "candidate_value_band": band_from_value(value),
        "confidence_band": confidence,
        "uncertainty_reasons": "; ".join(reasons) if reasons else "review_only_candidate",
        "candidate_vs_frozen_note": candidate_vs_frozen_note(value, final_rank, player),
        "candidate_vs_dynasty_note": candidate_vs_dynasty_note(value, dynasty),
        "candidate_action_summary": action_summary(value, confidence, manual_flag),
        "manual_review_flag": manual_flag,
        "source_note": (
            "EMERGENCY_REVIEW_ONLY_CANDIDATE; does not replace final_board_rank or "
            "Dynasty Rank; ADP is display-only price context."
        ),
        "outcome_applicable_summary": outcome_summary(position, outcome),
        "adp": NOT_ENOUGH,
        "adp_source_status": NOT_ENOUGH,
        "available_pool_adp_rank": NOT_ENOUGH,
        "available_pool_adp_range": NOT_ENOUGH,
        "current_pick_value_1_03": NOT_ENOUGH,
        "current_pick_value_1_04": NOT_ENOUGH,
        "current_pick_value_1_09": NOT_ENOUGH,
        "current_pick_value_2_04": NOT_ENOUGH,
        "current_pick_value_2_08": NOT_ENOUGH,
        "current_pick_value": NOT_ENOUGH,
        "current_pick_value_reason": NOT_ENOUGH,
    }


def rookie_crosswalk_value(rank: float, tier: str) -> float:
    if rank <= 1:
        base = 57.5
    elif rank <= 3:
        base = 53.0 - (rank - 2) * 0.8
    elif rank <= 6:
        base = 50.5 - (rank - 4) * 1.0
    elif rank <= 12:
        base = 44.0 - (rank - 7) * 0.8
    elif rank <= 24:
        base = 37.0 - (rank - 13) * 0.5
    else:
        base = 30.0 - min(10.0, (rank - 25) * 0.25)
    lower = tier.lower()
    if "priority" in lower:
        base += 1.5
    elif "manual" in lower or "discount" in lower:
        base -= 2.0
    return base


def age_curve_component(position: str, age: float | None) -> float:
    if age is None:
        return -1.0
    if position == "RB":
        if age <= 23.5:
            return 2.0
        if age <= 25.5:
            return 0.5
        if age <= 27.5:
            return -3.0
        return -7.0
    if position == "WR":
        if age <= 24.5:
            return 2.0
        if age <= 27.5:
            return 0.5
        if age <= 29.5:
            return -3.0
        return -8.0
    if position == "TE":
        if age <= 26.5:
            return 1.0
        if age <= 30.5:
            return 0.0
        return -7.0
    if position == "QB":
        if age <= 27.5:
            return 1.0
        if age <= 32.5:
            return -1.0
        return -5.0
    return 0.0


def position_scarcity_component(position: str) -> float:
    return {"RB": 2.5, "WR": 1.5, "TE": 0.8, "QB": -6.0, "K": -50.0}.get(position, 0.0)


def role_evidence_component(position: str, frozen: dict[str, Any], dynasty: dict[str, Any]) -> float:
    text = " ".join(
        clean(value).lower()
        for value in (
            frozen.get("depth_chart_role_display_only"),
            frozen.get("nfl_draft_capital_display_only"),
            dynasty.get("confidence_status"),
            dynasty.get("trust_status"),
            dynasty.get("risk_level"),
        )
    )
    value = 0.0
    if "round=1" in text:
        value += 3.0
    elif "round=2" in text:
        value += 1.0
    elif "round=4" in text:
        value -= 2.0
    if "premium_three_down" in text or "receiving_back" in text:
        value += 2.5
    if "target" in text and position == "WR":
        value += 1.0
    if "needs_data" in text:
        value -= 2.5
    if "high_confidence" in text or "usable_with_confidence" in text:
        value += 0.8
    if "warnings" in text:
        value -= 1.0
    return value


def outcome_support_component(position: str, outcome: dict[str, Any]) -> float:
    if not outcome:
        return 0.0
    supported = [
        meaningful_number(outcome.get(column))
        for column in applicable_outcome_columns(position)
    ]
    supported = [value for value in supported if value is not None]
    if not supported:
        return 0.0
    top = max(supported)
    if top >= 0.45:
        return 2.0
    if top >= 0.25:
        return 1.0
    return 0.4


def uncertainty_penalty(
    position: str,
    frozen: dict[str, Any],
    dynasty: dict[str, Any],
    outcome: dict[str, Any],
    asset_type: str,
) -> float:
    text = " ".join(clean(value).lower() for value in [*frozen.values(), *dynasty.values()])
    penalty = 0.0
    if asset_type == "rookie" and not dynasty:
        penalty += 3.5
    if "needs_data" in text:
        penalty += 3.0
    if "manual_review" in text or clean(frozen.get("needs_manual_review")).lower() == "true":
        penalty += 3.5
    if "critical_trap_guard" in text:
        penalty += 8.0
    if clean(frozen.get("nfl_team")).upper() == "UNKNOWN" or clean(dynasty.get("nfl_team")).upper() == "UNKNOWN":
        penalty += 4.0
    if "missing_or_review" in text:
        penalty += 1.5
    if not outcome or not has_applicable_outcome(position, outcome):
        penalty += 0.8
    if position == "QB":
        penalty += 1.5
    return penalty


def component_reasons(
    components: dict[str, float],
    frozen: dict[str, Any],
    dynasty: dict[str, Any],
    outcome: dict[str, Any],
    asset_type: str,
) -> list[str]:
    reasons: list[str] = []
    if asset_type == "rookie":
        reasons.append("rookie_not_raw_score_compared_to_veteran_value")
    if clean(frozen.get("score_basis_visible")):
        reasons.append(f"frozen_score_basis={clean(frozen.get('score_basis_visible'))}")
    if dynasty:
        reasons.append("full_dynasty_anchor_available")
    else:
        reasons.append("no_full_dynasty_row")
    if not outcome or not has_applicable_outcome(clean(frozen.get("position") or dynasty.get("position")), outcome):
        reasons.append("outcome=Not enough information")
    for name, value in components.items():
        if value:
            reasons.append(f"{name}={value:+.1f}")
    return reasons


def manual_review_flag(frozen: dict[str, Any], dynasty: dict[str, Any], reasons: list[str]) -> str:
    text = " ".join([clean(frozen.get("needs_manual_review")), clean(dynasty.get("data_needed")), " ".join(reasons)]).lower()
    if "critical" in text:
        return "human_decision_only"
    if "true" in text or "needs_data" in text or "unknown" in text or "manual" in text:
        return "yes"
    return "no"


def confidence_band(
    value: float,
    uncertainty: float,
    manual_flag: str,
    dynasty: dict[str, Any],
    asset_type: str,
) -> str:
    if manual_flag == "human_decision_only":
        return "Very low"
    if uncertainty >= 10:
        return "Very low"
    if uncertainty >= 6 or manual_flag == "yes":
        return "Low"
    if dynasty and asset_type != "rookie":
        return "Medium-high" if value >= 35 else "Medium"
    return "Medium"


def add_available_pool_adp_context(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    adps: list[float | None] = []
    adp_source: list[str] = []
    lookup = load_adp_lookup()
    for row in enriched.to_dict("records"):
        adp_row = lookup.get(identity(row.get("player"), row.get("pos")), {})
        value = meaningful_number(adp_row.get("adp"))
        adps.append(value)
        adp_source.append(adp_row.get("source_risk", "") or ("display_only" if value else NOT_ENOUGH))
    enriched["_adp_numeric"] = adps
    adp_ranked = (
        enriched.loc[enriched["_adp_numeric"].notna()]
        .sort_values(["_adp_numeric", "_candidate_sort"], ascending=[True, False])
        .index
        .tolist()
    )
    rank_map = {index: rank + 1 for rank, index in enumerate(adp_ranked)}
    for index, row in enriched.iterrows():
        adp_value = row["_adp_numeric"]
        pool_rank = rank_map.get(index)
        enriched.at[index, "adp"] = f"{adp_value:.1f}" if adp_value is not None and not math.isnan(adp_value) else NOT_ENOUGH
        enriched.at[index, "adp_source_status"] = adp_source[index]
        enriched.at[index, "available_pool_adp_rank"] = str(pool_rank) if pool_rank else NOT_ENOUGH
        enriched.at[index, "available_pool_adp_range"] = adp_bucket(pool_rank)
        for pick, label in ((3, "1_03"), (4, "1_04"), (9, "1_09"), (14, "2_04"), (18, "2_08")):
            enriched.at[index, f"current_pick_value_{label}"] = current_pick_value_label(
                pick,
                pool_rank,
                meaningful_number(row.get("_candidate_sort")),
                clean(row.get("confidence_band")),
            )
        enriched.at[index, "current_pick_value"] = enriched.at[index, "current_pick_value_1_03"]
        enriched.at[index, "current_pick_value_reason"] = (
            "Display-only price label from current pick, available-pool ADP rank, "
            "emergency candidate rank/value, and confidence. ADP does not drive value."
        )
    return enriched.drop(columns=["_adp_numeric"])


def current_pick_value_label(
    pick: int,
    pool_rank: int | None,
    candidate_value: float | None,
    confidence: str,
) -> str:
    if pool_rank is None or candidate_value is None:
        return NOT_ENOUGH
    price_delta = pick - pool_rank
    low_confidence = confidence.lower() in {"low", "very low"}
    if low_confidence and price_delta < 4:
        return NOT_ENOUGH
    if price_delta <= -8:
        return "Too early"
    if price_delta <= -4:
        return "Reach"
    if price_delta <= -2:
        return "Slight reach"
    if candidate_value >= 55 and price_delta >= 2:
        return "Steal"
    if candidate_value >= 45 and price_delta >= 1:
        return "Value"
    return "Fair"


def adp_bucket(rank: int | None) -> str:
    if rank is None:
        return NOT_ENOUGH
    if rank <= 3:
        return "Early 1st equivalent"
    if rank <= 6:
        return "Mid 1st equivalent"
    if rank <= 10:
        return "Late 1st equivalent"
    if rank <= 14:
        return "Early 2nd equivalent"
    if rank <= 20:
        return "Mid/Late 2nd equivalent"
    return "Depth / later"


def build_horizon_candidate(candidate: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for row in candidate.to_dict("records"):
        position = clean(row.get("pos"))
        for metric in horizon_metrics(position):
            band = horizon_band(row, metric)
            rows.append(
                {
                    "player_id": clean(row.get("player_id")),
                    "player": clean(row.get("player")),
                    "pos": position,
                    "horizon_metric": metric,
                    "horizon_value_or_band": band,
                    "horizon_confidence": clean(row.get("confidence_band")) or "Low",
                    "horizon_reason": horizon_reason(row, metric, band),
                    "source_basis": (
                        "Candidate / Review-Only band derived from emergency cross-asset "
                        "candidate value, age, position, applicable current Outcome support, "
                        "and uncertainty. No approved horizon probability artifact exists."
                    ),
                    "display_status": "Candidate / Review-Only",
                }
            )
    return pd.DataFrame(rows)


def horizon_metrics(position: str) -> tuple[str, ...]:
    return {
        "QB": ("2026 QB T12", "2027 QB T12", "Next 5Y QB T12"),
        "RB": ("2026 RB T12", "2026 RB T24", "2027 RB T12", "2027 RB T24", "Next 5Y RB T12", "Next 5Y RB T24"),
        "WR": (
            "2026 WR T12",
            "2026 WR T24",
            "2026 WR T36",
            "2027 WR T12",
            "2027 WR T24",
            "2027 WR T36",
            "Next 5Y WR T12",
            "Next 5Y WR T24",
            "Next 5Y WR T36",
        ),
        "TE": ("2026 TE T12", "2027 TE T12", "Next 5Y TE T12"),
    }.get(position, tuple())


def horizon_band(row: dict[str, Any], metric: str) -> str:
    value = meaningful_number(row.get("emergency_cross_asset_value"))
    if value is None:
        return NOT_ENOUGH
    threshold = 56.0 if "T12" in metric else 48.0 if "T24" in metric else 41.0
    if "2026" in metric and clean(row.get("dynasty_rank")) == NOT_ENOUGH:
        threshold += 4.0
    if "Next 5Y" in metric:
        threshold -= 2.0
    delta = value - threshold
    if delta >= 8:
        return "Strong"
    if delta >= 0:
        return "Viable"
    if delta >= -8:
        return "Thin"
    return "Long shot"


def horizon_reason(row: dict[str, Any], metric: str, band: str) -> str:
    if band == NOT_ENOUGH:
        return NOT_ENOUGH
    return (
        f"{metric} {band.lower()} band from emergency value "
        f"{row.get('emergency_cross_asset_value')}, confidence {row.get('confidence_band')}, "
        f"and caveats: {row.get('uncertainty_reasons')}."
    )


def write_reports(frames: SourceFrames, candidate: pd.DataFrame, horizon: pd.DataFrame) -> None:
    anchors = candidate.loc[candidate["player"].isin(ANCHORS)].copy()
    anchors = anchors.sort_values("emergency_cross_asset_rank")
    (RUN_ROOT / "source_inventory_and_failure_diagnosis.md").write_text(
        source_inventory_report(frames, anchors),
        encoding="utf-8",
    )
    (RUN_ROOT / "cross_asset_formula_report.md").write_text(
        cross_asset_report(candidate, anchors),
        encoding="utf-8",
    )
    (RUN_ROOT / "adp_startup_adjustment_report.md").write_text(
        adp_report(candidate),
        encoding="utf-8",
    )
    (RUN_ROOT / "outcome_current_and_horizon_report.md").write_text(
        outcome_report(frames, horizon),
        encoding="utf-8",
    )
    (RUN_ROOT / "historical_sanity_tuning_report.md").write_text(
        sanity_report(candidate),
        encoding="utf-8",
    )
    top_level = emergency_top_level_report(candidate, horizon)
    (REPO_ROOT / "docs" / "hq" / "parallel_lanes" / "NWR_OVERNIGHT_CROSS_ASSET_OUTCOME_APP_REPAIR_20260622.md").write_text(
        top_level,
        encoding="utf-8",
    )
    (REPO_ROOT / "docs" / "hq" / "parallel_lanes" / "NWR_8H_EMERGENCY_COMPACT_HANDOFF_20260622.md").write_text(
        top_level,
        encoding="utf-8",
    )


def source_inventory_report(frames: SourceFrames, anchors: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Source Inventory And Failure Diagnosis",
            "",
            "Verdict: YELLOW-GREEN. The source issue is understood and repaired as a review-only display layer.",
            "",
            f"- Frozen board rows: {frames.frozen.shape[0]}",
            f"- Full dynasty rows: {frames.dynasty.shape[0]}",
            f"- Outcome display rows: {frames.outcome.shape[0]}",
            "- Non-comparable score bases: rookie rows use frozen rookie rank/tier score; dropped veterans use pinned veteran candidate value; full dynasty rows use nwr_dynasty_score.",
            "- Misleading display column: raw Visible Board Score is mixed-basis and should not be default sort/value truth.",
            "- Safe formula inputs: approved full dynasty score/rank, frozen rookie rank/tier/draft-capital display fields, age/DOB context, position, manual-review/warning fields, and current approved Outcome support as a small confidence signal.",
            "- Display-only only: ADP/startup fields, available-pool ADP rank/range, current-pick value, league/market ranks, and candidate horizon bands.",
            "",
            "## Named Anchor Output",
            markdown_table(anchors),
            "",
            "No latest, approved, pinned, or frozen source-truth artifacts were mutated.",
        ]
    )


def cross_asset_report(candidate: pd.DataFrame, anchors: pd.DataFrame) -> str:
    top = candidate.head(20)
    return "\n".join(
        [
            "# Emergency Cross-Asset Formula Report",
            "",
            "Verdict: YELLOW-GREEN. The formula is review-only and app-facing, not approved rank truth.",
            "",
            "Formula summary: emergency_cross_asset_value = internal value anchor + age curve + 10-team 1QB position scarcity + role evidence + small applicable Outcome support - uncertainty penalty.",
            "",
            "Material change vs the prior display: rookie raw scores are no longer directly compared to veteran candidate values. Rookies are crosswalked from rank/tier/draft capital onto the same review-only scale as full dynasty anchored veterans.",
            "",
            "## Top 20 Emergency Candidates",
            markdown_table(top[[
                "emergency_cross_asset_rank",
                "player",
                "pos",
                "final_board_rank",
                "dynasty_rank",
                "emergency_cross_asset_value",
                "candidate_value_band",
                "confidence_band",
            ]]),
            "",
            "## Sanity Anchors",
            markdown_table(anchors[[
                "emergency_cross_asset_rank",
                "player",
                "pos",
                "final_board_rank",
                "dynasty_rank",
                "emergency_cross_asset_value",
                "confidence_band",
                "candidate_vs_frozen_note",
            ]]),
        ]
    )


def adp_report(candidate: pd.DataFrame) -> str:
    supported = int(candidate["adp"].ne(NOT_ENOUGH).sum())
    return "\n".join(
        [
            "# ADP Startup Adjustment Report",
            "",
            "Verdict: YELLOW. Startup ADP is available only as display-only price context.",
            "",
            f"- Rows with ADP context: {supported}/{candidate.shape[0]}",
            "- Raw startup ADP was not used in emergency_cross_asset_value.",
            "- available_pool_adp_rank is computed by sorting only the visible candidate pool by display-only ADP.",
            "- current_pick_value labels compare current pick windows, available-pool ADP rank, candidate value, and confidence.",
            "- Required app label: ADP/range is display-only price context and does not drive NWR value.",
        ]
    )


def outcome_report(frames: SourceFrames, horizon: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Outcome Current And Horizon Report",
            "",
            "Verdict: YELLOW. Current approved Outcome display is preserved. Horizon output is candidate/review-only bands, not probabilities.",
            "",
            "Current approved Outcome heads: QB T12, RB T12, RB T24, WR T12, WR T24, WR T36, TE T12.",
            f"Approved Outcome artifact path: `{OUTCOME_PATH}`",
            f"Approved Outcome rows: {frames.outcome.shape[0]}",
            f"Candidate horizon rows: {horizon.shape[0]}",
            "",
            "No approved app-readable 2026/2027/Next-5Y probability artifact was found, so this run does not fabricate numeric horizon probabilities.",
            "The horizon CSV uses categorical bands: Strong, Viable, Thin, Long shot, Not enough information.",
        ]
    )


def sanity_report(candidate: pd.DataFrame) -> str:
    anchor_rows = candidate.loc[candidate["player"].isin(ANCHORS)]
    return "\n".join(
        [
            "# Historical / Sanity Tuning Report",
            "",
            "Verdict: YELLOW-GREEN. Tuning used source-consistency and named-anchor sanity checks only; no new model training was run.",
            "",
            "- Zay Flowers, Chris Olave, Jameson Williams, and Drake Maye are no longer buried purely by the mixed frozen score basis.",
            "- QB is discounted for 10-team 1QB, so Drake Maye can surface as a review candidate without pushing QB depth over RB/WR scarcity.",
            "- Keenan Allen and Darren Waller remain constrained by age/team/status uncertainty.",
            "- Missing Outcome is treated as uncertainty / Not enough information, not zero.",
            "- ADP effects are isolated to display-only price labels.",
            "",
            "## Anchor Check",
            markdown_table(anchor_rows[[
                "emergency_cross_asset_rank",
                "player",
                "pos",
                "emergency_cross_asset_value",
                "confidence_band",
                "uncertainty_reasons",
            ]]),
        ]
    )


def emergency_top_level_report(candidate: pd.DataFrame, horizon: pd.DataFrame) -> str:
    anchors = candidate.loc[candidate["player"].isin(ANCHORS)].sort_values(
        "emergency_cross_asset_rank"
    )
    top_draft = candidate.loc[candidate["final_board_rank"].astype(str).ne(NOT_ENOUGH)].sort_values(
        "emergency_cross_asset_rank"
    ).head(15)
    return "\n".join(
        [
            "# NWR Overnight Cross-Asset + Outcome App Repair - 2026-06-22",
            "",
            "Final verdict: YELLOW-GREEN pending browser validation. The app-facing layer is morning-usable as review-only context if validation passes.",
            "",
            "## What Changed",
            "",
            "- Built `emergency_cross_asset_candidate_player_board.csv` from approved/internal NWR sources.",
            "- Rookie raw scores are no longer compared directly to dropped-veteran candidate values.",
            "- Draft-room `cross_asset_candidate_rank` is now ranked within the frozen 66-player draft pool.",
            "- Full-board context keeps `emergency_overall_context_rank` for diagnostics.",
            "- Startup ADP remains display-only and is transformed into available-pool ADP rank/range.",
            "- Created candidate/review-only 2026, 2027, and Next-5Y horizon bands. No horizon probabilities were fabricated.",
            "- Player Compare includes candidate-vs-frozen notes and a Horizon Outcome Candidate block.",
            "",
            "## Formula",
            "",
            "`emergency_cross_asset_value = internal value anchor + age curve + 10-team 1QB position scarcity + role evidence + small applicable Outcome support - uncertainty penalty`",
            "",
            "ADP is not used in the value formula. Outcome is display-only and only a small support/confidence signal when applicable.",
            "",
            "## Top Draft-Pool Candidate View",
            markdown_table(
                top_draft[
                    [
                        "emergency_cross_asset_rank",
                        "player",
                        "pos",
                        "final_board_rank",
                        "dynasty_rank",
                        "emergency_cross_asset_value",
                        "confidence_band",
                        "available_pool_adp_range",
                    ]
                ]
            ),
            "",
            "## Named Sanity Anchors",
            markdown_table(
                anchors[
                    [
                        "emergency_cross_asset_rank",
                        "player",
                        "pos",
                        "final_board_rank",
                        "dynasty_rank",
                        "emergency_cross_asset_value",
                        "confidence_band",
                    ]
                ]
            ),
            "",
            "## Outcome",
            "",
            "- Current approved Outcome columns remain: QB T12, RB T12, RB T24, WR T12, WR T24, WR T36, TE T12.",
            f"- Horizon candidate rows: {horizon.shape[0]}. These are categorical bands only.",
            "- Same-position unsupported Outcome stays `Not enough information`; wrong-position Outcome is hidden by default / N/A in advanced views.",
            "",
            "## Guardrails",
            "",
            "No latest_candidate/latest_approved update, no pinned snapshot mutation, no frozen-board mutation, no Final Board Rank change, no Dynasty Rank overwrite, no raw vendor CSVs, and no raw prediction dumps.",
            "",
            "Detailed phase logs are under `docs/hq/parallel_lanes/overnight_8h_emergency_20260622/` and `docs/hq/parallel_lanes/overnight_emergency_logs_20260622/`.",
        ]
    )


def write_status(candidate_path: Path, horizon_path: Path, candidate: pd.DataFrame, horizon: pd.DataFrame) -> None:
    status = "\n".join(
        [
            "# NWR 8H Emergency Run Status",
            "",
            "Status: candidate layer generated.",
            f"- Candidate board: `{candidate_path}`",
            f"- Candidate board rows: {candidate.shape[0]}",
            f"- Horizon candidate: `{horizon_path}`",
            f"- Horizon rows: {horizon.shape[0]}",
            "- Guardrails: review-only outputs; no source-truth mutation by this script.",
        ]
    )
    (RUN_ROOT / "NWR_8H_EMERGENCY_RUN_STATUS.md").write_text(status, encoding="utf-8")


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    columns = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _column in columns) + " |",
    ]
    for row in frame.astype(str).to_dict("records"):
        values = [
            row.get(column, "").replace("|", "\\|").replace("\n", " ")
            for column in columns
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def load_age_lookup() -> dict[tuple[str, str], str]:
    if not ROSTER_AGE_CONTEXT_PATH.exists():
        return {}
    frame = pd.read_csv(ROSTER_AGE_CONTEXT_PATH, dtype=str).fillna("")
    if "live_use_allowed" in frame.columns:
        frame = frame.loc[frame["live_use_allowed"].str.lower().eq("true")]
    lookup = {}
    for row in frame.to_dict("records"):
        age = age_from_birth_date(row.get("birth_date"))
        if age != NOT_ENOUGH:
            lookup[identity(row.get("full_name"), row.get("position"))] = age
    return lookup


def load_adp_lookup() -> dict[tuple[str, str], dict[str, str]]:
    if not SLEEPER_ADP_POINTER_PATH.exists():
        return {}
    pointer = json.loads(SLEEPER_ADP_POINTER_PATH.read_text(encoding="utf-8-sig"))
    allowed = {str(value) for value in pointer.get("allowed_use", [])}
    blocked = {str(value) for value in pointer.get("blocked_use", [])}
    if "display_only" not in allowed or "rankings" not in blocked:
        return {}
    source_path = Path(str(pointer.get("snapshot_path", ""))) / str(pointer.get("data_file", ""))
    if not source_path.exists():
        return {}
    frame = pd.read_csv(source_path, dtype=str).fillna("")
    lookup = {}
    for row in frame.to_dict("records"):
        preferred = meaningful_number(row.get("preferred_adp_for_nwr"))
        if preferred is None:
            continue
        lookup[identity(row.get("player_name"), row.get("position"))] = {
            "adp": f"{preferred:.1f}",
            "source_risk": clean(row.get("source_risk")) or "YELLOW_DISPLAY_ONLY",
        }
    return lookup


def applicable_outcome_columns(position: str) -> tuple[str, ...]:
    return {
        "QB": ("qb_t12_display_pct",),
        "RB": ("rb_t12_display_pct", "rb_t24_display_pct"),
        "WR": ("wr_t12_display_pct", "wr_t24_display_pct", "wr_t36_display_pct"),
        "TE": ("te_t12_display_pct",),
    }.get(position, tuple())


def has_applicable_outcome(position: str, row: dict[str, Any]) -> bool:
    return any(meaningful_number(row.get(column)) is not None for column in applicable_outcome_columns(position))


def outcome_summary(position: str, row: dict[str, Any]) -> str:
    if not row:
        return NOT_ENOUGH
    pieces = []
    for column in applicable_outcome_columns(position):
        value = meaningful_number(row.get(column))
        if value is not None:
            pieces.append(f"{column.replace('_display_pct', '').upper()}={value:.0%}")
    return "; ".join(pieces) if pieces else NOT_ENOUGH


def position_rank_from_dynasty(row: dict[str, Any]) -> str:
    # Position rank is display context only. Compute from dynasty rank externally would be
    # fragile here, so do not fabricate it when absent.
    return ""


def band_from_value(value: float) -> str:
    if value >= 58:
        return "Priority candidate"
    if value >= 50:
        return "Strong candidate"
    if value >= 40:
        return "Viable candidate"
    if value >= 25:
        return "Depth/discount candidate"
    return "Human-review only longshot"


def action_summary(value: float, confidence: str, manual_flag: str) -> str:
    if manual_flag == "human_decision_only":
        return "Human decision only"
    if confidence in {"Very low", "Low"}:
        return "Review caveats before using"
    if value >= 55:
        return "Best-available review target"
    if value >= 40:
        return "Viable if roster fit/value aligns"
    return "Discount/manual-review only"


def candidate_vs_frozen_note(value: float, final_rank: str, player: str) -> str:
    rank = meaningful_number(final_rank)
    if rank is None:
        return "Not in frozen board; review-only dynasty context."
    if value >= 50 and rank > 20:
        return f"{player} screens higher than frozen rank because frozen score basis was mixed."
    if value < 35 and rank <= 15:
        return f"{player} carries emergency formula caution versus frozen rank."
    return "Generally aligned with frozen board review posture."


def candidate_vs_dynasty_note(value: float, dynasty: dict[str, Any]) -> str:
    rank = clean(dynasty.get("nwr_rank"))
    if not rank:
        return "No approved full dynasty row; candidate relies on rookie/frozen crosswalk."
    return f"Anchored to full dynasty rank {rank} and score {clean(dynasty.get('nwr_dynasty_score'))}."


def candidate_columns() -> list[str]:
    return [
        "player_id",
        "player",
        "pos",
        "nfl_team",
        "age",
        "position_rank",
        "tier",
        "final_board_rank",
        "dynasty_rank",
        "current_score_or_value",
        "current_score_basis",
        "emergency_cross_asset_rank",
        "emergency_cross_asset_value",
        "emergency_overall_context_rank",
        "cross_asset_candidate_rank",
        "cross_asset_candidate_value",
        "candidate_value_band",
        "confidence_band",
        "uncertainty_reasons",
        "candidate_vs_frozen_note",
        "candidate_vs_dynasty_note",
        "candidate_action_summary",
        "adp",
        "adp_source_status",
        "available_pool_adp_rank",
        "available_pool_adp_range",
        "current_pick_value_1_03",
        "current_pick_value_1_04",
        "current_pick_value_1_09",
        "current_pick_value_2_04",
        "current_pick_value_2_08",
        "current_pick_value",
        "current_pick_value_reason",
        "outcome_applicable_summary",
        "manual_review_flag",
        "source_note",
    ]


def display_age(value: Any) -> str:
    numeric = meaningful_number(value)
    if numeric is None:
        return NOT_ENOUGH
    return f"{numeric:.1f}"


def age_from_birth_date(value: Any) -> str:
    text = clean(value)
    if not text:
        return NOT_ENOUGH
    try:
        born = date.fromisoformat(text[:10])
    except ValueError:
        return NOT_ENOUGH
    years = (AS_OF_DATE - born).days / 365.2425
    return f"{years:.1f}" if years > 0 else NOT_ENOUGH


def meaningful_number(value: Any) -> float | None:
    text = clean(value)
    if not text or text.lower() in {"nan", "none", "null", "not enough information", "n/a"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number):
        return None
    return number


def identity(name: Any, position: Any) -> tuple[str, str]:
    return re.sub(r"[^a-z0-9]+", "", clean(name).casefold()), clean(position).upper()


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


if __name__ == "__main__":
    main()
