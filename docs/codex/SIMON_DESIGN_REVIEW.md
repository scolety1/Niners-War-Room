# Simon Design Review

## Verdict
RED

## One-Sentence Read
The branch is still presenting a diagnostic wrapper and broken route captures instead of the Drop Deadline Command Center, which is not a design problem so much as the product failing to appear.

## Mission Fit
The mission is table-first, local-first decision support for a keeper deadline. The current root screen partially understands the restraint: plain typography, one action, a small route checklist, no fake fantasy-blog theater. But the actual Streamlit routes in the latest screenshots render as "Not found", so the user cannot see the Niners roster, forced release logic, import review, draft values, trade board, or league pressure board. That misses the mission at the first gate. A war room cannot be a sign taped to a locked door.

## Taste Check
The root page has a few correct instincts: sober spacing, minimal copy, a red action color that nods to the team without becoming fan-art, and a table-like inspection list. It feels more disciplined than generic SaaS confetti.

But the hierarchy is wrong for the current phase. "Inspect route results" is now louder than the actual product, and the static root reads like a QA holding page. The mobile table also clips the runtime source column, which makes the one visible table feel unfinished. The repeated route failure screens are stark, empty, and unacceptable as product evidence.

## Visual Problems To Fix
- Customer-facing route captures for Import Review, Team, War Board, Trade Central, Draft Room, League Intel, and Model Audit show "Not found" instead of command tables.
- The root page is a diagnostic wrapper, not the V1 command center; it makes QA process the first-screen product.
- The root CTA "Inspect route results" visually dominates more than any actual decision surface.
- The mobile root table overflows horizontally and clips file paths, creating a cramped, amateur inspection view.
- The visible product identity is thin: "Drop Deadline Board" is close, but the screen does not immediately answer "who do I drop, keep, or shop?"
- There is no visible separation of Official Rank, Market Rank, War Room Rank, and My Rank in the captured route evidence because the routes are not rendering.
- The automated visual report says no blocking visual bugs while screenshots show route failure; the inspection system is producing false comfort.

## Strongest Opportunities
- Make the real first screen a compact command board with the top-five status, forced release candidate, keeper pressure, and one primary sortable table.
- Keep the visual language austere: dense tables, small status chips, restrained red accents, no decorative dashboard fluff.
- Put import/source/model audit details behind tabs, expanders, or a secondary route so the first screen stays decision-first.
- Use a consistent table grammar across pages: same rank columns, confidence/source columns, risk markers, and row actions.
- Treat mobile as a review surface, not a full spreadsheet: prioritize top decision columns and hide secondary fields behind row detail.

## Priority Fix
Restore the actual Streamlit/product routes in visual capture before any design polish. The next task should make `/Import_Review`, `/Team`, `/War_Board`, `/Trade_Central`, `/Draft_Room`, `/League_Intel`, and `/Model_Audit` render their primary command tables instead of "Not found"; the root diagnostic page can remain quiet only if it links to working product surfaces and does not pretend to be the app.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: latest route screenshots still show missing command tables while the root is a diagnostic wrapper instead of the V1 product.

## Designer Handoff
Next implementer: stop adding surfaces and make the existing surfaces visible. Keep the restrained typography, simple red accent, and table-first tone. Change the first impression from "QA capture page" to "drop deadline decisions are ready": top-five release status first, then the main sortable table, then secondary audit/import details behind disclosure. The user should feel they are looking at a private decision instrument, not a development placeholder with a nice button.

## What Not To Do Next
- Do not add more pages, sections, or cards while core routes render "Not found".
- Do not decorate the root page to compensate for missing product screens.
- Do not introduce big dashboard KPIs unless they are tied directly to forced release, keeper/drop, trade, league pressure, or pick value decisions.
- Do not turn formula audit content into first-screen prose.
- Do not ignore mobile overflow; table density still needs discipline on small screens.
- Do not change backend scope, data architecture, auth, deployments, packages, or analytics as part of this design repair.

## Next 5 Design Tasks
- [ ] Fix visual route rendering so every captured app route shows its primary table or empty-state table, with no "Not found" screenshots accepted.
- [ ] Replace the root diagnostic emphasis with a quieter entry that points to the command board and keeps QA explanation behind the existing disclosure.
- [ ] Make the primary command board first screen show top-five status, forced release candidate, and the main decision table above any explanatory content.
- [ ] Tighten mobile table presentation by hiding or wrapping runtime/source/detail columns so no first-screen horizontal clipping appears.
- [ ] Standardize visible rank columns across decision tables with separate labels for Official, Market, War Room, and My Rank; no merged or ambiguous rank language.

## Stop Or Continue
stop for human design review