from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.data.csv_schemas import CSV_SCHEMAS
from src.data.validators import validate_data_pack
from src.services.lve_stats_first_preview_service import (
    DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    STATS_FIRST_PREVIEW_MANIFEST_FILE,
    STATS_FIRST_PREVIEW_OUTPUT_FILE,
    stats_first_preview_review_rows,
)
from src.services.market_influence_policy_service import cap_market_blended_value

DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT = Path("local_exports/data_packs")
STATS_FIRST_APPLIED_PACK_MANIFEST_FILE = "stats_first_applied_pack_manifest.json"
STATS_FIRST_APPLY_CONFIRMATION = "APPLY_STATS_FIRST_PREVIEW"


@dataclass(frozen=True)
class StatsFirstApplyResult:
    applied_pack_id: str
    source_pack_path: Path
    applied_pack_path: Path
    manifest_path: Path
    status: str
    created: bool
    applied_row_count: int
    message: str


def create_stats_first_applied_pack(
    data_pack_path: str | Path,
    preview_root: str | Path = DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    output_root: str | Path = DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT,
    *,
    preview_id: str,
    applied_pack_id: str | None = None,
    confirmation_text: str,
    created_at: str | None = None,
) -> StatsFirstApplyResult:
    source_pack = Path(data_pack_path)
    created = created_at or _now_utc()
    resolved_pack_id = _slug(applied_pack_id or f"{source_pack.name}_{preview_id}_stats_first")
    target = Path(output_root) / resolved_pack_id
    manifest_path = target / STATS_FIRST_APPLIED_PACK_MANIFEST_FILE
    if confirmation_text != STATS_FIRST_APPLY_CONFIRMATION:
        return _blocked(
            resolved_pack_id,
            source_pack,
            target,
            manifest_path,
            "Confirmation text did not match; no applied pack was created.",
        )
    if target.exists():
        return _blocked(
            resolved_pack_id,
            source_pack,
            target,
            manifest_path,
            "Applied pack already exists; choose a new applied pack id.",
        )
    validated = validate_data_pack(source_pack)
    if validated.has_errors:
        return _blocked(
            resolved_pack_id,
            source_pack,
            target,
            manifest_path,
            "Source data pack has validation errors; fix Import Review before applying.",
        )
    preview_dir = Path(preview_root) / preview_id
    preview_output_path = preview_dir / STATS_FIRST_PREVIEW_OUTPUT_FILE
    preview_manifest_path = preview_dir / STATS_FIRST_PREVIEW_MANIFEST_FILE
    if not preview_output_path.exists() or not preview_manifest_path.exists():
        return _blocked(
            resolved_pack_id,
            source_pack,
            target,
            manifest_path,
            "Preview output or manifest is missing; regenerate the preview.",
        )

    ready_rows = _ready_preview_output_rows(preview_root, preview_id)
    if not ready_rows:
        return _blocked(
            resolved_pack_id,
            source_pack,
            target,
            manifest_path,
            "No review-ready preview rows are available to apply.",
        )
    duplicate_ids = _duplicate_player_ids(ready_rows)
    if duplicate_ids:
        return _blocked(
            resolved_pack_id,
            source_pack,
            target,
            manifest_path,
            "Duplicate ready preview rows found for: " + ", ".join(duplicate_ids[:5]),
        )

    shutil.copytree(source_pack, target)
    model_outputs_path = target / "model_outputs.csv"
    applied_count = _apply_ready_preview_rows(model_outputs_path, ready_rows)
    preview_manifest = _read_json(preview_manifest_path)
    manifest = {
        "applied_pack_id": resolved_pack_id,
        "created_at": created,
        "source_pack_path": str(source_pack.resolve()),
        "source_preview_id": preview_id,
        "source_preview_path": str(preview_dir.resolve()),
        "source_preview_model_version": preview_manifest.get("model_version", ""),
        "applied_row_count": applied_count,
        "ready_preview_row_count": len(ready_rows),
        "confirmation_required": STATS_FIRST_APPLY_CONFIRMATION,
        "scoring_effect": (
            "generated pack copy only; source pack and selected pack were not overwritten"
        ),
        "review_next_action": "Run Import Review admission on this applied pack before draft use.",
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return StatsFirstApplyResult(
        applied_pack_id=resolved_pack_id,
        source_pack_path=source_pack.resolve(),
        applied_pack_path=target.resolve(),
        manifest_path=manifest_path.resolve(),
        status="created",
        created=True,
        applied_row_count=applied_count,
        message="Stats-first applied pack copy created. Source pack was not changed.",
    )


def stats_first_applied_pack_snapshot_rows(
    output_root: str | Path = DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT,
) -> list[dict[str, object]]:
    root = Path(output_root)
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for pack_path in sorted(root.iterdir(), reverse=True):
        if not pack_path.is_dir():
            continue
        manifest = _read_json(pack_path / STATS_FIRST_APPLIED_PACK_MANIFEST_FILE)
        if not manifest:
            continue
        rows.append(
            {
                "applied_pack_id": manifest.get("applied_pack_id", pack_path.name),
                "created_at": manifest.get("created_at", ""),
                "source_preview_id": manifest.get("source_preview_id", ""),
                "applied_row_count": manifest.get("applied_row_count", 0),
                "applied_pack_path": str(pack_path),
                "scoring_effect": manifest.get("scoring_effect", ""),
                "next_action": manifest.get("review_next_action", ""),
            }
        )
    return rows


def stats_first_applied_pack_review_rows(
    output_root: str | Path = DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for snapshot in stats_first_applied_pack_snapshot_rows(output_root):
        pack_path = Path(str(snapshot["applied_pack_path"]))
        manifest = _read_json(pack_path / STATS_FIRST_APPLIED_PACK_MANIFEST_FILE)
        try:
            validated = validate_data_pack(pack_path)
            validation_errors = sum(1 for issue in validated.issues if issue.severity == "error")
            validation_warnings = sum(
                1 for issue in validated.issues if issue.severity == "warning"
            )
        except Exception as exc:  # pragma: no cover - defensive for malformed local folders
            validation_errors = 1
            validation_warnings = 0
            rows.append(
                {
                    **snapshot,
                    "review_status": "blocked",
                    "reason": f"Applied pack could not be validated: {exc}",
                    "next_action": "Regenerate the applied pack copy.",
                }
            )
            continue
        applied_count = int(manifest.get("applied_row_count") or 0)
        if validation_errors:
            status = "blocked"
            reason = "Applied pack has validation errors."
            next_action = "Fix or regenerate the applied pack before use."
        elif applied_count <= 0:
            status = "blocked"
            reason = "Applied pack manifest reports zero applied rows."
            next_action = "Regenerate from a ready preview."
        elif validation_warnings:
            status = "review"
            reason = "Applied pack validates with warnings."
            next_action = "Open Import Review admission before using this pack."
        else:
            status = "ready"
            reason = "Applied pack copy validates and contains applied model rows."
            next_action = "Run Import Review admission and select this pack only if ready."
        rows.append(
            {
                **snapshot,
                "review_status": status,
                "reason": reason,
                "validation_error_count": validation_errors,
                "validation_warning_count": validation_warnings,
                "next_action": next_action,
            }
        )
    return rows


def _ready_preview_output_rows(
    preview_root: str | Path,
    preview_id: str,
) -> list[dict[str, str]]:
    review_ready_ids = {
        str(row.get("player_id") or "")
        for row in stats_first_preview_review_rows(preview_root)
        if row.get("preview_id") == preview_id and row.get("review_status") == "ready"
    }
    if not review_ready_ids:
        return []
    output_path = Path(preview_root) / preview_id / STATS_FIRST_PREVIEW_OUTPUT_FILE
    with output_path.open(newline="", encoding="utf-8") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if str(row.get("player_id") or "") in review_ready_ids
        ]


def _apply_ready_preview_rows(
    model_outputs_path: Path,
    preview_rows: list[dict[str, str]],
) -> int:
    header, live_rows = _read_csv(model_outputs_path)
    schema_header = list(CSV_SCHEMAS["model_outputs.csv"].all_columns)
    output_header = list(dict.fromkeys([*(header or []), *schema_header]))
    preview_by_player = {row["player_id"]: row for row in preview_rows}
    applied_count = 0
    output_rows: list[dict[str, object]] = []
    for live_row in live_rows:
        player_id = str(live_row.get("player_id") or "")
        preview_row = preview_by_player.get(player_id)
        if not preview_row:
            output_rows.append(live_row)
            continue
        applied_count += 1
        updated = dict(live_row)
        updated.update(_live_model_row_from_preview(live_row, preview_row))
        output_rows.append(updated)
    _write_csv(model_outputs_path, output_header, output_rows)
    return applied_count


def _live_model_row_from_preview(
    live_row: dict[str, str],
    preview_row: dict[str, str],
) -> dict[str, object]:
    keeper = _float(preview_row.get("keeper_score"))
    trade = _float(preview_row.get("trade_value"))
    private = _float(preview_row.get("private_lve_value"))
    market_trade_value = _float(preview_row.get("market_trade_value"), trade)
    warning_status = preview_row.get("warning_status", "")
    risk_flags = preview_row.get("risk_flags", "")
    return {
        "snapshot_date": live_row.get("snapshot_date", ""),
        "player_id": preview_row.get("player_id", ""),
        "player_name": preview_row.get("player_name", live_row.get("player_name", "")),
        "position": preview_row.get("position", live_row.get("position", "")),
        "overall_rank": preview_row.get("overall_rank", ""),
        "position_rank": preview_row.get("position_rank", ""),
        "position_rank_label": preview_row.get("position_rank_label", ""),
        "private_score": private,
        "market_score": market_trade_value,
        "war_score": cap_market_blended_value(keeper, (keeper * 0.70) + (trade * 0.30)),
        "keeper_score": keeper,
        "drop_candidate_score": preview_row.get("drop_candidate_score", ""),
        "veteran_base_value": private,
        "win_now_value": preview_row.get("win_now_value", ""),
        "dynasty_hold_value": preview_row.get("dynasty_hold_value", ""),
        "horizon_retention_score": preview_row.get("horizon_retention_score", ""),
        "trade_value": trade,
        "market_trade_value": market_trade_value,
        "market_edge_score": preview_row.get("market_edge_score", ""),
        "market_edge_label": preview_row.get("market_edge_label", ""),
        "market_edge_warning": preview_row.get("market_edge_warning", ""),
        "lve_format_fit": private,
        "structural_adjustment": preview_row.get("structural_adjustment", ""),
        "cross_position_replacement_baseline": preview_row.get(
            "cross_position_replacement_baseline",
            "",
        ),
        "lve_lineup_demand_adjustment": preview_row.get(
            "lve_lineup_demand_adjustment",
            "",
        ),
        "missing_data_penalty": "",
        "risk_flags": risk_flags,
        "upside_flags": preview_row.get("upside_flags", ""),
        "floor_flags": preview_row.get("floor_flags", ""),
        "pick_adjusted_value": round(trade * 10, 1),
        "confidence_score": preview_row.get("confidence_score", ""),
        "risk_level": _risk_level(warning_status, risk_flags),
        "warning_status": warning_status,
        "warning_reasons": preview_row.get("warning_reasons", ""),
        "recommendation": _recommendation(_float(preview_row.get("drop_candidate_score")), keeper),
        "model_version": preview_row.get("model_version", ""),
        "computed_at": preview_row.get("computed_at", ""),
        "rank_audit": preview_row.get("rank_audit", ""),
        "notes": (
            "Applied from stats-first preview copy; source pack was not overwritten. "
            "Private score is statistics-first; market_score is trade liquidity."
        ),
    }


def _risk_level(warning_status: str, risk_flags: str) -> str:
    if warning_status in {"blocking", "review_needed"}:
        return "high"
    if risk_flags:
        return "medium"
    return "low"


def _recommendation(drop_score: float, keeper_score: float) -> str:
    if drop_score >= 55:
        return "shop/release"
    if drop_score >= 35:
        return "shop"
    if keeper_score >= 82:
        return "keep"
    return "bubble"


def _duplicate_player_ids(rows: list[dict[str, str]]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        player_id = str(row.get("player_id") or "")
        if player_id in seen:
            duplicates.add(player_id)
        seen.add(player_id)
    return sorted(duplicates)


def _blocked(
    applied_pack_id: str,
    source_pack_path: Path,
    applied_pack_path: Path,
    manifest_path: Path,
    message: str,
) -> StatsFirstApplyResult:
    return StatsFirstApplyResult(
        applied_pack_id=applied_pack_id,
        source_pack_path=source_pack_path,
        applied_pack_path=applied_pack_path,
        manifest_path=manifest_path,
        status="blocked",
        created=False,
        applied_row_count=0,
        message=message,
    )


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "stats_first_applied_pack"
