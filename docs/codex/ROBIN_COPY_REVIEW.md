# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The copy is mission-fit, sober, and appropriately analytical, but several app and planning phrases still lean toward internal builder language instead of crisp owner-facing decision language.

## Mission Voice Fit
The language matches the product position well: private, local-first, deterministic, table-first, and built for one owner making deadline decisions. It avoids fantasy-blog hype and protects the difference between official rank, market rank, private model output, and user judgment. The best copy uses concrete nouns like "official top five", "default release", "keeper pressure", "pick values", and "Trade Central". The weaker copy appears in review and repair documents, where phrases like "repair lane", "active work pack", "visible outcome", and "pause ship" sound like instructions to Codex rather than language for a working decision tool.

## Delicate Wording Risks
- "decision engine" is acceptable internally, but customer-facing surfaces should prefer "decision table", "command board", or "model output" when the user is looking at computed results.
- "recommendations" needs care. For analytical software, use "model labels", "score labels", or "review candidates" near tables so the app does not imply certainty or advice.
- "Which trade options can save value" may overpromise. It should say "which trade options may preserve value" or "which trade options improve the model view".
- "players are likely to enter the draft pool" should be staged with confidence and source labels. Without visible assumptions, "likely" can sound predictive.
- "AcceptanceChance" is risky as a naked label because it can imply prediction. It should be paired with "model estimate", "assumptions", or "manual review required".
- "POLITICAL RISK" is vivid and useful internally, but in the UI it should be explained as league-context risk, not as a moral or personal judgment.
- "repair active pack", "pause ship", "No More Features Lock", "blocker-clearing repair", and "visible outcome" are build-system phrases. They should stay in docs, not visible app copy.
- "workflow", "handoff", "polish", and "manager-ready" do not appear as smoke hits, which is good. Keep them out of customer-facing copy unless the reader, action, and outcome are concrete.
- "War Score" and "War Room Rank" need stable definitions. If both appear, the UI should not make them feel interchangeable.
- "official top-5 release pressure" is accurate but slightly compressed. In first-screen UI, "Top-Five Release Risk" is clearer.

## Beautiful Language Opportunities
- Make page openings more decisive: short route title, one status line, then the table.
- Use "Review" and "Why" labels for expandable detail instead of explanatory paragraphs above tables.
- Replace advice-like labels with table labels that preserve humility: "Model Label", "Confidence", "Source", "Assumption", "Why".
- Give each page one plain job: "Review import issues", "See release risk", "Compare keeper labels", "Review trade candidates", "Check league pressure", "Audit model outputs".
- Make uncertainty useful instead of apologetic. Use copy like "Low confidence: missing market rank" or "Rank 400 source value" instead of broad caveats.
- Tighten action labels so they feel like a command table, not a fantasy column: KEEP, DROP RISK, SHOP, HOLD, OFFER, AVOID.
- Separate public/product language from app language. The README can say "decision engine"; the app should say "model output", "score table", and "review board".
- Let "Drop Deadline Command Center" remain the product promise, but keep the working screens spare and concrete.

## Priority Rewrite
The most important wording problem to fix next is advice certainty in analytical labels. Any screen that shows trade, keeper, drop, draft-pool, or acceptance outputs should label them as deterministic model outputs with visible confidence, source, and assumptions. Nami should replace loose phrases like "recommendations", "likely", "save value", and "AcceptanceChance" with concrete review language that makes clear what was computed and what still needs human judgment.

## Suggested Rewrites
- Before: "Which trade options save value before Roster Declaration Day?"
  After: "Which trade candidates preserve model value before Roster Declaration Day?"

- Before: "Which players are likely to enter the draft pool?"
  After: "Which players project as draft-pool candidates under the current assumptions?"

- Before: "Keeper/drop recommendations"
  After: "Keeper and drop labels"

- Before: "AcceptanceChance"
  After: "Acceptance estimate"

- Before: "POLITICAL RISK"
  After: "League-context risk"

- Before: "V1 is the Drop Deadline Command Center. It focuses on official top-5 release pressure, keeper/drop decisions, pick values, trade leverage, and league pressure using local CSV/SQLite snapshots."
  After: "V1 is the Drop Deadline Command Center: local CSV/SQLite tables for top-five release risk, keeper/drop labels, pick values, trade candidates, and league pressure."

- Before: "Review players to shop and shield targets."
  After: "Review shop candidates and shield targets."

## Voice Rules
- Use concrete football and table nouns: roster, pick, rank, score, label, pressure, release risk, trade candidate, draft pool.
- Keep first-screen copy short: one title, one status line, then the table or board.
- Say "model output", "model label", or "estimate" when the app computes a result.
- Pair scenario and what-if copy with visible assumptions.
- Avoid guru language: no "lock", "steal", "must", "win the trade", or certainty theater unless the rule is official and deterministic.
- Keep internal build language out of app surfaces.
- Use "Official Rank", "Market Rank", "War Room Rank", and "My Rank" exactly and separately.
- Put long explanations behind "Why", "Audit", "Source", or "Details".

## Next 5 Copy Tasks
- [ ] Replace visible "recommendations" copy with "model labels" or "review candidates"; guardrail: do not change formulas or labels, only surrounding text.
- [ ] Audit all trade table headers for prediction language; guardrail: "AcceptanceChance" must become a humble estimate label wherever visible.
- [ ] Tighten each Streamlit page intro to one title and one short status line; guardrail: no new explanatory blocks above the primary table.
- [ ] Add plain assumption/source wording near draft-pool and what-if outputs; guardrail: do not invent confidence claims or new data.
- [ ] Standardize risk labels across pages; guardrail: keep Official, Market, War Room, and My Rank distinct.

## Stop Or Continue
continue but fix copy first