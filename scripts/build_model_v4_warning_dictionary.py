from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.model_v4_warning_dictionary_service import (  # noqa: E402
    write_warning_dictionary_outputs,
)


def main() -> None:
    paths = write_warning_dictionary_outputs()
    for key, path in paths.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
