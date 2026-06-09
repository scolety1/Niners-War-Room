from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class AgeCurveProfile:
    age: float | None
    age_curve_score: float
    age_bucket: str
    age_warning: str
    age_interaction_flags: tuple[str, ...]
    source_status: str


def build_age_lookup(public_preview: str | Path) -> dict[tuple[str, str], float]:
    root = Path(public_preview)
    rows = [
        *_read_csv(root / "downloads" / "sleeper_players_nfl.csv"),
        *_read_csv(root / "downloads" / "nflverse_players.csv"),
    ]
    output: dict[tuple[str, str], float] = {}
    for row in rows:
        age = _float(row.get("age"), -1.0)
        if age < 0:
            age = age_from_birth_date(row.get("birth_date"))
        if age < 0:
            continue
        for key_name in ("sleeper_id", "player_id", "gsis_id"):
            key_value = str(row.get(key_name) or "")
            if key_value:
                output[(key_name, key_value.strip())] = age
    return output


def age_for_row(
    row: dict[str, object],
    age_lookup: dict[tuple[str, str], float],
) -> float | None:
    for key_name in ("sleeper_id", "player_id", "gsis_id"):
        key_value = str(row.get(key_name) or "").strip()
        if not key_value:
            continue
        age = age_lookup.get((key_name, key_value))
        if age is not None:
            return age
    return None


def age_curve_profile(
    position: str,
    age: float | None,
    *,
    role_score: float = 50.0,
    target_score: float = 50.0,
    workload_score: float = 50.0,
    injury_score: float = 75.0,
    rushing_profile_score: float = 50.0,
    route_score: float = 50.0,
) -> AgeCurveProfile:
    if age is None:
        return AgeCurveProfile(
            age=None,
            age_curve_score=50.0,
            age_bucket="age_not_available",
            age_warning="age_not_available",
            age_interaction_flags=(),
            source_status="neutral_imputation",
        )
    bucket = age_bucket(position, age)
    score = age_curve_score(position, age)
    warning = age_warning(bucket)
    flags = age_interaction_flags(
        position,
        bucket,
        role_score=role_score,
        target_score=target_score,
        workload_score=workload_score,
        injury_score=injury_score,
        rushing_profile_score=rushing_profile_score,
        route_score=route_score,
    )
    return AgeCurveProfile(
        age=round(age, 2),
        age_curve_score=round(score, 2),
        age_bucket=bucket,
        age_warning=warning,
        age_interaction_flags=flags,
        source_status="derived_real_data",
    )


def age_bucket(position: str, age: float) -> str:
    if position == "QB":
        if age <= 31:
            return "prime_window"
        if age <= 35:
            return "mild_decline"
        return "cliff_risk_window"
    if position == "RB":
        if age <= 25:
            return "prime_window"
        if age <= 27:
            return "mild_decline"
        return "cliff_risk_window"
    if position == "WR":
        if age <= 27:
            return "prime_window"
        if age <= 30:
            return "mild_decline"
        return "cliff_risk_window"
    if position == "TE":
        if age <= 29:
            return "prime_window"
        if age <= 32:
            return "mild_decline"
        return "cliff_risk_window"
    return "age_not_available"


def age_curve_score(position: str, age: float) -> float:
    if position == "QB":
        if age <= 23:
            return 82.0
        if age <= 31:
            return 92.0
        if age <= 35:
            return 82.0
        return max(52.0, 82.0 - ((age - 35.0) * 7.0))
    if position == "RB":
        if age <= 21:
            return 92.0
        if age <= 25:
            return 95.0
        if age <= 27:
            return 82.0
        return max(35.0, 82.0 - ((age - 27.0) * 12.0))
    if position == "WR":
        if age <= 22:
            return 90.0
        if age <= 27:
            return 94.0
        if age <= 30:
            return 82.0
        return max(45.0, 82.0 - ((age - 30.0) * 9.0))
    if age <= 23:
        return 86.0
    if age <= 29:
        return 92.0
    if age <= 32:
        return 78.0
    return max(42.0, 78.0 - ((age - 32.0) * 8.0))


def age_warning(bucket: str) -> str:
    if bucket == "age_not_available":
        return "age_not_available"
    if bucket == "cliff_risk_window":
        return "age_cliff_risk_window"
    if bucket == "mild_decline":
        return "age_mild_decline_window"
    return ""


def age_interaction_flags(
    position: str,
    bucket: str,
    *,
    role_score: float,
    target_score: float,
    workload_score: float,
    injury_score: float,
    rushing_profile_score: float,
    route_score: float,
) -> tuple[str, ...]:
    flags: list[str] = []
    if position == "RB" and bucket in {"mild_decline", "cliff_risk_window"}:
        if workload_score >= 70 or injury_score < 70:
            flags.append("rb_age_injury_workload_fragility")
    if position == "WR" and bucket in {"mild_decline", "cliff_risk_window"}:
        if target_score < 68 or route_score < 68:
            flags.append("wr_age_target_route_decline")
    if position == "QB" and bucket in {"mild_decline", "cliff_risk_window"}:
        if rushing_profile_score >= 70 or role_score < 70:
            flags.append("qb_rushing_age_or_start_security_decline")
    if position == "TE" and bucket in {"mild_decline", "cliff_risk_window"}:
        if route_score < 72 or target_score < 70:
            flags.append("te_late_prime_no_premium_route_dependency")
    return tuple(flags)


def age_from_birth_date(value: object) -> float:
    try:
        born = date.fromisoformat(str(value)[:10])
    except ValueError:
        return -1.0
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default
