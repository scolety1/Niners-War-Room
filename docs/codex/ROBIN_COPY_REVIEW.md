# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is sober, useful, and mostly mission-fit, but it still needs sharper separation between computed model output, human decision support, and vague command-center language.

## Mission Voice Fit
The language matches the mission better than a generic fantasy app: it is local-first, deterministic, table-first, and built around the Niners co-owner's deadline decisions. The strongest copy uses concrete nouns like "official top five," "forced-release risk," "keeper/drop recommendations," "pick value table," and "Trade Central." The weaker copy leans on broad product posture such as "decision engine," "Command Center," "league pressure," and "war score" without always showing the precise reader action or computed basis.

## Delicate Wording Risks
- "Decision engine" can imply stronger advice than the product should claim unless paired with computed outputs, assumptions, and review language.
- "Recommendations" needs care in analytical software. It should not sound like certainty or fantasy-guru advice; prefer "model labels," "review flags," or "computed recommendation label" where the source matters.
- "Which trade options save value" slightly overclaims outcome. The tool can identify modeled value gaps, not guarantee saved value.
- "Which players are likely to enter the draft pool" risks prediction theater unless the UI labels the basis as rule pressure, roster math, and assumptions.
- "AcceptanceChance" is a sensitive label. It can sound predictive or behavioral; it should be framed as a heuristic estimate from configured inputs.
- "War Score" is distinctive but may blur the separation between Official Rank, Market Rank, War Room Rank, and My Rank. It needs a visible definition near first use.
- "Command Center" is acceptable as project language, but customer-facing UI should still use direct task labels: Roster, Import Review, War Board, Trade Central, Draft Room, League Intel, Model Audit.
- "League pressure" is useful shorthand, but visible copy should explain whether this means keeper slots, official top-five exposure, roster count, or modeled drop pressure.
- "No Blocking Visual Bugs" conflicts with the reported "Not found" screenshots. This is a copy trust failure as well as a design failure because the report language says the opposite of the evidence.
- Repair-loop phrases like "pause ship and inspect results," "repair active pack," "handoff," "workflow," and "polish" belong in internal docs only, not visible product surfaces.

## Beautiful Language Opportunities
- Make the first screen more concrete: "Niners Official Top Five" is stronger than broad command-center framing.
- Use audit language as a trust layer: "source," "assumption," "formula," "confidence," and "why" should appear near model outputs.
- Replace broad advice language with review language: "Review DROP flags" is more honest than "Find drops."
- Give trade copy more humility: "modeled edge," "keeper impact," and "opponent benefit" are better than "save value."
- Give draft-pool copy clearer staging: first show the table, then hide "why this player may be available" behind detail.
- Keep page titles short and operational: "Import Review," "Niners Roster," "War Board," "Trade Central," "Draft Room," "League Intel," "Model Audit."
- Use status labels consistently and sparingly: KEEP, DROP, SHOP, HOLD, OFFER, CONSIDER, AVOID, RELEASE RISK.
- Add plain assumption labels near scenario or what-if controls so recalculation does not read as prediction.

## Priority Rewrite
Fix analytical overconfidence in customer-facing labels before polish. Nami should audit visible page titles, table headers, badges, and helper text for words that imply certainty, prediction, or guaranteed advice, especially "recommendations," "likely," "save value," and "AcceptanceChance." Replace them with concrete model-output language that names the source, assumption, or formula basis.

## Suggested Rewrites
- Before: "Which trade options save value before Roster Declaration Day?"
  After: "Which trade options show modeled value before Roster Declaration Day?"

- Before: "Which players are likely to enter the draft pool?"
  After: "Which players are flagged as possible draft-pool entries from keeper pressure and roster rules?"

- Before: "Display deterministic scores and recommendations."
  After: "Display deterministic scores, labels, assumptions, and source fields."

- Before: "AcceptanceChance"
  After: "Acceptance Estimate"

- Before: "No Blocking Visual Bugs"
  After: "Visual check passed: real page content found"

- Before: "No Blocking Visual Bugs" when screenshots show "Not found"
  After: "Visual check failed: route rendered Not found"

- Before: "league pressure"
  After: "keeper pressure"

- Before: "War Score"
  After: "War Room Score"

## Voice Rules
- Use concrete football and product nouns before brand language.
- Keep the working app terse: table first, detail second, explanation only on request.
- Separate computed output from advice in every label that affects decisions.
- Use "flag," "estimate," "model output," "source," and "assumption" when uncertainty matters.
- Avoid fantasy-guru language: no "must drop," "steal," "smash," "lock of the draft," or guaranteed trade outcomes.
- Keep Official Rank, Market Rank, War Room Rank, and My Rank visibly distinct.
- Use internal repair language only in docs, never in visible app copy.
- Do not let QA reports claim success when visible evidence shows missing routes or blank pages.

## Next 5 Copy Tasks
- [ ] Rename any visible "AcceptanceChance" label to "Acceptance Estimate"; guardrail: do not change formula names or tests unless required by display mapping.
- [ ] Audit visible uses of "recommendation" and replace overconfident instances with "model label" or "review flag"; guardrail: keep table headers short.
- [ ] Rewrite draft-pool copy to say "possible draft-pool entries" unless the basis is explicitly shown; guardrail: no prediction language without assumptions.
- [ ] Update visual QA report language so "Not found" screenshots cannot produce "No Blocking Visual Bugs"; guardrail: copy must match evidence.
- [ ] Add or verify a short definition for "War Room Score" near first visible use; guardrail: keep the definition behind a detail control if it is longer than one sentence.

## Stop Or Continue
continue but fix copy first