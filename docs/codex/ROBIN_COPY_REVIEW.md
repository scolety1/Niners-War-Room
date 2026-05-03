# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is mostly disciplined and mission-fit, but it still leans on internal process language where the product should speak in concrete decision terms.

## Mission Voice Fit
The language matches the mission when it stays close to the owner job: official top five, forced release, keep, drop, shop, trade value, league pressure, pick values. It is strongest in the mission and model docs, where the product is framed as deterministic, local-first, and table-first instead of a fantasy advice blog. The weaker voice appears in repair and review copy, where phrases like "active work pack", "handoff", "polish", "workflow", and "pause ship" sound like builder instructions rather than useful app language.

## Delicate Wording Risks
- "Decision engine" is acceptable in docs, but in visible UI it may sound more confident than the deterministic model can support unless paired with "model output", "assumptions", or "source".
- "Recommendations" can imply advice. Prefer "labels", "model output", or "review list" where the app is calculating rather than deciding.
- "Which trade options can save value" risks overclaiming outcome. The app can show value gaps and keeper impact, not guarantee saved value.
- "Which players are likely to enter the draft pool" needs humility. Use "projected" or "flagged by current inputs" near the table.
- "AcceptanceChance" is risky if shown without assumptions; it can read like prediction theater. It needs source and formula context.
- "War Score" and "War Room Rank" fit the project name, but should not bury the difference between official rank, market rank, private rank, and computed score.
- Repair copy such as "pause ship and inspect results", "active work pack", "blocker-clearing repair", and "preserve prior product phase" is internal and should never appear in the working app.
- "Route diagnostics", "runtime source paths", and "visual evidence" are useful developer language, but should be behind diagnostics, not first-screen product copy.
- "Ready for service", "handoff", "workflow", "polish", and "manager-ready" were not found in the public-copy smoke hits, but should remain forbidden for visible app copy unless the reader, action, and outcome are concrete.

## Beautiful Language Opportunities
- Rename first-screen labels around the user's decisions, not the system: "Official Top Five", "Default Release", "Keep", "Shop", "Drop", "Pick Value".
- Replace broad system nouns with concrete table nouns: "Keeper Pressure Board", "Draft Pool Watch", "Trade Value Gaps", "Source Snapshot".
- Add short assumption labels near scenario and model outputs: "Current snapshot", "Configured league rule", "Formula output", "Manual review needed".
- Keep explanatory copy terse and staged behind expanders, especially formula details and import diagnostics.
- Make uncertainty visible without making the app feel weak: "flagged", "projected", "current inputs", "low confidence", "missing source".
- Use sharper page subtitles that answer "what do I do here?" without sales language.

## Priority Rewrite
The most important wording problem is the gap between computed output and advice. Nami should audit visible labels and helper text for words like "recommendation", "likely", "chance", "save value", and "decision engine", then revise them so every model-driven claim names the output, source, and assumption level. The app should feel decisive about showing the math, not falsely certain about football outcomes.

## Suggested Rewrites
- Before: "Which trade options can save value before Roster Declaration Day?"
  After: "Which trade ideas improve keeper value under the current snapshot?"

- Before: "Which players are likely to enter the draft pool?"
  After: "Which players are projected as draft-pool candidates from current keeper pressure?"

- Before: "Display deterministic scores and recommendations."
  After: "Display deterministic scores, labels, and review flags."

- Before: "AcceptanceChance"
  After: "Acceptance Estimate"

- Before: "Drop Deadline Command Center"
  After: "Drop Deadline Board"

- Before: "private local-first fantasy football decision engine"
  After: "private local-first roster and trade board"

- Before: "Recommendation labels"
  After: "Model labels"

## Voice Rules
- Use concrete football and roster nouns before system nouns.
- Separate computed output from advice: show formula, source, confidence, and assumption when a label could affect a roster decision.
- Keep first-screen copy short; move formula detail, diagnostics, and repair context behind expanders.
- Do not use sales language inside the working app.
- Do not imply prediction certainty. Use "projected", "flagged", "estimated", or "current snapshot" when the model depends on assumptions.
- Keep Official Rank, Market Rank, War Room Rank, and My Rank visibly separate in language and tables.
- Avoid internal process words in user-facing UI: workflow, handoff, polish, active pack, route evidence, blocker, ship.
- Prefer labels a co-owner can act on in one scan: Keep, Shop, Drop, Shield, Review, Low Confidence.

## Next 5 Copy Tasks
- [ ] Audit visible Streamlit page titles and subtitles for internal process language; replace only with concrete roster, trade, draft, or import nouns.
- [ ] Rename any visible "recommendation" copy to "model label" or "review flag" unless a human action is clearly stated nearby.
- [ ] Add assumption labels beside "Acceptance Estimate", projected draft-pool, and keeper-pressure outputs; keep each label under 8 words.
- [ ] Review first-screen copy for staging; move diagnostics, file paths, and formula explanations behind existing expanders or detail controls.
- [ ] Check rank and score labels for separation; do not let Official Rank, Market Rank, War Room Rank, My Rank, and War Score collapse into one vague value claim.

## Stop Or Continue
continue but fix copy first