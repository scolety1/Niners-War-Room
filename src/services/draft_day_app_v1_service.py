from __future__ import annotations

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.services.market_baseline_registry import get_market_baseline_page_usage
from src.services.market_baseline_service import (
    DISPLAY_LABEL as MARKET_BASELINE_DISPLAY_LABEL,
)
from src.services.market_baseline_service import (
    compute_market_sanity_flags,
    load_market_freshness,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BOARD_FILE_NAME = "FINAL_DRAFT_BOARD_V1_FROZEN.csv"
DYNASTY_BOARD_FILE_NAME = "full_player_board_value_review_rows.csv"
OUTCOME_NUMERIC_DISPLAY_FILE_NAME = "numeric_outcome_display_v1.csv"
CROSS_ASSET_CANDIDATE_FILE_NAME = "cross_asset_candidate_player_board.csv"

LOCAL_FROZEN_BOARD_ROOT = Path(
    r"C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622"
)
LOCAL_FROZEN_BOARD_PATH = LOCAL_FROZEN_BOARD_ROOT / BOARD_FILE_NAME
REPO_SAFE_FROZEN_BOARD_ROOT = (
    REPO_ROOT
    / "docs"
    / "draft_day_exports"
    / "final_board_v1_20260622"
)
REPO_SAFE_FROZEN_BOARD_PATH = REPO_SAFE_FROZEN_BOARD_ROOT / BOARD_FILE_NAME
CROSS_ASSET_CANDIDATE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_8h_emergency_20260622"
    / "emergency_cross_asset_candidate_player_board.csv"
)
HISTORICAL_TUNED_CANDIDATE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "historical_cross_asset_tuning_20260622"
    / "tuned_candidate_app_overlay.csv"
)
TUNED_V2_CANDIDATE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_accuracy_max_20260622"
    / "tuned_v2_current_draft_pool_overlay.csv"
)
PDF_FREE_AGENT_DRAFTABLE_POOL_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_accuracy_max_20260622"
    / "free_agent_pdf_page3_draftable_pool.csv"
)
ROOKIE_VERIFIED_AGE_DISPLAY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "age_source_audit_20260622"
    / "rookie_verified_age_display_20260622.csv"
)
FALLBACK_CROSS_ASSET_CANDIDATE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "cross_asset_formula_app_repair_20260622"
    / CROSS_ASSET_CANDIDATE_FILE_NAME
)

LOCAL_APP_PROP_ROOT = Path(r"C:\NWR_SHARED_DATA\draft_day_app_props\20260622")
REPO_SAFE_APP_PROP_ROOT = REPO_SAFE_FROZEN_BOARD_ROOT / "app_props"
APP_PROP_ROOT = LOCAL_APP_PROP_ROOT
EXPECTED_ROW_COUNT = 66
EXPECTED_DYNASTY_ROW_COUNT = 240
LOCAL_DYNASTY_RANKINGS_ROOT = (
    REPO_ROOT / "local_exports" / "model_v4" / "current_value" / "latest"
)
LOCAL_DYNASTY_RANKINGS_PATH = LOCAL_DYNASTY_RANKINGS_ROOT / DYNASTY_BOARD_FILE_NAME
CONTROL_REPO_ROOT = Path(r"C:\NWR\Niners-War-Room")
CONTROL_DYNASTY_RANKINGS_PATH = (
    CONTROL_REPO_ROOT
    / "local_exports"
    / "model_v4"
    / "current_value"
    / "latest"
    / DYNASTY_BOARD_FILE_NAME
)
EXPECTED_DYNASTY_RANKINGS_HASH = (
    "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
)
OUTCOME_NUMERIC_DISPLAY_PATH = (
    Path(r"C:\NWR\Niners-War-Room-outcome")
    / "app"
    / "generated"
    / "outcome_probability"
    / OUTCOME_NUMERIC_DISPLAY_FILE_NAME
)
EXPECTED_OUTCOME_NUMERIC_DISPLAY_HASH = (
    "1fb63fec25f7893ed09004830c7eb4e5ed32c6622c08876849fb61a2e4826cb0"
)
PINNED_SNAPSHOT_MANIFEST = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots"
    r"\20260620_controlled_sim_v1\pinned_snapshot_manifest.json"
)
EXPECTED_PINNED_MANIFEST_HASH = (
    "5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE"
)
ROSTER_AGE_CONTEXT_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context"
    r"\20260621_011500_timing_metadata_v1\player_roster_display_context.csv"
)
AGE_AS_OF_DATE = date(2026, 6, 22)

REQUIRED_VISIBLE_FIELDS = (
    "final_board_rank",
    "final_tier",
    "position_rank",
    "model_posture_used",
    "candidate_status",
    "risk_notes",
    "needs_manual_review",
)
INTERNAL_COLUMNS = ("source_file",)
HIDDEN_SORT_PATTERNS = ("hidden_sort", "sort_key", "private_value")
DISPLAY_ONLY_COLUMNS = tuple(
    column
    for column in (
        "rookie_rank_display_only",
        "rookie_tier_display_only",
        "draft_action_display_only",
        "warning_severity_display_only",
        "nfl_draft_capital_display_only",
        "depth_chart_role_display_only",
        "veteran_candidate_value_display_only",
        "veteran_candidate_rank_display_only",
        "veteran_trust_status_display_only",
    )
)

FULL_DYNASTY_VIEW = "Full Dynasty Rankings"
ROOKIES_DRAFT_BOARD_VIEW = "Rookies / Draft Board"
UNIFIED_REVIEW_VIEW = "Unified Review"

LANE_NAMES = (
    "outcome_columns",
    "trading_lab",
    "rookie_hq",
    "mock_draft",
    "decision_board",
)

LANE_PROP_PRIMARY_FILES = {
    "outcome_columns": "outcome_player_context.csv",
    "trading_lab": "trade_helper_context.csv",
    "rookie_hq": "rookie_overlay_context.csv",
    "mock_draft": "availability_context.csv",
    "decision_board": "decision_flags_context.csv",
}

LANE_STATUS_FILES = {
    "outcome_columns": "OUTCOME_APP_PROP_STATUS.md",
    "trading_lab": "TRADING_LAB_APP_PROP_STATUS.md",
    "rookie_hq": "ROOKIE_HQ_APP_PROP_STATUS.md",
    "mock_draft": "MOCK_DRAFT_APP_PROP_STATUS.md",
    "decision_board": "DECISION_BOARD_APP_PROP_STATUS.md",
}

PROP_TECHNICAL_DISPLAY_COLUMNS = (
    "final_board_rank_override_allowed",
    "hidden_sort_field_created",
    "private_value_created",
)

DYNASTY_DISPLAY_COLUMNS = (
    "nwr_rank",
    "player_name",
    "position",
    "age",
    "nfl_team",
    "nwr_dynasty_score",
    "trust_status",
    "warning_flags",
    "market_rank",
    "league_rank",
    "pool_status",
    "data_needed",
    "outcome_availability_display_only",
    "qb_t12_display_only",
    "rb_t12_display_only",
    "rb_t24_display_only",
    "wr_t12_display_only",
    "wr_t24_display_only",
    "wr_t36_display_only",
    "te_t12_display_only",
)
FULL_DYNASTY_PLAYER_BOARD_DISPLAY_COLUMNS = (
    "nwr_rank",
    "player_name",
    "position",
    "nfl_team",
    "age",
    "nwr_dynasty_score",
    "nwr_position_rank",
    "outcome_availability_display_only",
    "qb_t12_display_only",
    "rb_t12_display_only",
    "rb_t24_display_only",
    "wr_t12_display_only",
    "wr_t24_display_only",
    "wr_t36_display_only",
    "te_t12_display_only",
    "candidate_value_band",
    "trust_status",
    "confidence_band",
    "candidate_key_caveat",
)
MARKET_BASELINE_DISPLAY_COLUMNS = (
    "dp_value_1qb",
    "dp_market_rank_1qb",
    "dp_ecr_pos",
    "dp_age",
    "market_gap",
    "market_sanity_label",
    "age_source_display",
    "market_baseline_label",
)
ROOKIES_DRAFT_BOARD_DISPLAY_COLUMNS = (
    "cross_asset_candidate_rank",
    "final_board_rank",
    "cross_asset_candidate_value",
    "player_name",
    "position",
    "nfl_team",
    "age",
    "candidate_value_band",
    "confidence_band",
    "asset_type_display",
    "available_pool_adp_range",
    "current_pick_value",
    "candidate_key_caveat",
    "nwr_rank",
    "qb_t12_display_only",
    "rb_t12_display_only",
    "rb_t24_display_only",
    "wr_t12_display_only",
    "wr_t24_display_only",
    "wr_t36_display_only",
    "te_t12_display_only",
)
UNIFIED_PLAYER_BOARD_DISPLAY_COLUMNS = (
    "nwr_rank",
    "cross_asset_candidate_rank",
    "cross_asset_candidate_value",
    "player_name",
    "position",
    "nfl_team",
    "age",
    "asset_type_display",
    "source_coverage",
    "final_board_rank",
    "final_tier",
    "position_rank",
    "candidate_value_band",
    "confidence_band",
    "available_pool_adp_range",
    "current_pick_value",
    "candidate_key_caveat",
    "nwr_dynasty_score",
    "trust_status",
    "warning_flags",
    "pool_status",
    "data_needed",
    "model_posture_used",
    "candidate_status",
    "risk_notes",
    "needs_manual_review",
    "qb_t12_display_only",
    "rb_t12_display_only",
    "rb_t24_display_only",
    "wr_t12_display_only",
    "wr_t24_display_only",
    "wr_t36_display_only",
    "te_t12_display_only",
)
OUTCOME_NOT_ENOUGH_INFORMATION = "Not enough information"
OUTCOME_NOT_APPLICABLE = "N/A"
OUTCOME_DISPLAY_MODE_POSITION_APPLICABLE = "Position-applicable only"
OUTCOME_DISPLAY_MODE_ALL = "All outcome columns"
OUTCOME_DISPLAY_MODE_HIDE = "Hide"
OUTCOME_DISPLAY_MODES = (
    OUTCOME_DISPLAY_MODE_POSITION_APPLICABLE,
    OUTCOME_DISPLAY_MODE_ALL,
    OUTCOME_DISPLAY_MODE_HIDE,
)
APPROVED_OUTCOME_DISPLAY_FIELDS = (
    ("qb_t12_display_pct", "qb_t12_display_only", "QB T12"),
    ("rb_t12_display_pct", "rb_t12_display_only", "RB T12"),
    ("rb_t24_display_pct", "rb_t24_display_only", "RB T24"),
    ("wr_t12_display_pct", "wr_t12_display_only", "WR T12"),
    ("wr_t24_display_pct", "wr_t24_display_only", "WR T24"),
    ("wr_t36_display_pct", "wr_t36_display_only", "WR T36"),
    ("te_t12_display_pct", "te_t12_display_only", "TE T12"),
)
OUTCOME_DISPLAY_FIELD_POSITIONS = {
    target: label.split(" ", maxsplit=1)[0]
    for _source, target, label in APPROVED_OUTCOME_DISPLAY_FIELDS
}


@dataclass(frozen=True)
class FrozenBoardBundle:
    frame: pd.DataFrame
    source_path: Path | None
    source_label: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def loaded(self) -> bool:
        return self.source_path is not None and self.frame.shape[0] > 0 and not self.errors

    @property
    def row_count(self) -> int:
        return int(self.frame.shape[0])


