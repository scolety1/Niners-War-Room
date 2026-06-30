# Guardrail Report

Verdict: GREEN for display/UX changes.

Confirmed scope:

- No Dynasty Rank mutation.
- No tier mutation.
- No Frozen Final Draft Board V1 mutation.
- No `final_board_rank` mutation.
- No pinned snapshot mutation.
- No `latest_candidate` update.
- No `latest_approved` update.
- No production model/rank logic change.
- No source-truth/model-input gate change.
- No DynastyProcess promotion to model input.
- No Outcome V2 promotion to rank logic.
- No injury-context promotion beyond review-only.
- No CFBD, NFL usage, vendor, Gmail, proxy, or review-only evidence promotion.
- No new player values.
- No market-adjusted rank.
- No outcome-adjusted rank.
- No injury-risk or recovery logic.
- Missing Statistic Analysis component fields display `Not enough information`, never zero, false, healthy, bad, low probability, or clean.

Protected artifacts remain outside this patch:

- frozen board artifacts
- latest candidate pointers
- latest approved pointers
- pinned snapshots
- Live Draft runtime
- Mock Draft runtime
