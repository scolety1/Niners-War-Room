from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_fantasypros_identity_mapping_service import normalize_player_name

DEFAULT_TRUTH_SET = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
DEFAULT_PLAYER_STATS = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv"
)
DEFAULT_ROLE_USAGE = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_role_usage_clean_rows.csv"
)
DEFAULT_CONTEXT = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_context_clean_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/rotowire_intake/latest")

EVIDENCE_LAYER_VERSION = "model_v4_rotowire_evidence_layer_0.1.0"

EVIDENCE_HEADER = (
    "player_name",
    "normalized_player_name",
    "position",
    "expected_team",
    "component",
    "row_count",
    "seasons",
    "latest_season",
    "source_families",
    "source_status",
    "allowed_use",
    "confidence_impact",
    "key_metrics_json",
    "warning",
    "evidence_version",
)

COVERAGE_HEADER = (
    "player_name",
    "position",
    "expected_team",
    "historical_production_status",
    "role_usage_status",
    "route_evidence_status",
    "projection_context_status",
    "injury_context_status",
    "depth_chart_context_status",
    "market_context_status",
    "rookie_workout_status",
    "overall_coverage_status",
    "warnings",
    "evidence_version",
)


@dataclass(frozen=True)
class RotoWireEvidenceLayerResult:
    evidence_rows: tuple[dict[str, object], ...]
    coverage_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rotowire_evidence_layer(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET,
    player_stats_path: str | Path = DEFAULT_PLAYER_STATS,
    role_usage_path: str | Path = DEFAULT_ROLE_USAGE,
    context_path: str | Path = DEFAULT_CONTEXT,
) -> RotoWireEvidenceLayerResult:
    truth_rows = _read_dict_rows(Path(truth_set_path))
    player_stats = _rows_by_name(Path(player_stats_path), "player_name")
    role_usage = _rows_by_name(Path(role_usage_path), "player_name")
    context = _rows_by_name(Path(context_path), "entity_name")

    evidence_rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    for truth in truth_rows:
        player = truth["player_name"]
        normalized = normalize_player_name(player)
        stats_rows = player_stats.get(normalized, [])
        role_rows = role_usage.get(normalized, [])
        context_rows = context.get(normalized, [])

        component_rows = [
            _component_row(
                truth,
                "historical_production",
                stats_rows,
                source_status="imported_real_data",
                allowed_use="scoring_allowed",
                confidence_impact="supports_confidence",
            ),
            _component_row(
                truth,
                "role_usage",
                role_rows,
                source_status="imported_role_usage_data",
                allowed_use="scoring_allowed_with_confidence_penalty",
                confidence_impact="supports_confidence",
                missing_source_status="not_applicable"
                if truth["position"] == "QB"
                else "missing",
                missing_allowed_use="not_applicable"
                if truth["position"] == "QB"
                else "scoring_allowed_with_confidence_penalty",
                missing_confidence_impact="not_required_for_qb"
                if truth["position"] == "QB"
                else "missing_evidence_warning",
                missing_warning="not_applicable_for_qb"
                if truth["position"] == "QB"
                else "missing_or_not_applicable",
            ),
            _component_row(
                truth,
                "licensed_route_evidence",
                _route_rows(stats_rows, role_rows),
                source_status="imported_route_data",
                allowed_use="scoring_allowed_with_confidence_penalty",
                confidence_impact="supports_confidence",
            ),
            _component_row(
                truth,
                "projection_context",
                _context_rows(context_rows, "projections"),
                source_status="raw_projection_stats_context",
                allowed_use="review_only",
                confidence_impact="comparison_only",
            ),
            _component_row(
                truth,
                "injury_context",
                _context_rows(context_rows, "injuries"),
                source_status="sourced_injury_context",
                allowed_use="context_only",
                confidence_impact="risk_context_only",
            ),
            _component_row(
                truth,
                "depth_chart_context",
                _context_rows(context_rows, "depth_charts"),
                source_status="current_depth_chart_context",
                allowed_use="context_only",
                confidence_impact="role_context_only",
            ),
            _component_row(
                truth,
                "market_context",
                _context_rows(context_rows, "market_context"),
                source_status="early_market_context",
                allowed_use="context_only",
                confidence_impact="no_private_value_impact",
            ),
            _component_row(
                truth,
                "rookie_workout_context",
                _context_rows(context_rows, "combine_workout"),
                source_status="prospect_workout_context",
                allowed_use="review_only",
                confidence_impact="rookie_bridge_context_only",
            ),
        ]
        evidence_rows.extend(component_rows)
        coverage_rows.append(_coverage_row(truth, component_rows))

    summary = {
        "evidence_version": EVIDENCE_LAYER_VERSION,
        "truth_player_count": len(truth_rows),
        "evidence_row_count": len(evidence_rows),
        "coverage_row_count": len(coverage_rows),
        "covered_player_count": sum(
            1 for row in coverage_rows if row["overall_coverage_status"] == "covered"
        ),
        "review_player_count": sum(
            1 for row in coverage_rows if row["overall_coverage_status"] != "covered"
        ),
        "model_scores_changed": False,
    }
    return RotoWireEvidenceLayerResult(
        evidence_rows=tuple(evidence_rows),
        coverage_rows=tuple(coverage_rows),
        summary=summary,
    )


