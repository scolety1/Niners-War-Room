# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is disciplined, local-first, and appropriately skeptical of fantasy advice theater, but several product labels still need sharper separation between computed model output and actionable owner judgment.

## Mission Voice Fit
The language mostly matches the mission: private, deterministic, table-first, and built for one fantasy football owner facing a deadline. The strongest copy uses concrete nouns like "official top five", "forced-release risk", "pick value table", "import errors", and "keeper pressure". The weaker copy appears where labels such as "recommendations", "trade options save value", "War Score", and "likely to enter the draft pool" could sound more certain than the underlying V1 model should claim.

## Delicate Wording Risks
- "recommendations" can imply advice rather than deterministic model output. Prefer "labels", "model labels", or "review flags" where the app is showing computed output.
- "Which trade options save value" sounds like a promise. The model can compare estimated value, but it cannot know whether a trade will save value in reality.
- "Which players are likely to enter the draft pool" risks prediction language. If this is based on keeper pressure and roster math, say that directly.
- "War Score" is distinctive, but it needs clear nearby support so it does not become a vague master score that hides Official Rank, Market Rank, War Room Rank, and My Rank.
- "AcceptanceChance" is risky if presented as a probability. It should be framed as a formula label or review band unless calibrated evidence exists.
- "POLITICAL RISK" is useful shorthand, but it may feel melodramatic unless defined as league-friction or owner-behavior risk.
- "private score" and "private value" are mission-fit, but visible UI should make clear they are local model outputs, not secret market facts.
- "confidence" should not read as certainty. It should stay tied to data completeness, agreement, and model separation.

## Beautiful Language Opportunities
- Replace advice-sounding headings with audit-friendly table labels: "Model Output", "Review Label", "Source", "Assumption", "Why".
- Make the root page sound like a serious deadline desk, not a generic app intro.
- Use the product's strongest nouns more often: "top-five release", "declaration deadline", "keeper pressure", "pick curve", "source snapshot".
- Put plain assumption labels near scenario controls: "Changed input", "Affected formula", "Held fixed".
- Tighten trade copy around review rather than persuasion: "candidate", "edge", "benefit", "risk band", "manual review".
- Give "War Room Rank" one clear definition in a side panel or expander so it does not blur into market or official rank.
- Convert "likely" language into "flagged by keeper pressure" or "projected by current snapshot".

## Priority Rewrite
The most important wording problem is prediction and advice language around trade and draft outcomes. Nami should replace visible phrases that imply the tool knows what will happen, such as "save value", "likely to enter", and "AcceptanceChance", with language that names the calculation and keeps the owner in charge: "estimated edge", "pressure flag", "review band", "model output", and "manual review required".

## Suggested Rewrites
- Before: "Which trade options save value before Roster Declaration Day?"
  After: "Which trade candidates show positive estimated edge before Roster Declaration Day?"
- Before: "Which players are likely to enter the draft pool?"
  After: "Which players are flagged as draft-pool candidates by current keeper pressure?"
- Before: "AcceptanceChance"
  After: "Acceptance Band"
- Before: "recommendations"
  After: "model labels"
- Before: "POLITICAL RISK"
  After: "League Friction Risk"
- Before: "War Score"
  After: "War Room Score"
- Before: "private score"
  After: "Private Model Score"
- Before: "Trade options can save value"
  After: "Trade candidates with estimated value edge"

## Voice Rules
- Keep the voice terse, specific, and audit-ready.
- Never make the model sound like a fantasy guru.
- Use "model output", "review label", "source", "assumption", "confidence", and "why" near computed values.
- Preserve separate language for Official Rank, Market Rank, War Room Rank, and My Rank.
- Avoid prediction verbs unless the formula and assumption are visible.
- Prefer "flagged", "estimated", "calculated", "current snapshot", and "manual review" over "knows", "will", "should", or "best".
- Keep UI copy table-first and low-text; move explanations into expanders or side panels.
- Use football language only when it clarifies the decision, not as decoration.

## Next 5 Copy Tasks
- [ ] Rename any visible "AcceptanceChance" label to "Acceptance Band" or "Acceptance Score"; do not present it as a calibrated probability.
- [ ] Review Trade Central headings and replace advice language with calculation language; keep each label under four words where possible.
- [ ] Add or verify one short side-panel definition for War Room Score; guardrail: it must not collapse Official Rank, Market Rank, War Room Rank, and My Rank.
- [ ] Replace visible "likely to enter the draft pool" copy with "draft-pool candidates by keeper pressure"; do not imply prediction beyond the current snapshot.
- [ ] Audit scenario controls for assumption labels; each what-if control should name the changed input, affected formula, and held-fixed outputs.

## Stop Or Continue
continue but fix copy first