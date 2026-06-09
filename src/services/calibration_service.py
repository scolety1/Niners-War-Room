from __future__ import annotations

from dataclasses import dataclass, replace

from src.models.rookie_scores import ModelMode, Position, RookieInput, score_rookie
from src.models.veteran_scores import VeteranInput, VeteranPosition, score_veteran
from src.services.asset_board_service import (
    UnifiedAsset,
    compare_pick_to_player,
    compare_rookie_to_veteran,
)
from src.services.forced_release_strategy_service import pre_declaration_trade_urgency
from src.services.historical_draft_service import (
    HistoricalReplayComparisonBoard,
    load_offline_rookie_notes,
)

HISTORICAL_NOTES = "sample_data/historical_rookie_notes/offline_notes_four_seasons.csv"


@dataclass(frozen=True)
class CalibrationScenario:
    scenario_id: str
    category: str
    expected_behavior: str
    observed_behavior: str
    passed: bool
    notes: str


@dataclass(frozen=True)
class SensitivityResult:
    scenario_id: str
    model_area: str
    baseline_score: float
    perturbed_score: float
    absolute_change: float
    volatility: str


@dataclass(frozen=True)
class CalibrationReport:
    scenario_rows: list[dict[str, object]]
    sensitivity_rows: list[dict[str, object]]
    historical_rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]


def build_calibration_report() -> CalibrationReport:
    scenarios = _scenario_results()
    sensitivity = _sensitivity_results()
    historical_rows = _historical_rows()
    return CalibrationReport(
        scenario_rows=[scenario.__dict__ for scenario in scenarios],
        sensitivity_rows=[row.__dict__ for row in sensitivity],
        historical_rows=historical_rows,
        summary_rows=[
            {
                "area": "scenario_pass_rate",
                "value": f"{sum(scenario.passed for scenario in scenarios)}/{len(scenarios)}",
                "notes": "Calibration fixtures check direction, gates, and LVE-specific traps.",
            },
            {
                "area": "max_sensitivity_change",
                "value": max(row.absolute_change for row in sensitivity),
                "notes": "Single-feature +5 perturbations should not swing final decisions wildly.",
            },
            {
                "area": "historical_rookie_records",
                "value": len(historical_rows),
                "notes": "Handwritten/offline records are provenance aids, not outcome labels yet.",
            },
        ],
    )


def calibration_verdict_summary_rows(
    comparison: HistoricalReplayComparisonBoard,
) -> list[dict[str, object]]:
    total_rows = len(comparison.rows)
    rows: list[dict[str, object]] = []
    for verdict in sorted({row.replay_verdict for row in comparison.rows}):
        count = sum(1 for row in comparison.rows if row.replay_verdict == verdict)
        rows.append(
            {
                "replay_verdict": verdict,
                "count": count,
                "share_pct": round((count / total_rows) * 100, 1) if total_rows else 0.0,
                "calibration_meaning": _verdict_meaning(verdict),
            }
        )
    return rows


def calibration_readiness_rows(
    report: CalibrationReport,
    comparison: HistoricalReplayComparisonBoard,
) -> list[dict[str, object]]:
    scenario_count = len(report.scenario_rows)
    scenario_passes = sum(1 for row in report.scenario_rows if row["passed"])
    high_volatility_count = sum(
        1 for row in report.sensitivity_rows if row["volatility"] == "high"
    )
    missing_model_count = comparison.missing_model_count
    return [
        {
            "area": "scenario_fixtures",
            "status": "ready" if scenario_passes == scenario_count else "review",
            "value": f"{scenario_passes}/{scenario_count}",
            "meaning": "Core LVE traps pass their deterministic behavior checks."
            if scenario_passes == scenario_count
            else "At least one LVE trap fixture needs formula review.",
        },
        {
            "area": "sensitivity",
            "status": "ready" if high_volatility_count == 0 else "review",
            "value": high_volatility_count,
            "meaning": "No single tested input causes a high-volatility score swing."
            if high_volatility_count == 0
            else "A tested input can swing scores too sharply.",
        },
        {
            "area": "historical_model_rows",
            "status": "review" if missing_model_count else "ready",
            "value": missing_model_count,
            "meaning": "Some actual historical picks lack as-of model replay rows."
            if missing_model_count
            else "Loaded historical picks have matching as-of model replay rows.",
        },
        {
            "area": "current_score_safety",
            "status": "ready",
            "value": "isolated",
            "meaning": "Calibration report data is read-only and does not feed current boards.",
        },
    ]


def _verdict_meaning(verdict: str) -> str:
    meanings = {
        "missing_model_replay": "Historical pick has no as-of model row yet.",
        "rank_aligned_needs_outcome": "Model rank matched the room, but outcome is not scored.",
        "rank_gap_needs_outcome": "Model and room disagreed, but outcome is not scored.",
        "model_found_value": "Model was higher than the room and the outcome supported it.",
        "model_correctly_faded": "Model was lower than the room and the outcome supported it.",
        "model_missed_hit": "Model was too low on a later hit.",
        "model_overrated_miss": "Model was too high on a later miss.",
        "model_aligned": "Model and room were close enough for this fixture.",
    }
    return meanings.get(verdict, "Replay verdict needs review.")


