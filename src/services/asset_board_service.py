from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.trade_scores import TradeAsset, TradeScoreInputs, score_trade
from src.services.asset_heuristics_service import (
    load_asset_heuristics,
    pick_equivalent_label,
    pick_optionality_bonus,
    pick_year_discount,
    stud_tax,
)
from src.services.market_influence_policy_service import cap_market_blended_value
from src.services.replacement_baseline_service import (
    load_replacement_baselines,
    replacement_gap_score,
)
from src.services.review_score_envelope_service import active_pack_private_score_context
from src.services.rookie_model_service import run_rookie_model_from_dir

PUBLIC_MARKET_FORMAT_PENALTY = {
    "QB": 12.0,
    "RB": 0.0,
    "WR": 0.0,
    "TE": 8.0,
}

# Compatibility-only quarantine: active-pack private_score may be exposed only as
# legacy_active_pack_score comparison context; primary_review_score stays blank.
LEGACY_ACTIVE_PACK_SCORE_QUARANTINE_NOTE = (
    "compatibility_only_legacy_active_pack_score_not_primary"
)


@dataclass(frozen=True)
class UnifiedAsset:
    asset_id: str
    asset_type: str
    player_id: str
    player_name: str
    position: str
    team: str
    all_asset_value: float
    acquisition_value: float
    keeper_adjusted_value: float
    trade_liquidity_value: float
    win_now_value: float
    dynasty_hold_value: float
    replacement_value: float
    confidence_score: float
    pick_equivalent: str
    recommendation: str
    source: str
    replacement_context: str = ""
    replacement_position_rank: int | None = None
    replacement_baseline: str = ""
    primary_review_score: float | None = None
    legacy_active_pack_score: float | None = None
    score_lineage_class: str = ""
    score_source_path: str = ""
    score_source_column: str = ""
    score_model_version: str = ""
    score_allowed_use: str = ""
    score_blocked_use: str = ""
    score_manual_decision_required: bool = False
    legacy_formula_warning: bool = False
    stale_or_legacy_formula_warning: bool = False


@dataclass(frozen=True)
class AssetComparison:
    preferred_asset_id: str
    value_gap: float
    recommendation: str


@dataclass(frozen=True)
class PackageMath:
    package_value: float
    raw_asset_value: float
    roster_spot_penalty: float
    consolidation_premium: float
    stud_tax_penalty: float = 0.0


@dataclass(frozen=True)
class AssetConversionInputs:
    private_base_score: float
    year1_score: float
    long_horizon_score: float
    age_curve_score: float
    format_fit_score: float
    role_security_score: float
    replacement_gap_score: float
    public_market_score: float
    liquidity_score: float
    confidence_score: float
    risk_penalty: float = 0.0
    current_cost_value: float = 50.0
    accessibility_bonus: float = 0.0
    roster_spot_cost: float = 0.0
    package_penalty: float = 0.0
    consolidation_bonus: float = 0.0
    liquidity_penalty: float = 0.0


@dataclass(frozen=True)
class AssetConversionResult:
    replacement_value: float
    win_now_value: float
    dynasty_hold_value: float
    trade_liquidity_value: float
    keeper_adjusted_value: float
    all_asset_value: float
    acquisition_value: float


@dataclass(frozen=True)
class UnifiedAssetBoard:
    snapshot_date: str | None
    rows: list[dict[str, object]]
    asset_types: list[str]
    positions: list[str]
    teams: list[str]
    recommendations: list[str]


def build_unified_asset_board(
    data_pack_path: str | Path,
    *,
    rookie_model_dir: str | Path | None = None,
) -> UnifiedAssetBoard:
    validated = validate_data_pack(data_pack_path)
    replacement_baselines = load_replacement_baselines()
    assets = [
        *_veteran_assets(
            validated.rows_by_table,
            replacement_baselines=replacement_baselines,
            data_pack_path=data_pack_path,
        ),
        *_pick_assets(validated.rows_by_table),
    ]
    if rookie_model_dir is not None:
        assets.extend(_rookie_assets(rookie_model_dir))

    rows = [
        _asset_row(asset)
        for asset in sorted(
            assets,
            key=lambda asset: (-asset.acquisition_value, -asset.all_asset_value, asset.asset_id),
        )
    ]
    return UnifiedAssetBoard(
        snapshot_date=validated.snapshot_date,
        rows=rows,
        asset_types=sorted({str(row["asset_type"]) for row in rows}),
        positions=sorted({str(row["position"]) for row in rows if row["position"]}),
        teams=sorted({str(row["team"]) for row in rows if row["team"]}),
        recommendations=sorted({str(row["recommendation"]) for row in rows}),
    )


