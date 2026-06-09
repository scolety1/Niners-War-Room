# Model v4 Rookie Ranking System Audit Prompt - 2026-05-22

You are auditing the rookie/prospect ranking system for a local-first dynasty fantasy football project, Model v4.

## League Context

- 10-team dynasty
- 1QB
- non-PPR
- first-down scoring
- no TE premium
- team under review: Niners
- June 15 roster/trade/rookie draft decision deadline

## Current Concern

The user reviewed the Draft Room Prospect Board and saw likely suspicious rookie ordering. Examples:

- Daniel Sobkowicz is ranked 1st despite missing major evidence and no NFL team shown.
- Skyler Bell is ranked 2nd.
- Kaytron Allen, Nicholas Singleton, Mike Washington, and other volatile or incomplete profiles are above several Deep Research priority names.
- Carnell Tate and Jadarian Price appear much lower than external rookie research expects.
- Some rows with very low `component_weight_available` appear too high.
- Board bands like `first_round_board_context_review` may be too confident for low-evidence rows.

The goal is not to tune the board to consensus. The goal is to verify whether the rookie formula, confidence caps, evidence admission, and UI labels are behaving correctly for this league.

## Files In Packet

Review the included packet folders:

- `01_rookie_draft_review`
  - `rookie_draft_board_review_rows.csv`
  - `rookie_pick_candidate_review_rows.csv`
  - `rookie_draft_component_rows.csv`
  - `rookie_draft_receipts.csv`
  - `rookie_draft_warnings.csv`
  - `rookie_draft_summary.csv`
- `02_research_overlay`
  - Deep Research overlay rows and pick-fit rows.
- `03_prospect_value`
  - Prospect value rows/components/receipts/warnings where available.
- `04_formula_contract`
  - Allowed field registry and blocked field registry.
- `05_evidence_matrices`
  - Admitted/current prospect matrices and source/warning coverage where available.
- `06_docs`
  - Rookie review docs, formula requirements, and research overlay notes.
- `07_app_context`
  - Draft Room page implementation for how the board is displayed.

Raw paid/source exports are intentionally excluded unless already safely processed.

## Audit Questions

1. Does the rookie ranking formula correctly handle missing data?
   - Missing evidence must not become zero, average, or positive evidence.
   - Low `component_weight_available` should not allow an inflated board rank.
   - Confidence caps should materially suppress low-evidence players.

2. Are players with incomplete evidence being ranked too high?
   - Specifically inspect Daniel Sobkowicz, Skyler Bell, Mike Washington, Logan Diggs, Ty Thompson, and other top-25 rows with low component availability or missing landing context.

3. Are high-evidence / high-research-priority players being pushed too low for a formula reason that makes sense?
   - Specifically inspect Jeremiyah Love, Carnell Tate, Jordyn Tyson, Jadarian Price, Makai Lemon, Kenyon Sadiq, and Eli Stowers.

4. Are board bands and pick windows too confident?
   - Should `first_round_board_context_review` require stronger source coverage?
   - Should there be a separate `watchlist_or_data_incomplete_context_review` band?
   - Should the UI show a distinct Draftable Board versus Watchlist/Data-Incomplete Board?

5. Is the model over-rewarding any fragile signal?
   - Small-school production
   - Raw college production without market share
   - athletic testing without production
   - landing spot without draft capital
   - RB volume proxies
   - TE production in no-premium scoring

6. Is the model underweighting required rookie priors?
   - NFL draft capital / landing commitment
   - admitted college market share
   - early declare / age if present
   - target/route evidence where admitted
   - first-down-friendly role evidence
   - confidence and source coverage

7. Does the system preserve source boundaries?
   - Deep Research should be guidance/context only, not private player evidence.
   - ADP/rankings/market/projections/mock drafts should not drive private football value.
   - Market context may be used only for review, edge finding, or sanity, not core score.

8. Does the rookie ranking system need:
   - formula repair,
   - confidence/missingness repair,
   - source/identity repair,
   - board-band/UI repair,
   - or only human review?

9. Recommend concrete repairs.
   - Prefer guardrails and explainability over opinion-matching.
   - Do not recommend simply forcing the board to match Deep Research or ADP.
   - If a repair is needed, describe the exact rule, threshold, or diagnostic test.

## Required Output

Please return:

1. Overall verdict:
   - `ready_for_human_rookie_review`
   - `needs_rookie_formula_repair`
   - `needs_confidence_missingness_repair`
   - `needs_source_identity_repair`
   - `needs_ui_board_band_repair`
   - `needs_more_data`

2. Critical blockers, if any.

3. High/medium/low findings with cited file/row evidence.

4. Player-specific notes for:
   - Daniel Sobkowicz
   - Skyler Bell
   - Jeremiyah Love
   - Carnell Tate
   - Jordyn Tyson
   - Jadarian Price
   - Makai Lemon
   - Kaytron Allen
   - Nicholas Singleton
   - Mike Washington
   - Ty Thompson
   - Eli Stowers
   - Kenyon Sadiq

5. Formula/guardrail recommendations.

6. UI recommendations for making the rookie board understandable.

7. Whether Model v4 should pause rookie decisions until repairs are made.

Remember: this is a review-only project. Do not suggest app promotion or active ranking mutation.
