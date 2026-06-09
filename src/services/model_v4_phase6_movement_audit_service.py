from __future__ import annotations

import csv
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_preview_engine_service import (
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_V3_REPORT_ROOT,
    build_model_v4_preview,
)
from src.services.model_v4_sanity_fixture_dry_run_service import (
    DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
)

PHASE_5_ARCHIVED_CONFIG_PATH = Path(
    "local_exports/model_v4/audit_packets/"
    "model_v4_phase4_external_audit_20260516T033806Z/"
    "docs/model_v4/MODEL_V4_FORMULA_CONFIG.json"
)
PHASE_5_RECONSTRUCTED_PREVIEW_ID = "phase5_checkpoint_reconstructed"
PHASE_5_RECONSTRUCTED_ROOT = (
    DEFAULT_OUTPUT_ROOT / PHASE_5_RECONSTRUCTED_PREVIEW_ID
)
PHASE_5_RECONSTRUCTED_CONFIG_PATH = (
    PHASE_5_RECONSTRUCTED_ROOT / "MODEL_V4_FORMULA_CONFIG_PHASE5_RECONSTRUCTED.json"
)
PHASE_6_MOVEMENT_AUDIT_CSV_PATH = Path("docs/model_v4/PHASE_6_MOVEMENT_AUDIT.csv")
PHASE_6_MOVEMENT_AUDIT_MD_PATH = Path("docs/model_v4/PHASE_6_MOVEMENT_AUDIT.md")

COMPONENTS = (
    "production",
    "first_down_scoring_fit",
    "usage_opportunity",
    "snap_proxy_role",
    "projection",
    "age_dropoff",
    "young_player_prior",
    "position_scarcity_suppression",
    "no_premium_suppression",
)

PHASE_6_MOVEMENT_HEADER = (
    "player",
    "position",
    "nfl_team",
    "truth_set_group",
    "audit_groups",
    "lifecycle",
    "phase5_rank",
    "phase6_rank",
    "rank_delta",
    "phase5_dynasty_asset_value",
    "phase6_dynasty_asset_value",
    "value_delta",
    "movement_magnitude",
    "movement_cause",
    "phase5_confidence_label",
    "phase6_confidence_label",
    "phase5_value_basis",
    "phase6_value_basis",
    "phase5_missing_value_components",
    "phase6_missing_value_components",
    "production_score_delta",
    "production_contribution_delta",
    "first_down_score_delta",
    "first_down_contribution_delta",
    "usage_score_delta",
    "usage_contribution_delta",
    "snap_score_delta",
    "snap_contribution_delta",
    "projection_score_delta",
    "projection_contribution_delta",
    "age_score_delta",
    "age_contribution_delta",
    "young_prior_score_delta",
    "young_prior_contribution_delta",
    "qb_suppression_score_delta",
    "qb_suppression_contribution_delta",
    "te_suppression_score_delta",
    "te_suppression_contribution_delta",
    "added_warnings",
    "removed_warnings",
    "receipt_backed_explanation",
    "review_note",
)


@dataclass(frozen=True)
class ModelV4Phase6MovementAuditResult:
    csv_path: Path
    markdown_path: Path
    reconstructed_phase5_preview_path: Path
    reconstructed_phase5_config_path: Path
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def run_model_v4_phase6_movement_audit(
    *,
    phase5_preview_path: str | Path | None = None,
    current_preview_path: str | Path = DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    output_csv_path: str | Path = PHASE_6_MOVEMENT_AUDIT_CSV_PATH,
    output_md_path: str | Path = PHASE_6_MOVEMENT_AUDIT_MD_PATH,
) -> ModelV4Phase6MovementAuditResult:
    baseline_path = (
        Path(phase5_preview_path)
        if phase5_preview_path is not None
        else ensure_phase5_reconstructed_preview()
    )
    phase5_rows = _ranked(_read_dicts(baseline_path))
    phase6_rows = _ranked(_read_dicts(Path(current_preview_path)))
    rows = tuple(
        _movement_row(player_key, phase5_rows.get(player_key), phase6_rows.get(player_key))
        for player_key in sorted(
            set(phase5_rows) | set(phase6_rows),
            key=lambda key: (
                _int((phase6_rows.get(key) or phase5_rows.get(key) or {}).get("rank"), 9999),
                key,
            ),
        )
    )
    summary = _summary(
        rows,
        phase5_preview_path=baseline_path,
        phase6_preview_path=Path(current_preview_path),
    )
    csv_path = Path(output_csv_path)
    md_path = Path(output_md_path)
    _write_csv(csv_path, PHASE_6_MOVEMENT_HEADER, rows)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown(summary, rows), encoding="utf-8")
    return ModelV4Phase6MovementAuditResult(
        csv_path=csv_path,
        markdown_path=md_path,
        reconstructed_phase5_preview_path=baseline_path,
        reconstructed_phase5_config_path=PHASE_5_RECONSTRUCTED_CONFIG_PATH,
        rows=rows,
        summary=summary,
    )


