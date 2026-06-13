from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    from src.services.nwr_outcome_constrained_ordinal_prototype_service import (
        export_sprint_5bf_internal_prototype,
    )

    result = export_sprint_5bf_internal_prototype(repo_root=REPO_ROOT)
    print(json.dumps(result["metadata"], indent=2))


if __name__ == "__main__":
    main()
