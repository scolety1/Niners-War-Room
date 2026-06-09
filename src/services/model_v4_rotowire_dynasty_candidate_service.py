from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from src.services.age_curve_service import age_curve_profile
from src.services.model_v4_fantasypros_identity_mapping_service import normalize_player_name

DEFAULT_TRUTH_SET = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
DEFAULT_STATS_FIRST = Path(
    "local_exports/model_v4/rotowire_stats_first/latest/rotowire_stats_first_value_rows.csv"
)
DEFAULT_STATS_COMPONENTS = Path(
    "local_exports/model_v4/rotowire_stats_first/latest/rotowire_stats_first_component_rows.csv"
)
DEFAULT_STATS_WARNINGS = Path(
    "local_exports/model_v4/rotowire_stats_first/latest/rotowire_stats_first_warning_rows.csv"
)
DEFAULT_VORP = Path(
    "local_exports/model_v4/rotowire_vorp_review/latest/rotowire_vorp_review_rows.csv"
)
DEFAULT_ROTOWIRE_AGE = Path(
    "local_exports/model_v4/raw_user_exports/rotowire_manual/2026/rankings_context/"
    "rotowire_dynasty_cheatsheet_overall.csv"
)
DEFAULT_SLEEPER_AGE = Path(
    "local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/"
    "draft_pool_downloads/sleeper_players_nfl.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_dynasty_candidate/latest")

DYNASTY_CANDIDATE_VERSION = "model_v4_rotowire_dynasty_candidate_0.1.0"

POSITION_WEIGHTS = {
    "RB": {
        "stats_first_evidence": 0.2632,
        "replacement_vorp": 0.2632,
        "role_volume": 0.2105,
        "route_target_role": 0.0842,
        "age_lifecycle": 0.1789,
    },
    "WR": {
        "stats_first_evidence": 0.2316,
        "replacement_vorp": 0.1895,
        "role_volume": 0.1579,
        "route_target_role": 0.2632,
        "age_lifecycle": 0.1578,
    },
    "QB": {
        "stats_first_evidence": 0.2222,
        "replacement_vorp": 0.3889,
        "role_volume": 0.2778,
        "age_lifecycle": 0.1111,
    },
    "TE": {
        "stats_first_evidence": 0.2316,
        "replacement_vorp": 0.2105,
        "role_volume": 0.1579,
        "route_target_role": 0.2632,
        "age_lifecycle": 0.1368,
    },
}

POSITION_FORMAT_MULTIPLIERS = {
    "RB": 1.00,
    "WR": 1.00,
    "QB": 0.78,
    "TE": 0.72,
}

CONFIDENCE_SCORES = {
    "strong": 100.0,
    "moderate": 78.0,
    "moderate_review": 60.0,
    "review": 55.0,
    "weak_review": 35.0,
}

CONFIDENCE_CAPS = {
    "strong": 100.0,
    "moderate": 78.0,
    "moderate_review": 60.0,
    "review": 55.0,
    "weak_review": 40.0,
}

CANDIDATE_HEADER = (
    "overall_candidate_rank",
    "position_candidate_rank",
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "lifecycle_expected",
    "dynasty_candidate_value",
    "pre_cap_candidate_value",
    "position_format_multiplier",
    "confidence_label",
    "confidence_cap_applied",
    "stats_first_value",
    "production_vorp_points",
    "age",
    "age_bucket",
    "age_source_status",
    "age_value_cap",
    "age_value_cap_applied",
    "review_warnings",
    "unavailable_sections",
    "projections_used_for_core_value",
    "market_used_for_private_value",
    "league_rank_used_for_private_value",
    "allowed_use",
    "candidate_version",
)

COMPONENT_HEADER = (
    "player_name",
    "position",
    "component",
    "raw_value",
    "normalized_score",
    "component_weight",
    "contribution",
    "source_status",
    "allowed_use",
    "warning",
    "candidate_version",
)

RECEIPT_HEADER = (
    "player_name",
    "position",
    "component",
    "raw_fields_json",
    "normalized_score",
    "component_weight",
    "contribution",
    "source_status",
    "allowed_use",
    "warning",
    "receipt_note",
    "candidate_version",
)

