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
    output["Draft Range Band"] = output.apply(_draft_range, axis=1)
    output["Evidence Band"] = output["tier"].map(_evidence_band)
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
    output["Athletic Context"] = output["athletic_component"].map(_athletic_context)
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
                    "Current Role Position": str(
                        context.get("current_role_position") or ""
                    ),
                    "Current Role Status": str(context.get("current_role_status") or ""),
                    "Current Role Projection Status": str(
                        context.get("current_role_projection_status") or ""
                    ),
                    "Current Role Block Reason": str(
                        context.get("current_role_block_reason") or ""
                    ),
                    "Eligibility Authority": str(context.get("authority_status") or ""),
                    "Eligibility Reason": str(context.get("owner_reason") or ""),
                    "Refresh Evidence Status": str(
                        context.get("refresh_evidence_status") or ""
                    ),
                    "Refresh Age": str(context.get("age_at_draft") or ""),
                    "Refresh Production": str(
                        context.get("source_production_component") or ""
                    ),
                    "Refresh Market Share": str(
                        context.get("source_market_share_component") or ""
                    ),
                    "Refresh Draft Capital": str(
                        context.get("source_draft_capital_component") or ""
                    ),
                    "Refresh Athletic": str(
                        context.get("source_athletic_component") or ""
                    ),
                    "Refresh Recruiting": str(
                        context.get("source_recruiting_component") or ""
                    ),
                    "Refresh Age Component": str(
                        context.get("source_age_component") or ""
                    ),
                    "Refresh Missing Components": str(
                        context.get("source_missing_components") or ""
                    ),
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
        output.loc[manual, "Evidence Band"] = "Manual review"
        output.loc[manual, "Draft Range Band"] = "Unranked — manual review required"
        output.loc[manual, "Blocked / pending reason"] = output.loc[
            manual, "Eligibility Reason"
        ]
        output.loc[manual, "Confidence"] = "Manual review"
        refresh_columns = {
            "age_at_draft": "Refresh Age",
            "production_component": "Refresh Production",
            "market_share_component": "Refresh Market Share",
            "draft_capital_component": "Refresh Draft Capital",
            "athletic_component": "Refresh Athletic",
            "recruiting_component": "Refresh Recruiting",
            "age_component": "Refresh Age Component",
            "missing_components": "Refresh Missing Components",
        }
        for target, source_column in refresh_columns.items():
            output.loc[manual, target] = output.loc[manual, source_column]
        output["Age"] = output["age_at_draft"].replace("", "-")
        output["College Production"] = output["production_component"].map(
            _component_context
        )
        output["Athletic Context"] = output["athletic_component"].map(
            _athletic_context
        )
        output.loc[manual, "Warnings"] = output.loc[manual].apply(
            lambda row: (
                "Governed factual/component evidence recovered; candidate score and rank "
                "remain excluded pending owner approval."
                if row["Refresh Available"]
                else str(row.get("Warnings") or "")
            ),
            axis=1,
        )
    preview = load_unified_research_preview(
        Path(research_packet_dir) if research_packet_dir is not None else None
    )
    research = preview.board
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
    neighborhoods = {
        str(row.get("rookie_governed_id") or ""): row
        for row in preview.neighborhoods.to_dict("records")
    }
    output["Market Share"] = output["market_share_component"].map(_component_context)
    output["Current Role"] = output.apply(_current_role_context, axis=1)
    output["Research Neighborhood"] = output.apply(
        lambda row: _research_neighborhood(row, neighborhoods), axis=1
    )
    output["What NWR likes"] = output.apply(_what_nwr_likes, axis=1)
    output["What holds them back"] = output.apply(_what_holds_back, axis=1)
    output["Biggest uncertainty"] = output.apply(_biggest_uncertainty, axis=1)
    score_counts = output["sprint14e_format_score"].astype(str).value_counts().to_dict()
    output["Why rank differs from raw score"] = output.apply(
        lambda row: _rank_vs_raw_score_explanation(
            row,
            tied_score_count=score_counts.get(str(row.get("sprint14e_format_score") or ""), 0),
        ),
        axis=1,
    )
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


def _evidence_band(value: object) -> str:
    source = str(value or "").strip()
    labels = {
        "first_round_board_context_review": "First-round evidence context",
        "second_round_board_context_review": "Second-round evidence context",
        "depth_board_context_review": "Depth-board evidence context",
        "watchlist_context_review": "Watchlist evidence context",
        "watchlist_or_data_incomplete_context_review": (
            "Watchlist or incomplete evidence context"
        ),
        "blocked_unranked": "Manual review",
    }
    return labels.get(source, "Not enough information")


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


def _current_role_context(row: pd.Series) -> str:
    team = str(row.get("Current Team") or row.get("nfl_team") or "").strip()
    frozen_position = str(row.get("position") or "").strip()
    current_position = str(row.get("Current Role Position") or "").strip()
    status = str(row.get("Current Role Status") or "").strip().upper()
    projection_status = str(row.get("Current Role Projection Status") or "").strip().upper()
    if current_position and frozen_position and current_position != frozen_position:
        return (
            f"Frozen Rookie Review position {frozen_position}; current registry position "
            f"{current_position} with {team or 'team unavailable'}. Redraft projection "
            f"status is {projection_status.lower() or 'under review'} for the role conflict; "
            "dynasty score unchanged."
        )
    if status == "ACT" and team:
        return f"Active on {team}'s current roster (factual context only)"
    if status and team:
        return f"{status} with {team} (factual context only)"
    if team:
        return f"Current team: {team}; role depth not governed"
    return "Not enough information"


