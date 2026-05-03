# Simon Design Review

## Verdict
RED

## One-Sentence Read
The product may be improving under the hood, but the latest visual evidence is a blank "Not found" page, which is not a command center - it is a locked door.

## Mission Fit
The mission is a local-first, table-first Drop Deadline Command Center for keeper decisions, and the reported code direction still matches that: deterministic formulas, CSV/SQLite snapshots, import review, roster logic, trade/draft/league boards, and model audit work are all relevant. But the current inspected design does not fulfill the mission visually because the captured customer-facing routes do not show the product at all. A fantasy decision engine cannot earn trust if the first visible artifact is route failure.

## Taste Check
There is no meaningful premium or modern visual quality to judge in the latest screenshots because the pages render only "Not found" on a white field. The restraint is accidental, not designed. The only taste signal here is operational: the automated visual report says "No Blocking Visual Bugs" while every inspected screenshot is blocked. That mismatch feels amateur and dangerous for a tool whose whole brand is correctness.

## Visual Problems To Fix
- All latest inspected desktop routes show only "Not found" in the top-left corner instead of command tables or page content.
- The visual QA report claims no blocking visual bugs despite screenshots proving the product routes are unavailable.
- The first screen has no primary job, no Niners roster context, no import status, no ranking separation, and no table surface.
- Route identity cannot be evaluated because the actual route chrome and page headers never render.
- The product hierarchy collapses completely: there is no visible command center, only browser-default whitespace.
- The missing route evidence repeats across Import Review, Draft Room, League Intel, and Model Audit, so this is not a single-page blemish.
- The current evidence makes prior design review loops unreliable because they are judging absence as success.

## Strongest Opportunities
- Restore reliable Streamlit route capture first, then make the command table the first visible object on each page.
- Add a visual smoke check that fails when the screenshot contains "Not found" or mostly blank white space.
- Keep page chrome quiet: one clear page title, one compact status row, then the table.
- Use the Model Audit page as the trust layer, but keep it secondary to the decision boards.
- Make rank separation visible in the tables with disciplined column grouping: Official, Market, War Room, My Rank.
- Use small, sober status badges for KEEP, DROP, SHOP, PRESSURE, and RELEASE RISK instead of large explanatory panels.

## Priority Fix
Fix the route evidence failure before touching visual polish. Nami should create one narrow repair task that makes the latest visual inspection open real Streamlit pages for Import Review, Draft Room, League Intel, and Model Audit, then fail the check if the screenshot includes "Not found" or is mostly blank. Until this is fixed, every design conversation is theater with better file names.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: latest screenshots still show Not found instead of the command center.

## Designer Handoff
Next batch should be evidence repair, not decoration. Keep the Streamlit app table-first, keep the low-text analytical posture, and keep formula/detail explanations behind audit panels or expanders. Change the visual QA path so the rendered screenshots prove that real pages load, then verify that the first screen on each route starts with the decision surface: import errors, Niners roster, forced top-5 release, draft values, league pressure, or model audit. The user should feel "I can make the deadline call from this screen," not "the harness says it passed, apparently."

## What Not To Do Next
- Do not add new pages while current route screenshots are broken.
- Do not add dashboards, hero sections, charts, or decorative styling to hide missing route evidence.
- Do not treat the automated "No Blocking Visual Bugs" report as credible until it catches "Not found."
- Do not expand backend, data packs, auth, deployment, APIs, or package scope.
- Do not redesign the whole app before the inspected pages render real command tables.
- Do not bury the primary decision table below intro copy or explanatory wrappers after the route fix.
- Do not ignore mobile once the desktop route is repaired.

## Next 5 Design Tasks
- [ ] Repair visual inspection routing for the current Streamlit pages; guardrail: latest screenshots must show real page content, not "Not found."
- [ ] Add a screenshot validation check for "Not found" and mostly blank white frames; guardrail: fail loudly before design review artifacts are written.
- [ ] On Import Review, make the first visible block the import status/error table; guardrail: no large intro panel above it.
- [ ] On Draft Room and League Intel, ensure the primary table appears above any model explanation; guardrail: explanations live in expanders or side/detail sections.
- [ ] Review mobile screenshots after routing is fixed; guardrail: no duplicated title bands, stacked route chrome, or table controls pushing the main decision content below the fold.

## Stop Or Continue
continue but fix visual issues first