WARNING_HEADER = (
    "player_name",
    "position",
    "warning_type",
    "severity",
    "detail",
    "candidate_version",
)

SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class RotoWireDynastyCandidateResult:
    candidate_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rotowire_dynasty_candidate_layer(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET,
    stats_first_path: str | Path = DEFAULT_STATS_FIRST,
    stats_components_path: str | Path = DEFAULT_STATS_COMPONENTS,
    stats_warnings_path: str | Path = DEFAULT_STATS_WARNINGS,
    vorp_path: str | Path = DEFAULT_VORP,
    rotowire_age_path: str | Path = DEFAULT_ROTOWIRE_AGE,
    sleeper_age_path: str | Path = DEFAULT_SLEEPER_AGE,
) -> RotoWireDynastyCandidateResult:
    truth_rows = _read_rows(Path(truth_set_path))
    stats_rows = _by_player(_read_rows(Path(stats_first_path)))
    component_rows = _components_by_player(_read_rows(Path(stats_components_path)))
    stats_warnings = _warnings_by_player(_read_rows(Path(stats_warnings_path)))
    vorp_rows = _by_player(_read_rows(Path(vorp_path)))
    age_lookup = {
        **_sleeper_age_lookup(Path(sleeper_age_path)),
        **_rotowire_age_lookup(Path(rotowire_age_path)),
    }
    vorp_scores = _vorp_percentiles(vorp_rows.values())

    candidates: list[dict[str, object]] = []
    components: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []

    for truth in truth_rows:
        built = _build_player_candidate(
            truth,
            stats_rows.get(normalize_player_name(truth["player_name"]), {}),
            component_rows.get(normalize_player_name(truth["player_name"]), []),
            stats_warnings.get(normalize_player_name(truth["player_name"]), []),
            vorp_rows.get(normalize_player_name(truth["player_name"]), {}),
            vorp_scores.get(normalize_player_name(truth["player_name"])),
            age_lookup.get(normalize_player_name(truth["player_name"])),
        )
        candidates.append(built["candidate"])
        components.extend(built["components"])
        receipts.extend(built["receipts"])
        warnings.extend(built["warnings"])

    _rank_candidates(candidates)
    summary = {
        "candidate_version": DYNASTY_CANDIDATE_VERSION,
        "review_status": "review_only",
        "candidate_row_count": len(candidates),
        "component_row_count": len(components),
        "receipt_row_count": len(receipts),
        "warning_row_count": len(warnings),
        "strong_confidence_count": sum(
            1 for row in candidates if row["confidence_label"] == "strong"
        ),
        "capped_player_count": sum(
            1 for row in candidates if str(row["confidence_cap_applied"]).lower() == "true"
        ),
        "projection_rows_used_for_core_value": 0,
        "market_value_used_for_private_value": False,
        "league_rank_used_for_private_value": False,
        "first_down_replacement_status": "estimated_from_history_review_only",
        "active_rankings_overwritten": False,
        "readiness_gate_unlocked": False,
    }
    return RotoWireDynastyCandidateResult(
        candidate_rows=tuple(candidates),
        component_rows=tuple(components),
        receipt_rows=tuple(receipts),
        warning_rows=tuple(warnings),
        summary=summary,
    )


