from __future__ import annotations

from dataclasses import dataclass

PURE_MODEL_VALUE = "pure_model_value"
KEEPER_DECISION = "keeper_decision"
TRADE_LIQUIDITY = "trade_liquidity"
FORCED_RELEASE_PAIN = "forced_release_pain"
DRAFT_AVAILABLE = "draft_available"


@dataclass(frozen=True)
class RankingSurface:
    surface_id: str
    label: str
    rank_source: str
    intended_use: str
    sort_description: str
    display_columns: tuple[str, ...]


SURFACES: dict[str, RankingSurface] = {
    PURE_MODEL_VALUE: RankingSurface(
        surface_id=PURE_MODEL_VALUE,
        label="Pure Model Value",
        rank_source="stats_value/private_lve_value descending",
        intended_use=(
            "Compare stats-first private football value only. This excludes keeper "
            "context, trade market context, and forced-release rules."
        ),
        sort_description="Model Value descending, then player.",
        display_columns=(
            "surface_rank",
            "position_rank_label",
            "player",
            "pos",
            "asset_lifecycle_label",
            "team",
            "stats_value",
            "confidence",
            "confidence_label",
            "warning_reason",
        ),
    ),
    KEEPER_DECISION: RankingSurface(
        surface_id=KEEPER_DECISION,
        label="Keeper Decision",
        rank_source="action priority, keeper/drop context, then model value",
        intended_use=(
            "Review roster-context keep, bubble, shop, and release pressure. This "
            "surface is not a pure player-quality ranking."
        ),
        sort_description="Action urgency, then Cut Risk descending, then Model Value.",
        display_columns=(
            "surface_rank",
            "player",
            "pos",
            "asset_lifecycle_label",
            "team",
            "action",
            "keeper_score",
            "drop_score",
            "stats_value",
            "confidence",
            "confidence_label",
            "warning_reason",
        ),
    ),
    TRADE_LIQUIDITY: RankingSurface(
        surface_id=TRADE_LIQUIDITY,
        label="Trade/Liquidity",
        rank_source="absolute model-vs-market edge, trade market, model value",
        intended_use=(
            "Find trade-market disagreement. Trade Market is liquidity/cost; it "
            "does not change private Model Value."
        ),
        sort_description="Largest absolute Model vs Market gap, then Model Value.",
        display_columns=(
            "surface_rank",
            "player",
            "pos",
            "asset_lifecycle_label",
            "team",
            "stats_value",
            "market_value",
            "market_edge",
            "edge_type",
            "confidence",
            "confidence_label",
            "warning_reason",
        ),
    ),
    FORCED_RELEASE_PAIN: RankingSurface(
        surface_id=FORCED_RELEASE_PAIN,
        label="Forced-Release Pain",
        rank_source="Roster's League-Rank Top Five only, lowest keep/highest cut pressure",
        intended_use=(
            "Inspect only each roster's five highest league-ranked players that "
            "can satisfy the forced-release rule. Regular cuts outside that "
            "roster top-five group are not ranked here."
        ),
        sort_description=(
            "Roster top-five candidates only; Cut Risk descending, Model Value ascending."
        ),
        display_columns=(
            "surface_rank",
            "player",
            "pos",
            "asset_lifecycle_label",
            "team",
            "league_rank",
            "action",
            "keeper_score",
            "drop_score",
            "stats_value",
            "confidence",
            "confidence_label",
            "warning_reason",
        ),
    ),
    DRAFT_AVAILABLE: RankingSurface(
        surface_id=DRAFT_AVAILABLE,
        label="Draft Board / Available Players Only",
        rank_source="draftable pool only, draft/model value descending",
        intended_use=(
            "Rank only players who are actually available to draft: rookies, "
            "declared released veterans, free agents, or manual draftable adds."
        ),
        sort_description="Available players only; draft/model value descending.",
        display_columns=(
            "overall_rank",
            "player",
            "position",
            "nfl_team",
            "asset_type",
            "asset_lifecycle_label",
            "stats_model_value",
            "market_value",
            "market_edge",
            "confidence",
            "confidence_label",
            "warning",
            "why_available",
        ),
    ),
}

SURFACE_ORDER: tuple[str, ...] = (
    PURE_MODEL_VALUE,
    KEEPER_DECISION,
    TRADE_LIQUIDITY,
    FORCED_RELEASE_PAIN,
    DRAFT_AVAILABLE,
)


