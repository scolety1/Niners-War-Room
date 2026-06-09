from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DEFAULT_INPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_11G_CURRENT_VALUE_CHECKPOINT.md")

CURRENT_VALUE_CHECKPOINT_VERSION = "model_v4_phase_11g_current_value_checkpoint_0.1.0"

RB_WR_VALUE_ROWS = DEFAULT_INPUT_ROOT / "rb_wr_current_value_review_rows.csv"
RB_WR_COMPONENT_ROWS = DEFAULT_INPUT_ROOT / "rb_wr_current_value_component_rows.csv"
RB_WR_RECEIPTS = DEFAULT_INPUT_ROOT / "rb_wr_current_value_receipts.csv"
RB_WR_WARNINGS = DEFAULT_INPUT_ROOT / "rb_wr_current_value_warnings.csv"
QB_TE_VALUE_ROWS = DEFAULT_INPUT_ROOT / "qb_te_current_value_review_rows.csv"
QB_TE_COMPONENT_ROWS = DEFAULT_INPUT_ROOT / "qb_te_current_value_component_rows.csv"
QB_TE_RECEIPTS = DEFAULT_INPUT_ROOT / "qb_te_current_value_receipts.csv"
QB_TE_WARNINGS = DEFAULT_INPUT_ROOT / "qb_te_current_value_warnings.csv"
LIFECYCLE_ROWS = DEFAULT_INPUT_ROOT / "lifecycle_archetype_review_rows.csv"
LIFECYCLE_COMPONENT_ROWS = DEFAULT_INPUT_ROOT / "lifecycle_archetype_component_rows.csv"
LIFECYCLE_RECEIPTS = DEFAULT_INPUT_ROOT / "lifecycle_archetype_receipts.csv"
LIFECYCLE_WARNINGS = DEFAULT_INPUT_ROOT / "lifecycle_archetype_warnings.csv"
CONFIDENCE_ROWS = DEFAULT_INPUT_ROOT / "confidence_missingness_review_rows.csv"
CONFIDENCE_RECEIPTS = DEFAULT_INPUT_ROOT / "confidence_missingness_receipts.csv"
CONFIDENCE_WARNINGS = DEFAULT_INPUT_ROOT / "confidence_missingness_warnings.csv"

NAMED_PLAYER_SANITY = (
    "Christian McCaffrey",
    "Lamar Jackson",
    "Josh Allen",
    "Brock Purdy",
    "Puka Nacua",
    "Jaxon Smith-Njigba",
    "Ja'Marr Chase",
    "Brock Bowers",
    "George Kittle",
)

VALUE_REVIEW_HEADER = (
    "canonical_player_key",
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "position_module",
    "scoring_season",
    "position_specific_review_score",
    "discipline_multiplier",
    "discipline_status",
    "lifecycle_modifier_review",
    "role_archetype",
    "role_fragility_status",
    "confidence_cap",
    "confidence_status",
    "checkpoint_review_score",
    "available_component_weight",
    "positive_vorp_points",
    "review_scoring_points",
    "imported_first_down_points",
    "first_down_source_status",
    "return_source_status",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "checkpoint_version",
)

COMPONENT_HEADER = (
    "canonical_player_key",
    "player_name",
    "position",
    "component_layer",
    "component_name",
    "component_value",
    "normalized_score",
    "component_weight",
    "weighted_contribution",
    "source_status",
    "source_file",
    "source_version",
    "component_warning",
    "checkpoint_version",
)

RECEIPT_HEADER = (
    "canonical_player_key",
    "player_name",
    "position",
    "receipt_layer",
    "feature_group",
    "receipt_pointer",
    "source_status",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "receipt_requirement",
    "source_version",
    "checkpoint_version",
)

WARNING_HEADER = (
    "entity_key",
    "player_name",
    "position",
    "warning_layer",
    "warning_type",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "source_version",
    "checkpoint_version",
)


@dataclass(frozen=True)
class CurrentValueCheckpointResult:
    review_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class CurrentValueCheckpointPaths:
    review_rows: Path
    component_rows: Path
    receipts: Path
    warnings: Path
    doc: Path


