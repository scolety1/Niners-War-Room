from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RANKINGS_POOL = Path("local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv")
FEATURE_SNAPSHOTS = Path(
    "local_exports/outcome_probability/sprint_5aw_2026_identity_repair/"
    "current_2026_veteran_feature_snapshots_after_identity_repair.csv"
)
PHASE5_HEAD_VERDICTS = Path(
    "local_exports/outcome_probability/sprint_5cu_phase5_local_candidate_model_evaluation/"
    "head_candidate_verdicts.csv"
)
PHASE6_HEAD_VERDICTS = Path(
    "local_exports/outcome_probability/sprint_5da_phase6_local_only_production_candidate_modeling/"
    "head_candidate_verdicts.csv"
)
OUTPUT_DIR = Path(
    "local_exports/outcome_probability/phase10_numeric_probability_display_runway/"
    "sprint_5ec_current_player_feature_coverage"
)

TARGET_HEADS = ("qb_t12", "rb_t12", "rb_t24", "wr_t12", "wr_t24", "wr_t36", "te_t12")
PHASE6_ACCEPTED_HEADS = ("qb_t12", "rb_t12", "wr_t12", "wr_t24", "wr_t36", "te_t12")
HEAD_POSITION = {
    "qb_t12": "QB",
    "rb_t12": "RB",
    "rb_t24": "RB",
    "wr_t12": "WR",
    "wr_t24": "WR",
    "wr_t36": "WR",
    "te_t12": "TE",
}
REQUIRED_FEATURES = (
    "prior_season_nwr_ppg",
    "prior_season_nwr_finish_rank",
    "prior_completed_season_games",
    "prior_completed_season_games_played",
    "prior_completed_season_games_active",
    "prior_completed_season_passing_yards",
    "prior_completed_season_rushing_yards",
    "prior_completed_season_receiving_yards",
    "prior_completed_season_rushing_first_downs",
    "prior_completed_season_receiving_first_downs",
    "prior_completed_season_receptions",
)


