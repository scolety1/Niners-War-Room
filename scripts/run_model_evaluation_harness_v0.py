from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.model_evaluation_harness_service import (  # noqa: E402
    run_model_evaluation_harness,
    validate_evaluation_outputs,
)


def main() -> int:
    paths = run_model_evaluation_harness()
    issues = validate_evaluation_outputs(paths["summary"].parent)
    for label, path in paths.items():
        print(f"{label}: {path}")
    if issues:
        print("Validation issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Model evaluation harness V0 outputs validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
