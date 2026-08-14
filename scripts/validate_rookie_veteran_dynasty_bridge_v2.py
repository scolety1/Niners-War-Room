"""Validate the bridge V2 packet and its fail-closed product invariants."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/hq/model/nwr_rookie_veteran_dynasty_bridge_v2_20260814"
VERDICT = "GREEN_NWR_ROOKIE_VETERAN_COMPARE_MULTI_AUTHORITY_READY"
REQUIRED = {
    "EXECUTIVE_VERDICT.md",
    "PRIOR_BRIDGE_RECOVERY.md",
    "DATA_AUTHORITY.md",
    "HORIZON_COMPLETENESS.csv",
    "VALIDATION_SPEND_LEDGER.md",
    "TARGET_GAUNTLET.csv",
    "MODEL_GAUNTLET.csv",
    "TEMPORAL_VALIDATION.csv",
    "PAIRWISE_RESULTS.csv",
    "POSITION_RESULTS.csv",
    "ONE_YEAR_RESULT.md",
    "THREE_YEAR_RESULT.md",
    "FIVE_YEAR_RESULT.md",
    "CURRENT_COMPARISON_CASES.md",
    "PRODUCT_CONTRACT.md",
    "DESKTOP_INTEGRATION.md",
    "TRADE_INTEGRATION.md",
    "AUTHORITY_PRESERVATION.md",
    "OWNER_ACCEPTANCE.md",
    "OWNER_APPROVAL_ADOPTION.md",
    "NEXT_ACTION.md",
    "MANIFEST.json",
}


def main() -> None:
    present = {path.name for path in PACKET.iterdir() if path.is_file()}
    missing = sorted(REQUIRED - present)
    if missing:
        raise SystemExit(f"Missing packet artifacts: {missing}")
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("verdict") != VERDICT:
        raise SystemExit("Manifest verdict mismatch")
    if manifest.get("common_dynasty_scale_admitted") is not False:
        raise SystemExit("Common dynasty scale must remain unadmitted")
    approval = manifest.get("owner_approval", {})
    if approval.get("local_multi_authority_adoption") is not True:
        raise SystemExit("Local multi-authority owner approval is not recorded")
    if approval.get("common_dynasty_scale_authorized") is not False:
        raise SystemExit("Owner approval must not authorize a common dynasty scale")
    acceptance = (PACKET / "OWNER_ACCEPTANCE.md").read_text(encoding="utf-8")
    if "directly comparable?** **NO.**" not in acceptance:
        raise SystemExit("Owner score-comparability answer is not NO")
    source = (ROOT / "src/services/rookie_veteran_dynasty_bridge_service.py").read_text(
        encoding="utf-8"
    )
    for badge in ("PRODUCTION", "REVIEW", "RESEARCH ONLY", "INSUFFICIENT EVIDENCE"):
        if badge not in source:
            raise SystemExit(f"Missing authority badge: {badge}")
    print(f"{VERDICT}: packet and fail-closed invariants verified")


if __name__ == "__main__":
    main()