def ensure_phase5_reconstructed_preview() -> Path:
    PHASE_5_RECONSTRUCTED_ROOT.mkdir(parents=True, exist_ok=True)
    config = _phase5_reconstructed_config()
    PHASE_5_RECONSTRUCTED_CONFIG_PATH.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = build_model_v4_preview(
        formula_config_path=PHASE_5_RECONSTRUCTED_CONFIG_PATH,
        v3_report_root=DEFAULT_V3_REPORT_ROOT,
        output_root=DEFAULT_OUTPUT_ROOT,
        preview_id=PHASE_5_RECONSTRUCTED_PREVIEW_ID,
    )
    return result.preview_outputs_path


def _phase5_reconstructed_config() -> dict[str, object]:
    source_path = (
        PHASE_5_ARCHIVED_CONFIG_PATH
        if PHASE_5_ARCHIVED_CONFIG_PATH.exists()
        else Path("docs/model_v4/MODEL_V4_FORMULA_CONFIG.json")
    )
    config = json.loads(source_path.read_text(encoding="utf-8"))
    reconstructed = deepcopy(config)
    reconstructed["formula_version"] = (
        "model_v4_review_only_0.1.0_phase5_checkpoint_reconstructed"
    )
    reconstructed.pop("missing_evidence_policy", None)
    weights = reconstructed.get("position_component_weights", {})
    if isinstance(weights, dict):
        wr_weights = weights.get("WR")
        if isinstance(wr_weights, dict):
            wr_weights.update(
                {
                    "production": 26,
                    "usage_opportunity": 24,
                    "snap_proxy_role": 6,
                    "projection": 10,
                }
            )
        qb_weights = weights.get("QB")
        if isinstance(qb_weights, dict):
            qb_weights["position_scarcity_suppression"] = 0
        te_weights = weights.get("TE")
        if isinstance(te_weights, dict):
            te_weights["no_premium_suppression"] = 0
    return reconstructed


