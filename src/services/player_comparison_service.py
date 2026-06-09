from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.veteran_scores import VeteranPosition, VeteranScore
from src.services.market_influence_policy_service import market_edge_label
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    STATS_FIRST_CONTRIBUTION_FILE,
    STATS_FIRST_NORMALIZED_FEATURE_FILE,
    build_player_feature_receipts,
)
from src.services.veteran_model_service import run_veteran_model_from_dir
from src.services.warning_language_service import warning_summary

SCORE_METRICS = (
    ("war_score", "War Room"),
    ("keeper_score", "Keeper"),
    ("veteran_base_value", "Private LVE"),
    ("trade_value", "Trade Liquidity"),
    ("drop_candidate_score", "Drop"),
    ("horizon_retention_score", "Dynasty Hold"),
    ("lve_format_fit", "LVE Fit"),
    ("confidence_score", "Confidence"),
)


@dataclass(frozen=True)
class PlayerComparisonReport:
    player_options: list[dict[str, object]]
    player_a: dict[str, object]
    player_b: dict[str, object]
    score_rows: list[dict[str, object]]
    component_rows: list[dict[str, object]]
    feature_rows: list[dict[str, object]]
    gap_driver_rows: list[dict[str, object]]
    warning_rows: list[dict[str, object]]
    market_edge_rows: list[dict[str, object]]
    issues: list[str]


@dataclass(frozen=True)
class ComparablePlayerScore:
    player_id: str
    player_name: str
    position: VeteranPosition
    model_version: str
    veteran_base_value: float
    horizon_retention_score: float
    keeper_score: float
    drop_candidate_score: float
    trade_value: float
    confidence_score: float
    lve_format_fit: float
    warning_status: str
    warning_reasons: tuple[str, ...]
    risk_flags: tuple[str, ...]
    upside_flags: tuple[str, ...]
    floor_flags: tuple[str, ...]


def build_player_compare_options(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
) -> list[dict[str, object]]:
    source_root = _veteran_model_dir(veteran_model_dir)
    active_scores = _active_stats_first_scores(data_pack_path, source_root)
    if active_scores:
        output_lookup = _data_pack_model_lookup(data_pack_path)
        return [
            _option_row(score, output_lookup.get(score.player_id, {}), None)
            for score in sorted(active_scores, key=lambda row: row.player_name)
        ]
    try:
        model_run = run_veteran_model_from_dir(source_root)
    except ValueError:
        return []
    output_lookup = _data_pack_model_lookup(data_pack_path)
    player_lookup = {player.player_id: player for player in model_run.schema_report.players}
    return [
        _option_row(
            score,
            output_lookup.get(score.player_id, {}),
            player_lookup.get(score.player_id),
        )
        for score in sorted(model_run.scores, key=lambda row: row.player_name)
    ]


def compare_players(
    data_pack_path: str | Path,
    player_a: str,
    player_b: str,
    *,
    veteran_model_dir: str | Path | None = None,
    gap_driver_limit: int = 15,
) -> PlayerComparisonReport:
    source_root = _veteran_model_dir(veteran_model_dir)
    active_scores = _active_stats_first_scores(data_pack_path, source_root)
    if active_scores:
        return _compare_score_set(
            data_pack_path,
            source_root,
            active_scores,
            player_a,
            player_b,
            gap_driver_limit,
        )
    try:
        model_run = run_veteran_model_from_dir(source_root)
    except ValueError as exc:
        return _empty_report([str(exc)])

    return _compare_score_set(
        data_pack_path,
        source_root,
        list(model_run.scores),
        player_a,
        player_b,
        gap_driver_limit,
        player_lookup={player.player_id: player for player in model_run.schema_report.players},
    )


