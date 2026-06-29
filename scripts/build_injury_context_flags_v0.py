from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.injury_context_flags_service import (  # noqa: E402
    write_injury_context_flags_v0_artifacts,
)


def main() -> int:
    result = write_injury_context_flags_v0_artifacts()
    print("Injury Context Flags V0 built")
    print(f"flags_path={result.flags_path}")
    print(f"manifest_path={result.manifest_path}")
    print(f"coverage_path={result.coverage_path}")
    print(f"enhanced_artifact_path={result.enhanced_artifact_path}")
    print(f"flag_rows={result.flag_rows}")
    print(f"enhanced_rows={result.enhanced_rows}")
    print(f"prior_season_context_rows={result.prior_season_context_rows}")
    print(f"missing_feature_rows={result.missing_feature_rows}")
    print(f"rookie_out_of_scope_rows={result.rookie_out_of_scope_rows}")
    print(f"enhanced_artifact_sha256={result.sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
