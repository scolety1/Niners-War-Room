from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from src.models.rookie_scores import (
    FEATURES_BY_POSITION,
    FINAL_WEIGHTS,
    MAIN_WEIGHTS,
    MODEL_VERSION,
    ModelMode,
    Position,
    RookieInput,
    RookieScore,
    feature_score,
    score_rookie,
)
from src.services.veteran_benchmark_service import (
    benchmark_rows,
    load_or_derive_veteran_benchmarks,
)

SOURCE_TABLES = (
    "rookie_prospect_inputs.csv",
    "rookie_feature_registry.csv",
    "rookie_normalization_rules.csv",
    "rookie_raw_metrics.csv",
    "veteran_opportunity_assets.csv",
    "veteran_opportunity_benchmarks.csv",
)
GENERATED_TABLES = ("rookie_feature_scores.csv", "rookie_model_outputs.csv")


@dataclass(frozen=True)
class RookieFeatureDefinition:
    feature_id: str
    position: Position
    feature_name: str
    parent_component: str
    default_weight: float
    min_weight: float
    max_weight: float
    evidence_strength: str
    is_core: bool
    is_display_only: bool
    post_draft_only: bool
    manual_entry_allowed: bool
    requires_source_type: str


@dataclass(frozen=True)
class VeteranBenchmark:
    benchmark_id: str
    position: Position
    benchmark_type: str
    benchmark_score: float
    source_snapshot_id: str
    source_date: str
    notes: str


@dataclass(frozen=True)
class RookieModelRun:
    model_version: str
    scores: tuple[RookieScore, ...]
    rookies: tuple[RookieInput, ...]
    registry: tuple[RookieFeatureDefinition, ...]
    benchmarks: tuple[VeteranBenchmark, ...]


def run_rookie_model_from_dir(data_dir: str | Path) -> RookieModelRun:
    root = Path(data_dir)
    registry = load_feature_registry(root / "rookie_feature_registry.csv")
    benchmarks = load_veteran_benchmarks_from_dir(root)
    validate_registry(registry)
    benchmark_by_position = {benchmark.position: benchmark for benchmark in benchmarks}
    rookies = load_rookie_inputs(
        root / "rookie_prospect_inputs.csv",
        benchmark_by_position,
    )
    scores = tuple(score_rookie(rookie) for rookie in rookies)
    return RookieModelRun(
        model_version=MODEL_VERSION,
        scores=tuple(sorted(scores, key=lambda item: (-item.final_decision_score, item.player_id))),
        rookies=rookies,
        registry=registry,
        benchmarks=benchmarks,
    )


def load_feature_registry(path: str | Path) -> tuple[RookieFeatureDefinition, ...]:
    rows = _read_csv(Path(path))
    return tuple(
        RookieFeatureDefinition(
            feature_id=row["feature_id"],
            position=Position(row["position"]),
            feature_name=row["feature_name"],
            parent_component=row["parent_component"],
            default_weight=_float(row["default_weight"]),
            min_weight=_float(row["min_weight"]),
            max_weight=_float(row["max_weight"]),
            evidence_strength=row["evidence_strength"],
            is_core=_bool(row["is_core"]),
            is_display_only=_bool(row["is_display_only"]),
            post_draft_only=_bool(row["post_draft_only"]),
            manual_entry_allowed=_bool(row["manual_entry_allowed"]),
            requires_source_type=row["requires_source_type"],
        )
        for row in rows
    )


def load_veteran_benchmarks(path: str | Path) -> tuple[VeteranBenchmark, ...]:
    rows = _read_csv(Path(path))
    return tuple(
        VeteranBenchmark(
            benchmark_id=row["benchmark_id"],
            position=Position(row["position"]),
            benchmark_type=row["benchmark_type"],
            benchmark_score=_float(row["benchmark_score"]),
            source_snapshot_id=row["source_snapshot_id"],
            source_date=row["source_date"],
            notes=row.get("notes", ""),
        )
        for row in rows
    )


def load_veteran_benchmarks_from_dir(data_dir: str | Path) -> tuple[VeteranBenchmark, ...]:
    root = Path(data_dir)
    derived = load_or_derive_veteran_benchmarks(root)
    if derived is not None:
        return tuple(
            VeteranBenchmark(
                benchmark_id=benchmark.benchmark_id,
                position=benchmark.position,
                benchmark_type=benchmark.benchmark_type,
                benchmark_score=benchmark.benchmark_score,
                source_snapshot_id=benchmark.source_snapshot_id,
                source_date=benchmark.source_date,
                notes=benchmark.notes,
            )
            for benchmark in derived
        )
    return load_veteran_benchmarks(root / "veteran_opportunity_benchmarks.csv")


