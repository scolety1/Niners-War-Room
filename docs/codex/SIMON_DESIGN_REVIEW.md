# Simon Design Review

## Verdict
RED

## One-Sentence Read
The latest visual evidence is not a command center, it is four blank white pages saying "Not found", which is not a design issue so much as the product leaving the room.

## Mission Fit
The intended direction still matches the mission: local-first, deterministic, table-first fantasy football decision support for drop-deadline choices. The current visible evidence does not match the mission because the primary routes do not render the command tables at all. A V1 Drop Deadline Command Center must immediately show import review, roster pressure, draft/pick value, league intel, or model audit surfaces; the latest screenshots show none of that.

## Taste Check
There is no premium or modern surface to evaluate in the latest screenshots. The only visible design is default white browser space with tiny monospace "Not found" text in the corner. That reads like broken routing, broken QA capture, or both. Earlier notes suggest real command pages briefly returned, but the current evidence has regressed below generic SaaS into absent product.

## Visual Problems To Fix
- The latest Import Review desktop screenshot renders only "Not found" instead of the import validation table.
- The latest Draft Room desktop screenshot renders only "Not found" instead of pick values, draft pool, or pick curve context.
- The latest League Intel desktop screenshot renders only "Not found" instead of keeper pressure or team comparison data.
- The latest Model Audit desktop screenshot renders only "Not found" instead of formula/source audit evidence.
- The visual QA report says "No Blocking Visual Bugs" while the screenshots are visibly broken; that evidence mismatch is itself a blocker.
- The first screen has no hierarchy, no command table, no current decision, no state, and no recovery affordance.
- Repeated page identity cannot be assessed because the customer-facing route content is missing entirely; this is worse than double headers.

## Strongest Opportunities
- Restore reliable route rendering before touching layout polish.
- Make each first screen open on one mission-critical table, not a page intro.
- Add a compact status strip only after the table is visible: data pack, snapshot date, rule config, and validation state.
- Use tight table hierarchy: stronger column grouping, sober status badges, frozen identity columns, and low-noise numeric emphasis.
- Put formula explanations, source notes, and model audit details behind side panels or expanders so the command surface stays fast.

## Priority Fix
Fix the visual evidence and route rendering path so the latest screenshots show real Streamlit command pages, not "Not found". Nami should make one narrow repair: verify the screenshot harness is opening the correct Streamlit routes for Import Review, Draft Room, League Intel, and Model Audit, then fail the visual check if any captured page contains "Not found" or mostly blank white space. No visual polish until the product is visible. The tuxedo can wait; the guest is currently locked outside.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: latest screenshots show "Not found" instead of the command tables.

## Designer Handoff
Next batch should be evidence-first and ruthless. Keep the table-first Streamlit direction, the local data posture, and the deterministic audit surface. Change only the route/capture failure that prevents the real pages from appearing, then confirm the first viewport on each route shows the primary job: import review table, draft value table, league pressure board, or model audit table. The user should feel like the war room is back online, not like they are reading a broken QA artifact.

## What Not To Do Next
- Do not add new sections, dashboards, cards, charts, or decorative styling.
- Do not redesign the app shell while the routes still capture as "Not found".
- Do not treat the automated "No Blocking Visual Bugs" report as credible until it catches this failure.
- Do not expand backend, data model, auth, deployment, package, or architecture scope.
- Do not bury the first screen under explanations once the routes render again.
- Do not ignore mobile after desktop is fixed; mobile must show usable command content, not blank route failure.

## Next 5 Design Tasks
- [ ] Repair the visual QA route targets so latest screenshots render real Streamlit pages; guardrail: no UI redesign or new pages.
- [ ] Add a screenshot assertion that fails on "Not found" or mostly blank white pages; guardrail: evidence-only change.
- [ ] Verify Import Review first viewport shows the import validation table before any explanatory copy; guardrail: no added feature text.
- [ ] Verify Draft Room first viewport shows pick/player value data with clear column hierarchy; guardrail: no charts unless already present.
- [ ] Verify Model Audit keeps formula/source detail behind expanders or panels after the audit table renders; guardrail: progressive disclosure only.

## Stop Or Continue
continue but fix visual issues first