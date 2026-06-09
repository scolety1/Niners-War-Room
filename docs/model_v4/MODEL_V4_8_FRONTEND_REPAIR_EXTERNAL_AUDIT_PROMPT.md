# Model v4.8 Frontend Repair External Audit Prompt

You are auditing the Model v4 local Streamlit frontend after a human-review UI repair sprint.

Context:
- League: 10-team dynasty, 1QB, non-PPR, first-down scoring, no TE premium.
- The model remains review-only.
- Do not judge whether the model should make final cut/keep/trade/draft decisions.
- Judge whether the app now helps a human review those decisions.
- Active rankings, My Team, War Board, readiness gates, and app promotion must remain unchanged.
- Market/ADP/ranking/projection context may be displayed only as labeled context and must not appear to drive private model value.

Audit packet contents include:
- Frontend repair prompt queue.
- App navigation and main shell files.
- Shared UI components.
- Primary page files.
- Screenshots for Review Workflow, Decision Board, Draft Room, Player Board, Trade Review, and Settings.

Please review the packet and answer:

1. Is the sidebar/page workflow understandable for a human who wants to review June 15 roster and rookie draft decisions?
2. Does Review Workflow work as a useful map rather than another technical dashboard?
3. Is Decision Board usable as the first stop for top-five drop rule, normal roster pressure, and cut-cost review?
4. Is Draft Room pick-first enough for owned picks, especially 1.03, 1.04, 2.04, 2.08, and manual-only 5.04?
5. Is Player Board readable as the main player inspection table?
6. Is Trade Review clearly context-only and not presented as final trade advice?
7. Is Settings now a data-health/status page first, with import/backfill/source-builder controls appropriately hidden under Advanced sections?
8. Are ages visible where dynasty decisions need them, or are there remaining high-value places where age is missing from the UI?
9. Is market/ADP/league-rank context clearly separated from model/private football value?
10. Are raw tables, receipts, file paths, warning codes, and builder tools hidden enough by default?
11. Do any first-viewport sections still feel too wide, clipped, table-heavy, or hard to understand at normal browser width?
12. Do the shared labels and player detail panels make warnings and rank explanations more understandable?
13. Are there any UI changes that accidentally create or imply final cut/keep/trade/draft recommendations?
14. Are there any signs of app promotion, readiness unlock, active ranking mutation, My Team mutation, or War Board mutation?

Required output:
- Overall verdict: `ready_for_human_frontend_review`, `needs_minor_ui_patch`, or `needs_major_ui_repair`.
- Critical blockers, if any.
- High-priority UI issues, if any.
- Medium/low-priority UI issues.
- Page-by-page notes for Review Workflow, Decision Board, Draft Room, Player Board, Trade Review, and Settings.
- Specific patch recommendations before the next human review session.

Be direct. If the UI is still confusing, say exactly where and why.
