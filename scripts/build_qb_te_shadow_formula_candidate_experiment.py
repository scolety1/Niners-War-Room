from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.qb_te_shadow_formula_candidate_service import (  # noqa: E402
    build_qb_te_shadow_formula_candidate_experiment,
    write_qb_te_shadow_formula_candidate_experiment,
)


def main() -> int:
    result = build_qb_te_shadow_formula_candidate_experiment()
    paths = write_qb_te_shadow_formula_candidate_experiment(result=result)
    print(f"output_root: {paths.output_root}")
    print(f"manifest: {paths.manifest}")
    print(f"diagnosis_report: {paths.diagnosis_report}")
    print(f"plan_report: {paths.plan_report}")
    print(f"results_report: {paths.results_report}")
    print(f"handoff_report: {paths.handoff_report}")
    print(f"baseline_rows: {result.summary['baseline_rows']}")
    print(f"baseline_scored_rows: {result.summary['baseline_scored_rows']}")
    print(f"baseline_k_rows: {result.summary['baseline_k_rows']}")
    print(f"baseline_hashes_match: {result.summary['baseline_hashes_match']}")
    print(f"sentinels_safe: {result.summary['sentinels_safe']}")
    print(f"contamination_safe: {result.summary['contamination_safe']}")
    for variant in result.variants:
        print(
            f"variant: {variant.variant_id} "
            f"top10_qbs={variant.summary['top_10_qb_count']} "
            f"top25_qbs={variant.summary['top_25_qb_count']} "
            f"top25_tes={variant.summary['top_25_te_count']} "
            f"trey_rank={variant.summary['trey_mcbride_shadow_rank']} "
            f"bowers_rank={variant.summary['brock_bowers_shadow_rank']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
