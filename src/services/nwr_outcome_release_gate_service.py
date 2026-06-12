from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RELEASE_GATES = (
    "leakage_gate",
    "validation_gate",
    "calibration_gate",
    "confidence_gate",
    "documentation_gate",
    "operational_gate",
    "hq_approval_gate",
)

STATUS_PRECEDENCE = (
    ("leakage_gate", "blocked_leakage_gate"),
    ("validation_gate", "blocked_validation_gate"),
    ("calibration_gate", "blocked_calibration_gate"),
    ("confidence_gate", "blocked_confidence_gate"),
    ("documentation_gate", "blocked_documentation_gate"),
    ("operational_gate", "blocked_operational_gate"),
    ("hq_approval_gate", "blocked_hq_approval"),
)

PROBABILITY_STATUS_CODES = (
    "in_development",
    "model_unavailable",
    "needs_data",
    "insufficient_evidence",
    "not_applicable",
    "blocked_leakage_gate",
    "blocked_validation_gate",
    "blocked_calibration_gate",
    "blocked_confidence_gate",
    "blocked_documentation_gate",
    "blocked_operational_gate",
    "blocked_hq_approval",
    "ready_internal_only",
    "ready_released",
)

SAME_YEAR_TARGETS = (
    "same_year_difference_maker",
    "same_year_starter",
    "same_year_useful",
    "same_year_replacement_or_bust",
)

BLOCKED_TARGETS = (
    "next_year_starter",
    "multi_year_targets",
    "hazard_windows",
    "injury_lost_risk",
    "ambiguous_risk",
)

KICKER_POSITIONS = ("K", "PK")


@dataclass(frozen=True)
class ProbabilityStatusResult:
    target: str
    status_code: str
    status_text: str
    tooltip_key: str
    confidence_label: str
    probability_payload: float | None = None
    probability_band: str | None = None
    hidden_sortable_probability: float | None = None
    app_readable_payload: bool = False


def default_release_gates(value: bool = False) -> dict[str, bool]:
    return {gate: value for gate in RELEASE_GATES}


def evaluate_probability_status(
    *,
    target: str,
    position: str | None = None,
    release_gates: Mapping[str, bool] | None = None,
    requested_probability: float | None = None,
    evidence_status: str = "in_development",
) -> ProbabilityStatusResult:
    if position and position.upper() in KICKER_POSITIONS:
        return _blocked_result(target=target, status_code="not_applicable")

    if target in BLOCKED_TARGETS:
        status = "blocked_validation_gate" if target == "next_year_starter" else "not_applicable"
        return _blocked_result(target=target, status_code=status)

    if target not in SAME_YEAR_TARGETS:
        return _blocked_result(target=target, status_code="not_applicable")

    if release_gates is None:
        return _blocked_result(target=target, status_code=evidence_status)

    normalized_gates = _normalize_gates(release_gates)
    for gate, status_code in STATUS_PRECEDENCE:
        if not normalized_gates[gate]:
            return _blocked_result(target=target, status_code=status_code)

    probability = _validate_probability(requested_probability)
    return ProbabilityStatusResult(
        target=target,
        status_code="ready_released",
        status_text="Ready released",
        tooltip_key="outcome_probability.ready_released",
        confidence_label="Released",
        probability_payload=probability,
        probability_band=None,
        hidden_sortable_probability=probability,
        app_readable_payload=True,
    )


def assert_monotonic_same_year_probabilities(probabilities: Mapping[str, float]) -> None:
    required = (
        "same_year_difference_maker",
        "same_year_starter",
        "same_year_useful",
    )
    missing = [target for target in required if target not in probabilities]
    if missing:
        raise ValueError("Missing same-year monotonic probability targets: " + ", ".join(missing))
    if not (
        probabilities["same_year_difference_maker"]
        <= probabilities["same_year_starter"]
        <= probabilities["same_year_useful"]
    ):
        raise ValueError(
            "Same-year probabilities must satisfy Difference-maker <= Starter <= Useful."
        )


