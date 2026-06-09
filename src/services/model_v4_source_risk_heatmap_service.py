from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "source_risk_heatmap/latest"
DOC_PATH = Path("docs/model_v4/SOURCE_RISK_HEATMAP.md")
VERSION = "model_v4_source_risk_heatmap_0.1.0"

SOURCE_COVERAGE_ROWS = MODEL_ROOT / "evidence_matrices/latest/source_coverage_matrix.csv"
WARNING_MATRIX_ROWS = MODEL_ROOT / "evidence_matrices/latest/warning_matrix.csv"
PROSPECT_ROWS = MODEL_ROOT / "prospect_value/latest/prospect_value_review_rows.csv"
PROSPECT_WARNINGS = MODEL_ROOT / "prospect_value/latest/prospect_value_warnings.csv"
CURRENT_ROWS = MODEL_ROOT / "current_value/latest/current_player_value_review_rows.csv"
CURRENT_WARNINGS = MODEL_ROOT / "current_value/latest/current_player_value_warnings.csv"
ROOKIE_BOARD_ROWS = MODEL_ROOT / "rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
ROOKIE_WARNINGS = MODEL_ROOT / "rookie_draft_review/latest/rookie_draft_warnings.csv"

REVIEW_ONLY_USE = "review_only_source_risk_heatmap_not_final_recommendation"
BLOCKED_USE = "do_not_use_as_final_pick_trade_cut_keep_or_rank_instruction"

FEATURES = (
    "production",
    "draft_capital",
    "team_share",
    "athletic",
    "recruiting",
    "age",
    "landing_context",
    "injury",
    "route_usage",
    "first_down",
)

