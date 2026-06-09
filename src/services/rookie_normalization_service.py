from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.models.rookie_scores import FEATURES_BY_POSITION, Position
from src.utils.scoring import clamp_score

RULE_FILE = "rookie_normalization_rules.csv"
RAW_METRICS_FILE = "rookie_raw_metrics.csv"
GENERATED_NORMALIZED_FILE = "rookie_prospect_inputs.csv"


@dataclass(frozen=True)
class NormalizationRule:
    rule_id: str
    position: Position
    feature_name: str
    raw_metric: str
    transform_type: str
    direction: str
    min_raw: float | None
    max_raw: float | None
    missing_policy: str
    source_snapshot_id: str
    notes: str


@dataclass(frozen=True)
class NormalizedFeature:
    player_id: str
    position: Position
    feature_name: str
    raw_metric: str
    raw_value: float | None
    normalized_score: float | None
    rule_id: str
    source_key: str


@dataclass(frozen=True)
class NormalizationResult:
    rows: tuple[dict[str, object], ...]
    features: tuple[NormalizedFeature, ...]


def load_normalization_rules(path: str | Path) -> tuple[NormalizationRule, ...]:
    rows = _read_csv(Path(path))
    return tuple(
        NormalizationRule(
            rule_id=row["rule_id"],
            position=Position(row["position"]),
            feature_name=row["feature_name"],
            raw_metric=row["raw_metric"],
            transform_type=row["transform_type"],
            direction=row["direction"],
            min_raw=_optional_float(row.get("min_raw")),
            max_raw=_optional_float(row.get("max_raw")),
            missing_policy=row["missing_policy"],
            source_snapshot_id=row["source_snapshot_id"],
            notes=row.get("notes", ""),
        )
        for row in rows
    )


def validate_normalization_rules(rules: tuple[NormalizationRule, ...]) -> None:
    seen_rule_ids: set[str] = set()
    seen_features: set[tuple[Position, str]] = set()
    for rule in rules:
        if rule.rule_id in seen_rule_ids:
            raise ValueError(f"Duplicate normalization rule_id: {rule.rule_id}")
        seen_rule_ids.add(rule.rule_id)
        key = (rule.position, rule.feature_name)
        if key in seen_features:
            raise ValueError(f"Duplicate normalization rule for feature: {rule.feature_name}")
        seen_features.add(key)
        if rule.feature_name not in FEATURES_BY_POSITION[rule.position]:
            raise ValueError(f"Rule targets unsupported V1 feature: {rule.rule_id}")
        if rule.transform_type not in {"linear", "draft_pick_curve"}:
            raise ValueError(f"Unsupported transform_type: {rule.transform_type}")
        if rule.direction not in {"higher_better", "lower_better", "younger_better"}:
            raise ValueError(f"Unsupported direction: {rule.direction}")
        if rule.transform_type == "linear":
            if rule.min_raw is None or rule.max_raw is None:
                raise ValueError(f"Linear rule needs min_raw and max_raw: {rule.rule_id}")
            if rule.min_raw >= rule.max_raw:
                raise ValueError(f"Linear rule min_raw must be below max_raw: {rule.rule_id}")


def normalize_raw_value(rule: NormalizationRule, raw_value: float | None) -> float | None:
    if raw_value is None:
        return None
    if rule.transform_type == "draft_pick_curve":
        return draft_pick_curve(raw_value)
    if rule.min_raw is None or rule.max_raw is None:
        raise ValueError(f"Rule missing linear bounds: {rule.rule_id}")
    if rule.direction == "higher_better":
        score = ((raw_value - rule.min_raw) / (rule.max_raw - rule.min_raw)) * 100
    else:
        score = ((rule.max_raw - raw_value) / (rule.max_raw - rule.min_raw)) * 100
    return round(clamp_score(score), 1)


def draft_pick_curve(overall_pick: float) -> float:
    pick = clamp_score(float(overall_pick), 1.0, 260.0)
    if pick <= 32:
        score = 100 - ((pick - 1) * (22 / 31))
    elif pick <= 100:
        score = 78 - ((pick - 32) * (28 / 68))
    else:
        score = 50 - ((pick - 100) * (45 / 160))
    return round(clamp_score(score), 1)


def normalize_rookie_raw_metrics(
    raw_metrics_csv: str | Path,
    rules_csv: str | Path,
) -> NormalizationResult:
    rules = load_normalization_rules(rules_csv)
    validate_normalization_rules(rules)
    rule_by_position_feature = {
        (rule.position, rule.feature_name): rule for rule in rules
    }
    rows = _read_csv(Path(raw_metrics_csv))
    normalized_rows: list[dict[str, object]] = []
    normalized_features: list[NormalizedFeature] = []
    for row in rows:
        position = Position(row["position"])
        output: dict[str, object] = {
            "player_id": row["player_id"],
            "player_name": row["player_name"],
            "position": row["position"],
            "class_year": row["class_year"],
            "model_mode": row["model_mode"],
            "source_snapshot_id": row["source_snapshot_id"],
            "source_name": row["source_name"],
            "source_date": row["source_date"],
            "data_completeness_status": row["data_completeness_status"],
        }
        for feature_name in FEATURES_BY_POSITION[position]:
            rule = rule_by_position_feature[(position, feature_name)]
            raw_value = _optional_float(row.get(rule.raw_metric))
            normalized = normalize_raw_value(rule, raw_value)
            output[feature_name] = "" if normalized is None else normalized
            output[f"{feature_name}_source_key"] = _source_key(row, rule)
            normalized_features.append(
                NormalizedFeature(
                    player_id=row["player_id"],
                    position=position,
                    feature_name=feature_name,
                    raw_metric=rule.raw_metric,
                    raw_value=raw_value,
                    normalized_score=normalized,
                    rule_id=rule.rule_id,
                    source_key=str(output[f"{feature_name}_source_key"]),
                )
            )
        output["rookie_opportunity_score"] = row.get("rookie_opportunity_score", "")
        normalized_rows.append(output)
    return NormalizationResult(
        rows=tuple(normalized_rows),
        features=tuple(normalized_features),
    )


def write_normalized_rookie_inputs(path: str | Path, rows: tuple[dict[str, object], ...]) -> None:
    _write_csv(Path(path), list(rows))


def _source_key(row: dict[str, str], rule: NormalizationRule) -> str:
    return "|".join(
        part
        for part in (
            row.get("source_snapshot_id", ""),
            rule.rule_id,
            rule.raw_metric,
        )
        if part
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
