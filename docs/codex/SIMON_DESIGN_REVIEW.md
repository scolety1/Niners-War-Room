# Simon Design Review

## Verdict
YELLOW

## One-Sentence Read
The app is finally pointing at the right mission, but the surface still feels like Streamlit wearing a draft-room badge instead of a disciplined command center.

## Mission Fit
The direction matches the V1 mission better than before: table-first pages, model audit, import review, draft room, league intel, and deterministic service-backed views all belong in a local-first drop deadline tool. The strongest mission fit is the separation of operational surfaces: import, roster/team, war board, trade, draft, league pressure, and audit. The weak spot is presentation discipline. A command center should make the next decision obvious in the first viewport; this still risks reading as a collection of pages rather than one urgent owner workflow.

## Taste Check
The premium part is the restraint: no fake fantasy-magazine hero, no prediction theater, no glossy dashboard nonsense. Good. The Model Audit page is also a correct instinct because this product earns trust through formula visibility, not vibes.

What feels generic is the default Streamlit rhythm: stacked page headers, explanatory copy blocks, similar table sections, and likely too many equal-weight controls. The design needs less "here is a page about the thing" and more "this is the answer, here is the evidence, now decide." Right now the suit is tailored, but the shirt is still from the conference swag bag.

## Visual Problems To Fix
- Page identity appears too repetitive across routes: each page risks opening with the same title-plus-intro pattern before the user reaches the actual command table.
- Route chrome and page headers appear to compete with the working surface instead of quietly orienting the user.
- The primary decision on each page is not visually loud enough: "release risk", "keep/drop/shop", "trade shield", and "league pressure" should win the first scan.
- Tables likely carry too much equal-weight data at once; rank, score, confidence, and action labels need a clearer visual order.
- Audit and helper explanation content should stay behind expanders, drawers, or tabs; it must not dilute the first-screen decision surface.
- The prior "Not found" visual evidence loop was mission-breaking. Latest report says no blocking visual bugs, but the QA system needs to keep proving real command pages, not blank routes.
- Mobile screenshots are listed, but the product still needs deliberate mobile hierarchy: fewer columns, stronger row summaries, and no header stack before the useful table.

## Strongest Opportunities
- Make every route start with a compact command strip: one page title, one primary table/action area, and only the 2-3 most important status metrics.
- Give action labels a sober but decisive treatment: KEEP, DROP RISK, SHOP, HOLD, OFFER, AVOID should be scannable without becoming carnival badges.
- Use progressive disclosure aggressively: formulas, import caveats, source provenance, and long explanations belong behind "Audit", "Why", or "Details".
- Create a consistent rank comparison pattern for Official Rank, Market Rank, War Room Rank, and My Rank so the owner can see disagreement instantly.
- Turn Model Audit into the trust anchor: source, formula, inputs, output, confidence, and test status in a compact table-first layout.

## Priority Fix
Reduce page chrome before adding anything else. Each customer-facing app route should have exactly one compact page identity area, then the primary decision table or board immediately. Remove duplicate intro bands, repeated labels, oversized explanatory blocks, and any wrapper panel that makes the actual command surface feel buried. Nami should make the first viewport answer the route's one job before exposing details.

## Magic Improvement Score
SCORE: 3; DIRECTION: improved; ACTIVE_PACK: none; REASON: current evidence suggests real command pages are back, but hierarchy is still too generic and not yet command-center sharp.

## Designer Handoff
Keep the table-first analytical spine, the deterministic audit posture, and the quiet visual language. Change the first-screen hierarchy: one compact route header, one urgent decision surface, one restrained control row, then details below or behind disclosure. The result should feel like a co-owner opening the app five minutes before a deadline and instantly seeing where the risk and leverage are.

## What Not To Do Next
- Do not add more pages or sections.
- Do not add prediction cards, big KPI theater, or fantasy advice prose.
- Do not make the UI more colorful to fake importance.
- Do not bury the main table under explanations about the model.
- Do not touch backend scope, data collection, auth, deployment, or packages.
- Do not ignore mobile; table-first does not mean desktop-only.

## Next 5 Design Tasks
- [ ] On each Streamlit page, reduce the top area to one title line plus one short status line; guardrail: no duplicate page title or intro block.
- [ ] Move long model/source explanations behind existing expanders or tabs; guardrail: first viewport must show the primary table or board.
- [ ] Standardize action labels across tables; guardrail: no new formula semantics, only visual/copy treatment.
- [ ] Create a compact rank comparison display for Official, Market, War Room, and My Rank; guardrail: keep all ranks separate and labeled.
- [ ] Review mobile screenshots and collapse low-priority columns into row details; guardrail: no horizontal wall of unreadable data.

## Stop Or Continue
continue but fix visual issues first