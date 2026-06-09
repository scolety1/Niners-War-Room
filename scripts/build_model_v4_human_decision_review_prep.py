from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_human_decision_review_prep_service import (  # noqa: E402
    build_human_decision_review_prep,
    write_human_decision_review_prep,
)


def main() -> None:
    result = build_human_decision_review_prep()
    paths = write_human_decision_review_prep(result=result)
    print(f"review_status={result.summary['review_status']}")
    print(f"pick_review_cards={result.summary['pick_review_cards']}")
    print(f"roster_pressure_review_cards={result.summary['roster_pressure_review_cards']}")
    print(f"trade_review_cards={result.summary['trade_review_cards']}")
    print(f"rookie_manual_scout_queue_rows={result.summary['rookie_manual_scout_queue_rows']}")
    print(f"veteran_risk_review_cards={result.summary['veteran_risk_review_cards']}")
    print(f"summary_path={paths.summary}")
    print(f"doc_path={paths.doc}")


if __name__ == "__main__":
    main()
