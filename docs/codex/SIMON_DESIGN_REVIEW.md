# Simon Design Review

## Verdict
RED

## One-Sentence Read
The product may be doing serious formula work underneath, but the visible experience currently presents as a broken route capture, which is not a command center - it is a white page with "Not found" wearing a tiny hat.

## Mission Fit
The design direction cannot be approved against the Drop Deadline Command Center mission because the latest visual evidence does not show the app at all. The mission asks for a table-first, deterministic Streamlit tool where the owner can quickly inspect top-five release pressure, keeper/drop calls, trades, league pressure, and pick value. The current screenshots instead show route failure across Draft Room, Import Review, League Intel, and Model Audit, so the UI cannot demonstrate table clarity, rank separation, import review, progressive disclosure, or decision readiness.

## Taste Check
The underlying product direction is right: table-first, local-first, formula-visible, and not a fantasy advice blog. That is the correct restraint for analytical software.

Visually, the current evidence is unacceptable. A blank white browser with "Not found" is not minimalism, it is absence. The automated visual bug report saying "No Blocking Visual Bugs" while every reviewed screenshot is "Not found" damages trust more than a merely ugly dashboard would.

## Visual Problems To Fix
- Latest desktop screenshots for Draft Room, Import Review, League Intel, and Model Audit all show only "Not found" in the top-left corner.
- The visual QA path is still capturing broken routes, so design review cannot judge actual page hierarchy, table density, rank labeling, or mobile behavior.
- The automated visual report claims no blocking visual bugs despite route failure, so the review system is visually blind to the most obvious failure state.
- Customer-facing app routes are not proving the primary command table first; the first screen is not the product, it is an error.
- Mobile screenshots are therefore also invalid evidence; no responsive layout quality can be trusted from this batch.
- Any prior UI cleanup is currently invisible because route access failure sits in front of the product surface.

## Strongest Opportunities
- Make visual QA route resolution boring and reliable before another styling task is allowed.
- Add a hard visual smoke check that fails on "Not found", mostly blank pages, or missing expected page titles.
- Once routes render, tighten each page around one primary table and one decision question: release, keep/drop/shop, trade, pressure, draft pool, or model audit.
- Use side panels or expanders for formula detail so the first screen stays operational and not explanatory.
- Treat status badges, confidence, source, and rank type as the visual language of trust instead of adding decorative dashboard chrome.

## Priority Fix
Fix the route evidence failure first. Nami should make the smallest possible repair that ensures every named Streamlit page used by visual QA loads real app content on desktop and mobile, then make the visual inspection fail loudly when captured text includes "Not found" or when the page is mostly blank. No layout polish matters until the screenshots prove the actual command center exists.

## Magic Improvement Score
SCORE: 1-5; DIRECTION: regressed; ACTIVE_PACK: none; REASON: latest evidence still shows route failure while visual QA reports no blockers.

## Designer Handoff
Next batch should be a visual evidence repair, not a redesign. Keep the table-first analytical direction, the local-first restraint, and the separation between Official Rank, Market Rank, War Room Rank, and My Rank. Change the visual QA route mapping and failure detection so screenshots show the actual Streamlit pages. The result should feel like opening a serious draft room command table immediately, not debugging a missing route.

## What Not To Do Next
- Do not add new pages or sections.
- Do not restyle the app while screenshots still show "Not found".
- Do not trust the automated visual bug report until it catches blank-route failure.
- Do not add prediction cards, fantasy prose, or strategy theatrics.
- Do not expand backend, data model, package, or formula scope to solve a visual route problem.
- Do not ignore mobile once real pages render.

## Next 5 Design Tasks
- [ ] Repair the visual QA route map so Draft Room, Import Review, League Intel, and Model Audit render real Streamlit content; guardrail: no product feature changes.
- [ ] Add a visual smoke assertion that fails on "Not found" text; guardrail: keep it limited to visual QA or static check support.
- [ ] Add a mostly blank page detection threshold to the screenshot review; guardrail: do not require pixel-perfect design approval.
- [ ] Re-capture desktop and mobile screenshots for the same four routes and verify each shows a real page title plus at least one data table; guardrail: no new screenshots from stale runs.
- [ ] After route evidence passes, remove one repeated or oversized visible chrome element from the busiest rendered page; guardrail: one page, one visible simplification only.

## Stop Or Continue
continue but fix visual issues first