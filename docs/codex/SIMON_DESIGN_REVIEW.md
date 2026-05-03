# Simon Design Review

## Verdict
RED

## One-Sentence Read
The product mission is serious, but the current visual evidence is still a blank "Not found" wall, which is not a command center - it is a failed entrance.

## Mission Fit
The underlying direction matches the mission: local-first data, deterministic formulas, auditable model pages, table-first Streamlit surfaces, and separate decision boards are exactly right for a private fantasy football drop-deadline tool. But the visible product does not currently prove that direction. The latest screenshots for Draft Room, Import Review, League Intel, and Model Audit still render as "Not found", while the visual bug report says there are no blocking bugs. That mismatch is mission-breaking because this app is supposed to help a co-owner trust deadline decisions, not trust a report that missed a blank page.

## Taste Check
The good taste is in the restraint: no fake ESPN skin, no fantasy advice blog nonsense, no glossy dashboard theater, and no runtime API dependency. That is the right posture for analytical software.

The bad taste is operational and visible: the design review is being asked to judge pages that do not appear in screenshots. That is amateur-hour evidence handling. The source suggests a useful formula audit table and command-board pages, but the customer-facing visual output is currently a white screen with two words in the corner. Paris has bad cafe menus with more hierarchy than this.

## Visual Problems To Fix
- Current visual screenshots show "Not found" instead of real Streamlit pages across key routes, including Model Audit, Draft Room, Import Review, and League Intel.
- The automated visual bug report says "No Blocking Visual Bugs" even though the screenshots are route failures; the QA layer is visually blind.
- Because the screenshots are invalid, layout, spacing, density, first-screen hierarchy, table behavior, mobile usability, and route chrome cannot be trusted.
- The root page source uses title, caption, subheader, and explanatory copy before the product work starts; if rendered, it risks repeated identity instead of immediate command value.
- Model Audit source is useful but prose-heavy, with long explanatory text before and between tables; it risks feeling like documentation instead of an audit console.
- Formula status copy in Model Audit appears stale against the branch summary, saying several formulas are "queued for spec alignment" even though recent commits claim those formulas were implemented.
- There is no verified first-screen evidence that official top-five, forced release, keeper/drop action, confidence, and rank separation scan immediately.
- Rank separation is mission-critical, but the current visual evidence does not prove Official Rank, Market Rank, War Room Rank, and My Rank are visibly distinct.
- Mobile screenshots are also "Not found", so wide analytical tables may still be unusable on small screens without anyone noticing.
- The latest visible repair changed Model Audit, but the screenshot evidence still cannot reach that page.

## Strongest Opportunities
- Make route evidence real and unforgiving: every captured page should fail QA if it contains "Not found" or mostly blank white space.
- Make the Team page the actual command anchor: official top five, forced release candidate, keeper/drop action, and confidence should be the first readable block.
- Use table structure as the primary design language: player, action, official status, model score, confidence, rank columns, then secondary detail.
- Convert Model Audit from prose-first to registry-first: formula area, status, equation, inputs, output, code path, and test evidence in one dense table.
- Build one quiet page header pattern across all routes: title, data pack, one short operational subtitle if needed, then the main table.
- Use restrained severity badges for Keep, Drop, Shop, Shield, Watch, Error, and Warning; no rainbow dashboard cosplay.
- Push long explanations into expanders or detail drawers so the first screen stays operational.

## Priority Fix
Fix visual route capture before touching visual polish. Nami should create one narrow task that makes the visual QA run load root, Import Review, Team, War Board, Trade Central, Draft Room, League Intel, and Model Audit as real Streamlit content on desktop and mobile, then hard-fail when any screenshot contains "Not found" or mostly blank white space. Until that works, design scoring is ceremony without evidence.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: screenshots still show route failure while visual QA reports no blocking bugs.

## Designer Handoff
Keep the product severe, tabular, local, and low-text. Do not add new sections, decorative styling, or a broader dashboard. First, make the real pages visible in screenshot evidence. Then tighten the command hierarchy: one quiet header, one immediate decision surface, one dominant table, restrained status badges, and all formula explanations behind progressive disclosure. The user should feel like they opened a deadline desk built for decisions, not a Streamlit notebook explaining itself.

## What Not To Do Next
- Do not add more app pages while route screenshots still show "Not found".
- Do not trust the visual bug report until it catches route failures and blank screens.
- Do not add more explanatory copy to compensate for weak hierarchy.
- Do not make a cosmetic theme pass before the app can be visually inspected.
- Do not introduce dashboards, prediction cards, or strategy theatrics.
- Do not bury forced-release logic below secondary tables.
- Do not merge rank concepts into one generic ranking field.
- Do not ignore mobile table usability once screenshots are real.
- Do not change backend scope, data architecture, packages, auth, deployment, or external integrations.

## Next 5 Design Tasks
- [ ] Add a screenshot guard that fails on "Not found" or mostly blank white pages; guardrail: no product UI changes in this task.
- [ ] Recapture desktop and mobile screenshots for every Streamlit route; guardrail: each screenshot must show real app content before visual QA can pass.
- [ ] Remove duplicate or low-value wrapper copy from root and page headers; guardrail: keep one title and at most one short operational subtitle.
- [ ] Reframe Team first viewport around official top five, forced release candidate, and action status; guardrail: keep it table-first and avoid new cards-heavy layout.
- [ ] Tighten Model Audit into a compact formula registry with status, equation, inputs, output, code path, and test evidence; guardrail: move explanatory prose behind expanders.

## Stop Or Continue
continue but fix visual issues first