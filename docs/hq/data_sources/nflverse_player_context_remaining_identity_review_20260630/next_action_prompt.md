# Next Action Prompt

Use this only if the user wants a future explicit human approval/binding pass for the 13 remaining NFLVerse player-context identity rows.

Inputs:

- `docs/hq/data_sources/nflverse_player_context_remaining_identity_review_20260630/human_decision_sheet_for_remaining_rows.csv`
- `docs/hq/data_sources/nflverse_player_context_remaining_identity_review_20260630/remaining_identity_review_matrix.csv`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`

Rules:

1. Do not approve any row unless explicit human decisions are provided in that lane.
2. Kentrel Bullock and Jamal Haynes require manual NWR/Sleeper binding review before any artifact exposure.
3. Rows marked `RECOMMEND_HUMAN_REVIEW` require explicit human approval and, where needed, a subsequent binding packet before artifact rebuild.
4. Rows marked `RECOMMEND_KEEP_BLOCKED` remain gated unless a future approved NFLVerse/GSIS source resolves the blocker.
5. Do not use DynastyProcess, market/ADP, vendor/private/Gmail, `ff_rankings`, or name-only evidence as identity truth.
6. Preserve all flags as review/display-only with model/training/source-truth/rank/hidden-sort/trade/pick flags false.
7. Missing values remain `Not enough information`.

Expected starting counts:

- Remaining gated rows: 13
- Human review candidates: 6
- Keep blocked rows: 7
- Approved rows in this packet: 0