@dataclass(frozen=True)
class DynastyRankingsBundle:
    frame: pd.DataFrame
    source_path: Path | None
    source_label: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    source_hash: str | None

    @property
    def loaded(self) -> bool:
        return self.source_path is not None and self.frame.shape[0] > 0 and not self.errors

    @property
    def row_count(self) -> int:
        return int(self.frame.shape[0])

    @property
    def veteran_count(self) -> int:
        if "is_rookie" not in self.frame.columns:
            return 0
        rookie_mask = self.frame["is_rookie"].astype(str).str.lower().isin({"1", "true", "yes"})
        return int((~rookie_mask).sum())

    @property
    def rookie_count(self) -> int:
        if "is_rookie" not in self.frame.columns:
            return 0
        rookie_mask = self.frame["is_rookie"].astype(str).str.lower().isin({"1", "true", "yes"})
        return int(rookie_mask.sum())


@dataclass(frozen=True)
class OutcomeDisplayBundle:
    frame: pd.DataFrame
    source_path: Path | None
    source_label: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    source_hash: str | None

    @property
    def loaded(self) -> bool:
        return self.source_path is not None and self.frame.shape[0] > 0 and not self.errors

    @property
    def row_count(self) -> int:
        return int(self.frame.shape[0])

    @property
    def available_count(self) -> int:
        if "outcome_status" not in self.frame.columns:
            return 0
        return int(self.frame["outcome_status"].astype(str).eq("available").sum())

    @property
    def unavailable_count(self) -> int:
        if "outcome_status" not in self.frame.columns:
            return self.row_count
        return int(~self.frame["outcome_status"].astype(str).eq("available").sum())


def resolve_frozen_board_path() -> tuple[Path | None, str, tuple[str, ...]]:
    warnings: list[str] = []
    for path, label, warning in frozen_board_candidates():
        if path.exists():
            if warning:
                warnings.append(warning)
            return path, label, tuple(warnings)
    return None, "missing frozen board", tuple(warnings)


def frozen_board_candidates() -> tuple[tuple[Path, str, str], ...]:
    candidates: list[tuple[Path, str, str]] = []
    env_root = os.environ.get("NWR_DRAFT_DAY_DATA_ROOT")
    if env_root:
        candidates.append(
            (
                Path(env_root) / BOARD_FILE_NAME,
                "environment frozen board",
                "Using NWR_DRAFT_DAY_DATA_ROOT frozen board.",
            )
        )
    candidates.extend(
        [
            (LOCAL_FROZEN_BOARD_PATH, "local frozen board", ""),
            (
                REPO_SAFE_FROZEN_BOARD_PATH,
                "repo-safe frozen board copy",
                "Using GitHub-safe frozen board copy because local-only data is missing.",
            ),
        ]
    )
    return tuple(candidates)


def app_prop_root_candidates() -> tuple[tuple[Path, str], ...]:
    candidates: list[tuple[Path, str]] = []
    env_root = os.environ.get("NWR_DRAFT_DAY_APP_PROPS_ROOT")
    if env_root:
        candidates.append((Path(env_root), "environment app props"))
    candidates.extend(
        [
            (LOCAL_APP_PROP_ROOT, "local app props"),
            (REPO_SAFE_APP_PROP_ROOT, "repo-safe app props"),
        ]
    )
    return tuple(candidates)


def lane_prop_folder(lane: str) -> tuple[Path, str]:
    primary_file = LANE_PROP_PRIMARY_FILES[lane]
    for root, label in app_prop_root_candidates():
        folder = root / lane
        if (folder / primary_file).exists():
            return folder, label
    first_root, first_label = app_prop_root_candidates()[0]
    return first_root / lane, first_label


def load_frozen_board() -> FrozenBoardBundle:
    path, label, warnings = resolve_frozen_board_path()
    if path is None:
        return FrozenBoardBundle(
            frame=pd.DataFrame(),
            source_path=None,
            source_label=label,
            errors=("Frozen Final Draft Board V1 CSV was not found.",),
            warnings=warnings,
        )

    frame = pd.read_csv(path).fillna("")
    errors = list(validate_frozen_board(frame))
    normalized = normalize_board_frame(frame)
    normalized = integrate_cross_asset_candidate_context(
        normalized,
        name_column="player",
        position_column="position",
    )
    return FrozenBoardBundle(
        frame=normalized,
        source_path=path,
        source_label=label,
        errors=tuple(errors),
        warnings=warnings,
    )


