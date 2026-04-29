# Simon Design Review

## Verdict
RED

## One-Sentence Read
The product direction is right, but the latest visual evidence is a white "Not found" page, so the design cannot be trusted yet.

## Mission Fit
The branch is advancing the mission on substance: deterministic formulas, auditability, local sample data, and table-first Streamlit pages all support the Drop Deadline Command Center. The problem is evidence. A command center that screenshots as "Not found" is not a command center, it is a locked door with a clipboard taped to it.

## Taste Check
The best current taste move is discipline: no fantasy-blog theatrics, no generic sports dashboard gloss, no live API dependency, and an emphasis on formula provenance. That is correct for this product.

What feels off is the visual QA story. The reported screenshots for Draft Room, Import Review, League Intel, Model Audit, and root appear to show only a blank white page with "Not found" in the upper left. That is not a small polish concern. It means the design review is judging intent and source structure more than the visible product. Confidence is lower because the available screenshots do not show the actual UI.

## Visual Problems To Fix
- Latest visual screenshots do not show the app; they show a white "Not found" page, which makes the visual bug report's "No Blocking Visual Bugs" verdict unreliable.
- Customer-facing route evidence is currently unusable, so layout, density, hierarchy, table behavior, and mobile responsiveness cannot be verified.
- The root page source still has a title, caption, subheader, and explanatory sentence before the product work starts; if this appears in the real UI, it risks repeated page identity and generic wrapper chrome.
- Streamlit default page titles and captions are likely doing too much identity work without enough command hierarchy.
- The Model Audit page source uses prose-heavy explanatory text and multiple full-width tables; useful, but visually likely closer to documentation than an audit console.
- Draft Room has three metrics, three controls, a subheader, a table, and an expander in a standard Streamlit stack; functional, but not yet visually sharp.
- The primary decision state is not clearly evidenced above the fold: forced release, top-five pressure, action labels, and confidence should scan immediately.
- Rank separation is mission-critical, but screenshots do not prove Official Rank, Market Rank, War Room Rank, and My Rank are visually distinct.
- Mobile table behavior is not proven; wide analytical tables can become useless if the key columns are not protected.
- Automated visual QA missed an obvious "Not found" screenshot state, so the inspection process itself needs a guardrail.

## Strongest Opportunities
- Make visual verification real before more feature work: every route screenshot must show the actual Streamlit page, not a routing failure.
- Turn the Team page into the command anchor: official top five, exposed player, forced release candidate, and next action visible immediately.
- Give action states a restrained system: Keep, Drop, Shop, Shield, Watch, Error, Warning, with clear severity and no carnival colors.
- Use column order as design: player, action, official status, keeper score, drop score, confidence, rank columns, then details.
- Make Model Audit feel like an evidence room: compact formula registry, status, code path, input set, and test status, with prose hidden behind expanders.
- Add a single quiet route header pattern across pages so the product never looks buried inside repeated wrapper labels.
- Treat Import Review as a severity board: blockers first, warnings second, clean rows last.

## Priority Fix
Fix the visual evidence pipeline and route loading before any design polish. Nami should make the screenshot run prove that root, Import Review, Team, War Board, Trade Central, Draft Room, League Intel, and Model Audit render actual app content on desktop and mobile, and the visual check must fail if the screenshot contains "Not found" or mostly blank white space. Until that is true, every design score is theater.

## Magic Improvement Score
SCORE: 2; DIRECTION: flat; ACTIVE_PACK: none; REASON: formula work improved trust, but visual evidence is invalid and the current UI cannot be judged.

## Designer Handoff
Keep the table-first, local-first, low-text product posture. Do not chase a prettier skin yet. First, repair the route/screenshot evidence so the team can see the real product. Then tighten hierarchy page by page: one quiet title, one decision strip where needed, one dominant table, restrained badges for actions and severity, and side panels or expanders for long explanations. The user should feel like the app is a serious deadline desk that surfaces the decision immediately, not a Streamlit notebook wandering through football math.

## What Not To Do Next
- Do not add more pages while screenshots show "Not found".
- Do not trust the automated visual bug report until it catches blank or failed route states.
- Do not add dashboards, prediction cards, or persuasive narrative insight before formula evidence is visible.
- Do not add more explanatory copy to compensate for weak hierarchy.
- Do not make broad style changes before route rendering and screenshots are reliable.
- Do not hide the forced-release answer below secondary tables.
- Do not collapse distinct rank concepts into one generic ranking column.
- Do not ignore mobile just because this is a private local tool.

## Next 5 Design Tasks
- [ ] Add a visual QA guard that fails when any route screenshot contains "Not found" or is mostly blank; do not change product UI in this task.
- [ ] Recapture desktop and mobile screenshots for all Streamlit routes; verify each screenshot shows real app content before marking visual QA green.
- [ ] Remove repeated or low-value wrapper copy from the root and page headers; keep one quiet page identity and no duplicate intro band.
- [ ] Rework the Team first viewport around official top five, forced-release candidate, and action status; keep it table-first and under two short visible copy lines.
- [ ] Tighten Model Audit into a compact formula registry with status, equation, inputs, output, code path, and test evidence; move explanatory prose behind expanders.

## Stop Or Continue
continue but fix visual issues first