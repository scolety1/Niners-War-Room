from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InputCheck:
    name: str
    path: Path | None
    required: bool
    note: str
    expected_headers: tuple[str, ...] = ()


REPO_ROOT = Path(__file__).resolve().parents[1]

INPUT_CHECKS = (
    InputCheck(
        name="frozen rookie mock draft input",
        path=Path(
            "local_exports/rookie_framework/final_post_fill_runway_20260616/"
            "rookie_2026_mock_draft_input_20260616.csv"
        ),
        required=True,
        note="Frozen rookie input must be reviewed before any mock draft run.",
        expected_headers=("asset_id", "player", "position"),
    ),
    InputCheck(
        name="dropped or available veteran pool",
        path=None,
        required=True,
        note="Path is not configured yet; lane owner must provide a local snapshot.",
    ),
    InputCheck(
        name="final pick order",
        path=None,
        required=True,
        note="Path is not configured yet; lane owner must provide final pick order.",
    ),
    InputCheck(
        name="current rosters and keepers",
        path=None,
        required=True,
        note="Path is not configured yet; lane owner must provide roster snapshot.",
    ),
    InputCheck(
        name="team needs and opponent tendencies",
        path=None,
        required=True,
        note="Path is not configured yet; ADP/market may not fill this as NWR value.",
    ),
    InputCheck(
        name="ADP/market behavior context",
        path=None,
        required=True,
        note="Path is not configured yet; behavior-only source separation required.",
    ),
)


def main() -> int:
    missing_required = 0
    print("Mock Draft input readiness: REVIEW ONLY")
    print("No files are written. Missing inputs are YELLOW readiness gaps.")

    for check in INPUT_CHECKS:
        if check.path is None:
            missing_required += int(check.required)
            print(f"YELLOW: {check.name}: not configured - {check.note}")
            continue

        full_path = REPO_ROOT / check.path
        if not full_path.exists():
            missing_required += int(check.required)
            print(f"YELLOW: {check.name}: missing - {check.path}")
            continue

        header_status = _csv_header_status(full_path, check.expected_headers)
        print(f"GREEN: {check.name}: present - {check.path}{header_status}")

    if missing_required:
        print(f"SUMMARY: YELLOW - {missing_required} required input(s) missing or unconfigured")
    else:
        print("SUMMARY: GREEN - all configured required inputs are present")
    return 0


def _csv_header_status(path: Path, expected_headers: tuple[str, ...]) -> str:
    if not expected_headers:
        return ""
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            headers = next(reader, [])
    except OSError as exc:
        return f"; header check unavailable: {exc}"

    missing = [header for header in expected_headers if header not in headers]
    if missing:
        return f"; headers missing: {', '.join(missing)}"
    return "; required headers present"


if __name__ == "__main__":
    raise SystemExit(main())
