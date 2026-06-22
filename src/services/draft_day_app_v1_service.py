from __future__ import annotations

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
BOARD_FILE_NAME = "FINAL_DRAFT_BOARD_V1_FROZEN.csv"
DYNASTY_BOARD_FILE_NAME = "full_player_board_value_review_rows.csv"
OUTCOME_NUMERIC_DISPLAY_FILE_NAME = "numeric_outcome_display_v1.csv"

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
UNIFIED_PLAYER_BOARD_DISPLAY_COLUMNS = (
    "nwr_rank",
    "final_board_rank",
    "player_name",
    "position",
    "nfl_team",
    "source_coverage",
    "final_tier",
    "position_rank",
    "age",
    "nwr_dynasty_score",
    "trust_status",
    "warning_flags",
    "pool_status",
    "data_needed",
    "model_posture_used",
    "candidate_status",
    "risk_notes",
    "needs_manual_review",
    "outcome_availability_display_only",
    "qb_t12_display_only",
    "rb_t12_display_only",
    "rb_t24_display_only",
    "wr_t12_display_only",
    "wr_t24_display_only",
    "wr_t36_display_only",
    "te_t12_display_only",
)
OUTCOME_NOT_ENOUGH_INFORMATION = "Not enough information"
APPROVED_OUTCOME_DISPLAY_FIELDS = (
    ("qb_t12_display_pct", "qb_t12_display_only", "QB T12"),
    ("rb_t12_display_pct", "rb_t12_display_only", "RB T12"),
    ("rb_t24_display_pct", "rb_t24_display_only", "RB T24"),
    ("wr_t12_display_pct", "wr_t12_display_only", "WR T12"),
    ("wr_t24_display_pct", "wr_t24_display_only", "WR T24"),
    ("wr_t36_display_pct", "wr_t36_display_only", "WR T36"),
    ("te_t12_display_pct", "te_t12_display_only", "TE T12"),
)


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
    return FrozenBoardBundle(
        frame=normalized,
        source_path=path,
        source_label=label,
        errors=tuple(errors),
        warnings=warnings,
    )


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
    normalized = integrate_outcome_display_context(normalize_dynasty_rankings_frame(frame))
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
    return merged.drop(
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
            "Full Dynasty source + Frozen Board"
            if board_row
            else "Full Dynasty source"
        )
        for column in (
            "final_board_rank",
            "final_tier",
            "position_rank",
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
    return sort_unified_player_board_for_view(unified, "Unified Review View")


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

    if view_mode == "Frozen Draft Board":
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


def display_unified_player_board_frame(frame: pd.DataFrame) -> pd.DataFrame:
    available = [
        column
        for column in UNIFIED_PLAYER_BOARD_DISPLAY_COLUMNS
        if column in frame.columns
    ]
    display = frame.loc[:, available].copy()
    if "warning_flags" in display.columns:
        display["warning_flags"] = display["warning_flags"].map(warning_summary)
    display = display.fillna("").astype(str)
    return display.rename(columns=UNIFIED_PLAYER_BOARD_DISPLAY_LABELS)


def _board_only_rows_for_unified_player_board(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in frame.to_dict("records"):
        rows.append(
            {
                "player_id": row.get("player_id", ""),
                "source_coverage": "Frozen Draft Board only",
                "nwr_rank": "Draft-board only",
                "final_board_rank": row.get("final_board_rank", ""),
                "final_tier": row.get("final_tier", ""),
                "position_rank": row.get("position_rank", ""),
                "player_name": row.get("player", ""),
                "position": row.get("position", ""),
                "age": OUTCOME_NOT_ENOUGH_INFORMATION,
                "nfl_team": row.get("nfl_team", ""),
                "nwr_dynasty_score": OUTCOME_NOT_ENOUGH_INFORMATION,
                "trust_status": "Draft-board only",
                "warning_flags": "",
                "pool_status": "Draft-board only",
                "data_needed": "Draft-board only",
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
    return normalized.reset_index(drop=True)


def display_dynasty_rankings_frame(frame: pd.DataFrame) -> pd.DataFrame:
    available = [column for column in DYNASTY_DISPLAY_COLUMNS if column in frame.columns]
    display = frame.loc[:, available].copy()
    if "warning_flags" in display.columns:
        display["warning_flags"] = display["warning_flags"].map(warning_summary)
    if "market_rank" in display.columns:
        display = display.rename(columns={"market_rank": "Market Rank (Display-Only)"})
    if "league_rank" in display.columns:
        display = display.rename(columns={"league_rank": "League Rank (Display-Only)"})
    return display.rename(columns=DYNASTY_DISPLAY_LABELS)


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
    "final_board_rank": "Final Board Rank",
    "final_tier": "Final Tier",
    "position_rank": "Position Rank",
    "player_name": "Player",
    "position": "Pos",
    "age": "Age",
    "nfl_team": "NFL Team",
    "nwr_dynasty_score": "NWR Dynasty Score",
    "trust_status": "Trust",
    "warning_flags": "Warnings",
    "pool_status": "Status",
    "data_needed": "Data Needed",
    "model_posture_used": "Model Posture Used",
    "candidate_status": "Candidate Status",
    "risk_notes": "Risk Notes",
    "needs_manual_review": "Needs Manual Review",
    "outcome_availability_display_only": "Outcome Availability (Display-Only)",
    "qb_t12_display_only": "QB T12 (Display-Only)",
    "rb_t12_display_only": "RB T12 (Display-Only)",
    "rb_t24_display_only": "RB T24 (Display-Only)",
    "wr_t12_display_only": "WR T12 (Display-Only)",
    "wr_t24_display_only": "WR T24 (Display-Only)",
    "wr_t36_display_only": "WR T36 (Display-Only)",
    "te_t12_display_only": "TE T12 (Display-Only)",
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
                "source_rule": "Must reference frozen Final Draft Board V1.",
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
