from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

CURRENT_BOARD_PATH = Path(
    r"C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest"
    r"\full_player_board_value_review_rows.csv"
)
IDENTITY_AUDIT_PATH = Path("docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv")
HISTORICAL_SEASON_LABELS_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels"
    r"\outcome_v2_season_outcome_labels.csv"
)
OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge")

SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")
NOT_ENOUGH_INFORMATION = "Not enough information"
MODEL_INPUT_ALLOWED = "no"
TRAINING_ALLOWED = "no"
APP_WIRING_ALLOWED = "no"

AUDIT_FILENAME = "outcome_v2_current_identity_bridge_audit.csv"
SUMMARY_FILENAME = "outcome_v2_current_identity_bridge_summary.csv"
MANIFEST_FILENAME = "outcome_v2_current_identity_bridge_manifest.csv"


@dataclass(frozen=True)
class CurrentIdentityBridgeGateResult:
    status: str
    output_root: Path
    audit_path: Path
    summary_path: Path
    manifest_path: Path
    board_rows: int
    eligible_rows: int
    approved_bridge_rows: int
    diagnostic_name_position_matches: int
    current_display_artifact_created: bool


def load_current_identity_bridge_sources(
    *,
    current_board_path: str | Path = CURRENT_BOARD_PATH,
    identity_audit_path: str | Path = IDENTITY_AUDIT_PATH,
    historical_season_labels_path: str | Path = HISTORICAL_SEASON_LABELS_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = [
        Path(current_board_path),
        Path(identity_audit_path),
        Path(historical_season_labels_path),
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Outcome V2 current identity gate inputs: {missing}")
    return tuple(pd.read_csv(path, dtype=str) for path in paths)  # type: ignore[return-value]


def build_current_identity_bridge_audit(
    current_board: pd.DataFrame,
    identity_audit: pd.DataFrame,
    historical_season_labels: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    _require_columns(
        current_board,
        {"player_id", "player_name", "position", "nfl_team"},
        "current_board",
    )
    _require_columns(
        identity_audit,
        {
            "player_name",
            "position",
            "sleeper_id",
            "nflverse_id_or_gsis",
            "match_method",
            "match_confidence",
            "needs_manual_review",
        },
        "identity_audit",
    )
    _require_columns(
        historical_season_labels,
        {"player_id", "player_name", "position", "season", "team"},
        "historical_season_labels",
    )

    board = current_board.copy()
    board["position"] = board["position"].fillna("").astype(str).str.upper()
    board = board[board["position"].isin(SUPPORTED_POSITIONS)].copy()
    board["player_id_text"] = _text_series(board, "player_id")
    board["normalized_name"] = board["player_name"].map(normalize_name)

    identity = identity_audit.copy()
    identity["position"] = identity["position"].fillna("").astype(str).str.upper()
    identity["sleeper_id_text"] = _text_series(identity, "sleeper_id")
    identity["gsis_id"] = _text_series(identity, "nflverse_id_or_gsis")
    identity["normalized_name"] = identity["player_name"].map(normalize_name)
    identity = _dedupe_identity_rows(identity)

    historical = historical_season_labels.copy()
    historical["position"] = historical["position"].fillna("").astype(str).str.upper()
    historical["normalized_name"] = historical["player_name"].map(normalize_name)
    historical["season_num"] = pd.to_numeric(historical["season"], errors="coerce")
    latest_historical = historical.sort_values("season_num").drop_duplicates(
        ["normalized_name", "position"],
        keep="last",
    )

    direct = board.merge(
        identity,
        left_on="player_id_text",
        right_on="sleeper_id_text",
        how="left",
        suffixes=("_board", "_identity"),
    )
    diagnostic = board.merge(
        latest_historical[
            ["normalized_name", "position", "player_id", "player_name", "season", "team"]
        ],
        on=["normalized_name", "position"],
        how="left",
        suffixes=("_board", "_historical"),
    )

    diagnostic_lookup = {
        str(row.player_id_board): row
        for row in diagnostic.itertuples(index=False)
    }
    rows: list[dict[str, Any]] = []
    for row in direct.itertuples(index=False):
        board_player_id = str(row.player_id)
        gsis_id = str(getattr(row, "gsis_id", "") or "").strip()
        diag = diagnostic_lookup.get(board_player_id)
        diagnostic_gsis = ""
        diagnostic_season = ""
        diagnostic_team = ""
        if diag is not None:
            diagnostic_gsis = _clean_missing(getattr(diag, "player_id_historical", ""))
            diagnostic_season = _clean_missing(getattr(diag, "season", ""))
            diagnostic_team = _clean_missing(getattr(diag, "team", ""))
        bridge_status = _bridge_status(
            gsis_id=gsis_id,
            match_method=str(getattr(row, "match_method", "") or ""),
            needs_manual_review=str(getattr(row, "needs_manual_review", "") or ""),
        )
        out_of_scope = _out_of_scope_status(
            board_player_id=board_player_id,
            diagnostic_gsis=diagnostic_gsis,
            is_rookie=str(getattr(row, "is_rookie", "") or ""),
        )
        rows.append(
            {
                "current_player_id": board_player_id,
                "player_name": row.player_name_board,
                "position": row.position_board,
                "nfl_team": getattr(row, "nfl_team", ""),
                "approved_gsis_id": gsis_id,
                "approved_bridge_status": bridge_status,
                "identity_match_method": getattr(row, "match_method", ""),
                "identity_match_confidence": getattr(row, "match_confidence", ""),
                "identity_needs_manual_review": getattr(row, "needs_manual_review", ""),
                "diagnostic_name_position_gsis_id": diagnostic_gsis,
                "diagnostic_latest_historical_season": diagnostic_season,
                "diagnostic_latest_historical_team": diagnostic_team,
                "diagnostic_only": "yes",
                "out_of_scope_status": out_of_scope,
                "current_feature_status": NOT_ENOUGH_INFORMATION,
                "display_artifact_allowed": "no",
                "blocker": _blocker(bridge_status, out_of_scope),
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "training_allowed": TRAINING_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
            }
        )
    audit = pd.DataFrame(rows)
    summary = pd.DataFrame(summary_rows(current_board, audit))
    return audit, summary


def summary_rows(current_board: pd.DataFrame, audit: pd.DataFrame) -> list[dict[str, str]]:
    eligible = current_board[current_board["position"].isin(SUPPORTED_POSITIONS)]
    approved_bridge_rows = int(audit["approved_bridge_status"].eq("approved_gsis_bridge").sum())
    diagnostic_matches = int(audit["diagnostic_name_position_gsis_id"].fillna("").ne("").sum())
    status = (
        "PASS_APPROVED_BRIDGE_AVAILABLE"
        if approved_bridge_rows == len(audit) and len(audit) > 0
        else "BLOCKED_NO_APPROVED_COMPACT_GSIS_BRIDGE"
    )
    rows = [
        _metric("gate_status", status),
        _metric("current_board_rows", len(current_board)),
        _metric("eligible_qb_rb_wr_te_rows", len(eligible)),
        _metric("approved_bridge_rows", approved_bridge_rows),
        _metric("diagnostic_name_position_matches", diagnostic_matches),
        _metric(
            "not_enough_information_rows",
            int(audit["current_feature_status"].eq(NOT_ENOUGH_INFORMATION).sum()),
        ),
        _metric(
            "out_of_scope_rookie_or_prospect_rows",
            int(audit["out_of_scope_status"].eq("out_of_scope_rookie_or_prospect").sum()),
        ),
        _metric("current_display_artifact_created", "no"),
        _metric("model_input_allowed", MODEL_INPUT_ALLOWED),
        _metric("training_allowed", TRAINING_ALLOWED),
        _metric("app_wiring_allowed", APP_WIRING_ALLOWED),
        _metric(
            "primary_blocker",
            "No approved current-board player_id/Sleeper ID to GSIS bridge was found.",
        ),
        _metric(
            "secondary_blocker",
            "Current 2026-pre-draft as-of feature definition remains unapproved.",
        ),
    ]
    return rows


def write_current_identity_bridge_gate_artifacts(
    *,
    output_root: str | Path = OUTPUT_ROOT,
    current_board_path: str | Path = CURRENT_BOARD_PATH,
    identity_audit_path: str | Path = IDENTITY_AUDIT_PATH,
    historical_season_labels_path: str | Path = HISTORICAL_SEASON_LABELS_PATH,
) -> CurrentIdentityBridgeGateResult:
    current_board, identity_audit, historical_labels = load_current_identity_bridge_sources(
        current_board_path=current_board_path,
        identity_audit_path=identity_audit_path,
        historical_season_labels_path=historical_season_labels_path,
    )
    audit, summary = build_current_identity_bridge_audit(
        current_board,
        identity_audit,
        historical_labels,
    )
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    audit_path = root / AUDIT_FILENAME
    summary_path = root / SUMMARY_FILENAME
    manifest_path = root / MANIFEST_FILENAME
    audit.to_csv(audit_path, index=False)
    summary.to_csv(summary_path, index=False)
    manifest = pd.DataFrame(
        _manifest_rows(
            artifacts={"audit": audit_path, "summary": summary_path},
            source_paths={
                "current_board": Path(current_board_path),
                "identity_audit": Path(identity_audit_path),
                "historical_season_labels": Path(historical_season_labels_path),
            },
        )
    )
    manifest.to_csv(manifest_path, index=False)
    metrics = dict(zip(summary["metric"], summary["value"], strict=True))
    return CurrentIdentityBridgeGateResult(
        status=metrics["gate_status"],
        output_root=root,
        audit_path=audit_path,
        summary_path=summary_path,
        manifest_path=manifest_path,
        board_rows=int(metrics["current_board_rows"]),
        eligible_rows=int(metrics["eligible_qb_rb_wr_te_rows"]),
        approved_bridge_rows=int(metrics["approved_bridge_rows"]),
        diagnostic_name_position_matches=int(metrics["diagnostic_name_position_matches"]),
        current_display_artifact_created=False,
    )


def normalize_name(value: object) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"[^a-zA-Z0-9]+", "", text).lower()


def _dedupe_identity_rows(identity: pd.DataFrame) -> pd.DataFrame:
    identity = identity.copy()
    identity["has_gsis"] = identity["gsis_id"].ne("")
    identity["manual_review_bool"] = identity["needs_manual_review"].map(_truthy)
    identity["confidence_num"] = pd.to_numeric(
        identity["match_confidence"],
        errors="coerce",
    ).fillna(0)
    identity = identity.sort_values(
        ["sleeper_id_text", "has_gsis", "manual_review_bool", "confidence_num"],
        ascending=[True, False, True, False],
    )
    return identity.drop_duplicates("sleeper_id_text", keep="first")


def _bridge_status(*, gsis_id: str, match_method: str, needs_manual_review: str) -> str:
    if not gsis_id:
        return "blocked_missing_gsis"
    if _truthy(needs_manual_review):
        return "blocked_manual_review_required"
    if "fuzzy" in match_method.lower() or "ambiguous" in match_method.lower():
        return "blocked_non_deterministic_match"
    return "approved_gsis_bridge"


def _out_of_scope_status(*, board_player_id: str, diagnostic_gsis: str, is_rookie: str) -> str:
    if _truthy(is_rookie):
        return "out_of_scope_rookie_or_prospect"
    if not diagnostic_gsis and board_player_id.isdigit() and int(board_player_id) >= 12000:
        return "out_of_scope_rookie_or_prospect"
    return "current_nfl_experienced_review"


def _blocker(bridge_status: str, out_of_scope_status: str) -> str:
    if out_of_scope_status == "out_of_scope_rookie_or_prospect":
        return "rookie_outcome_separate_lane_blocked"
    if bridge_status != "approved_gsis_bridge":
        return "missing_approved_gsis_bridge"
    return "blocked_current_feature_as_of_definition"


def _text_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([""] * len(frame), index=frame.index)
    return (
        frame[column]
        .fillna("")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _clean_missing(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _metric(metric: str, value: Any) -> dict[str, str]:
    return {"metric": metric, "value": str(value)}


def _manifest_rows(
    *,
    artifacts: dict[str, Path],
    source_paths: dict[str, Path],
) -> list[dict[str, Any]]:
    created_at = datetime.now(UTC).isoformat()
    rows: list[dict[str, Any]] = []
    for artifact_name, artifact_path in artifacts.items():
        rows.append(
            {
                "artifact_name": artifact_name,
                "path": str(artifact_path),
                "row_count": _csv_row_count(artifact_path),
                "sha256": _sha256(artifact_path),
                "created_at": created_at,
                "approval_status": "review_only_identity_bridge_gate",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "training_allowed": TRAINING_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "source_paths": ";".join(str(path) for path in source_paths.values()),
                "notes": "Current-player display artifact blocked; audit only.",
            }
        )
    return rows


def _csv_row_count(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _line in handle) - 1, 0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