def _scenario_results() -> list[CalibrationScenario]:
    obvious_keep = score_veteran(_veteran("obvious_keep", VeteranPosition.WR, 90, 88, 86, 85, 82))
    obvious_cut = score_veteran(_veteran("obvious_cut", VeteranPosition.RB, 38, 42, 35, 30, 40))
    forced_star = score_veteran(_veteran("forced_star", VeteranPosition.WR, 86, 86, 88, 85, 82))
    forced_star_urgency = pre_declaration_trade_urgency(
        keeper_score=forced_star.keeper_score,
        market_score=forced_star.trade_value,
        drop_score=forced_star.drop_candidate_score,
        confidence_score=forced_star.confidence_score,
        is_default_release=True,
    )
    rookie_asset = _asset("rookie:alpha_wr", "rookie", "Alpha Rookie", "WR", 82, 82, 86)
    veteran_asset = _asset("veteran:solid_wr", "veteran", "Solid Veteran", "WR", 73, 73, 72)
    pick_asset = _asset("pick:2026:1.04", "pick", "2026 1.04", "PICK", 84, 88, 95)
    player_asset = _asset("veteran:bubble_rb", "veteran", "Bubble RB", "RB", 68, 68, 66)
    rookie_vs_vet = compare_rookie_to_veteran(rookie_asset, veteran_asset)
    pick_vs_player = compare_pick_to_player(pick_asset, player_asset)
    pocket_qb = score_rookie(
        _rookie(
            "pocket_qb",
            Position.QB,
            {
                "draft_capital": 88,
                "rushing_profile": 25,
                "passing_efficiency": 86,
                "sack_avoidance": 80,
                "age_trajectory": 76,
            },
            veteran_benchmark=72,
        )
    )
    day3_te = score_rookie(
        _rookie(
            "day3_te",
            Position.TE,
            {
                "draft_capital": 38,
                "receiving_efficiency": 70,
                "route_role": 58,
                "production_volume": 65,
                "athletic_size": 78,
                "age_trajectory": 72,
            },
            veteran_benchmark=66,
        )
    )
    return [
        CalibrationScenario(
            "obvious_keep",
            "veteran",
            "Elite veteran should remain a strong keeper.",
            f"keeper={obvious_keep.keeper_score}, drop={obvious_keep.drop_candidate_score}",
            obvious_keep.keeper_score >= 82 and obvious_keep.drop_candidate_score < 35,
            "Protects against accidental over-cutting of clear core assets.",
        ),
        CalibrationScenario(
            "obvious_cut",
            "veteran",
            "Weak veteran should be a cut/shop candidate.",
            f"keeper={obvious_cut.keeper_score}, drop={obvious_cut.drop_candidate_score}",
            obvious_cut.keeper_score < 60 and obvious_cut.drop_candidate_score >= 35,
            "Checks that low role/value profiles do not survive as false keeps.",
        ),
        CalibrationScenario(
            "forced_release_star",
            "forced_release",
            "High-value forced-release player should be shopped before declaration.",
            f"urgency={forced_star_urgency}",
            forced_star_urgency >= 58,
            "Separates rule requirement from strategic action.",
        ),
        CalibrationScenario(
            "veteran_vs_rookie",
            "asset_conversion",
            "Superior rookie asset should beat a lower veteran.",
            rookie_vs_vet.recommendation,
            rookie_vs_vet.recommendation == "rookie",
            "Checks unified board acquisition math direction.",
        ),
        CalibrationScenario(
            "pick_vs_player",
            "asset_conversion",
            "Strong pick should beat a bubble player.",
            pick_vs_player.recommendation,
            pick_vs_player.recommendation == "pick_optionality",
            "Checks pick optionality remains live.",
        ),
        CalibrationScenario(
            "qb_1qb_suppression",
            "rookie",
            "Good pocket QB should still be suppressed in 1QB.",
            f"gate={pocket_qb.gate_applied}, final={pocket_qb.final_decision_score}",
            pocket_qb.gate_applied == "qb_structural_penalty"
            and pocket_qb.do_not_draft_before_pick >= 11,
            "Protects against generic Superflex drift.",
        ),
        CalibrationScenario(
            "te_no_premium_suppression",
            "rookie",
            "Low-capital TE should be heavily suppressed in no-premium.",
            f"gate={day3_te.gate_applied}, final={day3_te.final_decision_score}",
            day3_te.gate_applied == "te_day3_penalty"
            and day3_te.do_not_draft_before_pick >= 31,
            "Protects against generic TE-premium drift.",
        ),
    ]


