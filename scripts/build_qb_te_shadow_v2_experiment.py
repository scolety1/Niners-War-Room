from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.qb_te_shadow_v2_candidate_service import (  # noqa: E402
    build_qb_te_shadow_v2_experiment,
    write_qb_te_shadow_v2_experiment,
)


def main() -> int:
    result = build_qb_te_shadow_v2_experiment()
    paths = write_qb_te_shadow_v2_experiment(result=result)
    print(f"output_root: {paths.output_root}")
    print(f"manifest: {paths.manifest}")
    print(f"te_diagnosis: {paths.te_diagnosis}")
    print(f"plan_report: {paths.plan_report}")
    print(f"results_report: {paths.results_report}")
    print(f"production_proposal: {paths.production_proposal}")
    print(f"no_promotion_note: {paths.no_promotion_note}")
    print(f"active_hash_before: {result.active_hash_before}")
    print(f"active_hash_after: {result.active_hash_after}")
    print(f"active_output_changed: {result.summary['active_output_changed']}")
    print(f"selected_variant: {result.selected_variant or 'none'}")
    print(f"v2_improved_on_v1: {result.summary['v2_improved_on_v1']}")
    print(f"sentinels_safe: {result.summary['sentinels_safe']}")
    print(f"contamination_safe: {result.summary['contamination_safe']}")
    print(f"decision_board_blocked: {result.summary['decision_board_blocked']}")
    for variant in result.variants:
        print(
            f"variant: {variant.variant_id} "
            f"classification={variant.summary['classification']} "
            f"top25={variant.summary['top25_position_counts']} "
            f"top_te={variant.summary['top_te_player']}#{variant.summary['top_te_rank']} "
            f"bowers_rank={variant.summary['brock_bowers_rank']} "
            f"te_gate={variant.summary['te_exception_pass_count']}/"
            f"{variant.summary['te_exception_block_count']} "
            f"rbwr_delta={variant.summary['rb_wr_max_score_delta']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