def _research_neighborhood(
    row: pd.Series, neighborhoods: Mapping[str, Mapping[str, Any]]
) -> str:
    governed_id = str(row.get("player_id") or "").strip()
    context = neighborhoods.get(governed_id)
    if not context:
        return "Not enough information"
    above = str(context.get("veterans_above") or "").strip()
    below = str(context.get("veterans_below") or "").strip()
    if not above and not below:
        return "Not enough information"
    return (
        f"Research-only neighborhood: above {above or 'unavailable'}; "
        f"below {below or 'unavailable'}"
    )


def _athletic_context(value: object) -> str:
    try:
        number = float(str(value))
    except ValueError:
        return "NOT_ENOUGH_INFORMATION"
    if number >= 70:
        return f"STRONG ({number:.1f}/100 governed component)"
    if number >= 40:
        return f"ADEQUATE ({number:.1f}/100 governed component)"
    return f"CONCERN ({number:.1f}/100 governed component)"


def _what_nwr_likes(row: pd.Series) -> str:
    if not str(row.get("overall_review_rank") or "").strip():
        capital = _draft_capital(row)
        identity = str(row.get("Identity Status") or "").strip()
        values = _available_components(row)
        values.sort(reverse=True)
        evidence = [f"{label} {value:.1f}/100" for value, label in values[:3]]
        parts = [
            value
            for value in (capital, identity.replace("_", " ").title(), *evidence)
            if value and value != "â€”"
        ]
        return "; ".join(parts) or "Official drafted asset with a governed selection identity"
    values = _available_components(row)
    if not values:
        return "Admitted Rookie Review rank and score"
    values.sort(reverse=True)
    return "; ".join(f"{label} {value:.1f}/100" for value, label in values[:2])


def _what_holds_back(row: pd.Series) -> str:
    if not str(row.get("overall_review_rank") or "").strip():
        return str(
            row.get("Blocked / pending reason")
            or "Required Rookie Review evidence is unavailable"
        )
    values = _available_components(row)
    missing = str(row.get("missing_components") or "").strip()
    parts: list[str] = []
    if values:
        value, label = min(values)
        parts.append(f"Lowest available component: {label} {value:.1f}/100")
    if missing:
        parts.append("Missing governed components: " + missing.replace("|", ", ").replace("_", " "))
    return "; ".join(parts) or "No separately admitted negative component"


def _biggest_uncertainty(row: pd.Series) -> str:
    if not str(row.get("overall_review_rank") or "").strip():
        missing = str(row.get("missing_components") or "").strip()
        suffix = (
            "; remaining missing components: " + missing.replace("|", ", ").replace("_", " ")
            if missing
            else ""
        )
        return "Owner approval of the proposed identity contract and governed rebuild" + suffix
    warnings = str(row.get("warning_codes") or "").strip()
    if "missing_combine_evidence" in warnings:
        return "Athletic evidence is absent and not treated as neutral"
    if "model_edge_weirdness" in warnings:
        return "Model-edge behavior is flagged for owner review"
    if "draft_capital_anchor_warning" in warnings:
        return "Draft-capital anchoring materially limits the evidence-adjusted score"
    if str(row.get("missing_components") or "").strip():
        return "Missing athletic/recruiting evidence limits confidence"
    return "Normal rookie outcome uncertainty"


def _rank_vs_raw_score_explanation(row: pd.Series, *, tied_score_count: int = 0) -> str:
    if not str(row.get("overall_review_rank") or "").strip():
        return "No rank: the frozen Rookie Review did not admit a score"
    board = str(row.get("sprint14e_format_score") or "").strip()
    review = str(row.get("final_review_score") or "").strip()
    confidence = str(row.get("confidence_cap") or "").strip()
    explanation = (
        f"Rank uses the evidence-adjusted NWR Rookie Score {board}, not the broader "
        f"Review Score {review}; confidence cap {confidence or 'not available'} and governed "
        "format/gate rules are already reflected in the rank score."
    )
    if tied_score_count > 1:
        explanation += (
            " Equal Board Scores use the frozen builder's deterministic secondary key: "
            "player name descending."
        )
    return explanation


def _available_components(row: pd.Series) -> list[tuple[float, str]]:
    fields = (
        ("College production", "production_component"),
        ("Market share", "market_share_component"),
        ("NFL draft capital", "draft_capital_component"),
        ("Athletic evidence", "athletic_component"),
        ("Recruiting", "recruiting_component"),
        ("Age", "age_component"),
    )
    values: list[tuple[float, str]] = []
    for label, field in fields:
        try:
            values.append((float(str(row.get(field) or "")), label))
        except ValueError:
            continue
    return values


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
