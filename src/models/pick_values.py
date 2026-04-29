from __future__ import annotations

import math
import re
from dataclasses import dataclass

PICK_LABEL_PATTERN = re.compile(
    r"^(?:(?P<year>\d{4})\s+)?(?P<round>[1-9]\d*)\.(?P<slot>\d{2})$"
)

BRIEF_PICK_VALUE_CURVE_1000: tuple[float, ...] = (
    1000.0,
    820.0,
    720.0,
    630.0,
    560.0,
    500.0,
    450.0,
    405.0,
    365.0,
    330.0,
    300.0,
    260.0,
    230.0,
    200.0,
    175.0,
    152.0,
    132.0,
    115.0,
    100.0,
    88.0,
    78.0,
    69.0,
    61.0,
    54.0,
    48.0,
    43.0,
    39.0,
    35.0,
    32.0,
    29.0,
    28.0,
    27.0,
    26.0,
    25.0,
    24.0,
    23.0,
    22.0,
    21.0,
    20.0,
    19.0,
    18.6,
    18.4,
    18.2,
    18.0,
    17.0,
    16.0,
    15.0,
    14.0,
    13.0,
    12.0,
)


@dataclass(frozen=True)
class PickValueConfig:
    teams_per_round: int = 10
    rounds: int = 5
    current_pick_year: int = 2026
    annual_future_discount: float = 0.80
    declaration_adjustment_default: float = 0.0
    certainty_adjustments: dict[str, float] | None = None
    pick_value_curve_1000: tuple[float, ...] = BRIEF_PICK_VALUE_CURVE_1000

    def __post_init__(self) -> None:
        if self.annual_future_discount < 0.80 or self.annual_future_discount > 0.82:
            raise ValueError("Annual future discount must be between 0.80 and 0.82.")
        expected_picks = self.teams_per_round * self.rounds
        if len(self.pick_value_curve_1000) != expected_picks:
            raise ValueError(
                f"Pick value curve must contain exactly {expected_picks} values."
            )

    def certainty_factor(self, certainty: str) -> float:
        adjustments = self.certainty_adjustments or {
            "known": 1.0,
            "projected": 0.9,
            "estimated": 0.8,
            "unknown": 0.7,
        }
        normalized = certainty.strip().lower()
        if normalized not in adjustments:
            raise ValueError(f"Unknown pick certainty: {certainty}")
        return adjustments[normalized]


@dataclass(frozen=True)
class PickValue:
    pick_year: int
    round: int
    slot: int
    overall_pick: int
    pick_label: str
    base_value_1000: float
    future_discount: float
    certainty_adjustment: float
    declaration_adjustment: float
    final_pick_value: float
    bucket: str


def overall_pick(
    draft_round: int, slot: int, teams_per_round: int = 10, rounds: int = 5
) -> int:
    if draft_round < 1 or draft_round > rounds:
        raise ValueError(f"Round must be between 1 and {rounds}.")
    if slot < 1 or slot > teams_per_round:
        raise ValueError(f"Slot must be between 1 and {teams_per_round}.")
    return (10 * (draft_round - 1)) + slot


def format_pick_label(pick_year: int, draft_round: int, slot: int) -> str:
    return f"{pick_year} {draft_round}.{slot:02d}"


def parse_pick_label(
    pick_label: str, default_pick_year: int | None = None
) -> tuple[int, int, int]:
    match = PICK_LABEL_PATTERN.match(pick_label.strip())
    if not match:
        raise ValueError(f"Invalid pick label: {pick_label}")

    year_text = match.group("year")
    if year_text is None and default_pick_year is None:
        raise ValueError("Pick label is missing a year and no default was provided.")

    pick_year = int(year_text) if year_text is not None else default_pick_year
    if pick_year is None:
        raise ValueError("Pick year is required.")
    return pick_year, int(match.group("round")), int(match.group("slot"))


