from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.services.lve_normalization_service import NORMALIZED_FEATURE_HEADER
from src.services.lve_stats_first_veteran_formula_service import (
    STATS_FIRST_MODEL_VERSION,
    StatsFirstVeteranScore,
    score_stats_first_veteran_rows,
    stats_first_output_rows,
)

DEFAULT_STATS_FIRST_PREVIEW_ROOT = Path("local_exports/nflverse_model_previews")
STATS_FIRST_PREVIEW_MANIFEST_FILE = "stats_first_preview_manifest.json"
STATS_FIRST_PREVIEW_OUTPUT_FILE = "stats_first_veteran_model_preview_outputs.csv"
STATS_FIRST_PREVIEW_CONTRIBUTIONS_FILE = "stats_first_feature_contributions.csv"


@dataclass(frozen=True)
class StatsFirstPreviewResult:
    preview_id: str
    preview_path: Path
    output_path: Path
    contribution_path: Path
    manifest_path: Path
    created: bool
    row_count: int
    message: str


def create_stats_first_model_preview(
    normalized_feature_path: str | Path,
    output_root: str | Path = DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    *,
    preview_id: str | None = None,
    computed_at: str | None = None,
) -> StatsFirstPreviewResult:
    created_at = computed_at or _now_utc()
    resolved_preview_id = _preview_id(preview_id, created_at)
    preview_path = Path(output_root) / resolved_preview_id
    output_path = preview_path / STATS_FIRST_PREVIEW_OUTPUT_FILE
    contribution_path = preview_path / STATS_FIRST_PREVIEW_CONTRIBUTIONS_FILE
    manifest_path = preview_path / STATS_FIRST_PREVIEW_MANIFEST_FILE

    if preview_path.exists():
        return StatsFirstPreviewResult(
            preview_id=resolved_preview_id,
            preview_path=preview_path,
            output_path=output_path,
            contribution_path=contribution_path,
            manifest_path=manifest_path,
            created=False,
            row_count=0,
            message="Stats-first preview already exists; choose a new preview id.",
        )

    header, rows = _read_normalized_rows(normalized_feature_path)
    missing_required = [column for column in NORMALIZED_FEATURE_HEADER if column not in header]
    if missing_required:
        return StatsFirstPreviewResult(
            preview_id=resolved_preview_id,
            preview_path=preview_path,
            output_path=output_path,
            contribution_path=contribution_path,
            manifest_path=manifest_path,
            created=False,
            row_count=0,
            message=(
                "Normalized feature file is missing required columns: "
                + ", ".join(missing_required[:5])
            ),
        )
    if not rows:
        return StatsFirstPreviewResult(
            preview_id=resolved_preview_id,
            preview_path=preview_path,
            output_path=output_path,
            contribution_path=contribution_path,
            manifest_path=manifest_path,
            created=False,
            row_count=0,
            message="No normalized veteran feature rows are available for preview.",
        )

    scores = score_stats_first_veteran_rows(tuple(rows))
    output_rows = stats_first_output_rows(scores, computed_at=created_at)
    contribution_rows = _contribution_rows(scores)
    preview_path.mkdir(parents=True, exist_ok=False)
    _write_csv(output_path, output_rows)
    _write_csv(contribution_path, contribution_rows)
    manifest = {
        "preview_id": resolved_preview_id,
        "created_at": created_at,
        "model_version": STATS_FIRST_MODEL_VERSION,
        "source_file": str(Path(normalized_feature_path)),
        "output_file": STATS_FIRST_PREVIEW_OUTPUT_FILE,
        "contribution_file": STATS_FIRST_PREVIEW_CONTRIBUTIONS_FILE,
        "row_count": len(output_rows),
        "review_status": _overall_review_status(output_rows),
        "apply_boundary": (
            "preview_only; does not overwrite live model_outputs.csv or selected data pack"
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return StatsFirstPreviewResult(
        preview_id=resolved_preview_id,
        preview_path=preview_path.resolve(),
        output_path=output_path.resolve(),
        contribution_path=contribution_path.resolve(),
        manifest_path=manifest_path.resolve(),
        created=True,
        row_count=len(output_rows),
        message="Stats-first model preview created. Live model outputs were not changed.",
    )


def stats_first_preview_snapshot_rows(
    output_root: str | Path = DEFAULT_STATS_FIRST_PREVIEW_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for preview_path in sorted(root.iterdir(), reverse=True):
        if not preview_path.is_dir():
            continue
        manifest = _read_manifest(preview_path / STATS_FIRST_PREVIEW_MANIFEST_FILE)
        if not manifest:
            continue
        rows.append(
            {
                "preview_id": manifest.get("preview_id", preview_path.name),
                "created_at": manifest.get("created_at", ""),
                "model_version": manifest.get("model_version", ""),
                "row_count": manifest.get("row_count", 0),
                "review_status": manifest.get("review_status", "review"),
                "preview_path": str(preview_path),
                "output_file": manifest.get("output_file", STATS_FIRST_PREVIEW_OUTPUT_FILE),
                "apply_boundary": manifest.get("apply_boundary", "preview_only"),
            }
        )
    return rows


def stats_first_preview_review_rows(
    output_root: str | Path = DEFAULT_STATS_FIRST_PREVIEW_ROOT,
) -> list[dict[str, object]]:
    review_rows: list[dict[str, object]] = []
    root = Path(output_root)
    if not root.exists():
        return review_rows
    for preview_path in sorted(root.iterdir(), reverse=True):
        if not preview_path.is_dir():
            continue
        manifest = _read_manifest(preview_path / STATS_FIRST_PREVIEW_MANIFEST_FILE)
        output_file = preview_path / str(
            manifest.get("output_file") or STATS_FIRST_PREVIEW_OUTPUT_FILE
        )
        if not output_file.exists():
            continue
        with output_file.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                status, reason, next_action = _row_review(row)
                review_rows.append(
                    {
                        "preview_id": manifest.get("preview_id", preview_path.name),
                        "player_id": row.get("player_id", ""),
                        "player_name": row.get("player_name", ""),
                        "position": row.get("position", ""),
                        "private_lve_value": row.get("private_lve_value", ""),
                        "keeper_score": row.get("keeper_score", ""),
                        "drop_candidate_score": row.get("drop_candidate_score", ""),
                        "trade_value": row.get("trade_value", ""),
                        "confidence_score": row.get("confidence_score", ""),
                        "warning_status": row.get("warning_status", ""),
                        "review_status": status,
                        "review_reason": reason,
                        "next_action": next_action,
                    }
                )
    return review_rows


def stats_first_preview_review_summary_rows(
    review_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    if not review_rows:
        return [
            {
                "review_status": "needed",
                "rows": 0,
                "next_action": "Create a stats-first preview from normalized veteran features.",
            }
        ]
    output: list[dict[str, object]] = []
    for status in ("ready", "review", "blocked"):
        count = sum(1 for row in review_rows if row.get("review_status") == status)
        output.append(
            {
                "review_status": status,
                "rows": count,
                "next_action": _summary_next_action(status),
            }
        )
    return output


def _contribution_rows(scores: tuple[StatsFirstVeteranScore, ...]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for score in scores:
        for contribution in score.contributions:
            rows.append(
                {
                    "player_id": contribution.player_id,
                    "player_name": score.player_name,
                    "position": score.position,
                    "component": contribution.component,
                    "feature_name": contribution.feature_name,
                    "normalized_score": contribution.normalized_score,
                    "feature_weight": contribution.feature_weight,
                    "component_contribution": contribution.component_contribution,
                    "model_version": score.model_version,
                }
            )
    return rows


def _row_review(row: dict[str, object]) -> tuple[str, str, str]:
    warning_status = str(row.get("warning_status") or "")
    confidence = _float(row.get("confidence_score"))
    risk_flags = str(row.get("risk_flags") or "")
    if warning_status == "blocking" or confidence < 40:
        return (
            "blocked",
            "Preview output has blocking warnings or very low confidence.",
            "Fix normalized source rows and regenerate the preview.",
        )
    if warning_status in {"review_needed", "model_warning"} or confidence < 72:
        return (
            "review",
            "Preview scored, but warnings, risk, or confidence need inspection.",
            "Inspect this row before any later apply workflow.",
        )
    if "drop_candidate" in risk_flags or "keeper_bubble" in risk_flags:
        return (
            "review",
            "Preview row is decision-sensitive because it changes keep/drop pressure.",
            "Compare against live output and roster context before applying.",
        )
    return (
        "ready",
        "Preview row clears confidence and warning checks.",
        "Eligible for Phase 11 preview-vs-live comparison.",
    )


def _overall_review_status(output_rows: list[dict[str, object]]) -> str:
    statuses = [_row_review(row)[0] for row in output_rows]
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "review" for status in statuses):
        return "review"
    return "ready"


def _summary_next_action(status: str) -> str:
    if status == "ready":
        return "Ready rows can proceed to preview-vs-live comparison."
    if status == "review":
        return "Review warnings and score movement before any later apply step."
    return "Blocked rows must be fixed and previewed again."


def _read_normalized_rows(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _preview_id(preview_id: str | None, created_at: str) -> str:
    if preview_id:
        return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in preview_id)
    return "stats_first_" + created_at.replace("-", "").replace(":", "").replace("+", "_").replace(
        "Z", ""
    )


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default
