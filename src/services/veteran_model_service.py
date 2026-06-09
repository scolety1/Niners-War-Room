from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.models.veteran_scores import (
    VeteranInput,
    VeteranPosition,
    VeteranScore,
    score_veteran,
)
from src.services.market_influence_policy_service import (
    cap_market_blended_value,
    market_edge_label,
    market_edge_score,
)
from src.services.veteran_model_schema_service import (
    VeteranFeatureDefinition,
    VeteranFeatureScore,
    VeteranSchemaReport,
    build_veteran_schema_report,
)


@dataclass(frozen=True)
class VeteranModelRun:
    model_version: str
    schema_report: VeteranSchemaReport
    scores: tuple[VeteranScore, ...]


def run_veteran_model_from_dir(data_dir: str | Path) -> VeteranModelRun:
    report = build_veteran_schema_report(data_dir)
    if report.has_errors:
        issue_summary = "; ".join(issue.issue for issue in report.issues[:3])
        raise ValueError(f"Veteran model input has validation errors: {issue_summary}")

    inputs = veteran_inputs_from_report(report)
    scores = tuple(score_veteran(veteran) for veteran in inputs)
    model_version = scores[0].model_version if scores else "veteran_lve_v1_1_0"
    return VeteranModelRun(
        model_version=model_version,
        schema_report=report,
        scores=tuple(
            sorted(
                scores,
                key=lambda score: (
                    -score.keeper_score,
                    -score.veteran_base_value,
                    score.player_name,
                ),
            )
        ),
    )


def veteran_inputs_from_report(report: VeteranSchemaReport) -> tuple[VeteranInput, ...]:
    registry_by_position_feature = {
        (feature.position, feature.feature_name): feature for feature in report.registry
    }
    scores_by_player_feature = {
        (score.player_id, score.feature_name): score for score in report.feature_scores
    }
    source_reliability_by_key = {
        source.source_key: source.reliability_score for source in report.sources
    }
    source_date_by_key = {source.source_key: source.source_date for source in report.sources}
    source_freshness_window_by_key = {
        source.source_key: source.freshness_window_hours for source in report.sources
    }
    inputs: list[VeteranInput] = []
    for player in report.players:
        position = VeteranPosition(player.position)
        player_feature_names = {
            score.feature_name
            for score in report.feature_scores
            if score.player_id == player.player_id and score.position == player.position
        }
        registry_features = [
            feature
            for feature in report.registry
            if feature.position == player.position
            and feature.parent_component != "display_only"
            and (
                feature.scoring_status == "active_v1"
                or (
                    feature.scoring_status == "future_candidate"
                    and feature.feature_name in player_feature_names
                )
            )
        ]
        features: dict[str, float | None] = {}
        missing_penalties: dict[str, float] = {}
        source_reliability: dict[str, float] = {}
        source_freshness: dict[str, float] = {}
        source_confidence: dict[str, str] = {}
        user_overrides: dict[str, bool] = {}
        for feature in registry_features:
            row = scores_by_player_feature.get((player.player_id, feature.feature_name))
            value, reliability, freshness, confidence, is_override = _feature_context(
                row,
                feature,
                source_reliability_by_key,
                source_date_by_key,
                source_freshness_window_by_key,
            )
            features[feature.feature_name] = value
            missing_penalties[feature.feature_name] = feature.missing_data_penalty
            source_reliability[feature.feature_name] = reliability
            source_freshness[feature.feature_name] = freshness
            source_confidence[feature.feature_name] = confidence
            user_overrides[feature.feature_name] = is_override

        _ensure_position_features(position, features, registry_by_position_feature)
        inputs.append(
            VeteranInput(
                player_id=player.player_id,
                player_name=player.player_name,
                position=position,
                age=player.age,
                league_rank=player.league_rank,
                is_league_rank_top5=player.is_league_rank_top5,
                features=features,
                missing_penalties=missing_penalties,
                source_reliability=source_reliability,
                source_freshness=source_freshness,
                source_confidence=source_confidence,
                user_overrides=user_overrides,
            )
        )
    return tuple(inputs)


def generated_model_output_rows(
    scores: Iterable[VeteranScore],
    *,
    snapshot_date: str,
    computed_at: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for score in scores:
        market_trade_value = _market_trade_value_from_score(score)
        edge_score = market_edge_score(score.veteran_base_value, market_trade_value)
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "player_id": score.player_id,
                "player_name": score.player_name,
                "position": score.position.value,
                "private_score": score.veteran_base_value,
                # Keep the historical CSV column for compatibility. In the UI
                # and docs this is labeled Trade Liquidity, not player quality.
                "market_score": market_trade_value,
                "war_score": _war_score(score.keeper_score, score.trade_value),
                "keeper_score": score.keeper_score,
                "drop_candidate_score": score.drop_candidate_score,
                "veteran_base_value": score.veteran_base_value,
                "horizon_retention_score": score.horizon_retention_score,
                "trade_value": score.trade_value,
                "market_trade_value": market_trade_value,
                "market_edge_score": edge_score,
                "market_edge_label": market_edge_label(edge_score),
                "market_edge_warning": _market_edge_warning(score),
                "lve_format_fit": score.lve_format_fit,
                "structural_adjustment": score.structural_adjustment,
                "league_rank_signal": score.league_rank_signal,
                "top_five_release_pressure": score.top_five_release_pressure,
                "league_rank_adjustment": score.league_rank_adjustment,
                "missing_data_penalty": score.missing_data_penalty,
                "pick_adjusted_value": round(score.trade_value * 10, 1),
                "confidence_score": score.confidence_score,
                "risk_level": _risk_level(score.risk_flags, score.confidence_score),
                "warning_status": score.warning_status,
                "warning_reasons": "|".join(score.warning_reasons),
                "recommendation": _model_recommendation(
                    score.drop_candidate_score,
                    score.keeper_score,
                ),
                "do_not_draft_before_pick": "",
                "model_version": score.model_version,
                "computed_at": computed_at,
                "risk_flags": "|".join(score.risk_flags),
                "upside_flags": "|".join(score.upside_flags),
                "floor_flags": "|".join(score.floor_flags),
                "notes": _model_notes(
                    score.risk_flags,
                    score.upside_flags,
                    score.floor_flags,
                ),
            }
        )
    return rows


