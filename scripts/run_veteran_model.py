from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.services.veteran_model_service import (
        run_veteran_model_from_dir,
        write_generated_model_outputs,
    )

    parser = argparse.ArgumentParser(
        description="Run the local-first LVE veteran model from source CSVs."
    )
    parser.add_argument(
        "--data-dir",
        default="sample_data/veteran_model_v1",
        help="Directory containing veteran source CSVs.",
    )
    parser.add_argument(
        "--output",
        default="local_exports/veterans/veteran_model_outputs.csv",
        help="Generated veteran model output CSV path.",
    )
    parser.add_argument(
        "--snapshot-date",
        default="2026-05-05",
        help="Snapshot date to write into generated model outputs.",
    )
    args = parser.parse_args()

    run = run_veteran_model_from_dir(args.data_dir)
    output_path = Path(args.output)
    write_generated_model_outputs(
        output_path,
        run.scores,
        snapshot_date=args.snapshot_date,
        computed_at=datetime.now(UTC).isoformat(),
    )

    print(f"Ran {run.model_version} for {len(run.scores)} veterans.")
    print(f"Generated output: {output_path}")
    if run.scores:
        top = run.scores[0]
        print(
            "Top veteran: "
            f"{top.player_name} ({top.position.value}) "
            f"keeper={top.keeper_score:.1f}, drop={top.drop_candidate_score:.1f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
