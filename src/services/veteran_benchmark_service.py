from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.models.rookie_scores import Position
from src.utils.scoring import clamp_score

ASSET_FILE = "veteran_opportunity_assets.csv"

POSITION_BENCHMARK_COUNTS = {
    Position.QB: 3,
    Position.RB: 6,
    Position.WR: 8,
    Position.TE: 3,
}
FLEX_POSITIONS = {Position.RB, Position.WR, Position.TE}
FLEX_COUNT = 10


@dataclass(frozen=True)
class VeteranAsset:
    asset_id: str
    asset_name: str
    asset_type: str
    position: Position
    availability_status: str
    role_tier: str
    lve_veteran_score: float
    win_now_score: float
    hold_value_score: float
    trade_liquidity_score: float
    source_snapshot_id: str
    source_date: str
    is_active_benchmark: bool
    notes: str


@dataclass(frozen=True)
class DerivedVeteranBenchmark:
    benchmark_id: str
    position: Position
    benchmark_type: str
    benchmark_score: float
    same_position_score: float
    flex_pool_score: float
    source_snapshot_id: str
    source_date: str
    asset_count: int
    notes: str


def load_veteran_assets(path: str | Path) -> tuple[VeteranAsset, ...]:
    rows = _read_csv(Path(path))
    return tuple(
        VeteranAsset(
            asset_id=row["asset_id"],
            asset_name=row["asset_name"],
            asset_type=row["asset_type"],
            position=Position(row["position"]),
            availability_status=row["availability_status"],
            role_tier=row["role_tier"],
            lve_veteran_score=_float(row["lve_veteran_score"]),
            win_now_score=_float(row["win_now_score"]),
            hold_value_score=_float(row["hold_value_score"]),
            trade_liquidity_score=_float(row["trade_liquidity_score"]),
            source_snapshot_id=row["source_snapshot_id"],
            source_date=row["source_date"],
            is_active_benchmark=_bool(row["is_active_benchmark"]),
            notes=row.get("notes", ""),
        )
        for row in rows
    )


def validate_veteran_assets(assets: tuple[VeteranAsset, ...]) -> None:
    seen_ids: set[str] = set()
    for asset in assets:
        if asset.asset_id in seen_ids:
            raise ValueError(f"Duplicate veteran asset_id: {asset.asset_id}")
        seen_ids.add(asset.asset_id)
        if asset.asset_type not in {"released_veteran", "free_agent", "benchmark_only"}:
            raise ValueError(f"Unsupported veteran asset_type: {asset.asset_id}")
        if asset.availability_status not in {
            "available",
            "possibly_available",
            "protected",
            "uncertain",
        }:
            raise ValueError(f"Unsupported veteran availability_status: {asset.asset_id}")
        for label, score in (
            ("lve_veteran_score", asset.lve_veteran_score),
            ("win_now_score", asset.win_now_score),
            ("hold_value_score", asset.hold_value_score),
            ("trade_liquidity_score", asset.trade_liquidity_score),
        ):
            if score != clamp_score(score):
                raise ValueError(f"{label} must be 0-100 for {asset.asset_id}")


def derive_veteran_benchmarks(
    assets: tuple[VeteranAsset, ...],
) -> tuple[DerivedVeteranBenchmark, ...]:
    validate_veteran_assets(assets)
    active_assets = tuple(
        asset
        for asset in assets
        if asset.is_active_benchmark
        and asset.availability_status in {"available", "possibly_available"}
    )
    flex_score = _pool_average(
        [
            asset.lve_veteran_score
            for asset in active_assets
            if asset.position in FLEX_POSITIONS
        ],
        FLEX_COUNT,
    )
    benchmarks: list[DerivedVeteranBenchmark] = []
    for position in Position:
        position_assets = [asset for asset in active_assets if asset.position == position]
        same_position_score = _pool_average(
            [asset.lve_veteran_score for asset in position_assets],
            POSITION_BENCHMARK_COUNTS[position],
        )
        benchmark_score = _blended_benchmark(position, same_position_score, flex_score)
        snapshot_ids = sorted({asset.source_snapshot_id for asset in position_assets})
        source_dates = sorted({asset.source_date for asset in position_assets})
        benchmarks.append(
            DerivedVeteranBenchmark(
                benchmark_id=f"{position.value.lower()}_actual_available_pool",
                position=position,
                benchmark_type="actual_available_pool",
                benchmark_score=benchmark_score,
                same_position_score=same_position_score,
                flex_pool_score=flex_score if position in FLEX_POSITIONS else 0.0,
                source_snapshot_id="|".join(snapshot_ids),
                source_date="|".join(source_dates),
                asset_count=len(position_assets),
                notes=(
                    "Derived from active released-veteran/free-agent assets. "
                    "Applied as external rookie opportunity-cost overlay."
                ),
            )
        )
    return tuple(benchmarks)


def load_or_derive_veteran_benchmarks(
    data_dir: str | Path,
) -> tuple[DerivedVeteranBenchmark, ...] | None:
    asset_path = Path(data_dir) / ASSET_FILE
    if not asset_path.exists():
        return None
    return derive_veteran_benchmarks(load_veteran_assets(asset_path))


def benchmark_rows(benchmarks: tuple[DerivedVeteranBenchmark, ...]) -> list[dict[str, object]]:
    return [
        {
            "benchmark_id": benchmark.benchmark_id,
            "position": benchmark.position.value,
            "benchmark_type": benchmark.benchmark_type,
            "benchmark_score": benchmark.benchmark_score,
            "same_position_score": benchmark.same_position_score,
            "flex_pool_score": benchmark.flex_pool_score,
            "source_snapshot_id": benchmark.source_snapshot_id,
            "source_date": benchmark.source_date,
            "asset_count": benchmark.asset_count,
            "notes": benchmark.notes,
        }
        for benchmark in benchmarks
    ]


def asset_rows(assets: tuple[VeteranAsset, ...]) -> list[dict[str, object]]:
    return [
        {
            "asset_id": asset.asset_id,
            "asset_name": asset.asset_name,
            "asset_type": asset.asset_type,
            "position": asset.position.value,
            "availability_status": asset.availability_status,
            "role_tier": asset.role_tier,
            "lve_veteran_score": asset.lve_veteran_score,
            "win_now_score": asset.win_now_score,
            "hold_value_score": asset.hold_value_score,
            "trade_liquidity_score": asset.trade_liquidity_score,
            "source_snapshot_id": asset.source_snapshot_id,
            "source_date": asset.source_date,
            "is_active_benchmark": asset.is_active_benchmark,
            "notes": asset.notes,
        }
        for asset in assets
    ]


def _pool_average(scores: list[float], count: int) -> float:
    if not scores:
        return 50.0
    sorted_scores = sorted(scores, reverse=True)
    pool = sorted_scores[:count]
    return round(sum(pool) / len(pool), 2)


def _blended_benchmark(
    position: Position,
    same_position_score: float,
    flex_pool_score: float,
) -> float:
    if position == Position.QB:
        return same_position_score
    if position == Position.TE:
        return round((same_position_score * 0.55) + (flex_pool_score * 0.45), 2)
    return round((same_position_score * 0.70) + (flex_pool_score * 0.30), 2)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(value: str | float | int) -> float:
    return float(value)


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() == "true"
