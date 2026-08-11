"""Owner-facing Rookie Review presentation without changing governed model outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.owner_caveat_presentation_service import owner_caveat_summary

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOKIE_BOARD_PATH = REPO_ROOT / (
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/"
    "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv"
)


def load_owner_rookie_board(path: str | Path = ROOKIE_BOARD_PATH) -> pd.DataFrame:
    source = pd.read_csv(path, dtype=str, keep_default_na=False)
    if len(source) != 80:
        raise ValueError(f"Rookie Review must contain 80 drafted prospects; found {len(source)}")
    output = source.copy()
    output["Rank"] = output["overall_review_rank"].replace("", "—")
    output["Player"] = output["player_name"]
    output["Pos"] = output["position"]
    output["NFL Team"] = output["nfl_team"].replace("", "—")
    output["Rookie draft range"] = output.apply(_draft_range, axis=1)
    output["Rookie Tier"] = output["overall_review_rank"].map(_rookie_tier)
    output["NFL Draft Capital"] = output.apply(_draft_capital, axis=1)
    output["Board Score"] = output["sprint14e_format_score"].replace("", "—")
    output["Review Score"] = output["final_review_score"].replace("", "—")
    output["Why this rank"] = output.apply(_rank_explanation, axis=1)
    output["Authority"] = output.apply(_authority, axis=1)
    output["Blocked / pending reason"] = output.apply(_blocked_reason, axis=1)
    output["Warnings"] = output["warning_codes"].map(owner_caveat_summary)
    output["Confidence"] = output["evidence_confidence"].map(_confidence)
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
    position = str(row.get("position") or "").strip()
    explanation = (
        f"Rank is ordered by the {position} league-format/evidence-adjusted Board Score "
        f"({board_score}), not the broader Review Score ({review_score})."
    )
    if missing:
        explanation += " Missing evidence also invokes the governed confidence/evidence gate."
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


def _integer(value: object) -> int | None:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return None
