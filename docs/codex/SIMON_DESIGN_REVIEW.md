# Simon Design Review

## Verdict
RED

## One-Sentence Read
The branch is showing a diagnostic lobby and broken board routes instead of the Drop Deadline Command Center, which is not a product screen, it is a waiting room with a clipboard.

## Mission Fit
The design direction only partially matches the mission. The root page understands the local-first, table-first intent, and the typography has some discipline, but the actual V1 job is missing from the first visible experience: the user cannot inspect the Niners top five, forced release logic, keeper/drop calls, trade pressure, or pick values from the captured route screenshots because the route pages render "Not found." For an analytical command center, missing command tables are mission failure.

## Taste Check
The best part is the restraint: off-white background, strong black type, muted red action, and a sparse table feel closer to a serious local tool than generic fantasy SaaS confetti. Good. But the current surface is too much diagnostic wrapper and not enough product. The big marketing-scale title, loud CTA, and oversized mobile table make the page feel like an inspection artifact, not a usable war room. The design has taste in ingredients, but the plate did not leave the kitchen.

## Visual Problems To Fix
- The captured board routes for Draft Room, Import Review, League Intel, Model Audit, Team, Trade Central, and War Board show "Not found" instead of command tables.
- The root page is a diagnostic wrapper titled "Drop Deadline Board," not the actual V1 command center experience.
- The first screen spends too much visual weight on the hero title and "Inspect route results" CTA while the product-critical board data sits lower and thinner.
- On mobile, the route results table overflows horizontally; runtime source paths are clipped and the table does not feel intentionally responsive.
- The mobile hierarchy is oversized for an operations tool: the H1, paragraph, and CTA consume too much vertical space before the user reaches the useful table.
- The red CTA is visually dominant even though it is secondary inspection chrome, not the user's primary decision workflow.
- The root table only surfaces three boards, which makes the product feel incomplete against the stated V1 command center scope.
- No classic double header is visible, but the diagnostic root wrapper creates the same customer-facing problem: the real product page feels buried behind explanatory chrome.

## Strongest Opportunities
- Make the first visible screen a compact command board with the current top-five status, forced release candidate, import health, and next review actions above the fold.
- Replace the loud inspection CTA with a quiet secondary control or disclosure; inspection artifacts should support the board, not star in it.
- Use dense table hierarchy: compact headers, sticky column labels where appropriate, clear numeric alignment, and restrained status chips.
- Give each board route a small, consistent page header and immediately show its primary table, with formulas and provenance behind details or side panels.
- On mobile, collapse secondary columns behind row expansion instead of letting file paths and long labels wreck the grid.
- Add a consistent "source snapshot" and "model audit" affordance that feels like trust infrastructure, not a separate documentation page pretending to be the app.

## Priority Fix
Restore the actual command board routes as the first-class product surface and demote the diagnostic root page. Nami should turn this into a small visual repair: each captured route must render its primary table immediately, the root should point quietly to those boards only if needed, and the first screen must answer "what needs a drop decision now?" before showing inspection explanation.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: route screenshots still show missing command tables and the root is a diagnostic wrapper instead of the V1 product.

## Designer Handoff
Keep the restrained color, low-text posture, and table-first ambition. Change the hierarchy: the primary board must come first, with operational status, forced release, keeper/drop, and pick-value evidence visible without ceremony. Move route inspection, file paths, long explanations, and audit notes behind quiet disclosure controls. The result should feel like opening a private draft room spreadsheet that has been sharpened into a decision tool: fast, sober, and impossible to confuse with a fantasy advice blog.

## What Not To Do Next
- Do not add more sections to the diagnostic root page.
- Do not polish the "Not found" state or hide it with prettier copy.
- Do not add prediction cards, hero copy, or dashboard theater before the command tables render.
- Do not introduce more red buttons unless the action is truly primary.
- Do not expand backend scope, data contracts, model formulas, or package dependencies for this design repair.
- Do not ignore mobile; the current table behavior already looks accidental.
- Do not let documentation pages compete with the working app surface.

## Next 5 Design Tasks
- [ ] Make every captured board route render its primary table above the fold; guardrail: no route may show "Not found" in visual inspection.
- [ ] Replace the root hero/CTA dominance with a compact command entry layout; guardrail: the first viewport must show board status data, not only explanation.
- [ ] Reduce mobile type scale and CTA weight on the root screen; guardrail: useful table content must begin within the first mobile viewport.
- [ ] Convert runtime source paths into quiet secondary metadata; guardrail: no clipped code path should appear as primary table content on mobile.
- [ ] Add a consistent compact header pattern for all app pages; guardrail: one page title only, no duplicated intro bands, no route chrome louder than the command table.

## Stop Or Continue
stop for human design review