# Simon Design Review

## Verdict
YELLOW

## One-Sentence Read
The product is finally becoming a command center, but without screenshots the design confidence is low and the current Streamlit boards risk feeling like dressed-up dataframes instead of a sharp drop-deadline cockpit.

## Mission Fit
The direction matches the mission: table-first, deterministic, local-first, and focused on Niners roster pressure, official top-five logic, keeper/drop/shop decisions, and import validation. That is the right product spine. The risk is visual hierarchy: if every board looks equally important, the app will technically answer the right questions while making the owner hunt for the actual decision.

## Taste Check
The strongest taste move is restraint. This should not become a fantasy sports content site, and the branch appears to be staying close to command tables, validations, and decision boards. Good.

What feels undercooked is the lack of visual evidence and likely lack of hierarchy. Streamlit defaults can look competent for prototypes, but they rarely feel premium without disciplined spacing, column priority, status treatment, and a very clear "what should I do next" surface. If the War Room reads like a spreadsheet export with headings, that is not design, that is surrender in a hoodie.

## Visual Problems To Fix
- No screenshots were captured, so actual layout, density, mobile behavior, and visual regressions cannot be judged with high confidence.
- The app likely has too many equal-weight sections across Import Review, Team, and War Board, which weakens decision priority.
- Critical states like forced release, top-five shield, keep, drop, and shop need stronger visual treatment than plain table text.
- Long explanations are reportedly hidden, which is correct, but the visible summary still needs a tight decision signal before the user opens details.
- Import errors and warnings need clear severity grouping, not a flat list that makes warnings compete with blockers.
- War Board filters must feel like command controls, not incidental Streamlit widgets floating above a dataframe.
- The Niners official top five should be a first-screen anchor, not just another table section.
- Rank columns must stay visually distinct: Official Rank, Market Rank, War Room Rank, and My Rank cannot blur into one generic ranking soup.
- Mobile risk is unproven; wide tables can become unusable fast if key player, action, score, and rank columns are not protected.
- The quarantined polish pass suggests the design layer is still fragile and needs smaller, reviewable UI adjustments.

## Strongest Opportunities
- Create a single above-the-fold decision strip on the Team page: official top five, forced release candidate, keeper pressure count, and immediate action.
- Give every row an action classification with restrained but unmistakable visual language: Keep, Drop, Shop, Shield, Watch.
- Use table column ordering as design: player, team/status, action, keeper score, drop score, official rank, market rank, war room rank, my rank.
- Add severity badges for Import Review so blockers, warnings, and informational notes scan instantly.
- Make War Board feel like a trading desk: compact filters, dense table, pinned key columns, and side-panel detail instead of verbose page copy.
- Use consistent numeric formatting and alignment so scores and ranks feel analytical, not decorative.
- Add a lightweight page-level hierarchy system: one command header, one primary table, one secondary detail area.
- Capture desktop and mobile screenshots after every UI batch; design review without pixels is basically reading a menu without tasting the food.

## Priority Fix
Fix hierarchy on the Team and War Board pages before adding more surfaces. Nami should make the top decision visible within the first viewport: who is official top five, who is exposed, who is the forced-release candidate, and which players are Keep, Drop, or Shop. Keep the tables, but make the first row of meaning impossible to miss through column order, status badges, compact metrics, and restrained spacing.

## Magic Improvement Score
SCORE: 3; DIRECTION: improved; ACTIVE_PACK: none; REASON: mission-critical boards exist, but visual quality is unverified and polish failed quarantine.

## Designer Handoff
Treat the next batch as command-table hardening, not beautification. Keep the local-first Streamlit structure, the low-text posture, and the deterministic decision framing. Change the page hierarchy: each page gets one clear command header, one dominant table, severity/action badges, and side-panel detail for explanations. The user should feel like they opened a serious deadline tool that immediately tells them where the roster is bleeding value, not a generic analytics notebook with football names pasted in.

## What Not To Do Next
- Do not add more pages before the current boards have clear hierarchy.
- Do not add hero sections, marketing copy, decorative cards, or fantasy-blog flavor.
- Do not turn status logic into a rainbow badge festival.
- Do not hide the forced-release answer below secondary tables.
- Do not merge Official Rank, Market Rank, War Room Rank, and My Rank into one vague ranking concept.
- Do not expand backend scope, live data behavior, auth, deployment, or package surface.
- Do not ignore mobile table behavior just because this is a local command tool.
- Do not do another broad "polish pass"; make small visual fixes with screenshots.

## Next 5 Design Tasks
- [ ] Capture desktop and mobile screenshots for Import Review, Team, and War Board; do not change code in this task.
- [ ] Reorder Team page content so official top five and forced-release candidate are visible in the first viewport; keep copy under two short lines.
- [ ] Add consistent action/severity badges for Keep, Drop, Shop, Shield, Watch, Error, and Warning; avoid more than four dominant colors.
- [ ] Tighten War Board table columns around player, action, scores, and separated rank types; do not remove any required rank distinction.
- [ ] Move long player/model explanations into a side panel or expander pattern and keep the primary table dense and scannable.

## Stop Or Continue
continue but fix visual issues first