def main() -> None:
    pool_rows = _read_rows(RANKINGS_POOL)
    feature_rows = _read_rows(FEATURE_SNAPSHOTS)
    feature_by_player_id = {
        str(row.get("current_player_id") or ""): row
        for row in feature_rows
        if row.get("current_player_id") and row.get("snapshot_status") == "ready_feature_snapshot"
    }
    phase5 = _read_verdicts(PHASE5_HEAD_VERDICTS)
    phase6 = _read_verdicts(PHASE6_HEAD_VERDICTS)

    coverage_rows: list[dict[str, object]] = []
    position_counts = Counter(str(row.get("position") or "").upper() for row in pool_rows)
    ready_by_position = Counter()
    missing_by_position = Counter()
    rookie_rows = 0
    unsupported_rows = 0
    for row in pool_rows:
        position = str(row.get("position") or "").upper()
        player_id = str(row.get("player_id") or "")
        is_rookie = str(row.get("is_rookie") or "") == "1"
        if is_rookie:
            rookie_rows += 1
        if position not in {"QB", "RB", "WR", "TE"}:
            unsupported_rows += 1
        feature = feature_by_player_id.get(player_id)
        missing_features = _missing_required_features(feature)
        ready = (
            position in {"QB", "RB", "WR", "TE"}
            and not is_rookie
            and feature is not None
            and not missing_features
        )
        if ready:
            ready_by_position[position] += 1
        else:
            missing_by_position[position] += 1
        coverage_rows.append(
            {
                "player_id": player_id,
                "player_name": row.get("player_name", ""),
                "position": position,
                "pool_status": row.get("pool_status", ""),
                "is_rookie": row.get("is_rookie", ""),
                "feature_snapshot_ready": "yes" if feature else "no",
                "missing_required_features": "|".join(missing_features),
                "eligibility": "eligible_for_local_dry_run" if ready else _ineligible_reason(row, feature, missing_features),
            }
        )

    rb_t24_phase5 = phase5.get("rb_t24", {})
    rb_t24_decision = _rb_t24_decision(rb_t24_phase5, ready_by_position["RB"])
    approved_heads = [
        head
        for head in TARGET_HEADS
        if head in PHASE6_ACCEPTED_HEADS or (head == "rb_t24" and rb_t24_decision["decision"] == "GREEN_UPGRADED_FOR_LOCAL_DRY_RUN")
    ]

    summary = {
        "verdict": "GREEN",
        "rankings_pool_path": str(RANKINGS_POOL),
        "feature_snapshot_path": str(FEATURE_SNAPSHOTS),
        "rankings_pool_rows": len(pool_rows),
        "feature_snapshot_ready_rows": len(feature_by_player_id),
        "position_counts": dict(sorted(position_counts.items())),
        "ready_feature_coverage_by_position": dict(sorted(ready_by_position.items())),
        "not_ready_by_position": dict(sorted(missing_by_position.items())),
        "rookie_rows": rookie_rows,
        "unsupported_position_rows": unsupported_rows,
        "phase6_accepted_heads": list(PHASE6_ACCEPTED_HEADS),
        "target_heads": list(TARGET_HEADS),
        "approved_heads_for_local_dry_run": approved_heads,
        "rb_t24_phase5_evidence": rb_t24_phase5,
        "rb_t24_phase6_evidence": phase6.get("rb_t24", {"candidate_verdict": "excluded_from_phase6"}),
        "rb_t24_decision": rb_t24_decision,
        "probabilities_emitted": False,
        "app_readable_artifact_created": False,
        "app_source_files_edited": False,
        "rankings_sorting_changed": False,
        "hidden_sort_keys_created": False,
        "promoted_artifacts_created": False,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "current_player_feature_coverage_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    with (OUTPUT_DIR / "current_player_feature_coverage_rows.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(coverage_rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(coverage_rows)
    print(json.dumps(summary, indent=2, sort_keys=True))


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_verdicts(path: Path) -> dict[str, dict[str, str]]:
    return {row.get("head", ""): row for row in _read_rows(path) if row.get("head")}


def _missing_required_features(row: dict[str, str] | None) -> tuple[str, ...]:
    if row is None:
        return REQUIRED_FEATURES
    missing = []
    for feature in REQUIRED_FEATURES:
        value = str(row.get(feature) or "").strip()
        if not value:
            missing.append(feature)
    return tuple(missing)


def _ineligible_reason(
    row: dict[str, str],
    feature: dict[str, str] | None,
    missing_features: tuple[str, ...],
) -> str:
    position = str(row.get("position") or "").upper()
    if position not in {"QB", "RB", "WR", "TE"}:
        return "unsupported_position"
    if str(row.get("is_rookie") or "") == "1":
        return "rookie_unavailable_for_veteran_heads"
    if feature is None:
        return "missing_feature_snapshot"
    if missing_features:
        return "missing_required_features"
    return "unavailable_unknown_reason"


def _rb_t24_decision(evidence: dict[str, str], ready_rb_rows: int) -> dict[str, object]:
    verdict = evidence.get("candidate_verdict", "")
    brier = _float(evidence.get("brier_mean"))
    base_brier = _float(evidence.get("base_brier_mean"))
    log_loss = _float(evidence.get("log_loss_mean"))
    base_log_loss = _float(evidence.get("base_log_loss_mean"))
    thin_bins = int(float(evidence.get("thin_calibration_bins") or 999))
    improves_brier = brier is not None and base_brier is not None and brier < base_brier
    improves_log_loss = (
        log_loss is not None and base_log_loss is not None and log_loss < base_log_loss
    )
    if (
        verdict == "candidate_caution"
        and improves_brier
        and improves_log_loss
        and ready_rb_rows >= 20
    ):
        return {
            "decision": "GREEN_UPGRADED_FOR_LOCAL_DRY_RUN",
            "reason": (
                "HQ-requested rb_t24 remains display-gated, but Phase 5 metrics improved "
                "Brier/log-loss versus base rate and current RB feature coverage is enough "
                "for a quarantined local-only dry run."
            ),
            "thin_calibration_bins": thin_bins,
            "display_release_approved": False,
        }
    return {
        "decision": "NOT_GREEN_EXCLUDE_OR_STOP",
        "reason": "rb_t24 did not satisfy the local dry-run upgrade gate.",
        "thin_calibration_bins": thin_bins,
        "display_release_approved": False,
    }


def _float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