def build_current_value_checkpoint(
    *,
    input_root: str | Path = DEFAULT_INPUT_ROOT,
) -> CurrentValueCheckpointResult:
    root = Path(input_root)
    rb_wr_rows = _read_rows(root / RB_WR_VALUE_ROWS.name)
    qb_te_rows = _read_rows(root / QB_TE_VALUE_ROWS.name)
    lifecycle_by_key = _index(_read_rows(root / LIFECYCLE_ROWS.name), "canonical_player_key")
    confidence_by_key = _index(_read_rows(root / CONFIDENCE_ROWS.name), "entity_key")
    base_rows = (*rb_wr_rows, *qb_te_rows)
    review_rows = tuple(
        _checkpoint_row(
            row,
            lifecycle_by_key.get(row["canonical_player_key"], {}),
            confidence_by_key,
        )
        for row in base_rows
    )
    component_rows = (
        *_current_value_components(
            _read_rows(root / RB_WR_COMPONENT_ROWS.name),
            "rb_wr_current_value",
        ),
        *_current_value_components(
            _read_rows(root / QB_TE_COMPONENT_ROWS.name),
            "qb_te_current_value",
        ),
        *_lifecycle_components(_read_rows(root / LIFECYCLE_COMPONENT_ROWS.name)),
        *_confidence_components(_read_rows(root / CONFIDENCE_ROWS.name)),
    )
    receipt_rows = (
        *_receipts(_read_rows(root / RB_WR_RECEIPTS.name), "rb_wr_current_value"),
        *_receipts(_read_rows(root / QB_TE_RECEIPTS.name), "qb_te_current_value"),
        *_receipts(_read_rows(root / LIFECYCLE_RECEIPTS.name), "lifecycle_archetype"),
        *_confidence_receipts(_read_rows(root / CONFIDENCE_RECEIPTS.name)),
    )
    warning_rows = (
        *_warnings(_read_rows(root / RB_WR_WARNINGS.name), "rb_wr_current_value"),
        *_warnings(_read_rows(root / QB_TE_WARNINGS.name), "qb_te_current_value"),
        *_warnings(_read_rows(root / LIFECYCLE_WARNINGS.name), "lifecycle_archetype"),
        *_confidence_warnings(_read_rows(root / CONFIDENCE_WARNINGS.name)),
        *_sanity_warnings(review_rows),
    )
    summary = {
        "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        "review_status": "review_only",
        "review_rows": len(review_rows),
        "component_rows": len(component_rows),
        "receipt_rows": len(receipt_rows),
        "warning_rows": len(warning_rows),
        "market_rows_used": 0,
        "projection_rows_used": 0,
        "adp_rows_used": 0,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return CurrentValueCheckpointResult(
        review_rows=review_rows,
        component_rows=tuple(component_rows),
        receipt_rows=tuple(receipt_rows),
        warning_rows=tuple(warning_rows),
        summary=summary,
    )


def write_current_value_checkpoint_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    result: CurrentValueCheckpointResult | None = None,
) -> CurrentValueCheckpointPaths:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_current_value_checkpoint()
    paths = CurrentValueCheckpointPaths(
        review_rows=output / "current_player_value_review_rows.csv",
        component_rows=output / "current_player_value_component_rows.csv",
        receipts=output / "current_player_value_receipts.csv",
        warnings=output / "current_player_value_warnings.csv",
        doc=Path(doc_path),
    )
    _write_csv(paths.review_rows, VALUE_REVIEW_HEADER, result.review_rows)
    _write_csv(paths.component_rows, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_doc(paths.doc, result, paths)
    return paths


def _checkpoint_row(
    row: dict[str, str],
    lifecycle: dict[str, str],
    confidence_by_key: dict[str, dict[str, str]],
) -> dict[str, object]:
    key = row["canonical_player_key"]
    confidence = confidence_by_key.get(key, {})
    base_score = _float(row.get("current_value_review_score"))
    lifecycle_modifier = _float(lifecycle.get("lifecycle_modifier_review"), 1.0)
    confidence_cap = _float(confidence.get("confidence_cap"), 1.0)
    checkpoint_score = (
        round(base_score * lifecycle_modifier * confidence_cap, 4)
        if base_score is not None
        else ""
    )
    warning_flags = "|".join(
        dict.fromkeys(
            flag
            for flag in (
                *_split_flags(row.get("warning_flags")),
                *_split_flags(lifecycle.get("warning_flags")),
                *_split_flags(confidence.get("cap_reasons")),
            )
            if flag
        )
    )
    return {
        "canonical_player_key": key,
        "player_name": row.get("player_name", ""),
        "normalized_player_name": row.get("normalized_player_name", ""),
        "position": row.get("position", ""),
        "nfl_team": row.get("nfl_team", ""),
        "position_module": _position_module(row.get("position", "")),
        "scoring_season": row.get("scoring_season", ""),
        "position_specific_review_score": "" if base_score is None else base_score,
        "discipline_multiplier": row.get("discipline_multiplier", "1.0"),
        "discipline_status": row.get("discipline_status", ""),
        "lifecycle_modifier_review": lifecycle_modifier,
        "role_archetype": lifecycle.get("role_archetype", ""),
        "role_fragility_status": lifecycle.get("role_fragility_status", ""),
        "confidence_cap": confidence_cap,
        "confidence_status": confidence.get("confidence_status", ""),
        "checkpoint_review_score": checkpoint_score,
        "available_component_weight": row.get("available_component_weight", ""),
        "positive_vorp_points": row.get("positive_vorp_points", ""),
        "review_scoring_points": row.get("review_scoring_points", ""),
        "imported_first_down_points": row.get("imported_first_down_points", ""),
        "first_down_source_status": row.get("first_down_source_status", ""),
        "return_source_status": row.get("return_source_status", ""),
        "allowed_use": "review_only_current_value_checkpoint",
        "blocked_use": "do_not_use_as_final_ranking_or_roster_recommendation",
        "warning_flags": warning_flags,
        "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
    }


def _position_module(position: str) -> str:
    return "rb_wr_current_value" if position in {"RB", "WR"} else "qb_te_current_value"


def _current_value_components(
    rows: tuple[dict[str, str], ...],
    layer: str,
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "canonical_player_key": row.get("canonical_player_key", ""),
            "player_name": row.get("player_name", ""),
            "position": row.get("position", ""),
            "component_layer": layer,
            "component_name": row.get("component_name", ""),
            "component_value": row.get("raw_component_value", ""),
            "normalized_score": row.get("normalized_score", ""),
            "component_weight": row.get("component_weight", ""),
            "weighted_contribution": row.get("weighted_contribution", ""),
            "source_status": row.get("source_status", ""),
            "source_file": row.get("allowed_input_file", ""),
            "source_version": row.get("formula_version", ""),
            "component_warning": row.get("component_warning", ""),
            "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        }
        for row in rows
    )


def _lifecycle_components(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "canonical_player_key": row.get("canonical_player_key", ""),
            "player_name": row.get("player_name", ""),
            "position": row.get("position", ""),
            "component_layer": "lifecycle_archetype",
            "component_name": row.get("component_name", ""),
            "component_value": row.get("component_value", ""),
            "normalized_score": row.get("component_score", ""),
            "component_weight": "",
            "weighted_contribution": "",
            "source_status": row.get("source_status", ""),
            "source_file": row.get("allowed_input_file", ""),
            "source_version": row.get("lifecycle_version", ""),
            "component_warning": row.get("component_warning", ""),
            "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        }
        for row in rows
    )


def _confidence_components(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "canonical_player_key": row.get("entity_key", ""),
            "player_name": row.get("entity_name", ""),
            "position": row.get("position", ""),
            "component_layer": "confidence_missingness",
            "component_name": "confidence_cap",
            "component_value": row.get("cap_reasons", ""),
            "normalized_score": row.get("confidence_cap", ""),
            "component_weight": "",
            "weighted_contribution": "",
            "source_status": "review_only_confidence_metadata",
            "source_file": row.get("source_matrix", ""),
            "source_version": row.get("confidence_version", ""),
            "component_warning": row.get("warning_flags", ""),
            "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        }
        for row in rows
        if row.get("entity_type") == "nfl_player"
    )


def _receipts(rows: tuple[dict[str, str], ...], layer: str) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "canonical_player_key": row.get("canonical_player_key", ""),
            "player_name": row.get("player_name", ""),
            "position": row.get("position", ""),
            "receipt_layer": layer,
            "feature_group": row.get("feature_group", ""),
            "receipt_pointer": row.get("receipt_pointer", ""),
            "source_status": row.get("source_status", ""),
            "allowed_input_file": row.get("allowed_input_file", ""),
            "allowed_lane": row.get("allowed_lane", ""),
            "allowed_field_or_json_path": row.get("allowed_field_or_json_path", ""),
            "receipt_requirement": row.get("receipt_requirement", ""),
            "source_version": row.get("formula_version") or row.get("lifecycle_version", ""),
            "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        }
        for row in rows
    )


