from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.nwr_outcome_release_gate_service import (
    SAME_YEAR_TARGETS,
    evaluate_probability_status,
)

APP_STATUS_VERDICT = "STATUS_ONLY_SERVICE_READY_APP_WIRING_DEFERRED"

STATUS_LABELS = {
    "in_development": "In development",
    "model_unavailable": "Model unavailable",
    "needs_data": "Needs data",
    "insufficient_evidence": "Insufficient evidence",
    "not_applicable": "Not applicable",
    "blocked_leakage_gate": "Blocked by release gate",
    "blocked_validation_gate": "Blocked by release gate",
    "blocked_calibration_gate": "Blocked by release gate",
    "blocked_confidence_gate": "Blocked by release gate",
    "blocked_documentation_gate": "Blocked by release gate",
    "blocked_operational_gate": "Blocked by release gate",
    "blocked_hq_approval": "Blocked by release gate",
    "ready_internal_only": "Internal only - not released",
}

STATUS_HELP = {
    "in_development": "Outcome model status is visible, but no probability has been released.",
    "model_unavailable": "No released outcome model is available for this target.",
    "needs_data": "More legal data is required before this target can be released.",
    "insufficient_evidence": "Current evidence is not sufficient for an app-facing release.",
    "not_applicable": "Outcome probability display is not applicable for this row or target.",
    "ready_internal_only": "Internal diagnostics exist, but this target is not app-released.",
}

TARGET_LABELS = {
    "same_year_difference_maker": "Same-year difference-maker",
    "same_year_starter": "Same-year starter",
    "same_year_useful": "Same-year useful",
    "same_year_replacement_or_bust": "Same-year replacement/bust",
    "next_year_starter": "Next-year starter",
    "multi_year_targets": "Multi-year targets",
    "hazard_windows": "Hazard windows",
}


@dataclass(frozen=True)
class OutcomeStatusDisplay:
    target: str
    target_label: str
    status_code: str
    status_label: str
    tooltip_key: str
    status_help: str
    probability_value: None = None
    probability_band: None = None
    sortable_value: None = None
    is_released: bool = False
    is_numeric: bool = False


def build_outcome_status_display(
    *,
    target: str,
    position: str | None = None,
    evidence_status: str = "in_development",
) -> OutcomeStatusDisplay:
    if evidence_status == "ready_released":
        raise ValueError("Status-only app display cannot request ready_released.")

    result = evaluate_probability_status(
        target=target,
        position=position,
        evidence_status=evidence_status,
    )
    status_code = result.status_code
    return OutcomeStatusDisplay(
        target=target,
        target_label=TARGET_LABELS.get(target, target.replace("_", " ").title()),
        status_code=status_code,
        status_label=_status_label(status_code),
        tooltip_key=result.tooltip_key,
        status_help=_status_help(status_code),
        probability_value=None,
        probability_band=None,
        sortable_value=None,
        is_released=False,
        is_numeric=False,
    )


def build_default_app_status_registry(position: str | None = None) -> list[OutcomeStatusDisplay]:
    targets = (
        *SAME_YEAR_TARGETS,
        "next_year_starter",
        "multi_year_targets",
        "hazard_windows",
    )
    return [
        build_outcome_status_display(target=target, position=position)
        for target in targets
    ]


def outcome_status_sort_value(display: OutcomeStatusDisplay) -> None:
    return display.sortable_value


def write_sprint_5ah_status_only_exports(output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    _validate_status_output_dir(output)
    output.mkdir(parents=True, exist_ok=True)

    paths = {
        "status_only_app_contract": output / "status_only_app_contract.csv",
        "status_only_target_display_registry": output
        / "status_only_target_display_registry.csv",
        "app_surface_integration_audit": output / "app_surface_integration_audit.csv",
        "blocked_numeric_probability_paths": output / "blocked_numeric_probability_paths.csv",
        "readme": output / "README_SPRINT_5AH.md",
    }
    _write_csv(paths["status_only_app_contract"], status_only_app_contract_rows())
    _write_csv(
        paths["status_only_target_display_registry"],
        status_only_target_display_registry_rows(),
    )
    _write_csv(paths["app_surface_integration_audit"], app_surface_integration_audit_rows())
    _write_csv(
        paths["blocked_numeric_probability_paths"],
        blocked_numeric_probability_path_rows(),
    )
    paths["readme"].write_text(_readme_text(), encoding="utf-8")
    return paths


def status_only_app_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "field": "status_code",
            "allowed_value": "status_text_only",
            "app_safe": "yes",
            "notes": "Status code can be displayed but cannot imply a released probability.",
        },
        {
            "field": "status_label",
            "allowed_value": "text_only",
            "app_safe": "yes",
            "notes": "Examples include In development, Needs data, or Not applicable.",
        },
        {
            "field": "status_help",
            "allowed_value": "text_only",
            "app_safe": "yes",
            "notes": "Tooltip/help copy only.",
        },
        {
            "field": "probability_value",
            "allowed_value": "null",
            "app_safe": "yes",
            "notes": "Always null in the Sprint 5AH status-only adapter.",
        },
        {
            "field": "probability_band",
            "allowed_value": "null",
            "app_safe": "yes",
            "notes": "Probability bands remain blocked.",
        },
        {
            "field": "sortable_value",
            "allowed_value": "null",
            "app_safe": "yes",
            "notes": "No hidden numeric sorting by outcome status.",
        },
        {
            "field": "is_released",
            "allowed_value": "false",
            "app_safe": "yes",
            "notes": "Default app status config cannot reach ready_released.",
        },
        {
            "field": "is_numeric",
            "allowed_value": "false",
            "app_safe": "yes",
            "notes": "Display is status-only and nonnumeric.",
        },
    ]


