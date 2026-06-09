from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.services.rookie_normalization_service import (
        normalize_rookie_raw_metrics,
        write_normalized_rookie_inputs,
    )

    parser = argparse.ArgumentParser(
        description="Generate normalized rookie prospect inputs from local raw metrics."
    )
    parser.add_argument(
        "--raw-metrics",
        default="sample_data/rookie_model_v1/rookie_raw_metrics.csv",
        help="CSV containing raw rookie metrics.",
    )
    parser.add_argument(
        "--rules",
        default="sample_data/rookie_model_v1/rookie_normalization_rules.csv",
        help="CSV containing deterministic normalization rules.",
    )
    parser.add_argument(
        "--output",
        default="local_exports/rookies/normalized_rookie_prospect_inputs.csv",
        help="Generated normalized rookie prospect CSV.",
    )
    args = parser.parse_args()

    result = normalize_rookie_raw_metrics(args.raw_metrics, args.rules)
    write_normalized_rookie_inputs(args.output, result.rows)
    print(f"Normalized {len(result.rows)} rookies.")
    print(f"Generated output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
