from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.model_v4_player_rank_explainer_service import (
    write_player_rank_explainer_outputs,
)


def main() -> None:
    paths = write_player_rank_explainer_outputs()
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