def load_rookie_inputs(
    path: str | Path,
    benchmark_by_position: dict[Position, VeteranBenchmark],
) -> tuple[RookieInput, ...]:
    rows = _read_csv(Path(path))
    rookies: list[RookieInput] = []
    for row in rows:
        position = Position(row["position"])
        features = {
            feature_name: _optional_float(row.get(feature_name))
            for feature_name in FEATURES_BY_POSITION[position]
        }
        feature_sources = {
            feature_name: _feature_source_key(row, feature_name)
            for feature_name in FEATURES_BY_POSITION[position]
        }
        mode = ModelMode(row.get("model_mode") or ModelMode.PRE_DRAFT)
        benchmark = benchmark_by_position.get(position)
        rookies.append(
            RookieInput(
                player_id=row["player_id"],
                player_name=row["player_name"],
                position=position,
                class_year=int(row["class_year"]),
                model_mode=mode,
                source_snapshot_id=row["source_snapshot_id"],
                source_name=row["source_name"],
                source_date=row["source_date"],
                features=features,
                feature_sources=feature_sources,
                rookie_opportunity_score=_optional_float(row.get("rookie_opportunity_score")),
                veteran_benchmark_score=benchmark.benchmark_score if benchmark else 50.0,
            )
        )
    return tuple(rookies)


def validate_registry(registry: Iterable[RookieFeatureDefinition]) -> None:
    seen_feature_ids: set[str] = set()
    core_by_position_name: set[tuple[Position, str]] = set()
    for feature in registry:
        if feature.feature_id in seen_feature_ids:
            raise ValueError(f"Duplicate feature_id: {feature.feature_id}")
        seen_feature_ids.add(feature.feature_id)
        if not feature.min_weight <= feature.default_weight <= feature.max_weight:
            raise ValueError(f"Weight out of bounds for {feature.feature_id}")
        if feature.is_display_only and feature.default_weight != 0:
            raise ValueError(f"Display-only feature has live weight: {feature.feature_id}")
        if feature.is_core:
            key = (feature.position, feature.feature_name)
            if key in core_by_position_name:
                raise ValueError(f"Feature core-weighted more than once: {feature.feature_name}")
            core_by_position_name.add(key)
            if feature.parent_component != "main_prospect_score":
                raise ValueError(f"Core feature outside main component: {feature.feature_id}")


def generated_model_output_rows(scores: Iterable[RookieScore]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rank, score in enumerate(scores, start=1):
        row = asdict(score)
        row["board_rank"] = rank
        row["position"] = score.position.value
        row["risk_flags"] = "|".join(score.risk_flags)
        row["upside_flags"] = "|".join(score.upside_flags)
        row["floor_flags"] = "|".join(score.floor_flags)
        rows.append(row)
    return rows


def generated_audit_rows(run: RookieModelRun) -> list[dict[str, object]]:
    scores_by_player = {score.player_id: score for score in run.scores}
    registry_by_position_feature = {
        (feature.position, feature.feature_name): feature for feature in run.registry
    }
    rows: list[dict[str, object]] = []
    for rookie in run.rookies:
        score = scores_by_player[rookie.player_id]
        weights = MAIN_WEIGHTS[rookie.position]
        weight_total = sum(weights.values())
        for feature_name in FEATURES_BY_POSITION[rookie.position]:
            registry = registry_by_position_feature[(rookie.position, feature_name)]
            normalized = feature_score(rookie.features.get(feature_name))
            feature_weight = weights[feature_name]
            component_contribution = normalized * feature_weight / weight_total
            rows.append(
                {
                    "player_id": rookie.player_id,
                    "player_name": rookie.player_name,
                    "position": rookie.position.value,
                    "feature_id": registry.feature_id,
                    "feature_name": feature_name,
                    "parent_component": "main_prospect_score",
                    "normalized_score": normalized,
                    "feature_weight": feature_weight,
                    "component_contribution": round(component_contribution, 4),
                    "weighted_final_contribution": round(
                        component_contribution * FINAL_WEIGHTS["main_prospect_score"],
                        4,
                    ),
                    "is_missing": rookie.features.get(feature_name) is None,
                    "evidence_strength": registry.evidence_strength,
                    "source_snapshot_id": rookie.source_snapshot_id,
                    "source_key": (rookie.feature_sources or {}).get(feature_name, ""),
                    "score_component_value": score.main_prospect_score,
                }
            )
    return rows


def generated_veteran_benchmark_rows(data_dir: str | Path) -> list[dict[str, object]]:
    derived = load_or_derive_veteran_benchmarks(data_dir)
    if derived is not None:
        return benchmark_rows(derived)
    return [
        {
            "benchmark_id": benchmark.benchmark_id,
            "position": benchmark.position.value,
            "benchmark_type": benchmark.benchmark_type,
            "benchmark_score": benchmark.benchmark_score,
            "same_position_score": benchmark.benchmark_score,
            "flex_pool_score": "",
            "source_snapshot_id": benchmark.source_snapshot_id,
            "source_date": benchmark.source_date,
            "asset_count": "",
            "notes": benchmark.notes,
        }
        for benchmark in load_veteran_benchmarks(
            Path(data_dir) / "veteran_opportunity_benchmarks.csv"
        )
    ]


def write_generated_model_outputs(path: str | Path, scores: Iterable[RookieScore]) -> None:
    rows = generated_model_output_rows(scores)
    _write_csv(Path(path), rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return _float(value)


def _float(value: str | float | int) -> float:
    return float(value)


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() == "true"


def _feature_source_key(row: dict[str, str], feature_name: str) -> str:
    return (
        row.get(f"{feature_name}_source_key")
        or row.get("source_snapshot_id")
        or row.get("source_name")
        or ""
    )
