from __future__ import annotations

import hashlib
import json
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
ROSTER_CONTEXT_POINTER_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context"
    r"\latest_candidate.json"
)
HISTORICAL_SEASON_LABELS_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels"
    r"\outcome_v2_season_outcome_labels.csv"
)
OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge")

BRIDGE_FILENAME = "outcome_v2_current_identity_bridge.csv"
AUDIT_FILENAME = "outcome_v2_current_identity_bridge_audit.csv"
MANIFEST_FILENAME = "outcome_v2_current_identity_bridge_manifest.csv"

SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")
TEAM_ALIASES = {
    "ARZ": "ARI",
    "JAC": "JAX",
    "LA": "LAR",
    "LAR": "LAR",
    "LV": "LV",
    "OAK": "LV",
    "SD": "LAC",
    "STL": "LAR",
}
DISPLAY_ONLY = "true"
MODEL_USE_ALLOWED = "false"
SOURCE_TRUTH_ALLOWED = "false"
TRAINING_ALLOWED = "false"
NOT_ENOUGH_INFORMATION = "Not enough information"


@dataclass(frozen=True)
class IdentityBridgeSourceMetadata:
    roster_context_path: Path
    roster_pointer_path: Path | None
    roster_manifest_path: Path | None
    approval_status: str
    approval_scope: str
    allowed_use: tuple[str, ...]
    forbidden_use: tuple[str, ...]
    source_policy_status: str


@dataclass(frozen=True)
class IdentityBridgeBuildResult:
    status: str
    output_root: Path
    bridge_path: Path
    audit_path: Path
    manifest_path: Path
    current_board_rows: int
    bridge_rows: int
    veteran_non_rookie_rows: int
    matched_exact_rows: int
    matched_high_confidence_rows: int
    missing_gsis_rows: int
    ambiguous_rows: int
    out_of_scope_rookie_or_prospect_rows: int
    high_confidence_coverage_pct: float


