"""Owner-facing Rookie Review presentation without changing governed model outputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.owner_caveat_presentation_service import owner_caveat_summary
from src.services.owner_mode_view_service import owner_range_contract, translate_research_tier
from src.services.unified_research_preview_service import load_unified_research_preview

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOKIE_BOARD_PATH = REPO_ROOT / (
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/"
    "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv"
)


def load_owner_rookie_board(
    path: str | Path = ROOKIE_BOARD_PATH,
    *,
    research_packet_dir: str | Path | None = None,
    eligibility_rows: Sequence[Mapping[str, Any]] | None = None,
) -> pd.DataFrame:
    source = pd.read_csv(path, dtype=str, keep_default_na=False)
    if len(source) != 80:
        raise ValueError(f"Rookie Review must contain 80 drafted prospects; found {len(source)}")
    output = source.copy()
    output["Rank"] = output["overall_review_rank"].replace("", "—")
    output["Rookie Rank"] = output["overall_review_rank"].replace("", "-")
    output["Player"] = output["player_name"]
    output["Pos"] = output["position"]
    output["NFL Team"] = output["nfl_team"].replace("", "—")
    output["Rookie draft range"] = output.apply(_draft_range, axis=1)
    output["Rookie Tier"] = output["overall_review_rank"].map(_rookie_tier)
    output["NFL Draft Capital"] = output.apply(_draft_capital, axis=1)
    output["Board Score"] = output["sprint14e_format_score"].replace("", "—")
    output["Review Score"] = output["final_review_score"].replace("", "—")
    output["NWR Rookie Score"] = output["sprint14e_format_score"].replace("", "-")
    output["Why this rank"] = output.apply(_rank_explanation, axis=1)
    output["Authority"] = output.apply(_authority, axis=1)
    output["Blocked / pending reason"] = output.apply(_blocked_reason, axis=1)
    output["Warnings"] = output["warning_codes"].map(owner_caveat_summary)
    output["Confidence"] = output["evidence_confidence"].map(_confidence)
    output["Age"] = output["age_at_draft"].replace("", "-")
    output["College Production"] = output["production_component"].map(_component_context)
    output["Athletic Context"] = output["athletic_component"].map(_component_context)
    if eligibility_rows is not None:
        eligibility_by_pick = {
            str(row.get("overall_pick") or "").strip(): row for row in eligibility_rows
        }
        overlay_records: list[dict[str, Any]] = []
        for row in output.to_dict("records"):
            pick = str(row.get("overall_pick") or "").strip()
            context = eligibility_by_pick.get(pick)
            if context is None:
                raise ValueError(f"Rookie eligibility overlay is missing official pick {pick}")
            if (
                str(context.get("player_name") or "").strip()
                != str(row.get("player_name") or "").strip()
                or str(context.get("position") or "").strip()
                != str(row.get("position") or "").strip()
            ):
                raise ValueError(f"Rookie eligibility receipt mismatch at official pick {pick}")
            score_eligible = bool(context.get("model_score_eligible"))
            overlay_records.append(
                {
                    "Live Player ID": str(context.get("live_governed_player_id") or ""),
                    "Identity Status": str(context.get("identity_status") or ""),
                    "Draft Eligibility": (
                        "Draft eligible" if context.get("draft_eligible") else "Not draft eligible"
                    ),
                    "Score Status": str(context.get("score_status") or ""),
                    "Model Score Eligible": score_eligible,
                    "Searchable": bool(context.get("searchable")),
                    "Selectable": bool(context.get("selectable")),
                    "Draftable": bool(context.get("draftable")),
                    "Refresh Available": bool(context.get("refresh_available")),
                    "Draft Round": context.get("draft_round"),
                    "Overall Pick": context.get("overall_pick"),
                    "Current Team": str(context.get("team") or ""),
                    "Eligibility Authority": str(context.get("authority_status") or ""),
                    "Eligibility Reason": str(context.get("owner_reason") or ""),
                }
            )
        overlay_frame = pd.DataFrame(overlay_records)
        output = pd.concat([output.reset_index(drop=True), overlay_frame], axis=1)
        output["Player"] = output["player_name"]
        output["NFL Team"] = output["Current Team"].replace("", "—")
        output["NFL Draft Capital"] = output.apply(
            lambda row: (
                f"NFL Round {int(row['Draft Round'])} · Pick {int(row['Overall Pick'])}"
                if pd.notna(row["Draft Round"]) and pd.notna(row["Overall Pick"])
                else "—"
            ),
            axis=1,
        )
        output["Authority"] = output["Eligibility Authority"]
        manual = ~output["Model Score Eligible"].astype(bool)
        output.loc[manual, "Rookie Tier"] = "Manual Review"
        output.loc[manual, "Rookie draft range"] = "Unranked — manual review required"
        output.loc[manual, "Blocked / pending reason"] = output.loc[
            manual, "Eligibility Reason"
        ]
        output.loc[manual, "Confidence"] = "Manual review"
        output.loc[manual, "Warnings"] = output.loc[manual].apply(
            lambda row: (
                "Updated identity available; frozen Rookie Review score not rebuilt."
                if row["Refresh Available"]
                else str(row.get("Warnings") or "")
            ),
            axis=1,
        )
    research = load_unified_research_preview(
        Path(research_packet_dir) if research_packet_dir is not None else None
    ).board
    research_by_asset = {
        str(row.get("source_asset_id") or ""): row for row in research.to_dict("records")
    }
    research_rows = []
    for row in output.to_dict("records"):
        player_id = str(row.get("player_id") or "").strip()
        source_asset_id = (
            f"rookie:{player_id}"
            if player_id
            else f"blocked-rookie:{_slug(row.get('player_name'))}"
        )
        context = research_by_asset.get(source_asset_id, {})
        contract = owner_range_contract(
            {
                "asset_type": "Rookie Review",
                "research_downside_signal": context.get("downside_signal"),
                "research_tier": context.get("research_tier"),
                "research_ceiling_signal": context.get("ceiling_signal"),
            }
        )
        research_rows.append(
            {
                "Unified Research": translate_research_tier(context.get("research_tier")),
                "Floor": contract["Floor"],
                "NWR Expected": contract["NWR Expected"],
                "Ceiling": contract["Ceiling"],
                "Research confidence": _probability(context.get("confidence")),
                "Research status": str(context.get("status") or "Not enough information"),
            }
        )
    output = pd.concat([output.reset_index(drop=True), pd.DataFrame(research_rows)], axis=1)
    return output


def rookie_component_rows(row: dict[str, object]) -> pd.DataFrame:
    labels = (
        ("College production", "production_component"),
        ("College market share", "market_share_component"),
        ("NFL draft capital", "draft_capital_component"),
        ("Athletic evidence", "athletic_component"),
        ("Recruiting evidence", "recruiting_component"),
        ("Age / lifecycle", "age_component"),
    )
    rows: list[dict[str, str]] = []
    for label, column in labels:
        value = str(row.get(column) or "").strip()
        rows.append(
            {
                "Evidence": label,
                "Normalized value": value or "—",
                "Model effect": _component_effect(value),
            }
        )
    return pd.DataFrame(rows)


def _draft_range(row: pd.Series) -> str:
    rank = _integer(row.get("overall_review_rank"))
    if rank is None:
        return "Unranked — evidence/identity gate"
    if rank <= 4:
        return "Early 1st range (1.01–1.04)"
    if rank <= 10:
        return "Mid/late 1st range (1.05–1.10)"
    if rank <= 20:
        return "2nd-round range"
    if rank <= 30:
        return "3rd-round range"
    if rank <= 50:
        return "Later-round target"
    return "Watchlist / deep target"


def _rookie_tier(value: object) -> str:
    rank = _integer(value)
    if rank is None:
        return "Unranked — evidence gate"
    if rank <= 4:
        return "Tier 1 · Cornerstone range"
    if rank <= 10:
        return "Tier 2 · First-round target"
    if rank <= 20:
        return "Tier 3 · Second-round target"
    if rank <= 30:
        return "Tier 4 · Third-round target"
    if rank <= 50:
        return "Tier 5 · Later-round swing"
    return "Tier 6 · Watchlist"


def _draft_capital(row: pd.Series) -> str:
    round_number = str(row.get("draft_round") or "").strip()
    overall = str(row.get("overall_pick") or "").strip()
    if not round_number or not overall:
        return "—"
    return f"NFL Round {round_number} · Pick {overall}"


def _rank_explanation(row: pd.Series) -> str:
    if not str(row.get("overall_review_rank") or "").strip():
        return _blocked_reason(row)
    board_score = str(row.get("sprint14e_format_score") or "").strip()
    review_score = str(row.get("final_review_score") or "").strip()
    missing = str(row.get("missing_components") or "").strip()
    confidence_cap = str(row.get("confidence_cap") or "").strip()
    evidence_confidence = _confidence(row.get("evidence_confidence"))
    position = str(row.get("position") or "").strip()
    explanation = (
        f"Rank is ordered by the {position} league-format/evidence-adjusted Board Score "
        f"({board_score}), not the broader Review Score ({review_score})."
    )
    drivers = _component_drivers(row)
    if drivers:
        explanation += f" Admitted component context: {drivers}."
    if confidence_cap:
        explanation += (
            f" Evidence status is {evidence_confidence}; confidence cap is {confidence_cap}."
        )
    if missing:
        explanation += (
            " Missing components ("
            + missing.replace("|", ", ").replace("_", " ")
            + ") also invoke the governed confidence/evidence gate."
        )
    explanation += " NFL draft capital is one component, not an automatic rank override."
    return explanation


def _authority(row: pd.Series) -> str:
    if str(row.get("overall_review_rank") or "").strip():
        return "Rookie Review — decision context only"
    if str(row.get("player_name")) == "De'Zhaun Stribling":
        return "Identity found in newer governed data; Rookie Review rebuild pending"
    return "Unscored — exact Rookie Review identity gate"


def _blocked_reason(row: pd.Series) -> str:
    if str(row.get("overall_review_rank") or "").strip():
        return ""
    if str(row.get("player_name")) == "De'Zhaun Stribling":
        return (
            "A newer governed source now has exact GSIS ID 00-0041035, but the frozen "
            "Rookie Review authority has not been lawfully rebuilt with that identity. "
            "NWR shows him but does not invent a score or rank."
        )
    raw = str(row.get("blocking_reason") or "").strip()
    if raw:
        return owner_caveat_summary(raw)
    return "NWR cannot prove one exact identity across the Rookie Review's required sources."


def _confidence(value: object) -> str:
    text = str(value or "").strip()
    return {
        "usable_with_confidence_cap": "Usable, with evidence cap",
        "blocked": "Blocked",
    }.get(text, text.replace("_", " ").title() or "—")


def _component_effect(value: str) -> str:
    try:
        number = float(value)
    except ValueError:
        return "Unavailable"
    if number >= 60:
        return "HELPED"
    if number < 40:
        return "HURT"
    return "NEUTRAL"


def _component_context(value: object) -> str:
    try:
        return f"{float(str(value)):.1f} / 100 normalized"
    except ValueError:
        return "Not enough information"


def _component_drivers(row: pd.Series) -> str:
    labels = (
        ("production", "production_component"),
        ("market share", "market_share_component"),
        ("NFL draft capital", "draft_capital_component"),
        ("athletic evidence", "athletic_component"),
        ("recruiting evidence", "recruiting_component"),
        ("age/lifecycle", "age_component"),
    )
    values: list[tuple[float, str]] = []
    for label, field in labels:
        try:
            values.append((float(str(row.get(field) or "")), label))
        except ValueError:
            continue
    if not values:
        return ""
    values.sort(reverse=True)
    strongest = ", ".join(f"{label} {value:.1f}" for value, label in values[:2])
    weakest_value, weakest_label = values[-1]
    return f"strongest {strongest}; lowest available {weakest_label} {weakest_value:.1f}"


def _probability(value: object) -> str:
    try:
        return f"{float(str(value)) * 100:.1f}%"
    except ValueError:
        return "Not enough information"


def _slug(value: object) -> str:
    return "-".join(str(value or "").lower().replace("'", "").split())


def _integer(value: object) -> int | None:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return None
