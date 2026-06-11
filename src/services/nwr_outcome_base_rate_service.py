from __future__ import annotations

import csv
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.services.nwr_outcome_scoring_service import (
    MODELED_POSITIONS,
    add_position_ranks,
    aggregate_season_scores,
    app_tier_labels,
    forbidden_input_violations,
    score_player_week,
)

SCOPE = "limited_truth_set_v0"
COMPONENT_WAIVER_ID = "truth_set_v0_component_waiver_v1"
SOURCE_MANIFEST_VERSION = "truth_set_v3_source_decisions_v1"
LABEL_SCHEMA_VERSION = "nwr_outcome_labels_v1"
SUPPORTED_BASE_RATE_ROW_FAMILIES = ("all_player_pre_week1", "offseason_carryover")
EXCLUDED_ROW_FAMILIES = ("rookie_post_draft",)
SUPPORTED_OUTCOMES = (
    "same_year_difference_maker",
    "same_year_starter",
    "same_year_useful",
    "same_year_replacement_or_bust",
    "next_year_starter",
)
CANONICAL_COMPONENTS = (
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_tds",
    "rushing_first_downs",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "receiving_first_downs",
    "fumbles_lost",
)
ZERO_WEIGHT_DEFAULT_COMPONENTS = ("passing_first_downs", "sacks_suffered", "misc_yards")
WAIVED_RARE_COMPONENTS = (
    "passing_2pt",
    "rushing_2pt",
    "receiving_2pt",
    "return_yards",
    "return_tds",
    "special_tds",
    "fumble_recovery_tds",
)


@dataclass(frozen=True)
class PlayerSeasonLabel:
    player_id: str
    player_name: str
    position: str
    season: int
    row_family: str
    forecast_origin: str
    cohort: str
    season_total_score: float
    qualified_ppg: float | None
    ppg_game_count: int
    is_difference_maker: bool
    is_starter: bool
    is_useful: bool
    is_replacement_or_bust: bool
    next_year_starter: bool | None
    prior_finish_tier: str
    trailing_ppg_tier: str
    games_played_tier: str
    age_band: str


@dataclass(frozen=True)
class BaseRateBucketResult:
    bucket_id: str
    parent_bucket_id: str
    position: str
    cohort: str
    row_family: str
    forecast_origin: str
    bucket_family: str
    primary_bucket: str
    secondary_bucket: str
    outcome_label: str
    training_window: str
    n_raw: int
    success_raw: int
    raw_rate: float | None
    parent_rate: float
    prior_alpha: float
    prior_beta: float
    posterior_mean: float
    ci80_low: float
    ci80_high: float
    ci95_low: float
    ci95_high: float
    reliability_flag: str
    component_waiver_id: str
    source_manifest_version: str
    label_schema_version: str
    scope: str


@dataclass(frozen=True)
class BaseRateBuildResult:
    bucket_results: tuple[BaseRateBucketResult, ...]
    parent_priors: tuple[dict[str, Any], ...]
    input_manifest: tuple[dict[str, Any], ...]
    censoring_report: tuple[dict[str, Any], ...]
    reliability_report: tuple[dict[str, Any], ...]
    leakage_guardrail_report: tuple[dict[str, Any], ...]


def build_limited_truth_set_base_rates(
    week_rows: Sequence[Mapping[str, Any]],
    *,
    row_families: Sequence[str] = SUPPORTED_BASE_RATE_ROW_FAMILIES,
    component_waiver_id: str = COMPONENT_WAIVER_ID,
    scope: str = SCOPE,
) -> BaseRateBuildResult:
    _validate_row_families(row_families)
    leakage_report = leakage_guardrail_report(week_rows)
    if any(row["status"] == "blocked" for row in leakage_report):
        raise ValueError("Forbidden fields detected in base-rate input.")

    scored_weeks = _score_week_rows(week_rows)
    season_labels = build_player_season_labels(scored_weeks, row_families=row_families)
    bucket_results = _build_bucket_results(
        season_labels,
        component_waiver_id=component_waiver_id,
        scope=scope,
    )
    return BaseRateBuildResult(
        bucket_results=tuple(bucket_results),
        parent_priors=tuple(_parent_prior_rows(bucket_results)),
        input_manifest=tuple(_input_manifest_rows(week_rows, season_labels, row_families)),
        censoring_report=tuple(_censoring_rows(season_labels)),
        reliability_report=tuple(_reliability_rows(bucket_results)),
        leakage_guardrail_report=tuple(leakage_report),
    )


