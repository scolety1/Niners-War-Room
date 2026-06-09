# 5-27 Frontend Human Review Repair Prompts

Purpose:
Turn the Model v4 app from a builder/audit workbench into a usable human decision review tool. The model formulas have passed audit; this sprint is about page structure, labels, visibility, age/context display, and reducing table overload.

Rules for every prompt:
- Keep everything review-only.
- Do not mutate active rankings, My Team, War Board, readiness gates, app promotion, or final recommendations.
- Do not create final cut/keep/trade/draft recommendations.
- Do not use ADP, market rankings, projections, mock drafts, big boards, or consensus as private football value.
- Market/ADP may appear only as explicitly labeled optional context.
- Missing data remains missing and must be labeled honestly.
- Add age anywhere dynasty decisions are shown when admitted age data is available.
- Hide raw tables, receipts, formula versions, file paths, and warning codes behind Advanced/Receipts unless they are the main point of the page.
- Run focused tests, Ruff, compile/static checks, and reload the local app where practical.

## Prompt 1 - Decision Board v2

```text
Model v4.8 / Frontend Prompt 1: Decision Board v2

Goal:
Make Decision Board feel like an actual June 15 deadline board instead of a raw model output table.

Tasks:
1. Rework the default Decision Board layout around four plain-English sections:
   - Top-Five Drop Rule
   - Normal Cut Candidates
   - Do Not Cut Without Trade Check
   - Cut Cost / Replacement Context
2. Show cards before tables.
3. For each visible player card show:
   - player
   - age
   - position
   - NFL team
   - model value
   - internal/startup slot if available
   - rookie pick equivalent
   - cut cost label
   - top warning/risk group
   - human check question
4. Keep explicit review-only wording, but do not let it dominate the page.
5. Move raw Sprint rows, formula versions, warning code tables, receipt paths, and downloads under Advanced.
6. Preserve filters, but move them below the main cards or into a collapsed filter drawer.
7. Ensure 2026 5.04 remains manual-only with no fake baseline.
8. Add/keep age fields from admitted age data only; if age is missing, show "Age missing".
9. Do not create final cut/keep/trade recommendations.

Acceptance checks:
- Decision Board first viewport shows actual decision cards.
- Top-five slot is visible without scrolling.
- Normal cut candidates are visible without opening tabs.
- Raw technical tables are not visible by default.
- Ages appear where available.
- Review-only constraints remain visible.
- Focused tests, Ruff, and py_compile pass.
```

## Prompt 2 - Player Board v2

```text
Model v4.8 / Frontend Prompt 2: Player Board v2

Goal:
Make Player Board readable as the main player inspection table.

Tasks:
1. Make the default table search-first and manager-friendly.
2. Default visible columns:
   - model rank
   - player
   - age
   - position
   - NFL team
   - owner
   - model value
   - keep priority
   - drop pressure
   - trust/confidence
   - review label
   - top warning group
3. Hide market/ADP/league-rank context by default behind a clearly labeled:
   - Market Context (Read-Only)
4. Hide raw formula components behind:
   - Formula Components
5. Hide receipts behind:
   - Receipts
6. Rename or avoid any "recommendation" wording in visible UI.
7. Add a compact "Why to open this page" note:
   - use this page when a specific player/rank looks weird.
8. Add age from admitted age data only. Missing age must display as "Age missing".
9. Keep review-only and no-market-leakage language.

Acceptance checks:
- Default Player Board does not show ADP/market columns.
- Default table includes age.
- No visible column is named "recommendation".
- User can search a player quickly.
- Formula/raw/receipt content is collapsed by default.
- Focused tests, Ruff, and py_compile pass.
```

## Prompt 3 - Draft Room v2

```text
Model v4.8 / Frontend Prompt 3: Draft Room v2

Goal:
Make Draft Room usable for rookie draft review, especially owned picks.

Tasks:
1. Make the first screen owned-pick-first.
2. Put Pick Decision Lab above the full Prospect Board.
3. For each owned pick show a card:
   - pick label
   - pick value score / manual-only status
   - top rookie cluster
   - nearby veteran/current assets from startup slot
   - highest upside candidate
   - safest candidate
   - biggest model risk
   - human question
4. Show 2026 5.04 as manual-only/no exact baseline.
5. Prospect Board default columns:
   - rank
   - player
   - age
   - position
   - NFL team
   - college
   - final score
   - production
   - college team share
   - NFL draft pick signal
   - athletic
   - trust
   - warning/model edge label
   - why this rank
6. Put historical comps, receipts, raw warnings, and advanced draft tools behind collapsed sections.
7. Keep mock/draft interaction tools if present, but do not let them dominate the default review view.
8. Do not create final draft recommendations.

Acceptance checks:
- Owned picks are visible before the big prospect table.
- Ages are visible for rookies where admitted.
- 5.04 is clearly manual-only.
- Prospect Board is understandable without raw code columns.
- Advanced draft tools are collapsed by default.
- Focused tests, Ruff, and py_compile pass.
```