def _confidence_receipts(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "canonical_player_key": row.get("entity_key", ""),
            "player_name": row.get("entity_name", ""),
            "position": "",
            "receipt_layer": "confidence_missingness",
            "feature_group": row.get("feature_group", ""),
            "receipt_pointer": row.get("receipt_pointer", ""),
            "source_status": row.get("source_status", ""),
            "allowed_input_file": row.get("allowed_input_file", ""),
            "allowed_lane": row.get("allowed_lane", ""),
            "allowed_field_or_json_path": row.get("allowed_field_or_json_path", ""),
            "receipt_requirement": row.get("receipt_requirement", ""),
            "source_version": row.get("confidence_version", ""),
            "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        }
        for row in rows
        if row.get("entity_type") == "nfl_player"
    )


def _warnings(rows: tuple[dict[str, str], ...], layer: str) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "entity_key": row.get("entity_key", ""),
            "player_name": row.get("player_name", ""),
            "position": row.get("position", ""),
            "warning_layer": layer,
            "warning_type": row.get("warning_type", ""),
            "severity": row.get("severity", ""),
            "warning_code": row.get("warning_code", ""),
            "warning_detail": row.get("warning_detail", ""),
            "next_action": row.get("next_action", ""),
            "source_version": row.get("formula_version") or row.get("lifecycle_version", ""),
            "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        }
        for row in rows
    )


