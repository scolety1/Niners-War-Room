from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DEFAULT_HEURISTICS_DIR = (
    Path(__file__).resolve().parents[2] / "sample_data" / "asset_conversion"
)


@dataclass(frozen=True)
class PickBand:
    key: str
    min_value: float
    max_value: float
    label: str
    notes: str


@dataclass(frozen=True)
class PickHeuristics:
    year_discounts: dict[int, float]
    option_bonus_threshold: float
    strong_pick_optionality_bonus: float
    depth_pick_optionality_bonus: float
    pick_equivalent_bands: tuple[PickBand, ...]


@dataclass(frozen=True)
class StudTaxRate:
    key: str
    min_value: float
    max_value: float
    rate: float
    notes: str


@dataclass(frozen=True)
class PackageHeuristics:
    extra_roster_spot_cost: float
    consolidation_gap_rate: float
    consolidation_max: float
    stud_tax_extra_asset_cost: float
    stud_tax_rates: tuple[StudTaxRate, ...]


@dataclass(frozen=True)
class AssetHeuristics:
    picks: PickHeuristics
    packages: PackageHeuristics


def load_asset_heuristics(path: str | Path = DEFAULT_HEURISTICS_DIR) -> AssetHeuristics:
    root = Path(path)
    return AssetHeuristics(
        picks=load_pick_heuristics(root / "lve_pick_heuristics.csv"),
        packages=load_package_heuristics(root / "lve_package_heuristics.csv"),
    )


def load_pick_heuristics(path: str | Path) -> PickHeuristics:
    rows = _read_rows(path)
    year_discounts: dict[int, float] = {}
    strong_bonus: float | None = None
    depth_bonus: float | None = None
    option_threshold = 70.0
    bands: list[PickBand] = []

    for row_number, row in enumerate(rows, start=2):
        row_type = str(row.get("heuristic_type") or "")
        key = str(row.get("key") or "")
        if row_type == "year_discount":
            year_discounts[int(key)] = _required_float(row, "value", row_number)
        elif row_type == "optionality_bonus":
            if key == "strong_pick":
                option_threshold = _optional_float(row.get("min_value"), option_threshold)
                strong_bonus = _required_float(row, "value", row_number)
            elif key == "depth_pick":
                depth_bonus = _required_float(row, "value", row_number)
        elif row_type == "pick_equivalent":
            bands.append(
                PickBand(
                    key=key,
                    min_value=_required_float(row, "min_value", row_number),
                    max_value=_required_float(row, "max_value", row_number),
                    label=str(row.get("label") or ""),
                    notes=str(row.get("notes") or ""),
                )
            )

    if not year_discounts:
        raise ValueError("Pick heuristics must define at least one year_discount row.")
    if strong_bonus is None or depth_bonus is None:
        raise ValueError("Pick heuristics must define strong_pick and depth_pick bonuses.")
    if not bands:
        raise ValueError("Pick heuristics must define pick_equivalent bands.")

    return PickHeuristics(
        year_discounts=year_discounts,
        option_bonus_threshold=option_threshold,
        strong_pick_optionality_bonus=strong_bonus,
        depth_pick_optionality_bonus=depth_bonus,
        pick_equivalent_bands=tuple(sorted(bands, key=lambda band: -band.min_value)),
    )


def load_package_heuristics(path: str | Path) -> PackageHeuristics:
    rows = _read_rows(path)
    knobs: dict[str, float] = {}
    tax_rates: list[StudTaxRate] = []
    for row_number, row in enumerate(rows, start=2):
        row_type = str(row.get("heuristic_type") or "")
        key = str(row.get("key") or "")
        if row_type == "package_knob":
            knobs[key] = _required_float(row, "value", row_number)
        elif row_type == "stud_tax_rate":
            tax_rates.append(
                StudTaxRate(
                    key=key,
                    min_value=_required_float(row, "min_value", row_number),
                    max_value=_required_float(row, "max_value", row_number),
                    rate=_required_float(row, "value", row_number),
                    notes=str(row.get("notes") or ""),
                )
            )

    required_knobs = {
        "extra_roster_spot_cost",
        "consolidation_gap_rate",
        "consolidation_max",
        "stud_tax_extra_asset_cost",
    }
    missing = required_knobs - set(knobs)
    if missing:
        raise ValueError(f"Missing package heuristic knobs: {', '.join(sorted(missing))}.")
    if not tax_rates:
        raise ValueError("Package heuristics must define stud_tax_rate rows.")

    return PackageHeuristics(
        extra_roster_spot_cost=knobs["extra_roster_spot_cost"],
        consolidation_gap_rate=knobs["consolidation_gap_rate"],
        consolidation_max=knobs["consolidation_max"],
        stud_tax_extra_asset_cost=knobs["stud_tax_extra_asset_cost"],
        stud_tax_rates=tuple(sorted(tax_rates, key=lambda rate: rate.min_value)),
    )


def pick_year_discount(pick_year: int, *, current_year: int = 2026) -> float:
    heuristics = load_asset_heuristics().picks
    year_offset = max(0, pick_year - current_year)
    return heuristics.year_discounts.get(
        year_offset,
        heuristics.year_discounts[max(heuristics.year_discounts)],
    )


def pick_optionality_bonus(current_pick_curve_value: float) -> float:
    heuristics = load_asset_heuristics().picks
    if current_pick_curve_value >= heuristics.option_bonus_threshold:
        return heuristics.strong_pick_optionality_bonus
    return heuristics.depth_pick_optionality_bonus


def pick_equivalent_label(value: float) -> str:
    heuristics = load_asset_heuristics().picks
    for band in heuristics.pick_equivalent_bands:
        if band.min_value <= value <= band.max_value:
            return band.label
    return "UDFA"


def stud_tax_rate(value: float) -> float:
    heuristics = load_asset_heuristics().packages
    for tax_rate in heuristics.stud_tax_rates:
        if tax_rate.min_value <= value <= tax_rate.max_value:
            return tax_rate.rate
    return 0.0


def stud_tax(value: float, *, extra_asset_count: int) -> float:
    heuristics = load_asset_heuristics().packages
    if extra_asset_count <= 0:
        return 0.0
    return round(
        (value * stud_tax_rate(value))
        + (extra_asset_count * heuristics.stud_tax_extra_asset_cost),
        2,
    )


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _required_float(row: dict[str, str], column: str, row_number: int) -> float:
    value = row.get(column)
    if value is None or value == "":
        raise ValueError(f"Row {row_number}: {column} is required.")
    return float(value)


def _optional_float(value: object, default: float) -> float:
    if value is None or value == "":
        return default
    return float(value)
