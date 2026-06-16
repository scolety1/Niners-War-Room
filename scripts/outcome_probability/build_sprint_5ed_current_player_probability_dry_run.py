from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_sprint_5ct_phase5_candidate_modeling_harness as phase5

RANKINGS_POOL = REPO_ROOT / "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
FEATURE_SNAPSHOTS = REPO_ROOT / (
    "local_exports/outcome_probability/sprint_5aw_2026_identity_repair/"
    "current_2026_veteran_feature_snapshots_after_identity_repair.csv"
)
OUTPUT_DIR = REPO_ROOT / (
    "local_exports/outcome_probability/phase10_numeric_probability_display_runway/"
    "sprint_5ed_current_player_probability_dry_run"
)

APPROVED_HEADS = ("qb_t12", "rb_t12", "rb_t24", "wr_t12", "wr_t24", "wr_t36", "te_t12")
HEAD_POSITION = {
    "qb_t12": "QB",
    "rb_t12": "RB",
    "rb_t24": "RB",
    "wr_t12": "WR",
    "wr_t24": "WR",
    "wr_t36": "WR",
    "te_t12": "TE",
}
PROBABILITY_COLUMNS = tuple(f"{head}_probability_audit_unit" for head in APPROVED_HEADS)
FORBIDDEN_OUTPUT_TERMS = (
    "sort",
    "rank_delta",
    "ranking_delta",
    "market",
    "projection",
    "adp",
    "trade",
    "rotowire",
    "private_score",
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pool_rows = _read_rows(RANKINGS_POOL)
    feature_rows = _read_rows(FEATURE_SNAPSHOTS)
    features_by_player_id = {
        str(row.get("current_player_id") or ""): row
        for row in feature_rows
        if row.get("current_player_id") and row.get("snapshot_status") == "ready_feature_snapshot"
    }
    historical_rows = phase5.load_historical_rows()
    models = _fit_models(historical_rows)
    output_rows = _score_rows(pool_rows, features_by_player_id, models)
    _assert_no_forbidden_output_columns(output_rows)

    output_path = OUTPUT_DIR / "current_player_probability_dry_run.csv"
    fieldnames = (
        "output_scope",
        "player_id",
        "player_display_name",
        "position",
        *PROBABILITY_COLUMNS,
        "outcome_probability_status",
        "unavailable_reason",
        "approved_heads_available",
        "feature_source_path",
        "historical_training_source",
        "model_family",
        "code_version_git_commit",
    )
    _write_csv(output_path, output_rows, fieldnames)
    summary = _summary(output_rows, models)
    summary_path = OUTPUT_DIR / "current_player_probability_dry_run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (OUTPUT_DIR / "README.md").write_text(
        "# Sprint 5ED local-only current-player probability dry run\n\n"
        "Quarantined local evidence only. Not app-readable. Not promoted. No UI/source "
        "wiring, rankings/sorting fields, hidden sort keys, exact app percentages, or "
        "coarse app bands were created.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


def _fit_models(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    models: dict[str, dict[str, object]] = {}
    for head in APPROVED_HEADS:
        position, canonical_head = phase5.APPROVED_HEADS[head]
        train = [row for row in rows if row["position"] == position]
        train_x = [phase5.feature_values(row) for row in train]
        train_y = [1 if row["threshold_labels"][canonical_head] else 0 for row in train]
        positives = sum(train_y)
        if positives <= 0 or positives >= len(train_y):
            phase5.fail(f"cannot fit local dry-run model for {head}")
        weights = phase5.fit_logistic(train_x, train_y)
        models[head] = {
            "position": position,
            "canonical_head": canonical_head,
            "train_x": train_x,
            "weights": weights,
            "train_rows": len(train_y),
            "train_positives": positives,
        }
    return models


def _score_rows(
    pool_rows: list[dict[str, str]],
    features_by_player_id: dict[str, dict[str, str]],
    models: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    output_rows: list[dict[str, object]] = []
    for row in pool_rows:
        position = str(row.get("position") or "").upper()
        player_id = str(row.get("player_id") or "")
        feature_row = features_by_player_id.get(player_id)
        base = {
            "output_scope": "local_only_not_app_readable",
            "player_id": player_id,
            "player_display_name": row.get("player_name") or "",
            "position": position,
            "outcome_probability_status": "unavailable",
            "unavailable_reason": "",
            "approved_heads_available": "",
            "feature_source_path": str(FEATURE_SNAPSHOTS.relative_to(REPO_ROOT)),
            "historical_training_source": "local historical 2010-2019 feature/label packages",
            "model_family": "low_complexity_logistic_local_dry_run",
            "code_version_git_commit": _git_commit(),
        }
        for column in PROBABILITY_COLUMNS:
            base[column] = ""
        reason = _unavailable_reason(row, feature_row)
        if reason:
            base["unavailable_reason"] = reason
            output_rows.append(base)
            continue
        if feature_row is None:
            base["unavailable_reason"] = "missing_feature_snapshot"
            output_rows.append(base)
            continue
        current_x = [[float(feature_row[name]) for name in phase5.APPROVED_FEATURES]]
        available_heads: list[str] = []
        for head in APPROVED_HEADS:
            if HEAD_POSITION[head] != position:
                continue
            model = models[head]
            probability = phase5.logistic_predict(
                model["train_x"],  # type: ignore[arg-type]
                current_x,
                model["weights"],  # type: ignore[arg-type]
            )[0]
            base[f"{head}_probability_audit_unit"] = f"{probability:.6f}"
            available_heads.append(head)
        if available_heads:
            base["outcome_probability_status"] = "local_dry_run_probability_available"
            base["approved_heads_available"] = "|".join(available_heads)
        else:
            base["unavailable_reason"] = "no_approved_head_for_position"
        output_rows.append(base)
    return output_rows


def _unavailable_reason(
    row: dict[str, str],
    feature_row: dict[str, str] | None,
) -> str:
    position = str(row.get("position") or "").upper()
    if position not in {"QB", "RB", "WR", "TE"}:
        return "unsupported_position"
    if str(row.get("is_rookie") or "") == "1":
        return "rookie_unavailable_for_veteran_heads"
    if feature_row is None:
        return "missing_feature_snapshot"
    missing = [name for name in phase5.APPROVED_FEATURES if not str(feature_row.get(name) or "").strip()]
    if missing:
        return "missing_required_features"
    return ""


def _summary(
    rows: list[dict[str, object]],
    models: dict[str, dict[str, object]],
) -> dict[str, object]:
    status_counts = Counter(str(row.get("outcome_probability_status") or "") for row in rows)
    unavailable_counts = Counter(
        str(row.get("unavailable_reason") or "available")
        for row in rows
    )
    position_counts = Counter(str(row.get("position") or "") for row in rows)
    emitted_by_head = {
        head: sum(1 for row in rows if row.get(f"{head}_probability_audit_unit"))
        for head in APPROVED_HEADS
    }
    ranges = {}
    for head in APPROVED_HEADS:
        values = [
            float(row[f"{head}_probability_audit_unit"])
            for row in rows
            if row.get(f"{head}_probability_audit_unit")
        ]
        ranges[head] = {
            "count": len(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }
    return {
        "verdict": "GREEN",
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "output_scope": "local_only_not_app_readable",
        "output_dir": str(OUTPUT_DIR.relative_to(REPO_ROOT)),
        "player_pool_rows": len(rows),
        "position_counts": dict(sorted(position_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "unavailable_reason_counts": dict(sorted(unavailable_counts.items())),
        "approved_heads_emitted": list(APPROVED_HEADS),
        "rb_t24_included": True,
        "rb_t24_inclusion_reason": "5EC GREEN-upgraded rb_t24 for quarantined local-only dry run.",
        "emitted_probability_counts_by_head": emitted_by_head,
        "probability_ranges_by_head": ranges,
        "model_support_by_head": {
            head: {
                "train_rows": model["train_rows"],
                "train_positives": model["train_positives"],
                "canonical_head": model["canonical_head"],
            }
            for head, model in models.items()
        },
        "app_readable_output_created": False,
        "app_wiring_created": False,
        "rankings_sorting_fields_created": False,
        "hidden_sort_keys_created": False,
        "promoted_artifacts_created": False,
    }


def _assert_no_forbidden_output_columns(rows: list[dict[str, object]]) -> None:
    if not rows:
        phase5.fail("no dry-run rows created")
    columns = set(rows[0])
    matches = [
        column
        for column in columns
        if any(term in column.lower() for term in FORBIDDEN_OUTPUT_TERMS)
    ]
    if matches:
        phase5.fail(f"forbidden output columns detected: {matches}")


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        phase5.fail(f"missing required input: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: tuple[str, ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    main()
