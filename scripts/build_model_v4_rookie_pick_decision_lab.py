from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.model_v4_rookie_pick_decision_lab_service import (
    write_rookie_pick_decision_lab_outputs,
)


def main() -> None:
    paths = write_rookie_pick_decision_lab_outputs()
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
