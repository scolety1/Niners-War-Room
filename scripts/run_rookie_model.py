from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.services.rookie_model_service import (
        run_rookie_model_from_dir,
        write_generated_model_outputs,
    )

    parser = argparse.ArgumentParser(
        description="Run the local-first LVE rookie model from committed source CSVs."
    )
    parser.add_argument(
        "--data-dir",
        default="sample_data/rookie_model_v1",
        help="Directory containing rookie source CSVs.",
    )
    parser.add_argument(
        "--output",
        default="local_exports/rookies/rookie_model_outputs.csv",
        help="Generated model output CSV path.",
    )
    args = parser.parse_args()

    run = run_rookie_model_from_dir(args.data_dir)
    output_path = Path(args.output)
    write_generated_model_outputs(output_path, run.scores)

    print(f"Ran {run.model_version} for {len(run.scores)} rookies.")
    print(f"Generated output: {output_path}")
    if run.scores:
        top = run.scores[0]
        print(
            "Top rookie: "
            f"{top.player_name} ({top.position.value}) "
            f"{top.final_decision_score:.1f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
