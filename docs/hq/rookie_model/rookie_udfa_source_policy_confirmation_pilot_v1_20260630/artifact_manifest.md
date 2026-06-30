# Artifact Manifest

All artifacts in this packet are review-only. They do not edit source truth, do not patch the original entry-status artifact, and do not approve training or model use.

## Input Artifacts Used

- `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/undrafted_candidate_audit.csv`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/identity_collision_report.csv`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_qa_v1_20260630/entry_status_packet_qa_summary.md`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_qa_v1_20260630/likely_udfa_evidence_distribution.csv`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_qa_v1_20260630/collision_overlap_audit.csv`
- `docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/` if available; present in this base.

## Source Policy Status

- `confirmed_udfa=0` in the source entry-status artifact.
- `likely_udfa_needs_review=2514` remains blocked.
- Draft absence, NFL appearance, player_stats, and Outcome V2 labels cannot confirm UDFA status.
- Gmail, vendor, private, proxy, RotoWire, FantasyPros, and scraped FootballDB evidence are blocked.

## Blocked Populations

- All likely UDFA candidates remain review-only.
- No row is model-use-approved.
- No row is training-approved.
- Drafted-only Outcome review remains separate from this UDFA policy pilot.

## Output Artifacts Created

| Artifact | Type | Row Count | Purpose | Review-Only |
|---|---|---:|---|---|
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/artifact_manifest.md` | markdown | n/a | Manifest of review-only inputs, outputs, blocked populations, and approval limits. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/udfa_confirmation_policy_v1.md` | markdown | n/a | Conservative source policy for confirmed_udfa. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/udfa_source_inventory.csv` | csv | 10 | Inventory of available, blocked, and pending source types. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/likely_udfa_confirmation_candidate_audit.csv` | csv | 2514 | One-row-per-likely-UDFA source-policy audit. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/confirmed_udfa_patch_proposal.csv` | csv | 0 | Review-only patch proposal; zero rows if no candidate qualifies. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/blocked_udfa_review_queue.csv` | csv | 2514 | Rows that cannot be promoted and why. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/udfa_confirmation_coverage_by_class.csv` | csv | 100 | Class/position promotion coverage summary. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/collision_risk_udfa_blockers.csv` | csv | 2514 | Likely UDFA candidates with collision or identity risk. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/rookie_outcome_udfa_handoff_update.md` | markdown | n/a | Outcome handoff limits after this lane. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/final_udfa_policy_pilot_recommendation.md` | markdown | n/a | Final verdict and next branch recommendation. | yes |
| `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/merge_safety_report.md` | markdown | n/a | Guardrail and command evidence report. | yes |

## What This Packet Does Not Approve

- No automatic conversion from `likely_udfa_needs_review` to `confirmed_udfa`.
- No training, tuning, probabilities, app wiring, Gate F release, Gate G release, or Rankings wiring.
- No fake round 8, draft round 0, draft pick 0, or missing-as-zero logic.
