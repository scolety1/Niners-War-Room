from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_ROOT = REPO_ROOT / "docs" / "hq" / "data_sources" / "nfl_usage" / "review_artifacts"

LIVE_SMOKE_PATH = REVIEW_ROOT / "live_smoke" / "nfl_usage_live_smoke_summary_v0.csv"
FIELD_INVENTORY_PATH = (
    REVIEW_ROOT / "live_field_inventory" / "nfl_usage_live_field_inventory_v0.csv"
)
FIELD_GAP_PATH = REVIEW_ROOT / "live_field_inventory" / "nfl_usage_live_field_gap_report_v0.csv"
PROXY_TRUE_PATH = REVIEW_ROOT / "nfl_usage_proxy_vs_true_final_report_v0.csv"
VALIDATION_PATH = REVIEW_ROOT / "validation" / "nfl_usage_live_validation_report_v0.csv"
QUARANTINE_PATH = REVIEW_ROOT / "validation" / "nfl_usage_live_quarantine_report_v0.csv"
PROMOTION_CANDIDATES_PATH = (
    REVIEW_ROOT.parent / "NWR_NFL_USAGE_FIELD_PROMOTION_CANDIDATES_V0_20260624.csv"
)


@dataclass(frozen=True)
class NflUsageEvidenceReviewData:
    smoke: pd.DataFrame
    field_inventory: pd.DataFrame
    field_gaps: pd.DataFrame
    proxy_true: pd.DataFrame
    validation: pd.DataFrame
    quarantine: pd.DataFrame
    promotion_candidates: pd.DataFrame
    summary: dict[str, object]


def load_nfl_usage_evidence_review_data(
    review_root: Path = REVIEW_ROOT,
) -> NflUsageEvidenceReviewData:
    smoke = _read_csv(review_root / "live_smoke" / LIVE_SMOKE_PATH.name)
    field_inventory = _read_csv(
        review_root / "live_field_inventory" / FIELD_INVENTORY_PATH.name
    )
    field_gaps = _read_csv(review_root / "live_field_inventory" / FIELD_GAP_PATH.name)
    proxy_true = _read_csv(review_root / PROXY_TRUE_PATH.name)
    validation = _read_csv(review_root / "validation" / VALIDATION_PATH.name)
    quarantine = _read_csv(review_root / "validation" / QUARANTINE_PATH.name)
    promotion_candidates = _read_csv(PROMOTION_CANDIDATES_PATH)
    return NflUsageEvidenceReviewData(
        smoke=smoke,
        field_inventory=field_inventory,
        field_gaps=field_gaps,
        proxy_true=proxy_true,
        validation=validation,
        quarantine=quarantine,
        promotion_candidates=promotion_candidates,
        summary=build_summary_counts(
            smoke,
            field_inventory,
            field_gaps,
            validation,
            quarantine,
        ),
    )


def build_summary_counts(
    smoke: pd.DataFrame,
    field_inventory: pd.DataFrame,
    field_gaps: pd.DataFrame,
    validation: pd.DataFrame,
    quarantine: pd.DataFrame,
) -> dict[str, object]:
    return {
        "sources_inventoried": int(len(smoke)),
        "sources_green": _count_status(smoke, "status", "GREEN"),
        "sources_quarantined_or_skipped": int(
            len(smoke) - _count_status(smoke, "status", "GREEN")
        ),
        "true_factual_fields": _count_status(
            field_inventory,
            "field_type",
            "TRUE_FACTUAL_FIELD",
        ),
        "derived_proxy_fields": _count_status(field_inventory, "field_type", "DERIVED_PROXY"),
        "licensed_data_gaps": _count_status(field_gaps, "licensed_data_gap", "yes"),
        "field_quarantines": int(len(quarantine)),
        "validation_green": _all_green(validation),
        "app_wiring_allowed": _all_no(field_inventory, "app_wiring_allowed"),
        "model_input_allowed": _all_no(field_inventory, "model_input_allowed"),
        "raw_data_loaded": "no",
    }


def table_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    existing = [column for column in columns if column in frame.columns]
    return frame.loc[:, existing].copy()


def export_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False)


def _count_status(frame: pd.DataFrame, column: str, value: str) -> int:
    if column not in frame.columns:
        return 0
    return int(frame[column].astype(str).str.lower().eq(value.lower()).sum())


def _all_green(frame: pd.DataFrame) -> str:
    if "validation_status" not in frame.columns:
        return "missing"
    return "yes" if frame["validation_status"].astype(str).eq("GREEN").all() else "no"


def _all_no(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return "missing"
    return "no" if frame[column].astype(str).str.lower().eq("no").all() else "mixed"
