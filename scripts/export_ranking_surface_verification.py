from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.ranking_surface_audit_service import (
    build_ranking_surface_audit,
    write_ranking_surface_audit,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export ranking-surface verification CSVs."
    )
    parser.add_argument(
        "--data-pack",
        default="local_exports/data_packs/lve_sleeper_20260505_pdf_ranks",
        help="Active data pack path.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Destination folder. Defaults to timestamped local_exports/model_audits.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    report = build_ranking_surface_audit(args.data_pack)
    paths = write_ranking_surface_audit(output_dir, report)
    print(f"ranking_surface_audit_dir={output_dir}")
    for name, path in paths.items():
        print(f"{name}={path}")


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("local_exports") / "model_audits" / f"ranking_surface_verification_{stamp}"


if __name__ == "__main__":
    main()