def compare_rookie_to_veteran(rookie: UnifiedAsset, veteran: UnifiedAsset) -> AssetComparison:
    gap = round(rookie.acquisition_value - veteran.acquisition_value, 2)
    if gap >= 5:
        return AssetComparison(rookie.asset_id, gap, "rookie")
    if gap <= -5:
        return AssetComparison(veteran.asset_id, abs(gap), "veteran")
    preferred = rookie if rookie.trade_liquidity_value >= veteran.trade_liquidity_value else veteran
    return AssetComparison(preferred.asset_id, abs(gap), "tier_tiebreak")


def compare_pick_to_player(pick: UnifiedAsset, player: UnifiedAsset) -> AssetComparison:
    gap = round(pick.acquisition_value - player.acquisition_value, 2)
    if gap >= 5:
        return AssetComparison(pick.asset_id, gap, "pick_optionality")
    if gap <= -5:
        return AssetComparison(player.asset_id, abs(gap), "player")
    return AssetComparison(pick.asset_id, abs(gap), "pick_tiebreak")


def package_math(assets: tuple[UnifiedAsset, ...]) -> PackageMath:
    heuristics = load_asset_heuristics().packages
    raw_value = round(sum(asset.all_asset_value for asset in assets), 2)
    extra_assets = max(0, len(assets) - 1)
    roster_penalty = round(float(extra_assets * heuristics.extra_roster_spot_cost), 2)
    ordered_values = sorted((asset.all_asset_value for asset in assets), reverse=True)
    consolidation = 0.0
    if len(ordered_values) >= 2:
        consolidation = min(
            heuristics.consolidation_max,
            max(0.0, ordered_values[0] - ordered_values[1])
            * heuristics.consolidation_gap_rate,
        )
    tax_penalty = (
        stud_tax(ordered_values[0], extra_asset_count=extra_assets)
        if ordered_values
        else 0.0
    )
    final_value = round(raw_value - roster_penalty - tax_penalty + consolidation, 2)
    return PackageMath(
        package_value=final_value,
        raw_asset_value=raw_value,
        roster_spot_penalty=roster_penalty,
        consolidation_premium=round(consolidation, 2),
        stud_tax_penalty=round(tax_penalty, 2),
    )


def trade_package_score(
    incoming_assets: tuple[UnifiedAsset, ...],
    outgoing_assets: tuple[UnifiedAsset, ...],
):
    return score_trade(
        TradeScoreInputs(
            incoming_assets=tuple(_trade_asset(asset) for asset in incoming_assets),
            outgoing_assets=tuple(_trade_asset(asset) for asset in outgoing_assets),
        )
    )