def _confidence_warnings(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "entity_key": row.get("entity_key", ""),
            "player_name": row.get("entity_name", ""),
            "position": row.get("position", ""),
            "warning_layer": "confidence_missingness",
            "warning_type": row.get("warning_type", ""),
            "severity": row.get("severity", ""),
            "warning_code": row.get("warning_code", ""),
            "warning_detail": row.get("warning_detail", ""),
            "next_action": row.get("next_action", ""),
            "source_version": row.get("confidence_version", ""),
            "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        }
        for row in rows
        if row.get("entity_type") == "nfl_player"
    )


def _sanity_warnings(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    by_name = {str(row["player_name"]): row for row in rows}
    warnings: list[dict[str, object]] = []
    for name in NAMED_PLAYER_SANITY:
        row = by_name.get(name)
        warnings.append(
            _sanity_warning(
                name,
                str(row.get("position", "")) if row else "",
                "named_player_present" if row else "named_player_missing",
                f"{name} sanity row {'present' if row else 'missing'} in checkpoint.",
            )
        )
    warnings.extend(_specific_sanity_warnings(by_name))
    niners = tuple(row for row in rows if row.get("nfl_team") == "SF")
    warnings.append(
        _sanity_warning(
            "Niners roster",
            "SF",
            "niners_roster_checkpoint",
            f"Niners checkpoint rows present: {len(niners)}.",
        )
    )
    warnings.extend(
        _sanity_warning(
            str(row["player_name"]),
            str(row["position"]),
            "niners_roster_player_present",
            f"{row['player_name']} present in Niners roster checkpoint.",
        )
        for row in niners
    )
    warnings.append(
        _sanity_warning(
            "Phase 11G",
            "QB|RB|WR|TE",
            "confidence_caps_visible_sanity",
            "Checkpoint score is base score times lifecycle modifier times confidence cap.",
        )
    )
    return tuple(warnings)


def _specific_sanity_warnings(
    by_name: dict[str, dict[str, object]],
) -> tuple[dict[str, object], ...]:
    checks = (
        ("Lamar Jackson", "one_qb_small_vorp_gap_cap", "lamar_one_qb_rushing_cap_visible"),
        ("Josh Allen", "one_qb_real_vorp_gap", "josh_allen_real_vorp_gap_visible"),
        ("Brock Purdy", "one_qb_pocket_mid_qb_cap", "brock_purdy_pocket_qb_cap_visible"),
        ("Christian McCaffrey", "rb_short_window", "cmc_short_window_role_visible"),
        ("Brock Bowers", "no_premium_te_real_vorp_gap", "bowers_no_premium_gap_visible"),
        ("George Kittle", "no_premium_te_small_gap_cap", "kittle_no_premium_cap_visible"),
    )
    warnings: list[dict[str, object]] = []
    for name, expected_token, code in checks:
        row = by_name.get(name, {})
        haystack = "|".join(str(value) for value in row.values()).lower()
        status = "passed" if expected_token.lower() in haystack else "needs_review"
        warnings.append(
            _sanity_warning(
                name,
                str(row.get("position", "")),
                code,
                f"{name} sanity check {status}: expected `{expected_token}` visibility.",
            )
        )
    return tuple(warnings)


def _sanity_warning(
    player_name: str,
    position: str,
    code: str,
    detail: str,
) -> dict[str, object]:
    return {
        "entity_key": f"phase_11g_sanity:{player_name}",
        "player_name": player_name,
        "position": position,
        "warning_layer": "checkpoint_sanity",
        "warning_type": "sanity_fixture",
        "severity": "review",
        "warning_code": code,
        "warning_detail": detail,
        "next_action": "Review checkpoint before any promotion planning.",
        "source_version": CURRENT_VALUE_CHECKPOINT_VERSION,
        "checkpoint_version": CURRENT_VALUE_CHECKPOINT_VERSION,
    }


def _index(rows: tuple[dict[str, str], ...], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def _split_flags(value: object) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(flag.strip() for flag in str(value).split("|") if flag.strip())


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(
    path: Path,
    result: CurrentValueCheckpointResult,
    outputs: CurrentValueCheckpointPaths,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(
        result.review_rows,
        key=lambda row: _float(row.get("checkpoint_review_score"), -1.0) or -1.0,
        reverse=True,
    )
    lines = [
        "# Phase 11G Current Value Integration Checkpoint",
        "",
        "## Purpose",
        "",
        "Phase 11G combines the review-only RB/WR, QB/TE, lifecycle, and confidence "
        "layers into one current player checkpoint. This is not a final dynasty "
        "ranking and is not promoted to the active app.",
        "",
        "## Outputs",
        "",
        f"- `{outputs.review_rows}`",
        f"- `{outputs.component_rows}`",
        f"- `{outputs.receipts}`",
        f"- `{outputs.warnings}`",
        "",
        "## Formula Visibility",
        "",
        "- `position_specific_review_score` stays separate from position module details.",
        "- `discipline_status` keeps QB/TE replacement discipline visible.",
        "- `lifecycle_modifier_review` and `role_archetype` stay visible.",
        "- `confidence_cap` is applied openly to produce `checkpoint_review_score`.",
        "- Market, projection, ADP, and ranking fields are not consumed.",
        "",
        "## Summary",
        "",
        f"- Review rows: {result.summary['review_rows']}",
        f"- Component rows: {result.summary['component_rows']}",
        f"- Receipt rows: {result.summary['receipt_rows']}",
        f"- Warning rows: {result.summary['warning_rows']}",
        f"- Market rows used: {result.summary['market_rows_used']}",
        f"- Projection rows used: {result.summary['projection_rows_used']}",
        "",
        "## Sample Rows Sorted For Review",
        "",
        "| Player | Pos | Module | Base | Lifecycle | Confidence | Checkpoint |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows[:15]:
        lines.append(
            "| {player} | {position} | {module} | {base} | {life} | {conf} | {score} |".format(
                player=row["player_name"],
                position=row["position"],
                module=row["position_module"],
                base=row["position_specific_review_score"],
                life=row["lifecycle_modifier_review"],
                conf=row["confidence_cap"],
                score=row["checkpoint_review_score"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
