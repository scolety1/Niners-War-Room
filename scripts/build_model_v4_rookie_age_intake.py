from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rookie_age_intake_service import (  # noqa: E402
    build_rookie_age_rows,
    write_rookie_age_outputs,
)


def main() -> None:
    result = build_rookie_age_rows()
    output_path, doc_path = write_rookie_age_outputs(result=result)
    print(f"rookie_age_rows={len(result.rows)}")
    print(f"rookie_age_warnings={len(result.warning_rows)}")
    print(f"rookie_age_output={output_path}")
    print(f"rookie_age_doc={doc_path}")


if __name__ == "__main__":
    main()
