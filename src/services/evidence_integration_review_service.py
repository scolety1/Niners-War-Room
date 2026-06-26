from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_ROOT = REPO_ROOT / "docs" / "hq" / "integration"
REGISTRY_PATH = INTEGRATION_ROOT / "evidence_status_registry_v1_20260626.csv"

REGISTRY_TABLE_COLUMNS = [
    "evidence_lane",
    "current_status",
    "review_only",
    "model_input_allowed",
    "app_wiring_allowed",
    "training_allowed",
    "approved_by_human",
    "display_only_allowed",
    "known_blockers",
    "next_gate",
]
BLOCKER_TABLE_COLUMNS = [
    "evidence_lane",
    "current_status",
    "known_blockers",
    "next_gate",
]
NEXT_GATE_TABLE_COLUMNS = [
    "evidence_lane",
    "next_gate",
    "known_blockers",
    "notes",
]


@dataclass(frozen=True)
class EvidenceIntegrationReviewData:
    registry: pd.DataFrame
    blockers: pd.DataFrame
    next_gates: pd.DataFrame
    guardrails: pd.DataFrame
    summary: dict[str, object]


def load_evidence_integration_review_data(
    registry_path: Path = REGISTRY_PATH,
) -> EvidenceIntegrationReviewData:
    registry = pd.read_csv(registry_path, keep_default_na=False)
    blockers = registry.loc[
        registry["known_blockers"].astype(str).str.strip().ne("")
        | registry["current_status"].astype(str).isin(["BLOCKED", "RED", "YELLOW"])
    ].copy()
    next_gates = registry.loc[
        registry["next_gate"].astype(str).str.strip().ne("")
    ].copy()
    return EvidenceIntegrationReviewData(
        registry=registry,
        blockers=blockers,
        next_gates=next_gates,
        guardrails=build_guardrail_checklist(registry),
        summary=build_summary(registry),
    )


def build_summary(registry: pd.DataFrame) -> dict[str, object]:
    return {
        "evidence_lanes": int(len(registry)),
        "review_only_lanes": _count_yes(registry, "review_only"),
        "model_input_enabled": _any_yes(registry, "model_input_allowed"),
        "app_wiring_enabled": _any_yes(registry, "app_wiring_allowed"),
        "training_enabled": _any_yes(registry, "training_allowed"),
        "raw_data_tracked": _any_yes(registry, "raw_data_tracked"),
        "blocked_lanes": int(registry["current_status"].astype(str).eq("BLOCKED").sum()),
        "display_only_lanes": _count_yes(registry, "display_only_allowed"),
    }


def build_guardrail_checklist(registry: pd.DataFrame) -> pd.DataFrame:
    checks = [
        (
            "Model input enabled",
            "GREEN" if not _has_yes(registry, "model_input_allowed") else "RED",
            "No registry row may enable active model input in this lane.",
        ),
        (
            "Decision-page app wiring enabled",
            "GREEN" if not _has_yes(registry, "app_wiring_allowed") else "RED",
            (
                "Evidence must not feed rankings, Drafting Mode, Player Compare, "
                "Trading Lab, Post-Draft, or model features."
            ),
        ),
        (
            "Training enabled",
            "GREEN" if not _has_yes(registry, "training_allowed") else "RED",
            "Review/proxy evidence is not training truth.",
        ),
        (
            "Raw data tracked",
            "GREEN" if not _has_yes(registry, "raw_data_tracked") else "RED",
            "Raw CFBD, nflverse, local runtime, and shared-cache payloads must remain untracked.",
        ),
        (
            "Unified Universe app wiring",
            _lane_status(registry, "Unified Player Universe Review V1", expected_app_wiring="no"),
            "Unified Universe remains review-only until a later source-quality/app-wiring gate.",
        ),
        (
            "RotoWire live collection",
            "GREEN"
            if _lane_value(registry, "RotoWire Usage Lane", "current_status") == "BLOCKED"
            else "YELLOW",
            "RotoWire scraping remains blocked/manual.",
        ),
    ]
    return pd.DataFrame(checks, columns=["check", "status", "meaning"])


def table_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    existing = [column for column in columns if column in frame.columns]
    return frame.loc[:, existing].copy()


def export_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def _count_yes(frame: pd.DataFrame, column: str) -> int:
    if column not in frame.columns:
        return 0
    return int(frame[column].astype(str).str.lower().eq("yes").sum())


def _any_yes(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return "missing"
    return "yes" if _has_yes(frame, column) else "no"


def _has_yes(frame: pd.DataFrame, column: str) -> bool:
    if column not in frame.columns:
        return False
    return bool(frame[column].astype(str).str.lower().eq("yes").any())


def _lane_value(registry: pd.DataFrame, lane: str, column: str) -> str:
    if column not in registry.columns:
        return ""
    matches = registry.loc[registry["evidence_lane"].astype(str).eq(lane), column]
    if matches.empty:
        return ""
    return str(matches.iloc[0])


def _lane_status(
    registry: pd.DataFrame,
    lane: str,
    *,
    expected_app_wiring: str,
) -> str:
    return (
        "GREEN"
        if _lane_value(registry, lane, "app_wiring_allowed").lower()
        == expected_app_wiring
        else "YELLOW"
    )