def _movement_row(
    player_key: str,
    previous: dict[str, object] | None,
    current: dict[str, object] | None,
) -> dict[str, object]:
    row = current or previous or {}
    previous_scores = _component_values(previous, "component_scores")
    current_scores = _component_values(current, "component_scores")
    previous_contributions = _component_values(previous, "component_contributions")
    current_contributions = _component_values(current, "component_contributions")
    score_deltas = _component_deltas(previous_scores, current_scores)
    contribution_deltas = _component_deltas(previous_contributions, current_contributions)
    value_delta = round(
        _float((current or {}).get("dynasty_asset_value"))
        - _float((previous or {}).get("dynasty_asset_value")),
        3,
    )
    rank_delta = _int((current or {}).get("rank")) - _int((previous or {}).get("rank"))
    warning_delta = _warning_delta(previous, current)
    context = MovementCauseContext(
        previous=previous,
        current=current,
        score_deltas=score_deltas,
        contribution_deltas=contribution_deltas,
        value_delta=value_delta,
        rank_delta=rank_delta,
        warning_delta=warning_delta,
    )
    cause = classify_phase6_movement_cause(context)
    magnitude = movement_magnitude(value_delta, rank_delta)
    return {
        "player": row.get("player", ""),
        "position": row.get("position", ""),
        "nfl_team": row.get("nfl_team", ""),
        "truth_set_group": row.get("truth_set_group", ""),
        "audit_groups": "|".join(_audit_groups(row)),
        "lifecycle": row.get("lifecycle", ""),
        "phase5_rank": (previous or {}).get("rank", ""),
        "phase6_rank": (current or {}).get("rank", ""),
        "rank_delta": rank_delta if previous and current else "",
        "phase5_dynasty_asset_value": _format_number(
            (previous or {}).get("dynasty_asset_value")
        ),
        "phase6_dynasty_asset_value": _format_number(
            (current or {}).get("dynasty_asset_value")
        ),
        "value_delta": _format_number(value_delta) if previous and current else "",
        "movement_magnitude": magnitude,
        "movement_cause": cause,
        "phase5_confidence_label": (previous or {}).get("confidence_label", ""),
        "phase6_confidence_label": (current or {}).get("confidence_label", ""),
        "phase5_value_basis": (previous or {}).get("value_basis", ""),
        "phase6_value_basis": (current or {}).get("value_basis", ""),
        "phase5_missing_value_components": (previous or {}).get(
            "missing_value_components", ""
        ),
        "phase6_missing_value_components": (current or {}).get(
            "missing_value_components", ""
        ),
        "production_score_delta": _format_number(score_deltas["production"]),
        "production_contribution_delta": _format_number(
            contribution_deltas["production"]
        ),
        "first_down_score_delta": _format_number(
            score_deltas["first_down_scoring_fit"]
        ),
        "first_down_contribution_delta": _format_number(
            contribution_deltas["first_down_scoring_fit"]
        ),
        "usage_score_delta": _format_number(score_deltas["usage_opportunity"]),
        "usage_contribution_delta": _format_number(
            contribution_deltas["usage_opportunity"]
        ),
        "snap_score_delta": _format_number(score_deltas["snap_proxy_role"]),
        "snap_contribution_delta": _format_number(
            contribution_deltas["snap_proxy_role"]
        ),
        "projection_score_delta": _format_number(score_deltas["projection"]),
        "projection_contribution_delta": _format_number(
            contribution_deltas["projection"]
        ),
        "age_score_delta": _format_number(score_deltas["age_dropoff"]),
        "age_contribution_delta": _format_number(
            contribution_deltas["age_dropoff"]
        ),
        "young_prior_score_delta": _format_number(score_deltas["young_player_prior"]),
        "young_prior_contribution_delta": _format_number(
            contribution_deltas["young_player_prior"]
        ),
        "qb_suppression_score_delta": _format_number(
            score_deltas["position_scarcity_suppression"]
        ),
        "qb_suppression_contribution_delta": _format_number(
            contribution_deltas["position_scarcity_suppression"]
        ),
        "te_suppression_score_delta": _format_number(
            score_deltas["no_premium_suppression"]
        ),
        "te_suppression_contribution_delta": _format_number(
            contribution_deltas["no_premium_suppression"]
        ),
        "added_warnings": "|".join(warning_delta["added"]),
        "removed_warnings": "|".join(warning_delta["removed"]),
        "receipt_backed_explanation": _receipt_explanation(
            cause,
            score_deltas,
            contribution_deltas,
            previous,
            current,
        ),
        "review_note": _review_note(cause, magnitude, row),
    }


@dataclass(frozen=True)
class MovementCauseContext:
    previous: dict[str, object] | None
    current: dict[str, object] | None
    score_deltas: dict[str, float]
    contribution_deltas: dict[str, float]
    value_delta: float
    rank_delta: int
    warning_delta: dict[str, tuple[str, ...]]