def _veteran_assets(
    rows_by_table: dict[str, list[dict[str, object]]],
    *,
    replacement_baselines,
    data_pack_path: str | Path = "",
) -> list[UnifiedAsset]:
    outputs = _by_player_id(rows_by_table.get("model_outputs", []))
    rankings = _by_player_id(rows_by_table.get("official_rankings", []))
    position_ranks = _model_position_ranks(rows_by_table.get("rosters", []), outputs)
    assets: list[UnifiedAsset] = []
    for roster_row in rows_by_table.get("rosters", []):
        player_id = str(roster_row.get("player_id") or "")
        output = outputs.get(player_id, {})
        rank_row = rankings.get(player_id, {})
        asset_type = _asset_type_for_roster_status(str(roster_row.get("roster_status") or ""))
        position = str(roster_row.get("position") or "")
        replacement_context = _replacement_context_for_asset_type(asset_type)
        replacement_rank = position_ranks.get(player_id)
        replacement_value = replacement_gap_score(
            position,
            replacement_rank,
            context=replacement_context,
            baselines=replacement_baselines,
        )
        league_rank = _first_present(
            roster_row.get("league_rank"),
            rank_row.get("league_rank"),
            roster_row.get("official_rank"),
            rank_row.get("official_rank"),
        )
        private = _score(output.get("private_score"))
        score_context = active_pack_private_score_context(
            output,
            source_path=str(Path(data_pack_path) / "model_outputs.csv")
            if data_pack_path
            else "model_outputs.csv",
            score_as_of_date=str(output.get("snapshot_date") or ""),
            asset_id=player_id,
            display_name=str(roster_row.get("player_name") or player_id),
        )
        keeper = _score(output.get("keeper_score"), private)
        raw_market = _score(output.get("market_score"), keeper)
        market = public_market_score_capped(
            raw_market,
            private_base_score=private,
            position=position,
        )
        confidence = _score(output.get("confidence_score"), 45.0)
        conversion = convert_asset_value(
            AssetConversionInputs(
                private_base_score=private,
                year1_score=private,
                long_horizon_score=keeper,
                age_curve_score=keeper,
                format_fit_score=_score(output.get("lve_format_fit"), private),
                role_security_score=keeper,
                replacement_gap_score=replacement_value,
                public_market_score=market,
                liquidity_score=raw_market,
                confidence_score=confidence,
                risk_penalty=_risk_penalty(output.get("risk_level")),
                current_cost_value=50.0,
                accessibility_bonus=_accessibility_bonus(asset_type),
                roster_spot_cost=_roster_spot_cost(asset_type),
                liquidity_penalty=liquidity_penalty(raw_market),
            )
        )
        assets.append(
            UnifiedAsset(
                asset_id=f"{asset_type}:{player_id}",
                asset_type=asset_type,
                player_id=player_id,
                player_name=str(roster_row.get("player_name") or player_id),
                position=position,
                team=str(roster_row.get("team_name") or roster_row.get("team_id") or ""),
                all_asset_value=conversion.all_asset_value,
                acquisition_value=conversion.acquisition_value,
                keeper_adjusted_value=conversion.keeper_adjusted_value,
                trade_liquidity_value=conversion.trade_liquidity_value,
                win_now_value=conversion.win_now_value,
                dynasty_hold_value=conversion.dynasty_hold_value,
                replacement_value=conversion.replacement_value,
                confidence_score=confidence,
                pick_equivalent=pick_equivalent(conversion.all_asset_value),
                recommendation=_asset_recommendation(
                    asset_type,
                    conversion.all_asset_value,
                    conversion.acquisition_value,
                    league_rank,
                ),
                source="model_outputs.csv",
                replacement_context=replacement_context,
                replacement_position_rank=replacement_rank,
                replacement_baseline=f"{replacement_context}:{position}",
                # Legacy active-pack score disclosure only; not a primary value.
                primary_review_score=None,
                legacy_active_pack_score=_optional_float(
                    score_context.get("legacy_active_pack_score")
                ),
                score_lineage_class=str(score_context.get("score_lineage_class") or ""),
                score_source_path=str(score_context.get("score_source_path") or ""),
                score_source_column=str(score_context.get("score_source_column") or ""),
                score_model_version=str(score_context.get("score_model_version") or ""),
                score_allowed_use=str(score_context.get("score_allowed_use") or ""),
                score_blocked_use=str(score_context.get("score_blocked_use") or ""),
                score_manual_decision_required=bool(
                    score_context.get("score_manual_decision_required")
                ),
                legacy_formula_warning=bool(score_context.get("legacy_formula_warning")),
                stale_or_legacy_formula_warning=bool(
                    score_context.get("stale_or_legacy_formula_warning")
                ),
            )
        )
    return assets


def _pick_assets(rows_by_table: dict[str, list[dict[str, object]]]) -> list[UnifiedAsset]:
    pick_values = {
        (int(row["pick_year"]), str(row["pick_label"])): row
        for row in rows_by_table.get("pick_values", [])
        if row.get("pick_year") is not None and row.get("pick_label")
    }
    assets: list[UnifiedAsset] = []
    for pick in rows_by_table.get("future_picks", []):
        pick_year = int(pick["pick_year"])
        pick_label = str(pick["pick_label"])
        value_row = pick_values.get((pick_year, pick_label), {})
        raw_value = _score_from_pick_value(value_row.get("final_pick_value"))
        confidence = _pick_confidence(str(pick.get("certainty") or "unknown"))
        all_value = pick_all_asset_value(raw_value, pick_year)
        conversion = convert_asset_value(
            AssetConversionInputs(
                private_base_score=all_value,
                year1_score=all_value,
                long_horizon_score=all_value * 0.90,
                age_curve_score=100.0,
                format_fit_score=75.0,
                role_security_score=90.0,
                replacement_gap_score=all_value,
                public_market_score=all_value,
                liquidity_score=95.0,
                confidence_score=confidence,
                current_cost_value=50.0,
                accessibility_bonus=4.0,
            )
        )
        assets.append(
            UnifiedAsset(
                asset_id=f"pick:{pick_year}:{pick_label}",
                asset_type="pick",
                player_id="",
                player_name=pick_label,
                position="PICK",
                team=str(pick.get("current_team_name") or pick.get("current_team_id") or ""),
                all_asset_value=conversion.all_asset_value,
                acquisition_value=conversion.acquisition_value,
                keeper_adjusted_value=0.0,
                trade_liquidity_value=conversion.trade_liquidity_value,
                win_now_value=conversion.win_now_value,
                dynasty_hold_value=conversion.dynasty_hold_value,
                replacement_value=conversion.replacement_value,
                confidence_score=confidence,
                pick_equivalent=pick_label,
                recommendation="pick_optionality"
                if conversion.all_asset_value >= 65
                else "pick_depth",
                source="fact_pick_values.csv",
                replacement_context="pick_curve",
            )
        )
    return assets