def base_pick_value_1000(overall: int, config: PickValueConfig | None = None) -> float:
    cfg = config or PickValueConfig()
    max_pick = cfg.teams_per_round * cfg.rounds
    if overall < 1 or overall > max_pick:
        raise ValueError(f"Overall pick must be between 1 and {max_pick}.")

    return cfg.pick_value_curve_1000[overall - 1]


def future_discount(pick_year: int, config: PickValueConfig | None = None) -> float:
    cfg = config or PickValueConfig()
    years_out = pick_year - cfg.current_pick_year
    if years_out <= 0:
        return 1.0
    return cfg.annual_future_discount**years_out


def certainty_adjustment(
    certainty: str, config: PickValueConfig | None = None
) -> float:
    cfg = config or PickValueConfig()
    return cfg.certainty_factor(certainty)


def declaration_adjustment(config: PickValueConfig | None = None) -> float:
    cfg = config or PickValueConfig()
    return cfg.declaration_adjustment_default


def pick_value(
    pick_year: int,
    draft_round: int,
    slot: int,
    *,
    certainty: str = "known",
    config: PickValueConfig | None = None,
) -> PickValue:
    cfg = config or PickValueConfig()
    overall = overall_pick(draft_round, slot, cfg.teams_per_round, cfg.rounds)
    base_value = base_pick_value_1000(overall, cfg)
    discount = future_discount(pick_year, cfg)
    certainty_factor = certainty_adjustment(certainty, cfg)
    declaration = declaration_adjustment(cfg)
    final_value = (base_value * discount * certainty_factor) + declaration

    return PickValue(
        pick_year=pick_year,
        round=draft_round,
        slot=slot,
        overall_pick=overall,
        pick_label=format_pick_label(pick_year, draft_round, slot),
        base_value_1000=base_value,
        future_discount=discount,
        certainty_adjustment=certainty_factor,
        declaration_adjustment=declaration,
        final_pick_value=final_value,
        bucket=_pick_bucket(pick_year, draft_round, cfg),
    )


def pick_value_from_label(
    pick_label: str,
    *,
    certainty: str = "known",
    config: PickValueConfig | None = None,
) -> PickValue:
    cfg = config or PickValueConfig()
    pick_year, draft_round, slot = parse_pick_label(pick_label, cfg.current_pick_year)
    return pick_value(pick_year, draft_round, slot, certainty=certainty, config=cfg)


def trade_up_cost(
    target_pick_value: float,
    outgoing_pick_values: list[float] | tuple[float, ...],
) -> float:
    return target_pick_value - sum(outgoing_pick_values)


def trade_down_surplus(
    outgoing_pick_value: float,
    incoming_pick_values: list[float] | tuple[float, ...],
) -> float:
    return sum(incoming_pick_values) - outgoing_pick_value


def do_not_draft_before_pick(
    player_value_1000: float,
    *,
    pick_year: int | None = None,
    certainty: str = "known",
    config: PickValueConfig | None = None,
) -> str:
    cfg = config or PickValueConfig()
    resolved_pick_year = cfg.current_pick_year if pick_year is None else pick_year
    max_pick = cfg.teams_per_round * cfg.rounds

    for overall in range(1, max_pick + 1):
        draft_round = math.ceil(overall / cfg.teams_per_round)
        slot = overall - ((draft_round - 1) * cfg.teams_per_round)
        candidate = pick_value(
            resolved_pick_year, draft_round, slot, certainty=certainty, config=cfg
        )
        if candidate.final_pick_value <= player_value_1000:
            return candidate.pick_label

    final_pick_label = format_pick_label(
        resolved_pick_year, cfg.rounds, cfg.teams_per_round
    )
    return f"After {final_pick_label}"


def _pick_bucket(pick_year: int, draft_round: int, config: PickValueConfig) -> str:
    prefix = "future-" if pick_year > config.current_pick_year else ""
    return f"{prefix}round-{draft_round}"
