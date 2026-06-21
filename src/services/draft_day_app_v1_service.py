from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

LOCAL_FROZEN_BOARD_ROOT = Path(
    r"C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622"
)
LOCAL_FROZEN_BOARD_PATH = LOCAL_FROZEN_BOARD_ROOT / "FINAL_DRAFT_BOARD_V1_FROZEN.csv"
REPO_SAFE_FROZEN_BOARD_PATH = (
    REPO_ROOT
    / "docs"
    / "draft_day_exports"
    / "final_board_v1_20260622"
    / "FINAL_DRAFT_BOARD_V1_FROZEN.csv"
)

APP_PROP_ROOT = Path(r"C:\NWR_SHARED_DATA\draft_day_app_props\20260622")
EXPECTED_ROW_COUNT = 66
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

LANE_PROP_FOLDERS = {
    "outcome_columns": APP_PROP_ROOT / "outcome_columns",
    "trading_lab": APP_PROP_ROOT / "trading_lab",
    "rookie_hq": APP_PROP_ROOT / "rookie_hq",
    "mock_draft": APP_PROP_ROOT / "mock_draft",
    "decision_board": APP_PROP_ROOT / "decision_board",
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


def resolve_frozen_board_path() -> tuple[Path | None, str, tuple[str, ...]]:
    warnings: list[str] = []
    if LOCAL_FROZEN_BOARD_PATH.exists():
        return LOCAL_FROZEN_BOARD_PATH, "local frozen board", tuple(warnings)
    if REPO_SAFE_FROZEN_BOARD_PATH.exists():
        warnings.append(
            "Using GitHub-safe frozen board copy because the local-only frozen package is missing."
        )
        return REPO_SAFE_FROZEN_BOARD_PATH, "repo-safe frozen board copy", tuple(warnings)
    return None, "missing frozen board", tuple(warnings)


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
    for lane, folder in LANE_PROP_FOLDERS.items():
        files = sorted(folder.glob("*")) if folder.exists() else []
        rows.append(
            {
                "lane": lane,
                "status": "GREEN" if files else "YELLOW-HOLD",
                "path": str(folder),
                "file_count": str(len([path for path in files if path.is_file()])),
                "source_rule": "Must reference frozen Final Draft Board V1.",
            }
        )
    return rows


def first_lane_prop_csv(lane: str) -> Path | None:
    folder = LANE_PROP_FOLDERS.get(lane)
    if folder is None or not folder.exists():
        return None
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
