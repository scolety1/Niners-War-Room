# Project Gold Sprint 3 / Phase 17: Receipt Trust Pass

Date: 2026-05-14

## Result

My Team receipts now show compact first-view explanations for every Niners roster player.

Each receipt includes:

- lifecycle explanation;
- top positive private/stat drivers;
- top negative private/stat drivers;
- young-player bridge contribution when applicable;
- confidence explanation;
- source warnings;
- Model vs Market status without treating missing market data as real edge.

Raw feature rows remain under Advanced roster feature receipts.

## Patch

Updated `src/services/my_team_decision_receipts_service.py` so compact receipts separate positive and negative score drivers instead of mixing them by absolute contribution. Missing/default market data now reads as unavailable instead of showing a misleading market-liquidity contribution.

Updated `app/pages/02_team.py` so the first-view Why? expanders show the compact receipt fields directly.

## Coverage

Added tests proving:

- forced-release receipts keep top-five rule and model recommendation separate;
- compact receipts show positive and negative drivers;
- missing market data does not create fake Model vs Market edge;
- all 24 active Niners roster players have compact receipt rows.

## Audit Artifacts

- `local_exports/model_audits/sprint3_phase17_receipt_trust_pass_20260514/niners_compact_receipts.csv`
- `local_exports/model_audits/sprint3_phase17_receipt_trust_pass_20260514/pre_decision_checklist_summary.csv`
- `local_exports/model_audits/sprint3_phase17_receipt_trust_pass_20260514/manifest.json`

## Readiness

- Roster Decisions: Roster Decisions Ready
- Draft: Draft Pool Needs Data
- Final Money Decisions: Needs Data

This phase does not change player scores.
