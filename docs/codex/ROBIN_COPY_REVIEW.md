# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is usefully restrained and mission-fit, but it still needs sharper separation between computed model output, user decisions, and internal repair language.

## Mission Voice Fit
The language mostly matches the mission: private, local-first, deterministic, table-first, and focused on the Niners co-owner's roster declaration decisions. The strongest copy uses concrete nouns like "official top five", "drop candidate", "pick value", "Trade Central", and "Model Audit". The weaker copy appears in review and repair artifacts, where phrases like "ship", "magic", "polish", "active pack", "quality quarantine", and "repair lane" sound like builder process rather than a buyer-facing decision tool. For an analytical fantasy command center, the app should sound calm, exact, and auditable, not like a product hype loop or a QA harness.

## Delicate Wording Risks
- "decision engine" is acceptable in technical docs, but customer-facing screens should avoid sounding like the app decides for the owner. Prefer "decision board", "model output", or "command table" when the user still makes the call.
- "recommendations" can overstate certainty unless paired with inputs, assumptions, confidence, or "model label".
- "Which trade options can save value" risks implying certain outcomes. Prefer "which trade options may protect value under the current model".
- "AcceptanceChance" is potentially overconfident if it is not calibrated against real league history. Label it as a modeled estimate or heuristic score.
- "likely to enter the draft pool" should be staged carefully as "projected draft pool" or "model-flagged release candidates" unless the app shows why.
- "Magic Scorecard" is too cute for this analytical product and undercuts trust.
- "War Score" and "War Room Rank" fit the brand, but should not crowd out precise rank names. Keep Official Rank, Market Rank, War Room Rank, and My Rank visibly separate.
- Repair language such as "ship", "quarantine", "active pack", "repair lane", "polish", and "handoff" belongs in internal docs only, not app screens.
- "No Blocking Visual Bugs" conflicts with Simon evidence reporting "Not found" screenshots. This wording sounds falsely conclusive and should be softened or made conditional.
- "External build passed" is clear for internal reports, but it is not useful buyer-facing copy.
- "private score" needs a visible definition near audit/detail views so it does not sound like hidden judgment.

## Beautiful Language Opportunities
- Make the first screen more concrete: "Niners Top Five", "Default Release", "Keeper Pressure", and "Trade Leverage" are stronger than broad explanation.
- Use "Model Audit" to build trust with labels like "Formula", "Inputs", "Output", "Confidence", "Source", and "Assumption".
- Replace hype words with accountable words: "computed", "loaded from", "official", "manual rank", "market rank", "sample pack", "last import".
- Give trade copy a manual-review posture: "Review", "Shop", "Shield", "Hold", and "Offer Candidate" are better than confident advice.
- Use compact status language on import pages: "Loaded", "Warning", "Error", "Missing rank", "Duplicate pick", "Unknown team".
- Stage explanations behind expanders with labels like "Why this score", "Inputs used", and "League rule".
- The mission phrase "Drop Deadline Command Center" is strong. Keep it, but pair it with tables rather than long prose.

## Priority Rewrite
The single most important wording problem is analytical certainty. Any label that sounds like advice, prediction, or guaranteed trade outcome should be reframed as deterministic model output with visible assumptions. Nami should scan app-visible labels and docs summaries for words like "save", "likely", "recommendation", "chance", and "decision engine", then rewrite them so the owner sees what was computed, from which inputs, and where manual judgment remains required.

## Suggested Rewrites
- Before: "Which trade options can save value before Roster Declaration Day?"
  After: "Which trade options may protect roster value before Roster Declaration Day?"

- Before: "Which players are likely to enter the draft pool?"
  After: "Which players are model-flagged as possible draft-pool entries?"

- Before: "AcceptanceChance"
  After: "Acceptance estimate"

- Before: "No Blocking Visual Bugs"
  After: "Automated visual check found no blocking issues in captured pages"

- Before: "Private, local-first fantasy football decision engine"
  After: "Private, local-first fantasy football command board"

- Before: "Review keeper/drop recommendations"
  After: "Review keeper, drop, and shop labels"

- Before: "Do not use generated AI text to make decisions."
  After: "Do not use generated AI text as model output."

- Before: "Magic Scorecard"
  After: "Ship Scorecard" or "Quality Scorecard"

## Voice Rules
- Use concrete table labels before explanatory copy.
- Keep first-screen copy short: title, status line, primary table.
- Separate model output from advice.
- Pair scores with source, assumption, confidence, or "why" when space allows.
- Keep Official Rank, Market Rank, War Room Rank, and My Rank as distinct visible terms.
- Use "projected", "model-flagged", "computed", and "current snapshot" instead of certainty language.
- Keep repair, QA, and builder-process language out of app-visible copy.
- Avoid hype, fantasy-blog voice, guru language, and playful quality names.
- Prefer "review", "compare", "filter", "audit", and "select" as user actions.
- Hide long explanations behind "Why this score" or "Inputs used".

## Next 5 Copy Tasks
- [ ] Audit app-visible labels for prediction language; guardrail: rewrite only labels that imply certainty, and do not change formulas or data.
- [ ] Rename any customer-facing "AcceptanceChance" display to "Acceptance estimate"; guardrail: keep internal code identifiers unchanged unless already exposed.
- [ ] Add or tighten one Model Audit detail label to show "Inputs", "Output", "Confidence", or "Source"; guardrail: no new model claims.
- [ ] Replace one vague repair or QA phrase in docs with concrete evidence language; guardrail: internal docs only, no app behavior change.
- [ ] Review the first screen for staged copy; guardrail: keep only the current page job, one status line, and table-first labels visible.

## Stop Or Continue
continue but fix copy first