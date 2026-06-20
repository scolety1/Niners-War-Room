# ruff: noqa: E402,I001

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.outcome_lane_exchange import run_readiness_cli


if __name__ == "__main__":
    raise SystemExit(run_readiness_cli())
