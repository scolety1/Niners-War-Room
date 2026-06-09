from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.model_v4_rookie_outcome_label_service import (
    write_rookie_outcome_label_outputs,
)


def main() -> None:
    paths = write_rookie_outcome_label_outputs()
    print(f"wrote={paths['labels'].parent}")
    print(f"labels={paths['labels']}")
    print(f"summary={paths['summary']}")


if __name__ == "__main__":
    main()