def classify_phase6_movement_cause(context: MovementCauseContext) -> str:
    previous = context.previous
    current = context.current
    if previous is None or current is None:
        return "unexpected movement"
    if (
        abs(context.value_delta) < 1.0
        and abs(context.rank_delta) < 3
        and not context.warning_delta["added"]
        and not context.warning_delta["removed"]
    ):
        return "no material movement"
    if (
        str(previous.get("position") or "") != str(current.get("position") or "")
        or str(previous.get("nfl_team") or "") != str(current.get("nfl_team") or "")
    ):
        return "unexpected movement"

    position = str(current.get("position") or "").upper()
    contribution_deltas = context.contribution_deltas
    if position == "QB" and _meaningful_delta(
        contribution_deltas["position_scarcity_suppression"]
    ):
        return "QB suppression patch"
    if position == "TE" and _meaningful_delta(
        contribution_deltas["no_premium_suppression"]
    ):
        return "TE suppression patch"
    if position == "WR" and any(
        _meaningful_delta(contribution_deltas[component])
        for component in (
            "production",
            "usage_opportunity",
            "snap_proxy_role",
            "projection",
        )
    ):
        return "WR production/projection weighting patch"
    if position == "RB" and any(
        _meaningful_delta(contribution_deltas[component])
        for component in ("usage_opportunity", "age_dropoff")
    ):
        return "RB workload/age patch"
    if _meaningful_delta(contribution_deltas["young_player_prior"]):
        return "young bridge patch"
    if (
        str(current.get("value_basis") or "") == "evidence_adjusted_missing_not_zero"
        and str(current.get("missing_value_components") or "")
        and _component_deltas_are_tiny(contribution_deltas)
    ):
        return "confidence/missing-data patch"
    if str(previous.get("confidence_label") or "") != str(
        current.get("confidence_label") or ""
    ):
        return "confidence/missing-data patch"
    if context.warning_delta["added"] or context.warning_delta["removed"]:
        return "confidence/missing-data patch"
    if position in {"RB", "WR"} and abs(context.rank_delta) >= 3:
        return "RB/WR balance formula patch"
    return "unexpected movement"


def movement_magnitude(value_delta: float, rank_delta: int) -> str:
    abs_value = abs(value_delta)
    abs_rank = abs(rank_delta)
    if abs_value >= 8.0 or abs_rank >= 12:
        return "large"
    if abs_value >= 3.0 or abs_rank >= 5:
        return "medium"
    if abs_value >= 1.0 or abs_rank >= 3:
        return "small"
    return "none"


def _component_deltas(
    previous: dict[str, object],
    current: dict[str, object],
) -> dict[str, float]:
    return {
        component: round(
            _float(current.get(component)) - _float(previous.get(component)),
            3,
        )
        for component in COMPONENTS
    }


def _component_deltas_are_tiny(component_deltas: dict[str, float]) -> bool:
    return all(abs(value) < 0.01 for value in component_deltas.values())


def _receipt_explanation(
    cause: str,
    score_deltas: dict[str, float],
    contribution_deltas: dict[str, float],
    previous: dict[str, object] | None,
    current: dict[str, object] | None,
) -> str:
    if previous is None or current is None:
        return "Player appeared/disappeared between previews; inspect identity/source scope."
    if cause == "WR production/projection weighting patch":
        return (
            "WR value moved because production, usage, snap, and projection weights "
            "changed; receipt contribution deltas are production "
            f"{contribution_deltas['production']:+.2f}, usage "
            f"{contribution_deltas['usage_opportunity']:+.2f}, snap "
            f"{contribution_deltas['snap_proxy_role']:+.2f}, projection "
            f"{contribution_deltas['projection']:+.2f}."
        )
    if cause == "QB suppression patch":
        return (
            "QB value moved because the 1QB suppression component is now emitted; "
            "receipt contribution delta is "
            f"{contribution_deltas['position_scarcity_suppression']:+.2f}."
        )
    if cause == "TE suppression patch":
        return (
            "TE value moved because the no-premium TE suppression component is now emitted; "
            "receipt contribution delta is "
            f"{contribution_deltas['no_premium_suppression']:+.2f}."
        )
    if cause == "confidence/missing-data patch":
        return (
            "Value/trust moved because missing evidence now keeps its warning and "
            "applies the Phase 6 uncertainty penalty when value is evidence-adjusted."
        )
    if cause == "young bridge patch":
        return (
            "Young-player bridge contribution changed; inspect draft-prior and NFL "
            "evidence receipt rows before interpreting the movement."
        )
    if cause == "RB workload/age patch":
        return (
            "RB value moved through usage or age/dropoff receipt contribution changes; "
            "inspect workload and age rows before interpreting the movement."
        )
    if cause == "RB/WR balance formula patch":
        return (
            "Player rank moved mostly because other RB/WR values changed under the "
            "Phase 6 balance patch; own component scores were materially stable."
        )
    if cause == "no material movement":
        return "No material value, rank, warning, or receipt movement."
    top_component = max(
        COMPONENTS,
        key=lambda component: abs(contribution_deltas.get(component, 0.0)),
    )
    return (
        "Movement did not map cleanly to a planned patch category. Largest receipt "
        f"contribution delta is {top_component} "
        f"{contribution_deltas[top_component]:+.2f}; score delta "
        f"{score_deltas[top_component]:+.2f}."
    )


