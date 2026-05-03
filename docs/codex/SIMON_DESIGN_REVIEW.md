# Simon Design Review

## Verdict
RED

## One-Sentence Read
The latest visual evidence is not a command center, it is a white page saying "Not found", which is less war room and more unlocked broom closet.

## Mission Fit
The intended direction still fits the mission: table-first, deterministic, local-first, formula-visible Streamlit tooling for drop deadline decisions. The current visible result does not fit the mission because the inspected routes do not render the product at all. A fantasy decision engine cannot be judged as trustworthy, sortable, or mission-specific when Draft Room, Import Review, League Intel, and Model Audit all show a blank route failure.

## Taste Check
There is nothing premium, modern, or current to reward in the latest screenshots because the app surface is absent. The taste issue is not color, spacing, typography, or SaaS genericness yet. The visible product fails before hierarchy starts: tiny default "Not found" text on a white canvas, no app frame, no navigation, no tables, no owner-facing decision context. Automated visual QA saying "No Blocking Visual Bugs" while the screenshots show "Not found" is especially troubling; the evidence system is grading the restaurant while standing outside a locked door.

## Visual Problems To Fix
- The latest desktop screenshots for Draft Room, Import Review, League Intel, and Model Audit all render only "Not found" in the upper-left corner.
- The product pages are not visible, so the user cannot access the primary V1 jobs: import review, draft pool pressure, pick values, league pressure, or model audit.
- There is no command hierarchy on the captured routes: no title, no table, no data state, no filters, no action controls, no proof of loaded local snapshot.
- The visual QA report claims no blocking visual bugs despite route-level failure screenshots, so the design review cannot trust the current visual gate.
- Repeated page identity cannot be meaningfully inspected because the actual page chrome does not render; this remains unresolved until real pages are visible.
- The branch is still spending design-review cycles on recovery evidence instead of improving the table-first command surface.

## Strongest Opportunities
- Restore route rendering first, then make the first screen a dense command table with the single most important decision visible above the fold.
- Add a quiet but persistent command header that identifies the active snapshot, roster declaration context, and decision deadline without becoming a marketing banner.
- Use status chips sparingly for KEEP, DROP, SHOP, RELEASE RISK, and PRESSURE so the table communicates urgency without turning into a dashboard carnival.
- Make formula provenance reachable through row details or a side panel, not stacked explanatory text on the main screen.
- Tighten visual QA so "Not found", blank white screens, and missing tables are treated as hard failures before any design polish is considered.

## Priority Fix
Fix the visual route evidence path and page routing before touching layout polish. Nami should create one narrow repair task that makes the inspected Streamlit routes render real app content on desktop and mobile, then fails the visual check if the capture contains "Not found" or lacks the expected page heading/table. Until that is true, no amount of hierarchy tuning matters.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: latest screenshots show route failure instead of command tables.

## Designer Handoff
Next batch should be pure recovery, not decoration. Keep the product ambition: a restrained, table-first war room for one owner making keeper/drop and trade decisions from local data. Change only what is necessary to make the inspected routes render the actual pages and make visual QA catch this failure. Once pages are visible again, keep the UI compact, source-aware, and analytical: tables first, formula details behind expanders or side panels, no broad hero areas, no generic SaaS cards, no new sections pretending to be progress. The user should feel they opened a decision terminal, not a brochure and not a broken link.

## What Not To Do Next
- Do not add new feature pages while existing inspected pages render "Not found".
- Do not redesign colors, icons, cards, or spacing before route rendering is fixed.
- Do not accept visual QA that passes blank or "Not found" screenshots.
- Do not broaden scope into backend, architecture, package changes, or data model work.
- Do not add explanatory wrappers or repeated intro bands to compensate for missing page content.
- Do not hide the core table behind dashboards, summary prose, or decorative metrics.
- Do not ignore mobile after desktop recovers; both captures must show real product content.

## Next 5 Design Tasks
- [ ] Repair the inspected Streamlit route mapping so Draft Room, Import Review, League Intel, and Model Audit render their real page content; guardrail: no new pages and no visual redesign.
- [ ] Add a visual QA assertion that fails on "Not found", mostly blank white screens, or missing expected page titles; guardrail: evidence-only change, no product logic changes.
- [ ] Verify each recovered route shows one primary table or explicit empty data state above the fold; guardrail: no marketing copy or hero treatment.
- [ ] Reduce first-screen chrome after routes recover by keeping only one page title and one quiet context row; guardrail: no duplicated title bands or repeated route labels.
- [ ] Move formula/detail explanations behind existing expanders or row details on one recovered page; guardrail: table remains the dominant first-screen object.

## Stop Or Continue
continue but fix visual issues first