def _rookie_assets(rookie_model_dir: str | Path) -> list[UnifiedAsset]:
    run = run_rookie_model_from_dir(rookie_model_dir)
    assets: list[UnifiedAsset] = []
    for score in run.scores:
        conversion = convert_asset_value(
            AssetConversionInputs(
                private_base_score=score.final_decision_score,
                year1_score=score.rookie_opportunity_score,
                long_horizon_score=score.long_term_dynasty_score,
                age_curve_score=score.long_term_dynasty_score,
                format_fit_score=score.league_fit_score,
                role_security_score=score.rookie_opportunity_score,
                replacement_gap_score=score.league_fit_score,
                public_market_score=score.trade_insulation_score,
                liquidity_score=55.0,
                confidence_score=score.confidence_score,
                current_cost_value=50.0,
                accessibility_bonus=3.0,
            )
        )
        assets.append(
            UnifiedAsset(
                asset_id=f"rookie:{score.player_id}",
                asset_type="rookie",
                player_id=score.player_id,
                player_name=score.player_name,
                position=score.position.value,
                team="Rookie Pool",
                all_asset_value=conversion.all_asset_value,
                acquisition_value=conversion.acquisition_value,
                keeper_adjusted_value=conversion.keeper_adjusted_value,
                trade_liquidity_value=conversion.trade_liquidity_value,
                win_now_value=conversion.win_now_value,
                dynasty_hold_value=conversion.dynasty_hold_value,
                replacement_value=conversion.replacement_value,
                confidence_score=score.confidence_score,
                pick_equivalent=pick_equivalent(conversion.all_asset_value),
                recommendation="rookie_target"
                if conversion.all_asset_value >= 74
                else "rookie_stash",
                source="rookie_model",
                replacement_context="declaration_window",
            )
        )
    return assets


def all_asset_value(
    *,
    win_now_value: float,
    dynasty_hold_value: float,
    trade_liquidity_value: float,
    keeper_adjusted_value: float,
    replacement_value: float,
) -> float:
    """Compatibility helper for callers with already-computed component values."""
    return round(
        min(
            max(
                (0.30 * win_now_value)
                + (0.25 * dynasty_hold_value)
                + (0.20 * trade_liquidity_value)
                + (0.15 * keeper_adjusted_value)
                + (0.10 * replacement_value),
                0.0,
            ),
            100.0,
        ),
        2,
    )


def convert_asset_value(inputs: AssetConversionInputs) -> AssetConversionResult:
    replacement = weighted_score(
        (inputs.replacement_gap_score, 70),
        (inputs.role_security_score, 20),
        (inputs.format_fit_score, 10),
    )
    win_now = weighted_score(
        (inputs.year1_score, 45),
        (replacement, 25),
        (inputs.format_fit_score, 15),
        (inputs.confidence_score, 15),
        penalty=inputs.risk_penalty * 0.50,
    )
    dynasty_hold = weighted_score(
        (inputs.private_base_score, 35),
        (inputs.long_horizon_score, 25),
        (inputs.age_curve_score, 20),
        (inputs.role_security_score, 10),
        (inputs.confidence_score, 10),
        penalty=inputs.risk_penalty,
    )
    trade_liquidity = weighted_score(
        (inputs.public_market_score, 45),
        (inputs.liquidity_score, 35),
        (inputs.confidence_score, 20),
    )
    keeper_adjusted = weighted_score(
        (dynasty_hold, 40),
        (win_now, 30),
        (inputs.role_security_score, 20),
        (inputs.confidence_score, 10),
    )
    all_value = weighted_score(
        (keeper_adjusted, 32),
        (win_now, 27),
        (dynasty_hold, 21),
        (trade_liquidity, 12),
        (inputs.confidence_score, 8),
        penalty=inputs.risk_penalty,
    )
    market_free_all_value = weighted_score(
        (keeper_adjusted, 38),
        (win_now, 31),
        (dynasty_hold, 23),
        (inputs.confidence_score, 8),
        penalty=inputs.risk_penalty,
    )
    all_value = cap_market_blended_value(market_free_all_value, all_value)
    acquisition = acquisition_value(
        all_value,
        current_cost_value=inputs.current_cost_value,
        accessibility_bonus=inputs.accessibility_bonus,
        roster_spot_cost=inputs.roster_spot_cost,
        package_penalty=inputs.package_penalty,
        consolidation_bonus=inputs.consolidation_bonus,
        liquidity_penalty=inputs.liquidity_penalty,
    )
    return AssetConversionResult(
        replacement_value=replacement,
        win_now_value=win_now,
        dynasty_hold_value=dynasty_hold,
        trade_liquidity_value=trade_liquidity,
        keeper_adjusted_value=keeper_adjusted,
        all_asset_value=all_value,
        acquisition_value=acquisition,
    )


