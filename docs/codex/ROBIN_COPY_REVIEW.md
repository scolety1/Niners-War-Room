# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is disciplined, local-first, and mostly trustworthy, but some labels still lean toward command-room theater instead of plain analytical software.

## Mission Voice Fit
The language generally matches the mission: private, deterministic, table-first, and built for one fantasy football owner making Roster Declaration Day decisions. The strongest copy uses concrete nouns like "official top five", "keeper pressure", "pick value", "trade board", "import errors", and "model audit." That language is useful, specific, and not generic fantasy advice.

The weaker edge is naming. "War Room", "Command Center", "Trade Central", and "League Intel" are clear enough in context, but together they can make the app sound more dramatic than the mission requires. This is acceptable for a private tool, but the visible UI should keep the drama in page names and keep table labels sober: source, rank, score, confidence, assumption, why.

## Delicate Wording Risks
- "decision engine" can imply advice or authority if the UI does not keep computed outputs, assumptions, and confidence visible.
- "Which top-five player should be released" is useful internally, but customer-facing or visible app copy should soften toward "default release candidate" or "release pressure" unless the rule outcome is fully shown.
- "Which trade options can save value" risks overclaiming. A deterministic model can identify value gaps, not guarantee saved value.
- "likely to enter the draft pool" is acceptable if backed by rules and assumptions, but should appear near confidence/source context.
- "AcceptanceChance" can imply prediction. Prefer "Acceptance Estimate" or "Acceptance Heuristic" if the model is rule-based and uncalibrated.
- "POLITICAL RISK" is vivid and useful for this private tool, but it needs a concrete definition in detail copy so it does not feel like vague drama.
- "Magic Scorecard" sounds too cute for an analytical quality gate. It is probably internal, but if visible to users, rename or hide it.
- "Autopilot" language in docs may imply unattended judgment. Keep it internal and avoid surfacing it in product copy.
- "repair active pack before fresh work", "handoff", "workflow", "manager-ready", and similar builder-language patterns should stay out of the app UI. They are fine in internal docs only.
- "recommendations" should be used carefully. In the app, prefer "model label", "computed label", or "review label" when the user must make the final decision.

## Beautiful Language Opportunities
- Replace broad promise language with precise product nouns: "release pressure", "keeper count", "rank source", "pick curve", "trade gap", "model audit."
- Make every scenario or trade label show what changed, what stayed fixed, and what formula produced the result.
- Use "why" panels for long explanations, but keep first-screen labels short and concrete.
- Rename any visible "chance" or "likely" labels to show humility unless calibration is proven.
- Strengthen trust copy around rank separation: Official Rank, Market Rank, War Room Rank, and My Rank should always read as different sources, not competing truths.
- Use restrained urgency. "Deadline board" works better than language that sounds like fantasy advice theater.

## Priority Rewrite
The most important wording problem is analytical certainty. Any visible copy that says or implies "should", "save value", "likely", or "chance" needs nearby source, assumption, confidence, or "model output" language. Nami should audit the first-screen tables and replace advice-like labels with computed-output labels, while keeping the final decision clearly in the owner's hands.

## Suggested Rewrites
- Before: "Which top-five player should be released if nothing changes?"
  After: "Which top-five player is the default release candidate if nothing changes?"

- Before: "Which trade options can save value before Roster Declaration Day?"
  After: "Which trade ideas show a value gap before Roster Declaration Day?"

- Before: "Which players are likely to enter the draft pool?"
  After: "Which players are projected into the draft pool under current assumptions?"

- Before: "AcceptanceChance"
  After: "Acceptance Heuristic"

- Before: "recommendations"
  After: "model labels"

- Before: "Trade Central"
  After: "Trade Board"

- Before: "League Intel"
  After: "Keeper Pressure"

- Before: "Do not use generated AI text to make decisions."
  After: "Decision outputs must come from deterministic formulas, not generated text."

## Voice Rules
- Use concrete football and data nouns before metaphor: roster, rank, keeper, drop, pick, trade, source, score, confidence.
- Keep the first screen operational: short labels, tables first, explanations behind expanders or detail panels.
- Do not write like a fantasy advice blog. Avoid guru language, certainty, hype, and prediction theater.
- Separate computed output from owner judgment. Use "model output", "computed label", "assumption", "source", "confidence", and "why."
- Treat "chance", "likely", "best", and "should" as sensitive words that need visible support.
- Keep internal builder terms out of the app UI.
- Preserve the four rank lanes exactly: Official Rank, Market Rank, War Room Rank, My Rank.
- Prefer "default release candidate" over "player to release" unless the rule result is final and auditable.

## Next 5 Copy Tasks
- [ ] Audit visible page titles and table headings for advice-like certainty; guardrail: change labels only, no formula or layout changes.
- [ ] Replace visible "chance" language with "heuristic" or "estimate" where calibration is not proven; guardrail: do not invent calibration claims.
- [ ] Add or tighten one short "why" label for trade outputs; guardrail: keep explanation behind the existing detail action.
- [ ] Review all visible uses of "recommendation" and decide whether "model label" is more accurate; guardrail: preserve user-facing clarity.
- [ ] Check that every scenario or what-if control names the changed input and fixed assumptions; guardrail: no new controls or backend changes.

## Stop Or Continue
continue but fix copy first