def _sensitivity_results() -> list[SensitivityResult]:
    veteran = _veteran("sensitivity_vet", VeteranPosition.RB, 78, 76, 80, 74, 82)
    veteran_score = score_veteran(veteran)
    hotter_veteran = replace(
        veteran,
        features={**veteran.features, "role_security": veteran.features["role_security"] + 5},
    )
    hotter_veteran_score = score_veteran(hotter_veteran)
    rookie = _rookie(
        "sensitivity_wr",
        Position.WR,
        {
            "draft_capital": 76,
            "target_earning": 78,
            "efficiency_dominance": 76,
            "age_trajectory": 74,
            "chain_moving": 72,
        },
        veteran_benchmark=72,
    )
    rookie_score = score_rookie(rookie)
    hotter_rookie = replace(
        rookie,
        features={**rookie.features, "target_earning": rookie.features["target_earning"] + 5},
    )
    hotter_rookie_score = score_rookie(hotter_rookie)
    rookie_change = abs(
        hotter_rookie_score.final_decision_score - rookie_score.final_decision_score
    )
    rows = [
        SensitivityResult(
            "veteran_role_security_plus_5",
            "veteran_keeper",
            veteran_score.keeper_score,
            hotter_veteran_score.keeper_score,
            round(abs(hotter_veteran_score.keeper_score - veteran_score.keeper_score), 2),
            _volatility(abs(hotter_veteran_score.keeper_score - veteran_score.keeper_score)),
        ),
        SensitivityResult(
            "rookie_target_earning_plus_5",
            "rookie_final",
            rookie_score.final_decision_score,
            hotter_rookie_score.final_decision_score,
            round(rookie_change, 2),
            _volatility(rookie_change),
        ),
    ]
    return rows


def _historical_rows() -> list[dict[str, object]]:
    board = load_offline_rookie_notes(HISTORICAL_NOTES)
    return [
        {
            "season": entry.season,
            "rookie_pick": entry.rookie_pick_number,
            "player": entry.drafted_player,
            "team": entry.drafting_team,
            "position": entry.position,
            "confidence": entry.confidence,
            "needs_review": entry.needs_traded_pick_review,
            "source": entry.source,
        }
        for entry in board.entries
    ]


def _veteran(
    player_id: str,
    position: VeteranPosition,
    projection: float,
    role: float,
    market_or_position: float,
    age: float,
    durability_or_fit: float,
) -> VeteranInput:
    feature_names = {
        VeteranPosition.QB: (
            "lve_projection_value",
            "role_security",
            "market_liquidity",
            "age_curve",
            "position_replaceability",
        ),
        VeteranPosition.RB: (
            "lve_projection_value",
            "role_security",
            "first_down_td_fit",
            "age_curve",
            "injury_durability",
        ),
        VeteranPosition.WR: (
            "lve_projection_value",
            "role_security",
            "market_liquidity",
            "age_curve",
            "target_earning_stability",
        ),
        VeteranPosition.TE: (
            "lve_projection_value",
            "route_share_stability",
            "role_security",
            "age_curve",
            "position_replaceability",
        ),
    }[position]
    values = (projection, role, market_or_position, age, durability_or_fit)
    features = dict(zip(feature_names, values, strict=True))
    return VeteranInput(
        player_id=player_id,
        player_name=player_id.replace("_", " ").title(),
        position=position,
        age=27.0,
        league_rank=20,
        is_league_rank_top5=True,
        features=features,
        missing_penalties={name: 6.0 for name in features},
        source_reliability={name: 85.0 for name in features},
        source_freshness={name: 90.0 for name in features},
        source_confidence={name: "derived" for name in features},
        user_overrides={name: False for name in features},
    )


def _rookie(
    player_id: str,
    position: Position,
    features: dict[str, float],
    *,
    veteran_benchmark: float,
) -> RookieInput:
    return RookieInput(
        player_id=player_id,
        player_name=player_id.replace("_", " ").title(),
        position=position,
        class_year=2026,
        model_mode=ModelMode.POST_DRAFT,
        source_snapshot_id="calibration_fixture",
        source_name="calibration_fixture",
        source_date="2026-05-05",
        features=features,
        feature_sources={name: "calibration_fixture" for name in features},
        rookie_opportunity_score=70,
        veteran_benchmark_score=veteran_benchmark,
    )


def _asset(
    asset_id: str,
    asset_type: str,
    name: str,
    position: str,
    all_value: float,
    acquisition: float,
    confidence: float,
) -> UnifiedAsset:
    return UnifiedAsset(
        asset_id=asset_id,
        asset_type=asset_type,
        player_id=asset_id.split(":")[-1],
        player_name=name,
        position=position,
        team="Calibration",
        all_asset_value=all_value,
        acquisition_value=acquisition,
        keeper_adjusted_value=all_value,
        trade_liquidity_value=all_value,
        win_now_value=all_value,
        dynasty_hold_value=all_value,
        replacement_value=all_value,
        confidence_score=confidence,
        pick_equivalent="2.01-2.05",
        recommendation="calibration",
        source="calibration_fixture",
    )


def _volatility(change: float) -> str:
    if change >= 6:
        return "high"
    if change >= 3:
        return "medium"
    return "low"