def weighted_score(*items: tuple[float, float], penalty: float = 0.0) -> float:
    weight_sum = sum(weight for _, weight in items)
    if weight_sum <= 0:
        return 50.0
    value = sum(_score(score) * weight for score, weight in items) / weight_sum
    return round(min(max(value - penalty, 0.0), 100.0), 2)


def public_market_score_capped(
    raw_market_score: float,
    *,
    private_base_score: float,
    position: str,
) -> float:
    format_adjusted = _score(raw_market_score) - PUBLIC_MARKET_FORMAT_PENALTY.get(
        position,
        0.0,
    )
    return round(min(max(format_adjusted, 0.0), _score(private_base_score) + 12.0, 100.0), 2)


def liquidity_penalty(liquidity_score: float) -> float:
    score = _score(liquidity_score)
    if score >= 60:
        return 0.0
    if score >= 40:
        return 3.0
    if score >= 25:
        return 6.0
    return 10.0


def rookie_all_asset_value(
    *,
    final_decision_score: float,
    long_term_dynasty_score: float,
    trade_insulation_score: float,
    rookie_opportunity_score: float,
    league_fit_score: float,
) -> float:
    return round(
        min(
            max(
                (0.35 * final_decision_score)
                + (0.25 * long_term_dynasty_score)
                + (0.20 * trade_insulation_score)
                + (0.10 * rookie_opportunity_score)
                + (0.10 * league_fit_score),
                0.0,
            ),
            100.0,
        ),
        2,
    )


def pick_all_asset_value(current_pick_curve_value: float, pick_year: int) -> float:
    year_discount = pick_year_discount(pick_year)
    optionality = pick_optionality_bonus(current_pick_curve_value)
    return round(min(max((current_pick_curve_value * year_discount) + optionality, 0.0), 100.0), 2)


def acquisition_value(
    all_value: float,
    *,
    confidence_score: float | None = None,
    current_cost_value: float = 50.0,
    accessibility_bonus: float = 0.0,
    roster_spot_cost: float = 0.0,
    liquidity_bonus: float = 0.0,
    package_penalty: float = 0.0,
    consolidation_bonus: float = 0.0,
    liquidity_penalty: float = 0.0,
) -> float:
    confidence_penalty = 0.0
    if confidence_score is not None:
        confidence_penalty = max(0.0, (75.0 - confidence_score) * 0.08)
    raw_value = (
        50.0
        + all_value
        - current_cost_value
        + accessibility_bonus
        + liquidity_bonus
        - roster_spot_cost
        - confidence_penalty
        - package_penalty
        + consolidation_bonus
        - liquidity_penalty
    )
    return round(min(max(raw_value, 0.0), 100.0), 2)


def pick_equivalent(value: float) -> str:
    return pick_equivalent_label(value)


