from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


FIXTURE_ROOT = Path("tests/fixtures/mock_draft_inputs")


def main() -> int:
    from src.services.mock_draft_input_contract import (
        default_real_input_paths,
        fixture_input_paths,
        validate_input_contract,
    )
    from src.services.mock_draft_readiness_report import render_readiness_report
    from src.services.mock_draft_readiness_service import build_mock_draft_readiness_report

    print("Mock Draft input readiness: REVIEW ONLY")
    print("No simulations run. No files are written.")
    print("ADP/market is opponent behavior, availability, and pick timing only.")
    print("ADP/market is never NWR private quality or value.")

    aggregate = build_mock_draft_readiness_report(repo_root=REPO_ROOT)
    print("\n" + render_readiness_report(aggregate))

    real_report = validate_input_contract(
        default_real_input_paths(),
        mode="real",
        repo_root=REPO_ROOT,
    )
    _print_report("Real input readiness", real_report)

    fixture_root = REPO_ROOT / FIXTURE_ROOT
    if fixture_root.exists():
        fixture_report = validate_input_contract(
            fixture_input_paths(FIXTURE_ROOT),
            mode="fixture",
            repo_root=REPO_ROOT,
        )
        _print_report("Fixture contract readiness", fixture_report)
        if fixture_report.readiness == "RED":
            return 1
    else:
        print(f"YELLOW: Fixture contract readiness: missing {FIXTURE_ROOT}")

    return 0


def _print_report(title: str, report: object) -> None:
    print(f"\n=== {title}: {report.readiness} ===")
    print(f"Policy: {report.market_policy}")
    for row in report.rows:
        details = []
        if row.path:
            details.append(f"path={row.path}")
        details.append(f"rows={row.row_count}")
        if row.missing_columns:
            details.append(f"missing={','.join(row.missing_columns)}")
        if row.blocked_columns:
            details.append(f"blocked={','.join(row.blocked_columns)}")
        if row.warnings:
            details.append(f"warnings={' | '.join(row.warnings)}")
        if row.errors:
            details.append(f"errors={' | '.join(row.errors)}")
        print(f"{row.readiness}: {row.label} ({'; '.join(details)})")


if __name__ == "__main__":
    raise SystemExit(main())
