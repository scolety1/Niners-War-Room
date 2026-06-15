from __future__ import annotations

import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATHS = (
    REPO_ROOT / "src/services/nwr_outcome_phase8_status_contract_service.py",
)

APPROVED_STATUSES = {
    "internal_review_passed",
    "under_review",
    "unavailable",
}

ELIGIBLE_HEADS = {
    "qb_t12",
    "rb_t12",
    "wr_t12",
    "wr_t24",
    "wr_t36",
    "te_t12",
}

RED_PATTERNS = (
    "%",
    "outcome_prob",
    "outcome_pct",
    "outcome_band",
    "outcome_score",
    "outcome_rank",
    "outcome_sort",
    "status_priority",
    "hidden_outcome",
    "current_player",
    "model_artifact",
    "local_exports",
    "read_csv",
    "glob(",
)

BAND_WORDS = (
    "green",
    "yellow",
    "red",
    "high",
    "medium",
    "low",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    paths = [Path(path) for path in args.paths] if args.paths else list(DEFAULT_PATHS)
    issues: list[str] = []

    for raw_path in paths:
        path = raw_path if raw_path.is_absolute() else REPO_ROOT / raw_path
        if not path.exists():
            issues.append(f"YELLOW missing path: {path}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        for pattern in RED_PATTERNS:
            if pattern in text:
                issues.append(f"RED forbidden pattern {pattern!r} in {path.relative_to(REPO_ROOT)}")
        for word in BAND_WORDS:
            if f" {word}" in text or f"_{word}" in text:
                issues.append(f"RED coarse word {word!r} in {path.relative_to(REPO_ROOT)}")

    if issues:
        for issue in issues:
            print(issue)
        if any(issue.startswith("RED") for issue in issues):
            print("VERDICT=RED")
            return 1
        print("VERDICT=YELLOW")
        return 2

    print("VERDICT=GREEN")
    print(f"approved_statuses={','.join(sorted(APPROVED_STATUSES))}")
    print(f"eligible_heads={','.join(sorted(ELIGIBLE_HEADS))}")
    print("outputs_written=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
