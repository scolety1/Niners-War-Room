"""Sprint 5CL local-only threshold-head support evaluation.

Counts support for candidate future-outcome heads from the 5CK-R2 consolidated
inventory. This script does not train, predict, calibrate, rank, or create
probabilities, exact percentages, bands, app outputs, or promoted artifacts.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTCOME_EXPORT_ROOT = REPO_ROOT / "local_exports" / "outcome_probability"
SOURCE_DIR = OUTCOME_EXPORT_ROOT / "sprint_5ck_r2_consolidated_2010_2019_historical_model_readiness_reaudit"
RUN_ID = "sprint_5cl_threshold_head_support_evaluation"
OUT_DIR = OUTCOME_EXPORT_ROOT / RUN_ID

HEAD_LABELS = {
    "QB": {
        "same_year_qb_t6": "QB Top 6",
        "same_year_qb_t12": "QB Top 12",
        "same_year_qb_t18": "QB Top 18",
        "same_year_qb_t24": "QB Top 24",
    },
    "RB": {
        "same_year_rb_t6": "RB Top 6",
        "same_year_rb_t12": "RB Top 12",
        "same_year_rb_t24": "RB Top 24",
        "same_year_rb_t36": "RB Top 36",
        "same_year_rb_t48": "RB Top 48",
    },
    "WR": {
        "same_year_wr_t6": "WR Top 6",
        "same_year_wr_t12": "WR Top 12",
        "same_year_wr_t24": "WR Top 24",
        "same_year_wr_t36": "WR Top 36",
        "same_year_wr_t48": "WR Top 48",
    },
    "TE": {
        "same_year_te_t3": "TE Top 3",
        "same_year_te_t6": "TE Top 6",
        "same_year_te_t12": "TE Top 12",
        "same_year_te_t18": "TE Top 18",
        "same_year_te_t24": "TE Top 24",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def readiness_label(
    *, eligible_rows: int, positive_examples: int, negative_examples: int, seasons: int, sparse_seasons: int
) -> str:
    if eligible_rows < 300 or positive_examples < 10 or negative_examples < 10 or seasons < 5:
        return "RED_INSUFFICIENT_SUPPORT"
    if positive_examples < 25 or negative_examples < 25 or sparse_seasons > 6:
        return "YELLOW_CONSTRAINED_SUPPORT"
    return "GREEN_LOCAL_SHADOW_MODELING_EVALUATION_ONLY"


def main() -> None:
    required_files = [
        SOURCE_DIR / "metadata_sprint_5ck.json",
        SOURCE_DIR / "label_support_by_head_season_position.csv",
        SOURCE_DIR / "blocked_rows_by_target_season_position_reason.csv",
        SOURCE_DIR / "accepted_excluded_blocker_contract.csv",
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing 5CK-R2 inputs:\n" + "\n".join(missing))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_metadata = json.loads((SOURCE_DIR / "metadata_sprint_5ck.json").read_text(encoding="utf-8"))
    support_rows = read_csv(SOURCE_DIR / "label_support_by_head_season_position.csv")
    blocked_rows = read_csv(SOURCE_DIR / "blocked_rows_by_target_season_position_reason.csv")
    accepted_blockers = read_csv(SOURCE_DIR / "accepted_excluded_blocker_contract.csv")

    blocked_by_position = Counter()
    for row in blocked_rows:
        blocked_by_position[row["position"]] += int(row["blocked_rows"])

    support_by_head: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in support_rows:
        key = (row["position"], row["outcome"])
        support_by_head[key].append(row)

    evaluation_rows: list[dict[str, object]] = []
    for position, heads in HEAD_LABELS.items():
        for canonical_head, display_head in heads.items():
            rows = support_by_head[(position, canonical_head)]
            eligible_rows = sum(int(row["row_count"]) for row in rows)
            positive_examples = sum(int(row["event_count"]) for row in rows)
            negative_examples = sum(int(row["non_event_count"]) for row in rows)
            seasons = len({row["target_season"] for row in rows})
            sparse_seasons = sum(1 for row in rows if row["sparse_flag"] == "yes")
            one_class_seasons = sum(1 for row in rows if row["one_class_flag"] == "yes")
            blocked = blocked_by_position[position]
            status = readiness_label(
                eligible_rows=eligible_rows,
                positive_examples=positive_examples,
                negative_examples=negative_examples,
                seasons=seasons,
                sparse_seasons=sparse_seasons,
            )
            if status.startswith("GREEN"):
                future_treatment = "viable_for_future_local_shadow_modeling_evaluation_only"
            elif status.startswith("YELLOW"):
                future_treatment = "constrained_requires_hq_limits_before_shadow_modeling"
            else:
                future_treatment = "blocked_from_future_local_shadow_modeling"
            evaluation_rows.append(
                {
                    "output_scope": "internal_only_not_app_readable",
                    "position": position,
                    "display_head": display_head,
                    "canonical_head": canonical_head,
                    "eligible_rows": eligible_rows,
                    "positive_examples": positive_examples,
                    "negative_examples": negative_examples,
                    "blocked_rows_position_scope": blocked,
                    "seasons_represented": seasons,
                    "positions_represented": 1,
                    "sparse_seasons": sparse_seasons,
                    "one_class_seasons": one_class_seasons,
                    "support_result": status,
                    "future_treatment": future_treatment,
                    "notes": "Counts only. No percentages, probabilities, model training, scoring, app output, ranking, sorting, hidden key, or promoted artifact.",
                }
            )

    result_counts = Counter(row["support_result"] for row in evaluation_rows)
    viable_heads = [
        row["canonical_head"]
        for row in evaluation_rows
        if row["future_treatment"] == "viable_for_future_local_shadow_modeling_evaluation_only"
    ]
    constrained_heads = [
        row["canonical_head"]
        for row in evaluation_rows
        if row["future_treatment"] == "constrained_requires_hq_limits_before_shadow_modeling"
    ]
    blocked_heads = [
        row["canonical_head"]
        for row in evaluation_rows
        if row["future_treatment"] == "blocked_from_future_local_shadow_modeling"
    ]

    write_csv(
        OUT_DIR / "threshold_head_support_evaluation.csv",
        evaluation_rows,
        [
            "output_scope",
            "position",
            "display_head",
            "canonical_head",
            "eligible_rows",
            "positive_examples",
            "negative_examples",
            "blocked_rows_position_scope",
            "seasons_represented",
            "positions_represented",
            "sparse_seasons",
            "one_class_seasons",
            "support_result",
            "future_treatment",
            "notes",
        ],
    )
    metadata = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_run_id": source_metadata.get("run_id"),
        "source_audit_verdict": source_metadata.get("audit_verdict"),
        "output_scope": "internal_only_not_app_readable",
        "audit_verdict": "GREEN",
        "candidate_heads_evaluated": len(evaluation_rows),
        "support_result_counts": dict(result_counts),
        "viable_future_local_shadow_modeling_evaluation_only": viable_heads,
        "constrained_requires_hq_limits": constrained_heads,
        "blocked_from_future_local_shadow_modeling": blocked_heads,
        "accepted_excluded_blocker_count": len(accepted_blockers),
        "model_training_performed": False,
        "probabilities_created": False,
        "exact_percentages": "blocked",
        "coarse_bands": "blocked",
        "app_wiring": "blocked",
        "rankings_sorting": "blocked",
        "hidden_sort_keys": "blocked",
        "promoted_artifacts": "blocked",
    }
    (OUT_DIR / "metadata_sprint_5cl.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "README_SPRINT_5CL.md").write_text(
        "# Sprint 5CL Threshold-Head Support Evaluation\n\n"
        "Internal-only support counts for candidate future outcome heads. "
        "No model training, probabilities, exact percentages, coarse bands, app outputs, "
        "rankings, hidden sort keys, or promoted artifacts.\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
