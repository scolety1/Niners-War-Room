from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_sanity_fixture_dry_run_service import (
    DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
)

PHASE_4_PREVIEW_OUTPUTS_PATH = Path(
    "local_exports/model_v4/audit_packets/"
    "model_v4_phase4_external_audit_20260516T033806Z/"
    "local_exports/model_v4/review_only_latest/v4_preview_outputs.csv"
)
PHASE_5_MOVEMENT_AUDIT_CSV_PATH = Path("docs/model_v4/PHASE_5_MOVEMENT_AUDIT.csv")
PHASE_5_MOVEMENT_AUDIT_MD_PATH = Path("docs/model_v4/PHASE_5_MOVEMENT_AUDIT.md")

COMPONENTS = (
    "production",
    "first_down_scoring_fit",
    "usage_opportunity",
    "snap_proxy_role",
    "projection",
    "age_dropoff",
    "young_player_prior",
)

MOVEMENT_HEADER = (
    "player",
    "position",
    "nfl_team",
    "truth_set_group",
    "audit_groups",
    "lifecycle",
    "phase4_rank",
    "phase5_rank",
    "rank_delta",
    "phase4_dynasty_asset_value",
    "phase5_dynasty_asset_value",
    "value_delta",
    "movement_magnitude",
    "movement_cause",
    "phase4_confidence_label",
    "phase5_confidence_label",
    "value_basis",
    "missing_value_components",
    "production_delta",
    "first_down_delta",
    "usage_delta",
    "snap_delta",
    "projection_delta",
    "age_delta",
    "young_prior_delta",
    "added_warnings",
    "removed_warnings",
    "review_note",
)


@dataclass(frozen=True)
class ModelV4MovementAuditResult:
    csv_path: Path
    markdown_path: Path
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def run_model_v4_movement_audit(
    *,
    phase4_preview_path: str | Path = PHASE_4_PREVIEW_OUTPUTS_PATH,
    current_preview_path: str | Path = DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    output_csv_path: str | Path = PHASE_5_MOVEMENT_AUDIT_CSV_PATH,
    output_md_path: str | Path = PHASE_5_MOVEMENT_AUDIT_MD_PATH,
) -> ModelV4MovementAuditResult:
    phase4_rows = _ranked(_read_dicts(Path(phase4_preview_path)))
    current_rows = _ranked(_read_dicts(Path(current_preview_path)))
    rows = tuple(
        _movement_row(player_key, phase4_rows.get(player_key), current_rows.get(player_key))
        for player_key in sorted(
            set(phase4_rows) | set(current_rows),
            key=lambda key: (
                _int((current_rows.get(key) or phase4_rows.get(key) or {}).get("rank"), 9999),
                key,
            ),
        )
    )
    summary = _summary(rows, phase4_preview_path=Path(phase4_preview_path))
    csv_path = Path(output_csv_path)
    markdown_path = Path(output_md_path)
    _write_csv(csv_path, MOVEMENT_HEADER, rows)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_markdown(summary, rows), encoding="utf-8")
    return ModelV4MovementAuditResult(
        csv_path=csv_path,
        markdown_path=markdown_path,
        rows=rows,
        summary=summary,
    )


def _movement_row(
    player_key: str,
    previous: dict[str, object] | None,
    current: dict[str, object] | None,
) -> dict[str, object]:
    row = current or previous or {}
    previous_components = _component_scores(previous)
    current_components = _component_scores(current)
    component_deltas = {
        component: round(
            _float(current_components.get(component))
            - _float(previous_components.get(component)),
            3,
        )
        for component in COMPONENTS
    }
    value_delta = round(
        _float((current or {}).get("dynasty_asset_value"))
        - _float((previous or {}).get("dynasty_asset_value")),
        3,
    )
    rank_delta = _int((current or {}).get("rank")) - _int((previous or {}).get("rank"))
    warning_delta = _warning_delta(previous, current)
    cause = _movement_cause(
        previous=previous,
        current=current,
        component_deltas=component_deltas,
        value_delta=value_delta,
        rank_delta=rank_delta,
        warning_delta=warning_delta,
    )
    magnitude = _movement_magnitude(value_delta, rank_delta)
    return {
        "player": row.get("player", ""),
        "position": row.get("position", ""),
        "nfl_team": row.get("nfl_team", ""),
        "truth_set_group": row.get("truth_set_group", ""),
        "audit_groups": "|".join(_audit_groups(row)),
        "lifecycle": row.get("lifecycle", ""),
        "phase4_rank": (previous or {}).get("rank", ""),
        "phase5_rank": (current or {}).get("rank", ""),
        "rank_delta": rank_delta if previous and current else "",
        "phase4_dynasty_asset_value": _format_number(
            (previous or {}).get("dynasty_asset_value")
        ),
        "phase5_dynasty_asset_value": _format_number(
            (current or {}).get("dynasty_asset_value")
        ),
        "value_delta": _format_number(value_delta) if previous and current else "",
        "movement_magnitude": magnitude,
        "movement_cause": cause,
        "phase4_confidence_label": (previous or {}).get("confidence_label", ""),
        "phase5_confidence_label": (current or {}).get("confidence_label", ""),
        "value_basis": (current or {}).get("value_basis", ""),
        "missing_value_components": (current or {}).get("missing_value_components", ""),
        "production_delta": _format_number(component_deltas["production"]),
        "first_down_delta": _format_number(component_deltas["first_down_scoring_fit"]),
        "usage_delta": _format_number(component_deltas["usage_opportunity"]),
        "snap_delta": _format_number(component_deltas["snap_proxy_role"]),
        "projection_delta": _format_number(component_deltas["projection"]),
        "age_delta": _format_number(component_deltas["age_dropoff"]),
        "young_prior_delta": _format_number(component_deltas["young_player_prior"]),
        "added_warnings": "|".join(warning_delta["added"]),
        "removed_warnings": "|".join(warning_delta["removed"]),
        "review_note": _review_note(cause, magnitude, row),
    }