def write_rotowire_dynasty_candidate_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWireDynastyCandidateResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_dynasty_candidate_layer()
    candidate_path = output / "rotowire_dynasty_candidate_rows.csv"
    component_path = output / "rotowire_dynasty_candidate_component_rows.csv"
    receipt_path = output / "rotowire_dynasty_candidate_receipt_rows.csv"
    warning_path = output / "rotowire_dynasty_candidate_warning_rows.csv"
    summary_path = output / "rotowire_dynasty_candidate_summary.csv"
    _write_csv(candidate_path, CANDIDATE_HEADER, result.candidate_rows)
    _write_csv(component_path, COMPONENT_HEADER, result.component_rows)
    _write_csv(receipt_path, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(warning_path, WARNING_HEADER, result.warning_rows)
    _write_csv(
        summary_path,
        SUMMARY_HEADER,
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {
        "candidates": candidate_path,
        "components": component_path,
        "receipts": receipt_path,
        "warnings": warning_path,
        "summary": summary_path,
    }


def _build_player_candidate(
    truth: dict[str, str],
    stats_row: dict[str, str],
    stats_components: list[dict[str, str]],
    stats_warnings: list[dict[str, str]],
    vorp_row: dict[str, str],
    vorp_score: float | None,
    age: float | None,
) -> dict[str, list[dict[str, object]] | dict[str, object]]:
    player = truth["player_name"]
    position = truth["position"]
    lifecycle = truth.get("lifecycle_expected", "")
    weights = POSITION_WEIGHTS[position]
    stats_component_lookup = {row["component"]: row for row in stats_components}
    warning_rows: list[dict[str, object]] = []

    stats_value = _float(stats_row.get("stats_first_value"))
    confidence_label = stats_row.get("confidence_label") or "weak_review"
    if not stats_row:
        confidence_label = "weak_review"
    confidence_score = CONFIDENCE_SCORES.get(confidence_label, 35.0)

    route_score = _component_score(stats_component_lookup, "route_receiving_role")
    route_warning = _component_warning(stats_component_lookup, "route_receiving_role")
    role_score = _mean_present(
        (
            _component_score(stats_component_lookup, "opportunity_volume"),
            _component_score(stats_component_lookup, "red_zone_role"),
            _component_score(stats_component_lookup, "snap_role"),
        )
    )
    route_target_score = route_score if route_score is not None else 50.0
    route_source_status = "not_applicable" if position == "QB" else _component_source_status(
        stats_component_lookup,
        "route_receiving_role",
    )
    route_allowed_use = (
        "not_applicable" if position == "QB" else "scoring_allowed_with_confidence_penalty"
    )

    age_profile = age_curve_profile(
        position,
        age,
        role_score=role_score or 50.0,
        target_score=route_target_score,
        workload_score=role_score or 50.0,
        route_score=route_target_score,
    )
    age_score = age_profile.age_curve_score
    age_warning = age_profile.age_warning

    if age is None:
        age_score = _lifecycle_age_proxy_score(position, lifecycle)
        age_warning = "age_not_available_lifecycle_proxy_used"

    if route_warning and position != "QB":
        warning_rows.append(
            _warning(
                truth,
                route_warning,
                "review",
                "Route/target role evidence missing.",
            )
        )
    if age_warning:
        warning_rows.append(
            _warning(truth, age_warning, "review", "Age/lifecycle risk affects confidence.")
        )
    for source_warning in stats_warnings:
        warning_rows.append(
            _warning(
                truth,
                source_warning.get("warning_type", "stats_first_warning"),
                source_warning.get("severity", "review"),
                source_warning.get("detail", ""),
            )
        )
    if vorp_row.get("warning"):
        warning_rows.append(
            _warning(
                truth,
                vorp_row["warning"],
                "review",
                (
                    "VORP uses first-down estimates from historical rates where direct "
                    "current first-down fields are unavailable; review-only until audited."
                ),
            )
        )

    component_specs = [
        (
            "stats_first_evidence",
            stats_value,
            stats_value if stats_row else None,
            "derived_real_data" if stats_row else "missing",
            "scoring_allowed_with_confidence_penalty",
            "",
            {
                "stats_first_value": stats_value,
                "source_version": stats_row.get("value_version", ""),
            },
            (
                "Historical RotoWire stats-first value. Projections, market, ADP, and "
                "league rank are excluded."
            ),
        ),
        (
            "replacement_vorp",
            vorp_row.get("production_vorp_points", ""),
            vorp_score,
            _vorp_source_status(vorp_row),
            "review_only",
            vorp_row.get("warning", "missing_replacement_vorp"),
            {
                "production_vorp_points": vorp_row.get("production_vorp_points", ""),
                "pre_first_down_vorp_points": vorp_row.get("pre_first_down_vorp_points", ""),
                "estimated_first_down_points": vorp_row.get("estimated_first_down_points", ""),
                "first_down_adjusted_points": vorp_row.get("first_down_adjusted_points", ""),
                "first_down_source_status": vorp_row.get("first_down_source_status", ""),
                "replacement_player": vorp_row.get("replacement_player", ""),
                "replacement_lve_base_points": vorp_row.get("replacement_lve_base_points", ""),
                "replacement_first_down_adjusted_points": vorp_row.get(
                    "replacement_first_down_adjusted_points",
                    "",
                ),
            },
            (
                "Position replacement/VORP review. It includes first-down-adjusted "
                "points using historical first-down estimates when current direct "
                "first-down fields are unavailable, and remains review-only until audited."
            ),
        ),
        (
            "role_volume",
            role_score,
            role_score,
            "derived_real_data" if role_score is not None else "missing",
            "scoring_allowed_with_confidence_penalty",
            "" if role_score is not None else "missing_role_volume",
            {
                "opportunity_volume": _component_score(
                    stats_component_lookup,
                    "opportunity_volume",
                ),
                "red_zone_role": _component_score(stats_component_lookup, "red_zone_role"),
                "snap_role": _component_score(stats_component_lookup, "snap_role"),
            },
            (
                "Opportunity, red-zone, and snap evidence. Snap is role proxy only, not "
                "route participation."
            ),
        ),
        (
            "route_target_role",
            route_score if route_score is not None else "",
            route_score if route_score is not None or position == "QB" else None,
            route_source_status,
            route_allowed_use,
            route_warning if position != "QB" else "not_applicable_for_qb",
            {"route_receiving_role": route_score},
            (
                "Licensed local RotoWire route/target evidence where available. Missing "
                "route data does not become average evidence."
            ),
        ),
        (
            "age_lifecycle",
            age if age is not None else lifecycle,
            age_score,
            age_profile.source_status if age is not None else "lifecycle_proxy_not_bio",
            "scoring_allowed_with_confidence_penalty",
            age_warning,
            {
                "age": age,
                "age_bucket": age_profile.age_bucket,
                "lifecycle_expected": lifecycle,
            },
            (
                "Age curve is sourced from local bio/age when available; lifecycle proxy "
                "is labeled when bio age is missing."
            ),
        ),
        (
            "evidence_confidence",
            confidence_label,
            confidence_score,
            "derived_coverage_label",
            "confidence_only",
            "",
            {"stats_first_confidence_label": confidence_label},
            "Confidence affects caps and uncertainty; it is not a hidden production boost.",
        ),
    ]

    components: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    pre_multiplier = 0.0
    for (
        name,
        raw_value,
        normalized_score,
        source_status,
        allowed_use,
        warning,
        raw_fields,
        note,
    ) in component_specs:
        weight = weights.get(name, 0.0)
        is_missing_evidence = source_status == "missing" or normalized_score is None
        score = _optional_float(normalized_score)
        contribution = 0.0 if is_missing_evidence or score is None else score * weight
        displayed_score: object = "" if is_missing_evidence or score is None else round(score, 4)
        displayed_contribution: object = "" if is_missing_evidence else round(contribution, 4)
        components.append(
            {
                "player_name": player,
                "position": position,
                "component": name,
                "raw_value": raw_value,
                "normalized_score": displayed_score,
                "component_weight": weight,
                "contribution": displayed_contribution,
                "source_status": source_status,
                "allowed_use": allowed_use,
                "warning": warning,
                "candidate_version": DYNASTY_CANDIDATE_VERSION,
            }
        )
        receipts.append(
            {
                "player_name": player,
                "position": position,
                "component": name,
                "raw_fields_json": json.dumps(raw_fields, sort_keys=True),
                "normalized_score": displayed_score,
                "component_weight": weight,
                "contribution": displayed_contribution,
                "source_status": source_status,
                "allowed_use": allowed_use,
                "warning": warning,
                "receipt_note": note,
                "candidate_version": DYNASTY_CANDIDATE_VERSION,
            }
        )
        if not is_missing_evidence:
            pre_multiplier += contribution

    multiplier = POSITION_FORMAT_MULTIPLIERS.get(position, 1.0)
    pre_cap = pre_multiplier * multiplier
    confidence_cap = _confidence_cap(confidence_label, stats_row, stats_components)
    age_value_cap = _age_value_cap(position, age)
    cap = min(confidence_cap, age_value_cap)
    capped = min(pre_cap, cap)
    cap_applied = cap < 100.0
    age_cap_applied = age_value_cap < 100.0
    if cap_applied:
        warning_rows.append(
            _warning(
                truth,
                "confidence_cap_applied",
                "review",
                (
                    f"Candidate value capped at {cap} from confidence/age policy; "
                    f"confidence is {confidence_label}."
                ),
            )
        )
    if age_cap_applied:
        warning_rows.append(
            _warning(
                truth,
                "age_value_cap_applied",
                "review",
                f"{position} age curve cap is {age_value_cap}.",
            )
        )

    unavailable = _unavailable_sections(stats_components, position, age)
    candidate = {
        "overall_candidate_rank": "",
        "position_candidate_rank": "",
        "player_name": player,
        "normalized_player_name": normalize_player_name(player),
        "position": position,
        "nfl_team": truth.get("nfl_team", ""),
        "lifecycle_expected": lifecycle,
        "dynasty_candidate_value": round(capped, 4),
        "pre_cap_candidate_value": round(pre_cap, 4),
        "position_format_multiplier": multiplier,
        "confidence_label": confidence_label,
        "confidence_cap_applied": cap_applied,
        "stats_first_value": stats_value if stats_row else "",
        "production_vorp_points": vorp_row.get("production_vorp_points", ""),
        "age": "" if age is None else age,
        "age_bucket": age_profile.age_bucket if age is not None else "age_not_available",
        "age_source_status": (
            age_profile.source_status if age is not None else "lifecycle_proxy_not_bio"
        ),
        "age_value_cap": age_value_cap,
        "age_value_cap_applied": age_cap_applied,
        "review_warnings": "|".join(sorted({str(row["warning_type"]) for row in warning_rows})),
        "unavailable_sections": "|".join(unavailable),
        "projections_used_for_core_value": False,
        "market_used_for_private_value": False,
        "league_rank_used_for_private_value": False,
        "allowed_use": "review_only",
        "candidate_version": DYNASTY_CANDIDATE_VERSION,
    }
    return {
        "candidate": candidate,
        "components": components,
        "receipts": receipts,
        "warnings": warning_rows,
    }


def _confidence_cap(
    confidence_label: str,
    stats_row: dict[str, str],
    stats_components: list[dict[str, str]],
) -> float:
    if not stats_row:
        return 35.0
    missing_components = sum(
        1 for component in stats_components if component.get("source_status") == "missing"
    )
    if missing_components >= 3:
        return 45.0
    return CONFIDENCE_CAPS.get(confidence_label, 50.0)


def _age_value_cap(position: str, age: float | None) -> float:
    if age is None:
        return 100.0
    if position == "RB":
        if age >= 30:
            return 58.0
        if age >= 28:
            return 65.0
        if age >= 27:
            return 72.0
    if position == "WR":
        if age >= 32:
            return 58.0
        if age >= 30:
            return 72.0
    if position == "TE":
        if age >= 33:
            return 45.0
        if age >= 30:
            return 60.0
    if position == "QB":
        if age >= 36:
            return 62.0
        if age >= 33:
            return 78.0
    return 100.0


def _lifecycle_age_proxy_score(position: str, lifecycle: str) -> float:
    if "year_one" in lifecycle:
        return 78.0
    if "year_two" in lifecycle:
        return 86.0
    if "year_three" in lifecycle:
        return 88.0
    if "aging" in lifecycle:
        return 48.0
    if position == "QB":
        return 82.0
    return 72.0


def _unavailable_sections(
    stats_components: list[dict[str, str]],
    position: str,
    age: float | None,
) -> tuple[str, ...]:
    unavailable: list[str] = []
    for component in stats_components:
        if component.get("source_status") == "missing":
            unavailable.append(component.get("component", "missing_component"))
    if position == "QB":
        unavailable = [
            item for item in unavailable if item not in {"snap_role", "route_receiving_role"}
        ]
    if age is None:
        unavailable.append("direct_age_bio")
    return tuple(sorted(set(unavailable)))


def _component_score(
    component_lookup: dict[str, dict[str, str]],
    component: str,
) -> float | None:
    row = component_lookup.get(component)
    if not row or row.get("source_status") in {"missing", "not_applicable"}:
        return None
    return _float(row.get("normalized_score"))


def _component_warning(
    component_lookup: dict[str, dict[str, str]],
    component: str,
) -> str:
    row = component_lookup.get(component)
    if not row:
        return "missing_component_evidence"
    return row.get("warning", "")


def _component_source_status(
    component_lookup: dict[str, dict[str, str]],
    component: str,
) -> str:
    row = component_lookup.get(component)
    if not row:
        return "missing"
    return row.get("source_status", "")


def _vorp_source_status(vorp_row: dict[str, str]) -> str:
    if not vorp_row:
        return "missing"
    first_down_status = vorp_row.get("first_down_source_status", "")
    if first_down_status == "estimated_from_history":
        return "review_only_first_down_estimated_from_history"
    if first_down_status:
        return f"review_only_{first_down_status}"
    return "review_only"


def _vorp_percentiles(vorp_rows: object) -> dict[str, float]:
    by_position: dict[str, list[tuple[str, float]]] = {}
    for row in vorp_rows:
        value = _optional_float(row.get("production_vorp_points"))
        if value is None:
            continue
        by_position.setdefault(row.get("position", ""), []).append(
            (normalize_player_name(row.get("player_name", "")), value)
        )
    output: dict[str, float] = {}
    for entries in by_position.values():
        values = [value for _name, value in entries]
        for name, value in entries:
            output[name] = _percentile_score(value, values)
    return output


def _rotowire_age_lookup(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 3:
        return {}
    output: dict[str, float] = {}
    for row in rows[2:]:
        if len(row) < 5:
            continue
        name = normalize_player_name(row[1])
        age = _optional_float(row[4])
        if name and age is not None:
            output[name] = age
    return output


def _sleeper_age_lookup(path: Path) -> dict[str, float]:
    output: dict[str, float] = {}
    for row in _read_rows(path):
        name = normalize_player_name(row.get("player_name", ""))
        age = _optional_float(row.get("age"))
        if name and age is not None:
            output[name] = age
    return output


def _by_player(rows: tuple[dict[str, str], ...]) -> dict[str, dict[str, str]]:
    return {normalize_player_name(row.get("player_name", "")): row for row in rows}


def _components_by_player(rows: tuple[dict[str, str], ...]) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        output.setdefault(normalize_player_name(row.get("player_name", "")), []).append(row)
    return output


def _warnings_by_player(rows: tuple[dict[str, str], ...]) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        output.setdefault(normalize_player_name(row.get("player_name", "")), []).append(row)
    return output


def _rank_candidates(rows: list[dict[str, object]]) -> None:
    rows.sort(key=lambda row: float(row["dynasty_candidate_value"]), reverse=True)
    by_position: dict[str, int] = {}
    for index, row in enumerate(rows, start=1):
        row["overall_candidate_rank"] = index
        position = str(row["position"])
        by_position[position] = by_position.get(position, 0) + 1
        row["position_candidate_rank"] = by_position[position]


def _warning(
    truth: dict[str, str],
    warning_type: str,
    severity: str,
    detail: str,
) -> dict[str, object]:
    return {
        "player_name": truth["player_name"],
        "position": truth["position"],
        "warning_type": warning_type,
        "severity": severity,
        "detail": detail,
        "candidate_version": DYNASTY_CANDIDATE_VERSION,
    }


def _mean_present(values: tuple[float | None, ...]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _percentile_score(value: float, values: list[float]) -> float:
    if not values:
        return 0.0
    lower_or_equal = sum(1 for candidate in values if candidate <= value)
    return (lower_or_equal / len(values)) * 100.0


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _float(value: object) -> float:
    maybe = _optional_float(value)
    return 0.0 if maybe is None else maybe


def _optional_float(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(str(value).replace(",", "").replace("%", ""))
    except ValueError:
        return None