PLAYER_HEADER = (
    "player_name",
    "position",
    "entity_type",
    "model_score",
    "evidence_completeness_score",
    "production_status",
    "draft_capital_status",
    "team_share_status",
    "athletic_status",
    "recruiting_status",
    "age_status",
    "landing_context_status",
    "injury_status",
    "route_usage_status",
    "first_down_status",
    "source_risk_level",
    "biggest_source_risk",
    "warning_summary",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

FEATURE_HEADER = (
    "feature_key",
    "player_name",
    "position",
    "entity_type",
    "feature_name",
    "risk_level",
    "status_reason",
    "coverage_present",
    "coverage_source_status",
    "warning_codes",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

SUMMARY_HEADER = (
    "summary_key",
    "entity_type",
    "source_risk_level",
    "player_count",
    "most_common_warning",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

PLAYER_SUMMARY_HEADER = (
    "player_name",
    "position",
    "model_score",
    "worst_source_risk_level",
    "severity_label",
    "severity_rank",
    "human_review_priority",
    "evidence_modules_present",
    "evidence_modules_missing_or_partial",
    "biggest_source_risk",
    "warning_summary",
    "raw_module_row_count",
    "allowed_use",
    "blocked_use",
    "formula_version",
)


@dataclass(frozen=True)
class SourceRiskHeatmapResult:
    player_rows: tuple[dict[str, object], ...]
    player_summary_rows: tuple[dict[str, object], ...]
    feature_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_source_risk_heatmap() -> SourceRiskHeatmapResult:
    coverage_rows = _read_rows(SOURCE_COVERAGE_ROWS)
    matrix_warnings = _read_rows(WARNING_MATRIX_ROWS)
    prospect_rows = _read_rows(PROSPECT_ROWS)
    current_rows = _read_rows(CURRENT_ROWS)
    rookie_rows = _read_rows(ROOKIE_BOARD_ROWS)
    all_warning_rows = (
        _read_rows(PROSPECT_WARNINGS)
        + _read_rows(CURRENT_WARNINGS)
        + _read_rows(ROOKIE_WARNINGS)
        + matrix_warnings
    )

    coverage_lookup = _coverage_lookup(coverage_rows)
    warning_lookup = _warning_lookup(all_warning_rows)
    rookie_lookup = {_norm(row.get("prospect_name")): row for row in rookie_rows}

    player_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, object]] = []

    for row in prospect_rows:
        name = str(row.get("prospect_name", "")).strip()
        if not name:
            continue
        player = _build_player(
            name=name,
            position=str(row.get("position", "")),
            entity_type="rookie_prospect",
            model_score=_float(row.get("prospect_private_value_review_score")),
            row_warnings=_join(
                row.get("warning_flags"),
                rookie_lookup.get(_norm(name), {}).get("warning_flags"),
            ),
            coverage_rows=_lookup_typed(coverage_lookup, name, "rookie_prospect"),
            warning_codes=_lookup_typed(warning_lookup, name, "rookie_prospect"),
            component_values={
                "production": row.get("production_score"),
                "draft_capital": row.get("draft_capital_score"),
                "team_share": row.get("market_share_score"),
                "athletic": row.get("athletic_prior_score"),
                "recruiting": row.get("recruiting_prior_score"),
                "age": row.get("age_lifecycle_score"),
                "landing_context": row.get("landing_context_review"),
            },
        )
        player_rows.append(player)
        feature_rows.extend(
            _feature_rows_for_player(
                player,
                _lookup_typed(coverage_lookup, name, "rookie_prospect"),
                _lookup_typed(warning_lookup, name, "rookie_prospect"),
            )
        )

    for row in current_rows:
        name = str(row.get("player_name", "")).strip()
        if not name:
            continue
        player = _build_player(
            name=name,
            position=str(row.get("position", "")),
            entity_type="current_player",
            model_score=_float(row.get("checkpoint_review_score")),
            row_warnings=row.get("warning_flags", ""),
            coverage_rows=_lookup_typed(coverage_lookup, name, "current_player"),
            warning_codes=_lookup_typed(warning_lookup, name, "current_player"),
            component_values={
                "production": row.get("review_scoring_points"),
                "draft_capital": "",
                "team_share": "",
                "athletic": "",
                "recruiting": "",
                "age": row.get("lifecycle_modifier_review"),
                "landing_context": row.get("role_archetype"),
                "route_usage": row.get("role_fragility_status"),
                "first_down": row.get("first_down_source_status"),
            },
        )
        player_rows.append(player)
        feature_rows.extend(
            _feature_rows_for_player(
                player,
                _lookup_typed(coverage_lookup, name, "current_player"),
                _lookup_typed(warning_lookup, name, "current_player"),
            )
        )

    player_rows.sort(
        key=lambda row: (
            _risk_sort(str(row["source_risk_level"])),
            -(_float(row["model_score"]) or 0.0),
            str(row["player_name"]),
        )
    )
    summary_rows = _summary_rows(player_rows)
    player_summary_rows = _player_summary_rows(player_rows)
    return SourceRiskHeatmapResult(
        player_rows=tuple(player_rows),
        player_summary_rows=tuple(player_summary_rows),
        feature_rows=tuple(feature_rows),
        summary_rows=tuple(summary_rows),
        doc_text=_doc_text(player_rows, player_summary_rows, summary_rows),
    )


def write_source_risk_heatmap_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
) -> dict[str, Path]:
    result = build_source_risk_heatmap()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "player_rows": output / "source_risk_player_rows.csv",
        "player_summary_rows": output / "source_risk_player_summary_rows.csv",
        "feature_rows": output / "source_risk_feature_rows.csv",
        "summary": output / "source_risk_summary.csv",
        "doc": doc,
    }
    _write_csv(paths["player_rows"], PLAYER_HEADER, result.player_rows)
    _write_csv(
        paths["player_summary_rows"],
        PLAYER_SUMMARY_HEADER,
        result.player_summary_rows,
    )
    _write_csv(paths["feature_rows"], FEATURE_HEADER, result.feature_rows)
    _write_csv(paths["summary"], SUMMARY_HEADER, result.summary_rows)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _build_player(
    *,
    name: str,
    position: str,
    entity_type: str,
    model_score: float | None,
    row_warnings: str,
    coverage_rows: list[dict[str, str]],
    warning_codes: list[str],
    component_values: dict[str, object],
) -> dict[str, object]:
    warning_codes_text = _join(row_warnings, "|".join(warning_codes))
    statuses = {
        feature: _feature_status(
            feature,
            component_values.get(feature),
            coverage_rows,
            warning_codes_text,
            entity_type,
        )
        for feature in FEATURES
    }
    completeness = _completeness_score(statuses)
    source_risk = _overall_risk(statuses)
    biggest = _biggest_risk(statuses)
    return {
        "player_name": name,
        "position": position,
        "entity_type": entity_type,
        "model_score": _blank(model_score),
        "evidence_completeness_score": completeness,
        **{f"{feature}_status": statuses[feature] for feature in FEATURES},
        "source_risk_level": source_risk,
        "biggest_source_risk": biggest,
        "warning_summary": _plain_warning_summary(warning_codes_text),
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _feature_status(
    feature: str,
    value: object,
    coverage_rows: list[dict[str, str]],
    warnings: str,
    entity_type: str,
) -> str:
    feature_rows = [row for row in coverage_rows if _coverage_feature(row) == feature]
    has_coverage = any(str(row.get("present", "")).lower() == "true" for row in feature_rows)
    source_limited = _warning_applies_to_feature(warnings, feature, "source_limited") or any(
        "source-limited" in str(row.get("source_status", "")).lower()
        or "source_limited" in str(row.get("warnings", "")).lower()
        for row in feature_rows
    )
    quarantined = any(
        term in warnings
        for term in (
            "identity_review_cap",
            "partial_or_quarantined_join_cap",
            "source_normalized_review_not_formula_admitted",
        )
    )
    feature_missing_warning = _warning_applies_to_feature(warnings, feature, "missing")
    feature_mismatch_warning = _warning_applies_to_feature(warnings, feature, "mismatch")
    missing = _is_missing(value)
    if feature in {"draft_capital", "athletic", "recruiting"} and entity_type == "current_player":
        return "gray_missing"
    if quarantined:
        return "red_manual_review"
    if source_limited:
        return "orange_source_limited"
    if missing and not has_coverage:
        return "gray_missing"
    if missing or feature_missing_warning or feature_mismatch_warning:
        return "yellow_partial"
    if has_coverage or not missing:
        return "green_complete"
    return "yellow_partial"


def _feature_rows_for_player(
    player: dict[str, object],
    coverage_rows: list[dict[str, str]],
    warning_codes: list[str],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for feature in FEATURES:
        feature_coverage = [row for row in coverage_rows if _coverage_feature(row) == feature]
        output.append(
            {
                "feature_key": f"{_norm(player['player_name'])}:{feature}",
                "player_name": player["player_name"],
                "position": player["position"],
                "entity_type": player["entity_type"],
                "feature_name": feature,
                "risk_level": player[f"{feature}_status"],
                "status_reason": _status_reason(str(player[f"{feature}_status"]), feature),
                "coverage_present": any(
                    str(row.get("present", "")).lower() == "true" for row in feature_coverage
                ),
                "coverage_source_status": _join(
                    *(row.get("source_status", "") for row in feature_coverage)
                ),
                "warning_codes": "|".join(warning_codes),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output


def _coverage_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    output: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (_norm(row.get("entity_name")), _entity_bucket(row.get("entity_type")))
        output.setdefault(key, []).append(row)
    return output


def _warning_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[str]]:
    output: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        name = row.get("entity_name") or row.get("player_name") or row.get("entity_label")
        code = row.get("warning_code") or row.get("warning_flags")
        if not name or not code:
            continue
        entity_type = _entity_bucket(row.get("entity_type") or row.get("warning_layer"))
        for part in str(code).replace(";", "|").split("|"):
            clean = part.strip()
            if clean:
                output.setdefault((_norm(name), entity_type), []).append(clean)
    return output


def _lookup_typed(
    lookup: dict[tuple[str, str], list],
    name: str,
    entity_type: str,
) -> list:
    key = _norm(name)
    wanted = _entity_bucket(entity_type)
    rows = list(lookup.get((key, wanted), []))
    if wanted == "rookie_prospect":
        rows.extend(lookup.get((key, "current_prospect"), []))
    if wanted == "current_player":
        rows.extend(lookup.get((key, "nfl_player"), []))
    return rows


def _entity_bucket(value: object) -> str:
    text = str(value or "").lower()
    if "rookie" in text or "prospect" in text:
        return "rookie_prospect" if "current_player" not in text else "current_player"
    if "nfl_player" in text or "current_player" in text or "current_value" in text:
        return "current_player"
    return text or "unknown"


def _coverage_feature(row: dict[str, str]) -> str:
    group = str(row.get("feature_group", "")).lower()
    lane = str(row.get("lane", "")).lower()
    if "market_share" in group or "share" in group:
        return "team_share"
    if "draft" in group:
        return "draft_capital"
    if "workout" in group or "combine" in group:
        return "athletic"
    if "recruit" in group:
        return "recruiting"
    if "first_down" in group:
        return "first_down"
    if "route" in group or "snap" in group or "target" in group:
        return "route_usage"
    if "injury" in group:
        return "injury"
    if "depth" in group or "landing" in group:
        return "landing_context"
    if "age" in group or "lifecycle" in group:
        return "age"
    if "production" in group or "stats" in group or "scoring" in lane:
        return "production"
    return "production"


def _overall_risk(statuses: dict[str, str]) -> str:
    values = set(statuses.values())
    if "red_manual_review" in values:
        return "red_manual_review"
    if "orange_source_limited" in values:
        return "orange_source_limited"
    if "yellow_partial" in values:
        return "yellow_partial"
    if values == {"gray_missing"}:
        return "gray_missing"
    return "green_complete"


def _biggest_risk(statuses: dict[str, str]) -> str:
    for risk in ("red_manual_review", "orange_source_limited", "yellow_partial", "gray_missing"):
        for feature, status in statuses.items():
            if status == risk:
                return f"{feature}:{risk}"
    return "no_major_source_risk"


def _completeness_score(statuses: dict[str, str]) -> float:
    points = {
        "green_complete": 1.0,
        "yellow_partial": 0.65,
        "orange_source_limited": 0.45,
        "red_manual_review": 0.2,
        "gray_missing": 0.0,
    }
    return round(sum(points.get(value, 0.0) for value in statuses.values()) / len(statuses), 4)


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for entity_type in sorted({str(row["entity_type"]) for row in rows}):
        subset = [row for row in rows if row["entity_type"] == entity_type]
        warning_counter = Counter()
        for row in subset:
            for warning in str(row.get("warning_summary", "")).split("; "):
                if warning:
                    warning_counter[warning] += 1
        for risk in sorted({str(row["source_risk_level"]) for row in subset}, key=_risk_sort):
            risk_subset = [row for row in subset if row["source_risk_level"] == risk]
            output.append(
                {
                    "summary_key": f"{entity_type}:{risk}",
                    "entity_type": entity_type,
                    "source_risk_level": risk,
                    "player_count": len(risk_subset),
                    "most_common_warning": (
                        warning_counter.most_common(1)[0][0] if warning_counter else ""
                    ),
                    "allowed_use": REVIEW_ONLY_USE,
                    "blocked_use": BLOCKED_USE,
                    "formula_version": VERSION,
                }
            )
    return output


def _player_summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(_norm(row.get("player_name")), []).append(row)

    output: list[dict[str, object]] = []
    for group_rows in grouped.values():
        representative = sorted(group_rows, key=lambda row: str(row["player_name"]))[0]
        statuses_by_feature: dict[str, set[str]] = {
            feature: {str(row.get(f"{feature}_status", "")) for row in group_rows}
            for feature in FEATURES
        }
        present_modules = [
            feature
            for feature, statuses in statuses_by_feature.items()
            if "green_complete" in statuses
        ]
        missing_or_partial_modules = [
            feature
            for feature, statuses in statuses_by_feature.items()
            if statuses - {"", "green_complete"}
        ]
        risk_rows = sorted(
            group_rows,
            key=lambda row: (
                _risk_sort(str(row.get("source_risk_level", ""))),
                str(row.get("biggest_source_risk", "")),
            ),
        )
        scores = [_float(row.get("model_score")) for row in group_rows]
        warnings = _join(*(row.get("warning_summary", "") for row in group_rows))
        output.append(
            {
                "player_name": representative["player_name"],
                "position": _join(*(row.get("position", "") for row in group_rows)),
                "model_score": _blank(
                    max((score for score in scores if score is not None), default=None)
                ),
                "worst_source_risk_level": risk_rows[0].get("source_risk_level", ""),
                "severity_label": _severity_label(
                    str(risk_rows[0].get("source_risk_level", ""))
                ),
                "severity_rank": _severity_rank(
                    str(risk_rows[0].get("source_risk_level", ""))
                ),
                "human_review_priority": _human_review_priority(
                    str(risk_rows[0].get("source_risk_level", ""))
                ),
                "evidence_modules_present": "|".join(present_modules),
                "evidence_modules_missing_or_partial": "|".join(missing_or_partial_modules),
                "biggest_source_risk": risk_rows[0].get("biggest_source_risk", ""),
                "warning_summary": warnings,
                "raw_module_row_count": len(group_rows),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return sorted(
        output,
        key=lambda row: (
            _risk_sort(str(row["worst_source_risk_level"])),
            -(_float(row["model_score"]) or 0.0),
            str(row["player_name"]),
        ),
    )


def _plain_warning_summary(warnings: str) -> str:
    labels: list[str] = []
    for warning in warnings.split("|"):
        if not warning:
            continue
        if "source_limited" in warning:
            labels.append("source-limited evidence")
        elif "college_team_mismatch" in warning or "team_mismatch" in warning:
            labels.append("team or context mismatch warning")
        elif "quarantined" in warning or "identity_review" in warning:
            labels.append("quarantined or identity-review source")
        elif "mismatch" in warning:
            labels.append("team or context mismatch warning")
        elif "missing" in warning:
            labels.append("missing evidence")
        elif "route" in warning or "snap" in warning:
            labels.append("partial route or snap evidence")
    deduped: list[str] = []
    for label in labels:
        if label not in deduped:
            deduped.append(label)
    return "; ".join(deduped)


def _severity_label(risk_level: str) -> str:
    return {
        "red_manual_review": "High",
        "orange_source_limited": "Medium-high",
        "yellow_partial": "Medium",
        "gray_missing": "Manual context",
        "green_complete": "Low",
    }.get(risk_level, "Review")


def _severity_rank(risk_level: str) -> int:
    return {
        "red_manual_review": 1,
        "orange_source_limited": 2,
        "yellow_partial": 3,
        "gray_missing": 4,
        "green_complete": 5,
    }.get(risk_level, 9)


def _human_review_priority(risk_level: str) -> str:
    return {
        "red_manual_review": "Open receipts before relying on this row.",
        "orange_source_limited": "Review source limits and role context.",
        "yellow_partial": "Check missing or partial modules.",
        "gray_missing": "Use as manual context only where evidence is absent.",
        "green_complete": "Normal review; still not a final recommendation.",
    }.get(risk_level, "Review evidence before making a human decision.")


def _status_reason(status: str, feature: str) -> str:
    return {
        "green_complete": f"{feature} evidence is present.",
        "yellow_partial": f"{feature} evidence is partial or warning-capped.",
        "orange_source_limited": f"{feature} evidence is source-limited.",
        "red_manual_review": f"{feature} evidence requires manual review.",
        "gray_missing": f"{feature} evidence is missing, not zero-filled.",
    }.get(status, "Review feature evidence.")


def _warning_applies_to_feature(warnings: str, feature: str, kind: str) -> bool:
    tokens = [token for token in warnings.split("|") if token]
    for token in tokens:
        if kind not in token:
            continue
        if feature == "athletic" and any(
            term in token for term in ("combine", "workout", "athletic")
        ):
            return True
        if feature == "team_share" and any(
            term in token for term in ("market_share", "team_share")
        ):
            return True
        if feature == "production" and any(
            term in token for term in ("production", "college_team")
        ):
            return True
        if feature == "draft_capital" and "draft" in token:
            return True
        if feature == "age" and any(term in token for term in ("age", "lifecycle")):
            return True
        if feature == "landing_context" and any(
            term in token for term in ("landing", "depth", "college_team")
        ):
            return True
        if feature == "route_usage" and any(term in token for term in ("route", "snap", "target")):
            return True
        if feature == "first_down" and "first_down" in token:
            return True
        if feature == "injury" and "injury" in token:
            return True
        if feature == "recruiting" and "recruit" in token:
            return True
    return False


def _doc_text(
    rows: list[dict[str, object]],
    player_summary_rows: list[dict[str, object]],
    summary_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Source-Risk Heatmap",
        "",
        "## Scope",
        "",
        "This review-only heatmap shows where player value is evidence-supported and "
        "where it is fragile due to missing, partial, source-limited, or quarantined data.",
        "",
        "## Export Shape",
        "",
        "`source_risk_player_rows.csv` preserves module/context-level evidence rows for audit. "
        "A player can appear more than once there when separate evidence modules or contexts "
        "need separate risk tracking. `source_risk_player_summary_rows.csv` is the "
        "human-facing one-row-per-player export.",
        "",
        "## Summary",
        "",
        "| Entity Type | Risk Level | Count |",
        "|---|---|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['entity_type']} | {row['source_risk_level']} | "
            f"{row['player_count']} |"
        )
    lines.extend(
        [
            "",
            "## Player Summary Rows",
            "",
            "| Player | Pos | Worst Risk | Biggest Risk | Raw Rows |",
            "|---|---|---|---|---:|",
        ]
    )
    for row in player_summary_rows[:25]:
        lines.append(
            f"| {row['player_name']} | {row['position']} | "
            f"{row['worst_source_risk_level']} | {row['biggest_source_risk']} | "
            f"{row['raw_module_row_count']} |"
        )
    lines.extend(
        [
            "",
            "## Highest Risk Rows",
            "",
            "| Player | Pos | Type | Risk | Biggest Risk |",
            "|---|---|---|---|---|",
        ]
    )
    for row in rows[:25]:
        lines.append(
            f"| {row['player_name']} | {row['position']} | {row['entity_type']} | "
            f"{row['source_risk_level']} | {row['biggest_source_risk']} |"
        )
    return "\n".join(lines) + "\n"


def _risk_sort(value: str) -> int:
    return {
        "red_manual_review": 0,
        "orange_source_limited": 1,
        "yellow_partial": 2,
        "gray_missing": 3,
        "green_complete": 4,
    }.get(value, 9)


def _is_missing(value: object) -> bool:
    return str(value or "").strip() in {"", "nan", "None"}


def _float(value: object) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value))
    except ValueError:
        return None


def _blank(value: float | None) -> str | float:
    return "" if value is None else round(value, 4)


def _join(*values: object) -> str:
    parts: list[str] = []
    for value in values:
        for part in str(value or "").replace(";", "|").split("|"):
            clean = part.strip()
            if clean and clean not in parts:
                parts.append(clean)
    return "|".join(parts)


def _norm(value: object) -> str:
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
