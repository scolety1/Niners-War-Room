# Simon Design Review

## Verdict
RED

## One-Sentence Read
The mission may be sound underneath, but the current visual evidence is a white page saying "Not found", which is not a command center, it is a locked door.

## Mission Fit
The product direction still matches the mission on paper: local-first, deterministic, table-first, focused on drop deadline decisions, trade pressure, draft pool, and model auditability. The visible branch does not currently prove that mission because every latest inspected route screenshot shows "Not found" instead of Streamlit product screens. For an analytical tool where trust is the product, a broken visual QA path is not a side issue; it means the team cannot verify hierarchy, table density, progressive disclosure, or whether the actual decision flow is working.

## Taste Check
There is no premium surface to reward in the latest screenshots. The only visible design is default white browser space and tiny black "Not found" text in the upper left. That reads like failed routing, not restrained analytical design. The underlying docs suggest a better product philosophy than the screenshots show: correctness first, tables first, explanations behind panels. Good. But taste is judged on what ships to the screen, and right now the screen is doing a mime act.

## Visual Problems To Fix
- Latest desktop screenshots for Draft Room, Import Review, League Intel, and Model Audit all show only "Not found" on a blank white page.
- Latest visual QA reports "No Blocking Visual Bugs" while the captured evidence is visibly blocked; the inspection standard is failing its basic job.
- No primary table, decision summary, import review, roster state, model audit, or page identity is visible in the captured route screenshots.
- Route-level identity cannot be evaluated because the app content is absent; this blocks review of repeated headers, duplicate intro bands, stacked nav, or buried product surfaces.
- The blank route state destroys trust before the user reaches any deterministic formula or source-visible table.
- Mobile evidence is also unusable if it follows the same route failure pattern; the project cannot claim responsive readiness from these captures.
- The repair loop has drifted into unrelated or guardrail-failing file touches while the customer-facing evidence remains broken.

## Strongest Opportunities
- Make visual QA open the real Streamlit routes and fail loudly when the screenshot contains "Not found", mostly blank white space, or no table-like content.
- Use the first working screen to prove the product promise: official top five, forced release candidate, keep/drop/shop status, and confidence/source columns above the fold.
- Keep the UI sober and operational: dense tables, compact metrics, clear rank separation, and quiet filters.
- Put formula notes, data provenance, import diagnostics, and internal validation detail behind expanders, tabs, or side panels.
- Establish one consistent page shell: one title, one job-focused subtitle at most, one quiet nav layer, then the table.
- Treat Model Audit as a trust panel, not a blog page: formula inputs, expected outputs, fixture references, and pass/fail state.

## Priority Fix
Fix visual evidence routing before touching page polish. The next implementer should make one narrow change that ensures root, Import Review, Team, War Board, Trade Central, Draft Room, League Intel, and Model Audit screenshots capture actual Streamlit content, then add a guard that fails if "Not found" appears. Until the screenshots show product tables, design review is theater.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: latest screenshots show Not found instead of command tables.

## Designer Handoff
Keep the mission: table-first, deterministic, low-text, source-visible, and local-first. Change the evidence path first, then reduce any visible chrome that competes with the actual decision table. The first screen should feel like a deadline command board: "who is protected, who is exposed, what changed, what can I act on." Keep formulas and provenance available, but make them secondary. The result should feel like a sharp internal war room tool, not a demo wrapper explaining itself and certainly not a blank page pretending it passed QA.

## What Not To Do Next
- Do not add new pages, cards, charts, or scenario controls before route evidence works.
- Do not redesign colors, typography, or spacing while screenshots still say "Not found".
- Do not touch backend scope, data packs, dependencies, auth, deployment, or generated output for this design repair.
- Do not accept automated visual reports that pass blank or missing pages.
- Do not bury the main command table under intro text, route wrappers, or duplicated headers once the pages render.
- Do not make the app feel like generic fantasy content; this is a deadline decision engine.

## Next 5 Design Tasks
- [ ] Fix the visual QA route map so each named Streamlit page screenshot loads real page content; guardrail: no product feature changes.
- [ ] Add a screenshot assertion that fails on "Not found", blank white captures, or missing table-like content; guardrail: keep it evidence-only.
- [ ] Verify one desktop and one mobile screenshot for Import Review after routing is fixed; guardrail: first screen must show the import/table job, not explanatory filler.
- [ ] Verify one desktop and one mobile screenshot for Draft Room after routing is fixed; guardrail: show pick value data and keep detail notes secondary.
- [ ] Audit the restored page shell for duplicate titles, repeated intro bands, and loud route chrome; guardrail: remove or quiet one repeated element only.

## Stop Or Continue
continue but fix visual issues first