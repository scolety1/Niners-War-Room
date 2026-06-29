from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

SHARED_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\injury_context")
RAW_INJURY_FILENAME = "nflreadpy_injuries_review_only_2012_2025.csv"
AUDIT_FILENAME = "injury_context_source_gate_audit.csv"
MANIFEST_FILENAME = "injury_context_source_gate_manifest.csv"

APPROVE_REVIEW_ONLY = "APPROVE_INJURY_CONTEXT_REVIEW_ONLY"
PARTIAL_APPROVAL = "PARTIAL_INJURY_CONTEXT_APPROVAL"
BLOCKED_NO_LOADER = "BLOCKED_NO_LOADER"
BLOCKED_NO_LOCAL_DATA = "BLOCKED_NO_LOCAL_DATA"
BLOCKED_SOURCE_POLICY = "BLOCKED_SOURCE_POLICY"
BLOCKED_IDENTITY_JOIN = "BLOCKED_IDENTITY_JOIN"
BLOCKED_FIELD_COVERAGE = "BLOCKED_FIELD_COVERAGE"

REQUIRED_BASE_FIELDS = {"season", "week", "team", "position"}
IDENTITY_FIELDS = {"gsis_id", "player_id"}
STATUS_FIELDS = {"report_status", "practice_status", "game_status"}
INJURY_DETAIL_FIELDS = {
    "report_primary_injury",
    "report_secondary_injury",
    "practice_primary_injury",
    "practice_secondary_injury",
    "injury",
    "primary_injury",
    "secondary_injury",
}
MEDICAL_SCORE_TOKENS = (
    "risk_score",
    "injury_score",
    "recovery_probability",
    "comeback_projection",
    "acl_projection",
    "achilles_projection",
    "medical_projection",
    "return_probability",
)


@dataclass(frozen=True)
class InjuryContextSourceGateResult:
    decision: str
    audit_path: Path | None
    manifest_path: Path | None
    raw_output_path: Path | None
    row_count: int
    seasons_covered: str
    gsis_coverage_rate: float
    source_policy_status: str


def nflreadpy_injury_loader_available() -> tuple[bool, str]:
    try:
        import nflreadpy  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - exercised by tests via explicit flags.
        return False, f"{type(exc).__name__}: {exc}"
    loader = getattr(nflreadpy, "load_injuries", None)
    if loader is None:
        return False, "nflreadpy import succeeded but load_injuries is missing"
    version = str(getattr(nflreadpy, "__version__", "unknown"))
    return True, f"nflreadpy {version} load_injuries available"


def load_nflreadpy_injuries(seasons: list[int]) -> pd.DataFrame:
    import nflreadpy  # noqa: PLC0415

    frame = nflreadpy.load_injuries(seasons)
    if hasattr(frame, "to_pandas"):
        return frame.to_pandas()
    return pd.DataFrame(frame)


