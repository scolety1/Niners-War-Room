# Project Gold Sprint 3 / Phase 16: Forced-Release Decision Deep Audit

Date: 2026-05-14

## Result

The Niners forced-release decision is now presented as a top-five-only decision in the primary My Team view.

The default forced-release candidate is still Luther Burden, and the audit confirms he is chosen from the Niners league-rank top five only. Secondary roster-cut context remains available in Advanced, but it no longer appears in the primary top-five release explanation.

## Niners League-Rank Top Five

| player | position | league_rank | lifecycle | model_value | keep_priority | cut_risk | confidence | top_five_rule |
|---|---:|---:|---|---:|---:|---:|---:|---|
| De'Von Achane | RB | 10 | Year-Three NFL Bridge | 66.14 | 62.94 | 33.00 | 66.50 | Top-five protected slot |
| Lamar Jackson | QB | 31 | Established Veteran | 54.68 | 41.09 | 46.84 | 68.50 | Top-five protected slot |
| Chase Brown | RB | 35 | Year-Three NFL Bridge | 54.38 | 52.46 | 42.03 | 66.50 | Top-five protected slot |
| Luther Burden | WR | 56 | Year-One NFL Bridge | 49.48 | 37.79 | 55.46 | 36.00 | Required top-five release slot |
| Brian Thomas | WR | 66 | Year-Two NFL Bridge | 75.81 | 72.49 | 22.97 | 66.50 | Top-five protected slot |

## Forced-Release Logic

The default release is selected by sorting only the league-rank top-five group by lowest Keep Priority, then Cut Risk as a tiebreaker.

Current default explanation:

> Luther Burden is the current required top-five release because he has the lowest Keep Priority (37.79) inside the league-rank top five. League rank: 56. Cut Risk: 55.46. Release Pain: 20.48. Next closest protected top-five option: Lamar Jackson at 41.09 Keep Priority (3.30 higher). Secondary roster-cut context is available only in Advanced.

## Patch

Changed the primary forced-release explanation path in `src/services/command_board_service.py` so:

- the visible My Team forced-release row explains only the top-five comparison;
- non-top-five/easy-cut context is demoted to Advanced strategy audit;
- the explanation names the next closest protected top-five option and the Keep Priority gap;
- Release Pain remains visible without implying non-top-five drops choose the forced-release player.

## Audit Artifacts

- `local_exports/model_audits/sprint3_phase16_forced_release_deep_audit_20260514/niners_top_five_release_audit.csv`
- `local_exports/model_audits/sprint3_phase16_forced_release_deep_audit_20260514/pre_decision_checklist_summary.csv`
- `local_exports/model_audits/sprint3_phase16_forced_release_deep_audit_20260514/pre_decision_checklist_rows.csv`
- `local_exports/model_audits/sprint3_phase16_forced_release_deep_audit_20260514/manifest.json`
- `local_exports/model_audits/sprint3_phase16_model_audit_packet_20260514/manifest.json`

## Readiness

- Roster Decisions: Roster Decisions Ready
- Draft: Draft Pool Needs Data
- Final Money Decisions: Needs Data

This phase does not change formulas or unlock draft/final decision readiness.