def _review_note(cause: str, magnitude: str, row: dict[str, object]) -> str:
    if cause == "unexpected movement":
        return "Review before any promotion; movement was not explained by a planned patch."
    if magnitude in {"medium", "large"}:
        return "Meaningful movement; review receipts before promotion."
    if "young" in str(row.get("lifecycle") or "").lower():
        return "Young bridge row remains review-only."
    return "No promotion; v4 remains review-only."


def _summary(
    rows: tuple[dict[str, object], ...],
    *,
    phase5_preview_path: Path,
    phase6_preview_path: Path,
) -> dict[str, object]:
    return {
        "review_status": "review_only",
        "phase5_baseline": str(phase5_preview_path),
        "phase6_preview": str(phase6_preview_path),
        "rows": len(rows),
        "meaningful_movement_rows": sum(
            1 for row in rows if row["movement_magnitude"] != "none"
        ),
        "large_movement_rows": sum(
            1 for row in rows if row["movement_magnitude"] == "large"
        ),
        "medium_movement_rows": sum(
            1 for row in rows if row["movement_magnitude"] == "medium"
        ),
        "unexpected_movement_rows": sum(
            1 for row in rows if row["movement_cause"] == "unexpected movement"
        ),
        "niners_roster_rows": _group_count(rows, "niners_roster"),
        "elite_rb_rows": _group_count(rows, "elite_rb"),
        "elite_wr_rows": _group_count(rows, "elite_wr"),
        "aging_veteran_rows": _group_count(rows, "aging_veteran"),
        "young_bridge_rows": _group_count(rows, "young_bridge"),
        "qb_rows": _group_count(rows, "qb"),
        "te_rows": _group_count(rows, "te"),
        "active_rankings_promoted": False,
        "decision_ready_unlocked": False,
    }


def _markdown(summary: dict[str, object], rows: tuple[dict[str, object], ...]) -> str:
    meaningful_rows = tuple(row for row in rows if row["movement_magnitude"] != "none")
    suspicious_rows = tuple(
        row for row in rows if row["movement_cause"] == "unexpected movement"
    )
    lines = [
        "# Phase 6 Movement Audit",
        "",
        "This report compares the post-formula-patch v4 review-only preview against "
        "a reconstructed Phase 5 checkpoint baseline. The reconstructed baseline uses "
        "the archived 0.1.0 config and current Phase 5 repaired source rows, while "
        "preserving old behavior for QB/TE suppression components. It does not promote "
        "app rankings or unlock readiness.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Cause Counts", ""])
    for cause, count in _cause_counts(rows):
        lines.append(f"- {cause}: {count}")
    lines.extend(["", "## Meaningful Movements", ""])
    table_header = (
        "player",
        "position",
        "audit_groups",
        "phase5_rank",
        "phase6_rank",
        "rank_delta",
        "phase5_dynasty_asset_value",
        "phase6_dynasty_asset_value",
        "value_delta",
        "movement_magnitude",
        "movement_cause",
        "receipt_backed_explanation",
    )
    lines.extend(_markdown_table(table_header, meaningful_rows[:70]))
    lines.extend(["", "## Remaining Suspicious Rankings", ""])
    if suspicious_rows:
        lines.extend(_markdown_table(table_header, suspicious_rows[:40]))
    else:
        lines.append("No unexpected movement rows were detected by the Phase 6 audit.")
    lines.extend(["", "## Named Group Coverage", ""])
    group_header = (
        "audit_group",
        "row_count",
        "meaningful_rows",
        "largest_abs_value_delta",
    )
    lines.extend(_markdown_table(group_header, _group_summary(rows)))
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- v4 remains review-only.",
            "- Active War Board/My Team rankings were not promoted.",
            "- Readiness gates remain locked.",
            "- Movement cause labels are audit metadata, not formula tuning.",
            "",
        ]
    )
    return "\n".join(lines)


