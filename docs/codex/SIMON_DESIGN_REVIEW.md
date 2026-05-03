# Simon Design Review

## Verdict
RED

## One-Sentence Read
The product may be structurally useful underneath, but the current visual evidence is a blank white "Not found" page, which is not a command center, it is a locked door with bad typography.

## Mission Fit
The intended direction matches the mission: local-first, deterministic, table-first, and focused on drop-deadline decisions rather than generic fantasy content. The visible product does not currently prove that mission because the inspected routes for Draft Room, Import Review, League Intel, and Model Audit all render "Not found" instead of the actual Streamlit surfaces. Until the user can see the import review, roster pressure, draft value, and audit tables, the design cannot be judged as a functioning V1 command center.

## Taste Check
There is no meaningful premium or modern visual layer visible in the latest screenshots. The only visible artifact is a tiny default "Not found" label on a blank white canvas, which reads like broken route plumbing, not restrained analytical software. For this mission, restraint is good; invisibility is not restraint, it is failure with confidence.

## Visual Problems To Fix
- The latest desktop screenshots for Draft Room, Import Review, League Intel, and Model Audit all show only "Not found" in the upper-left corner.
- The primary product surfaces are absent, so the user cannot reach the table-first decision workflow.
- Visual QA says "No Blocking Visual Bugs" while screenshots show route failure; the review loop is currently trusting the wrong signal.
- There is no visible page identity, table hierarchy, filter region, or decision state in the captured routes.
- The blank page makes every route feel like a dead end rather than a command center.
- Repeated page identity cannot be fully inspected because the routes do not render real product content; confidence in header, intro, and route chrome quality is therefore lower.

## Strongest Opportunities
- Fix route capture and page rendering first, then judge actual hierarchy instead of reviewing an error state.
- Make the first loaded screen a dense command table with a compact status strip, not explanatory prose.
- Keep Official Rank, Market Rank, War Room Rank, and My Rank visibly separate as first-class columns.
- Use small, plain confidence and source markers so the tool feels auditable without becoming a dashboard circus.
- Push formula explanations, import diagnostics, and long notes behind expanders or side panels.

## Priority Fix
The single most important design problem is that the inspected routes render "Not found" instead of the product. Nami should make one narrow repair to the visual QA route mapping or Streamlit navigation path so each captured URL lands on actual app content, then add a guard that fails the visual check when "Not found" appears. Do not style anything before this is fixed; lipstick needs a face.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: latest screenshots show Not found instead of product pages.

## Designer Handoff
Next implementer: restore visible route evidence before touching layout polish. The target result is simple: opening Draft Room, Import Review, League Intel, and Model Audit in visual QA must show the actual Streamlit page with its main table or audit content above the fold. Keep the table-first, low-text direction. Keep explanations tucked behind expanders. Change only the navigation or capture path needed to remove the broken blank state. The user should feel, immediately, "I can inspect the data and make a keeper decision."

## What Not To Do Next
- Do not add new pages or features while the existing routes render "Not found".
- Do not redesign colors, cards, typography, or dashboards before the app is visible.
- Do not trust an automated "no visual bugs" report when screenshots show route failure.
- Do not add more explanatory wrappers to compensate for missing content.
- Do not touch backend scope, auth, APIs, deployment, analytics, or package files.
- Do not expand into flashy prediction UI or scenario theatrics.

## Next 5 Design Tasks
- [ ] Fix one visual QA route so Import Review renders real Streamlit content instead of "Not found"; guardrail: no backend or feature changes.
- [ ] Apply the same route mapping pattern to Draft Room, League Intel, and Model Audit; guardrail: only navigation or capture configuration changes.
- [ ] Add a visual check that fails if captured page text includes "Not found"; guardrail: do not create false positives for normal empty data states.
- [ ] Re-run desktop and mobile screenshots for the four affected pages; guardrail: verify the first screen contains a table, audit panel, or import review content.
- [ ] Once routes render, remove one repeated or oversized page header if visible; guardrail: reduce chrome only, do not add new sections.

## Stop Or Continue
continue but fix visual issues first