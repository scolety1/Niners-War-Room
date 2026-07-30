"""Build the governed review-only Model V4 2026 rookie board."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_2026_rookie_board_review_service import (  # noqa: E402
    execute_review_build,
    run_required_mutations,
)


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo)
    parser.add_argument(
        "--config",
        type=Path,
        default=repo / "config" / "model_v4_2026_compatible_input_pack_v1.json",
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--run-mutations", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = execute_review_build(
        repo_root=args.repo_root,
        config_path=args.config,
        run_root=args.run_root,
    )
    summary: dict[str, object] = {
        "board_path": str(result.board_path),
        "board_rows": len(result.board_rows),
        "exact_rows": sum(bool(row["player_id"]) for row in result.board_rows),
        "blocked_rows": sum(not bool(row["player_id"]) for row in result.board_rows),
        "scored_rows": sum(row["final_review_score"] != "" for row in result.board_rows),
        "governed_digest": result.governed_digest,
    }
    if args.run_mutations:
        mutations = run_required_mutations(result)
        mutation_path = result.run_root / "MUTATION_SENSITIVITY_RESULTS.csv"
        with mutation_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=tuple(mutations[0]))
            writer.writeheader()
            writer.writerows(mutations)
        summary["mutations"] = len(mutations)
        summary["mutation_path"] = str(mutation_path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
