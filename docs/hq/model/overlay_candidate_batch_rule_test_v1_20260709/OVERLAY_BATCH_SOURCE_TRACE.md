# Overlay Batch Source Trace

## Direct Inputs

- Miss-Specific Overlay Library / Candidate Discovery V1: `docs/hq/model/miss_specific_overlay_library_candidate_discovery_v1_20260709/`
- Prior overlay-library commit: `d9ec52781d682b7bee116b7896fef678b9df1552`
- Manual Review Evidence Sort / Decision Packet V1: `docs/hq/master/manual_review_evidence_sort_decision_packet_v1_20260709/`
- Manual-review commit: `5774ebdaa82cfd13c0e92e6afe4e62d1e0e70e99`
- Formula Miss Taxonomy / Red Team Review V1 script: `C:\NWR\Niners-War-Room-formula-miss-taxonomy-red-team-review-v1-20260709\docs\hq\model\formula_miss_taxonomy_red_team_review_v1_20260709\build_formula_miss_taxonomy_red_team_review_v1.py`

## Local Source Packet Verification

The following accepted local-only source packet paths were verified during validation because not all prior packets are present in this branch tree:

- `C:\NWR\Niners-War-Room-sparse-history-overlay-candidate-preservation-v1-20260709\docs\hq\model\sparse_history_overlay_candidate_preservation_v1_20260709`
- `C:\NWR\Niners-War-Room-sparse-history-refined-rule-review-readiness-gate-v1-20260709\docs\hq\model\sparse_history_refined_rule_review_readiness_gate_v1_20260709`
- `C:\NWR\Niners-War-Room-sparse-history-rule-refinement-execution-v1-20260709\docs\hq\model\sparse_history_rule_refinement_execution_v1_20260709`
- `C:\NWR\Niners-War-Room-formula-miss-taxonomy-red-team-review-v1-20260709\docs\hq\model\formula_miss_taxonomy_red_team_review_v1_20260709`
- `C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\master\ingredient_upgrade_phase_batch_canonicalization_merge_review_v1_20260709`

## Remote

- Canonical remote HQ: `origin/work/hq-parallel-control`
- Verified remote HQ head: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`

## Source / Use Gate

Review-only overlay batch test only. Production/model-use, rankings integration, app/runtime changes, source promotion, push/merge, canonical `local_exports`, hidden sort, recommendation logic, and ranking simulation remain blocked.

Leakage/as-of: all tested signals are lagged review-only or static post-entry context. Same-season/future context, current-only ADP, SportsDataIO, paid/API sources, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