def _movement_cause(
    *,
    previous: dict[str, object] | None,
    current: dict[str, object] | None,
    component_deltas: dict[str, float],
    value_delta: float,
    rank_delta: int,
    warning_delta: dict[str, tuple[str, ...]],
) -> str:
    if previous is None:
        return "identity repair"
    if current is None:
        return "identity repair"
    if (
        abs(value_delta) < 1.0
        and abs(rank_delta) < 3
        and not warning_delta["added"]
        and not warning_delta["removed"]
    ):
        return "no material movement"
    if (
        str(previous.get("position") or "") != str(current.get("position") or "")
        or str(previous.get("nfl_team") or "") != str(current.get("nfl_team") or "")
    ):
        return "identity repair"
    if _meaningful_delta(component_deltas["production"]):
        return "production import repair"
    if _meaningful_delta(component_deltas["first_down_scoring_fit"]):
        return "first-down import repair"
    if _meaningful_delta(component_deltas["usage_opportunity"]):
        return "usage repair"
    if _meaningful_delta(component_deltas["snap_proxy_role"]):
        return "snap repair"
    if _meaningful_delta(component_deltas["projection"]) or _projection_warning_changed(
        warning_delta
    ):
        return "projection/first-down estimate repair"
    if str(previous.get("confidence_label") or "") != str(current.get("confidence_label") or ""):
        return "warning/confidence label change"
    if str(current.get("value_basis") or "") in {
        "evidence_adjusted_missing_not_zero",
        "insufficient_evidence_not_rankable",
    }:
        return "normalization repair"
    if warning_delta["added"] or warning_delta["removed"]:
        return "warning/confidence label change"
    return "no material movement"


def _movement_magnitude(value_delta: float, rank_delta: int) -> str:
    abs_value = abs(value_delta)
    abs_rank = abs(rank_delta)
    if abs_value >= 8.0 or abs_rank >= 12:
        return "large"
    if abs_value >= 3.0 or abs_rank >= 5:
        return "medium"
    if abs_value >= 1.0 or abs_rank >= 3:
        return "small"
    return "none"


def _review_note(cause: str, magnitude: str, row: dict[str, object]) -> str:
    if cause == "normalization repair":
        return "Missing established-veteran evidence is no longer treated as zero value."
    if cause == "projection/first-down estimate repair":
        return (
            "Projection component changed after first-down estimates and missing "
            "projection guardrails."
        )
    if cause == "identity repair":
        return "Player identity/team/position presence changed between snapshots."
    if magnitude in {"medium", "large"}:
        return "Review receipts before any promotion."
    if "young" in str(row.get("lifecycle") or "").lower():
        return "Young bridge row remains review-only."
    return "No promotion; v4 remains review-only."


def _summary(
    rows: tuple[dict[str, object], ...],
    *,
    phase4_preview_path: Path,
) -> dict[str, object]:
    return {
        "review_status": "review_only",
        "phase4_baseline": str(phase4_preview_path),
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
        "niners_roster_rows": _group_count(rows, "niners_roster"),
        "elite_rb_rows": _group_count(rows, "elite_rb"),
        "elite_wr_rows": _group_count(rows, "elite_wr"),
        "aging_veteran_rows": _group_count(rows, "aging_veteran"),
        "young_bridge_rows": _group_count(rows, "young_bridge"),
        "qb_rows": _group_count(rows, "qb"),
        "te_rows": _group_count(rows, "te"),
        "active_rankings_promoted": False,
    }


def _markdown(summary: dict[str, object], rows: tuple[dict[str, object], ...]) -> str:
    meaningful_rows = tuple(row for row in rows if row["movement_magnitude"] != "none")
    lines = [
        "# Phase 5 Movement Audit",
        "",
        "This report compares the regenerated Phase 5 v4 preview against the preserved "
        "Phase 4 external-audit preview. It is review-only and does not promote app rankings.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Cause Counts",
            "",
        ]
    )
    for cause, count in _cause_counts(rows):
        lines.append(f"- {cause}: {count}")
    lines.extend(
        [
            "",
            "## Meaningful Movements",
            "",
        ]
    )
    table_header = (
        "player",
        "position",
        "audit_groups",
        "phase4_rank",
        "phase5_rank",
        "rank_delta",
        "phase4_dynasty_asset_value",
        "phase5_dynasty_asset_value",
        "value_delta",
        "movement_magnitude",
        "movement_cause",
        "review_note",
    )
    lines.extend(_markdown_table(table_header, meaningful_rows[:60]))
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


def _component_scores(row: dict[str, object] | None) -> dict[str, object]:
    if row is None:
        return {}
    try:
        parsed = json.loads(str(row.get("component_scores") or "{}"))
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


def _projection_warning_changed(warning_delta: dict[str, tuple[str, ...]]) -> bool:
    return any(
        "projection" in warning or "first_down" in warning
        for warning in (*warning_delta["added"], *warning_delta["removed"])
    )


def _meaningful_delta(value: float) -> bool:
    return abs(value) >= 0.1


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
        group_rows = [row for row in rows if group in str(row.get("audit_groups", "")).split("|")]
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


def _format_number(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return f"{float(text):.2f}"
    except ValueError:
        return text


def _md_cell(value: object) -> str:
    return str(value or "").replace("|", "<br>").replace("\n", " ")