def write_rotowire_evidence_layer_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RotoWireEvidenceLayerResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rotowire_evidence_layer()
    evidence_path = output / "rotowire_evidence_rows.csv"
    coverage_path = output / "rotowire_evidence_coverage.csv"
    summary_path = output / "rotowire_evidence_summary.csv"
    _write_csv(evidence_path, EVIDENCE_HEADER, result.evidence_rows)
    _write_csv(coverage_path, COVERAGE_HEADER, result.coverage_rows)
    _write_csv(
        summary_path,
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {"evidence": evidence_path, "coverage": coverage_path, "summary": summary_path}


def _component_row(
    truth: dict[str, str],
    component: str,
    rows: list[dict[str, str]],
    *,
    source_status: str,
    allowed_use: str,
    confidence_impact: str,
    missing_source_status: str = "missing",
    missing_allowed_use: str | None = None,
    missing_confidence_impact: str = "missing_evidence_warning",
    missing_warning: str = "missing_or_not_applicable",
) -> dict[str, object]:
    seasons = sorted({row.get("season", "") for row in rows if row.get("season")})
    families = sorted({row.get("source_family", "") for row in rows if row.get("source_family")})
    warning = "" if rows else missing_warning
    return {
        "player_name": truth["player_name"],
        "normalized_player_name": normalize_player_name(truth["player_name"]),
        "position": truth["position"],
        "expected_team": truth.get("nfl_team", ""),
        "component": component,
        "row_count": len(rows),
        "seasons": "|".join(seasons),
        "latest_season": max(seasons) if seasons else "",
        "source_families": "|".join(families),
        "source_status": source_status if rows else missing_source_status,
        "allowed_use": allowed_use if rows else (missing_allowed_use or allowed_use),
        "confidence_impact": confidence_impact if rows else missing_confidence_impact,
        "key_metrics_json": json.dumps(_key_metrics(rows), sort_keys=True),
        "warning": warning,
        "evidence_version": EVIDENCE_LAYER_VERSION,
    }


def _coverage_row(
    truth: dict[str, str],
    component_rows: list[dict[str, object]],
) -> dict[str, object]:
    by_component = {row["component"]: row for row in component_rows}
    warnings = [
        str(row["component"])
        for row in component_rows
        if row["warning"] == "missing_or_not_applicable"
        and row["component"] in {"historical_production", "role_usage"}
    ]
    overall = "covered" if not warnings else "review"
    return {
        "player_name": truth["player_name"],
        "position": truth["position"],
        "expected_team": truth.get("nfl_team", ""),
        "historical_production_status": by_component["historical_production"]["source_status"],
        "role_usage_status": by_component["role_usage"]["source_status"],
        "route_evidence_status": by_component["licensed_route_evidence"]["source_status"],
        "projection_context_status": by_component["projection_context"]["source_status"],
        "injury_context_status": by_component["injury_context"]["source_status"],
        "depth_chart_context_status": by_component["depth_chart_context"]["source_status"],
        "market_context_status": by_component["market_context"]["source_status"],
        "rookie_workout_status": by_component["rookie_workout_context"]["source_status"],
        "overall_coverage_status": overall,
        "warnings": "|".join(warnings),
        "evidence_version": EVIDENCE_LAYER_VERSION,
    }


def _route_rows(
    stats_rows: list[dict[str, str]],
    role_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    routed = [
        row
        for row in stats_rows
        if row.get("source_family") == "receiving" and row.get("source_detail") == "advanced"
    ]
    routed.extend(row for row in role_rows if row.get("source_family") == "te_routes")
    return routed


def _context_rows(rows: list[dict[str, str]], family: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("source_family") == family]


def _key_metrics(rows: list[dict[str, str]]) -> dict[str, object]:
    if not rows:
        return {}
    latest = sorted(rows, key=lambda row: row.get("season", ""))[-1]
    metrics = json.loads(latest.get("metrics_json") or "{}")
    interesting = {}
    for key in sorted(metrics):
        if key in {
            "receiving_tar",
            "receiving_rec",
            "receiving_yds",
            "rushing_att",
            "rushing_yds",
            "rushing_td",
            "routes_run_rts",
            "routes_run_tprr",
            "routes_run_yprr",
            "route_data_route",
            "snap_count_off",
            "snap_count_off_2",
            "week_by_week_targets_tar_g",
            "receiving_totals_tar",
            "depth_rank",
            "listed_status",
            "status",
            "injury",
            "rank",
        }:
            interesting[key] = metrics[key]
    return interesting


def _rows_by_name(path: Path, name_column: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in _read_dict_rows(path):
        normalized = normalize_player_name(row.get(name_column, ""))
        if not normalized:
            continue
        grouped.setdefault(normalized, []).append(row)
    return grouped


def _read_dict_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