def _ranked(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    sorted_rows = sorted(
        rows,
        key=lambda row: _float(row.get("dynasty_asset_value")),
        reverse=True,
    )
    output: dict[str, dict[str, object]] = {}
    for rank, row in enumerate(sorted_rows, 1):
        copy: dict[str, object] = dict(row)
        copy["rank"] = rank
        output[_key(row.get("player"))] = copy
    return output


def _component_values(row: dict[str, object] | None, field: str) -> dict[str, object]:
    if row is None:
        return {}
    try:
        parsed = json.loads(str(row.get(field) or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _warning_delta(
    previous: dict[str, object] | None,
    current: dict[str, object] | None,
) -> dict[str, tuple[str, ...]]:
    previous_warnings = set(_split((previous or {}).get("review_warnings")))
    current_warnings = set(_split((current or {}).get("review_warnings")))
    return {
        "added": tuple(sorted(current_warnings - previous_warnings)),
        "removed": tuple(sorted(previous_warnings - current_warnings)),
    }


def _audit_groups(row: dict[str, object]) -> tuple[str, ...]:
    groups = []
    truth_group = str(row.get("truth_set_group") or "")
    lifecycle = str(row.get("lifecycle") or "")
    position = str(row.get("position") or "").upper()
    if truth_group == "niners_roster":
        groups.append("niners_roster")
    if "elite_rb" in truth_group:
        groups.append("elite_rb")
    if "elite_wr" in truth_group:
        groups.append("elite_wr")
    if "aging" in truth_group:
        groups.append("aging_veteran")
    if "bridge" in lifecycle or "rookie" in lifecycle:
        groups.append("young_bridge")
    if position == "QB":
        groups.append("qb")
    if position == "TE":
        groups.append("te")
    return tuple(groups or ("other",))


def _group_summary(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    output = []
    for group in (
        "niners_roster",
        "elite_rb",
        "elite_wr",
        "aging_veteran",
        "young_bridge",
        "qb",
        "te",
    ):
        group_rows = [
            row for row in rows if group in str(row.get("audit_groups", "")).split("|")
        ]
        output.append(
            {
                "audit_group": group,
                "row_count": len(group_rows),
                "meaningful_rows": sum(
                    1 for row in group_rows if row["movement_magnitude"] != "none"
                ),
                "largest_abs_value_delta": _format_number(
                    max(
                        (abs(_float(row.get("value_delta"))) for row in group_rows),
                        default=0.0,
                    )
                ),
            }
        )
    return tuple(output)


def _group_count(rows: tuple[dict[str, object], ...], group: str) -> int:
    return sum(1 for row in rows if group in str(row.get("audit_groups", "")).split("|"))


def _cause_counts(rows: tuple[dict[str, object], ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        cause = str(row["movement_cause"])
        counts[cause] = counts.get(cause, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _markdown_table(
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> list[str]:
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_cell(row.get(column, "")) for column in header) + " |")
    return lines


def _split(value: object) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value or "").split("|") if part.strip())


def _key(value: object) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ").replace("'", "").replace(".", "")
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value).strip()
        if not text:
            return default
        return round(float(text), 3)
    except (TypeError, ValueError):
        return default


def _int(value: object, default: int = 0) -> int:
    try:
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _meaningful_delta(value: float) -> bool:
    return abs(value) >= 0.1


def _format_number(value: object) -> str:
    if value is None:
        return ""
    return f"{_float(value):.2f}"


def _md_cell(value: object) -> str:
    text = str(value)
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ")
    return text
