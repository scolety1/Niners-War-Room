# Model v4.6 External Audit Prompt

You are auditing Model v4.6, a review-only dynasty fantasy football decision system.

League context:
- 10-team dynasty
- 1QB
- non-PPR
- rushing/receiving first-down scoring
- no TE premium
- user team: Niners
- June 15 roster deadline

Audit goal:
Verify that the v4.6 cleanup is working as expected and that the system is ready for human final decision review.

Important constraints:
- Do not judge the model by whether it matches consensus rankings.
- Weird model outputs are allowed if they are supported by admitted evidence and clearly labeled.
- Market, ADP, rankings, projections, mock drafts, big boards, and consensus must not drive private football value.
- All outputs must remain review-only.
- No final cut, keep, trade, defer, or draft recommendations should be created.
- Missing data must remain missing and must not become zero, average, or fake precision.

Please review the attached packet and answer:

1. Does the v4.6 guided human review flow make the app easier to inspect?
2. Does the Evidence Risk consolidation preserve raw audit rows while giving a clear one-row-per-player summary?
3. Is 2026 5.04 still safely handled as `manual_only_no_exact_model_baseline` with no synthetic exact baseline?
4. Does the warning-code dictionary make raw warning strings understandable while preserving audit precision?
5. Does the final human review brief point the user to the right pages and files without creating recommendations?
6. Are all key outputs still review-only?
7. Is there any sign of market/ADP/ranking/projection/mock/consensus leakage into private model value?
8. Are QB and TE constraints still visible for 1QB and no-TE-premium format?
9. Are high evidence-risk and model-edge players clearly marked for manual review?
10. Is the system ready for human final decision review, or does any issue need repair first?

Return:
- Overall verdict: `ready_for_human_final_decision_review` or `needs_repair_before_human_review`
- Critical blockers, if any
- High-priority issues, if any
- Medium/low issues, if any
- Specific file/row examples supporting your findings
- Whether the packet proves review-only/no-market-leakage constraints
- Recommended next action
