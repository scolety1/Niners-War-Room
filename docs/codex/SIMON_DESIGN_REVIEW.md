# Simon Design Review

## Verdict
RED

## One-Sentence Read
The branch is trying to be a Drop Deadline Command Center, but the latest visual evidence mostly shows a static inspection placard and broken routes, which is not a command center, it is a waiting room with a clipboard.

## Mission Fit
The design direction only partially matches the mission. The root page has the correct instinct: local-first, restrained, table-first, and focused on inspection before new work. But the actual product routes for Import Review, Team, War Board, Trade Central, Draft Room, League Intel, and Model Audit render as "Not found" in the latest screenshots, so the mission-critical command tables are not visible. For V1, the user must land directly on deterministic decision surfaces: official top five, forced release, keeper/drop score, pick values, trade board, and league pressure. Right now the visible product does not prove those jobs are available.

## Taste Check
The root page has some taste: the typography is simple, the warm off-white background avoids generic dark-dashboard cosplay, and the table-first move is closer to the mission than a fake fantasy sports cockpit. The red accent has enough authority for a deadline tool.

But the hierarchy is too ceremonial for a utility app. "Drop Deadline Board" is huge while the useful content is a three-row inspection table. On mobile, the table overflows horizontally and the file path column becomes the loudest thing on the page. The route pages are just "Not found", which makes every design discussion after that feel theoretical. A premium command tool cannot have seven doors that open into drywall.

## Visual Problems To Fix
- The main application routes render "Not found" instead of the actual Streamlit command tables, so the visible product surface is broken.
- The root page is an inspection wrapper, not the command center itself; it makes the user inspect route results before showing the primary decision workflow.
- The first screen does not answer any core V1 question: no official top five, no forced release candidate, no keeper/drop table, no pick value table.
- Mobile table layout overflows horizontally; the runtime source paths are clipped and dominate the viewport.
- The root page hierarchy is oversized for the amount of content, with a hero-scale title consuming attention that should go to the decision table.
- The CTA "Inspect route results" is visually louder than the actual board rows, which reverses the product priority.
- Runtime file paths are shown as primary table content; useful for developers, but too internal for the first product screen.
- There is no repeated double header visible on the root route, but there is a larger route identity problem: the inspection page replaces the app instead of quietly supporting it.
- The latest automated visual report says no blocking visual bugs, but that misses the obvious product failure: the screenshots show no usable command tables on customer-facing routes.

## Strongest Opportunities
- Make the root screen the actual Drop Deadline Command Center: top-five status, forced release flag, keeper/drop board, and source snapshot status above the fold.
- Keep the austere table-first direction, but reduce the title scale and make row density feel like an operations desk, not a landing page.
- Move developer inspection details behind a small "Route diagnostics" or "Data sources" disclosure.
- Give every page a visible first job: Import Review validates files, Team shows official top five, War Board ranks keep/drop/shop, Draft Room shows pick values, League Intel shows pressure.
- Use confidence/source badges inside tables with restrained color, so the app feels deterministic and auditable without becoming decorative.
- Fix mobile with stacked row summaries or a horizontally scrollable table container that does not crop the most important columns.

## Priority Fix
Restore the real product routes and make the first visible screen answer the command-center job. Nami should first ensure `/Import_Review`, `/Team`, `/War_Board`, `/Trade_Central`, `/Draft_Room`, `/League_Intel`, and `/Model_Audit` render meaningful tables instead of "Not found", then demote the static route-inspection page into a quiet diagnostic detail. No new sections, no prettier wrapper, no extra theatre: show the decision surfaces.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: latest route screenshots still show missing command tables and the root is a diagnostic wrapper instead of the V1 product.

## Designer Handoff
Keep the restrained local-tool tone: off-white surface, sharp typography, low decoration, table-first structure. Change the information priority. The first screen should feel like a private deadline desk where the co-owner immediately sees "who is in danger, why, and what can be done." Put current snapshot status and the top decision table first; move route results, runtime file paths, explanatory copy, and model audit detail behind small disclosures. The result should feel fast, sober, and useful, like opening a binder already turned to the correct page.

## What Not To Do Next
- Do not add more pages while the existing routes render "Not found".
- Do not polish the static `index.html` wrapper as if it were the product.
- Do not add hero copy, cards, dashboard chrome, or fantasy-sports decoration.
- Do not turn model explanations into first-screen content.
- Do not make file paths and diagnostics compete with roster decisions.
- Do not ignore mobile; the current table behavior already breaks trust.
- Do not change backend scope or invent new product features to cover the visual failure.

## Next 5 Design Tasks
- [ ] Restore each named route to render its primary table, with no "Not found" state in the latest visual screenshots.
- [ ] Replace the root inspection-first layout with a compact command-center summary showing snapshot status, official top five, and forced release candidate.
- [ ] Move runtime source paths and route diagnostics behind a collapsed detail control, keeping the first screen free of developer-only content.
- [ ] Reduce hero title scale and CTA dominance so the table is visually primary on desktop and mobile.
- [ ] Add a mobile table treatment for the root and primary command tables, with no clipped critical columns and no horizontal overflow unless explicitly contained.

## Stop Or Continue
stop for human design review