@lru_cache(maxsize=1)
def load_pdf_free_agent_pool() -> pd.DataFrame:
    """Load the verified LVE PDF page-3 free-agent overlay without mutating sources."""

    if not PDF_FREE_AGENT_DRAFTABLE_POOL_PATH.exists():
        return pd.DataFrame()
    try:
        frame = pd.read_csv(PDF_FREE_AGENT_DRAFTABLE_POOL_PATH, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()
    hidden_like = hidden_sort_columns(frame.columns)
    if hidden_like:
        return pd.DataFrame()
    return frame


def load_expanded_draftable_player_pool(frozen_frame: pd.DataFrame) -> pd.DataFrame:
    """Return baseline board rows plus verified PDF free agents for draft UI only."""

    if frozen_frame.empty:
        return frozen_frame.copy()
    expanded = _prepare_frozen_rows_for_expanded_pool(frozen_frame)
    pdf_rows = _pdf_free_agent_rows_for_expanded_pool(expanded)
    if not pdf_rows.empty:
        expanded = pd.concat([expanded, pdf_rows], ignore_index=True, sort=False).fillna("")
    expanded = enrich_display_age_from_roster_context(expanded, name_column="player")
    expanded = enrich_display_age_from_rookie_birthdate_audit(expanded)
    expanded = _recalculate_expanded_candidate_rank(expanded)
    expanded = _apply_on_clock_decision_layer(expanded)
    expanded = _recalculate_expanded_available_pool_adp(expanded)
    return expanded.fillna("").reset_index(drop=True)


def _apply_on_clock_decision_layer(frame: pd.DataFrame) -> pd.DataFrame:
    decision = frame.copy()
    if decision.empty:
        return decision
    values: list[float | None] = []
    for row in decision.to_dict("records"):
        values.append(_on_clock_decision_value(row))
    decision["_on_clock_decision_value_sort"] = values
    decision["on_clock_decision_value"] = [
        f"{value:.2f}" if value is not None else OUTCOME_NOT_ENOUGH_INFORMATION
        for value in values
    ]
    decision["on_clock_decision_tier"] = [
        _on_clock_decision_tier(value) if value is not None else OUTCOME_NOT_ENOUGH_INFORMATION
        for value in values
    ]
    decision["on_clock_confidence"] = [
        _on_clock_confidence(row, value)
        for row, value in zip(decision.to_dict("records"), values, strict=False)
    ]
    reasons: list[str] = []
    warnings: list[str] = []
    for row, value in zip(decision.to_dict("records"), values, strict=False):
        reason, warning = _on_clock_reason_and_warning(row, value)
        reasons.append(reason)
        warnings.append(warning)
    decision["on_clock_reason"] = reasons
    decision["on_clock_warning"] = warnings
    decision["dynasty_asset_score"] = decision["on_clock_decision_value"]
    decision["dynasty_asset_tier"] = [
        _dynasty_asset_tier(value) if value is not None else OUTCOME_NOT_ENOUGH_INFORMATION
        for value in values
    ]
    decision["dynasty_asset_confidence"] = decision["on_clock_confidence"]
    decision["why_draft"] = reasons
    decision["main_risk"] = warnings
    decision["human_review_flag"] = [
        _dynasty_asset_human_review_flag(row, value)
        for row, value in zip(decision.to_dict("records"), values, strict=False)
    ]

    eligible = decision["position"].astype(str).str.upper().isin({"QB", "RB", "WR", "TE"})
    order = decision.loc[eligible & decision["_on_clock_decision_value_sort"].notna()].copy()
    if not order.empty:
        order = order.sort_values(
            by=["_on_clock_decision_value_sort", "player"],
            ascending=[False, True],
            kind="stable",
        )
        for rank, index in enumerate(order.index, start=1):
            decision.at[index, "on_clock_decision_rank"] = str(rank)
            decision.at[index, "dynasty_asset_rank"] = str(rank)
    decision["on_clock_decision_rank"] = decision.get(
        "on_clock_decision_rank",
        OUTCOME_NOT_ENOUGH_INFORMATION,
    )
    decision["dynasty_asset_rank"] = decision.get(
        "dynasty_asset_rank",
        OUTCOME_NOT_ENOUGH_INFORMATION,
    )
    return decision.drop(columns=["_on_clock_decision_value_sort"])


def _on_clock_decision_value(row: dict[str, object]) -> float | None:
    key = _player_identity_key(row.get("player"), row.get("position"))
    anchor = _on_clock_anchor_value(key)
    if anchor is not None:
        return anchor

    base = _safe_float(row.get("cross_asset_candidate_value"))
    if base is None:
        return None
    position = _clean_text(row.get("position")).upper()
    source_group = _clean_text(row.get("source_group"))
    confidence = _clean_text(row.get("confidence_band")).lower()
    caveat_text = " ".join(
        _clean_text(row.get(column)).lower()
        for column in (
            "candidate_key_caveat",
            "uncertainty_reasons",
            "risk_notes",
            "needs_manual_review",
        )
    )
    value = base
    if position == "QB":
        value -= 7.0
    if source_group == "LVE PDF Free Agent":
        value -= 4.0
    if confidence in {"low", "very low"}:
        value -= 6.0
    elif confidence in {"medium-low", "medium low"}:
        value -= 2.0
    if _clean_text(row.get("asset_type")).lower() == "rookie" and not _has_display_age(row):
        value -= 1.5
    if "manual" in caveat_text or "needs_data" in caveat_text:
        value -= 2.5
    if "age" in caveat_text or "injury" in caveat_text or "risk" in caveat_text:
        value -= 2.0
    age = _safe_float(row.get("age"))
    if age is not None:
        if position in {"RB", "WR", "TE"} and age >= 30:
            value -= 6.0
        elif position in {"RB", "WR", "TE"} and age >= 28:
            value -= 3.0
        elif position == "QB" and age >= 32:
            value -= 4.0
    return max(min(value, 100.0), 0.0)


def _on_clock_anchor_value(key: tuple[str, str]) -> float | None:
    anchors = {
        ("zayflowers", "WR"): 78.0,
        ("chrisolave", "WR"): 76.0,
        ("jeremiyahlove", "RB"): 74.0,
        ("drakemaye", "QB"): 73.0,
        ("makailemon", "WR"): 69.0,
        ("carnelltate", "WR"): 67.0,
        ("jamesonwilliams", "WR"): 66.0,
        ("kcconcepcion", "WR"): 64.0,
        ("jadarianprice", "RB"): 62.0,
        ("brianthomas", "WR"): 61.0,
        ("brianthomasjr", "WR"): 61.0,
        ("jaylenwarren", "RB"): 59.0,
        ("rasheerice", "WR"): 58.0,
        ("brockpurdy", "QB"): 52.0,
        ("dakprescott", "QB"): 49.0,
        ("tyreekhill", "WR"): 40.0,
        ("keenanallen", "WR"): 32.0,
        ("darrenwaller", "TE"): 24.0,
    }
    return anchors.get(key)


def _on_clock_decision_tier(value: float) -> str:
    if value >= 72:
        return "Tier 1 - on-clock core"
    if value >= 60:
        return "Tier 2 - strong review"
    if value >= 45:
        return "Tier 3 - situational value"
    if value >= 30:
        return "Tier 4 - discount only"
    return "Hold / deep discount"


def _dynasty_asset_tier(value: float) -> str:
    if value >= 72:
        return "Tier 1A: core on-clock candidates"
    if value >= 60:
        return "Tier 1B: strong alternatives"
    if value >= 45:
        return "Tier 2: viable but conditional"
    if value >= 30:
        return "Tier 3: discount / depth / risky"
    return "Avoid / emergency only"


def _dynasty_asset_human_review_flag(row: dict[str, object], value: float | None) -> str:
    if value is None:
        return "HIGH - not enough internal evidence"
    key = _player_identity_key(row.get("player"), row.get("position"))
    if key in {
        ("drakemaye", "QB"),
        ("tyreekhill", "WR"),
        ("keenanallen", "WR"),
        ("darrenwaller", "TE"),
    }:
        return "HIGH"
    if _clean_text(row.get("asset_type")).lower() == "rookie" and not _has_display_age(row):
        return "MEDIUM - rookie age missing"
    existing = _clean_text(row.get("human_review_priority")) or _clean_text(
        row.get("manual_review_flag")
    )
    if existing:
        return existing
    if str(row.get("needs_manual_review", "")).lower() in {"true", "yes", "1"}:
        return "MEDIUM"
    return "LOW"


def _has_display_age(row: dict[str, object]) -> bool:
    return age_display_value(row.get("age")) != OUTCOME_NOT_ENOUGH_INFORMATION


def _on_clock_confidence(row: dict[str, object], value: float | None) -> str:
    if value is None:
        return "Low"
    key = _player_identity_key(row.get("player"), row.get("position"))
    if key in {
        ("zayflowers", "WR"),
        ("chrisolave", "WR"),
        ("drakemaye", "QB"),
        ("jamesonwilliams", "WR"),
    }:
        return "Medium"
    if key in {("tyreekhill", "WR"), ("keenanallen", "WR"), ("darrenwaller", "TE")}:
        return "Low"
    confidence = _clean_text(row.get("confidence_band"))
    return confidence or "Medium-low"


def _on_clock_reason_and_warning(row: dict[str, object], value: float | None) -> tuple[str, str]:
    if value is None:
        return (
            "Not enough internal evidence for on-clock value; still draftable if eligible.",
            "Not enough information.",
        )
    key = _player_identity_key(row.get("player"), row.get("position"))
    reason_warning = {
        ("zayflowers", "WR"): (
            "Proven young WR anchor; should not be buried behind medium/low-confidence rookies.",
            "Review-only anchor; still compare with Final Board Rank.",
        ),
        ("chrisolave", "WR"): (
            "Proven young WR anchor with primary-target profile; top decision tier.",
            "Review-only anchor; verify human preference versus rookies.",
        ),
        ("jeremiyahlove", "RB"): (
            "Top rookie/prospect remains high, but confidence is capped versus proven NFL assets.",
            "Rookie uncertainty remains high.",
        ),
        ("drakemaye", "QB"): (
            "Elite-young-QB exception: 1QB discount still applies, but he must stay "
            "review-visible.",
            "10-team 1QB lowers ceiling versus WR/RB, but prior rank was too buried.",
        ),
        ("jamesonwilliams", "WR"): (
            "Explosive young NFL WR production keeps him review-visible against rookies.",
            "Volatility remains; do not treat as risk-free.",
        ),
        ("tyreekhill", "WR"): (
            "PDF free agent with major age/status/injury risk; discount only despite name value.",
            "LOUD WARNING: not on frozen board; major current-status and age risk.",
        ),
        ("keenanallen", "WR"): (
            "Older veteran profile; draft only at discount if roster construction needs "
            "short-term WR.",
            "Age/role risk; not a long-term anchor.",
        ),
        ("darrenwaller", "TE"): (
            "Older TE with return/health risk; human-review hold unless cost is trivial.",
            "Age/retirement/health risk.",
        ),
    }
    if key in reason_warning:
        return reason_warning[key]
    source_group = _clean_text(row.get("source_group"))
    confidence = _clean_text(row.get("confidence_band")) or "Medium-low"
    if source_group == "LVE PDF Free Agent":
        return (
            "PDF free-agent overlay with review-only internal value where available.",
            "Not on frozen board; use human review.",
        )
    return (
        f"On-clock value from tuned candidate layer with {confidence} confidence.",
        "Review-only; does not replace Final Board Rank.",
    )


def _prepare_frozen_rows_for_expanded_pool(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    prepared["source_group"] = "Frozen Baseline"
    prepared["draftable_status"] = "Frozen Final Draft Board V1 baseline"
    prepared["include_default"] = "yes"
    prepared["exclude_reason"] = ""
    if "source_label_display_only" not in prepared.columns:
        prepared["source_label_display_only"] = "Frozen Baseline"
    if "asset_type_display" not in prepared.columns:
        prepared["asset_type_display"] = prepared.get("asset_type", "Frozen Baseline")
    return prepared


def _pdf_free_agent_rows_for_expanded_pool(existing_frame: pd.DataFrame) -> pd.DataFrame:
    pool = load_pdf_free_agent_pool()
    if pool.empty:
        return pd.DataFrame()
    existing_keys = {
        _player_identity_key(row.get("player"), row.get("position"))
        for row in existing_frame.to_dict("records")
    }
    rows: list[dict[str, object]] = []
    for row in pool.to_dict("records"):
        identity = _player_identity_key(row.get("player"), row.get("pos"))
        if identity in existing_keys:
            continue
        rows.append(_pdf_free_agent_row(row))
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _pdf_free_agent_row(row: dict[str, object]) -> dict[str, object]:
    player = _clean_text(row.get("player"))
    position = _clean_text(row.get("pos")).upper()
    age = age_display_value(row.get("age"))
    adp = _candidate_display_value(row.get("adp"))
    candidate_value = _pdf_candidate_value(row)
    confidence = _pdf_confidence_band(row, candidate_value)
    caveat = _pdf_candidate_caveat(row, candidate_value)
    return {
        "player_id": _clean_text(row.get("player_id")),
        "final_board_rank": "Not on frozen board",
        "final_tier": "PDF Free Agent",
        "position_rank": OUTCOME_NOT_ENOUGH_INFORMATION,
        "player": player,
        "position": position,
        "nfl_team": _clean_text(row.get("nfl_team")),
        "age": age,
        "asset_type": "PDF Free Agent / Draftable",
        "asset_type_display": "PDF Free Agent / Draftable",
        "source_group": "LVE PDF Free Agent",
        "draftable_status": "PDF Page 3 Free Agent",
        "include_default": _clean_text(row.get("include_default")) or "no",
        "exclude_reason": _clean_text(row.get("exclude_reason")),
        "source_label_display_only": "PDF Free Agent / Draftable",
        "availability_status": "PDF Page 3 Free Agent",
        "model_posture_used": "PDF draftable overlay / review-only",
        "candidate_status": "REVIEW_ONLY_PDF_FREE_AGENT",
        "risk_notes": "Not on frozen board; draftable per LVE Rosters page 3.",
        "needs_manual_review": "true",
        "adp": adp,
        "adp_source_status": "Display-only Sleeper ADP context where available",
        "cross_asset_candidate_rank": OUTCOME_NOT_ENOUGH_INFORMATION,
        "cross_asset_candidate_value": candidate_value,
        "candidate_value_band": _tuned_v2_value_band(candidate_value),
        "confidence_band": confidence,
        "uncertainty_reasons": _pdf_uncertainty_reasons(row, candidate_value),
        "candidate_key_caveat": caveat,
        "candidate_vs_frozen_note": (
            "PDF Free Agent / Review-Only; not on frozen board; does not replace "
            "Final Board Rank."
        ),
        "candidate_vs_dynasty_note": _pdf_dynasty_note(row),
        "candidate_action_summary": caveat,
        "available_pool_adp_rank": OUTCOME_NOT_ENOUGH_INFORMATION,
        "available_pool_adp_range": OUTCOME_NOT_ENOUGH_INFORMATION,
        "current_pick_value": OUTCOME_NOT_ENOUGH_INFORMATION,
        "current_pick_value_reason": (
            "Computed from available-pool ADP rank when display-only ADP exists; "
            "ADP does not drive internal value."
        ),
        "outcome_applicable_summary": OUTCOME_NOT_ENOUGH_INFORMATION,
        "horizon_2026_band": OUTCOME_NOT_ENOUGH_INFORMATION,
        "horizon_2027_band": OUTCOME_NOT_ENOUGH_INFORMATION,
        "horizon_next5y_band": OUTCOME_NOT_ENOUGH_INFORMATION,
        "manual_review_flag": "HIGH",
        "source_note": (
            "LVE Rosters 061326.pdf page 3 Free Agents; draftable overlay only; "
            "PDF ranks are display-only and not model inputs."
        ),
        "pdf_overall_rank_or_number": _clean_text(row.get("pdf_overall_rank_or_number")),
        "pdf_position_rank": _clean_text(row.get("pdf_position_rank")),
    }


def _pdf_candidate_value(row: dict[str, object]) -> str:
    tuned = _clean_text(row.get("tuned_v2_cross_asset_value"))
    if tuned:
        return tuned
    score = _safe_float(row.get("nwr_dynasty_score"))
    if score is not None:
        return f"{max(min(score, 100.0), 0.0):.2f}"
    return OUTCOME_NOT_ENOUGH_INFORMATION


def _pdf_confidence_band(row: dict[str, object], candidate_value: object) -> str:
    if _safe_float(candidate_value) is None:
        return "Low"
    confidence = _clean_text(row.get("tuned_v2_confidence_band"))
    if confidence:
        return confidence
    if _clean_text(row.get("matched_full_dynasty_rank")):
        return "Medium-low"
    return "Low"


def _pdf_uncertainty_reasons(row: dict[str, object], candidate_value: object) -> str:
    reasons = ["pdf_page3_free_agent_overlay", "not_on_frozen_board"]
    if _safe_float(candidate_value) is None:
        reasons.append("no_internal_candidate_value_available")
    if not _clean_text(row.get("matched_full_dynasty_rank")):
        reasons.append("not_matched_full_dynasty_source")
    if not _clean_text(row.get("player_id")):
        reasons.append("player_id_not_matched")
    return "; ".join(reasons)


def _pdf_candidate_caveat(row: dict[str, object], candidate_value: object) -> str:
    if _safe_float(candidate_value) is None:
        return "PDF Free Agent / Draftable; internal candidate value is Not enough information."
    return "PDF Free Agent / Draftable; candidate value is review-only."


def _pdf_dynasty_note(row: dict[str, object]) -> str:
    rank = _clean_text(row.get("matched_full_dynasty_rank"))
    if rank:
        return f"Matched full dynasty rank {rank}; review-only overlay."
    return "No matched full dynasty rank; use human review."


def _recalculate_expanded_candidate_rank(frame: pd.DataFrame) -> pd.DataFrame:
    ranked = frame.copy()
    if "cross_asset_candidate_value" not in ranked.columns:
        return ranked
    eligible = ranked["position"].astype(str).str.upper().isin({"QB", "RB", "WR", "TE"})
    values = pd.to_numeric(ranked["cross_asset_candidate_value"], errors="coerce")
    order = ranked.loc[eligible & values.notna()].copy()
    if order.empty:
        return ranked
    order["_expanded_candidate_value_sort"] = values.loc[order.index]
    order = order.sort_values(
        by=["_expanded_candidate_value_sort", "player"],
        ascending=[False, True],
        kind="stable",
    )
    for rank, index in enumerate(order.index, start=1):
        ranked.at[index, "cross_asset_candidate_rank"] = str(rank)
    return ranked


def _recalculate_expanded_available_pool_adp(frame: pd.DataFrame) -> pd.DataFrame:
    expanded = frame.copy()
    if "adp" not in expanded.columns:
        return expanded
    eligible = expanded["position"].astype(str).str.upper().isin({"QB", "RB", "WR", "TE"})
    adp_values = pd.to_numeric(expanded["adp"], errors="coerce")
    order = expanded.loc[eligible & adp_values.notna()].copy()
    if order.empty:
        return expanded
    order["_expanded_adp_sort"] = adp_values.loc[order.index]
    order = order.sort_values(
        by=["_expanded_adp_sort", "player"],
        ascending=[True, True],
        kind="stable",
    )
    for rank, index in enumerate(order.index, start=1):
        expanded.at[index, "available_pool_adp_rank"] = str(rank)
        expanded.at[index, "available_pool_adp_range"] = _available_pool_adp_range(rank)
        expanded.at[index, "pool_adp_pick_equivalent"] = _pool_adp_pick_equivalent(rank)
    return expanded


def _pool_adp_pick_equivalent(rank: int) -> str:
    if rank <= 0:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    round_number = ((rank - 1) // 10) + 1
    round_pick = ((rank - 1) % 10) + 1
    return f"{round_number}.{round_pick:02d}"


def _available_pool_adp_range(rank: int) -> str:
    if rank <= 3:
        return "Early 1st equivalent"
    if rank <= 7:
        return "Mid 1st equivalent"
    if rank <= 10:
        return "Late 1st equivalent"
    if rank <= 13:
        return "Early 2nd equivalent"
    if rank <= 20:
        return "Mid/Late 2nd equivalent"
    return "Depth / later"


def _safe_float(value: object) -> float | None:
    try:
        numeric = float(str(value or "").strip())
    except ValueError:
        return None
    if pd.isna(numeric):
        return None
    return numeric


def validate_frozen_board(frame: pd.DataFrame) -> tuple[str, ...]:
    errors: list[str] = []
    if frame.shape[0] != EXPECTED_ROW_COUNT:
        errors.append(f"Expected {EXPECTED_ROW_COUNT} frozen board rows; found {frame.shape[0]}.")
    missing = [column for column in REQUIRED_VISIBLE_FIELDS if column not in frame.columns]
    if missing:
        errors.append(f"Missing required visible fields: {', '.join(missing)}.")
    hidden_like = hidden_sort_columns(frame.columns)
    if hidden_like:
        errors.append(
            f"Hidden/private sort-like columns are not allowed: {', '.join(hidden_like)}."
        )
    return tuple(errors)


def hidden_sort_columns(columns: Iterable[str]) -> tuple[str, ...]:
    blocked: list[str] = []
    for column in columns:
        lower = column.lower()
        if any(pattern in lower for pattern in HIDDEN_SORT_PATTERNS):
            blocked.append(column)
    return tuple(blocked)


def normalize_board_frame(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in INTERNAL_COLUMNS:
        if column in normalized.columns:
            normalized = normalized.drop(columns=[column])
    if "final_board_rank" in normalized.columns:
        normalized["final_board_rank"] = pd.to_numeric(
            normalized["final_board_rank"], errors="coerce"
        )
        normalized = normalized.sort_values("final_board_rank", kind="stable")
    if "age" in normalized.columns:
        normalized["age"] = normalized["age"].map(age_display_value)
    else:
        normalized["age"] = OUTCOME_NOT_ENOUGH_INFORMATION
    normalized = enrich_display_age_from_roster_context(normalized, name_column="player")
    return normalized.reset_index(drop=True)


def dynasty_rankings_candidates() -> tuple[tuple[Path, str, str], ...]:
    candidates: list[tuple[Path, str, str]] = []
    env_root = os.environ.get("NWR_DYNASTY_RANKINGS_ROOT")
    if env_root:
        candidates.append(
            (
                Path(env_root) / DYNASTY_BOARD_FILE_NAME,
                "environment dynasty rankings",
                "Using NWR_DYNASTY_RANKINGS_ROOT full dynasty rankings.",
            )
        )
    candidates.append((LOCAL_DYNASTY_RANKINGS_PATH, "approved local dynasty rankings", ""))
    if CONTROL_DYNASTY_RANKINGS_PATH != LOCAL_DYNASTY_RANKINGS_PATH:
        candidates.append(
            (
                CONTROL_DYNASTY_RANKINGS_PATH,
                "approved control-repo dynasty rankings",
                (
                    "Using the approved local dynasty rankings artifact from the clean "
                    "control repo because this lane worktree does not contain local_exports."
                ),
            )
        )
    return tuple(candidates)


def resolve_dynasty_rankings_path() -> tuple[Path | None, str, tuple[str, ...]]:
    warnings: list[str] = []
    for path, label, warning in dynasty_rankings_candidates():
        if path.exists():
            if warning:
                warnings.append(warning)
            return path, label, tuple(warnings)
    return None, "missing approved dynasty rankings", tuple(warnings)


def load_dynasty_rankings() -> DynastyRankingsBundle:
    path, label, warnings = resolve_dynasty_rankings_path()
    if path is None:
        return DynastyRankingsBundle(
            frame=pd.DataFrame(),
            source_path=None,
            source_label=label,
            errors=(
                "Approved full dynasty rankings CSV was not found. Expected "
                f"{LOCAL_DYNASTY_RANKINGS_PATH}.",
            ),
            warnings=warnings,
            source_hash=None,
        )

    frame = pd.read_csv(path, dtype=str).fillna("")
    source_hash = file_sha256(path)
    errors = list(validate_dynasty_rankings(frame))
    if source_hash != EXPECTED_DYNASTY_RANKINGS_HASH:
        errors.append(
            "Approved dynasty rankings hash mismatch: expected "
            f"{EXPECTED_DYNASTY_RANKINGS_HASH}; found {source_hash}."
        )
    normalized = integrate_cross_asset_candidate_context(
        integrate_outcome_display_context(normalize_dynasty_rankings_frame(frame)),
        name_column="player_name",
        position_column="position",
    )
    return DynastyRankingsBundle(
        frame=normalized,
        source_path=path,
        source_label=label,
        errors=tuple(errors),
        warnings=warnings,
        source_hash=source_hash,
    )


def validate_dynasty_rankings(frame: pd.DataFrame) -> tuple[str, ...]:
    errors: list[str] = []
    if frame.shape[0] != EXPECTED_DYNASTY_ROW_COUNT:
        errors.append(
            f"Expected {EXPECTED_DYNASTY_ROW_COUNT} dynasty ranking rows; found "
            f"{frame.shape[0]}."
        )
    required = ("nwr_rank", "player_name", "position", "nwr_dynasty_score", "is_rookie")
    missing = [column for column in required if column not in frame.columns]
    if missing:
        errors.append(f"Missing dynasty ranking fields: {', '.join(missing)}.")
    hidden_like = hidden_sort_columns(frame.columns)
    if hidden_like:
        errors.append(
            f"Hidden/private sort-like columns are not allowed: {', '.join(hidden_like)}."
        )
    return tuple(errors)


def load_outcome_numeric_display() -> OutcomeDisplayBundle:
    path = OUTCOME_NUMERIC_DISPLAY_PATH
    if not path.exists():
        return OutcomeDisplayBundle(
            frame=pd.DataFrame(),
            source_path=None,
            source_label="missing approved Outcome V1 numeric display",
            errors=(f"Approved Outcome V1 numeric display was not found at {path}.",),
            warnings=(),
            source_hash=None,
        )
    frame = pd.read_csv(path, dtype=str).fillna("")
    source_hash = file_sha256(path)
    errors = list(validate_outcome_numeric_display(frame))
    if source_hash != EXPECTED_OUTCOME_NUMERIC_DISPLAY_HASH:
        errors.append(
            "Approved Outcome V1 numeric display hash mismatch: expected "
            f"{EXPECTED_OUTCOME_NUMERIC_DISPLAY_HASH}; found {source_hash}."
        )
    return OutcomeDisplayBundle(
        frame=frame,
        source_path=path,
        source_label="approved Outcome V1 numeric display",
        errors=tuple(errors),
        warnings=(),
        source_hash=source_hash,
    )


@lru_cache(maxsize=1)
def load_cross_asset_candidate_board() -> pd.DataFrame:
    base_path = (
        CROSS_ASSET_CANDIDATE_PATH
        if CROSS_ASSET_CANDIDATE_PATH.exists()
        else FALLBACK_CROSS_ASSET_CANDIDATE_PATH
    )
    if not base_path.exists():
        return pd.DataFrame()
    try:
        frame = pd.read_csv(base_path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()
    hidden_like = hidden_sort_columns(frame.columns)
    if hidden_like:
        return pd.DataFrame()
    return _overlay_tuned_v2_candidate_rows(
        _overlay_historical_tuned_candidate_rows(frame)
    )


def _overlay_historical_tuned_candidate_rows(base_frame: pd.DataFrame) -> pd.DataFrame:
    if not HISTORICAL_TUNED_CANDIDATE_PATH.exists():
        return base_frame
    try:
        tuned = pd.read_csv(HISTORICAL_TUNED_CANDIDATE_PATH, dtype=str).fillna("")
    except Exception:
        return base_frame
    if hidden_sort_columns(tuned.columns):
        return base_frame
    required = {"player", "pos", "tuned_cross_asset_rank", "tuned_cross_asset_value"}
    if not required.issubset(tuned.columns):
        return base_frame

    merged = base_frame.copy()
    base_lookup = {
        _player_identity_key(row.get("player"), row.get("pos")): index
        for index, row in merged.iterrows()
    }
    for _, tuned_row in tuned.iterrows():
        key = _player_identity_key(tuned_row.get("player"), tuned_row.get("pos"))
        if key not in base_lookup:
            continue
        index = base_lookup[key]
        _apply_tuned_candidate_row(merged, index, tuned_row)
    return merged


def _apply_tuned_candidate_row(
    frame: pd.DataFrame,
    index: int,
    tuned_row: pd.Series,
) -> None:
    mapping = {
        "tuned_cross_asset_rank": "cross_asset_candidate_rank",
        "tuned_cross_asset_value": "cross_asset_candidate_value",
        "value_band": "candidate_value_band",
        "confidence_band": "confidence_band",
        "uncertainty_reasons": "uncertainty_reasons",
        "outcome_applicable_summary": "outcome_applicable_summary",
        "manual_review_flag": "manual_review_flag",
        "adp": "adp",
        "available_pool_adp_rank": "available_pool_adp_rank",
        "available_pool_adp_range": "available_pool_adp_range",
    }
    for source, target in mapping.items():
        if source in tuned_row.index:
            frame.at[index, target] = _candidate_display_value(tuned_row.get(source))

    frame.at[index, "candidate_vs_frozen_note"] = _historical_tuned_note(
        tuned_row.get("direction_vs_frozen_rank"),
        tuned_row.get("main_reason_to_draft"),
    )
    frame.at[index, "candidate_vs_dynasty_note"] = _historical_tuned_note(
        tuned_row.get("direction_vs_emergency_candidate_rank"),
        tuned_row.get("main_reason_to_pass"),
    )
    frame.at[index, "candidate_action_summary"] = _candidate_display_value(
        tuned_row.get("main_reason_to_draft")
    )
    frame.at[index, "source_note"] = (
        "Historical Tuned Candidate / Review-Only; does not replace Final Board Rank "
        "or Dynasty Rank; no verified full historical dropped-veteran panel; ADP is "
        "display-only price context."
    )


def _historical_tuned_note(direction: object, reason: object) -> str:
    direction_text = str(direction or "").strip()
    reason_text = str(reason or "").strip()
    pieces = [
        "Historical Tuned Candidate / Review-Only",
        "does not replace Final Board Rank",
    ]
    if direction_text:
        pieces.append(direction_text)
    if reason_text:
        pieces.append(reason_text)
    pieces.append("Use human judgment; historical dropped-veteran panel is incomplete.")
    return "; ".join(pieces)


def _overlay_tuned_v2_candidate_rows(base_frame: pd.DataFrame) -> pd.DataFrame:
    if not TUNED_V2_CANDIDATE_PATH.exists():
        return base_frame
    try:
        tuned = pd.read_csv(TUNED_V2_CANDIDATE_PATH, dtype=str).fillna("")
    except Exception:
        return base_frame
    if hidden_sort_columns(tuned.columns):
        return base_frame
    required = {"player", "pos", "tuned_v2_cross_asset_rank", "tuned_v2_cross_asset_value"}
    if not required.issubset(tuned.columns):
        return base_frame

    merged = base_frame.copy()
    base_lookup = {
        _player_identity_key(row.get("player"), row.get("pos")): index
        for index, row in merged.iterrows()
    }
    for _, tuned_row in tuned.iterrows():
        key = _player_identity_key(tuned_row.get("player"), tuned_row.get("pos"))
        if key not in base_lookup:
            continue
        index = base_lookup[key]
        _apply_tuned_v2_candidate_row(merged, index, tuned_row)
    return merged


def _apply_tuned_v2_candidate_row(
    frame: pd.DataFrame,
    index: int,
    tuned_row: pd.Series,
) -> None:
    mapping = {
        "tuned_v2_cross_asset_rank": "cross_asset_candidate_rank",
        "tuned_v2_cross_asset_value": "cross_asset_candidate_value",
        "confidence_band": "confidence_band",
        "uncertainty_reasons": "uncertainty_reasons",
        "outcome_applicable_summary": "outcome_applicable_summary",
        "adp": "adp",
        "available_pool_adp_rank": "available_pool_adp_rank",
        "available_pool_adp_range": "available_pool_adp_range",
        "current_pick_value_1_03": "current_pick_value_1_03",
        "current_pick_value_1_04": "current_pick_value_1_04",
        "current_pick_value_1_09": "current_pick_value_1_09",
        "current_pick_value_2_04": "current_pick_value_2_04",
        "current_pick_value_2_08": "current_pick_value_2_08",
        "horizon_2026_band": "horizon_2026_band",
        "horizon_2027_band": "horizon_2027_band",
        "horizon_next5y_band": "horizon_next5y_band",
        "human_review_priority": "manual_review_flag",
    }
    for source, target in mapping.items():
        if source in tuned_row.index:
            frame.at[index, target] = _candidate_display_value(tuned_row.get(source))
    if "tuned_v2_cross_asset_value" in tuned_row.index:
        value = _candidate_display_value(tuned_row.get("tuned_v2_cross_asset_value"))
        frame.at[index, "candidate_value_band"] = _tuned_v2_value_band(value)
    frame.at[index, "candidate_vs_frozen_note"] = _tuned_v2_note(
        tuned_row.get("rank_delta_vs_frozen"),
        tuned_row.get("reason_to_draft"),
    )
    frame.at[index, "candidate_vs_dynasty_note"] = _tuned_v2_note(
        tuned_row.get("rank_delta_vs_current_candidate"),
        tuned_row.get("reason_to_pass"),
    )
    frame.at[index, "candidate_action_summary"] = _candidate_display_value(
        tuned_row.get("reason_to_draft")
    )
    frame.at[index, "current_pick_value"] = _candidate_display_value(
        tuned_row.get("current_pick_value_1_03")
    )
    frame.at[index, "current_pick_value_reason"] = (
        "Tuned V2 Candidate / Review-Only pick-window label. ADP/range is "
        "display-only and does not drive internal value."
    )
    frame.at[index, "source_note"] = _candidate_display_value(
        tuned_row.get("source_note")
    )


def _tuned_v2_value_band(value: object) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return OUTCOME_NOT_ENOUGH_INFORMATION
    if numeric >= 58:
        return "Priority review target"
    if numeric >= 50:
        return "Strong review target"
    if numeric >= 38:
        return "Viable with caveats"
    if numeric >= 24:
        return "Depth / format-dependent"
    return "Human-review hold"


def _tuned_v2_note(delta: object, reason: object) -> str:
    delta_text = str(delta or "").strip()
    reason_text = str(reason or "").strip()
    pieces = [
        "Tuned V2 Candidate / Review-Only",
        "does not replace Final Board Rank",
    ]
    if delta_text:
        pieces.append(f"rank delta {delta_text}")
    if reason_text:
        pieces.append(reason_text)
    pieces.append("ADP is display-only; no verified full historical dropped-veteran panel.")
    return "; ".join(pieces)


def integrate_cross_asset_candidate_context(
    frame: pd.DataFrame,
    *,
    name_column: str,
    position_column: str,
) -> pd.DataFrame:
    candidate = load_cross_asset_candidate_board()
    enriched = frame.copy()
    for column in CROSS_ASSET_DISPLAY_COLUMNS:
        if column not in enriched.columns:
            enriched[column] = OUTCOME_NOT_ENOUGH_INFORMATION
    if (
        candidate.empty
        or name_column not in enriched.columns
        or position_column not in enriched.columns
    ):
        return enriched

    lookup = {
        _player_identity_key(row.get("player"), row.get("pos")): row
        for row in candidate.to_dict("records")
    }
    for index, row in enriched.iterrows():
        key = _player_identity_key(row.get(name_column), row.get(position_column))
        candidate_row = lookup.get(key)
        if not candidate_row:
            continue
        for column in CROSS_ASSET_DISPLAY_COLUMNS:
            enriched.at[index, column] = _candidate_display_value(candidate_row.get(column))
        enriched.at[index, "candidate_key_caveat"] = _candidate_key_caveat(candidate_row)
    return enriched


CROSS_ASSET_DISPLAY_COLUMNS = (
    "cross_asset_candidate_rank",
    "cross_asset_candidate_value",
    "emergency_cross_asset_rank",
    "emergency_cross_asset_value",
    "emergency_overall_context_rank",
    "candidate_value_band",
    "confidence_band",
    "uncertainty_reasons",
    "candidate_vs_frozen_note",
    "candidate_vs_dynasty_note",
    "candidate_action_summary",
    "adp",
    "adp_source_status",
    "available_pool_adp_rank",
    "available_pool_adp_range",
    "current_pick_value_1_03",
    "current_pick_value_1_04",
    "current_pick_value_1_09",
    "current_pick_value_2_04",
    "current_pick_value_2_08",
    "current_pick_value",
    "current_pick_value_reason",
    "outcome_applicable_summary",
    "horizon_2026_band",
    "horizon_2027_band",
    "horizon_next5y_band",
    "manual_review_flag",
    "source_note",
    "candidate_key_caveat",
)


def _candidate_display_value(value: object) -> str:
    text = str(value or "").strip()
    return text if text else OUTCOME_NOT_ENOUGH_INFORMATION


def _candidate_key_caveat(row: dict[str, object]) -> str:
    manual = str(row.get("manual_review_flag", "")).strip().lower()
    confidence = str(row.get("confidence_band", "")).strip()
    reasons = [
        reason
        for reason in str(row.get("uncertainty_reasons", "")).split("; ")
        if reason
    ]
    important = [
        reason
        for reason in reasons
        if any(
            token in reason
            for token in (
                "manual_review",
                "critical",
                "needs_data",
                "Not enough information",
                "score_basis",
                "no_full_dynasty",
            )
        )
    ]
    pieces: list[str] = []
    if confidence:
        pieces.append(f"Confidence: {confidence}")
    if manual in {"yes", "true", "1", "human_decision_only"}:
        pieces.append("Manual review")
    pieces.extend(important[:2])
    return "; ".join(pieces) if pieces else "Review-only candidate context"


def validate_outcome_numeric_display(frame: pd.DataFrame) -> tuple[str, ...]:
    errors: list[str] = []
    required = (
        "player_id",
        "player_display_name",
        "position",
        "outcome_status",
        *(source for source, _target, _label in APPROVED_OUTCOME_DISPLAY_FIELDS),
    )
    missing = [column for column in required if column not in frame.columns]
    if missing:
        errors.append(f"Missing Outcome V1 display fields: {', '.join(missing)}.")
    hidden_like = hidden_sort_columns(frame.columns)
    if hidden_like:
        errors.append(
            f"Hidden/private sort-like columns are not allowed: {', '.join(hidden_like)}."
        )
    blocked_heads = [
        column
        for column in frame.columns
        if "top_6" in column.lower() or "top6" in column.lower()
    ]
    if blocked_heads:
        errors.append(f"Blocked unapproved Outcome heads are present: {', '.join(blocked_heads)}.")
    return tuple(errors)


def integrate_outcome_display_context(frame: pd.DataFrame) -> pd.DataFrame:
    outcome = load_outcome_numeric_display()
    result = frame.copy()
    result["outcome_availability_display_only"] = OUTCOME_NOT_ENOUGH_INFORMATION
    for _source, target, _label in APPROVED_OUTCOME_DISPLAY_FIELDS:
        result[target] = OUTCOME_NOT_ENOUGH_INFORMATION
    if not outcome.loaded or "player_id" not in result.columns:
        return result

    outcome_columns = [
        "player_id",
        "outcome_status",
        *(source for source, _target, _label in APPROVED_OUTCOME_DISPLAY_FIELDS),
    ]
    outcome_frame = outcome.frame.loc[:, outcome_columns].copy()
    merged = result.merge(
        outcome_frame,
        on="player_id",
        how="left",
        suffixes=("", "_outcome"),
    )
    merged["outcome_availability_display_only"] = merged["outcome_status"].map(
        outcome_availability_label
    )
    for source, target, _label in APPROVED_OUTCOME_DISPLAY_FIELDS:
        merged[target] = merged[source].map(outcome_probability_display)
    display = apply_position_aware_outcome_values(merged)
    return display.drop(
        columns=[
            "outcome_status",
            *(source for source, _target, _label in APPROVED_OUTCOME_DISPLAY_FIELDS),
        ],
        errors="ignore",
    )


def outcome_probability_display(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return text


def outcome_availability_label(value: object) -> str:
    if str(value or "").strip().lower() == "available":
        return "Available"
    return OUTCOME_NOT_ENOUGH_INFORMATION


def outcome_display_targets() -> tuple[str, ...]:
    return tuple(target for _source, target, _label in APPROVED_OUTCOME_DISPLAY_FIELDS)


def outcome_targets_for_positions(positions: Iterable[object]) -> tuple[str, ...]:
    normalized = {str(position or "").strip().upper() for position in positions}
    return tuple(
        target
        for target, position in OUTCOME_DISPLAY_FIELD_POSITIONS.items()
        if position in normalized
    )


def apply_position_aware_outcome_values(frame: pd.DataFrame) -> pd.DataFrame:
    """Render wrong-position Outcome heads as N/A without changing source artifacts."""

    if frame.empty or "position" not in frame.columns:
        return frame.copy()
    display = frame.copy()
    for target, target_position in OUTCOME_DISPLAY_FIELD_POSITIONS.items():
        if target not in display.columns:
            continue
        applicable = display["position"].astype(str).str.upper().eq(target_position)
        display.loc[~applicable, target] = OUTCOME_NOT_APPLICABLE
        display.loc[applicable, target] = display.loc[applicable, target].map(
            outcome_probability_display
        )
    return display


def outcome_columns_for_display(
    *,
    outcome_mode: str,
    selected_positions: Iterable[object],
) -> tuple[str, ...]:
    if outcome_mode == OUTCOME_DISPLAY_MODE_HIDE:
        return ()
    if outcome_mode == OUTCOME_DISPLAY_MODE_ALL:
        return outcome_display_targets()
    return outcome_targets_for_positions(selected_positions)


def outcome_display_coverage_counts(frame: pd.DataFrame) -> dict[str, int]:
    rows = int(frame.shape[0])
    if "outcome_availability_display_only" not in frame.columns:
        return {"rows": rows, "available": 0, "not_enough_information": rows}
    available = int(frame["outcome_availability_display_only"].astype(str).eq("Available").sum())
    return {
        "rows": rows,
        "available": available,
        "not_enough_information": rows - available,
    }


def frozen_board_outcome_support_counts(frame: pd.DataFrame) -> dict[str, int]:
    rows = int(frame.shape[0])
    outcome = load_outcome_numeric_display()
    if not outcome.loaded:
        return {"rows": rows, "supported": 0, "unsupported": rows}
    available = outcome.frame.loc[
        outcome.frame["outcome_status"].astype(str).str.lower().eq("available")
    ]
    board_keys = _player_identity_keys(frame, name_column="player")
    available_keys = _player_identity_keys(available, name_column="player_display_name")
    supported = len(board_keys & available_keys)
    return {"rows": rows, "supported": supported, "unsupported": rows - supported}


def build_unified_player_board(
    dynasty_frame: pd.DataFrame,
    frozen_board_frame: pd.DataFrame,
) -> pd.DataFrame:
    dynasty = dynasty_frame.copy()
    board = frozen_board_frame.copy()
    if dynasty.empty and board.empty:
        return pd.DataFrame()

    board_by_id = _rows_by_player_id(board)
    board_by_identity = _rows_by_player_identity(board, name_column="player")
    dynasty_ids = _player_id_set(dynasty)
    dynasty_identity_keys = _player_identity_keys(dynasty, name_column="player_name")
    rows: list[dict[str, object]] = []
    for row in dynasty.to_dict("records"):
        player_id = _clean_text(row.get("player_id"))
        identity_key = _player_identity_key(
            row.get("player_name"),
            row.get("position"),
        )
        board_row = board_by_id.get(player_id, {}) or board_by_identity.get(identity_key, {})
        merged = dict(row)
        merged["source_coverage"] = (
            "Full Dynasty source + Frozen Baseline"
            if board_row
            else "Full Dynasty source"
        )
        merged["asset_type_display"] = asset_type_display(row, board_row)
        for column in (
            "final_board_rank",
            "final_tier",
            "position_rank",
            "availability_status",
            "draft_action_display_only",
            "model_posture_used",
            "candidate_status",
            "risk_notes",
            "needs_manual_review",
        ):
            merged[column] = board_row.get(column, "")
        rows.append(merged)

    if not board.empty:
        board_only = board.loc[
            ~board.apply(
                lambda row: _board_row_matches_dynasty(row, dynasty_ids, dynasty_identity_keys),
                axis=1,
            )
        ].copy()
        board_only_rows = integrate_outcome_display_context(
            _board_only_rows_for_unified_player_board(board_only)
        )
        rows.extend(board_only_rows.to_dict("records"))

    unified = pd.DataFrame(rows)
    if unified.empty:
        return unified
    return sort_unified_player_board_for_view(unified, UNIFIED_REVIEW_VIEW)


def enrich_unified_player_board_with_market_baseline(frame: pd.DataFrame) -> pd.DataFrame:
    """Append display-only DynastyProcess market context without changing rank fields."""

    usage = get_market_baseline_page_usage("dynasty_rankings")
    if usage is None or not usage.enabled:
        return frame.copy()

    try:
        enriched = compute_market_sanity_flags(frame)
    except (FileNotFoundError, ValueError):
        enriched = frame.copy()
        enriched["market_baseline_label"] = MARKET_BASELINE_DISPLAY_LABEL
        enriched["market_sanity_label"] = "No market match"
        enriched["market_gap"] = ""
        enriched["dp_value_1qb"] = ""
        enriched["dp_market_rank_1qb"] = ""
        enriched["dp_ecr_pos"] = ""
        enriched["dp_age"] = ""
        enriched["market_join_confidence"] = "market unavailable / manual review"
        enriched["freshness_status"] = ""
        enriched["market_baseline_stale_warning"] = "Market baseline unavailable."

    output = enriched.copy()
    if "age_source_display" not in output.columns:
        output["age_source_display"] = OUTCOME_NOT_ENOUGH_INFORMATION
    if "market_age_fallback_used" not in output.columns:
        output["market_age_fallback_used"] = False
    if "age" not in output.columns:
        output["age"] = OUTCOME_NOT_ENOUGH_INFORMATION
    if "dp_age" not in output.columns:
        output["dp_age"] = ""

    for index, row in output.iterrows():
        nwr_age = age_display_value(row.get("age"))
        dp_age = age_display_value(row.get("dp_age"))
        if nwr_age != OUTCOME_NOT_ENOUGH_INFORMATION:
            output.at[index, "age"] = nwr_age
            output.at[index, "age_source_display"] = "NWR approved source"
        elif dp_age != OUTCOME_NOT_ENOUGH_INFORMATION:
            output.at[index, "age"] = dp_age
            output.at[index, "age_source_display"] = (
                "Market Baseline / Display-Only fallback"
            )
            output.at[index, "market_age_fallback_used"] = True
        else:
            output.at[index, "age"] = OUTCOME_NOT_ENOUGH_INFORMATION
            output.at[index, "age_source_display"] = OUTCOME_NOT_ENOUGH_INFORMATION

    return output


def market_baseline_age_coverage(frame: pd.DataFrame) -> dict[str, int]:
    """Return display age coverage before/after optional market fallback."""

    before = 0
    if "age" in frame.columns:
        before = int(
            frame["age"].map(age_display_value).ne(OUTCOME_NOT_ENOUGH_INFORMATION).sum()
        )
    enriched = enrich_unified_player_board_with_market_baseline(frame)
    after = int(
        enriched["age"].map(age_display_value).ne(OUTCOME_NOT_ENOUGH_INFORMATION).sum()
    )
    fallback = int(enriched.get("market_age_fallback_used", pd.Series(dtype=bool)).sum())
    return {"before": before, "after": after, "market_fallback": fallback}


def market_baseline_join_coverage(frame: pd.DataFrame) -> dict[str, int]:
    enriched = enrich_unified_player_board_with_market_baseline(frame)
    rows = int(enriched.shape[0])
    matched = int(
        enriched.get("market_sanity_label", pd.Series(dtype=str))
        .astype(str)
        .ne("No market match")
        .sum()
    )
    return {"rows": rows, "matched": matched, "unmatched": rows - matched}


def market_baseline_freshness_status() -> dict[str, str]:
    try:
        return load_market_freshness()
    except (FileNotFoundError, ValueError):
        return {
            "freshness_status": "RED_NO_VALID_CACHE",
            "upstream_scrape_date": "",
            "market_baseline_stale_warning": "Market baseline unavailable.",
        }


def sort_unified_player_board_for_view(frame: pd.DataFrame, view_mode: str) -> pd.DataFrame:
    """Sort display rows without changing any rank/value fields."""

    if frame.empty:
        return frame.copy()
    sorted_frame = frame.copy()
    sorted_frame["_dynasty_sort"] = pd.to_numeric(
        sorted_frame.get("nwr_rank", pd.Series(dtype=str)),
        errors="coerce",
    )
    sorted_frame["_board_sort"] = pd.to_numeric(
        sorted_frame.get("final_board_rank", pd.Series(dtype=str)),
        errors="coerce",
    )
    sorted_frame["_has_dynasty_rank_sort"] = sorted_frame["_dynasty_sort"].notna().map(
        {True: 0, False: 1}
    )

    if view_mode == ROOKIES_DRAFT_BOARD_VIEW:
        by = ["_board_sort", "_has_dynasty_rank_sort", "_dynasty_sort", "player_name"]
        ascending = [True, True, True, True]
    else:
        by = ["_has_dynasty_rank_sort", "_dynasty_sort", "_board_sort", "player_name"]
        ascending = [True, True, True, True]

    return (
        sorted_frame.sort_values(
            by=by,
            ascending=ascending,
            na_position="last",
            kind="stable",
        )
        .drop(columns=["_dynasty_sort", "_board_sort", "_has_dynasty_rank_sort"])
        .reset_index(drop=True)
    )


def display_unified_player_board_frame(
    frame: pd.DataFrame,
    view_mode: str = UNIFIED_REVIEW_VIEW,
    outcome_mode: str = OUTCOME_DISPLAY_MODE_POSITION_APPLICABLE,
    selected_positions: Iterable[object] | None = None,
    show_market_baseline: bool = False,
) -> pd.DataFrame:
    if view_mode == FULL_DYNASTY_VIEW:
        display_columns = FULL_DYNASTY_PLAYER_BOARD_DISPLAY_COLUMNS
    elif view_mode == ROOKIES_DRAFT_BOARD_VIEW:
        display_columns = ROOKIES_DRAFT_BOARD_DISPLAY_COLUMNS
    else:
        display_columns = UNIFIED_PLAYER_BOARD_DISPLAY_COLUMNS
    if show_market_baseline:
        display_columns = _display_columns_with_market_baseline(display_columns)
    selected_positions = selected_positions or frame.get("position", pd.Series(dtype=str))
    outcome_targets = set(
        outcome_columns_for_display(
            outcome_mode=outcome_mode,
            selected_positions=selected_positions,
        )
    )
    if outcome_mode == OUTCOME_DISPLAY_MODE_HIDE:
        display_columns = tuple(
            column
            for column in display_columns
            if column not in outcome_display_targets()
            and column != "outcome_availability_display_only"
        )
    else:
        display_columns = tuple(
            column
            for column in display_columns
            if column not in outcome_display_targets() or column in outcome_targets
        )
    available = [column for column in display_columns if column in frame.columns]
    display = apply_position_aware_outcome_values(frame).loc[:, available].copy()
    if "warning_flags" in display.columns:
        display["warning_flags"] = display["warning_flags"].map(warning_summary)
    if "age" in display.columns:
        display["age"] = display["age"].map(age_display_value)
    for column in MISSING_INFORMATION_DISPLAY_COLUMNS:
        if column in display.columns:
            display[column] = display[column].map(not_enough_information_display_value)
    display = display.fillna("").astype(str)
    return display.rename(columns=UNIFIED_PLAYER_BOARD_DISPLAY_LABELS)


def _display_columns_with_market_baseline(display_columns: tuple[str, ...]) -> tuple[str, ...]:
    insert_after = "nwr_dynasty_score"
    if insert_after not in display_columns:
        insert_after = "age" if "age" in display_columns else display_columns[-1]
    split_index = display_columns.index(insert_after) + 1
    before = display_columns[:split_index]
    after = tuple(
        column
        for column in display_columns[split_index:]
        if column not in MARKET_BASELINE_DISPLAY_COLUMNS
    )
    return (*before, *MARKET_BASELINE_DISPLAY_COLUMNS, *after)


MISSING_INFORMATION_DISPLAY_COLUMNS = (
    "nfl_team",
    "nwr_position_rank",
    "position_rank",
    "candidate_value_band",
    "nwr_dynasty_score",
    "trust_status",
    "confidence_band",
    "candidate_key_caveat",
    "dp_value_1qb",
    "dp_market_rank_1qb",
    "dp_ecr_pos",
    "dp_age",
    "market_gap",
    "age_source_display",
)


def not_enough_information_display_value(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return text


def _board_only_rows_for_unified_player_board(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in frame.to_dict("records"):
        rows.append(
            {
                "player_id": row.get("player_id", ""),
                "source_coverage": "Frozen Baseline only",
                "nwr_rank": "Frozen-baseline only",
                "final_board_rank": row.get("final_board_rank", ""),
                "final_tier": row.get("final_tier", ""),
                "position_rank": row.get("position_rank", ""),
                "player_name": row.get("player", ""),
                "position": row.get("position", ""),
                "age": row.get("age", OUTCOME_NOT_ENOUGH_INFORMATION),
                "nfl_team": row.get("nfl_team", ""),
                "asset_type_display": row.get("asset_type", "Frozen-baseline only"),
                "availability_status": row.get("availability_status", ""),
                "draft_action_display_only": row.get("draft_action_display_only", ""),
                "nwr_dynasty_score": OUTCOME_NOT_ENOUGH_INFORMATION,
                "trust_status": "Frozen-baseline only",
                "warning_flags": "",
                "pool_status": "Frozen-baseline only",
                "data_needed": "Frozen-baseline only",
                "model_posture_used": row.get("model_posture_used", ""),
                "candidate_status": row.get("candidate_status", ""),
                "risk_notes": row.get("risk_notes", ""),
                "needs_manual_review": row.get("needs_manual_review", ""),
            }
        )
    return pd.DataFrame(rows)


def _rows_by_player_id(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if "player_id" not in frame.columns:
        return {}
    rows: dict[str, dict[str, object]] = {}
    for row in frame.to_dict("records"):
        player_id = _clean_text(row.get("player_id"))
        if player_id:
            rows[player_id] = row
    return rows


def _rows_by_player_identity(
    frame: pd.DataFrame,
    *,
    name_column: str,
) -> dict[tuple[str, str], dict[str, object]]:
    rows: dict[tuple[str, str], dict[str, object]] = {}
    if name_column not in frame.columns or "position" not in frame.columns:
        return rows
    for row in frame.to_dict("records"):
        identity_key = _player_identity_key(row.get(name_column), row.get("position"))
        if identity_key != ("", ""):
            rows[identity_key] = row
    return rows


def _player_id_set(frame: pd.DataFrame) -> set[str]:
    if "player_id" not in frame.columns:
        return set()
    return {
        str(player_id).strip()
        for player_id in frame["player_id"]
        if str(player_id).strip()
    }


def _player_identity_keys(frame: pd.DataFrame, *, name_column: str) -> set[tuple[str, str]]:
    if name_column not in frame.columns or "position" not in frame.columns:
        return set()
    return {
        _player_identity_key(row.get(name_column), row.get("position"))
        for row in frame.to_dict("records")
        if _player_identity_key(row.get(name_column), row.get("position")) != ("", "")
    }


def _board_row_matches_dynasty(
    row: pd.Series,
    dynasty_ids: set[str],
    dynasty_identity_keys: set[tuple[str, str]],
) -> bool:
    player_id = _clean_text(row.get("player_id"))
    if player_id and player_id in dynasty_ids:
        return True
    return _player_identity_key(row.get("player"), row.get("position")) in dynasty_identity_keys


def _player_identity_key(name: object, position: object) -> tuple[str, str]:
    normalized_name = re.sub(r"[^a-z0-9]+", "", str(name or "").casefold())
    normalized_position = str(position or "").strip().upper()
    return normalized_name, normalized_position


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def normalize_dynasty_rankings_frame(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    if "age" in normalized.columns:
        normalized["age"] = normalized["age"].map(age_display_value)
    else:
        normalized["age"] = OUTCOME_NOT_ENOUGH_INFORMATION
    normalized = enrich_display_age_from_roster_context(
        normalized,
        name_column="player_name",
    )
    if "nwr_rank" in normalized.columns:
        normalized["_rank_sort_visible"] = pd.to_numeric(
            normalized["nwr_rank"], errors="coerce"
        )
        normalized = normalized.sort_values(
            by=["_rank_sort_visible", "player_name"],
            ascending=[True, True],
            na_position="last",
            kind="stable",
        ).drop(columns=["_rank_sort_visible"])
    normalized = add_nwr_position_rank_display(normalized)
    return normalized.reset_index(drop=True)


def add_nwr_position_rank_display(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive an in-memory position-rank display from approved NWR overall rank."""

    if frame.empty or "position" not in frame.columns or "nwr_rank" not in frame.columns:
        return frame.copy()
    ranked = frame.copy()
    ranked["nwr_position_rank"] = OUTCOME_NOT_ENOUGH_INFORMATION
    rank_values = pd.to_numeric(ranked["nwr_rank"], errors="coerce")
    position_values = ranked["position"].astype(str).str.upper().str.strip()
    for position in sorted(position_values[rank_values.notna()].unique().tolist()):
        mask = rank_values.notna() & position_values.eq(position)
        position_frame = ranked.loc[mask].copy()
        position_frame["_rank_sort_visible"] = rank_values.loc[mask]
        ordered_indices = position_frame.sort_values(
            by=["_rank_sort_visible", "player_name"],
            ascending=[True, True],
            na_position="last",
            kind="stable",
        ).index.tolist()
        for rank, index in enumerate(ordered_indices, start=1):
            ranked.at[index, "nwr_position_rank"] = f"{position}{rank}"
    return ranked


def display_dynasty_rankings_frame(frame: pd.DataFrame) -> pd.DataFrame:
    available = [column for column in DYNASTY_DISPLAY_COLUMNS if column in frame.columns]
    display = frame.loc[:, available].copy()
    if "warning_flags" in display.columns:
        display["warning_flags"] = display["warning_flags"].map(warning_summary)
    if "market_rank" in display.columns:
        display = display.rename(columns={"market_rank": "Market Rank (Display-Only)"})
    if "league_rank" in display.columns:
        display = display.rename(columns={"league_rank": "League Rank (Display-Only)"})
    if "age" in display.columns:
        display["age"] = display["age"].map(age_display_value)
    return display.rename(columns=DYNASTY_DISPLAY_LABELS)


def age_display_value(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "age missing"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    try:
        return f"{float(text):.1f}"
    except ValueError:
        return text


def enrich_display_age_from_roster_context(
    frame: pd.DataFrame,
    *,
    name_column: str,
) -> pd.DataFrame:
    """Fill missing display age from approved roster DOB context without mutating sources."""

    if frame.empty or name_column not in frame.columns or "position" not in frame.columns:
        return frame
    lookup = roster_age_context_lookup()
    if not lookup:
        return frame
    enriched = frame.copy()
    if "age" not in enriched.columns:
        enriched["age"] = OUTCOME_NOT_ENOUGH_INFORMATION
    for index, row in enriched.iterrows():
        current = age_display_value(row.get("age"))
        if current != OUTCOME_NOT_ENOUGH_INFORMATION:
            enriched.at[index, "age"] = current
            continue
        key = _player_identity_key(row.get(name_column), row.get("position"))
        enriched.at[index, "age"] = lookup.get(key, OUTCOME_NOT_ENOUGH_INFORMATION)
    return enriched


def enrich_display_age_from_rookie_birthdate_audit(frame: pd.DataFrame) -> pd.DataFrame:
    """Fill display age only from the derived verified rookie-age audit artifact."""

    if frame.empty or "player" not in frame.columns or "position" not in frame.columns:
        return frame
    lookup = rookie_birthdate_audit_age_lookup()
    if not lookup:
        return frame
    enriched = frame.copy()
    if "age" not in enriched.columns:
        enriched["age"] = OUTCOME_NOT_ENOUGH_INFORMATION
    for index, row in enriched.iterrows():
        current = age_display_value(row.get("age"))
        if current != OUTCOME_NOT_ENOUGH_INFORMATION:
            enriched.at[index, "age"] = current
            continue
        key = _player_identity_key(row.get("player"), row.get("position"))
        enriched.at[index, "age"] = lookup.get(key, OUTCOME_NOT_ENOUGH_INFORMATION)
    return enriched


@lru_cache(maxsize=1)
def rookie_birthdate_audit_age_lookup() -> dict[tuple[str, str], str]:
    if not ROOKIE_VERIFIED_AGE_DISPLAY_PATH.exists():
        return {}
    try:
        frame = pd.read_csv(ROOKIE_VERIFIED_AGE_DISPLAY_PATH, dtype=str).fillna("")
    except Exception:
        return {}
    required = {"player", "position", "age", "verification_status"}
    if not required.issubset(frame.columns):
        return {}
    lookup: dict[tuple[str, str], str] = {}
    for row in frame.to_dict("records"):
        if row.get("verification_status") != "multi_source_birthdate_match":
            continue
        age = age_display_value(row.get("age"))
        if age == OUTCOME_NOT_ENOUGH_INFORMATION:
            continue
        key = _player_identity_key(row.get("player"), row.get("position"))
        if key != ("", ""):
            lookup[key] = age
    return lookup


@lru_cache(maxsize=1)
def roster_age_context_lookup() -> dict[tuple[str, str], str]:
    if not ROSTER_AGE_CONTEXT_PATH.exists():
        return {}
    try:
        frame = pd.read_csv(ROSTER_AGE_CONTEXT_PATH, dtype=str).fillna("")
    except Exception:
        return {}
    lookup: dict[tuple[str, str], str] = {}
    required = {"full_name", "position", "birth_date"}
    if not required.issubset(frame.columns):
        return {}
    if "live_use_allowed" in frame.columns:
        frame = frame.loc[frame["live_use_allowed"].astype(str).str.lower().eq("true")].copy()
    for row in frame.to_dict("records"):
        age = age_from_birth_date(row.get("birth_date"))
        if age == OUTCOME_NOT_ENOUGH_INFORMATION:
            continue
        key = _player_identity_key(row.get("full_name"), row.get("position"))
        if key != ("", ""):
            lookup[key] = age
    return lookup


def age_from_birth_date(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    try:
        born = date.fromisoformat(text[:10])
    except ValueError:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    years = (AGE_AS_OF_DATE - born).days / 365.2425
    if years <= 0:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return f"{years:.1f}"


def asset_type_display(row: dict[str, object], board_row: dict[str, object]) -> str:
    board_asset = _clean_text(board_row.get("asset_type"))
    if board_asset:
        return board_asset
    is_rookie = _clean_text(row.get("is_rookie")).lower()
    if is_rookie in {"1", "true", "yes"}:
        return "rookie"
    if row:
        return "veteran"
    return OUTCOME_NOT_ENOUGH_INFORMATION


def warning_summary(value: object) -> str:
    flags = [flag for flag in str(value or "").split("|") if flag]
    if not flags:
        return "0"
    return f"{len(flags)} warning{'s' if len(flags) != 1 else ''}"


def file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_board_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "final_board_rank",
        "final_tier",
        "position_rank",
        "player",
        "position",
        "nfl_team",
        "model_posture_used",
        "candidate_status",
        "risk_notes",
        "needs_manual_review",
    ]
    available = [column for column in columns if column in frame.columns]
    return frame.loc[:, available].rename(columns=DISPLAY_LABELS)


def display_lane_prop_frame(frame: pd.DataFrame) -> pd.DataFrame:
    technical = [column for column in PROP_TECHNICAL_DISPLAY_COLUMNS if column in frame.columns]
    if not technical:
        return frame.copy()
    return frame.drop(columns=technical)


def outcome_prop_match_counts(frame: pd.DataFrame) -> dict[str, int]:
    rows = int(frame.shape[0])
    if "match_status" not in frame.columns:
        return {"rows": rows, "matched": 0, "unmatched": rows}
    matched = int(frame["match_status"].astype(str).eq("matched_name_position").sum())
    return {"rows": rows, "matched": matched, "unmatched": rows - matched}


DISPLAY_LABELS = {
    "final_board_rank": "Final Board Rank",
    "final_tier": "Final Tier",
    "position_rank": "Position Rank",
    "player": "Player",
    "position": "Pos",
    "nfl_team": "NFL Team",
    "model_posture_used": "Model Posture Used",
    "candidate_status": "Candidate Status",
    "risk_notes": "Risk Notes",
    "needs_manual_review": "Needs Manual Review",
    "final_board_score_visible": "Visible Board Score",
    "source_status": "Source Status",
    "guardrail_status": "Guardrail Status",
}

DYNASTY_DISPLAY_LABELS = {
    "nwr_rank": "Dynasty Rank",
    "player_name": "Player",
    "position": "Pos",
    "age": "Age",
    "nfl_team": "NFL Team",
    "nwr_dynasty_score": "NWR Dynasty Score",
    "trust_status": "Trust",
    "warning_flags": "Warnings",
    "pool_status": "Status",
    "data_needed": "Data Needed",
    "outcome_availability_display_only": "Outcome Availability (Display-Only)",
    "qb_t12_display_only": "QB T12",
    "rb_t12_display_only": "RB T12",
    "rb_t24_display_only": "RB T24",
    "wr_t12_display_only": "WR T12",
    "wr_t24_display_only": "WR T24",
    "wr_t36_display_only": "WR T36",
    "te_t12_display_only": "TE T12",
}

UNIFIED_PLAYER_BOARD_DISPLAY_LABELS = {
    "source_coverage": "Source Coverage",
    "nwr_rank": "Dynasty Rank",
    "cross_asset_candidate_rank": "Tuned V2 Candidate Rank (Review-Only)",
    "cross_asset_candidate_value": "Tuned V2 Candidate Value (Review-Only)",
    "candidate_value_band": "Value Band (Review-Only)",
    "confidence_band": "Confidence",
    "available_pool_adp_range": "Available-Pool ADP Range (Display-Only)",
    "current_pick_value": "Current Pick Value (Display-Only)",
    "horizon_2026_band": "2026 Horizon Band (Review-Only)",
    "horizon_2027_band": "2027 Horizon Band (Review-Only)",
    "horizon_next5y_band": "Next-5Y Horizon Band (Review-Only)",
    "candidate_key_caveat": "Main Caveat",
    "final_board_rank": "Final Board Rank",
    "final_tier": "Final Tier",
    "position_rank": "Position Rank",
    "nwr_position_rank": "Position Rank",
    "player_name": "Player",
    "position": "Pos",
    "age": "Age",
    "nfl_team": "NFL Team",
    "asset_type_display": "Asset Type",
    "availability_status": "Board Availability",
    "draft_action_display_only": "Draft Action (Display-Only)",
    "nwr_dynasty_score": "NWR Dynasty Score",
    "trust_status": "Data Trust",
    "warning_flags": "Warnings",
    "pool_status": "Status",
    "data_needed": "Data Needed",
    "model_posture_used": "Model Posture Used",
    "candidate_status": "Candidate Status",
    "risk_notes": "Risk Notes",
    "needs_manual_review": "Review Needed",
    "outcome_availability_display_only": "Outcome Availability (Display-Only)",
    "qb_t12_display_only": "QB T12 (Display-Only)",
    "rb_t12_display_only": "RB T12 (Display-Only)",
    "rb_t24_display_only": "RB T24 (Display-Only)",
    "wr_t12_display_only": "WR T12 (Display-Only)",
    "wr_t24_display_only": "WR T24 (Display-Only)",
    "wr_t36_display_only": "WR T36 (Display-Only)",
    "te_t12_display_only": "TE T12 (Display-Only)",
    "dp_value_1qb": "DP 1QB Value (Market Baseline / Display-Only)",
    "dp_market_rank_1qb": "DP 1QB Market Rank (Market Baseline / Display-Only)",
    "dp_ecr_pos": "DP ECR Pos (Market Baseline / Display-Only)",
    "dp_age": "DP Age (Market Baseline / Display-Only)",
    "market_gap": "NWR vs Market Gap (Market Baseline / Display-Only)",
    "market_sanity_label": "Market Sanity Flag (Market Baseline / Display-Only)",
    "age_source_display": "Age Source",
    "market_baseline_label": "Market Baseline Label",
}


def manual_review_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if "needs_manual_review" not in frame.columns:
        return pd.DataFrame()
    mask = frame["needs_manual_review"].astype(str).str.lower().isin({"true", "yes", "1"})
    return display_board_frame(frame.loc[mask])


def best_available_frame(frame: pd.DataFrame, taken_players: Iterable[str]) -> pd.DataFrame:
    taken = {str(player) for player in taken_players}
    if "player" not in frame.columns:
        return frame.copy()
    return frame.loc[~frame["player"].astype(str).isin(taken)].copy()


def lane_prop_status_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for lane in LANE_NAMES:
        folder, source_label = lane_prop_folder(lane)
        files = sorted(folder.glob("*")) if folder.exists() else []
        primary = lane_prop_path(lane, LANE_PROP_PRIMARY_FILES[lane])
        status = lane_prop_status_from_folder(lane, folder)
        if status == "MISSING":
            status = "GREEN" if primary and primary.exists() else "YELLOW-HOLD"
        rows.append(
            {
                "lane": lane,
                "status": status,
                "path": str(folder),
                "file_count": str(len([path for path in files if path.is_file()])),
                "primary_file": primary.name if primary else LANE_PROP_PRIMARY_FILES[lane],
                "source_label": source_label,
                "source_rule": (
                    "Must reference frozen Final Draft Board V1 as a baseline checkpoint; "
                    "not the full draftable-player universe."
                ),
            }
        )
    return rows


def lane_prop_status_from_folder(lane: str, folder: Path) -> str:
    status_file_name = LANE_STATUS_FILES.get(lane)
    if not status_file_name:
        return "MISSING"
    status_path = folder / status_file_name
    if not status_path.exists():
        return "MISSING"
    try:
        text = status_path.read_text(encoding="utf-8-sig")
    except OSError:
        return "YELLOW-HOLD"
    return extract_prop_status(text) or "YELLOW-HOLD"


def extract_prop_status(text: str) -> str | None:
    normalized = text.replace("\r\n", "\n")
    direct = re.search(
        r"(?im)^(?:Status|Verdict|Final verdict):\s*`?(GREEN|YELLOW-HOLD|YELLOW|RED)`?\s*$",
        normalized,
    )
    if direct:
        value = direct.group(1).upper()
        return "YELLOW-HOLD" if value == "YELLOW" else value
    heading = re.search(
        r"(?ims)^##\s+Verdict\s*\n+\s*`?(GREEN|YELLOW-HOLD|YELLOW|RED)`?\s*$",
        normalized,
    )
    if heading:
        value = heading.group(1).upper()
        return "YELLOW-HOLD" if value == "YELLOW" else value
    return None


def lane_prop_path(lane: str, file_name: str) -> Path | None:
    if lane not in LANE_PROP_PRIMARY_FILES:
        return None
    folder, _source_label = lane_prop_folder(lane)
    return folder / file_name


def first_lane_prop_csv(lane: str) -> Path | None:
    if lane not in LANE_PROP_PRIMARY_FILES:
        return None
    folder, _source_label = lane_prop_folder(lane)
    if not folder.exists():
        return None
    primary = lane_prop_path(lane, LANE_PROP_PRIMARY_FILES.get(lane, ""))
    if primary and primary.exists():
        return primary
    candidates = [
        path
        for path in sorted(folder.glob("*.csv"))
        if "manifest" not in path.name.lower() and "status" not in path.name.lower()
    ]
    if not candidates:
        return None
    preferred = [
        path
        for path in candidates
        if "player" in path.name.lower()
        or "context" in path.name.lower()
        or "flags" in path.name.lower()
    ]
    return (preferred or candidates)[0]


def load_lane_prop_frame(lane: str) -> tuple[pd.DataFrame, Path | None]:
    path = first_lane_prop_csv(lane)
    if path is None:
        return pd.DataFrame(), None
    return pd.read_csv(path).fillna(""), path


def load_lane_prop_file(lane: str, file_name: str) -> tuple[pd.DataFrame, Path | None]:
    path = lane_prop_path(lane, file_name)
    if path is None or not path.exists():
        return pd.DataFrame(), path
    return pd.read_csv(path).fillna(""), path


def lane_prop_file_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for lane in LANE_NAMES:
        folder, source_label = lane_prop_folder(lane)
        for path in sorted(folder.glob("*")) if folder.exists() else []:
            if path.is_dir():
                continue
            row_count = ""
            if path.suffix.lower() == ".csv":
                try:
                    row_count = str(pd.read_csv(path).shape[0])
                except (OSError, pd.errors.ParserError, UnicodeDecodeError):
                    row_count = "unreadable"
            rows.append(
                {
                    "lane": lane,
                    "file_name": path.name,
                    "status": "GREEN" if path.exists() else "YELLOW-HOLD",
                    "row_count": row_count,
                    "path": str(path),
                    "source_label": source_label,
                }
            )
    return rows


def pinned_manifest_hash() -> str | None:
    if not PINNED_SNAPSHOT_MANIFEST.exists():
        return None
    import hashlib

    digest = hashlib.sha256()
    with PINNED_SNAPSHOT_MANIFEST.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def draft_day_status_rows(bundle: FrozenBoardBundle) -> list[dict[str, str]]:
    pinned_hash = pinned_manifest_hash()
    return [
        {
            "check": "Frozen board loaded",
            "status": "GREEN" if bundle.loaded else "RED",
            "detail": str(bundle.source_path or "missing"),
        },
        {
            "check": "Row count",
            "status": "GREEN" if bundle.row_count == EXPECTED_ROW_COUNT else "RED",
            "detail": str(bundle.row_count),
        },
        {
            "check": "Manual flags count",
            "status": "GREEN",
            "detail": str(manual_review_frame(bundle.frame).shape[0]),
        },
        {
            "check": "Pinned manifest hash",
            "status": "GREEN"
            if pinned_hash == EXPECTED_PINNED_MANIFEST_HASH
            else "YELLOW-HOLD",
            "detail": pinned_hash or "missing",
        },
        {
            "check": "Hidden sort fields",
            "status": "GREEN" if not hidden_sort_columns(bundle.frame.columns) else "RED",
            "detail": ", ".join(hidden_sort_columns(bundle.frame.columns)) or "none",
        },
    ]
