from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.roster_decision_readiness_service import (  # noqa: E402
    build_roster_decision_readiness,
    roster_decision_gate_rows,
    roster_decision_summary_row,
)
from src.services.truth_set_v3_2_promotion_service import (  # noqa: E402
    build_truth_set_v3_2_safe_promotion,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a review-only Truth Set Lab v3.2 promoted model root."
    )
    parser.add_argument(
        "--data-pack",
        default="local_exports/data_packs/lve_sleeper_20260505_pdf_ranks",
        help="Data pack used to re-run the roster decision gate.",
    )
    parser.add_argument("--v3-preview-path", default=None)
    parser.add_argument("--promotion-id", default=None)
    args = parser.parse_args()

    result = build_truth_set_v3_2_safe_promotion(
        v3_preview_path=args.v3_preview_path,
        promotion_id=args.promotion_id,
    )
    readiness = build_roster_decision_readiness(
        args.data_pack,
        veteran_model_dir=result.output_path,
    )
    _write_gate_outputs(result.output_path, readiness)
    print(f"v3.2 promotion root: {result.output_path}")
    print(f"promotion report: {result.report_path}")
    print(f"roster readiness: {readiness.badge} ({readiness.status})")


def _write_gate_outputs(output_path: Path, readiness: object) -> None:
    summary_path = output_path / "truth_set_v3_2_roster_gate_summary.csv"
    rows_path = output_path / "truth_set_v3_2_roster_gate_rows.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        row = roster_decision_summary_row(readiness)
        writer = csv.DictWriter(handle, fieldnames=tuple(row.keys()))
        writer.writeheader()
        writer.writerow(row)
    rows = roster_decision_gate_rows(readiness)
    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
