# Overlay Source Trace

## Direct Inputs

- Overlay Candidate Batch Rule Test V1: `docs/hq/model/overlay_candidate_batch_rule_test_v1_20260709/`
- Prior overlay batch commit: `4b5f9c68970b0487ccf147be920b1051be4455fb`
- Miss-Specific Overlay Library / Candidate Discovery V1: `docs/hq/model/miss_specific_overlay_library_candidate_discovery_v1_20260709/`
- Prior overlay-library commit: `d9ec52781d682b7bee116b7896fef678b9df1552`
- Manual Review Evidence Sort / Decision Packet V1: `docs/hq/master/manual_review_evidence_sort_decision_packet_v1_20260709/`

## Local Source Packet Verification

Some accepted sparse-history source packets remain local-only in their source worktrees. These paths were verified and used as source context:

- `C:\NWR\Niners-War-Room-sparse-history-overlay-candidate-preservation-v1-20260709\docs\hq\model\sparse_history_overlay_candidate_preservation_v1_20260709`
- `C:\NWR\Niners-War-Room-sparse-history-refined-rule-review-readiness-gate-v1-20260709\docs\hq\model\sparse_history_refined_rule_review_readiness_gate_v1_20260709`

## Remote

- Canonical remote HQ: `origin/work/hq-parallel-control`
- Verified remote HQ head: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`

## Source / Use Gate

This packet is docs/review closeout only. Production/model-use, rankings integration, app/runtime changes, source promotion, push/merge, canonical `local_exports`, hidden sort, recommendation logic, overlay stacking, and ranking simulation remain blocked.

Leakage/as-of: this packet did not run new tests or introduce new data. It preserves accepted review-only, lag-safe decisions from prior packets.