def write_sprint_5af_release_gate_contract(output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    paths = {
        "release_gate_registry": output / "release_gate_registry.csv",
        "probability_status_codes": output / "probability_status_codes.csv",
        "target_release_registry_draft": output / "target_release_registry_draft.csv",
        "status_precedence_rules": output / "status_precedence_rules.csv",
        "app_safe_display_contract": output / "app_safe_display_contract.csv",
        "blocked_probability_paths": output / "blocked_probability_paths.csv",
        "readme": output / "README_SPRINT_5AF.md",
    }
    _write_csv(paths["release_gate_registry"], release_gate_registry_rows())
    _write_csv(paths["probability_status_codes"], probability_status_code_rows())
    _write_csv(paths["target_release_registry_draft"], target_release_registry_rows())
    _write_csv(paths["status_precedence_rules"], status_precedence_rows())
    _write_csv(paths["app_safe_display_contract"], app_safe_display_rows())
    _write_csv(paths["blocked_probability_paths"], blocked_probability_path_rows())
    paths["readme"].write_text(_readme_text(), encoding="utf-8")
    return paths


def release_gate_registry_rows() -> list[dict[str, str]]:
    gate_notes = {
        "leakage_gate": "Final leakage audit must pass.",
        "validation_gate": "Out-of-time validation evidence must pass release thresholds.",
        "calibration_gate": "Calibration stability must pass release thresholds.",
        "confidence_gate": "Confidence/display gate must be approved.",
        "documentation_gate": "Model card, release policy, and source lineage must be complete.",
        "operational_gate": "Monitoring, rollback, and QA controls must be ready.",
        "hq_approval_gate": "Explicit HQ approval is required.",
    }
    return [
        {
            "gate": gate,
            "required_for_ready_released": "yes",
            "default_state": "failed",
            "failure_status": dict(STATUS_PRECEDENCE)[gate],
            "notes": gate_notes[gate],
        }
        for gate in RELEASE_GATES
    ]


def probability_status_code_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for status in PROBABILITY_STATUS_CODES:
        released = status == "ready_released"
        rows.append(
            {
                "status_code": status,
                "numeric_probability_allowed": "yes" if released else "no",
                "probability_band_allowed": "yes" if released else "no",
                "hidden_sort_value_allowed": "yes" if released else "no",
                "app_display_text": _status_text(status),
                "tooltip_key": f"outcome_probability.{status}",
                "notes": "Requires all gates true."
                if released
                else "Returns null probability payload.",
            }
        )
    return rows


def target_release_registry_rows() -> list[dict[str, str]]:
    rows = [
        {
            "target": target,
            "target_family": "same_year",
            "release_status": "ready_internal_only",
            "app_release_allowed": "no",
            "default_app_status": "in_development",
            "notes": "Draft registry only; all gates must pass before ready_released.",
        }
        for target in SAME_YEAR_TARGETS
    ]
    rows.extend(
        {
            "target": target,
            "target_family": "blocked_or_future",
            "release_status": "blocked_validation_gate"
            if target == "next_year_starter"
            else "not_applicable",
            "app_release_allowed": "no",
            "default_app_status": "blocked_validation_gate"
            if target == "next_year_starter"
            else "not_applicable",
            "notes": "Not released in Sprint 5AF.",
        }
        for target in BLOCKED_TARGETS
    )
    return rows


def status_precedence_rows() -> list[dict[str, str]]:
    rows = [
        {
            "precedence_rank": str(index),
            "failed_gate": gate,
            "status_code": status_code,
            "probability_payload": "null",
            "notes": "First failed gate controls status.",
        }
        for index, (gate, status_code) in enumerate(STATUS_PRECEDENCE, start=1)
    ]
    rows.append(
        {
            "precedence_rank": str(len(STATUS_PRECEDENCE) + 1),
            "failed_gate": "none",
            "status_code": "ready_released",
            "probability_payload": "allowed_only_after_all_gates_pass",
            "notes": "Difference-maker <= Starter <= Useful must also pass before future release.",
        }
    )
    return rows


def app_safe_display_rows() -> list[dict[str, str]]:
    return [
        {
            "display_rule": "unreleased_numeric_probability",
            "allowed": "no",
            "required_behavior": "show_status_text_only",
            "notes": "No numeric probability, probability band, or hidden sortable value.",
        },
        {
            "display_rule": "released_numeric_probability",
            "allowed": "only_if_ready_released",
            "required_behavior": "show_probability_from_release_payload",
            "notes": "Requires all gates true and monotonic same-year checks.",
        },
        {
            "display_rule": "kickers",
            "allowed": "status_only",
            "required_behavior": "not_applicable",
            "notes": "Kickers do not receive outcome probabilities.",
        },
        {
            "display_rule": "debug_fields",
            "allowed": "internal_debug_only",
            "required_behavior": "hide_from_normal_app_users",
            "notes": "No debug leakage into public/player-facing UI.",
        },
        {
            "display_rule": "sorting",
            "allowed": "no_for_unreleased",
            "required_behavior": "sort_unreleased_as_null",
            "notes": "Unreleased statuses must not be sorted as numeric probability values.",
        },
    ]


def blocked_probability_path_rows() -> list[dict[str, str]]:
    return [
        {
            "path": "internal_model_outputs_to_app",
            "blocked": "yes",
            "reason": "Internal outputs cannot become app probabilities without all release gates.",
        },
        {
            "path": "player_facing_probability_export",
            "blocked": "yes",
            "reason": "No per-player probability export is allowed in Sprint 5AF.",
        },
        {
            "path": "app_readable_probability_table",
            "blocked": "yes",
            "reason": "No app-readable real probability table is created.",
        },
        {
            "path": "ranking_or_sorting_by_probability",
            "blocked": "yes",
            "reason": "Outcome statuses must not drive rankings or decision automation.",
        },
        {
            "path": "promoted_model_artifact",
            "blocked": "yes",
            "reason": "No model artifact is promoted or released.",
        },
    ]


def _blocked_result(target: str, status_code: str) -> ProbabilityStatusResult:
    if status_code not in PROBABILITY_STATUS_CODES:
        raise ValueError(f"Unknown probability status code: {status_code}")
    return ProbabilityStatusResult(
        target=target,
        status_code=status_code,
        status_text=_status_text(status_code),
        tooltip_key=f"outcome_probability.{status_code}",
        confidence_label=_confidence_label(status_code),
        probability_payload=None,
        probability_band=None,
        hidden_sortable_probability=None,
        app_readable_payload=False,
    )


def _normalize_gates(gates: Mapping[str, bool]) -> dict[str, bool]:
    unknown = sorted(set(gates) - set(RELEASE_GATES))
    if unknown:
        raise ValueError("Unknown release gates: " + ", ".join(unknown))
    return {gate: bool(gates.get(gate, False)) for gate in RELEASE_GATES}


def _validate_probability(probability: float | None) -> float | None:
    if probability is None:
        return None
    value = float(probability)
    if not 0 <= value <= 1:
        raise ValueError("Released probability must be between 0 and 1.")
    return value


def _status_text(status_code: str) -> str:
    text = {
        "in_development": "In development",
        "model_unavailable": "Model unavailable",
        "needs_data": "Needs data",
        "insufficient_evidence": "Insufficient evidence",
        "not_applicable": "Not applicable",
        "ready_internal_only": "Internal only",
        "ready_released": "Ready released",
    }.get(status_code)
    if text:
        return text
    if status_code.startswith("blocked_"):
        return "Blocked"
    raise ValueError(f"Unknown probability status code: {status_code}")


def _confidence_label(status_code: str) -> str:
    return {
        "in_development": "In development",
        "model_unavailable": "Model unavailable",
        "needs_data": "Needs data",
        "insufficient_evidence": "Insufficient evidence",
        "not_applicable": "Not applicable",
        "ready_internal_only": "In development",
        "ready_released": "Released",
    }.get(status_code, "Model unavailable")


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
    return """# Sprint 5AF Release Gate Status Contract

Verdict: `RELEASE_GATE_STATUS_CONTRACT_READY`

This local export defines the future app-safe probability status contract. It does not wire any
real probabilities into the app and does not create an app-readable probability table.

Real probabilities remain blocked unless every release gate passes and the target is released.
Every unreleased or blocked status returns a null probability payload.
"""