def _asset_row(asset: UnifiedAsset) -> dict[str, object]:
    return {
        "asset_id": asset.asset_id,
        "asset_type": asset.asset_type,
        "player": asset.player_name,
        "position": asset.position,
        "team": asset.team,
        "all_asset_value": asset.all_asset_value,
        "acquisition_value": asset.acquisition_value,
        "keeper_adjusted_value": asset.keeper_adjusted_value,
        "trade_liquidity_value": asset.trade_liquidity_value,
        "win_now_value": asset.win_now_value,
        "dynasty_hold_value": asset.dynasty_hold_value,
        "replacement_value": asset.replacement_value,
        "replacement_context": asset.replacement_context,
        "replacement_position_rank": asset.replacement_position_rank,
        "replacement_baseline": asset.replacement_baseline,
        "confidence": asset.confidence_score,
        "pick_equivalent": asset.pick_equivalent,
        "recommendation": asset.recommendation,
        "source": asset.source,
        "primary_review_score": (
            "" if asset.primary_review_score is None else asset.primary_review_score
        ),
        # Keep legacy score comparison-only in exported rows.
        "legacy_active_pack_score": (
            "" if asset.legacy_active_pack_score is None else asset.legacy_active_pack_score
        ),
        "score_lineage_class": asset.score_lineage_class,
        "score_source_path": asset.score_source_path,
        "score_source_column": asset.score_source_column,
        "score_model_version": asset.score_model_version,
        "score_allowed_use": asset.score_allowed_use,
        "score_blocked_use": asset.score_blocked_use,
        "score_manual_decision_required": asset.score_manual_decision_required,
        "legacy_formula_warning": asset.legacy_formula_warning,
        "stale_or_legacy_formula_warning": asset.stale_or_legacy_formula_warning,
    }


def _asset_type_for_roster_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized in {"released", "released_veteran"}:
        return "released_veteran"
    if normalized in {"free_agent", "fa", "available"}:
        return "free_agent"
    return "veteran"


def _replacement_context_for_asset_type(asset_type: str) -> str:
    if asset_type in {"released_veteran", "free_agent"}:
        return "declaration_window"
    return "steady_state"


def _asset_recommendation(
    asset_type: str,
    all_value: float,
    acquisition: float,
    league_rank: object,
) -> str:
    if asset_type == "released_veteran":
        return "released_target" if acquisition >= 66 else "released_depth"
    if asset_type == "free_agent":
        return "fa_add" if acquisition >= 70 else "fa_watch"
    if league_rank is not None and all_value < 64:
        return "release_watch"
    if all_value >= 84:
        return "core_asset"
    if all_value >= 68:
        return "keeper"
    return "bubble"


def _score(value: object, default: float = 50.0) -> float:
    if value is None or value == "":
        return default
    return min(max(float(value), 0.0), 100.0)


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _score_from_pick_value(value: object) -> float:
    if value is None or value == "":
        return 0.0
    return min(max(float(value) / 10.0, 0.0), 100.0)


def _pick_confidence(certainty: str) -> float:
    if certainty == "known":
        return 95.0
    if certainty == "projected":
        return 78.0
    if certainty == "estimated":
        return 65.0
    return 50.0


def _roster_spot_cost(asset_type: str) -> float:
    if asset_type == "free_agent":
        return 6.0
    if asset_type == "released_veteran":
        return 2.0
    return 0.0


def _accessibility_bonus(asset_type: str) -> float:
    if asset_type == "released_veteran":
        return 4.0
    if asset_type == "free_agent":
        return 6.0
    return 0.0


def _risk_penalty(risk_level: object) -> float:
    risk = str(risk_level or "").strip().lower()
    if risk == "high":
        return 8.0
    if risk == "medium":
        return 4.0
    return 0.0


def _model_position_ranks(
    roster_rows: list[dict[str, object]],
    outputs: dict[str, dict[str, object]],
) -> dict[str, int]:
    ranked_rows: list[tuple[str, str, float]] = []
    for roster_row in roster_rows:
        player_id = str(roster_row.get("player_id") or "")
        position = str(roster_row.get("position") or "")
        if not player_id or position not in {"QB", "RB", "WR", "TE"}:
            continue
        output = outputs.get(player_id, {})
        model_value = _score(
            _first_present(
                output.get("private_score"),
                output.get("war_score"),
                output.get("keeper_score"),
            )
        )
        ranked_rows.append((player_id, position, model_value))

    ranks: dict[str, int] = {}
    for position in {"QB", "RB", "WR", "TE"}:
        position_rows = [
            (player_id, model_value)
            for player_id, row_position, model_value in ranked_rows
            if row_position == position
        ]
        for rank, (player_id, _) in enumerate(
            sorted(position_rows, key=lambda row: (-row[1], row[0])),
            start=1,
        ):
            ranks[player_id] = rank
    return ranks


def _trade_asset(asset: UnifiedAsset) -> TradeAsset:
    return TradeAsset(
        name=asset.player_name,
        private_value=asset.acquisition_value,
        market_value=asset.trade_liquidity_value,
        keeper_value=asset.keeper_adjusted_value,
    )


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return None