def surface_for_id(surface_id: str) -> RankingSurface:
    return SURFACES[surface_id]


def surface_rows() -> list[dict[str, object]]:
    return [
        {
            "surface": surface.label,
            "surface_id": surface.surface_id,
            "rank_source": surface.rank_source,
            "intended_use": surface.intended_use,
            "sort": surface.sort_description,
            "review_status": "review_only",
        }
        for surface_id in SURFACE_ORDER
        for surface in [SURFACES[surface_id]]
    ]


def apply_ranking_surface(
    rows: list[dict[str, object]],
    surface_id: str,
) -> list[dict[str, object]]:
    surface = surface_for_id(surface_id)
    prepared = [_with_surface_metadata(dict(row), surface) for row in rows]
    if surface_id == PURE_MODEL_VALUE:
        sorted_rows = sorted(
            prepared,
            key=lambda row: (-_score(row.get("stats_value")), str(row.get("player") or "")),
        )
    elif surface_id == KEEPER_DECISION:
        sorted_rows = sorted(
            prepared,
            key=lambda row: (
                _action_order(row.get("action")),
                -_score(row.get("drop_score")),
                -_score(row.get("keeper_score")),
                -_score(row.get("stats_value")),
                str(row.get("player") or ""),
            ),
        )
    elif surface_id == TRADE_LIQUIDITY:
        sorted_rows = sorted(
            prepared,
            key=lambda row: (
                -abs(_score(row.get("market_edge"), default=0.0)),
                -_score(row.get("market_value")),
                -_score(row.get("stats_value")),
                str(row.get("player") or ""),
            ),
        )
    elif surface_id == FORCED_RELEASE_PAIN:
        sorted_rows = sorted(
            _top_five_rows_by_team(prepared),
            key=lambda row: (
                -_score(row.get("drop_score")),
                _score(row.get("keeper_score")),
                _league_rank(row.get("league_rank")),
                str(row.get("player") or ""),
            ),
        )
    elif surface_id == DRAFT_AVAILABLE:
        sorted_rows = sorted(
            [row for row in prepared if str(row.get("draft_status") or "available") == "available"],
            key=lambda row: (
                -_score(row.get("draft_value") or row.get("stats_model_value")),
                -_score(row.get("confidence")),
                str(row.get("player") or ""),
            ),
        )
    else:
        sorted_rows = prepared
    return [_ranked(row, rank) for rank, row in enumerate(sorted_rows, start=1)]


def surface_summary_row(surface_id: str) -> dict[str, object]:
    surface = surface_for_id(surface_id)
    return {
        "surface": surface.label,
        "rank_source": surface.rank_source,
        "intended_use": surface.intended_use,
        "sort": surface.sort_description,
        "review_status": "review_only",
    }


def _with_surface_metadata(
    row: dict[str, object],
    surface: RankingSurface,
) -> dict[str, object]:
    row["surface"] = surface.label
    row["surface_id"] = surface.surface_id
    row["rank_source"] = surface.rank_source
    row["intended_use"] = surface.intended_use
    row["surface_sort"] = surface.sort_description
    return row


def _ranked(row: dict[str, object], rank: int) -> dict[str, object]:
    row["surface_rank"] = rank
    return row


def _top_five_rows_by_team(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        team = str(row.get("team") or "")
        if _league_rank(row.get("league_rank")) >= 999999:
            continue
        grouped.setdefault(team, []).append(row)
    top_five: list[dict[str, object]] = []
    for team_rows in grouped.values():
        top_five.extend(
            sorted(
                team_rows,
                key=lambda row: (
                    _league_rank(row.get("league_rank")),
                    str(row.get("player") or ""),
                ),
            )[:5]
        )
    return top_five


def _action_order(value: object) -> int:
    return {
        "shop/release": 0,
        "release": 1,
        "drop": 1,
        "release/drop": 1,
        "shop": 2,
        "bubble": 3,
        "review": 4,
        "risk": 5,
        "hold": 6,
        "keep": 7,
    }.get(str(value or "").lower(), 99)


def _league_rank(value: object) -> int:
    if value is None or value == "":
        return 999999
    return int(value)


def _score(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)