def build_limited_truth_set_base_rates_from_csv(
    source_path: str | Path,
    *,
    row_families: Sequence[str] = SUPPORTED_BASE_RATE_ROW_FAMILIES,
) -> BaseRateBuildResult:
    rows = _read_csv_dicts(Path(source_path))
    return build_limited_truth_set_base_rates(rows, row_families=row_families)


def export_base_rate_build(
    result: BaseRateBuildResult,
    output_dir: str | Path,
) -> tuple[Path, ...]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = (
        output / "base_rate_bucket_results.csv",
        output / "base_rate_parent_priors.csv",
        output / "base_rate_input_manifest.csv",
        output / "base_rate_censoring_report.csv",
        output / "base_rate_reliability_report.csv",
        output / "base_rate_leakage_guardrail_report.csv",
    )
    _write_csv(paths[0], [asdict(row) for row in result.bucket_results])
    _write_csv(paths[1], list(result.parent_priors))
    _write_csv(paths[2], list(result.input_manifest))
    _write_csv(paths[3], list(result.censoring_report))
    _write_csv(paths[4], list(result.reliability_report))
    _write_csv(paths[5], list(result.leakage_guardrail_report))
    return paths


def build_player_season_labels(
    scored_week_rows: Sequence[Mapping[str, Any]],
    *,
    row_families: Sequence[str] = SUPPORTED_BASE_RATE_ROW_FAMILIES,
) -> tuple[PlayerSeasonLabel, ...]:
    ranked = _ranked_season_rows(scored_week_rows)
    by_player_season = {
        (str(row["player_id"]), int(row["season"])): row for row in ranked
    }
    latest_season = max((int(row["season"]) for row in ranked), default=0)
    labels: list[PlayerSeasonLabel] = []
    for row_family in row_families:
        for row in ranked:
            season = int(row["season"])
            player_id = str(row["player_id"])
            tiers = app_tier_labels(
                str(row["fantasy_position"]),
                total_rank=_optional_int(row.get("season_total_rank_pos")),
                qualified_ppg_rank=_optional_int(row.get("qualified_ppg_rank_pos")),
            )
            next_row = by_player_season.get((player_id, season + 1))
            next_year_starter = None
            if season + 1 <= latest_season and next_row is not None:
                next_tiers = app_tier_labels(
                    str(next_row["fantasy_position"]),
                    total_rank=_optional_int(next_row.get("season_total_rank_pos")),
                    qualified_ppg_rank=_optional_int(next_row.get("qualified_ppg_rank_pos")),
                )
                next_year_starter = next_tiers["is_starter"]
            elif season + 1 <= latest_season:
                next_year_starter = False

            prior = by_player_season.get((player_id, season - 1))
            labels.append(
                PlayerSeasonLabel(
                    player_id=player_id,
                    player_name=str(row["player_name"]),
                    position=str(row["fantasy_position"]),
                    season=season,
                    row_family=row_family,
                    forecast_origin=_forecast_origin(row_family),
                    cohort="truth_set_2022_2024",
                    season_total_score=float(row["season_total_score"]),
                    qualified_ppg=_optional_float(row.get("qualified_ppg")),
                    ppg_game_count=int(row.get("ppg_game_count") or 0),
                    is_difference_maker=tiers["is_difference_maker"],
                    is_starter=tiers["is_starter"],
                    is_useful=tiers["is_useful"],
                    is_replacement_or_bust=not tiers["is_useful"],
                    next_year_starter=next_year_starter,
                    prior_finish_tier=_prior_finish_tier(prior),
                    trailing_ppg_tier=_trailing_ppg_tier(prior),
                    games_played_tier=_games_played_tier(prior),
                    age_band="age_unavailable",
                )
            )
    return tuple(labels)