def status_only_target_display_registry_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for display in build_default_app_status_registry():
        rows.append(
            {
                "target": display.target,
                "target_label": display.target_label,
                "status_code": display.status_code,
                "status_label": display.status_label,
                "probability_value": "null",
                "probability_band": "null",
                "sortable_value": "null",
                "is_released": "false",
                "is_numeric": "false",
                "notes": display.status_help,
            }
        )
    rows.append(
        {
            "target": "kicker_rows",
            "target_label": "Kicker rows",
            "status_code": "not_applicable",
            "status_label": "Not applicable",
            "probability_value": "null",
            "probability_band": "null",
            "sortable_value": "null",
            "is_released": "false",
            "is_numeric": "false",
            "notes": "Kickers do not receive outcome probability display.",
        }
    )
    return rows


def app_surface_integration_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "surface": "rankings_page",
            "integration_status": "deferred",
            "active_app_file_changed": "no",
            "risk": "low",
            "reason": (
                "Avoid status wiring on ranking surface before adversarial status-only audit."
            ),
        },
        {
            "surface": "player_detail_card",
            "integration_status": "deferred",
            "active_app_file_changed": "no",
            "risk": "low",
            "reason": "Service contract is ready; active component wiring deferred.",
        },
        {
            "surface": "live_draft_room",
            "integration_status": "deferred",
            "active_app_file_changed": "no",
            "risk": "low",
            "reason": "Draft-room decision surfaces must not consume model status until audited.",
        },
        {
            "surface": "status_display_service",
            "integration_status": "service_contract_ready",
            "active_app_file_changed": "no",
            "risk": "low",
            "reason": "Adapter returns status text only and null numeric fields.",
        },
    ]


def blocked_numeric_probability_path_rows() -> list[dict[str, str]]:
    return [
        {
            "path": "numeric_probability",
            "blocked": "yes",
            "enforced_by": "probability_value_null",
            "notes": "Status-only adapter never returns a numeric probability.",
        },
        {
            "path": "probability_band",
            "blocked": "yes",
            "enforced_by": "probability_band_null",
            "notes": "Bands remain blocked until real release gates pass.",
        },
        {
            "path": "hidden_sortable_value",
            "blocked": "yes",
            "enforced_by": "sortable_value_null",
            "notes": "Rankings cannot sort by hidden outcome model values.",
        },
        {
            "path": "internal_model_outputs",
            "blocked": "yes",
            "enforced_by": "no_internal_model_import",
            "notes": "Adapter mirrors release-gate status only.",
        },
        {
            "path": "app_probability_table",
            "blocked": "yes",
            "enforced_by": "no_app_table_export",
            "notes": "No app-readable real probability table is created.",
        },
    ]


def _status_label(status_code: str) -> str:
    if status_code in STATUS_LABELS:
        return STATUS_LABELS[status_code]
    if status_code.startswith("blocked_"):
        return "Blocked by release gate"
    raise ValueError(f"Unknown display status code: {status_code}")


def _status_help(status_code: str) -> str:
    if status_code in STATUS_HELP:
        return STATUS_HELP[status_code]
    if status_code.startswith("blocked_"):
        return "A release gate blocks this outcome from app-facing probability display."
    raise ValueError(f"Unknown display status code: {status_code}")


def _validate_status_output_dir(output_dir: Path) -> None:
    lower_parts = {part.lower() for part in output_dir.parts}
    if lower_parts.intersection({"app", "pages", "streamlit_app.py"}):
        raise ValueError("Status-only exports must not be written to app paths.")
    normalized = str(output_dir).replace("\\", "/").lower()
    blocked_fragments = (
        "current_value/latest",
        "rankings",
        "decision_board",
        "app_probability",
        "player_probabilities",
    )
    if any(fragment in normalized for fragment in blocked_fragments):
        raise ValueError("Status-only exports must not target app/ranking outputs.")


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    fieldnames = tuple(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _readme_text() -> str:
    return """# Sprint 5AH Status-Only App Integration

Verdict: `STATUS_ONLY_SERVICE_READY_APP_WIRING_DEFERRED`

This local export documents the status-only outcome-probability display contract.
The service is app-safe because it returns text status fields with null probability
value, null probability band, null sortable value, `is_released=false`, and
`is_numeric=false`.

Active app page wiring is deferred until the status-only contract receives an
adversarial audit. Real production/app probabilities remain blocked.
"""
