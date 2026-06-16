"""Run Sprint 5DA Phase 6 local-only production-candidate modeling.

Default execution uses the committed 5CZ harness, the six 5CY-approved heads,
and the quarantined 5DA local export path.
"""

from __future__ import annotations

import sys

from build_sprint_5cz_phase6_production_candidate_harness import main


DEFAULT_ARGS = [
    "--mode",
    "evaluate",
    "--heads",
    "approved",
    "--output-dir",
    "local_exports/outcome_probability/sprint_5da_phase6_local_only_production_candidate_modeling",
]


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.extend(DEFAULT_ARGS)
    main()