def leakage_guardrail_report(week_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    field_names: set[str] = set()
    for row in week_rows:
        field_names.update(str(field) for field in row.keys())
    violations = forbidden_input_violations(tuple(sorted(field_names)))
    fantasy_total_fields = tuple(
        sorted(
            field
            for field in field_names
            if field.lower() in {"fantasy_points", "fantasy_points_ppr", "fantasy_total"}
        )
    )
    return [
        {
            "guardrail": "forbidden_field_scan",
            "status": "blocked" if violations else "pass",
            "violation_count": len(violations),
            "details": "|".join(violations),
            "component_waiver_id": COMPONENT_WAIVER_ID,
            "scope": SCOPE,
        },
        {
            "guardrail": "imported_fantasy_totals_rejected",
            "status": "blocked" if fantasy_total_fields else "pass",
            "violation_count": len(fantasy_total_fields),
            "details": "|".join(fantasy_total_fields)
            or "Base-rate labels are reconstructed from raw components only.",
            "component_waiver_id": COMPONENT_WAIVER_ID,
            "scope": SCOPE,
        },
        {
            "guardrail": "rookie_post_draft_excluded",
            "status": "pass",
            "violation_count": 0,
            "details": "Historical draft-capital source registration remains incomplete.",
            "component_waiver_id": COMPONENT_WAIVER_ID,
            "scope": SCOPE,
        },
    ]


def _build_bucket_results(
    labels: Sequence[PlayerSeasonLabel],
    *,
    component_waiver_id: str,
    scope: str,
) -> list[BaseRateBucketResult]:
    bucket_inputs: list[tuple[str, str, str, str, list[PlayerSeasonLabel]]] = []
    for row_family in SUPPORTED_BASE_RATE_ROW_FAMILIES:
        family_labels = [row for row in labels if row.row_family == row_family]
        for position in sorted({row.position for row in family_labels}):
            position_labels = [row for row in family_labels if row.position == position]
            bucket_inputs.append(("position", position, "ALL", "ALL", position_labels))
            bucket_inputs.append(
                (
                    "position_cohort",
                    position,
                    "truth_set_2022_2024",
                    "ALL",
                    position_labels,
                )
            )
            for attr, bucket_family in (
                ("prior_finish_tier", "prior_finish_tier"),
                ("trailing_ppg_tier", "trailing_ppg_tier"),
                ("games_played_tier", "games_played_tier"),
                ("age_band", "age_band"),
            ):
                values = sorted({str(getattr(row, attr)) for row in position_labels})
                for value in values:
                    bucket_inputs.append(
                        (
                            bucket_family,
                            position,
                            value,
                            "ALL",
                            [row for row in position_labels if str(getattr(row, attr)) == value],
                        )
                    )

    global_rates = {
        outcome: _raw_rate([_outcome_value(row, outcome) for row in labels])
        for outcome in SUPPORTED_OUTCOMES
    }
    results: list[BaseRateBucketResult] = []
    for bucket_family, position, primary, secondary, rows in bucket_inputs:
        for outcome in SUPPORTED_OUTCOMES:
            values = [_outcome_value(row, outcome) for row in rows]
            observed = [value for value in values if value is not None]
            n_raw = len(observed)
            success_raw = sum(1 for value in observed if value)
            raw_rate = success_raw / n_raw if n_raw else None
            parent_rate = _parent_rate(
                labels,
                outcome=outcome,
                position=position,
                bucket_family=bucket_family,
                row_family=rows[0].row_family if rows else "unknown",
                global_rate=global_rates.get(outcome),
            )
            prior_alpha, prior_beta = _prior_from_parent(parent_rate)
            posterior = (success_raw + prior_alpha) / (n_raw + prior_alpha + prior_beta)
            ci80_low, ci80_high = _normal_beta_interval(
                posterior,
                n_raw + prior_alpha + prior_beta,
                z=1.2815515655446004,
            )
            ci95_low, ci95_high = _normal_beta_interval(
                posterior,
                n_raw + prior_alpha + prior_beta,
                z=1.959963984540054,
            )
            row_family = rows[0].row_family if rows else "unknown"
            bucket_id = _bucket_id(row_family, position, bucket_family, primary, secondary, outcome)
            results.append(
                BaseRateBucketResult(
                    bucket_id=bucket_id,
                    parent_bucket_id=_parent_bucket_id(
                        row_family,
                        position,
                        bucket_family,
                        outcome,
                    ),
                    position=position,
                    cohort="truth_set_2022_2024",
                    row_family=row_family,
                    forecast_origin=rows[0].forecast_origin if rows else "",
                    bucket_family=bucket_family,
                    primary_bucket=primary,
                    secondary_bucket=secondary,
                    outcome_label=outcome,
                    training_window=_training_window(labels),
                    n_raw=n_raw,
                    success_raw=success_raw,
                    raw_rate=round(raw_rate, 6) if raw_rate is not None else None,
                    parent_rate=round(parent_rate, 6),
                    prior_alpha=round(prior_alpha, 6),
                    prior_beta=round(prior_beta, 6),
                    posterior_mean=round(posterior, 6),
                    ci80_low=round(ci80_low, 6),
                    ci80_high=round(ci80_high, 6),
                    ci95_low=round(ci95_low, 6),
                    ci95_high=round(ci95_high, 6),
                    reliability_flag=_reliability_flag(n_raw, success_raw),
                    component_waiver_id=component_waiver_id,
                    source_manifest_version=SOURCE_MANIFEST_VERSION,
                    label_schema_version=LABEL_SCHEMA_VERSION,
                    scope=scope,
                )
            )
    return results


def _score_week_rows(week_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    scored_rows: list[dict[str, Any]] = []
    for row in week_rows:
        if str(row.get("position", "")).upper() not in MODELED_POSITIONS:
            continue
        scored = score_player_week(
            {
                **dict(row),
                "passing_first_downs": 0,
                "sacks_suffered": 0,
                "misc_yards": 0,
                "passing_2pt": 0,
                "rushing_2pt": 0,
                "receiving_2pt": 0,
                "return_yards": 0,
                "return_tds": 0,
                "special_tds": 0,
                "fumble_recovery_tds": 0,
            }
        )
        scored_rows.append(
            {
                **dict(row),
                **scored,
                "include_in_scoring": True,
                "ppg_game_eligible": True,
                "component_waiver_id": COMPONENT_WAIVER_ID,
                "scope": SCOPE,
            }
        )
    return scored_rows


def _ranked_season_rows(scored_week_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    season_rows = aggregate_season_scores(list(scored_week_rows))
    ranked_total = add_position_ranks(
        season_rows,
        value_column="season_total_score",
        rank_column="season_total_rank_pos",
    )
    return add_position_ranks(
        ranked_total,
        value_column="qualified_ppg",
        rank_column="qualified_ppg_rank_pos",
    )


def _outcome_value(row: PlayerSeasonLabel, outcome: str) -> bool | None:
    if outcome == "same_year_difference_maker":
        return row.is_difference_maker
    if outcome == "same_year_starter":
        return row.is_starter
    if outcome == "same_year_useful":
        return row.is_useful
    if outcome == "same_year_replacement_or_bust":
        return row.is_replacement_or_bust
    if outcome == "next_year_starter":
        return row.next_year_starter
    raise ValueError(f"Unsupported outcome label: {outcome}")


def _parent_rate(
    labels: Sequence[PlayerSeasonLabel],
    *,
    outcome: str,
    position: str,
    bucket_family: str,
    row_family: str,
    global_rate: float | None,
) -> float:
    if bucket_family != "position":
        position_rows = [
            row for row in labels if row.position == position and row.row_family == row_family
        ]
        position_rate = _raw_rate([_outcome_value(row, outcome) for row in position_rows])
        if position_rate is not None:
            return position_rate
    if global_rate is not None:
        return global_rate
    return 0.5


def _raw_rate(values: Sequence[bool | None]) -> float | None:
    observed = [value for value in values if value is not None]
    if not observed:
        return None
    return sum(1 for value in observed if value) / len(observed)


def _prior_from_parent(parent_rate: float, *, strength: float = 12.0) -> tuple[float, float]:
    parent_rate = min(max(parent_rate, 0.01), 0.99)
    return parent_rate * strength, (1 - parent_rate) * strength


def _normal_beta_interval(mean: float, total_strength: float, *, z: float) -> tuple[float, float]:
    variance = mean * (1 - mean) / max(total_strength + 1, 1)
    radius = z * math.sqrt(variance)
    return max(0.0, mean - radius), min(1.0, mean + radius)


def _reliability_flag(n_raw: int, event_count: int) -> str:
    if n_raw >= 100 and event_count >= 10:
        return "A"
    if n_raw >= 50 and event_count >= 5:
        return "B"
    if n_raw >= 25:
        return "C"
    if n_raw > 0:
        return "D"
    return "UNPUBLISHABLE"


def _parent_prior_rows(results: Sequence[BaseRateBucketResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for row in results:
        key = (row.parent_bucket_id, row.position, row.row_family, row.outcome_label, row.scope)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "parent_bucket_id": row.parent_bucket_id,
                "position": row.position,
                "row_family": row.row_family,
                "outcome_label": row.outcome_label,
                "parent_rate": row.parent_rate,
                "prior_alpha": row.prior_alpha,
                "prior_beta": row.prior_beta,
                "component_waiver_id": row.component_waiver_id,
                "source_manifest_version": row.source_manifest_version,
                "label_schema_version": row.label_schema_version,
                "scope": row.scope,
            }
        )
    return rows


def _input_manifest_rows(
    week_rows: Sequence[Mapping[str, Any]],
    labels: Sequence[PlayerSeasonLabel],
    row_families: Sequence[str],
) -> list[dict[str, Any]]:
    seasons = sorted({str(row.get("season")) for row in week_rows})
    source_dates = sorted(
        {str(row.get("source_date")) for row in week_rows if row.get("source_date")}
    )
    return [
        {
            "input_source": (
                "local_exports/truth_set_lab/v3/reports/"
                "truth_set_v3_production_player_week.csv"
            ),
            "source_classification": "production_candidate",
            "scope": SCOPE,
            "component_waiver_id": COMPONENT_WAIVER_ID,
            "source_manifest_version": SOURCE_MANIFEST_VERSION,
            "label_schema_version": LABEL_SCHEMA_VERSION,
            "row_count": len(week_rows),
            "player_season_label_count": len(labels),
            "row_families": "|".join(row_families),
            "excluded_row_families": "|".join(EXCLUDED_ROW_FAMILIES),
            "seasons": "|".join(seasons),
            "source_dates": "|".join(source_dates),
            "canonical_components": "|".join(CANONICAL_COMPONENTS),
            "zero_weight_default_components": "|".join(ZERO_WEIGHT_DEFAULT_COMPONENTS),
            "waived_rare_components": "|".join(WAIVED_RARE_COMPONENTS),
            "imported_fantasy_totals_used": "no",
        }
    ]


def _censoring_rows(labels: Sequence[PlayerSeasonLabel]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for outcome in SUPPORTED_OUTCOMES:
        values = [_outcome_value(row, outcome) for row in labels]
        censored = sum(1 for value in values if value is None)
        observed = len(values) - censored
        rows.append(
            {
                "outcome_label": outcome,
                "total_candidate_rows": len(values),
                "observed_rows": observed,
                "censored_or_null_rows": censored,
                "denominator_policy": "exclude_null_or_censored_labels",
                "component_waiver_id": COMPONENT_WAIVER_ID,
                "scope": SCOPE,
            }
        )
    return rows


def _reliability_rows(results: Sequence[BaseRateBucketResult]) -> list[dict[str, Any]]:
    counts = defaultdict(int)
    for row in results:
        counts[row.reliability_flag] += 1
    return [
        {
            "reliability_flag": flag,
            "bucket_count": count,
            "publish_policy": "internal_only_unpublished"
            if flag != "UNPUBLISHABLE"
            else "do_not_publish",
            "component_waiver_id": COMPONENT_WAIVER_ID,
            "scope": SCOPE,
        }
        for flag, count in sorted(counts.items())
    ]


def _validate_row_families(row_families: Sequence[str]) -> None:
    unsupported = [row for row in row_families if row not in SUPPORTED_BASE_RATE_ROW_FAMILIES]
    if unsupported:
        raise ValueError("Unsupported Sprint 4 row family: " + ", ".join(unsupported))


def _forecast_origin(row_family: str) -> str:
    if row_family == "all_player_pre_week1":
        return "pre_week1"
    if row_family == "offseason_carryover":
        return "offseason"
    return row_family


def _prior_finish_tier(prior: Mapping[str, Any] | None) -> str:
    if prior is None:
        return "no_prior"
    tiers = app_tier_labels(
        str(prior["fantasy_position"]),
        total_rank=_optional_int(prior.get("season_total_rank_pos")),
        qualified_ppg_rank=_optional_int(prior.get("qualified_ppg_rank_pos")),
    )
    if tiers["is_difference_maker"]:
        return "prior_difference_maker"
    if tiers["is_starter"]:
        return "prior_starter"
    if tiers["is_useful"]:
        return "prior_useful"
    return "prior_replacement_or_bust"


def _trailing_ppg_tier(prior: Mapping[str, Any] | None) -> str:
    if prior is None:
        return "no_prior"
    ppg = _optional_float(prior.get("qualified_ppg"))
    if ppg is None:
        return "prior_ppg_unqualified"
    if ppg >= 20:
        return "prior_ppg_20_plus"
    if ppg >= 15:
        return "prior_ppg_15_to_20"
    if ppg >= 10:
        return "prior_ppg_10_to_15"
    return "prior_ppg_under_10"


def _games_played_tier(prior: Mapping[str, Any] | None) -> str:
    if prior is None:
        return "no_prior"
    games = int(prior.get("ppg_game_count") or 0)
    if games >= 14:
        return "prior_games_14_plus"
    if games >= 8:
        return "prior_games_8_to_13"
    return "prior_games_under_8"


def _bucket_id(
    row_family: str,
    position: str,
    bucket_family: str,
    primary: str,
    secondary: str,
    outcome: str,
) -> str:
    return "|".join([row_family, position, bucket_family, primary, secondary, outcome])


def _parent_bucket_id(row_family: str, position: str, bucket_family: str, outcome: str) -> str:
    if bucket_family == "position":
        return "|".join(["global_offense_prior", outcome])
    return "|".join([row_family, position, "position", "ALL", "ALL", outcome])


def _training_window(labels: Sequence[PlayerSeasonLabel]) -> str:
    seasons = sorted({row.season for row in labels})
    if not seasons:
        return ""
    return f"{seasons[0]}-{seasons[-1]}"


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