def _compare_score_set(
    data_pack_path: str | Path,
    source_root: Path,
    scores: list[VeteranScore | ComparablePlayerScore],
    player_a: str,
    player_b: str,
    gap_driver_limit: int,
    *,
    player_lookup: dict[str, object] | None = None,
) -> PlayerComparisonReport:
    output_lookup = _data_pack_model_lookup(data_pack_path)
    player_lookup = player_lookup or {}
    score_lookup = {score.player_id: score for score in scores}
    name_lookup = {score.player_name.lower(): score for score in scores}
    score_a = score_lookup.get(player_a) or name_lookup.get(player_a.lower())
    score_b = score_lookup.get(player_b) or name_lookup.get(player_b.lower())
    if score_a is None or score_b is None:
        return _empty_report(["One or both selected players were not found in model inputs."])

    options = [
        _option_row(
            score,
            output_lookup.get(score.player_id, {}),
            player_lookup.get(score.player_id),
        )
        for score in sorted(scores, key=lambda row: row.player_name)
    ]
    receipts = build_player_feature_receipts(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    feature_rows = _feature_comparison_rows(receipts.rows, score_a, score_b)
    gap_driver_rows = sorted(
        feature_rows,
        key=lambda row: abs(float(row["contribution_gap_a_minus_b"])),
        reverse=True,
    )[:gap_driver_limit]
    return PlayerComparisonReport(
        player_options=options,
        player_a=_player_summary(
            score_a,
            output_lookup.get(score_a.player_id, {}),
            player_lookup.get(score_a.player_id),
        ),
        player_b=_player_summary(
            score_b,
            output_lookup.get(score_b.player_id, {}),
            player_lookup.get(score_b.player_id),
        ),
        score_rows=_score_rows(score_a, score_b, output_lookup),
        component_rows=_component_rows(receipts.component_summary_rows, score_a, score_b),
        feature_rows=feature_rows,
        gap_driver_rows=gap_driver_rows,
        warning_rows=_warning_rows(score_a, score_b),
        market_edge_rows=_market_edge_rows(score_a, score_b, output_lookup),
        issues=receipts.issues,
    )


def _empty_report(issues: list[str]) -> PlayerComparisonReport:
    return PlayerComparisonReport([], {}, {}, [], [], [], [], [], [], issues)


def _veteran_model_dir(veteran_model_dir: str | Path | None) -> Path:
    if veteran_model_dir is not None:
        return Path(veteran_model_dir)
    return DEFAULT_RECEIPT_VETERAN_MODEL_DIR


def _data_pack_model_lookup(data_pack_path: str | Path) -> dict[str, dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    if validated.has_errors:
        return {}
    return {
        str(row.get("player_id") or ""): row
        for row in validated.rows_by_table.get("model_outputs", [])
        if row.get("player_id")
    }


def _active_stats_first_scores(
    data_pack_path: str | Path,
    source_root: Path,
) -> list[ComparablePlayerScore]:
    if not (
        (source_root / STATS_FIRST_CONTRIBUTION_FILE).exists()
        and (source_root / STATS_FIRST_NORMALIZED_FEATURE_FILE).exists()
    ):
        return []
    rows = _data_pack_model_lookup(data_pack_path).values()
    scores = [_comparable_score_from_output(row) for row in rows]
    return [score for score in scores if score is not None]


def _comparable_score_from_output(
    row: dict[str, object],
) -> ComparablePlayerScore | None:
    try:
        position = VeteranPosition(str(row.get("position") or ""))
    except ValueError:
        return None
    model_version = str(row.get("model_version") or "")
    if not model_version or "placeholder" in model_version.lower():
        return None
    player_id = str(row.get("player_id") or "")
    player_name = str(row.get("player_name") or row.get("player") or "")
    if not player_id or not player_name:
        return None
    return ComparablePlayerScore(
        player_id=player_id,
        player_name=player_name,
        position=position,
        model_version=model_version,
        veteran_base_value=_float(row.get("veteran_base_value"), _float(row.get("private_score"))),
        horizon_retention_score=_float(
            row.get("horizon_retention_score"),
            _float(row.get("dynasty_hold_value")),
        ),
        keeper_score=_float(row.get("keeper_score")),
        drop_candidate_score=_float(row.get("drop_candidate_score")),
        trade_value=_float(row.get("trade_value"), _float(row.get("market_trade_value"))),
        confidence_score=_float(row.get("confidence_score")),
        lve_format_fit=_float(row.get("lve_format_fit"), _float(row.get("private_score"))),
        warning_status=str(row.get("warning_status") or ""),
        warning_reasons=_split_codes(row.get("warning_reasons")),
        risk_flags=_split_codes(row.get("risk_flags")),
        upside_flags=_split_codes(row.get("upside_flags")),
        floor_flags=_split_codes(row.get("floor_flags")),
    )


def _option_row(
    score: VeteranScore | ComparablePlayerScore,
    output_row: dict[str, object],
    player_row: object | None = None,
) -> dict[str, object]:
    team = str(output_row.get("team") or getattr(player_row, "team_name", "") or "")
    label_parts = [score.player_name, score.position.value]
    if team:
        label_parts.append(team)
    return {
        "player_id": score.player_id,
        "player": score.player_name,
        "position": score.position.value,
        "team": team,
        "label": " | ".join(label_parts),
    }


def _player_summary(
    score: VeteranScore | ComparablePlayerScore,
    output_row: dict[str, object],
    player_row: object | None = None,
) -> dict[str, object]:
    return {
        "player_id": score.player_id,
        "player": score.player_name,
        "position": score.position.value,
        "team": output_row.get("team") or getattr(player_row, "team_name", ""),
        "war_score": _war_score(score, output_row),
        "keeper_score": score.keeper_score,
        "private_lve_value": score.veteran_base_value,
        "trade_value": score.trade_value,
        "drop_score": score.drop_candidate_score,
        "confidence": score.confidence_score,
        "warning_status": score.warning_status,
    }


def _score_rows(
    score_a: VeteranScore | ComparablePlayerScore,
    score_b: VeteranScore | ComparablePlayerScore,
    output_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    output_a = output_lookup.get(score_a.player_id, {})
    output_b = output_lookup.get(score_b.player_id, {})
    values_a = _score_metric_values(score_a, output_a)
    values_b = _score_metric_values(score_b, output_b)
    rows: list[dict[str, object]] = []
    for metric_key, label in SCORE_METRICS:
        a_value = values_a[metric_key]
        b_value = values_b[metric_key]
        gap = round(a_value - b_value, 2)
        rows.append(
            {
                "metric": label,
                "player_a": score_a.player_name,
                "a_value": a_value,
                "player_b": score_b.player_name,
                "b_value": b_value,
                "gap_a_minus_b": gap,
                "leader": _leader(score_a.player_name, score_b.player_name, gap),
            }
        )
    return rows


def _component_rows(
    summary_rows: list[dict[str, object]],
    score_a: VeteranScore | ComparablePlayerScore,
    score_b: VeteranScore | ComparablePlayerScore,
) -> list[dict[str, object]]:
    by_player_component = {
        (str(row["player_id"]), str(row["component"])): row for row in summary_rows
    }
    components = sorted(
        {
            component
            for player_id, component in by_player_component
            if player_id in {score_a.player_id, score_b.player_id}
        }
    )
    rows: list[dict[str, object]] = []
    for component in components:
        row_a = by_player_component.get((score_a.player_id, component), {})
        row_b = by_player_component.get((score_b.player_id, component), {})
        a_value = _float(row_a.get("component_score"))
        b_value = _float(row_b.get("component_score"))
        gap = round(a_value - b_value, 2)
        rows.append(
            {
                "component": component,
                "player_a": score_a.player_name,
                "a_component_score": a_value,
                "a_contribution_sum": _float(row_a.get("contribution_sum")),
                "player_b": score_b.player_name,
                "b_component_score": b_value,
                "b_contribution_sum": _float(row_b.get("contribution_sum")),
                "gap_a_minus_b": gap,
                "leader": _leader(score_a.player_name, score_b.player_name, gap),
            }
        )
    return rows


def _feature_comparison_rows(
    receipt_rows: list[dict[str, object]],
    score_a: VeteranScore | ComparablePlayerScore,
    score_b: VeteranScore | ComparablePlayerScore,
) -> list[dict[str, object]]:
    rows_a = [row for row in receipt_rows if row["player_id"] == score_a.player_id]
    rows_b = [row for row in receipt_rows if row["player_id"] == score_b.player_id]
    by_a = {
        (str(row["component"]), str(row["formula_feature_name"])): row for row in rows_a
    }
    by_b = {
        (str(row["component"]), str(row["formula_feature_name"])): row for row in rows_b
    }
    keys = sorted(set(by_a) | set(by_b))
    rows: list[dict[str, object]] = []
    for component, feature in keys:
        row_a = by_a.get((component, feature), {})
        row_b = by_b.get((component, feature), {})
        missing_a = not row_a
        missing_b = not row_b
        a_contribution = _float(row_a.get("contribution"))
        b_contribution = _float(row_b.get("contribution"))
        contribution_gap = round(a_contribution - b_contribution, 4)
        normalized_gap = round(
            _float(row_a.get("normalized_score")) - _float(row_b.get("normalized_score")),
            2,
        )
        rows.append(
            {
                "component": component,
                "formula_feature_name": feature,
                "source_feature_a": row_a.get("source_feature_name", ""),
                "source_feature_b": row_b.get("source_feature_name", ""),
                "player_a": score_a.player_name,
                "a_raw_value": row_a.get("raw_feature_value", ""),
                "a_normalized_score": row_a.get("normalized_score", ""),
                "a_weight": row_a.get("feature_weight", ""),
                "a_contribution": a_contribution,
                "a_imputed": missing_a or bool(row_a.get("imputed_flag", False)),
                "player_b": score_b.player_name,
                "b_raw_value": row_b.get("raw_feature_value", ""),
                "b_normalized_score": row_b.get("normalized_score", ""),
                "b_weight": row_b.get("feature_weight", ""),
                "b_contribution": b_contribution,
                "b_imputed": missing_b or bool(row_b.get("imputed_flag", False)),
                "normalized_gap_a_minus_b": normalized_gap,
                "contribution_gap_a_minus_b": contribution_gap,
                "gap_leader": _leader(score_a.player_name, score_b.player_name, contribution_gap),
                "gap_driver_strength": abs(contribution_gap),
                "warning_reason_a": (
                    "feature not present for this player's position/model path"
                    if missing_a
                    else row_a.get("warning_reason", "")
                ),
                "warning_reason_b": (
                    "feature not present for this player's position/model path"
                    if missing_b
                    else row_b.get("warning_reason", "")
                ),
            }
        )
    return rows


def _warning_rows(
    score_a: VeteranScore | ComparablePlayerScore,
    score_b: VeteranScore | ComparablePlayerScore,
) -> list[dict[str, object]]:
    return [
        {
            "player": score_a.player_name,
            "warning_summary": warning_summary(
                "|".join(score_a.warning_reasons),
                score_a.warning_status,
            ),
            "risk_notes": warning_summary("|".join(score_a.risk_flags), default=""),
            "upside_notes": warning_summary("|".join(score_a.upside_flags), default=""),
            "floor_notes": warning_summary("|".join(score_a.floor_flags), default=""),
        },
        {
            "player": score_b.player_name,
            "warning_summary": warning_summary(
                "|".join(score_b.warning_reasons),
                score_b.warning_status,
            ),
            "risk_notes": warning_summary("|".join(score_b.risk_flags), default=""),
            "upside_notes": warning_summary("|".join(score_b.upside_flags), default=""),
            "floor_notes": warning_summary("|".join(score_b.floor_flags), default=""),
        },
    ]


def _market_edge_rows(
    score_a: VeteranScore | ComparablePlayerScore,
    score_b: VeteranScore | ComparablePlayerScore,
    output_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for score in (score_a, score_b):
        output = output_lookup.get(score.player_id, {})
        trade_liquidity = _float(output.get("market_score"), score.trade_value)
        private_value = _float(output.get("private_score"), score.veteran_base_value)
        edge = round(private_value - trade_liquidity, 2)
        rows.append(
            {
                "player": score.player_name,
                "private_lve_value": private_value,
                "trade_liquidity": trade_liquidity,
                "private_minus_trade_liquidity": edge,
                "market_edge_label": _market_edge_label(edge),
                "confidence_score": score.confidence_score,
                "source_warning": warning_summary(
                    "|".join(score.warning_reasons),
                    score.warning_status,
                    default="No source warning.",
                ),
            }
        )
    return rows


def _score_metric_values(
    score: VeteranScore | ComparablePlayerScore,
    output_row: dict[str, object],
) -> dict[str, float]:
    return {
        "war_score": _war_score(score, output_row),
        "keeper_score": score.keeper_score,
        "veteran_base_value": score.veteran_base_value,
        "trade_value": score.trade_value,
        "drop_candidate_score": score.drop_candidate_score,
        "horizon_retention_score": score.horizon_retention_score,
        "lve_format_fit": score.lve_format_fit,
        "confidence_score": score.confidence_score,
    }


def _war_score(
    score: VeteranScore | ComparablePlayerScore,
    output_row: dict[str, object],
) -> float:
    if output_row.get("war_score") not in {None, ""}:
        return _float(output_row.get("war_score"))
    return round((0.70 * score.keeper_score) + (0.30 * score.trade_value), 2)


def _leader(player_a: str, player_b: str, gap: float) -> str:
    if gap > 0:
        return player_a
    if gap < 0:
        return player_b
    return "even"


def _market_edge_label(edge: float) -> str:
    return market_edge_label(edge)


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return round(float(text), 4)
    except (TypeError, ValueError):
        return default


def _split_codes(value: object) -> tuple[str, ...]:
    text = str(value or "")
    return tuple(part for part in text.split("|") if part)
