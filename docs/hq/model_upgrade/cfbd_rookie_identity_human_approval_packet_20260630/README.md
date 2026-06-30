# CFBD Rookie Identity Human Approval Packet V1

Date: 2026-06-30

Verdict: `GREEN_REVIEW_ONLY_PACKET_BUILT`

This packet prepares CFBD rookie/prospect identity links for human review. It does not approve CFBD for model input, training use, ranking evidence, source truth, rookie probabilities, player values, or app/runtime behavior.

## Source Inputs

- `docs/hq/model_upgrade/manual_review_intake_20260630/source_gate_needed_matrix.csv`
- `docs/hq/model_upgrade/manual_review_intake_20260630/blocked_do_not_use_matrix.csv`
- `docs/hq/rookie_outcomes/rookie_outcome_columns_gated_20260629/cfbd_rookie_identity_human_approval_packet.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_high_confidence_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_possible_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_match_summary.csv`

## Packet Files

- `candidate_identity_review_v1.csv`: 213 candidate identity rows for human review.
- `blocked_needs_more_info_v1.csv`: 56 rows that should remain blocked or need more information.
- `approval_template_v1.csv`: human fill-in template with conservative defaults.
- `SOURCE_POLICY_NOTES.md`: source-use policy and blocked-use reminders.
- `REVIEWER_INSTRUCTIONS.md`: reviewer workflow and decision rules.
- `GUARDRAIL_PROOF.md`: proof of lane scope and protected artifact safety.

## Row Counts By Recommended Decision

| Decision | Rows |
| --- | ---: |
| APPROVE_REVIEW_ONLY | 157 |
| KEEP_BLOCKED | 10 |
| NEEDS_MORE_INFO | 10 |
| REJECT_WRONG_PLAYER | 36 |

## Top Ambiguity Types

| Ambiguity Type | Rows |
| --- | ---: |
| exact_name_position_school_candidate | 157 |
| position_mismatch | 36 |
| multiple_plausible_candidate_identities | 10 |
| possible_candidate_requires_review | 8 |
| missing_position_context | 2 |

## CFBD Matching Summary From Source Packet

| Metric | Value |
| --- | ---: |
| Source rows | 31822 |
| Candidate rows | 31827 |
| Exact-match count | 157 |
| Possible-candidate count | 46 |
| Ambiguous count | 5 |
| Unmatched count | 31614 |

## Safe Interpretation

`APPROVE_REVIEW_ONLY` means only that the human may approve the identity link for review-only use after spot-checking it. It does not mean model input, training use, source truth, rank evidence, player value, rookie probability, hidden sort, or draft decision use.

All rows in this packet set:

- `approved_by_human=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `review_only=true`