## Prompt 4 - Global Human Label Dictionary

```text
Model v4.8 / Frontend Prompt 4: Global Human Label Dictionary

Goal:
Replace machine-coded labels with plain English across the frontend.

Tasks:
1. Create or extend a shared UI label translator module.
2. Translate common codes globally:
   - manual_only_no_exact_model_baseline -> Manual only: no reliable baseline
   - review_only_no_final_recommendation -> Review only
   - review_only_no_cut_keep_recommendation -> No cut/keep call
   - review_only_no_trade_recommendation -> No trade call
   - source_shape_warning -> Data shape warning
   - model_edge_weirdness -> Model edge
   - no_premium_te_cap -> No-TE-premium cap
   - one_qb_qb_scarcity_cap -> 1QB value cap
   - missing_or_review_route_target_snap_evidence -> Missing route/target/snap evidence
   - rb_age_cliff_guardrail_unavailable -> RB age-risk check needed
3. Apply translator to:
   - Decision Board
   - Draft Room
   - Player Board
   - Trade Review
   - Settings/data health surfaces
4. Preserve raw codes in Advanced/Receipts.
5. Do not alter formulas or CSV outputs unless needed for display-only exports.

Acceptance checks:
- Primary UI no longer exposes raw machine labels by default.
- Raw warning codes remain available under Advanced.
- Tests prove translator preserves unknown codes safely.
- Focused tests, Ruff, and py_compile pass.
```

## Prompt 5 - Shared Player Detail Panel

```text
Model v4.8 / Frontend Prompt 5: Shared Player Detail Panel

Goal:
Create one reusable player detail panel that can be used across Decision Board, Draft Room, Player Board, and Trade Review.

Tasks:
1. Build a reusable component/function for player detail.
2. Inputs should come from existing review-only outputs.
3. Detail panel should show:
   - player
   - age
   - position
   - NFL team / college
   - owner if current player
   - model value
   - rank/internal slot
   - rookie pick equivalent if available
   - why this rank
   - strongest signals
   - weakest signals
   - warning groups
   - evidence risk / trust status
   - nearby players/picks
   - receipt links or source file pointers
4. Add this detail panel as an expander/card action wherever practical:
   - Decision Board cards
   - Draft Room prospect rows/cards
   - Player Board selected player area
   - Trade Review player rows
5. Missing fields must display honestly.
6. Do not create final recommendations.

Acceptance checks:
- A user can inspect one player without jumping across four pages.
- Detail panel includes age when admitted.
- Detail panel distinguishes model evidence from market context.
- Raw receipts are linked/collapsed.
- Focused tests, Ruff, and py_compile pass.
```

## Prompt 6 - Settings Simplification

```text
Model v4.8 / Frontend Prompt 6: Settings Simplification

Goal:
Make Settings useful for humans by default and move builder controls out of the way.

Tasks:
1. Default Settings view should show:
   - active data pack
   - data health status
   - last refresh/snapshot date where available
   - major warnings/errors
   - model mode/review-only status
2. Move advanced controls into collapsed sections:
   - Import & Refresh
   - Source Overrides
   - Backfills
   - Stats-first preview packs
   - Raw data/debug controls
3. Use plain-English labels.
4. Keep advanced controls available, but not visible by default.
5. Do not change data or run imports unless user clicks an existing action.

Acceptance checks:
- First viewport of Settings is data health, not controls.
- Advanced imports/backfills are collapsed.
- No app state is mutated by merely opening Settings.
- Focused tests, Ruff, and py_compile pass.
```

## Prompt 7 - Responsive Layout And Table Width Pass

```text
Model v4.8 / Frontend Prompt 7: Responsive Layout And Table Width Pass

Goal:
Fix horizontal overload and make key pages usable at normal browser widths.

Tasks:
1. Review screenshots/current browser for:
   - Decision Board
   - Draft Room
   - Player Board
   - Trade Review
   - Review Workflow
2. Replace first-viewport wide tables with cards or narrow summary tables.
3. Keep large raw tables only in Advanced sections.
4. Ensure text does not overflow cards/buttons.
5. Avoid huge columns that force the user to pan horizontally.
6. Use stable card/table widths and responsive wrapping.
7. Verify with browser screenshots after patching.

Acceptance checks:
- First viewport on each primary page is readable at normal width.
- No important first-screen content is clipped horizontally.
- Large raw tables are not visible by default.
- Browser screenshots are captured.
- Focused tests, Ruff, and py_compile pass.
```

## Prompt 8 - Frontend Repair Audit Packet