def audit_injury_context_source(
    injuries: pd.DataFrame | None,
    *,
    loader_available: bool,
    loader_notes: str,
    source_policy_status: str = "review_only_public_nflverse_factual_context",
    source_path: str = "nflreadpy.load_injuries",
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    if "blocked" in source_policy_status.lower():
        decision = BLOCKED_SOURCE_POLICY
    elif not loader_available and injuries is None:
        decision = BLOCKED_NO_LOADER
    elif injuries is None or injuries.empty:
        decision = BLOCKED_NO_LOCAL_DATA
    else:
        decision = _decision_from_frame(injuries)

    audit_rows = [_audit_row(injuries, decision, loader_available, loader_notes, source_path)]
    manifest_rows = [
        {
            "artifact": "injury_context_source_gate",
            "source_path": source_path,
            "decision": decision,
            "row_count": audit_rows[0]["row_count"],
            "seasons_covered": audit_rows[0]["seasons_covered"],
            "source_policy_status": source_policy_status,
            "display_only": "true",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "source_truth_allowed": "false",
            "app_wiring_allowed": "false",
            "medical_inference_allowed": "false",
            "created_at": datetime.now(UTC).isoformat(),
        }
    ]
    return decision, audit_rows, manifest_rows


def write_injury_context_source_gate_artifacts(
    output_root: str | Path = SHARED_OUTPUT_ROOT,
    *,
    seasons: list[int] | None = None,
    write_raw: bool = True,
) -> InjuryContextSourceGateResult:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    loader_available, loader_notes = nflreadpy_injury_loader_available()
    injuries: pd.DataFrame | None = None
    raw_output_path: Path | None = None
    if loader_available:
        injuries = load_nflreadpy_injuries(seasons or list(range(2012, 2026)))
        if write_raw and injuries is not None and not injuries.empty:
            raw_output_path = output / RAW_INJURY_FILENAME
            injuries.to_csv(raw_output_path, index=False)

    decision, audit_rows, manifest_rows = audit_injury_context_source(
        injuries,
        loader_available=loader_available,
        loader_notes=loader_notes,
        source_path=str(raw_output_path or "nflreadpy.load_injuries"),
    )
    audit_path = output / AUDIT_FILENAME
    manifest_path = output / MANIFEST_FILENAME
    _write_csv(audit_path, audit_rows)
    if raw_output_path is not None:
        manifest_rows.append(
            {
                "artifact": "raw_review_only_injury_context",
                "source_path": str(raw_output_path),
                "decision": decision,
                "row_count": len(injuries) if injuries is not None else 0,
                "seasons_covered": _seasons_covered(injuries),
                "source_policy_status": "review_only_public_nflverse_factual_context",
                "display_only": "true",
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "source_truth_allowed": "false",
                "app_wiring_allowed": "false",
                "medical_inference_allowed": "false",
                "sha256": _sha256(raw_output_path),
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
    _write_csv(manifest_path, manifest_rows)
    audit = audit_rows[0]
    return InjuryContextSourceGateResult(
        decision=decision,
        audit_path=audit_path,
        manifest_path=manifest_path,
        raw_output_path=raw_output_path,
        row_count=int(audit["row_count"]),
        seasons_covered=str(audit["seasons_covered"]),
        gsis_coverage_rate=float(audit["gsis_coverage_rate"]),
        source_policy_status="review_only_public_nflverse_factual_context",
    )


def _decision_from_frame(frame: pd.DataFrame) -> str:
    columns = set(frame.columns)
    if _medical_score_columns(frame):
        return BLOCKED_FIELD_COVERAGE
    if not (REQUIRED_BASE_FIELDS <= columns):
        return BLOCKED_FIELD_COVERAGE
    if not (IDENTITY_FIELDS & columns):
        return BLOCKED_IDENTITY_JOIN
    if not (STATUS_FIELDS & columns):
        return BLOCKED_FIELD_COVERAGE
    if not (INJURY_DETAIL_FIELDS & columns):
        return PARTIAL_APPROVAL
    if _identity_coverage(frame) < 0.95:
        return PARTIAL_APPROVAL
    return APPROVE_REVIEW_ONLY


def _audit_row(
    frame: pd.DataFrame | None,
    decision: str,
    loader_available: bool,
    loader_notes: str,
    source_path: str,
) -> dict[str, Any]:
    columns = [] if frame is None else list(frame.columns)
    row_count = 0 if frame is None else len(frame)
    gsis_coverage = 0.0 if frame is None else _identity_coverage(frame)
    status_fields = sorted(set(columns) & STATUS_FIELDS)
    injury_fields = sorted(set(columns) & INJURY_DETAIL_FIELDS)
    return {
        "decision": decision,
        "source_path": source_path,
        "loader_available": str(loader_available).lower(),
        "loader_notes": loader_notes,
        "row_count": row_count,
        "seasons_covered": _seasons_covered(frame),
        "teams_covered": _count_distinct(frame, "team"),
        "players_covered": _count_distinct(frame, "gsis_id")
        or _count_distinct(frame, "player_id"),
        "gsis_coverage_rate": round(gsis_coverage, 6),
        "required_base_fields_present": str(REQUIRED_BASE_FIELDS <= set(columns)).lower(),
        "identity_fields_present": "|".join(sorted(set(columns) & IDENTITY_FIELDS)),
        "status_fields_present": "|".join(status_fields),
        "injury_detail_fields_present": "|".join(injury_fields),
        "medical_score_fields_present": "|".join(_medical_score_columns(frame)),
        "safe_context_flags_later": (
            "injury_context_available|missed_prior_season|limited_recent_sample|"
            "last_materially_active_season|seasons_since_material_activity|"
            "availability_caveat|not_enough_information_reason"
        ),
        "blocked_outputs": (
            "injury_risk_score|medical_recovery_probability|acl_comeback_projection|"
            "achilles_comeback_projection|hidden_rank_adjustment"
        ),
        "display_only": "true",
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "app_wiring_allowed": "false",
        "medical_inference_allowed": "false",
    }


def _identity_coverage(frame: pd.DataFrame) -> float:
    if "gsis_id" in frame.columns:
        series = frame["gsis_id"]
    elif "player_id" in frame.columns:
        series = frame["player_id"]
    else:
        return 0.0
    if len(series) == 0:
        return 0.0
    return float(series.fillna("").astype(str).str.strip().ne("").mean())


def _medical_score_columns(frame: pd.DataFrame | None) -> list[str]:
    if frame is None:
        return []
    columns = []
    for column in frame.columns:
        normalized = column.lower()
        if any(token in normalized for token in MEDICAL_SCORE_TOKENS):
            columns.append(column)
    return columns


def _seasons_covered(frame: pd.DataFrame | None) -> str:
    if frame is None or "season" not in frame.columns or frame.empty:
        return ""
    seasons = pd.to_numeric(frame["season"], errors="coerce").dropna().astype(int)
    if seasons.empty:
        return ""
    return f"{seasons.min()}-{seasons.max()}"


def _count_distinct(frame: pd.DataFrame | None, column: str) -> int:
    if frame is None or column not in frame.columns:
        return 0
    return int(frame[column].fillna("").astype(str).str.strip().replace("", pd.NA).nunique())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = _fieldnames(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    return fieldnames