def write_generated_model_outputs(
    path: str | Path,
    scores: Iterable[VeteranScore],
    *,
    snapshot_date: str,
    computed_at: str,
) -> None:
    rows = generated_model_output_rows(
        scores,
        snapshot_date=snapshot_date,
        computed_at=computed_at,
    )
    _write_csv(Path(path), rows)


def _war_score(keeper_score: float, trade_value: float) -> float:
    raw_score = (keeper_score * 0.70) + (trade_value * 0.30)
    return cap_market_blended_value(keeper_score, raw_score)


def _market_trade_value_from_score(score: VeteranScore) -> float:
    for contribution in score.contributions:
        if (
            contribution.component == "trade_value"
            and contribution.feature_name == "market_liquidity_proxy"
        ):
            return round(contribution.normalized_score, 2)
    return score.trade_value


def _market_edge_warning(score: VeteranScore) -> str:
    if score.warning_status in {"blocking", "review_needed"}:
        return f"review:{score.warning_status}"
    if score.warning_reasons:
        return "source_warning:" + "|".join(score.warning_reasons)
    return "none"


def _risk_level(risk_flags: tuple[str, ...], confidence_score: float) -> str:
    if confidence_score < 65 or any("risk" in flag for flag in risk_flags):
        return "high"
    if risk_flags:
        return "medium"
    return "low"


def _model_recommendation(drop_score: float, keeper_score: float) -> str:
    if drop_score >= 55:
        return "shop/release"
    if drop_score >= 35:
        return "shop"
    if keeper_score >= 82:
        return "keep"
    return "bubble"


def _model_notes(
    risk_flags: tuple[str, ...],
    upside_flags: tuple[str, ...],
    floor_flags: tuple[str, ...],
) -> str:
    parts = []
    if risk_flags:
        parts.append(f"risk={'|'.join(risk_flags)}")
    if upside_flags:
        parts.append(f"upside={'|'.join(upside_flags)}")
    if floor_flags:
        parts.append(f"floor={'|'.join(floor_flags)}")
    return "; ".join(parts) or "Scored veteran model output."


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _feature_context(
    row: VeteranFeatureScore | None,
    feature: VeteranFeatureDefinition,
    source_reliability_by_key: dict[str, float],
    source_date_by_key: dict[str, str],
    source_freshness_window_by_key: dict[str, int | None],
) -> tuple[float | None, float, float, str, bool]:
    if row is None or row.is_missing:
        return None, 50.0, 50.0, "unknown", False
    return (
        row.normalized_score,
        source_reliability_by_key.get(row.source_key, 50.0),
        _source_freshness_score(
            row.snapshot_date,
            source_date_by_key.get(row.source_key, ""),
            source_freshness_window_by_key.get(row.source_key),
        ),
        row.source_confidence,
        row.is_user_override,
    )


def _source_freshness_score(
    snapshot_date: str,
    source_date: str,
    freshness_window_hours: int | None = None,
) -> float:
    try:
        snapshot = date.fromisoformat(snapshot_date[:10])
        source = date.fromisoformat(source_date[:10])
    except ValueError:
        return 50.0
    age_days = max(0, (snapshot - source).days)
    if freshness_window_hours:
        age_hours = age_days * 24
        if age_hours <= freshness_window_hours:
            return 100.0
        if age_hours <= freshness_window_hours * 3:
            return 70.0
        if age_hours <= freshness_window_hours * 7:
            return 40.0
        return 10.0
    if age_days <= 14:
        return 100.0
    if age_days <= 45:
        return 90.0
    if age_days <= 90:
        return 75.0
    if age_days <= 180:
        return 60.0
    if age_days <= 365:
        return 45.0
    return 30.0


def _ensure_position_features(
    position: VeteranPosition,
    features: dict[str, float | None],
    registry_by_position_feature: dict[tuple[str, str], VeteranFeatureDefinition],
) -> None:
    # The scoring model reads a few synthetic-safe keys by position. If a future registry
    # version omits one, neutralize it here rather than letting missing keys drift.
    expected = {
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
            "target_earning_stability",
            "age_curve",
            "market_liquidity",
        ),
        VeteranPosition.TE: (
            "lve_projection_value",
            "route_share_stability",
            "role_security",
            "position_replaceability",
            "age_curve",
        ),
    }[position]
    for feature_name in expected:
        if (position.value, feature_name) in registry_by_position_feature:
            features.setdefault(feature_name, None)