```text
Model v4.8 / Frontend Prompt 8: Frontend Repair Audit Packet

Goal:
Package the frontend repair sprint for external audit.

Tasks:
1. Capture screenshots of:
   - Review Workflow
   - Decision Board
   - Draft Room
   - Player Board
   - Trade Review
   - Settings
2. Package no more than 20 files:
   - frontend repair docs
   - app navigation
   - key page files
   - shared UI components
   - screenshots
   - relevant v4.7 UI audit report/prompt if available
3. Write a neutral audit prompt asking whether:
   - the app now supports final human review
   - the sidebar workflow is understandable
   - Decision Board is usable
   - Draft Room is pick-first
   - Player Board is readable
   - ages are visible where needed
   - market/ADP context is safely separated
   - advanced/builder tools are appropriately hidden
   - review-only constraints remain clear
4. Produce:
   - docs/model_v4/MODEL_V4_8_FRONTEND_REPAIR_EXTERNAL_AUDIT_PROMPT.md
   - local_exports/model_v4/audit_packets/model_v4_8_frontend_repair_audit_YYYYMMDD.zip
5. Verify zip file count is 20 or fewer.

Acceptance checks:
- Packet is audit-ready.
- Prompt is neutral.
- No app promotion or final recommendations.
```

## Prompt 9 - v4.8.1 UI Audit Polish Patch

```text
Model v4.8.1 / Frontend Prompt 9: UI Audit Polish Patch

Goal:
Apply the minor/high-priority polish items from the v4.8 external frontend audit
without reopening formula work or adding new decision logic.

Audit verdict:
- Ready for human front-end review.
- No critical blockers.
- Remaining issues are UI clarity, labels, responsive polish, and advanced-table wording.

Tasks:
1. Trade Review label cleanup:
   - Rename visible tab/section label "Advanced Package Builder" to
     "Trade Context Drill-Down" or "Advanced Trade Context".
   - Add a clear caption that no offer is created and package rows are review-only
     model-equivalence/context rows.
   - If visible, soften any "acceptance likelihood" wording so it reads as
     deal-friction/context, not a recommendation.

2. Player Board polish:
   - Add search placeholder text:
     "Search by player, team, or position".
   - In Market Context (Read-Only), repeat that league rank / ADP / market context
     is display-only and does not drive private model value.
   - Rename visible advanced label "Raw Legacy Recommendation" to
     "Historical Recommendation Label (legacy)" or hide it from default advanced
     displays if not needed.

3. Decision Board polish:
   - Keep filters collapsed and move/keep them below the primary decision cards
     and start-here guidance.
   - Ensure the user sees Top-Five Drop Rule, Normal Cut Candidates,
     Do Not Cut Without Trade Check, and Cut Cost / Replacement Context before
     any raw/technical table.
   - Keep "Final calls created" clearly "No" or hide it if it adds confusion.

4. Draft Room polish:
   - Add short tooltips/captions explaining "cluster", "tier", and "manual-only"
     in plain language.
   - Hide or de-duplicate duplicate manual_questions / manual_question_* fields
     from visible advanced displays where practical.
   - Keep 2026 5.04 manual-only with no fake baseline.

5. Settings polish:
   - Add a short plain-English explanation of "data pack":
     "A data pack is the active snapshot of rosters, picks, rankings context, and
     model review outputs the app is reading."
   - Make clear that switching packs changes what the app displays, but opening
     Settings does not mutate anything.
   - Keep import/backfill/source-builder controls collapsed under Advanced.

6. Responsive/layout polish:
   - Verify Review Workflow, Decision Board, Draft Room, Player Board, Trade Review,
     and Settings at normal desktop width and narrow/mobile width.
   - Patch any card/button/tab text that clips or overflows.
   - Keep large raw tables under Advanced.
   - Capture updated screenshots after patching.

7. Safety constraints:
   - Review-only outputs only.
   - No final cut/keep/trade/draft recommendations.
   - No formula changes.
   - No active rankings changes.
   - No My Team mutation.
   - No War Board mutation.
   - No readiness unlock.
   - No app promotion.
   - No market/ADP/ranking/projection leakage into private football value.

Acceptance checks:
- External audit high-priority UI issues are addressed.
- Trade Review no longer sounds like an offer-building tool.
- Player Board search and advanced labels are clearer.
- Settings explains data packs in human terms.
- Decision Board and Draft Room remain first-screen usable.
- Updated screenshots are captured.
- Focused tests, Ruff, and py_compile pass.
```

## Suggested Order

1. Prompt 1 - Decision Board v2
2. Prompt 2 - Player Board v2
3. Prompt 3 - Draft Room v2
4. Prompt 4 - Global Human Label Dictionary
5. Prompt 5 - Shared Player Detail Panel
6. Prompt 6 - Settings Simplification
7. Prompt 7 - Responsive Layout And Table Width Pass
8. Prompt 8 - Frontend Repair Audit Packet
9. Prompt 9 - v4.8.1 UI Audit Polish Patch