def load_identity_bridge_sources(
    *,
    current_board_path: str | Path = CURRENT_BOARD_PATH,
    roster_context_pointer_path: str | Path | None = ROSTER_CONTEXT_POINTER_PATH,
    roster_context_path: str | Path | None = None,
    historical_season_labels_path: str | Path = HISTORICAL_SEASON_LABELS_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, IdentityBridgeSourceMetadata]:
    board_path = Path(current_board_path)
    historical_path = Path(historical_season_labels_path)
    roster_path, metadata = resolve_roster_context_path(
        roster_context_pointer_path=roster_context_pointer_path,
        roster_context_path=roster_context_path,
    )
    source_paths = (board_path, roster_path, historical_path)
    missing = [str(path) for path in source_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Outcome V2 identity bridge inputs: {missing}")
    return (
        pd.read_csv(board_path, dtype=str),
        pd.read_csv(roster_path, dtype=str),
        pd.read_csv(historical_path, dtype=str),
        metadata,
    )


def resolve_roster_context_path(
    *,
    roster_context_pointer_path: str | Path | None = ROSTER_CONTEXT_POINTER_PATH,
    roster_context_path: str | Path | None = None,
) -> tuple[Path, IdentityBridgeSourceMetadata]:
    if roster_context_path is not None:
        path = Path(roster_context_path)
        return path, IdentityBridgeSourceMetadata(
            roster_context_path=path,
            roster_pointer_path=None,
            roster_manifest_path=None,
            approval_status="test_or_direct_source",
            approval_scope="test_or_direct_source",
            allowed_use=("identity_crosscheck",),
            forbidden_use=("model_training", "hidden_sort", "source_truth"),
            source_policy_status="direct_path_review_only",
        )

    pointer_path = Path(roster_context_pointer_path) if roster_context_pointer_path else None
    if pointer_path is None or not pointer_path.exists():
        raise FileNotFoundError(f"Missing roster context pointer: {pointer_path}")

    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    snapshot_path = Path(str(pointer.get("snapshot_path", "")))
    data_file = str(pointer.get("data_file", "player_roster_display_context.csv"))
    path = snapshot_path / data_file
    manifest_path = (
        Path(str(pointer.get("manifest_path", ""))) if pointer.get("manifest_path") else None
    )
    allowed_use = _tuple_text(pointer.get("allowed_use"))
    forbidden_use = _tuple_text(pointer.get("forbidden_use"))
    approval_status = str(pointer.get("approval_status") or "").strip()
    approval_scope = str(pointer.get("approval_scope") or pointer.get("approved_for") or "").strip()
    policy_status = _source_policy_status(
        approval_status=approval_status,
        allowed_use=allowed_use,
        forbidden_use=forbidden_use,
    )
    return path, IdentityBridgeSourceMetadata(
        roster_context_path=path,
        roster_pointer_path=pointer_path,
        roster_manifest_path=manifest_path,
        approval_status=approval_status,
        approval_scope=approval_scope,
        allowed_use=allowed_use,
        forbidden_use=forbidden_use,
        source_policy_status=policy_status,
    )


def build_outcome_v2_identity_bridge(
    current_board: pd.DataFrame,
    roster_context: pd.DataFrame,
    historical_season_labels: pd.DataFrame,
    *,
    source_metadata: IdentityBridgeSourceMetadata,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    _require_columns(
        current_board,
        {"player_id", "player_name", "position", "nfl_team"},
        "current_board",
    )
    _require_columns(
        roster_context,
        {
            "sleeper_id",
            "gsis_id",
            "full_name",
            "position",
            "team",
            "birth_date",
            "years_exp",
            "rookie_year",
        },
        "roster_context",
    )
    _require_columns(
        historical_season_labels,
        {"player_id", "player_name", "position", "season", "team"},
        "historical_season_labels",
    )

    board = _prepare_current_board(current_board)
    eligible = board[board["current_board_position"].isin(SUPPORTED_POSITIONS)].copy()
    roster = _prepare_roster_context(roster_context)
    historical_gsis_ids = set(_text_series(historical_season_labels, "player_id"))
    direct_lookup, direct_ambiguous = _direct_sleeper_lookup(roster)
    multikey_lookup, multikey_ambiguous = _multi_key_lookup(roster)

    rows: list[dict[str, Any]] = []
    for row in eligible.itertuples(index=False):
        bridge_row = _bridge_row_for_player(
            row=row,
            direct_lookup=direct_lookup,
            direct_ambiguous=direct_ambiguous,
            multikey_lookup=multikey_lookup,
            multikey_ambiguous=multikey_ambiguous,
            historical_gsis_ids=historical_gsis_ids,
            source_metadata=source_metadata,
        )
        rows.append(bridge_row)

    bridge = pd.DataFrame(rows, columns=_bridge_columns())
    audit = pd.DataFrame(_audit_rows(bridge, current_board, source_metadata))
    manifest = pd.DataFrame(
        _manifest_rows(
            bridge=bridge,
            audit=audit,
            source_metadata=source_metadata,
            current_board_rows=len(current_board),
        )
    )
    return bridge, audit, manifest


def write_outcome_v2_identity_bridge_artifacts(
    *,
    output_root: str | Path = OUTPUT_ROOT,
    current_board_path: str | Path = CURRENT_BOARD_PATH,
    roster_context_pointer_path: str | Path | None = ROSTER_CONTEXT_POINTER_PATH,
    roster_context_path: str | Path | None = None,
    historical_season_labels_path: str | Path = HISTORICAL_SEASON_LABELS_PATH,
) -> IdentityBridgeBuildResult:
    current_board, roster_context, historical_labels, metadata = load_identity_bridge_sources(
        current_board_path=current_board_path,
        roster_context_pointer_path=roster_context_pointer_path,
        roster_context_path=roster_context_path,
        historical_season_labels_path=historical_season_labels_path,
    )
    bridge, audit, manifest = build_outcome_v2_identity_bridge(
        current_board,
        roster_context,
        historical_labels,
        source_metadata=metadata,
    )
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    bridge_path = root / BRIDGE_FILENAME
    audit_path = root / AUDIT_FILENAME
    manifest_path = root / MANIFEST_FILENAME
    bridge.to_csv(bridge_path, index=False)
    audit.to_csv(audit_path, index=False)
    manifest = manifest.copy()
    manifest["artifact_path"] = manifest["artifact_name"].map(
        {
            "bridge": str(bridge_path),
            "audit": str(audit_path),
        }
    )
    manifest["sha256"] = manifest["artifact_path"].map(lambda value: _sha256(Path(value)))
    manifest["row_count"] = manifest["artifact_path"].map(lambda value: _csv_row_count(Path(value)))
    manifest.to_csv(manifest_path, index=False)

    metrics = _summary_metrics(bridge, len(current_board), metadata)
    return IdentityBridgeBuildResult(
        status=metrics["status"],
        output_root=root,
        bridge_path=bridge_path,
        audit_path=audit_path,
        manifest_path=manifest_path,
        current_board_rows=int(metrics["current_board_rows"]),
        bridge_rows=int(metrics["bridge_rows"]),
        veteran_non_rookie_rows=int(metrics["veteran_non_rookie_rows"]),
        matched_exact_rows=int(metrics["matched_exact_rows"]),
        matched_high_confidence_rows=int(metrics["matched_high_confidence_rows"]),
        missing_gsis_rows=int(metrics["missing_gsis_rows"]),
        ambiguous_rows=int(metrics["ambiguous_rows"]),
        out_of_scope_rookie_or_prospect_rows=int(
            metrics["out_of_scope_rookie_or_prospect_rows"]
        ),
        high_confidence_coverage_pct=float(metrics["high_confidence_coverage_pct"]),
    )


def normalize_name(value: object) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"[^a-zA-Z0-9]+", "", text).lower()


def normalize_team(value: object) -> str:
    text = str(value or "").strip().upper()
    return TEAM_ALIASES.get(text, text)


def _prepare_current_board(current_board: pd.DataFrame) -> pd.DataFrame:
    board = current_board.copy().fillna("")
    board["nwr_player_id"] = _text_series(board, "player_id")
    board["current_board_player_name"] = _text_series(board, "player_name")
    board["normalized_player_name"] = board["current_board_player_name"].map(normalize_name)
    board["current_board_position"] = _text_series(board, "position").str.upper()
    board["current_board_team"] = _text_series(board, "nfl_team").map(normalize_team)
    board["sleeper_id"] = board["nwr_player_id"]
    if "is_rookie" not in board.columns:
        board["is_rookie"] = ""
    return board


def _prepare_roster_context(roster_context: pd.DataFrame) -> pd.DataFrame:
    roster = roster_context.copy().fillna("")
    roster["sleeper_id"] = _text_series(roster, "sleeper_id")
    roster["gsis_id"] = _text_series(roster, "gsis_id")
    roster["nflverse_id"] = roster["gsis_id"]
    roster["normalized_player_name"] = _text_series(roster, "full_name").map(normalize_name)
    roster["position"] = _text_series(roster, "position").str.upper()
    roster["team"] = _text_series(roster, "team").map(normalize_team)
    roster["season_num"] = pd.to_numeric(roster.get("season", ""), errors="coerce").fillna(0)
    roster["week_num"] = pd.to_numeric(roster.get("week", ""), errors="coerce").fillna(0)
    return roster[
        roster["position"].isin(SUPPORTED_POSITIONS)
        & roster["sleeper_id"].ne("")
        & roster["gsis_id"].ne("")
    ].copy()


def _direct_sleeper_lookup(
    roster: pd.DataFrame,
) -> tuple[dict[str, pd.Series], dict[str, pd.DataFrame]]:
    lookup: dict[str, pd.Series] = {}
    ambiguous: dict[str, pd.DataFrame] = {}
    for sleeper_id, group in roster.groupby("sleeper_id", sort=False):
        if group["gsis_id"].nunique() > 1:
            ambiguous[sleeper_id] = group
            continue
        latest = group.sort_values(["season_num", "week_num"]).iloc[-1]
        lookup[sleeper_id] = latest
    return lookup, ambiguous


def _multi_key_lookup(
    roster: pd.DataFrame,
) -> tuple[dict[tuple[str, str, str], pd.Series], set[tuple[str, str, str]]]:
    lookup: dict[tuple[str, str, str], pd.Series] = {}
    ambiguous: set[tuple[str, str, str]] = set()
    for key, group in roster.groupby(["normalized_player_name", "position", "team"], sort=False):
        if group["gsis_id"].nunique() > 1:
            ambiguous.add(key)
            continue
        latest = group.sort_values(["season_num", "week_num"]).iloc[-1]
        lookup[key] = latest
    return lookup, ambiguous


def _bridge_row_for_player(
    *,
    row: Any,
    direct_lookup: dict[str, pd.Series],
    direct_ambiguous: dict[str, pd.DataFrame],
    multikey_lookup: dict[tuple[str, str, str], pd.Series],
    multikey_ambiguous: set[tuple[str, str, str]],
    historical_gsis_ids: set[str],
    source_metadata: IdentityBridgeSourceMetadata,
) -> dict[str, Any]:
    nwr_player_id = str(row.nwr_player_id)
    identity_status = "missing_gsis_id"
    match_method = "no_safe_identity_bridge"
    match_confidence = "0.00"
    evidence_fields = "current_board.player_id"
    review_notes = "No direct Sleeper ID to GSIS row and no deterministic multi-key match."
    roster_match: pd.Series | None = None

    if nwr_player_id in direct_ambiguous:
        identity_status = "ambiguous_review_required"
        match_method = "ambiguous_direct_sleeper_id_to_gsis"
        evidence_fields = "current_board.player_id=roster.sleeper_id"
        review_notes = "Sleeper ID maps to multiple GSIS IDs in roster context."
    elif nwr_player_id in direct_lookup:
        roster_match = direct_lookup[nwr_player_id]
        identity_status = "matched_exact"
        match_method = "direct_sleeper_id_to_gsis"
        match_confidence = "1.00"
        evidence_fields = (
            "current_board.player_id=roster.sleeper_id|gsis_id|position|name_review"
        )
        review_notes = _direct_review_note(row, roster_match, source_metadata)
    else:
        key = (
            str(row.normalized_player_name),
            str(row.current_board_position),
            str(row.current_board_team),
        )
        if key in multikey_ambiguous:
            identity_status = "ambiguous_review_required"
            match_method = "ambiguous_name_position_team"
            evidence_fields = "normalized_name|position|team"
            review_notes = "Name/position/team maps to multiple GSIS IDs in roster context."
        elif key in multikey_lookup:
            roster_match = multikey_lookup[key]
            identity_status = "matched_high_confidence"
            match_method = "deterministic_name_position_team"
            match_confidence = "0.95"
            evidence_fields = "normalized_name|position|team|single_gsis_candidate"
            review_notes = "Unique exact normalized name, position, and team match."

    if roster_match is not None and _is_rookie_or_prospect(row, roster_match):
        identity_status = "out_of_scope_rookie_or_prospect"
        match_method = f"{match_method}_out_of_scope"
        review_notes = (
            "Identity link found, but player is out of scope for Normal Outcome V2 "
            "because rookie/prospect status is indicated by current board ID or roster metadata."
        )

    gsis_id = _series_value(roster_match, "gsis_id")
    has_historical_label = "true" if gsis_id and gsis_id in historical_gsis_ids else "false"
    feature_coverage_note = (
        "historical_label_available"
        if has_historical_label == "true"
        else NOT_ENOUGH_INFORMATION
    )
    return {
        "nwr_player_id": nwr_player_id,
        "current_board_player_name": row.current_board_player_name,
        "normalized_player_name": row.normalized_player_name,
        "current_board_position": row.current_board_position,
        "current_board_team": row.current_board_team,
        "sleeper_id": nwr_player_id if roster_match is not None else "",
        "gsis_id": gsis_id,
        "nflverse_id": _series_value(roster_match, "nflverse_id"),
        "match_method": match_method,
        "match_confidence": match_confidence,
        "identity_status": identity_status,
        "evidence_fields_used": evidence_fields,
        "source_path": str(source_metadata.roster_context_path),
        "review_notes": review_notes,
        "display_only": DISPLAY_ONLY,
        "model_use_allowed": MODEL_USE_ALLOWED,
        "source_truth_allowed": SOURCE_TRUTH_ALLOWED,
        "training_allowed": TRAINING_ALLOWED,
        "source_approval_status": source_metadata.approval_status,
        "source_policy_status": source_metadata.source_policy_status,
        "source_allowed_use": "|".join(source_metadata.allowed_use),
        "source_forbidden_use": "|".join(source_metadata.forbidden_use),
        "roster_full_name": _series_value(roster_match, "full_name"),
        "roster_team": _series_value(roster_match, "team"),
        "roster_birth_date": _series_value(roster_match, "birth_date"),
        "roster_rookie_year": _series_value(roster_match, "rookie_year"),
        "roster_years_exp": _series_value(roster_match, "years_exp"),
        "historical_label_available": has_historical_label,
        "feature_coverage_note": feature_coverage_note,
    }


def _direct_review_note(
    row: Any,
    roster_match: pd.Series,
    source_metadata: IdentityBridgeSourceMetadata,
) -> str:
    notes = [
        "Direct current board player_id to roster sleeper_id to GSIS bridge.",
        f"source_policy={source_metadata.source_policy_status}",
    ]
    if str(row.current_board_position) != _series_value(roster_match, "position"):
        notes.append("position_mismatch_review_required")
    roster_team = normalize_team(_series_value(roster_match, "team"))
    if normalize_team(row.current_board_team) != roster_team:
        notes.append("team_variation_or_stale_team_review")
    if str(row.normalized_player_name) != _series_value(roster_match, "normalized_player_name"):
        notes.append("name_variation_review")
    return "; ".join(notes)


def _is_rookie_or_prospect(row: Any, roster_match: pd.Series) -> bool:
    if _truthy(getattr(row, "is_rookie", "")):
        return True
    player_id = str(row.nwr_player_id)
    if player_id.isdigit() and int(player_id) >= 12000:
        return True
    rookie_year = pd.to_numeric(_series_value(roster_match, "rookie_year"), errors="coerce")
    years_exp = pd.to_numeric(_series_value(roster_match, "years_exp"), errors="coerce")
    is_new_roster_player = (
        pd.notna(rookie_year)
        and rookie_year >= 2025
        and pd.notna(years_exp)
        and years_exp <= 0
    )
    return bool(is_new_roster_player)


def _summary_metrics(
    bridge: pd.DataFrame,
    current_board_rows: int,
    source_metadata: IdentityBridgeSourceMetadata,
) -> dict[str, Any]:
    matched_exact = int(bridge["identity_status"].eq("matched_exact").sum())
    matched_high = int(bridge["identity_status"].eq("matched_high_confidence").sum())
    missing = int(bridge["identity_status"].eq("missing_gsis_id").sum())
    ambiguous = int(bridge["identity_status"].eq("ambiguous_review_required").sum())
    out_of_scope = int(bridge["identity_status"].eq("out_of_scope_rookie_or_prospect").sum())
    veteran_rows = len(bridge) - out_of_scope
    coverage = ((matched_exact + matched_high) / veteran_rows * 100) if veteran_rows else 0.0
    if missing or ambiguous:
        status = "PARTIAL_IDENTITY_BRIDGE_BUILT"
    elif matched_exact + matched_high > 0 and source_metadata.source_policy_status in {
        "identity_crosscheck_candidate_review_only",
        "identity_crosscheck_approved_review_only",
        "direct_path_review_only",
    }:
        status = "PASS_IDENTITY_BRIDGE_BUILT_REVIEW_ONLY"
    else:
        status = "BLOCKED_NO_SAFE_IDENTITY_SOURCE"
    return {
        "status": status,
        "current_board_rows": current_board_rows,
        "bridge_rows": len(bridge),
        "veteran_non_rookie_rows": veteran_rows,
        "matched_exact_rows": matched_exact,
        "matched_high_confidence_rows": matched_high,
        "missing_gsis_rows": missing,
        "ambiguous_rows": ambiguous,
        "out_of_scope_rookie_or_prospect_rows": out_of_scope,
        "high_confidence_coverage_pct": round(coverage, 2),
    }


def _audit_rows(
    bridge: pd.DataFrame,
    current_board: pd.DataFrame,
    source_metadata: IdentityBridgeSourceMetadata,
) -> list[dict[str, str]]:
    metrics = _summary_metrics(bridge, len(current_board), source_metadata)
    rows = [{"metric": key, "value": str(value)} for key, value in metrics.items()]
    rows.extend(
        [
            {"metric": "display_only", "value": DISPLAY_ONLY},
            {"metric": "model_use_allowed", "value": MODEL_USE_ALLOWED},
            {"metric": "source_truth_allowed", "value": SOURCE_TRUTH_ALLOWED},
            {"metric": "training_allowed", "value": TRAINING_ALLOWED},
            {"metric": "source_approval_status", "value": source_metadata.approval_status},
            {"metric": "source_approval_scope", "value": source_metadata.approval_scope},
            {"metric": "source_policy_status", "value": source_metadata.source_policy_status},
            {"metric": "source_path", "value": str(source_metadata.roster_context_path)},
            {
                "metric": "source_policy_caveat",
                "value": (
                    "Roster identity source is used only for identity crosscheck and "
                    "review-only display bridge generation; it is not model, rank, hidden sort, "
                    "source truth, trade value, or pick value input."
                ),
            },
        ]
    )
    return rows


def _manifest_rows(
    *,
    bridge: pd.DataFrame,
    audit: pd.DataFrame,
    source_metadata: IdentityBridgeSourceMetadata,
    current_board_rows: int,
) -> list[dict[str, Any]]:
    created_at = datetime.now(UTC).isoformat()
    return [
        {
            "artifact_name": "bridge",
            "artifact_path": "",
            "row_count": len(bridge),
            "sha256": "",
            "created_at": created_at,
            "approval_status": "review_only_identity_bridge",
            "current_board_rows": current_board_rows,
            "source_path": str(source_metadata.roster_context_path),
            "source_approval_status": source_metadata.approval_status,
            "source_policy_status": source_metadata.source_policy_status,
            "display_only": DISPLAY_ONLY,
            "model_use_allowed": MODEL_USE_ALLOWED,
            "source_truth_allowed": SOURCE_TRUTH_ALLOWED,
            "training_allowed": TRAINING_ALLOWED,
            "notes": "Compact derived identity bridge only; no probabilities or app wiring.",
        },
        {
            "artifact_name": "audit",
            "artifact_path": "",
            "row_count": len(audit),
            "sha256": "",
            "created_at": created_at,
            "approval_status": "review_only_identity_bridge",
            "current_board_rows": current_board_rows,
            "source_path": str(source_metadata.roster_context_path),
            "source_approval_status": source_metadata.approval_status,
            "source_policy_status": source_metadata.source_policy_status,
            "display_only": DISPLAY_ONLY,
            "model_use_allowed": MODEL_USE_ALLOWED,
            "source_truth_allowed": SOURCE_TRUTH_ALLOWED,
            "training_allowed": TRAINING_ALLOWED,
            "notes": "Bridge gate audit summary only; no probabilities or app wiring.",
        },
    ]


def _source_policy_status(
    *,
    approval_status: str,
    allowed_use: tuple[str, ...],
    forbidden_use: tuple[str, ...],
) -> str:
    allowed = set(allowed_use)
    forbidden = set(forbidden_use)
    if "identity_crosscheck" not in allowed:
        return "blocked_missing_identity_crosscheck_approval"
    blocked_terms = {"model_training", "hidden_sort", "hidden_rank", "private_value"}
    if not forbidden.intersection(blocked_terms):
        return "blocked_missing_model_rank_forbidden_use"
    if approval_status == "approved":
        return "identity_crosscheck_approved_review_only"
    if approval_status == "candidate":
        return "identity_crosscheck_candidate_review_only"
    return "identity_crosscheck_review_only"


def _bridge_columns() -> list[str]:
    return [
        "nwr_player_id",
        "current_board_player_name",
        "normalized_player_name",
        "current_board_position",
        "current_board_team",
        "sleeper_id",
        "gsis_id",
        "nflverse_id",
        "match_method",
        "match_confidence",
        "identity_status",
        "evidence_fields_used",
        "source_path",
        "review_notes",
        "display_only",
        "model_use_allowed",
        "source_truth_allowed",
        "training_allowed",
        "source_approval_status",
        "source_policy_status",
        "source_allowed_use",
        "source_forbidden_use",
        "roster_full_name",
        "roster_team",
        "roster_birth_date",
        "roster_rookie_year",
        "roster_years_exp",
        "historical_label_available",
        "feature_coverage_note",
    ]


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


def _tuple_text(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value or "").strip()
    if not text:
        return ()
    return tuple(part.strip() for part in re.split(r"[,|;]", text) if part.strip())


def _series_value(row: pd.Series | None, column: str) -> str:
    if row is None or column not in row:
        return ""
    value = row[column]
    if pd.isna(value):
        return ""
    return str(value).strip()


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _csv_row_count(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _line in handle) - 1, 0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
