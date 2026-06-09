# Model v4 Prospect Board Explainability Audit Prompt - 2026-05-22

You are auditing the Prospect Board user experience and explainability for a local-first dynasty fantasy football project, Model v4.

## League Context

- 10-team dynasty
- 1QB
- non-PPR
- first-down scoring
- no TE premium
- Niners roster and June 15 deadline

## Current Concern

The Prospect Board may not be laid out well enough for a human manager to understand or trust it. The original visible board mostly showed:

- rank
- player
- position
- college/NFL team
- format score
- confidence cap
- roster fit
- board band
- long technical warning text

That was not enough. The user needs to see where each number comes from, whether the evidence is complete, and whether the board row is draftable or just a watchlist/scouting row.

## Recent UI Patch To Review

The Draft Room Prospect Board now adds more inline columns:

- Evidence Available
- Trust Status
- Production
- Market Share
- Athletic
- Recruiting
- Landing Context
- Research Tier
- Research Stance
- Manual Review Notes

This patch is intended to improve explainability, not to repair formula values.

## Files In Packet

Review the included packet folders:

- `01_rookie_draft_review`
  - rookie board, pick candidates, components, receipts, warnings
- `02_prospect_value`
  - prospect value rows/components/receipts/warnings
- `03_research_overlay`
  - Deep Research overlay and pick-fit rows
- `04_app_context`
  - Draft Room Streamlit page code
- `05_docs`
  - rookie analyzer and research docs
- `06_tests`
  - tests covering navigation/UI expectations

## Audit Questions

1. Is the Prospect Board understandable enough for human rookie review?

2. Does the board clearly separate:
   - draftable candidates,
   - watchlist/data-incomplete candidates,
   - manual scouting candidates,
   - research/model conflict candidates?

3. Are the new columns the right first-view columns?
   - Evidence Available
   - Trust Status
   - Production
   - Market Share
   - Athletic
   - Recruiting
   - Landing Context
   - Research Tier
   - Research Stance

4. What should be hidden behind drilldowns instead of shown in the main table?

5. Should there be separate tables for:
   - Draftable Board
   - Data-Incomplete Watchlist
   - Research Conflict Queue
   - Pick-Specific Shortlist
   - Receipt/Source Drilldown

6. Is the technical warning language too hard to understand?
   - Recommend plain-English warning labels.
   - Recommend row-level status labels.

7. Does the UI make it obvious that Deep Research is review-only context and not formula input?

8. Does the UI make it obvious that ADP/market/rank/projection context is not private football value?

9. Does the board currently risk misleading the user into taking low-evidence rows seriously because they are highly ranked?

10. Recommend concrete layout changes.
    - Prioritize changes that help the user decide who to scout, who to draft, who to avoid, and which rankings are suspicious.
    - Do not recommend app promotion or active ranking mutation.

## Required Output

Please return:

1. Overall verdict:
   - `prospect_board_ui_ready`
   - `needs_main_table_layout_repair`
   - `needs_draftable_watchlist_split`
   - `needs_warning_language_repair`
   - `needs_receipt_drilldown_repair`

2. Critical/high/medium/low findings.

3. Recommended main table columns in order.

4. Recommended tabs/sections in order.

5. Recommended row status labels.

6. Specific notes for whether the board should separate Daniel Sobkowicz/Skyler Bell-style low-evidence rows from Love/Tate/Tyson/Price/Lemon-style draft candidates.

7. Whether the current UI is safe for human review tonight.
